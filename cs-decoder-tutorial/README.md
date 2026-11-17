# Compressive Sensing Decoders for Distributed Gradient Compression

## A Complete, Self-Contained Tutorial on the Pseudo-Inverse and $\ell_1$ Recovery (ISTA/FISTA)

Welcome to this complete tutorial on the two canonical decoders of linear compressive sensing—the **Moore–Penrose pseudo-inverse** (minimum-norm least squares) and **$\ell_1$ minimization** (Basis Pursuit / LASSO solved via ISTA and FISTA)—tailored specifically for **gradient compression in distributed deep learning**.

---

## 1. The Running Example: Distributed Gradient Compression

Every mathematical concept, derivation, and numerical experiment in this tutorial is anchored to the following system model:

1. **Block Slicing:** During distributed data-parallel training across $W$ workers, each worker $i \in \{1, \dots, W\}$ computes a local gradient tensor and slices it into contiguous 1D blocks $g_i \in \mathbb{R}^N$ of size **$N = 1024$** (`float32` values). When analyzing a single block in isolation, we denote the uncompressed vector as $x \in \mathbb{R}^N$.
2. **Linear Encoding (Projection):** Each block $x \in \mathbb{R}^N$ is compressed into a measurement vector $y \in \mathbb{R}^M$ via a matrix-vector multiplication:
   $$y = \Phi x$$
   where $\Phi \in \mathbb{R}^{M \times N}$ has compression ratio $r = M/N \in (0, 1]$. Our canonical operating point is **$r = 0.25$**, meaning **$M = 256$** measurements per block of $N = 1024$ parameters (a $4\times$ reduction in communication volume).
3. **Shared Sensing Matrix:** The matrix $\Phi$ is drawn from either an i.i.d. **Gaussian** distribution ($\Phi_{ij} \sim \mathcal{N}(0, \sigma^2)$) or an i.i.d. **Rademacher** distribution ($\Phi_{ij} \in \{-\sigma, +\sigma\}$ with equal probability $1/2$). It is generated from a **shared pseudorandom seed** across all workers and held **fixed for the training run** (or regenerated synchronously per step, which we compare in Chapter 6).
4. **AllReduce Aggregation in Measurement Space:** Because every worker uses the exact same matrix $\Phi$, linearity of matrix multiplication allows the workers to AllReduce their compressed measurements directly:
   $$\bar{y} = \frac{1}{W} \sum_{i=1}^W y_i = \frac{1}{W} \sum_{i=1}^W \Phi g_i = \Phi \left(\frac{1}{W} \sum_{i=1}^W g_i\right) = \Phi \bar{g}$$
   where $\bar{g} = \frac{1}{W}\sum_{i=1}^W g_i$ is the true averaged gradient block. Thus, **each receiver only needs to run the decoder $\mathcal{D}(\bar{y})$ once per block** after AllReduce, rather than decoding $W$ separate messages.
5. **The Two Candidate Decoders:**
   - **Decoder 1: Rescaled Moore–Penrose Pseudo-Inverse (The Decoder of Record):**
     $$\hat{x}_{\text{pinv}} = \frac{N}{M} \Phi^+ y = \frac{N}{M} \Phi^+ \Phi x$$
     Without the $\frac{N}{M}$ factor, $\hat{x}_{\text{raw}} = \Phi^+ \Phi x$ shrinks the component along the true gradient direction $x$ to $\frac{M}{N} = r$ of its original length in expectation. With the $\frac{N}{M}$ rescaling, the estimator is **unbiased** ($\mathbb{E}[\hat{x}_{\text{pinv}}] = x$) and injects isotropic zero-mean variance of exactly $\left(\frac{N}{M} - 1\right)\|x\|_2^2$ (for rotationally invariant $\Phi$).
   - **Decoder 2: $\ell_1$ Regularized Recovery via ISTA/FISTA:**
     $$\hat{x}_{\ell_1} = \arg\min_{z \in \mathbb{R}^N} \frac{1}{2}\|\Phi z - y\|_2^2 + \lambda \|z\|_1$$
     A sparsity-exploiting alternative. Whether it beats the pseudo-inverse at $r = 0.25$ on real gradient blocks is the question Chapters 4–6 answer.

