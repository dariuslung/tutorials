# Chapter 99: Firmware Design Problem Solutions & NVMe Specification Reference

---

## Part I: Step-by-Step Solutions to Firmware Design Problems

### Chapter 1 Solutions

#### Problem 1.1: Doorbell Stride (`DSTRD`) Address Calculation & Virtualization Use Case
- **Formula:** By the NVMe Base Specification (Section 3.1.26), when `CAP.DSTRD` is $d$, each Doorbell slot occupies $4 \ll d = 4 \times 2^d$ bytes:
  $$\text{Offset}(\texttt{SQyTDBL}) = \texttt{0x1000} + (2y) \times (4 \ll d)$$
  $$\text{Offset}(\texttt{CQyHDBL}) = \texttt{0x1000} + (2y + 1) \times (4 \ll d)$$
- **For `DSTRD = 1` ($4 \ll 1 = 8\text{ bytes}$) and `y = 3`:**
  - `SQ3TDBL`: $\texttt{0x1000} + 2(3) \times 8 = \texttt{0x1000} + 48 = \mathbf{\texttt{0x1030}}$.
  - `CQ3HDBL`: $\texttt{0x1000} + (2(3)+1) \times 8 = \texttt{0x1000} + 56 = \mathbf{\texttt{0x1038}}$.
- **Why enterprise/virtualized SSDs support `DSTRD = 10` ($4\text{ KiB}$ stride):**
  In hypervisors (KVM/VMware/Hyper-V) or user-space drivers (SPDK / VFIO), the OS MMU maps physical BAR0 space into guest VMs or unprivileged user processes at **4 KiB page granularity**. If all doorbells were packed 4 bytes apart (`DSTRD = 0`), mapping page `0x1000` into Guest VM #1 would allow Guest VM #1 to ring Guest VM #2's doorbells! Setting `DSTRD` so each Queue Pair's doorbells sit on their own isolated 4 KiB MMU page allows safe, zero-exit user-space/guest doorbell mapping!

#### Problem 1.2: The Premature `CSTS.RDY = 0` Memory Corruption Bug
- Here is the exact disaster timeline when firmware clears `CSTS.RDY = 0` before draining in-flight PCIe DMAs:
  1. At $t = 0\ \mu\text{s}$: An in-flight 128 KiB Read (`CmdTag = 5`) is still receiving 4 KiB slices from NAND and DMA-writing them to Host DRAM physical pages `0x8000_0000 .. 0x8001_F000`.
  2. At $t = 1\ \mu\text{s}$: The host driver times out or unloads, writes `CC.EN = 0`, and spins polling `while (readl(CSTS) & 1);`.
  3. At $t = 2\ \mu\text{s}$: The buggy firmware immediately sets `CSTS.RDY = 0` while `CmdTag = 5`'s DMA is still queued in the SSD's Frontend DMA FIFO!
  4. At $t = 3\ \mu\text{s}$: Seeing `CSTS.RDY == 0`, the Linux kernel immediately unmaps the IOMMU entries or returns physical pages `0x8000_0000 .. 0x8001_F000` to the kernel page allocator (`free_pages()`), which hands page `0x8000_4000` to another process (or kernel page table!).
  5. At $t = 8\ \mu\text{s}$: The SSD's undrained DMA engine writes 4 KiB of old disk data over PCIe into `0x8000_4000`, silently overwriting live kernel data structures on the host!

#### Problem 1.3: Impact of `CC.MPS = 2` ($16\text{ KiB}$ Host Page Size)
- Setting `CC.MPS = 2` sets `HostPageSize` $= 2^{12 + 2} = 16,384\text{ bytes}$ ($16\text{ KiB}$).
- **What changes in the controller:**
  1. Every PRP page-offset mask in the PRP Walker becomes `0x3FFF` (14 bits) instead of `0x0FFF` (12 bits).
  2. `PRP1` can transfer up to $16\text{ KiB}$, `PRP2` (direct page) must be $16\text{ KiB}$-aligned (`(PRP2 & 0x3FFF) == 0`), and each PRP List page holds $16,384 / 8 = 2,048$ PRP entries!
  3. `Identify Controller.MDTS` is multiplied by `MPSMIN` ($2^{12 + \text{CAP.MPSMIN}}$), NOT `CC.MPS`.
