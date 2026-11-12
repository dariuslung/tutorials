# Chapter 5: Read, Write, Flush & Out-of-Order Completion Pipeline

Once the Command Parser and PRP/SGL Walker have validated an NVM command and translated its `(SLBA, NLB)` into 4 KiB FTL `SubReqs`, how do the **Write Pipeline**, **Read Pipeline**, **Barrier (`Flush` / `FUA`) Manager**, and **Completion / MSI-X Engine** actually move data between Host DRAM, Controller SRAM/DRAM, and the NAND Flash Backend?

In this chapter, we trace the exact hardware/firmware data flows for Reads, Writes, and Flushes—including **out-of-order 4 KiB flash page reassembly** and **interrupt coalescing**.

---

## 5.1 The Write Pipeline: Buffer Allocation, Early Completion vs. `FUA`, and `Flush`

### Intuition
Programming a Triple-Level Cell (TLC) or Quad-Level Cell (QLC) NAND flash page takes **$500\ \mu\text{s} \text{ to } 2,500\ \mu\text{s}$**—and requires assembling a full multi-plane **Superpage** (e.g., $64\text{ KiB} \text{ to } 192\text{ KiB}$) before the flash die can even begin programming!
If your SSD made the host wait $1.5\text{ ms}$ for NAND programming on every 4 KiB Write, QD=1 write throughput would drop to $\sim 2.6\text{ MB/s}$.
Instead, when **Volatile Write Cache (`VWC`)** is enabled (`WCE = 1`), the SSD Frontend completes a Write as soon as the payload has been DMA-read from Host DRAM into the SSD's internal **Controller SRAM / DRAM Write Buffer**—taking only **$\sim 2\text{ to } 5\ \mu\text{s}$**!

### Step-by-Step Write Pipeline (Normal Cached Write vs. `FUA` Write)

```mermaid
sequenceDiagram
    participant Host as Host DRAM / CPU
    participant FE as SSD Frontend (DMA + HIL FW)
    participant WBUF as Controller Write Buffer (SRAM/DRAM)
    participant FTL as FTL & NAND Backend

    Host->>FE: 1. Ring SQyTDBL (Write SLBA=100, NLB=3 [16 KiB])
    FE->>Host: 2. PCIe MRd -> CplD (Fetch 64B SQE into CmdSlot[tag])
    FE->>WBUF: 3. Allocate four 4 KiB Write Buffer Descriptors (BDs)
    FE->>Host: 4. PRP Walker issues PCIe MRd -> CplD (Pull 16 KiB data)
    Host-->>WBUF: 5. 16 KiB payload lands in Write Buffer BDs
    alt Normal Cached Write (WCE=1 and FUA=0)
        FE->>Host: 6a. EARLY COMPLETION! Post 16B CQE + MSI-X NOW (~3 us!)
        FE->>FTL: 7a. Hand 4 SubReqs (LPN 100..103) to FTL Write Queue in background
    else FUA Write (FUA=1 or WCE=0)
        FE->>FTL: 6b. Mark SubReqs URGENT_SYNC; FTL programs to NAND (or PLP-backed NVRAM)
        FTL-->>FE: 7b. All 4 SubReqs programmed to non-volatile media
        FE->>Host: 8b. Post 16B CQE + MSI-X AFTER NAND completion
    end
```

### 1. Write Buffer Credit Backpressure (Why Writes Don't Overflow Controller RAM)
What if the host blasts $6\text{ GB/s}$ of writes while the NAND backend can only program $3\text{ GB/s}$ (or is busy with Garbage Collection)?
- At step 3 above, before the Frontend DMA Engine issues a PCIe `MRd` to pull write data from Host DRAM, it must acquire `N` **4 KiB Write Buffer Credits** from the `FreeWriteBufferPool`.
- When the pool is exhausted (`FreeWriteCredits < N`), the Frontend **stalls Write DMA fetching** (leaving the Write commands waiting harmlessly in Host DRAM or in `CmdSlot`) while allowing **Read commands** to bypass stalled Writes and use the separate **Read Buffer Pool**!
- *(Firmware Design Rule):* Always partition or reserve minimum buffer credits separately for **Reads** vs. **Writes** so a heavy write burst never starves low-latency reads of SRAM buffer descriptors!

