# Chapter 2: Queue Context Tables (QCT), Doorbells & HW Fetch Engines

Once `CSTS.RDY = 1`, the host starts submitting commands by writing 64-byte Submission Queue Entries (SQEs) into Host DRAM and poking 32-bit BAR0 Doorbell registers (`SQyTDBL`).

How does your SSD Controller track dozens (or thousands) of active queues simultaneously, arbitrate fairly among them, fetch commands over PCIe without stalling, and post completions without ever overwriting an unconsumed Completion Queue Entry (CQE)? In this chapter, we open up the **Queue Context Table (`QCT`)**, the **Doorbell & Arbitration Engine**, the **Phase Tag (`P` bit) state machine**, and **CQ Full backpressure**.

---

## 2.1 Producer-Consumer Ring Buffers & Who Owns Which Pointer

### Intuition
Every NVMe Submission Queue (SQ) and Completion Queue (CQ) is a circular ring buffer living in **Host Physical DRAM**. Neither the host nor the SSD ever copies the whole ring across PCIe; instead, each side maintains **Head** (consumer) and **Tail** (producer) index pointers in `[0, QSize - 1]`.

As a Firmware Engineer, you must burn this ownership table into memory:

| Ring Buffer | Entry Size | Producer (`Tail` Owner) | Consumer (`Head` Owner) | How Producer Notifies Consumer |
| :--- | :--- | :--- | :--- | :--- |
| **Submission Queue (`SQ`)** | $64\text{ B}$ (`2^IOSQES`) | **Host Driver** (increments `SQ_Tail`) | **SSD Controller** (increments `SQ_Head`) | Host writes new `SQ_Tail` to BAR0 **`SQyTDBL`** Doorbell. SSD piggybacks its current **`SQ_Head`** inside every 16B `CQE`! |
| **Completion Queue (`CQ`)** | $16\text{ B}$ (`2^IOCQES`) | **SSD Controller** (increments `CQ_Tail`) | **Host Driver** (increments `CQ_Head`) | SSD flips the **Phase Tag (`P` bit)** in `CQE.DW3[16]` (+ optional MSI-X). Host writes new `CQ_Head` to BAR0 **`CQyHDBL`** Doorbell. |

### Ring Full vs. Ring Empty Math (Modulo Arithmetic)
For any circular ring of capacity $Q$ entries (indexed $0, 1, \dots, Q - 1$), one slot must always remain unused so that `Head == Tail` unambiguously means **Empty**:
- **Maximum usable entries in a ring of size $Q$:** $Q - 1$.
- **Ring is Empty:**
  $$\text{Head} == \text{Tail}$$
- **Number of Pending Entries in Ring:**
  $$\text{Count} = (\text{Tail} - \text{Head}) \bmod Q$$
- **Ring is Full:**
  $$(\text{Tail} + 1) \bmod Q == \text{Head} \quad (\text{i.e., } \text{Count} == Q - 1)$$

---

## 2.2 Inside the Controller SRAM: The Queue Context Table (`SQCT` & `CQCT`)

### Intuition
Where do `SQ_Head`, `SQ_Tail`, `CQ_Head`, `CQ_Tail`, and the queue base addresses actually live inside the SSD?
They live in a dedicated dual-port hardware SRAM table inside the NVMe Frontend ASIC called the **Queue Context Table (`QCT`)**, split into the **Submission Queue Context Table (`SQCT`)** and **Completion Queue Context Table (`CQCT`)**.
- **HIL Firmware** initializes an `SQCT[qid]` or `CQCT[qid]` entry when processing `Create I/O SQ` / `Create I/O CQ` (or at `CC.EN: 0 -> 1` for `QID = 0`).
- **Frontend Hardware Engines** (Doorbell Latch, WRR Arbiter, SQE Fetch Engine, CQE Posting Engine) read and update `Head`, `Tail`, and `Phase` atomically on every command!

### Exact C Struct Layout of `SQCT_Entry_t` and `CQCT_Entry_t` in Controller SRAM