---

## 2. Master Notation Table

| Symbol | Dimensions / Type | Mathematical Definition / Meaning | Role in Distributed Gradient Compression |
| :--- | :--- | :--- | :--- |
| $N$ | Integer $\ge 1$ | Ambient signal dimension | Gradient block length ($N = 1024$) |
| $M$ | Integer ($1 \le M \le N$) | Number of linear measurements | Compressed block length ($M = 256$) |
| $r$ | Scalar in $(0, 1]$ | Sampling / compression ratio $M/N$ | Bandwidth reduction factor ($r = 0.25$) |
| $W$ | Integer $\ge 1$ | Number of vectors in ensemble | Number of distributed workers / GPUs |
| $x$ or $g$ | $\mathbb{R}^N$ | True underlying signal vector | Single $N$-element gradient block |
| $g_i$ | $\mathbb{R}^N$ | $i$-th vector in ensemble | Local gradient block on worker $i$ |
| $\bar{g}$ | $\mathbb{R}^N$ | Ensemble mean $\frac{1}{W}\sum_{i=1}^W g_i$ | True synchronous AllReduce gradient average |
| $\Phi$ | $\mathbb{R}^{M \times N}$ | Sensing / projection matrix | Shared random compression matrix |
| $y$ | $\mathbb{R}^M$ | Linear measurement vector $y = \Phi x$ | Compressed payload transmitted via AllReduce |
| $\bar{y}$ | $\mathbb{R}^M$ | Averaged measurement $\frac{1}{W}\sum_{i=1}^W y_i$ | Result of AllReduce on compressed blocks |
| $\mathcal{D}(\cdot)$ | $\mathbb{R}^M \to \mathbb{R}^N$ | Reconstruction / decoding map | Gradient decompression operator |
| $\hat{x}$ | $\mathbb{R}^N$ | Reconstructed vector $\mathcal{D}(y)$ | Decoded gradient block passed to SGD/Adam |
| $\hat{x}_{\text{raw}}$ | $\mathbb{R}^N$ | Unscaled minimum-norm decode $\Phi^+ y$ | Biased projection onto $\text{row}(\Phi)$ |
| $\hat{x}_{\text{pinv}}$ | $\mathbb{R}^N$ | Rescaled decode $\frac{N}{M}\Phi^+ y$ | Unbiased pseudo-inverse gradient estimator |
| $\Phi^+$ | $\mathbb{R}^{N \times M}$ | Moore–Penrose pseudo-inverse of $\Phi$ | Minimum-$\ell_2$-norm linear decoder matrix |
| $P_{\mathcal{R}}$ | $\mathbb{R}^{N \times N}$ | Orthogonal projector $\Phi^+ \Phi$ onto $\text{row}(\Phi)$ | Rank-$M$ projection matrix |
| $P_{\mathcal{N}}$ | $\mathbb{R}^{N \times N}$ | Orthogonal projector $I_N - \Phi^+ \Phi$ onto $\text{null}(\Phi)$ | Rank-$(N-M)$ null-space projector |
| $U, \Sigma, V^T$ | $\mathbb{R}^{M\times M}, \mathbb{R}^{M\times N}, \mathbb{R}^{N\times N}$ | Singular Value Decomposition of $\Phi = U\Sigma V^T$ | Spectral decomposition of sensing matrix |
| $\sigma_j(\Phi)$ | Scalar $\ge 0$ | $j$-th singular value of $\Phi$ ($j=1,\dots,M$) | Gain of $\Phi$ along principal right singular vector $v_j$ |
| $\|x\|_0$ | Integer in $\{0,\dots,N\}$ | Number of non-zero entries $\#\{j : x_j \neq 0\}$ | Exact sparsity count |
| $\|x\|_1$ | Scalar $\ge 0$ | Manhattan norm $\sum_{j=1}^N |x_j|$ | Convex sparsity proxy |
| $\|x\|_2$ | Scalar $\ge 0$ | Euclidean norm $\sqrt{\sum_{j=1}^N x_j^2}$ | Energy / Euclidean length of block |
| $\|\Phi\|_2$ | Scalar $\ge 0$ | Spectral (operator) norm $\sigma_{\max}(\Phi)$ | Determines Lipschitz constant $L = \|\Phi\|_2^2$ |
| $\|\Phi\|_F$ | Scalar $\ge 0$ | Frobenius norm $\sqrt{\sum_{i,j}\Phi_{ij}^2} = \sqrt{\text{tr}(\Phi^T\Phi)}$ | Total matrix energy |
| $k$ | Integer in $\{1,\dots,N\}$ | Target sparsity level | Number of active coordinates in sparse model |
| $S$ | Subset of $\{1,\dots,N\}$ | Support set $\text{supp}(x) = \{j : x_j \neq 0\}$ | Indices of large gradient coordinates |
| $x_S$ | $\mathbb{R}^N$ or $\mathbb{R}^{|S|}$ | Restriction of $x$ to indices in $S$ | Top-$k$ component of $x$ |
| $\sigma_k(x)_p$ | Scalar $\ge 0$ | $\inf_{\|z\|_0 \le k} \|x - z\|_p = \|x - x_{\text{top-}k}\|_p$ | Best $k$-term approximation error in $\ell_p$ norm |
| $\delta_k$ | Scalar in $(0, 1)$ | Restricted Isometry Constant of order $k$ | Bounds how close $M\times k$ submatrices of $\Phi$ are to isometries |
| $\lambda$ | Scalar $> 0$ | LASSO regularization weight | Sparsity-vs-fit trade-off parameter |
| $L$ | Scalar $> 0$ | Lipschitz constant of $\nabla f(z)$, equal to $\|\Phi\|_2^2$ | Curvature bound for ISTA/FISTA step size |
| $\alpha$ | Scalar $> 0$ | Step size inside ISTA/FISTA (typically $1/L$) | Gradient descent step size in decoder |
| $\mathcal{S}_\tau(\cdot)$ | $\mathbb{R}^N \to \mathbb{R}^N$ | Soft-thresholding: $[\mathcal{S}_\tau(u)]_j = \text{sign}(u_j)\max(|u_j|-\tau, 0)$ | Proximal operator of $\tau \|\cdot\|_1$ |

