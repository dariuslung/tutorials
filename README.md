# Tutorials & Deep-Dive Study Notes

A curated personal repository of self-contained, first-principles technical tutorials, mathematical derivations, and runnable empirical verifications created for my research and continuous learning goals.

---

## Philosophy & Format

Each tutorial in this repository is designed to be:
1. **Self-Contained from Prerequisites to Proofs:** Required mathematical foundations (linear algebra, probability, optimization, signal processing) are taught inline and tied directly to the theorems that use them.
2. **Anchored to Concrete Systems & Running Examples:** Abstract theory is grounded in real engineering and machine learning workloads (such as distributed deep learning and gradient compression).
3. **Intuition $\to$ Statement $\to$ Derivation $\to$ Worked Example:** Key results build intuition first, state exact assumptions and theorems clearly, provide step-by-step proofs, and work through small numerical examples by hand.
4. **Empirically Verified:** Claims, scaling laws, and phase transitions are paired with short, dependency-light Python / NumPy scripts that verify the math empirically.
5. **Active Recall:** Chapters conclude with check-your-understanding exercises and complete worked solutions.

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
- **[99 — Complete Solutions & Annotated References](./cs-decoder-tutorial/99-solutions-and-references.md):** Full step-by-step solutions to all 18 end-of-chapter problems and an annotated bibliography separating proven theorems from engineering heuristics.

---

## Running the Empirical Verification Snippets

All code snippets across the tutorials use standard Python 3 and `numpy`. You can execute every verification script in a tutorial with a single command:

```bash
python3 -c '
import glob, re
for f in sorted(glob.glob("cs-decoder-tutorial/[0-9]*.md")):
    for i, code in enumerate(re.findall(r"```python\n(.*?)```", open(f).read(), re.DOTALL), 1):
        print(f"\n>>> Running {f} (snippet {i})")
        exec(code, {})
'
```