### 2. Read-After-Write Hazard Check (The Write Buffer Lookup / CAM)
Wait: if an Early-Completed Write for `LPN 100` is still sitting in the Controller Write Buffer waiting to be programmed to NAND, and $5\ \mu\text{s}$ later the host submits a **Read for `LPN 100`**, what happens if the Read goes straight to NAND?
It would read **stale old data** from NAND!
Therefore, on every incoming Read `SubReq(LPN)`, the Frontend / FTL must check:
1. Does the L2P table or **Write Buffer Content-Addressable Memory (CAM) / Hash Table** point `LPN 100` to an unprogrammed **Write Buffer Descriptor (`BD`)** in Controller DRAM/SRAM?
2. **If YES (Write Buffer Hit!):** The Frontend DMA Engine copies/DMAs the 4 KiB page directly from that Write Buffer `BD` to the host's Read `PRP` address in $< 2\ \mu\text{s}$ without touching NAND!

### 3. Implementing the `Flush` Command (`Opcode 0x00`) Barrier in HIL Firmware
When a filesystem (ext4/XFS) or database commits a transaction (`fsync()`), it sends an NVMe **`Flush` (`Opcode 0x00`)** command to an I/O SQ.
What does the NVMe Specification require for `Flush`?
> *"All data and metadata associated with all Write commands that completed **prior** to the submission of the `Flush` command (on the specified namespace `NSID`, or all namespaces if `NSID == 0xFFFFFFFF`) shall be written to non-volatile media before the `Flush` command completes."*

How HIL Firmware implements `Flush` without stalling new incoming Writes (**Epoch / Watermark Barrier**):
1. Every Write Buffer entry is stamped with a monotonically increasing **Write Sequence Number (`WSN`)** when its CQE is posted.
2. When `Flush` arrives at time $t$, HIL Firmware snapshots the current `target_wsn = g_last_completed_write_wsn` and sends a `FLUSH_BARRIER(target_wsn)` token to the FTL Write Queue.
3. New Writes arriving *after* the `Flush` can still allocate buffers (with `WSN > target_wsn`).
4. As soon as the FTL confirms that all Write Buffers with `WSN <= target_wsn` have been programmed to NAND and their L2P updates are crash-safe, FTL notifies HIL Firmware to post the 16B CQE for the `Flush` command!

---

## 5.2 The Read Pipeline & Out-of-Order 4 KiB NAND Page Reassembly

### Intuition
Consider a single **32 KiB Host Read command** (`SLBA = 0, NLB = 7` $\implies 8$ pages of $4\text{ KiB}$: `LPN 0..7`).
Inside the SSD, the FTL stripes `LPN 0..7` across 8 different NAND channels/dies:
- Suppose `LPN 0` hits a NAND die that is currently busy doing a $1,000\ \mu\text{s}$ Write or Erase!
- Meanwhile, `LPN 1..7` land on idle NAND dies and finish reading in **$45\ \mu\text{s}$**!

If the SSD Frontend waited for `LPN 0` before DMA-transferring `LPN 1..7` to Host DRAM, those seven 4 KiB buffers (`28 KiB` of precious Controller SRAM!) would sit locked inside the SSD for $1,000\ \mu\text{s}$!
Instead, because the Host gave us the complete `PRP1 / PRP2` physical address map upfront, the SSD Frontend **DMAs each 4 KiB slice to its exact Host DRAM address the instant that slice returns from NAND—completely out of order!**

### How Out-of-Order Sub-Request DMA & Reference Counting Work
When the 32 KiB Read command (`CmdTag = 12`) is parsed at intake:
1. The Slicer initializes the Command Slot's atomic reference counter:
   $$\texttt{CmdSlot[12].remaining\_subreqs = 8;}$$
   $$\texttt{CmdSlot[12].cumulative\_status = SC\_SUCCESS;}$$