- **What does NOT change:**
  The sizes of an SQE ($2^{\text{CC.IOSQES}} = 64\text{ B}$) and CQE ($2^{\text{CC.IOCQES}} = 16\text{ B}$) and the Namespace LBA size (`2^LBADS`) are completely independent of `CC.MPS`!

---

### Chapter 2 Solutions

#### Problem 2.1: Many-to-One SQ-to-CQ Mapping & Pre-Reserving CQ Slots at Fetch Time
- A 256-entry Completion Queue (`CQ 1`) can hold at most $256 - 1 = 255$ unconsumed CQEs before `(cq_tail + 1) % 256 == cq_head`. When the 8 SQs submit $8 \times 32 = 256$ commands, the 256th completion hits **CQ Full**.
- If the controller fetches all 256 commands without pre-reserving CQ slots, the 256th command will read 4 KiB from NAND into a **Controller SRAM Read Buffer (`BD`)**, DMA the data to the host, and then get stuck at the CQE Posting Engine (holding onto its `CmdSlot` or `BD` resource if CQE and DMA are coupled).
- By **maintaining a per-CQ `reserved_slots` counter** in `CQCT[cqid]` (`reserved_slots = in_flight_on_bound_sqs + unconsumed_cqes < qsize - 1`) and checking it inside the **SQE Arbiter/Fetcher**, the controller simply pauses fetching the 256th SQE from Host DRAM until the host advances `CQ1HDBL`, keeping internal SRAM buffers 100% free for other CQs!

#### Problem 2.2: Disambiguating `SQ1TDBL = 505` When `sq_head = 500, sq_tail = 510`
- Remember the ring invariant: the Host owns `sq_tail`, the SSD owns `sq_head`, and the Host is only allowed to advance `sq_tail` forward into empty slots without ever overtaking `sq_head`!
- When `sq_head = 500` and `sq_tail = 510` on a `1024`-entry ring:
  - Slots `500 .. 509` ($10$ slots) are currently **unfetched commands** owned by the SSD.
  - Slots `510 .. 1023` and `0 .. 498` ($1013$ slots) are **free slots** available to the Host!
  - Wait: can the host legally advance `sq_tail` from `510` all the way past `500` to `505`? **NO!** Because to reach `505` moving forward from `510`, `sq_tail` would have to wrap around `1023 -> 0` and **overtake `sq_head = 500`**, overwriting unfetched slots `500 .. 504`!
- **Hardware/Firmware Rule:** Any doorbell write `new_tail != old_tail` where the forward distance `(new_tail - old_tail) % qsize` is greater than the free space `(sq_head - 1 - old_tail) % qsize` (or `new_tail >= qsize`) is an **illegal backward/overflow doorbell write** (`Invalid Doorbell Write Value`). Meanwhile, a redundant write where `new_tail == old_tail` is ignored by hardware as a no-op.

#### Problem 2.3: Sizing the Internal `SQCT` / `CQCT` / Doorbell SRAM for 1024 Queue Pairs
- `SQCT`: $1025 \text{ queues (Admin + 1024 I/O)} \times 32\text{ B} = 32,800\text{ B} \approx 32\text{ KiB}$.
- `CQCT`: $1025 \text{ queues} \times 32\text{ B} = 32,800\text{ B} \approx 32\text{ KiB}$.
- `Doorbell SRAM`: $1025 \times 2 \text{ doorbells} \times 4\text{ B} = 8,200\text{ B} \approx 8\text{ KiB}$.
- **Total SRAM:** $\mathbf{\approx 72\text{ KiB}}$, which easily fits inside local Tightly Coupled Memory (TCM) on an enterprise controller!

---

### Chapter 3 Solutions