```c
// Stored in Frontend Controller SRAM: 32 bytes per Submission Queue
typedef struct {
    uint64_t base_addr;       // 64-bit Host DRAM base address (or PRP List addr if PC==0)
    uint16_t qsize;           // Number of entries (1-based: e.g., 1024)
    uint16_t sq_head;         // Owned & incremented by SSD SQE Fetch Engine
    uint16_t sq_tail;         // Latched directly from BAR0 SQyTDBL write by Host
    uint16_t cqid;            // Associated Completion Queue ID (Many-to-1 allowed: N SQs -> 1 CQ)
    uint8_t  prio_class;      // 00b=Urgent, 01b=High, 10b=Medium, 11b=Low (for WRR Arbiter)
    uint8_t  pc_bit     : 1;  // 1 = Physically Contiguous in Host DRAM, 0 = Non-Contiguous (PRP list)
    uint8_t  valid      : 1;  // 1 = Queue active, 0 = Unallocated or deleting
    uint8_t  draining   : 1;  // 1 = Delete I/O SQ in progress (stop fetching, drain in-flight!)
    uint8_t  reserved   : 5;
    uint16_t in_flight_cnt;   // Number of commands fetched from this SQ not yet completed (for Delete drain)
    uint8_t  pad[12];
} SQCT_Entry_t;

// Stored in Frontend Controller SRAM: 32 bytes per Completion Queue
typedef struct {
    uint64_t base_addr;       // 64-bit Host DRAM base address (or PRP List addr if PC==0)
    uint16_t qsize;           // Number of entries (1-based: e.g., 1024)
    uint16_t cq_head;         // Latched directly from BAR0 CQyHDBL write by Host
    uint16_t cq_tail;         // Owned & incremented by SSD CQE Posting Engine
    uint16_t iv;              // MSI-X Interrupt Vector number (0 .. NumVectors-1)
    uint8_t  phase_bit  : 1;  // Current Producer Phase Tag (Initialized to 1, flips on cq_tail wrap!)
    uint8_t  ien        : 1;  // Interrupts Enabled (1 = MSI-X active, 0 = Host polling only)
    uint8_t  pc_bit     : 1;  // 1 = Physically Contiguous
    uint8_t  valid      : 1;  // 1 = Queue active
    uint8_t  reserved   : 4;
    uint8_t  rsvd_align;      // Explicit alignment padding before 16-bit bound_sq_cnt
    uint16_t bound_sq_cnt;    // Reference count of SQs mapped to this CQ (must be 0 to Delete CQ!)
    uint16_t unack_cqe_cnt;   // Unacknowledged completions since last CQyHDBL write (for IRQ coalescing)
    uint8_t  pad[10];
} CQCT_Entry_t;
```

> **Look at `in_flight_cnt` in `SQCT` and `bound_sq_cnt` in `CQCT`:**
> Those two counters are lifesavers for HIL Firmware!
> - When the host sends `Delete I/O CQ (CQID=1)`, the NVMe spec mandates that if *any* I/O SQ is still associated with `CQID=1`, firmware must reject the deletion with `Invalid Queue Deletion (SCT=0x01, SC=0x0C)`. Checking `CQCT[1].bound_sq_cnt > 0` makes that an $O(1)$ single-cycle check!
> - When the host sends `Delete I/O SQ (SQID=1)`, firmware sets `SQCT[1].draining = 1` (stopping the Fetch Engine on `SQID=1`) and waits until `SQCT[1].in_flight_cnt == 0` before completing the Admin `Delete I/O SQ` command!

---

## 2.3 What Happens When the Doorbell Rings & How WRR Arbitration Works

### Step-by-Step Hardware Pipeline on `SQyTDBL` Write
Suppose the host CPU submits 4 new commands to `SQ 3` (moving `SQ_Tail` from `10` to `14`) and executes a 32-bit MMIO store to `BAR0 + 0x1018` (`SQ3TDBL = 14`):

1. **Doorbell Latch & Legality Check:**
   - The PCIe Endpoint receives the 4-byte `MWr` TLP and extracts `QID = 3` and `NewTail = 14`.
   - Hardware checks `SQCT[3].valid == 1`, `SQCT[3].draining == 0`, and `NewTail < SQCT[3].qsize`.
   - *(Spec Edge Case — Invalid Doorbell Write):* If `NewTail == SQCT[3].sq_tail` (a redundant doorbell write), hardware simply ignores it as a no-op. If `NewTail >= SQCT[3].qsize` or `NewTail` overtakes `sq_head`, hardware ignores the write and raises an interrupt to HIL FW to post an **Asynchronous Event (`Invalid Doorbell Write Value`)** if configured!