2. It issues 8 independent 4 KiB `SubReqs` to the FTL, each tagged with `(parent_cmd_tag = 12, slice_index = k)` for $k \in \{0, 1, \dots, 7\}$.
3. Whenever **any** slice $k$ returns from NAND (or LDPC ECC decoder) in a 4 KiB SRAM Read Buffer `BD`:
   - The Frontend looks up the host physical address for slice $k$ (`PRP_Offset = k * 4096`), issues a Posted PCIe `MWr` to transfer those 4 KiB to Host DRAM, and **immediately frees the 4 KiB SRAM Read Buffer `BD`** back to the pool!
   - If slice $k$ suffered an uncorrectable ECC error (`UECC`), it latches `CmdSlot[12].cumulative_status = SC_UNRECOVERED_READ_ERROR (SCT=0x02, SC=0x81)`.
   - It decrements `CmdSlot[12].remaining_subreqs--`.
4. **Only when `remaining_subreqs` transitions `1 -> 0`** does the Frontend hand `CmdTag = 12` to the **CQE Posting Engine** to send the single 16B CQE to the Host!

```
Out-of-Order Read Execution for 16 KiB Read (CmdTag=12, 4 Slices: k=0, 1, 2, 3):

  Intake: CmdSlot[12].remaining_subreqs = 4
    |-- Slice k=2 returns from NAND Ch 2 first (t=40 us) -> DMA to PRP[2], free BD, rem_subreqs = 3
    |-- Slice k=0 returns from NAND Ch 0 next  (t=42 us) -> DMA to PRP[0], free BD, rem_subreqs = 2
    |-- Slice k=3 returns from NAND Ch 3 next  (t=45 us) -> DMA to PRP[3], free BD, rem_subreqs = 1
    +-- Slice k=1 returns from busy NAND Ch 1  (t=310 us)-> DMA to PRP[1], free BD, rem_subreqs = 0!
                                                                 |
                                                                 v
                                                  Trigger single 16B CQE + MSI-X!
```

> **Note on Out-of-Order *Commands* Within the Same Submission Queue:**
> Not only do slices *within* one command complete out of order, **different commands within the same Submission Queue also complete out of order!**
> If the host submits Command A (`CID = 1`, 128 KiB Read hitting a busy NAND die) followed by Command B (`CID = 2`, 4 KiB Read hitting our Write Buffer CAM), Command B finishes in $2\ \mu\text{s}$ and posts its CQE (`CID = 2`) to the Completion Queue *long before* Command A (`CID = 1`) finishes! In NVMe, **commands in a Submission Queue are unordered** unless separated by a `Flush` or Fused operation.

---

## 5.3 The CQE Posting & MSI-X Interrupt Coalescing Engine