#### Problem 3.1: Why NVMe Uses 0's-Based Fields & What `QSIZE = 0x0000` Means
- **Why 0's-based:** A 16-bit unsigned integer holds values `0 .. 65535` (`0x0000 .. 0xFFFF`). By encoding `NLB` and `QSIZE` as 0's-based (where $v$ means $v + 1$), a 16-bit field can represent a power-of-two maximum of **$65,536$ ($64\text{K}$) blocks or queue entries** (`0xFFFF` $\implies 65,536$) without needing a 17th bit, and avoids the meaningless request of "$0$ blocks"!
- **Why `Create I/O SQ/CQ` with `QSIZE = 0x0000` is illegal:**
  `QSIZE = 0x0000` means a ring of size $0 + 1 = 1\text{ entry}$. Because a circular ring of capacity $Q$ can hold at most $Q - 1$ active entries (since `Head == Tail` means empty), a 1-entry ring can hold $1 - 1 = \mathbf{0\text{ entries}}$! Therefore, the NVMe spec mandates minimum queue size $= 2$ entries (`QSIZE >= 1`), and `QSIZE == 0` must be rejected with `Invalid Queue Size (SCT=0x01, SC=0x02)`.

#### Problem 3.2: Address Translation for a Non-Contiguous Queue (`PC = 0`)
- When `Create I/O SQ` has `PC = 0` for a 1024-entry SQ ($64\text{ KiB} = 16$ pages of $4\text{ KiB}$), `PRP1` points to a **PRP List in Host DRAM** containing sixteen 64-bit physical page addresses `QPage[0..15]`.
- Since each 4 KiB page holds $4096 / 64 = 64$ SQEs:
  - For `sq_head = 300`:
    $$\text{PageIndex} = \lfloor 300 / 64 \rfloor = 4, \qquad \text{ByteOffsetInPage} = (300 \bmod 64) \times 64 = 44 \times 64 = 2816\text{ (0xB00)}$$
  - Thus, the Fetch Engine reads the 64B SQE from Host DRAM physical address **`QPage[4] + 0xB00`**.

#### Problem 3.3: Why Firmware Must Mask an Async Event Type Until `Get Log Page` (`RAE = 0`)
- Suppose the host has parked 4 `AER` commands (`CID 100..103`) in your firmware.
- When temperature crosses $85^\circ\text{C}$, firmware completes `CID 100`.
- Remember: the temperature sensor is *still* reading $85^\circ\text{C}$ one microsecond later! If firmware did not mask the `Temperature` event bit after completing `CID 100`, the thermal monitor loop would immediately pop `CID 101`, `CID 102`, and `CID 103` in the next 3 microseconds—exhausting all 4 of the host's parked AERs on the exact same single event!
- Therefore, the NVMe spec requires the controller to **mask** that Asynchronous Event Type after completing one `AER`, and only clear the mask when the host reads the corresponding Log Page (`Get Log Page` with `RAE = 0`).

---

### Chapter 4 Solutions

#### Problem 4.1: The Unaligned 8 KiB PRP Trap (`Total = 8192B`, `PRP1 = 0x100000800`)
- Let us trace how many 4 KiB physical pages an 8192-byte buffer starting at offset `0x800` ($2048$) spans:
  1. **Page 1 (`PRP1 = 0x100000800`):** Transfers $\min(8192, 4096 - 2048) = \mathbf{2048\text{ bytes}}$. Remaining bytes $= 8192 - 2048 = \mathbf{6144\text{ bytes}}$.
  2. Since $\text{RemBytes} = 6144 > 4096$, the remaining bytes span **two more pages** ($4096\text{ B}$ on Page 2 + $2048\text{ B}$ on Page 3 = **3 physical pages total**)!
- Therefore, by Rule 4 (Section 4.3), **`PRP2` MUST point to a PRP List in Host DRAM** containing **2 entries** (`Entry[0]` for the 4096B middle page, and `Entry[1]` for the 2048B tail page)!

#### Problem 4.2: Maximum Transfer Size of a Single Non-Chained 4 KiB PRP List Page
- `PRP1` (at offset `0`) transfers **1 page** ($4\text{ KiB}$).
- A single 4 KiB PRP List page holds $4096 / 8 = \mathbf{512}$ 64-bit page pointers (`Entry[0..511]`). If there is no next PRP List page to chain to, even the 512th slot (`Entry[511]`) can point directly to a data page!
- Total data pages $= 1\text{ (from PRP1)} + 512\text{ (from PRP List)} = \mathbf{513\text{ pages}} = 513 \times 4\text{ KiB} = \mathbf{2,052\text{ KiB}}$ ($2,101,248\text{ bytes}$).

