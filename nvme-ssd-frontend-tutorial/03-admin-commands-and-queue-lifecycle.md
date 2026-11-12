# Chapter 3: The Firmware Control Plane — Admin Commands & I/O Queue Lifecycle

While the Hardware Fast Path automates I/O command fetching and data transfers on `QID > 0`, **every single command submitted to the Admin Queue (`QID = 0`) is routed directly to HIL Firmware**.

In this chapter, we walk through how HIL Firmware parses and executes the essential Admin commands that bring an NVMe drive online:
1. **`Identify`** (`Opcode 0x06`: Controller `CNS=0x01`, Namespace `CNS=0x00`, Active Namespace ID List `CNS=0x02`);
2. **`Set Features` (`0x09`) & `Get Features` (`0x0A`)** (Queue Count negotiation `FID=0x07`, Arbitration `FID=0x01`, Volatile Write Cache `FID=0x06`, Interrupt Coalescing `FID=0x08`);
3. **`Create I/O Completion Queue` (`0x05`) & `Create I/O Submission Queue` (`0x01`)** (including physically contiguous `PC=1` vs. non-contiguous `PC=0` queues!);
4. **`Delete I/O Submission Queue` (`0x00`) & `Delete I/O Completion Queue` (`0x04`)** (and the mandatory **Queue Deletion Drain Protocol**);
5. **`Asynchronous Event Request (AER, Opcode 0x0C)`** (how firmware parks CIDs to report asynchronous thermal, SMART, or namespace alerts).

---

## 3.1 How HIL Firmware Receives and Dispatches Admin Commands (`QID = 0`)

### Intuition
When the host driver rings `SQ0TDBL`, the Hardware SQE Fetch Engine sees `QID == 0` (which has strict top priority in the arbiter), DMA-reads the 64-byte Admin SQE from Host DRAM into an internal Admin Command Slot in Controller SRAM, and asserts `IRQ_ADMIN_SQE_ARRIVED` to the HIL CPU core.

### The Universal 64-Byte Admin SQE Header
Every Admin and NVM command shares the exact same 64-byte (16 Dword) layout:

| Dwords | Byte Offset | Field Name | Meaning & Firmware Usage |
| :--- | :--- | :--- | :--- |
| `CDW0` | `00..03` | `OPC [7:0]`, `FUSE [9:8]`, `PSDT [15:14]`, `CID [31:16]` | Opcode, Fused flag, PRP/SGL indicator (`00b` = PRP), and 16-bit Command ID. |
| `NSID` | `04..07` | Namespace Identifier | `0x00000000` (if not applicable), `1..N` (specific namespace), or `0xFFFFFFFF` (broadcast). |
| `CDW2–3` | `08..15` | Reserved | — |
| `MPTR` | `16..23` | Metadata Pointer (64-bit) | Unused for Admin commands. |
| `DPTR` | `24..39` | `PRP1` (`24..31`) + `PRP2` (`32..39`) | 64-bit Host DRAM physical address(es) for the 4 KiB Admin data payload (e.g., `Identify` buffer). |
| `CDW10–15` | `40..63` | Command-Specific Dwords | Parameters for the specific Admin Opcode (`CNS`, `FID`, `QID`, `QSIZE`, etc.). |

---

## 3.2 `Identify` (`Opcode 0x06`): Reporting Controller & Namespace Capabilities

### Intuition
Immediately after `CSTS.RDY == 1`, the very first command the host OS sends is `Identify Controller` (`CDW10.CNS = 0x01`), followed by `Identify Active Namespace ID List` (`CNS = 0x02`) and `Identify Namespace` (`CNS = 0x00`, `NSID = 1`).
In each case, the host passes a 4 KiB Host DRAM buffer in `PRP1` (and `PRP2` if the 4 KiB buffer crosses a host page boundary), and HIL Firmware must populate a 4096-byte structure in internal Controller SRAM and trigger the Frontend DMA engine to push those 4096 bytes to the host before posting the Admin CQE.

### Key Fields HIL Firmware Must Populate