When a command finishes and posts its 16-byte CQE to `CQ[cqid]`, should the hardware fire an MSI-X interrupt (`MWr` to the host CPU's LAPIC) on *every single CQE*?
- At $500,000$ IOPS, firing $500,000$ hardware interrupts per second would melt the host OS in interrupt-handler context switches!
- Instead, the Frontend MSI-X Controller implements two hardware mechanisms:
  1. **Interrupt Coalescing (`Feature ID 0x08`):** Waits until either `unack_cqe_cnt >= THR + 1` completions have accumulated in `CQ[cqid]` OR the coalescing timer reaches `TIME * 100 us`, then fires **one** MSI-X interrupt for the whole batch!
  2. **Interrupt Pin / Vector Auto-Masking on Unacknowledged CQEs:** Once an MSI-X is sent for `CQ[cqid]`, the controller can suppress redundant MSI-X writes for that CQ until the host driver acknowledges the batch by writing `CQ[cqid]HDBL`! (When `CQ[cqid]HDBL` is written, if `cq_head != cq_tail` still holds because new CQEs arrived while the ISR was running, the controller immediately fires a follow-up MSI-X so no completion is ever stranded!)

---

## 5.4 Runnable Out-of-Order Read, Write Buffer CAM & Flush Barrier Simulator

Run this self-contained Python simulation of the complete Frontend Data Pipeline, demonstrating:
1. **Early Write Completion** into the Write Buffer CAM;
2. **Read-After-Write Hit** (serving a Read directly from an unprogrammed Write Buffer in $2\ \mu\text{s}$ while other slices come from NAND);
3. **Out-of-Order 4 KiB NAND Slice Completion** (`remaining_subreqs` reference counting);
4. **`Flush` Watermark Barrier** waiting only for prior writes (`WSN <= target_wsn`).

```python
class FrontendDataPipelineSim:
    def __init__(self):
        self.cmd_slots = {}          # tag -> dict
        self.write_buffer_cam = {}   # lpn -> (wsn, data_str, programmed_to_nand)
        self.nand_storage = {}       # lpn -> data_str
        self.host_dram_pages = {}    # phys_addr -> data_str
        self.wsn_counter = 0
        self.completed_cqes = []     # list of (cid, status_sc, finish_time_us, note)

    def submit_write_4k_slices(self, tag: int, cid: int, slba: int, nlb: int, prp_addrs: list, fua: bool, now_us: int):
        num_slices = nlb + 1
        assert len(prp_addrs) == num_slices
        self.wsn_counter += 1
        wsn = self.wsn_counter

        for k in range(num_slices):
            lpn = slba + k
            payload = self.host_dram_pages[prp_addrs[k]]
            if fua:
                # FUA=1 bypasses volatile cache commitment: programs straight to NAND
                self.nand_storage[lpn] = payload
                self.write_buffer_cam[lpn] = (wsn, payload, True)
            else:
                # WCE=1, FUA=0: Stage in volatile Write Buffer CAM (not yet in NAND!)
                self.write_buffer_cam[lpn] = (wsn, payload, False)

        finish_us = now_us + (600 if fua else 3)
        mode = "FUA->NAND" if fua else f"EarlyWriteBuf(WSN={wsn})"
        self.completed_cqes.append((cid, 0x00, finish_us, mode))

    def submit_read_command(self, tag: int, cid: int, slba: int, nlb: int, prp_addrs: list, nand_latencies_us: list, now_us: int):
        num_slices = nlb + 1
        self.cmd_slots[tag] = {
            "cid": cid,
            "remaining_subreqs": num_slices,
            "status_sc": 0x00,
            "slice_events": [],
        }
        # Dispatch each 4 KiB slice; slices can hit Write Buffer CAM (2 us) or NAND (out of order!)
        events = []
        for k in range(num_slices):
            lpn = slba + k
            if lpn in self.write_buffer_cam and not self.write_buffer_cam[lpn][2]:
                # Write Buffer CAM Hit! Zero NAND latency!
                data = self.write_buffer_cam[lpn][1]
                events.append((now_us + 2, k, lpn, prp_addrs[k], data, "WriteBuf-CAM-Hit"))
            else:
                data = self.nand_storage.get(lpn, f"NAND_Zero_LPN{lpn}")
                events.append((now_us + nand_latencies_us[k], k, lpn, prp_addrs[k], data, "NAND-Channel"))

        # Process slice completions in chronological (out-of-order LPN!) sequence
        for done_us, k, lpn, host_addr, data, src in sorted(events, key=lambda x: x[0]):
            self._on_read_slice_done(tag, k, lpn, host_addr, data, src, done_us)

    def _on_read_slice_done(self, tag: int, slice_idx: int, lpn: int, host_addr: int, data: str, src: str, done_us: int):
        slot = self.cmd_slots[tag]
        # 1. Out-of-order DMA write to exact Host PRP address for slice_idx
        self.host_dram_pages[host_addr] = data
        slot["slice_events"].append(f"slice[{slice_idx}](LPN={lpn},{src}@{done_us}us)")
        # 2. Decrement atomic reference counter
        slot["remaining_subreqs"] -= 1
        if slot["remaining_subreqs"] == 0:
            trace = " -> ".join(slot["slice_events"])
            self.completed_cqes.append((slot["cid"], slot["status_sc"], done_us, f"ReadDone({trace})"))
            del self.cmd_slots[tag]

    def submit_flush(self, cid: int, now_us: int):
        target_wsn = self.wsn_counter
        dirty_lpns = [lpn for lpn, (wsn, _, prog) in self.write_buffer_cam.items() if wsn <= target_wsn and not prog]
        for lpn in dirty_lpns:
            wsn, data, _ = self.write_buffer_cam[lpn]
            self.nand_storage[lpn] = data
            self.write_buffer_cam[lpn] = (wsn, data, True)
        flush_done_us = now_us + (600 if dirty_lpns else 1)
        self.completed_cqes.append((cid, 0x00, flush_done_us, f"Flush(WSN<={target_wsn}, flushed_lpns={dirty_lpns})"))

pipe = FrontendDataPipelineSim()
pipe.nand_storage[100] = "Old_NAND_100"
pipe.nand_storage[101] = "Old_NAND_101"
pipe.nand_storage[102] = "Old_NAND_102"
pipe.nand_storage[103] = "Old_NAND_103"

# 1. Host writes new data to LPN 101 (Early completed in 3 us into Write Buffer CAM!)
pipe.host_dram_pages[0x1000] = "New_WriteBuf_101"
pipe.submit_write_4k_slices(tag=1, cid=10, slba=101, nlb=0, prp_addrs=[0x1000], fua=False, now_us=0)

# 2. Host reads LPN 100..103 (16 KiB):
#    - Slice 1 (LPN 101) hits Write Buffer CAM at t=12 us!
#    - Slice 0 (LPN 100) hits a busy NAND die (300 us), while Slices 2 & 3 finish in 45 us & 50 us!
read_prps = [0x2000, 0x3000, 0x4000, 0x5000]
pipe.submit_read_command(tag=2, cid=11, slba=100, nlb=3, prp_addrs=read_prps,
                         nand_latencies_us=[300, 999, 45, 50], now_us=10)

# 3. Host issues Flush to commit WSN<=1 to NAND
pipe.submit_flush(cid=12, now_us=20)

for cid, sc, t_us, info in pipe.completed_cqes:
    print(f"CQE CID={cid:2d} | SC=0x{sc:02X} | t={t_us:4d} us | {info}")
print("Host Read DRAM Buffers after CQE:", [pipe.host_dram_pages[a] for a in read_prps])
```

---

## 5.5 Check Your Understanding (Firmware Design Problems)

*(Full step-by-step solutions are in [Chapter 99](./99-solutions-and-references.md).)*

1. **The Overlapping Concurrent Write Hazard (`Write A` vs. `Write B` to Same LBA):** Suppose the host submits two Write commands back-to-back to the **same `SLBA = 50`** in the same Submission Queue (`Write A` with `CID = 1`, followed by `Write B` with `CID = 2`). Can the SSD DMA Engine fetch `Write B`'s data from Host DRAM before `Write A`'s data if PCIe read tags return out of order? What rule must your Write Buffer CAM / LBA Lock table enforce so that `Write A`'s data never overwrites `Write B`'s newer data in the Write Buffer?
2. **`FUA = 1` on a Read Command when `LPN` Is Dirty in the Write Buffer:** Look carefully at the NVMe specification for `Read` with `FUA = 1` (Force Unit Access). Suppose `LPN 101` was recently modified by a normal cached Write (`FUA = 0`), so the **newest** version of `LPN 101` is sitting in your volatile DRAM Write Buffer while the **old** version is in NAND. If the host now sends `Read (LPN 101, FUA = 1)`, must your firmware return the old data from NAND or the newest data?
3. **Why the Host Driver Still Needs `CQyHDBL` Even When Polling (`IEN = 0`):** In high-performance storage frameworks like SPDK or `io_uring` `IOPOLL`, the host sets `IEN = 0` (disabling MSI-X interrupts completely) and polls the `Phase` bit in Host DRAM. If interrupts are disabled, why must the host driver *still* write `CQyHDBL` over PCIe periodically?