#### Problem 4.3: The 16-Bit `sqe->nlb + 1` Overflow Bug
- In C, if `num_blocks` is declared as `uint16_t` and `sqe->nlb == 0xFFFF` ($65,535$), then `(uint16_t)(0xFFFF + 1)` wraps around 16-bit arithmetic to **`0x0000` ($0$ blocks)!**
- A buggy command parser using `uint16_t num_blocks` will think the transfer size is $0\text{ bytes}$, pass the `SLBA + 0 <= NSZE` bounds check even at the end of the disk, or underflow `remaining_subreqs`!
- **Always cast `NLB` to `uint32_t` before adding 1:** `uint32_t num_blocks = (uint32_t)sqe->nlb + 1U;`.

---

### Chapter 5 Solutions

#### Problem 5.1: Overlapping Concurrent Writes (`Write A` then `Write B` to `SLBA = 50`)
- Suppose `Write A` (`CID=1`) and `Write B` (`CID=2`) both write to `LPN 50`. Because `Write B` was fetched from the Submission Queue *after* `Write A` (or if serialized), if the DMA engine fetches both payloads in parallel and `Write A`'s PCIe `CplD` arrives *after* `Write B`'s `CplD`, `Write A` would overwrite `Write B` in the Write Buffer!
- **Two Standard Firmware Solutions:**
  1. **LBA Collision Serialization at Intake:** Maintain an **In-Flight Write LPN Hash/CAM**. When `Write B (LPN 50)` arrives and sees `Write A (LPN 50)` is still DMA-fetching from Host DRAM, stall `Write B` until `Write A`'s DMA finishes!
  2. **Write Sequence Number (`WSN`) Assignment at Fetch Time:** Stamp each Write command with its `WSN` in strict SQ fetch order (`WSN_A < WSN_B`). When inserting into the Write Buffer CAM, if the CAM already holds an entry for `LPN 50` with a *newer* `WSN > my_wsn`, discard the older write buffer update!

#### Problem 5.2: `Read (LPN 101, FUA = 1)` When `LPN 101` Is Dirty in the Write Buffer
- **You MUST return the newest data (from the Write Buffer / after flushing it), NEVER the stale old data from NAND!**
- Once a Write command to `LPN 101` has completed, the logical block `LPN 101` legally holds the new data. If a subsequent `Read (LPN 101, FUA = 1)` returned old NAND data, that would violate basic storage coherency!
- To satisfy both coherency and `FUA = 1` (which requires reading from non-volatile media or ensuring non-volatility): when `Read (LPN 101, FUA = 1)` hits a dirty unprogrammed entry in the volatile Write Buffer, firmware first **flushes `LPN 101` to NAND** (making it non-volatile) and returns the new data!

#### Problem 5.3: Why Polling Drivers (`IEN = 0`) Still Must Write `CQyHDBL`
- Because the SSD Controller's CQE Posting Engine uses `CQCT[cqid].cq_head` (which is updated **only** when the host writes `CQyHDBL`!) to check for **CQ Full (`(cq_tail + 1) % qsize == cq_head`)**!
- If a polling host driver consumed CQEs in DRAM by checking the `Phase` bit but never wrote `CQyHDBL`, after `QSize - 1` completions the SSD controller would think the CQ is $100\%$ full and stall all future completions! (Polling drivers like SPDK batch `CQyHDBL` writes—e.g., ringing `CQyHDBL` once every $32$ or $64$ polled completions to amortize PCIe MMIO overhead while keeping the ring from filling up.)

---

### Chapter 6 Solutions

#### Problem 6.1: Exceeding the `Abort Command Limit (ACL)`
- By the NVMe Base Specification (Section 5.1), if the host submits more concurrent `Abort` commands than `Identify.ACL + 1`, HIL Firmware must immediately complete the excess `Abort` command with Command Specific Status **`Abort Command Limit Exceeded (SCT=0x01, SC=0x03, DNR=1)`**.

