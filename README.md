# Tutorials & Deep-Dive Study Notes

A curated personal repository of self-contained, first-principles technical tutorials, mathematical derivations, firmware/hardware architectural deep dives, and runnable empirical verifications created for my research and continuous learning goals.

---

## Philosophy & Format

Each tutorial in this repository is designed to be:
1. **Self-Contained from Prerequisites to Proofs / Hardware State Machines:** Required foundations (linear algebra, probability, optimization, or PCIe / SoC hardware architecture) are taught inline and tied directly to the theorems or firmware routines that use them.
2. **Anchored to Concrete Systems & Running Examples:** Abstract theory and specifications are grounded in real engineering and machine learning workloads (distributed deep learning gradient compression, multi-million-IOPS NVMe SSD controller firmware).
3. **Intuition $\to$ Statement / Spec $\to$ Derivation / State Machine $\to$ Worked Example:** Key results build intuition first, state exact assumptions/specifications clearly, provide step-by-step proofs or firmware algorithms, and work through concrete byte/cycle examples by hand.
4. **Empirically Verified:** Claims, scaling laws, and hardware/firmware protocols are paired with short, dependency-light Python simulation scripts that verify the math and state transitions empirically.
5. **Active Recall:** Each tutorial concludes with check-your-understanding design problems and complete worked solutions.

---

## Tutorials Catalog

Each tutorial opens with an index that holds the running system model, notation, and the full chapter list. Start there.

### 1. [Compressive Sensing Decoders for Distributed Gradient Compression](./cs-decoder-tutorial/)
Compares the **Moore–Penrose pseudo-inverse** (minimum-norm least squares) with **$\ell_1$ recovery** (Basis Pursuit / LASSO via ISTA and FISTA), anchored to block-wise gradient compression ($N = 1024$, $M = 256$, $r = 0.25$) in distributed data-parallel deep learning.

- **Prerequisites:** linear algebra, basic probability, and some optimization; the tutorial teaches the rest inline.
- **Start here:** [Index & Master Notation](./cs-decoder-tutorial/00-index-and-notation.md)

---

### 2. [Inside the NVMe SSD Frontend: A Firmware Engineer's Complete Tutorial](./nvme-ssd-frontend-tutorial/)
An architectural and firmware tutorial on the **NVMe Host Interface Layer (HIL) / SSD frontend**, written from the perspective of an SSD controller firmware engineer working at multi-million IOPS: the HW/FW split, registers and queues, admin handlers, PRP/SGL DMA, the read/write completion pipeline, and abort/reset safety.

- **Prerequisites:** basic C and embedded-systems familiarity; PCIe and NVMe concepts are introduced as needed.
- **Start here:** [Index & SoC Hardware/Firmware Split](./nvme-ssd-frontend-tutorial/00-index-and-architecture.md)