2. **Update `SQCT[3].sq_tail` & Set Active Bit in Arbitration Bitmap:**
   - Hardware sets `SQCT[3].sq_tail = 14`.
   - Since `sq_head (10) != sq_tail (14)`, `SQ 3` now has `(14 - 10) = 4` pending SQEs. Hardware sets bit `3` in the **Active SQ Bitmap** corresponding to `SQCT[3].prio_class`.
3. **Queue Arbitration (Round Robin vs. Weighted Round Robin with Urgent Priority):**
   The NVMe Spec defines two hardware arbitration mechanisms (`CC.AMS`):
   - **Round Robin (`CC.AMS = 000b`):** All active SQs (except Admin `QID=0`, which always has highest priority) are visited in cyclic order, fetching up to `Arbitration Burst (AB = 2^n)` commands per visit.
   - **Weighted Round Robin with Urgent Priority Class (`CC.AMS = 001b`):**
     ```
     [Admin SQ (QID=0)]  ---> Strict Priority 1 (Always served first)
             | (when empty)
             v
     [Urgent Priority SQs] -> Strict Priority 2 (Round-Robin among Urgent SQs)
             | (when empty)
             v
     [Weighted Round-Robin Deficit Counter Loop]
        +-- High Priority SQs   (Weight = HPW + 1, from Feature ID 0x01)
        +-- Medium Priority SQs (Weight = MPW + 1)
        +-- Low Priority SQs    (Weight = LPW + 1)
     ```
4. **SQE DMA Fetch & Command Slot (`CmdTag`) Allocation:**
   - Before issuing a PCIe `MRd` for `SQ 3`, the Fetch Engine checks if at least one internal **Command Slot (`CmdTag` in `0..MaxTags-1`)** is free in Controller SRAM.
   - If a `CmdTag` is free, the Fetch Engine calculates the Host DRAM address of the next SQE (or batch of up to $\min(\text{pending}, \text{Burst}, \text{to\_wrap})$ contiguous SQEs):
     $$\text{HostAddr} = \text{SQCT}[3].\text{base\_addr} + 64 \times \text{SQCT}[3].\text{sq\_head}$$
   - It increments `SQCT[3].sq_head = (sq_head + 1) % qsize`, increments `SQCT[3].in_flight_cnt++`, and sends a Non-Posted PCIe `MRd` (64 bytes, tagged with `CmdTag`).
   - When the `CplD` returns from Host DRAM $800\text{ ns}$ later, the 64B payload lands directly in `CmdSlot[CmdTag].sqe`, and the Command Parser starts!

---

## 2.4 The Phase Tag (`P` Bit) Trick & Why the Host Never Zeroes CQ Memory

### Intuition
When the SSD finishes a command and DMA-writes a 16-byte CQE into Host DRAM at `CQ_Base + 16 * cq_tail`, how does a polling Host CPU know that a *new* CQE has arrived in slot `cq_head`?
If the Host CPU had to write zeros back into every consumed CQE in Host DRAM to clear a "valid" bit, that would cause cache-line ping-ponging between the Host CPU and the SSD DMA engine (and race conditions if the SSD wraps around the ring before the host finishes zeroing!).

Instead, NVMe uses the brilliant **Phase Tag (`P` bit, Bit 16 of `CQE.DW3`)**:
- When a Completion Queue is created, the Host zeros the entire CQ buffer in DRAM **once** (`P = 0` in every slot), and both the Host driver and `CQCT[cqid].phase_bit` initialize their expected **Phase Tag to `1`**.
- During Pass 1 through the ring (`cq_tail = 0, 1, ..., QSize - 1`), the SSD stamps **`P = 1`** into every CQE it writes. The Host polls `CQE[cq_head].P == 1`.
- The instant `cq_tail` wraps around from `QSize - 1` back to `0`, the SSD **inverts its producer Phase bit (`phase_bit ^= 1`, so `1 -> 0`)**!
- During Pass 2 through the ring (`cq_tail = 0, 1, ..., QSize - 1`), the old entries left over from Pass 1 already have `P = 1`, so the SSD stamps **`P = 0`** into every new CQE it writes, and the Host polls `CQE[cq_head].P == 0`!

