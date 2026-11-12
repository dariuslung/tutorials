# Tutorials & Deep-Dive Study Notes

A curated personal repository of self-contained, first-principles technical tutorials, mathematical derivations, firmware/hardware architectural deep dives, and runnable empirical verifications created for my research and continuous learning goals.

---

## Philosophy & Format

Each tutorial in this repository is designed to be:
1. **Self-Contained from Prerequisites to Proofs / Hardware State Machines:** Required foundations (linear algebra, probability, optimization, or PCIe / SoC hardware architecture) are taught inline and tied directly to the theorems or firmware routines that use them.
2. **Anchored to Concrete Systems & Running Examples:** Abstract theory and specifications are grounded in real engineering and machine learning workloads (distributed deep learning gradient compression, multi-million-IOPS NVMe SSD controller firmware).
3. **Intuition $\to$ Statement / Spec $\to$ Derivation / State Machine $\to$ Worked Example:** Key results build intuition first, state exact assumptions/specifications clearly, provide step-by-step proofs or firmware algorithms, and work through concrete byte/cycle examples by hand.
4. **Empirically Verified:** Claims, scaling laws, and hardware/firmware protocols are paired with short, dependency-light Python simulation scripts that verify the math and state transitions empirically.
5. **Active Recall:** Chapters conclude with check-your-understanding design problems and complete worked solutions.

---

## Tutorials Catalog

### 1. [Compressive Sensing Decoders for Distributed Gradient Compression](./cs-decoder-tutorial/)
A complete tutorial comparing the **Moore–Penrose Pseudo-Inverse** (minimum-norm least squares) and **$\ell_1$ Recovery** (Basis Pursuit / LASSO solved via ISTA and FISTA), anchored to block-wise gradient compression ($N = 1024, M = 256, r = 0.25$) in distributed data-parallel deep learning.

- **[00 — Index & Master Notation](./cs-decoder-tutorial/00-index-and-notation.md):** Running system model, AllReduce measurement aggregation, and master notation table.
- **[01 — Prerequisites](./cs-decoder-tutorial/01-prerequisites.md):** Norms ($\ell_0, \ell_1, \ell_2$), the Four Fundamental Subspaces ($\text{row}(\Phi) \perp \text{null}(\Phi)$), orthogonal projections, SVD, trace tricks, Marchenko–Pastur singular value bounds, $L$-smoothness, and proximal operators.
- **[02 — The Basic Problem: Underdetermined Systems](./cs-decoder-tutorial/02-underdetermined-systems.md):** Geometry of $y = \Phi x$ ($M < N$), affine solution spaces $\mathcal{H}_y = x_{\mathcal{R}} + \text{null}(\Phi)$, and hand-worked examples for $(N=2, M=1)$ and $(N=3, M=2)$.
- **[03 — The Pseudo-Inverse Decoder, Completely](./cs-decoder-tutorial/03-pseudo-inverse-decoder.md):** SVD definition, $\Phi^+ = \Phi^T(\Phi\Phi^T)^{-1}$, rank-$M$ projection $\Phi^+\Phi = P_{\mathcal{R}}$, minimum-$\ell_2$-norm proof, exact proofs of $\mathbb{E}[\Phi^+\Phi] = \frac{M}{N}I_N$ and variance $\mathbb{E}\|\frac{N}{M}\Phi^+\Phi x - x\|_2^2 = (\frac{N}{M}-1)\|x\|_2^2$, Gaussian vs. Rademacher symmetries, and AllReduce commutativity.
- **[04 — Sparsity and $\ell_1$ Recovery, Completely](./cs-decoder-tutorial/04-sparsity-and-l1-recovery.md):** Sparse vs. power-law compressible signals, $\ell_0$ NP-hardness, $\ell_1$ cross-polytope geometry, BP / BPDN / LASSO, Null Space Property (NSP), Restricted Isometry Property (RIP), $M \gtrsim C k \log(N/k)$, the Donoho–Tanner phase transition ($\rho_W(0.25) \approx 0.241$), and Candès–Romberg–Tao stability bounds.
- **[05 — Algorithms: ISTA and FISTA](./cs-decoder-tutorial/05-ista-and-fista-algorithms.md):** Proximal gradient derivation of ISTA, closed-form derivation of soft thresholding $\mathcal{S}_{\alpha\lambda}$ as $\text{prox}_{\alpha\lambda\|\cdot\|_1}$, Lipschitz step size $\alpha = 1/\|\Phi\|_2^2$, Nesterov momentum in FISTA ($O(1/k)$ vs. $O(1/k^2)$), choosing $\lambda$ relative to $\lambda_{\max} = \|\Phi^T y\|_\infty$, homotopy continuation, and FLOP cost analysis.
- **[06 — Head-to-Head Comparison & Application to Gradient Compression](./cs-decoder-tutorial/06-gradient-compression-comparison.md):** Bias vs. variance in SGD, fixed $\Phi$ (subspace training) vs. per-step $\Phi_t$, why nonlinear $\ell_1$ decoding breaks AllReduce aggregation and suffers support-union blowup, the exact duality with rescaled Rand-$k$ sparsification, Error Feedback, and why real neural network gradients ($k_{\text{eff}} \in [512, 652] \gg k_{\max} = 62$) favor the pseudo-inverse at $r = 0.25$.
- **[99 — Complete Solutions & Annotated References](./cs-decoder-tutorial/99-solutions-and-references.md):** Full step-by-step solutions to all 18 end-of-chapter problems and an annotated bibliography.