#### Problem 6.2: Fused Operations (`Compare and Write`, `FUSE = 01b` + `10b`)
- **(a) Mismatched `SLBA`/`NLB` or Missing Second Half:** Both commands in a Fused pair must be aborted with **`Invalid Field in Command (SCT=0x00, SC=0x02)`** (or `Command Sequence Error`).
- **(b) When the First Command (`Compare`, `FUSE=01b`) Fails (`SC=0x85 Compare Failure`):**
  - The first command (`Compare`) completes with `Compare Failure (SCT=0x02, SC=0x85)`.
  - The second command (`Write`, `FUSE=10b`) is **NOT executed** and must complete with Generic Status **`Commands Aborted due to Failed Fused Command (SCT=0x00, SC=0x09)`**!

#### Problem 6.3: PCIe Payload Efficiency (`MPS = 128B` vs. `MPS = 512B`)
- Assume $20\text{ B}$ framing overhead (TLP header + DLLP/Physical layer) per `MWr` packet:
  - **At `MPS = 128B`:** A $4096\text{ B}$ page requires $4096 / 128 = \mathbf{32\text{ TLPs}}$. Total wire bytes $= 32 \times (128 + 20) = 4,736\text{ B}$. Efficiency $= 4096 / 4736 = \mathbf{86.5\%}$.
  - **At `MPS = 512B`:** A $4096\text{ B}$ page requires $4096 / 512 = \mathbf{8\text{ TLPs}}$. Total wire bytes $= 8 \times (512 + 20) = 4,256\text{ B}$. Efficiency $= 4096 / 4256 = \mathbf{96.2\%}$ (nearly $10\%$ higher peak throughput on the exact same PCIe lanes!).

---

## Part II: Quick Reference Table for NVMe Firmware Engineers

### 1. Essential Admin Opcodes (`QID = 0`)
| Opcode | Command Name | Data Transfer | Key SQE Fields |
| :---: | :--- | :---: | :--- |
| `0x00` | `Delete I/O Submission Queue` | None | `CDW10[15:0] = QID` |
| `0x01` | `Create I/O Submission Queue` | None (allocates Host SQ) | `PRP1`, `CDW10 = {QSIZE, QID}`, `CDW11 = {CQID, QPRIO, PC}` |
| `0x02` | `Get Log Page` | SSD $\to$ Host | `PRP1/2`, `CDW10 = {NUMDL, RAE, LID}` |
| `0x04` | `Delete I/O Completion Queue` | None | `CDW10[15:0] = QID` |
| `0x05` | `Create I/O Completion Queue` | None (allocates Host CQ) | `PRP1`, `CDW10 = {QSIZE, QID}`, `CDW11 = {IV, IEN, PC}` |
| `0x06` | `Identify` | SSD $\to$ Host | `PRP1/2`, `NSID`, `CDW10[7:0] = CNS` |
| `0x08` | `Abort` | None | `CDW10 = {CID[31:16], SQID[15:0]}` |
| `0x09` | `Set Features` | Optional | `CDW10[7:0] = FID`, `CDW11 = Feature Value` |
| `0x0A` | `Get Features` | Optional | `CDW10[7:0] = FID` |
| `0x0C` | `Asynchronous Event Request` | None | Parked until event occurs! |

### 2. Essential NVM I/O Opcodes (`QID > 0`)
| Opcode | Command Name | Direction | Key SQE Fields |
| :---: | :--- | :---: | :--- |
| `0x00` | `Flush` | None | `NSID` |
| `0x01` | `Write` | Host $\to$ SSD | `NSID`, `PRP1/2`, `SLBA (CDW10-11)`, `NLB/FUA/PRINFO (CDW12)` |
| `0x02` | `Read` | SSD $\to$ Host | `NSID`, `PRP1/2`, `SLBA (CDW10-11)`, `NLB/FUA/PRINFO (CDW12)` |
| `0x05` | `Compare` | Host $\to$ SSD | `NSID`, `PRP1/2`, `SLBA`, `NLB` (often fused with Write) |
| `0x08` | `Write Zeroes` | None | `NSID`, `SLBA`, `NLB`, `DEAC` |
| `0x09` | `Dataset Management (TRIM)` | Host $\to$ SSD | `PRP1/2` (Range list), `CDW10 = NR`, `CDW11.AD = 1` (Deallocate) |