### Exact Hardware Logic Inside the CQE Posting Engine
```c
// Executed in Hardware/Firmware whenever posting a 16B CQE to CQ[cqid]
bool post_cqe_to_host(CQCT_Entry_t *cq, SQCT_Entry_t *sq, CQE_t *cqe) {
    // 1. Check for CQ Full BEFORE overwriting unconsumed CQE!
    uint16_t next_tail = (cq->cq_tail + 1) % cq->qsize;
    if (next_tail == cq->cq_head) {
        return false; // BACKPRESSURE! CQ is full; stall completion until Host rings CQyHDBL!
    }

    // 2. Stamp current SQ_Head and current CQ Phase bit into the 16B CQE
    cqe->sq_head = sq->sq_head;
    cqe->sq_id   = sq->sq_id;
    cqe->phase   = cq->phase_bit; // Bit 16 of DW3

    // 3. DMA Write 16B CQE to Host DRAM at cq->base_addr + 16 * cq->cq_tail
    uint64_t host_cqe_addr = cq->base_addr + 16ULL * cq->cq_tail;
    pcie_dma_write_posted_16B(host_cqe_addr, cqe);

    // 4. Advance CQ_Tail and INVERT phase_bit on wrap-around!
    cq->cq_tail = next_tail;
    if (cq->cq_tail == 0) {
        cq->phase_bit ^= 1;  // 1 -> 0 -> 1 -> 0 on every full ring revolution!
    }
    return true;
}
```

---

## 2.5 CQ Full Backpressure: What Happens When the Host Stops Updating `CQyHDBL`?

Look at Step 1 in `post_cqe_to_host()` above: what if the host submits $1023$ commands across four SQs that all map to a single 512-entry Completion Queue (`CQ 1`), and the host CPU hasn't updated `CQ1HDBL` yet?
- Once $511$ completions have been posted to `CQ 1`, `(cq_tail + 1) % 512 == cq_head`. **`CQ 1` is FULL!**
- If the SSD posted a 512th CQE, not only would it overwrite the unconsumed CQE at `cq_head`, it would also wrap `cq_tail` and flip `phase_bit`, corrupting the host's Phase Tag synchronization!
- **Correct Controller Behavior:**
  1. The CQE Posting Engine holds the 512th completion in an internal **Pending Completion FIFO** (or keeps it parked in its `CmdSlot`).
  2. To prevent the internal `CmdSlot` table from deadlocking other independent Completion Queues (`CQ 2, CQ 3, ...`), the **SQE Fetch Engine stops fetching new commands from any SQ mapped to a full (or nearly full) CQ**! Even better, many enterprise controllers **pre-reserve a CQ slot at SQE fetch time** (`reserved_cq_slots < qsize - 1`) so a fetched command is guaranteed to have a CQ slot waiting when it finishes.
  3. The moment the host writes `CQ1HDBL` to advance `cq_head`, the Doorbell Engine wakes up the CQE Posting Engine and drains the parked completions!

---

## 2.6 Hand-Worked Wrap-Around Trace ($QSize = 4$)

Let us trace a tiny 4-entry Completion Queue (`QSize = 4`, indices `0, 1, 2, 3`) across a wrap-around boundary:

| Step | Event | `CQ_Head` | `CQ_Tail` | SSD `phase_bit` | Host DRAM `CQE[0..3].P` | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 0 | Queue Created (`Create I/O CQ`) | `0` | `0` | `1` | `[0, 0, 0, 0]` | Empty (`Head == Tail`) |
| 1 | SSD posts CQE #1 (at slot 0) | `0` | `1` | `1` | **`[1, 0, 0, 0]`** | 1 CQE pending |
| 2 | SSD posts CQE #2 (at slot 1) | `0` | `2` | `1` | **`[1, 1, 0, 0]`** | 2 CQEs pending |
| 3 | SSD posts CQE #3 (at slot 2) | `0` | `3` | `1` | **`[1, 1, 1, 0]`** | **CQ FULL!** (`(3+1)%4 == 0`) |
| 4 | Host consumes 2 CQEs, writes `CQHDBL = 2` | **`2`** | `3` | `1` | `[1, 1, 1, 0]` | 1 CQE pending (2 slots freed!) |
| 5 | SSD posts CQE #4 (at slot 3 $\to$ **wraps to 0!**) | `2` | **`0`** | **`0` (Flipped!)** | **`[1, 1, 1, 1]`** | 2 CQEs pending (`Tail=0`) |
| 6 | SSD posts CQE #5 (at slot 0 with `P=0`!) | `2` | `1` | `0` | **`[0, 1, 1, 1]`** | 3 CQEs pending (**CQ FULL!**) |

