# Chapter 4: Data Path Mechanics — SQE Parsing, PRP/SGL Walkers & DMA Engines

Now we enter the **I/O Fast Path** (`QID > 0`). When the Hardware SQE Fetch Engine pulls a 64-byte NVM `Read` (`0x02`) or `Write` (`0x01`) command into an internal **Command Slot (`CmdTag`)**, the Frontend must:
1. Validate the command fields (`NSID`, `SLBA`, `NLB`, `PSDT`);
2. Walk the host's data buffer pointers (**Physical Region Pages [PRPs]** or **Scatter-Gather Lists [SGLs]**) to translate logical payload offsets into 64-bit Host DRAM physical addresses;
3. Slice the host LBA range `(SLBA, NLB)` into **4 KiB-aligned internal FTL Sub-Requests (`SubReqs`)** and allocate internal SRAM/DRAM **Buffer Descriptors (`BDs`)**.

In this chapter, we cover every bit, rule, edge case, and hardware/firmware algorithm for SQE parsing, PRP/SGL walking, and LBA slicing.

---

## 4.1 Bit-Accurate Anatomy of the 64-Byte NVM Command SQE & 16-Byte CQE

### 1. The 64-Byte NVM Read/Write Submission Queue Entry (`SQE`)

```
Byte   31              24 23              16 15               8 7                0
     +------------------+------------------+------------------+------------------+
0x00 |         Command Identifier (CID)    |PSDT|Rsvd | FUSE  |   Opcode (OPC)   | CDW0
     +------------------+------------------+------------------+------------------+
0x04 |                           Namespace Identifier (NSID)                     | CDW1
     +------------------+------------------+------------------+------------------+
0x08 |                                  Reserved                                 | CDW2-3
0x10 |                            Metadata Pointer (MPTR)                        | CDW4-5
     +------------------+------------------+------------------+------------------+
0x18 |                        Data Pointer (DPTR) - PRP1 [63:0]                  | CDW6-7
0x20 |                        Data Pointer (DPTR) - PRP2 [63:0]                  | CDW8-9
     |                     (or 16-Byte SGL1 Descriptor if PSDT != 00b)           |
     +------------------+------------------+------------------+------------------+
0x28 |                        Starting LBA - SLBA Low [31:0]                     | CDW10
0x2C |                        Starting LBA - SLBA High [63:32]                   | CDW11
     +------------------+------------------+------------------+------------------+
0x30 |LR|FUA| PRINFO |Rsvd|        Number of Logical Blocks (NLB, 0-based!)      | CDW12
     +------------------+------------------+------------------+------------------+
0x34 |                  Dataset Management (DSM) / Directives                    | CDW13
0x38 |                  Expected Initial Logical Block Reference Tag (EILBRT)    | CDW14
0x3C |                  Expected Logical Block App Tag & Mask (ELBATM / ELBAT)   | CDW15
     +------------------+------------------+------------------+------------------+
```

Key fields parsed by the Frontend Command Validator:
- **`OPC` (`CDW0[7:0]`):** `0x00` = `Flush`, `0x01` = `Write`, `0x02` = `Read`, `0x04` = `Write Uncorrectable`, `0x05` = `Compare`, `0x08` = `Write Zeroes`, `0x09` = `Dataset Management (Deallocate / TRIM)`.
- **`PSDT` (`CDW0[15:14]`):** PRP or SGL for Data Transfer:
  - `00b`: **PRPs** are used (`DPTR` contains 64-bit `PRP1` + 64-bit `PRP2`).
  - `01b`: **SGLs** are used for Data; `MPTR` is a contiguous physical address.
  - `10b`: **SGLs** are used for both Data and Metadata.