### 3. Essential NVMe Status Codes (`SCT`, `SC`)
| `SCT` | `SC` | Status Code Name | Typical Trigger in Frontend HW/FW |
| :---: | :---: | :--- | :--- |
| `0x0` | `0x00` | `Successful Completion` | Normal command completion |
| `0x0` | `0x01` | `Invalid Command Opcode` | Unrecognized `SQE.CDW0.OPC` |
| `0x0` | `0x02` | `Invalid Field in Command` | Bad `CNS`, `FID`, `MDTS` exceeded, or unsupported bit |
| `0x0` | `0x03` | `Command ID Conflict` | Duplicate in-flight `CID` on the same `SQID` |
| `0x0` | `0x07` | `Command Abort Requested` | Target I/O command aborted by Admin `Abort (0x08)` |
| `0x0` | `0x08` | `Command Aborted due to SQ Deletion` | In-flight command aborted during `Delete I/O SQ (0x00)` |
| `0x0` | `0x09` | `Command Aborted due to Failed Fused Command` | `Write` half aborted because `Compare` half failed |
| `0x0` | `0x0B` | `Invalid Namespace or Format` | Inactive or out-of-range `NSID` |
| `0x0` | `0x0C` | `Command Sequence Error` | E.g., `Set Features (Num Queues)` called after I/O Q created |
| `0x0` | `0x13` | **`PRP Offset Invalid`** | Non-zero page offset in `PRP2` (direct page) or PRP List entry |
| `0x0` | `0x80` | **`LBA Out of Range`** | `SLBA + NLB + 1 > NSZE` |
| `0x1` | `0x00` | `Completion Queue Invalid` | `Create I/O SQ` references non-existent `CQID` |
| `0x1` | `0x01` | `Invalid Queue Identifier` | `QID == 0`, `QID > Max`, or already created/deleted |
| `0x1` | `0x02` | `Invalid Queue Size` | `QSIZE == 0` or `QSIZE > CAP.MQES` |
| `0x1` | `0x03` | `Abort Command Limit Exceeded` | More than `ACL + 1` concurrent `Abort` commands |
| `0x1` | `0x05` | `Async Event Request Limit Exceeded` | More than `AERL + 1` parked `AER` commands |
| `0x1` | `0x0C` | **`Invalid Queue Deletion`** | `Delete I/O CQ` called while `bound_sq_cnt > 0` |
| `0x2` | `0x81` | `Unrecovered Read Error` | Backend LDPC ECC failed (`UECC`) on a Read slice |
| `0x2` | `0x82` | `End-to-End Guard Check Error` | PI `CRC-16` mismatch during DMA |
| `0x2` | `0x84` | `End-to-End Reference Tag Check Error` | PI `RefTag != Expected_LBA` |

---

## Part III: Standard References

1. **NVM Express® Base Specification, Revision 2.0c (2022) & NVM Express® NVM Command Set Specification, Revision 1.0c.** NVM Express, Inc.
   *(Authoritative specification for registers, queue administration, PRPs/SGLs, status codes, and state machines.)*
2. **PCI Express® Base Specification, Revision 5.0 / 6.0.** PCI-SIG.
   *(Authoritative reference for Posted vs. Non-Posted TLPs, Producer-Consumer ordering rules, Extended Tags, and Function Level Reset.)*
3. **Tavakkol, A., Gómez-Luna, J., Sadrosadati, M., Ghose, S., & Mutlu, O. (2018).** *MQSim: A framework for enabling realistic studies of modern multi-queue SSD devices.* FAST 2018.
   *(Standard architectural reference modeling multi-queue NVMe HIL, WRR arbitration, and FTL interaction.)*
4. **Gouk, D., et al. (2018).** *Amber: Enabling precise full-system simulation with detailed modeling of all SSD resources.* MICRO 2018 (SimpleSSD).
   *(Detailed breakdown of HIL CPU core execution, internal DMA engines, and SRAM buffer management inside an embedded multi-core ARM SSD controller.)*