Notice Step 6: Slot 0 previously held `P = 1` from Step 1. Without the host ever clearing Slot 0, the SSD overwrote Slot 0 with `P = 0` on Pass 2, and when the host's consumer pointer wraps to Slot 0 with expected phase `0`, it immediately detects `P == 0` as a brand-new completion!

---

## 2.7 Runnable Hardware/Firmware Co-Simulation: QCT, WRR Arbiter & Phase Tag Wrap-Around

Run this self-contained Python simulation of the SSD's internal `SQCT`/`CQCT` tables, Weighted Round-Robin with Urgent Priority Arbiter, Phase Tag wrap-around, and CQ Full backpressure recovery:

```python
from collections import deque

class QueueContextAndArbiterSim:
    def __init__(self):
        self.sqct = {}
        self.cqct = {}
        self.host_cq_dram = {}  # cqid -> list of (cid, sqid, sq_head, phase)
        # WRR weights (High=4, Medium=2, Low=1)
        self.wrr_weights = {1: 4, 2: 2, 3: 1}
        self.wrr_credits = {1: 4, 2: 2, 3: 1}
        self.pending_cqe_fifo = deque()

    def create_cq(self, cqid: int, qsize: int):
        self.cqct[cqid] = {"qsize": qsize, "head": 0, "tail": 0, "phase": 1, "bound_sqs": 0}
        self.host_cq_dram[cqid] = [(0, 0, 0, 0)] * qsize  # Zeroed Host DRAM (P=0)

    def create_sq(self, sqid: int, cqid: int, qsize: int, prio: int):
        assert cqid in self.cqct
        self.sqct[sqid] = {"qsize": qsize, "head": 0, "tail": 0, "cqid": cqid, "prio": prio, "in_flight": 0}
        self.cqct[cqid]["bound_sqs"] += 1

    def ring_sq_doorbell(self, sqid: int, new_tail: int):
        sq = self.sqct[sqid]
        assert 0 <= new_tail < sq["qsize"], "Invalid Doorbell Write Value!"
        sq["tail"] = new_tail

    def ring_cq_doorbell(self, cqid: int, new_head: int):
        cq = self.cqct[cqid]
        assert 0 <= new_head < cq["qsize"], "Invalid CQ Doorbell Write Value!"
        cq["head"] = new_head
        # Drain any completions that were stalled by CQ Full backpressure
        drained = 0
        for _ in range(len(self.pending_cqe_fifo)):
            sqid, cid = self.pending_cqe_fifo.popleft()
            if not self.try_post_cqe(sqid, cid):
                self.pending_cqe_fifo.append((sqid, cid))
            else:
                drained += 1
        if drained:
            print(f"  [CQE Engine] CQHDBL={new_head} freed slots -> drained {drained} stalled CQEs!")

    def arbitrate_next_sq(self):
        """Hardware WRR with Urgent Priority Class Arbiter."""
        active_sqs = [sqid for sqid, sq in self.sqct.items() if sq["head"] != sq["tail"]]
        if not active_sqs:
            return None
        # 1. Admin Q (0) and Urgent (prio=0) have strict priority
        for p in [0]:
            urgent = [sqid for sqid in active_sqs if self.sqct[sqid]["prio"] == p]
            if urgent:
                return urgent[0]
        # 2. Weighted Round Robin across High (1), Medium (2), Low (3)
        for _ in range(2):
            for prio in [1, 2, 3]:
                candidates = [sqid for sqid in active_sqs if self.sqct[sqid]["prio"] == prio]
                if candidates and self.wrr_credits[prio] > 0:
                    self.wrr_credits[prio] -= 1
                    return candidates[0]
            # Reload WRR credits when all active classes exhaust credits
            self.wrr_credits = dict(self.wrr_weights)
        return active_sqs[0]

    def fetch_one_sqe(self, sqid: int, cid: int):
        sq = self.sqct[sqid]
        sq["head"] = (sq["head"] + 1) % sq["qsize"]
        sq["in_flight"] += 1
        return (sqid, cid)

    def try_post_cqe(self, sqid: int, cid: int) -> bool:
        sq = self.sqct[sqid]
        cq = self.cqct[sq["cqid"]]
        next_tail = (cq["tail"] + 1) % cq["qsize"]
        if next_tail == cq["head"]:
            return False  # CQ FULL!
        # Write CQE to Host DRAM at cq["tail"] with current Phase bit
        self.host_cq_dram[sq["cqid"]][cq["tail"]] = (cid, sqid, sq["head"], cq["phase"])
        cq["tail"] = next_tail
        if cq["tail"] == 0:
            cq["phase"] ^= 1  # Invert Phase Tag on wrap-around!
        sq["in_flight"] -= 1
        return True

sim = QueueContextAndArbiterSim()
sim.create_cq(cqid=1, qsize=4)  # 4-slot CQ (max 3 unconsumed CQEs before CQ Full!)
sim.create_sq(sqid=1, cqid=1, qsize=16, prio=1)  # High Priority (weight 4)
sim.create_sq(sqid=2, cqid=1, qsize=16, prio=2)  # Medium Priority (weight 2)

# Host submits 4 commands on SQ1 and 2 commands on SQ2
sim.ring_sq_doorbell(sqid=1, new_tail=4)
sim.ring_sq_doorbell(sqid=2, new_tail=2)

fetched_order = []
for step in range(6):
    winner_sq = sim.arbitrate_next_sq()
    fetched_order.append(winner_sq)
    sqid, cid = sim.fetch_one_sqe(winner_sq, cid=100 + step)
    if not sim.try_post_cqe(sqid, cid):
        print(f"  [Backpressure] Step {step+1}: CQ1 is FULL (Head={sim.cqct[1]['head']}, Tail={sim.cqct[1]['tail']})! Parking CID={cid}")
        sim.pending_cqe_fifo.append((sqid, cid))

print(f"WRR Fetch Order (High weight=4 vs Med weight=2): {fetched_order}")
print(f"Host CQ1 DRAM before CQHDBL (cid, sqid, sq_head, P): {sim.host_cq_dram[1]}")

# Host consumes 3 CQEs and rings CQ1HDBL = 3 -> wraps CQ1 and flips Phase bit to 0!
sim.ring_cq_doorbell(cqid=1, new_head=3)
print(f"Host CQ1 DRAM after CQHDBL=3 & wrap (cid, sqid, sq_head, P): {sim.host_cq_dram[1]}")
print(f"CQ1 internal state after wrap: Head={sim.cqct[1]['head']}, Tail={sim.cqct[1]['tail']}, Phase={sim.cqct[1]['phase']}")
```