1. **`Identify Controller` (`CNS = 0x01`, 4096 Bytes):**
   - `Bytes [01:00]` (`VID`): PCI Vendor ID (e.g., `0x144D` Samsung, `0x8086` Intel).
   - `Bytes [23:04]` (`SN`): 20-byte ASCII Serial Number (space-padded, not null-terminated!).
   - `Bytes [63:24]` (`MN`): 40-byte ASCII Model Number.
   - `Bytes [71:64]` (`FR`): 8-byte ASCII Firmware Revision.
   - `Byte 77` (`MDTS`): **Maximum Data Transfer Size** in units of the minimum host page size ($2^{\text{MDTS}} \times 2^{12 + \text{CAP.MPSMIN}}$). *Crucial for Firmware:* If your internal Command Slot / PRP table can only handle up to $256\text{ KiB}$ ($64$ pages of $4\text{ KiB}$) per command, you set `MDTS = 6` ($2^6 \times 4\text{ KiB} = 256\text{ KiB}$) so the host OS block layer automatically splits any larger I/O!
   - `Bytes [259:258]` (`OACS`): Optional Admin Command Support (Firmware Commit, Format NVM, Security).
   - `Byte 262` (`AERL`): **Async Event Request Limit** (0's-based! E.g., `3` means the host may park up to $4$ concurrent `AER` commands in your firmware).
   - `Byte 512` (`SQES`): Required/Max I/O SQ Entry Size (`0x66` $\implies \min = 2^6 = 64\text{ B}, \max = 2^6 = 64\text{ B}$).
   - `Byte 513` (`CQES`): Required/Max I/O CQ Entry Size (`0x44` $\implies \min = 2^4 = 16\text{ B}, \max = 2^4 = 16\text{ B}$).
   - `Bytes [519:516]` (`NN`): **Number of Namespaces** supported by the controller (e.g., `1`).
   - `Byte 524` (`VWC`): **Volatile Write Cache** (`Bit 0 = 1` tells the host your SSD uses DRAM/SRAM write caching and supports the `Flush` command!).
   - `Bytes [539:536]` (`SGLS`): **SGL Support** (`Bit 0 = 1` if your DMA hardware supports SGLs for NVM commands).

2. **`Identify Namespace` (`CNS = 0x00, NSID = 1`, 4096 Bytes):**
   - `Bytes [07:00]` (`NSZE`): **Namespace Size** in logical blocks (e.g., for a $1\text{ TiB}$ drive with $4\text{ KiB}$ blocks, $\text{NSZE} = 268,435,456$). *Note:* HIL Firmware copies `NSZE` into a fast hardware register so the Command Validator can check `SLBA + NLB < NSZE` on every Read/Write!
   - `Bytes [15:08]` (`NCAP`): Namespace Capacity.
   - `Byte 26` (`FLBAS`): **Formatted LBA Size** index (`Bits [3:0]` select an entry in the `LBAF0..15` table at bytes `128..191`).
   - `Bytes [131:128]` (`LBAF0`): LBA Format 0 (`MS [15:0]` = Metadata Size in bytes, e.g., `0` or `8`; `LBADS [23:16]` = LBA Data Size as $2^{\text{LBADS}}$, where `LBADS = 9` $\implies 512\text{ B}$ and **`LBADS = 12` $\implies 4096\text{ B}$**).

---

## 3.3 `Set Features` (`0x09`) & `Get Features` (`0x0A`): Negotiating Queues & Policies

Before creating I/O queues, the host driver sends `Set Features` with **Feature Identifier `FID = 0x07` (Number of Queues)**:
- **Host Request (`CDW10 = 0x07`, `CDW11`):**
  - `CDW11[15:0]` (`NSQR`): Number of I/O Submission Queues Requested (**0's-based**! E.g., on a 16-core CPU, the host requests `15` $\implies 16$ I/O SQs).
  - `CDW11[31:16]` (`NCQR`): Number of I/O Completion Queues Requested (**0's-based**!).
- **HIL Firmware Response (Returned directly in `CQE.DW0`!):**
  - Notice that `Set Features (FID=0x07)` does not transfer a data buffer; instead, firmware writes the allocated counts into **`CQE.DW0`**:
    - `CQE.DW0[15:0]` (`NSQA`): Number of I/O SQs Allocated (0's-based, e.g., $\min(\text{NSQR}, \text{MaxSupportedSQs} - 1)$).
    - `CQE.DW0[31:16]` (`NCQA`): Number of I/O CQs Allocated (0's-based).
  - *Spec Rule:* If the host tries to call `Set Features (FID=0x07)` *after* any I/O Queue has already been created, firmware must reject it with `Command Sequence Error (SCT=0x00, SC=0x0C)`!

Other critical `Set Features` (`FID`) handlers in HIL Firmware:
- **`FID = 0x01` (Arbitration):** Programs `AB` (Arbitration Burst) and the WRR weights `LPW`, `MPW`, `HPW` directly into the Hardware WRR Arbiter registers.
- **`FID = 0x06` (Volatile Write Cache):** `CDW11[0] = WCE` (Write Cache Enable). If the host sets `WCE = 0`, firmware must flush all dirty DRAM write buffers to NAND and switch the Write Pipeline from *Early Completion* to *Post-NAND-Program Completion* (like `FUA` on every write!).
- **`FID = 0x08` (Interrupt Coalescing):** Programs `THR` (aggregation threshold of CQEs) and `TIME` (aggregation timeout in $100\ \mu\text{s}$ increments) into the Hardware MSI-X Coalescing timer.

---

## 3.4 Creating & Deleting I/O Queues: Step-by-Step Firmware Implementation

### 1. Mandatory Creation Order: **`Create I/O CQ` (`0x05`) FIRST, Then `Create I/O SQ` (`0x01`)!**
Why must the host create a Completion Queue *before* creating any Submission Queue that points to it?
Because `Create I/O SQ` passes `CQID` in `CDW11[31:16]`. If the host tries to create an SQ pointing to a `CQID` that does not exist yet (`CQCT[cqid].valid == 0`), HIL Firmware **must reject `Create I/O SQ`** with Command Specific Status **`Completion Queue Invalid (SCT=0x01, SC=0x00)`**!

### 2. `Create I/O Completion Queue` (`Opcode 0x05`) Handler
- **Inputs in SQE:**
  - `PRP1`: 64-bit Host DRAM physical address of CQ buffer (if `PC == 1`) or PRP List of pages (if `PC == 0`).
  - `CDW10[15:0]` (`QID`): Completion Queue ID to create (`1 .. NCQA + 1`).
  - `CDW10[31:16]` (`QSIZE`): Queue Size (**0's-based**! E.g., `1023` means $1024$ entries).
  - `CDW11[0]` (`PC`): Physically Contiguous (`1` = single contiguous buffer in Host DRAM; `0` = non-contiguous, `PRP1` points to a PRP List of page addresses!).
  - `CDW11[1]` (`IEN`): Interrupts Enabled (`1` = enable MSI-X for this CQ).
  - `CDW11[31:16]` (`IV`): MSI-X Interrupt Vector (`0 .. MaxVectors - 1`).
- **Firmware Validation Checks (Return `SCT=0x01` Command Specific Errors on failure):**
  1. Is `QID == 0` or `QID > max_cqs` or `CQCT[QID].valid == 1`? $\to$ Return `Invalid Queue Identifier (SC=0x01)`.
  2. Is `QSIZE == 0` (meaning 1 slot, which can hold $0$ items!) or `QSIZE > CAP.MQES`? $\to$ Return `Invalid Queue Size (SC=0x02)`.
  3. Is `IV > max_msix_vector`? $\to$ Return `Invalid Interrupt Vector (SC=0x08)`.
  4. Is `PC == 0` when `CAP.CQR == 1`? $\to$ Return `Invalid Field in Command (SCT=0x00, SC=0x02)`.
- **Programming `CQCT[QID]`:**
  - If `PC == 0` (Non-Contiguous Queue): Firmware instructs the DMA engine to fetch the Queue's PRP List from `PRP1` into an internal **Queue Page Table SRAM** so the CQE Posting Engine can translate `cq_tail` into the right physical page!
  - Initialize `CQCT[QID]`: `base_addr = PRP1`, `qsize = QSIZE + 1`, `cq_head = 0`, `cq_tail = 0`, **`phase_bit = 1`**, `iv = IV`, `ien = IEN`, `bound_sq_cnt = 0`, `valid = 1`.
  - Clear BAR0 Doorbell `CQ[QID]HDBL = 0`.

### 3. `Create I/O Submission Queue` (`Opcode 0x01`) Handler
- **Inputs in SQE:**
  - `PRP1`: 64-bit Host DRAM physical address of SQ buffer (or PRP List if `PC == 0`).
  - `CDW10[15:0]` (`QID`): Submission Queue ID (`1 .. NSQA + 1`).
  - `CDW10[31:16]` (`QSIZE`): Queue Size (**0's-based**!).
  - `CDW11[0]` (`PC`): Physically Contiguous.
  - `CDW11[2:1]` (`QPRIO`): Queue Priority (`00b` = Urgent, `01b` = High, `10b` = Medium, `11b` = Low).
  - `CDW11[31:16]` (`CQID`): Associated Completion Queue ID (`1 .. max_cqs`).
- **Firmware Validation Checks:**
  1. **Check `CQID` first:** Is `CQID == 0` or `CQID > max_cqs` or `CQCT[CQID].valid == 0`? $\to$ Return **`Completion Queue Invalid (SCT=0x01, SC=0x00)`**.
  2. Is `QID == 0` or `QID > max_sqs` or `SQCT[QID].valid == 1`? $\to$ Return `Invalid Queue Identifier (SCT=0x01, SC=0x01)`.
  3. Is `QSIZE == 0` or `QSIZE > CAP.MQES`? $\to$ Return `Invalid Queue Size (SCT=0x01, SC=0x02)`.
- **Programming `SQCT[QID]`:**
  - Initialize `SQCT[QID]`: `base_addr = PRP1`, `qsize = QSIZE + 1`, `sq_head = 0`, `sq_tail = 0`, `cqid = CQID`, `prio_class = QPRIO`, `in_flight_cnt = 0`, `draining = 0`, `valid = 1`.
  - Increment **`CQCT[CQID].bound_sq_cnt++`**!
  - Clear BAR0 Doorbell `SQ[QID]TDBL = 0`.

### 4. Mandatory Deletion Order & The SQ Deletion Drain Protocol (`Delete I/O SQ` `0x00` $\to$ `Delete I/O CQ` `0x04`)
When tearing down queues, the order is **strictly reversed**: the host must delete **all** Submission Queues bound to a Completion Queue *before* deleting that Completion Queue!

- **`Delete I/O Completion Queue` (`Opcode 0x04`, `CDW10[15:0] = QID`):**
  1. Check `CQCT[QID].valid == 1` (and `QID != 0`).
  2. **Check `CQCT[QID].bound_sq_cnt == 0`!** If `bound_sq_cnt > 0` (meaning at least one I/O SQ is still pointing to this CQ), HIL Firmware **must reject the command** with **`Invalid Queue Deletion (SCT=0x01, SC=0x0C)`**!
  3. Otherwise, set `CQCT[QID].valid = 0` and post the Admin CQE on `CQ 0`.

- **`Delete I/O Submission Queue` (`Opcode 0x00`, `CDW10[15:0] = QID`):**
  What if there are still $32$ Read/Write commands in flight on `SQ[QID]` when the host sends `Delete I/O SQ`?
  The NVMe Specification (Section 5.8) requires the controller to **abort or complete all in-flight commands associated with `SQ[QID]` BEFORE posting the Admin CQE for `Delete I/O SQ`**!
  Here is the exact **4-Step SQ Deletion Drain State Machine** in HIL Firmware:
  1. Set `SQCT[QID].draining = 1` (this immediately tells the Hardware WRR Arbiter and SQE Fetch Engine to stop fetching any new commands from `SQ[QID]`).
  2. Scan all active `CmdSlot` entries in Controller SRAM with `slot.sqid == QID`: mark them for fast abort (or wait for their FTL/DMA operations to finish and post their CQEs with status `Command Aborted due to SQ Deletion` or normal completion to `CQ[SQCT[QID].cqid]`).
  3. **Suspend the `Delete I/O SQ` Admin command** in an asynchronous wait list until `SQCT[QID].in_flight_cnt == 0`!
  4. The moment `SQCT[QID].in_flight_cnt` hits `0`:
     - Decrement `CQCT[SQCT[QID].cqid].bound_sq_cnt--`.
     - Set `SQCT[QID].valid = 0`.
     - Post the Admin CQE for `Delete I/O SQ` to **Admin Completion Queue `CQ 0`**!

---

## 3.5 Asynchronous Event Requests (`AER`, Opcode `0x0C`): Parking Commands in Firmware

### Intuition
How can an SSD proactively notify the host OS that its temperature just crossed $85^\circ\text{C}$, or a spare NAND block count dropped below threshold, when NVMe has no "unsolicited command" channel from SSD to Host?
NVMe solves this brilliantly: during initialization, the host submits $N$ (typically $4$, up to `AERL + 1`) **`Asynchronous Event Request (AER, Opcode 0x0C)`** commands to the Admin Queue (`SQ 0`).
- When HIL Firmware receives an `AER` command, **it does NOT complete it!**
- Instead, firmware **parks** the command's `CID` in a small internal array `g_parked_aer_cids[]` (with no timeout!).
- Hours or days later, when the thermal sensor or FTL triggers an alert (e.g., `Temperature > Threshold`), HIL Firmware pops one parked `CID` from `g_parked_aer_cids[]`, packs the Event Type, Event Info, and Log Page ID (`0x02` = SMART/Health Log) into `CQE.DW0`, and posts the CQE to `CQ 0`!
- Upon receiving the `AER` completion, the host driver reads the specified Log Page via `Get Log Page (Opcode 0x02)` and submits a fresh `AER` command to replenish the parked pool.
- *(Spec Rule):* If the host submits more than `AERL + 1` concurrent `AER` commands, firmware must immediately reject the excess command with **`Asynchronous Event Request Limit Exceeded (SCT=0x01, SC=0x05)`**.

---

## 3.6 Runnable HIL Firmware Control-Plane Simulation in Python

Run this self-contained script to test our HIL Firmware Control Plane across `Identify`, `Set Features (Number of Queues)`, `Create/Delete I/O CQ/SQ` (including catching illegal creation/deletion orders and draining in-flight I/Os on `Delete SQ`), and `AER` parking/firing:

```python
import struct

# NVMe Status Codes: (SCT, SC)
SC_SUCCESS                = (0x00, 0x00)
SC_INVALID_FIELD          = (0x00, 0x02)
SC_CMD_SEQ_ERROR          = (0x00, 0x0C)
SC_CQ_INVALID             = (0x01, 0x00)
SC_QID_INVALID            = (0x01, 0x01)
SC_QSIZE_INVALID          = (0x01, 0x02)
SC_AER_LIMIT_EXCEEDED     = (0x01, 0x05)
SC_INVALID_QUEUE_DELETION = (0x01, 0x0C)

class HILAdminControlPlane:
    def __init__(self, max_io_q=8, mqes=1023, aerl=3):
        self.max_io_q = max_io_q
        self.mqes = mqes          # 0-based max queue size (1023 -> 1024 entries)
        self.aerl = aerl          # 0-based AER limit (3 -> max 4 parked AERs)
        self.allocated_nsqa = 0   # 0-based allocated SQs
        self.allocated_ncqa = 0   # 0-based allocated CQs
        self.sqct = {}
        self.cqct = {}
        self.parked_aers = []     # List of parked Admin CIDs

    def process_admin_sqe(self, opc: int, cid: int, nsid: int = 0, prp1: int = 0, cdw10: int = 0, cdw11: int = 0):
        if opc == 0x06:    # Identify
            return self._handle_identify(cid, nsid, prp1, cdw10)
        elif opc == 0x09:  # Set Features
            return self._handle_set_features(cid, cdw10, cdw11)
        elif opc == 0x05:  # Create I/O CQ
            return self._handle_create_io_cq(cid, prp1, cdw10, cdw11)
        elif opc == 0x01:  # Create I/O SQ
            return self._handle_create_io_sq(cid, prp1, cdw10, cdw11)
        elif opc == 0x00:  # Delete I/O SQ
            return self._handle_delete_io_sq(cid, cdw10)
        elif opc == 0x04:  # Delete I/O CQ
            return self._handle_delete_io_cq(cid, cdw10)
        elif opc == 0x0C:  # Async Event Request (AER)
            return self._handle_aer(cid)
        return (cid, 0, SC_INVALID_FIELD)

    def _handle_identify(self, cid: int, nsid: int, prp1: int, cdw10: int):
        cns = cdw10 & 0xFF
        buf = bytearray(4096)
        if cns == 0x01:  # Identify Controller
            struct.pack_into("<H", buf, 0, 0x1B4B)                 # VID
            buf[4:24] = b"SN-NVME-TUTORIAL-01 "                    # SN (20B)
            buf[24:64] = b"Antigravity Virtual NVMe Controller     "  # MN (40B)
            buf[64:72] = b"FW2.0.01"                               # FR (8B)
            buf[77] = 6                                            # MDTS = 6 (2^6 * 4KiB = 256KiB)
            buf[262] = self.aerl                                   # AERL = 3 (4 AERs max)
            buf[512] = 0x66                                        # SQES = 64B
            buf[513] = 0x44                                        # CQES = 16B
            struct.pack_into("<I", buf, 516, 1)                    # NN = 1 namespace
            return (cid, len(buf), SC_SUCCESS)
        elif cns == 0x00 and nsid == 1:  # Identify Namespace 1
            nsze = 268435456  # 1 TiB in 4 KiB logical blocks
            struct.pack_into("<QQQ", buf, 0, nsze, nsze, nsze)
            buf[26] = 0       # FLBAS = LBAF0
            struct.pack_into("<I", buf, 128, (12 << 16) | 0)       # LBAF0: LBADS=12 (4096B), MS=0
            return (cid, nsze, SC_SUCCESS)
        return (cid, 0, SC_INVALID_FIELD)

    def _handle_set_features(self, cid: int, cdw10: int, cdw11: int):
        fid = cdw10 & 0xFF
        if fid == 0x07:  # Number of Queues
            if self.sqct or self.cqct:
                return (cid, 0, SC_CMD_SEQ_ERROR)
            nsqr = cdw11 & 0xFFFF
            ncqr = (cdw11 >> 16) & 0xFFFF
            self.allocated_nsqa = min(nsqr, self.max_io_q - 1)
            self.allocated_ncqa = min(ncqr, self.max_io_q - 1)
            dw0 = (self.allocated_ncqa << 16) | self.allocated_nsqa
            return (cid, dw0, SC_SUCCESS)
        return (cid, 0, SC_SUCCESS)

    def _handle_create_io_cq(self, cid: int, prp1: int, cdw10: int, cdw11: int):
        qid = cdw10 & 0xFFFF
        qsize_0 = (cdw10 >> 16) & 0xFFFF
        if qid == 0 or qid > self.allocated_ncqa + 1 or qid in self.cqct:
            return (cid, 0, SC_QID_INVALID)
        if qsize_0 == 0 or qsize_0 > self.mqes:
            return (cid, 0, SC_QSIZE_INVALID)
        self.cqct[qid] = {"base": prp1, "qsize": qsize_0 + 1, "bound_sq_cnt": 0}
        return (cid, 0, SC_SUCCESS)

    def _handle_create_io_sq(self, cid: int, prp1: int, cdw10: int, cdw11: int):
        qid = cdw10 & 0xFFFF
        qsize_0 = (cdw10 >> 16) & 0xFFFF
        cqid = (cdw11 >> 16) & 0xFFFF
        if cqid not in self.cqct:
            return (cid, 0, SC_CQ_INVALID)
        if qid == 0 or qid > self.allocated_nsqa + 1 or qid in self.sqct:
            return (cid, 0, SC_QID_INVALID)
        if qsize_0 == 0 or qsize_0 > self.mqes:
            return (cid, 0, SC_QSIZE_INVALID)
        self.sqct[qid] = {"base": prp1, "qsize": qsize_0 + 1, "cqid": cqid, "in_flight": 0}
        self.cqct[cqid]["bound_sq_cnt"] += 1
        return (cid, 0, SC_SUCCESS)

    def _handle_delete_io_cq(self, cid: int, cdw10: int):
        qid = cdw10 & 0xFFFF
        if qid not in self.cqct:
            return (cid, 0, SC_QID_INVALID)
        if self.cqct[qid]["bound_sq_cnt"] > 0:
            return (cid, 0, SC_INVALID_QUEUE_DELETION)  # Must delete bound SQs first!
        del self.cqct[qid]
        return (cid, 0, SC_SUCCESS)

    def _handle_delete_io_sq(self, cid: int, cdw10: int):
        qid = cdw10 & 0xFFFF
        if qid not in self.sqct:
            return (cid, 0, SC_QID_INVALID)
        sq = self.sqct[qid]
        # Drain any in-flight I/Os on this SQ before completing Delete I/O SQ!
        drained = sq["in_flight"]
        sq["in_flight"] = 0
        self.cqct[sq["cqid"]]["bound_sq_cnt"] -= 1
        del self.sqct[qid]
        return (cid, drained, SC_SUCCESS)

    def _handle_aer(self, cid: int):
        if len(self.parked_aers) >= self.aerl + 1:
            return (cid, 0, SC_AER_LIMIT_EXCEEDED)
        self.parked_aers.append(cid)
        return None  # Parked! No CQE posted until an async event occurs!

    def trigger_thermal_async_event(self):
        assert self.parked_aers, "No parked AER CID available!"
        aer_cid = self.parked_aers.pop(0)
        # DW0: EventType=1 (SMART/Health), EventInfo=1 (Temp Threshold), LogPageID=0x02
        dw0 = (0x02 << 16) | (0x01 << 8) | 0x01
        return (aer_cid, dw0, SC_SUCCESS)

fw = HILAdminControlPlane(max_io_q=8)
print("1. Identify Controller:", fw.process_admin_sqe(opc=0x06, cid=1, cdw10=0x01))
print("2. Negotiate 16 Qs (capped to 8 -> 0-based 7):",
      fw.process_admin_sqe(opc=0x09, cid=2, cdw10=0x07, cdw11=(15 << 16) | 15))
print("3. Try Create SQ1 BEFORE CQ1 exists (Expect SC_CQ_INVALID=(1, 0)):",
      fw.process_admin_sqe(opc=0x01, cid=3, cdw10=(255 << 16) | 1, cdw11=(1 << 16) | 1))
print("4. Create CQ1 (size 256):", fw.process_admin_sqe(opc=0x05, cid=4, cdw10=(255 << 16) | 1, cdw11=1))
print("5. Create SQ1 bound to CQ1:", fw.process_admin_sqe(opc=0x01, cid=5, cdw10=(255 << 16) | 1, cdw11=(1 << 16) | 1))
print("6. Try Delete CQ1 while SQ1 still bound (Expect SC_INVALID_QUEUE_DELETION=(1, 12)):",
      fw.process_admin_sqe(opc=0x04, cid=6, cdw10=1))
fw.sqct[1]["in_flight"] = 5  # Simulate 5 in-flight I/Os on SQ1
print("7. Delete SQ1 (drains 5 I/Os first):", fw.process_admin_sqe(opc=0x00, cid=7, cdw10=1))
print("8. Delete CQ1 (now succeeds):", fw.process_admin_sqe(opc=0x04, cid=8, cdw10=1))

# Park 4 AERs, verify 5th is rejected, then trigger a SMART Thermal Event
for cid in range(100, 104):
    assert fw.process_admin_sqe(opc=0x0C, cid=cid) is None
print("9. 5th AER (Expect SC_AER_LIMIT_EXCEEDED=(1, 5)):", fw.process_admin_sqe(opc=0x0C, cid=104))
print("10. Fire Thermal Event (completes parked CID=100):", fw.trigger_thermal_async_event())
```

---

## 3.7 Check Your Understanding (Firmware Design Problems)

*(Full step-by-step solutions are in [Chapter 99](./99-solutions-and-references.md).)*

1. **The 0's-Based vs. 1's-Based Trap:** In the NVMe specification, `CAP.MQES`, `AQA.ASQS`, `AQA.ACQS`, `Create I/O SQ/CQ QSIZE`, `Set Features (Number of Queues) NSQR/NCQR`, `Identify.AERL`, and `NVM Read/Write NLB` are all **0's-based** (where value $v$ means $v + 1$). Why did the NVMe architects make `QSIZE` and `NLB` 0's-based in a 16-bit field, and what happens if a host sends `Create I/O SQ` with `QSIZE = 0x0000`?
2. **Non-Contiguous I/O Queues (`PC = 0`):** Suppose your controller sets `CAP.CQR = 0` (supporting physically non-contiguous I/O queues) and the host creates a $1024$-entry Submission Queue ($1024 \times 64\text{ B} = 64\text{ KiB} = 16$ pages of $4\text{ KiB}$) with `PC = 0`. What does `PRP1` in the `Create I/O SQ` command point to, and how does the SQE Fetch Engine compute the Host DRAM physical address of `sq_head = 300`?
3. **Duplicate `AER` Event Masking:** Once HIL Firmware completes a parked `AER` command to report a `Temperature > Threshold` event (Log Page `0x02`), why must firmware **mask** further `Temperature` async events until the host reads Log Page `0x02` via `Get Log Page (Opcode 0x02)` (with `RAE = 0`, Retain Asynchronous Event cleared)? What would happen to the host's remaining 3 parked AERs within microseconds if firmware didn't mask that event source?