- **`CID` (`CDW0[31:16]`):** 16-bit host tag echoed back in the CQE.
- **`SLBA` (`{CDW11, CDW10}`):** 64-bit Starting Logical Block Address.
- **`NLB` (`CDW12[15:0]`):** Number of Logical Blocks (**0's-based**! E.g., `NLB = 0` means **1 logical block**; `NLB = 7` means **8 logical blocks**; `NLB = 65535` means **65,536 logical blocks**).
- **`FUA` (`CDW12[30]`):** Force Unit Access (`1` = bypass volatile cache; read from / program to non-volatile NAND before completing!).

### 2. The 16-Byte Completion Queue Entry (`CQE`)

```
Byte   31              24 23              16 15               8 7                0
     +------------------+------------------+------------------+------------------+
0x00 |                         Command Specific (DW0)                            | DW0
0x04 |                                Reserved (DW1)                             | DW1
     +------------------+------------------+------------------+------------------+
0x08 |            SQ Identifier (SQID)     |          SQ Head Pointer (SQHD)     | DW2
     +------------------+------------------+------------------+------------------+
0x0C |DNR|M|CRD|  SCT   |    Status Code (SC)   |P|   Command Identifier (CID)   | DW3
     +------------------+------------------+------------------+------------------+
```

Look closely at `DW3[31:16]` (the 16-bit Status Field + Phase Bit):
- **`Bit 16` (`P`):** Phase Tag (`0` or `1`).
- **`Bits [24:17]` (`SC`):** 8-bit Status Code (e.g., `0x00` = Successful Completion, `0x02` = Invalid Field in Command, `0x13` = PRP Offset Invalid, `0x80` = LBA Out of Range).
- **`Bits [27:25]` (`SCT`):** 3-bit Status Code Type (`000b` = Generic Command Status, `001b` = Command Specific Status, `010b` = Media and Data Integrity Errors).
- **`Bit 31` (`DNR`):** **Do Not Retry** (`1` = tells the host OS driver that retrying the exact same command will never succeed, e.g., `LBA Out of Range` or `Invalid Opcode`!).

---

## 4.2 Fast-Path Command Validation Rules (Hardware + Firmware Exception Trap)

Before touching the DMA engine or FTL, the Frontend Command Validator checks every incoming SQE in 1 clock cycle (and traps to HIL Firmware to post an error CQE with `DNR = 1` if any check fails):

1. **Namespace Check:** Is `NSID == 0` or `NSID > NN` or inactive? $\to$ Reject with `Invalid Namespace or Format (SCT=0x00, SC=0x0B, DNR=1)`.
2. **LBA Bounds & 64-bit Overflow Check:**
   Compute the total blocks `num_blocks = (uint32_t)NLB + 1`. Does `SLBA + num_blocks > NSZE` (or wrap around $2^{64}$)? $\to$ Reject with **`LBA Out of Range (SCT=0x00, SC=0x80, DNR=1)`**.
3. **MDTS (Maximum Data Transfer Size) Check:**
   Does `num_blocks * BlockSize > MaxTransferBytes`? $\to$ Reject with `Invalid Field in Command (SCT=0x00, SC=0x02, DNR=1)`.
4. **Duplicate `CID` Check (Per-SQ):**
   Is there already an in-flight command from the same `SQID` with the exact same `CID`? $\to$ Reject with **`Command ID Conflict (SCT=0x00, SC=0x03, DNR=1)`**.

---

## 4.3 Physical Region Pages (PRPs) — Complete Hardware Walker Rules

### Intuition
In a virtualized OS (Linux/Windows), a 16 KiB or 128 KiB buffer allocated with `malloc()` is contiguous in *virtual* memory, but scattered across arbitrary non-contiguous 4 KiB pages in *physical* Host DRAM.
How does the host tell the SSD where those physical pages are using only two 64-bit fields (`PRP1` and `PRP2`) inside the 64-byte SQE?

### The Four Sacred Rules of PRPs (NVMe Base Spec Section 4.1.1)
Let `PageSize` be the Host Memory Page Size configured in `CC.MPS` ($2^{12 + \text{CC.MPS}}$, almost always **$4096\text{ bytes}$**; let `OffsetMask = PageSize - 1 = 0xFFF`, and `PageMask = ~0xFFF`).

1. **Rule 1 (`PRP1` Offset Rule):**
   `PRP1` is ALWAYS the 64-bit Host DRAM physical address of the **first byte** of the data transfer.
   - `PRP1` **may have a non-zero page offset** (`prp1_offset = PRP1 & 0xFFF`), though it must be Dword-aligned (`Bits [1:0] == 00b`).
   - Therefore, the number of bytes that fit inside the first physical page (`PRP1`) is:
     $$\text{FirstPageBytes} = \min\big(\text{TotalTransferBytes}, \; \text{PageSize} - (\text{PRP1} \mathbin{\&} \text{OffsetMask})\big)$$

2. **Rule 2 (When `PRP2` Is Unused):**
   If $\text{TotalTransferBytes} \le \text{PageSize} - (\text{PRP1} \mathbin{\&} \text{OffsetMask})$, the **entire transfer fits inside the single page pointed to by `PRP1`**!
   - In this case, `PRP2` is completely ignored by the SSD hardware (the host doesn't even need to zero `PRP2`).

3. **Rule 3 (When `PRP2` Is a Direct Second Page Pointer):**
   Suppose bytes remain after `PRP1` ($\text{RemBytes} = \text{TotalTransferBytes} - \text{FirstPageBytes} > 0$), AND $\text{RemBytes} \le \text{PageSize}$.
   - Then the entire remaining transfer fits inside **one more page**, so **`PRP2` is the direct 64-bit physical base address of the second data page!**
   - **CRITICAL ALIGNMENT RULE:** Unlike `PRP1`, when `PRP2` points to a data page, its page offset **MUST BE ZERO (`(PRP2 & OffsetMask) == 0`)**! If `(PRP2 & OffsetMask) != 0`, your PRP Walker hardware must immediately abort the command and return **`PRP Offset Invalid (SCT=0x00, SC=0x13, DNR=1)`**!

4. **Rule 4 (When `PRP2` Is a Pointer to a PRP List in Host DRAM):**
   Suppose after `PRP1`, **more than one page** of data remains ($\text{RemBytes} > \text{PageSize}$).
   - Now `PRP2` does **NOT** point to user data! Instead, **`PRP2` is the 64-bit Host DRAM physical address of a PRP List**—an array of 64-bit physical page pointers `[Entry_0, Entry_1, Entry_2, ...]` stored in Host DRAM!
   - **Alignment Rules for a PRP List:**
     - `PRP2` itself must be Dword-aligned (`Bits [1:0] == 00b`) and may start at an offset inside a host page, though it cannot cross a page boundary without chaining.
     - **Every single 64-bit entry `Entry_k` inside the PRP List MUST have page offset ZERO (`(Entry_k & OffsetMask) == 0`)!** If any `Entry_k` has a non-zero page offset, abort with **`PRP Offset Invalid (SCT=0x00, SC=0x13, DNR=1)`**!
   - **Rule 4b (Chained PRP Lists for Huge Transfers $> 2\text{ MiB}$):**
     A single 4 KiB host page can hold at most $4096 / 8 = 512$ PRP entries. If a PRP List requires more entries than remain in the current 4 KiB PRP List page, the **very last 64-bit entry** of the current PRP List page (`offset 0xFF8`) is **NOT** a data page pointer—it is the **64-bit physical base address of the NEXT 4 KiB PRP List page**!

```
Case A: 4 KiB Aligned Transfer (Total=4096B, PRP1=0x1000_0000 [offset 0])
  [PRP1: 0x1000_0000 (4096B)]   [PRP2: Ignored!]

Case B: 4 KiB Unaligned Transfer Crossing Page Boundary (Total=4096B, PRP1=0x1000_0800 [offset 2048])
  [PRP1: 0x1000_0800 (First 2048B)]  +  [PRP2: 0x2000_0000 (Remaining 2048B, offset MUST be 0!)]

Case C: 16 KiB Aligned Transfer (Total=16384B = 4 Pages, PRP1=0x1000_0000)
  [PRP1: 0x1000_0000 (Page 0: 4096B)]
  [PRP2: 0x9000_0000] ---> Points to PRP List in Host DRAM (SSD issues extra 24B PCIe MRd!):
                           +---------------------------------------+
                           | Entry 0: 0x2000_0000 (Page 1: 4096B)  |
                           | Entry 1: 0x3000_0000 (Page 2: 4096B)  |
                           | Entry 2: 0x4000_0000 (Page 3: 4096B)  |
                           +---------------------------------------+
```

> **Why PRPs Cannot Represent Arbitrary Scatter-Gather Buffers:**
> Look at Rules 1–4: only the *very first chunk* (`PRP1`) can end at a page boundary after starting mid-page, and only the *very last chunk* can end mid-page after starting at offset `0`. Every intermediate chunk **must start at offset `0` and span a full `PageSize` ($4096\text{ B}$)**! If a user application tries to gather two 512-byte buffers from the middle of two different pages into one NVMe command, **PRPs cannot express it**! That limitation is why NVMe introduced **Scatter-Gather Lists (SGLs)**.

---

## 4.4 Scatter-Gather Lists (SGLs) — Flexible Arbitrary-Byte Addressing

When `SQE.CDW0.PSDT != 00b`, the 16-byte `DPTR` field (`Bytes [39:24]` of the SQE) contains an **SGL1 Descriptor** instead of `PRP1 + PRP2`. Every SGL descriptor is **16 bytes** (`Address [63:0]`, `Length [31:0]`, `Reserved [23:0]`, `SGL Identifier [7:0]` where `Bits [7:4]` = SGL Descriptor Type):

| SGL Type (`Bits [7:4]`) | Name | Meaning for SSD DMA Engine |
| :---: | :--- | :--- |
| `0x0` | **SGL Data Block** | `Address` = 64-bit Host DRAM byte address (any alignment!), `Length` = exact byte count to transfer. |
| `0x1` | **SGL Bit Bucket** | Used on Reads to discard `Length` bytes without DMA-writing them to Host DRAM (`Address` ignored!). |
| `0x2` | **SGL Segment** | `Address` points to an array of more 16B SGL descriptors in Host DRAM (total byte size = `Length`, multiple of 16), and **more segments follow**! |
| `0x3` | **SGL Last Segment** | Same as `SGL Segment`, except this is the **final segment** of SGL descriptors. |

---

## 4.5 LBA Slicing: Translating Host `(SLBA, NLB)` into 4 KiB FTL `SubReqs`

### Intuition
Inside a modern SSD, the Flash Translation Layer (FTL) maps logical addresses to physical flash pages at a fixed **FTL Mapping Granularity (`LPN` — Logical Page Number)**, which is almost universally **$4096\text{ bytes}$ ($4\text{ KiB}$)**.
- What if the namespace is formatted with **`LBADS = 12` ($4096\text{ B}$ logical blocks)**?
  Then $1\text{ Host LBA} = 1\text{ FTL LPN}$ ($4\text{ KiB}$)! A Read with `SLBA = 100, NLB = 3` ($4$ blocks $= 16\text{ KiB}$) slices cleanly into $4$ internal FTL Sub-Requests: `LPN 100, 101, 102, 103`.
- What if the namespace is formatted with legacy **`LBADS = 9` ($512\text{ B}$ logical sectors)**?
  Then $8\text{ Host LBAs} = 1\text{ FTL LPN}$ ($4\text{ KiB}$), with:
  $$\text{LPN} = \lfloor \text{LBA} / 8 \rfloor = \text{LBA} \gg 3, \qquad \text{SectorOffset} = \text{LBA} \mathbin{\&} 7$$
  If a host writes an **unaligned** 512B sector (say `SLBA = 3, NLB = 0`), it modifies only sector `3` inside `LPN 0`! The SSD must perform an internal **Read-Modify-Write (RMW)**: FTL reads the full 4 KiB `LPN 0` from NAND into a 4 KiB SRAM buffer, overwrites bytes `[1536..2047]` with the 512B host DMA data, and programs the updated 4 KiB `LPN 0` to NAND!

---

## 4.6 Runnable Hardware PRP Walker & LBA Slicer in Python

Run this self-contained script, which implements the exact NVMe hardware PRP Builder (Host side) and **Hardware PRP Walker + Alignment Validator + 4 KiB LBA Slicer** (SSD Frontend side), testing all 4 PRP cases (1 page, 2 pages unaligned, PRP List, and Chained PRP Lists $> 2\text{ MiB}$) as well as catching `PRP Offset Invalid`:

```python
import struct

class NVMePRPWalkerAndSlicer:
    """Bit-accurate SSD Frontend Hardware PRP Walker & 4 KiB Sub-Request Slicer."""
    def __init__(self, host_page_size=4096):
        self.page_size = host_page_size
        self.offset_mask = host_page_size - 1
        self.page_mask = ~self.offset_mask
        self.host_dram_prp_pages = {}  # page_addr -> bytearray(4096)

    def walk_prp(self, prp1: int, prp2: int, total_bytes: int):
        """
        Walks PRP1 and PRP2 for a transfer of `total_bytes`.
        Returns (status_sc, chunks, pcie_prp_list_reads) where chunks is a list of (host_phys_addr, length).
        """
        if (prp1 & 0x3) != 0:
            return (0x13, [], 0)  # SC=0x13: PRP Offset Invalid (not Dword aligned)

        chunks = []
        prp_list_reads = 0

        # Rule 1: First page from PRP1
        first_offset = prp1 & self.offset_mask
        first_len = min(total_bytes, self.page_size - first_offset)
        chunks.append((prp1, first_len))
        rem_bytes = total_bytes - first_len

        # Rule 2: Fits completely in PRP1
        if rem_bytes == 0:
            return (0x00, chunks, prp_list_reads)

        # Rule 3: Remaining bytes fit in a single second page -> PRP2 is a direct page pointer!
        if rem_bytes <= self.page_size:
            if (prp2 & self.offset_mask) != 0:
                return (0x13, [], prp_list_reads)  # SC=0x13: PRP2 direct page MUST have offset 0!
            chunks.append((prp2, rem_bytes))
            return (0x00, chunks, prp_list_reads)

        # Rule 4: Remaining bytes > PageSize -> PRP2 points to a PRP List in Host DRAM!
        if (prp2 & 0x3) != 0:
            return (0x13, [], prp_list_reads)

        curr_list_ptr = prp2
        prp_list_reads += 1

        while rem_bytes > 0:
            list_page_base = curr_list_ptr & self.page_mask
            list_offset = curr_list_ptr & self.offset_mask
            page_buf = self.host_dram_prp_pages[list_page_base]
            entry_val = struct.unpack_from("<Q", page_buf, list_offset)[0]

            # Check if we are at the last 8B slot of a PRP List page AND still need > 1 page
            is_last_slot_in_page = (list_offset == self.page_size - 8)
            if is_last_slot_in_page and rem_bytes > self.page_size:
                # Rule 4b: Chained PRP List pointer!
                if (entry_val & self.offset_mask) != 0:
                    return (0x13, [], prp_list_reads)
                curr_list_ptr = entry_val
                prp_list_reads += 1
                continue

            # Regular PRP List entry: MUST have page offset 0!
            if (entry_val & self.offset_mask) != 0:
                return (0x13, [], prp_list_reads)

            chunk_len = min(rem_bytes, self.page_size)
            chunks.append((entry_val, chunk_len))
            rem_bytes -= chunk_len
            curr_list_ptr += 8

        return (0x00, chunks, prp_list_reads)

walker = NVMePRPWalkerAndSlicer(host_page_size=4096)

# Case 1: 4 KiB aligned transfer (fits in PRP1 alone)
sc, chunks, reads = walker.walk_prp(prp1=0x1000_0000, prp2=0xDEAD_BEEF, total_bytes=4096)
print(f"Case 1 (4KiB aligned):    SC=0x{sc:02X}, Chunks={len(chunks)}, Extra PRP List MRds={reads} -> {chunks}")

# Case 2: 4 KiB unaligned transfer starting at offset 0x800 (uses PRP1 + PRP2 direct)
sc, chunks, reads = walker.walk_prp(prp1=0x1000_0800, prp2=0x2000_0000, total_bytes=4096)
print(f"Case 2 (4KiB unaligned):  SC=0x{sc:02X}, Chunks={len(chunks)}, Extra PRP List MRds={reads} -> "
      f"[(0x{chunks[0][0]:X}, {chunks[0][1]}), (0x{chunks[1][0]:X}, {chunks[1][1]})]")

# Case 3: Illegal PRP2 with non-zero offset (0x2000_0400) -> Caught by HW Walker!
sc, _, _ = walker.walk_prp(prp1=0x1000_0800, prp2=0x2000_0400, total_bytes=4096)
print(f"Case 3 (Bad PRP2 offset): SC=0x{sc:02X} (Expected 0x13 = PRP Offset Invalid!)")

# Case 4: 16 KiB transfer (4 pages -> PRP1 + 3-entry PRP List at 0x9000_0000)
prp_list_page = bytearray(4096)
for i, addr in enumerate([0x2000_0000, 0x3000_0000, 0x4000_0000]):
    struct.pack_into("<Q", prp_list_page, i * 8, addr)
walker.host_dram_prp_pages[0x9000_0000] = prp_list_page
sc, chunks, reads = walker.walk_prp(prp1=0x1000_0000, prp2=0x9000_0000, total_bytes=16384)
print(f"Case 4 (16KiB PRP List):  SC=0x{sc:02X}, Chunks={len(chunks)}, Extra PRP List MRds={reads}")

# Case 5: 2.01 MiB transfer (515 pages -> PRP1 + Chained 2-page PRP List!)
list_p1, list_p2 = bytearray(4096), bytearray(4096)
for i in range(511):
    struct.pack_into("<Q", list_p1, i * 8, 0xA000_0000 + i * 4096)
struct.pack_into("<Q", list_p1, 511 * 8, 0x9000_1000)  # Last slot chains to list_p2!
for i in range(3):
    struct.pack_into("<Q", list_p2, i * 8, 0xB000_0000 + i * 4096)
walker.host_dram_prp_pages[0x9000_0000] = list_p1
walker.host_dram_prp_pages[0x9000_1000] = list_p2
sc, chunks, reads = walker.walk_prp(prp1=0x1000_0000, prp2=0x9000_0000, total_bytes=515 * 4096)
print(f"Case 5 (515-page Chained): SC=0x{sc:02X}, Chunks={len(chunks)}, Extra PRP List MRds={reads}")
```

---

## 4.7 Check Your Understanding (Firmware Design Problems)

*(Full step-by-step solutions are in [Chapter 99](./99-solutions-and-references.md).)*

1. **The Unaligned 8 KiB PRP Trap:** Suppose the host sends an **8 KiB (`8192` bytes)** Read command (`NLB = 1` with 4 KiB blocks), and `PRP1 = 0x0000_0001_0000_0800` (page offset `2048`). Does `PRP2` contain the physical address of the second page, OR does `PRP2` point to a **PRP List**? Calculate how many physical pages this 8 KiB buffer spans and how many entries are in the PRP List!
2. **Maximum Transfer Size of a Single Non-Chained 4 KiB PRP List Page:** If `PRP1` is page-aligned (`offset = 0`) and `PRP2` points to the start (`offset = 0`) of a single 4 KiB PRP List page (with no chaining to a second PRP List page), what is the exact maximum number of 4 KiB data pages (and total bytes) that can be transferred by that single command?
3. **Why `NLB = 0xFFFF` Can Overflow Naive 16-Bit Firmware Math:** Look at `SQE.CDW12[15:0]` (`NLB`). If a firmware engineer writes `uint16_t num_blocks = sqe->nlb + 1;` in C, what bug occurs when the host submits a valid command with `NLB = 0xFFFF` ($65,535$)?