---

## 2.8 Check Your Understanding (Firmware Design Problems)

*(Full step-by-step solutions are in [Chapter 99](./99-solutions-and-references.md).)*

1. **Many-to-One SQ-to-CQ Mapping & Head-of-Line Blocking:** Suppose a host maps 8 Submission Queues (`SQ 1..8`) to a single Completion Queue (`CQ 1`) of size $256$, and submits $32$ commands on each of the 8 SQs ($256$ commands total). Why can this cause a CQ Full stall, and why is **pre-reserving a CQ slot at SQE fetch time** better than stalling at CQE post time after a NAND read has already occupies a 4 KiB read buffer in Controller SRAM?
2. **Duplicate or Backward Doorbell Writes:** Suppose `SQCT[1]` currently has `qsize = 1024`, `sq_head = 500`, and `sq_tail = 510`. What does it mean if the host writes `SQ1TDBL = 505`? Is `505` a backward move of $5$ entries, or did the host just submit $1019$ new commands that wrapped around the 1024-entry ring? How can your hardware/firmware tell the difference?
3. **Sizing the Internal `SQCT` / `CQCT` SRAM:** If your enterprise SSD controller supports $1024$ Submission Queues and $1024$ Completion Queues using the 32-byte `SQCT_Entry_t` and `CQCT_Entry_t` structures from Section 2.2, plus a 4-byte Doorbell SRAM per doorbell, how many kilobytes of internal controller SRAM are required in total?