---

### 2. [Inside the NVMe SSD Frontend: A Firmware Engineer's Complete Tutorial](./nvme-ssd-frontend-tutorial/)
An end-to-end architectural and firmware tutorial on the **NVMe Host Interface Layer (HIL) / SSD Frontend** written from the perspective of an embedded SSD Controller Firmware Engineer (covering the HW/FW split at $3\text{M+}$ IOPS, BAR0 traps, Queue Context Tables, Admin control-plane handlers, PRP/SGL DMA walkers, out-of-order 4 KiB read reassembly, and Abort/Reset safety).

- **[00 — Index & SoC Hardware/Firmware Split](./nvme-ssd-frontend-tutorial/00-index-and-architecture.md):** Multi-core SSD controller architecture, the $333\text{ ns}$ cycle budget rule, Fast-Path ASIC Engines vs. HIL Firmware, and Spec-to-Internal glossary.
- **[01 — PCIe Endpoint, BAR0 Traps & The Boot/Reset State Machine](./nvme-ssd-frontend-tutorial/01-pcie-and-controller-registers.md):** Posted (`MWr`) vs. Non-Posted (`MRd` $\to$ `CplD`) TLPs, PCIe Producer-Consumer ordering, `CAP`/`CC`/`CSTS`/`AQA`/`ASQ`/`ACQ` bitfields, and HIL Firmware state machines for Enable (`CC.EN: 0 -> 1`), Reset (`CC.EN: 1 -> 0` with DMA drain), Shutdown (`CC.SHN`), and FLR.
- **[02 — Queue Context Tables (QCT), Doorbells & HW Fetch Engines](./nvme-ssd-frontend-tutorial/02-queues-doorbells-and-arbitration.md):** Internal `SQCT` and `CQCT` SRAM structures, Doorbell latching, Weighted Round-Robin (WRR) with Urgent Priority hardware arbitration, Phase Tag (`P` bit) wrap-around logic, and CQ Full backpressure.
- **[03 — The Firmware Control Plane: Admin Commands & I/O Queue Lifecycle](./nvme-ssd-frontend-tutorial/03-admin-commands-and-queue-lifecycle.md):** Firmware handlers for `Identify` (`CNS=0x00, 0x01`), `Set/Get Features` (`Number of Queues`), `Create/Delete I/O CQ & SQ` (including non-contiguous `PC=0` queues and the **SQ Deletion Drain Protocol**), and parking/firing `Asynchronous Event Requests (AER)`.
- **[04 — Data Path Mechanics: SQE Parsing, PRP/SGL Walkers & DMA Engines](./nvme-ssd-frontend-tutorial/04-nvm-commands-prp-sgl-and-dma.md):** Bit-accurate 64B SQE and 16B CQE layouts, fast-path command validation, the 4 sacred PRP rules (direct `PRP2` vs. PRP List vs. Chained PRP Lists, plus catching `PRP Offset Invalid`), SGL descriptors, and 4 KiB FTL `SubReq` slicing.
- **[05 — Read, Write, Flush & Out-of-Order Completion Pipeline](./nvme-ssd-frontend-tutorial/05-read-write-flush-and-completion-pipeline.md):** Write Buffer credit backpressure, Early Write Completion vs. `FUA`, Write Buffer CAM hits on Read-After-Write, `Flush` watermark barriers, out-of-order 4 KiB NAND slice DMA + atomic reference counting, and MSI-X interrupt coalescing.
- **[06 — What Keeps Firmware Engineers Awake: Aborts, Resets, PI & Performance](./nvme-ssd-frontend-tutorial/06-error-handling-aborts-resets-and-debug.md):** Multi-stage `Abort` (`0x08`) implementation and CQE ordering, the 16-bit Generation Counter (`cmd_gen`) guard against zombie FTL sub-requests, End-to-End Protection Information (`PI` / T10 DIF `CRC-16`), and Little's Law sizing for PCIe Read Tags and HIL CPU cycles.
- **[99 — Firmware Design Problem Solutions & Spec Reference](./nvme-ssd-frontend-tutorial/99-solutions-and-references.md):** Complete solutions to all 18 firmware engineering design problems and quick-reference tables of NVMe 2.0 opcodes and status codes.