---

## 3. Chapter Map

Chapters build on one another; each ends with check-your-understanding problems, solved in Chapter 99.

- **[Chapter 1: Prerequisites](./01-prerequisites.md)** — Which norms, subspaces, SVD, probability and convex-optimization tools do the later proofs use?
- **[Chapter 2: The Basic Problem — Underdetermined Linear Systems](./02-underdetermined-systems.md)** — What does the solution set of $y = \Phi x$ with $M < N$ look like?
- **[Chapter 3: The Pseudo-Inverse Decoder, Completely](./03-pseudo-inverse-decoder.md)** — Why is the rescaled pseudo-inverse unbiased, and what exact variance does it add?
- **[Chapter 4: Sparsity and $\ell_1$ Recovery, Completely](./04-sparsity-and-l1-recovery.md)** — When can $\ell_1$ minimization recover a sparse signal exactly, and from how many measurements?
- **[Chapter 5: Algorithms — ISTA and FISTA](./05-ista-and-fista-algorithms.md)** — How do we solve the LASSO efficiently, and at what cost?
- **[Chapter 6: Head-to-Head Comparison & Application to Gradient Compression](./06-gradient-compression-comparison.md)** — Which decoder wins on real gradients at $r = 0.25$, and why?
- **[Chapter 99: Solutions & Annotated References](./99-solutions-and-references.md)** — Worked solutions to the end-of-chapter problems and a bibliography.
