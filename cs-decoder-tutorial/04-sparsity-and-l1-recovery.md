# Chapter 4: Sparsity and $\ell_1$ Recovery, Completely

The pseudo-inverse decoder of Chapter 3 makes **zero assumptions** about the structure of $x$: it treats all directions in $\mathbb{R}^N$ equally and pays an unavoidable error of $(1 - M/N)\|x\|_2^2$ (unscaled) or $(N/M - 1)\|x\|_2^2$ (rescaled).

**Compressive Sensing (CS)**—pioneered in the mid-2000s by Candès, Romberg, Tao (2006a, 2006b) and Donoho (2006)—asks a bold question:
> *"What if the signal $x \in \mathbb{R}^N$ is **sparse** (only $k \ll M < N$ entries are non-zero) or **compressible** (most of its energy is concentrated in $k \ll M$ entries)? Can we recover $x$ **exactly** from $M < N$ linear measurements $y = \Phi x$?"*

In this chapter, we develop the complete theory of sparse and compressible recovery via $\ell_1$ minimization, and pinpoint the exact mathematical boundaries where $\ell_1$ succeeds and where it fails.

---

## 4.1 Sparse vs. Compressible Signals and Best $k$-Term Approximation

### Intuition
In idealized math problems, a vector $x \in \mathbb{R}^{1024}$ is **strictly $k$-sparse**: say, $k = 20$ coordinates are non-zero and the remaining $1004$ coordinates are *literally* $0.000000$.
In real life—and especially in deep learning gradients—no block of $1024$ floating-point numbers has $1004$ exact zeros. Instead, real signals have a spectrum of sorted magnitudes $|x_{(1)}| \ge |x_{(2)}| \ge \dots \ge |x_{(N)}|$. Whether $\ell_1$ recovery works depends entirely on **how fast those sorted magnitudes decay**.

### Definitions
1. **Strictly $k$-Sparse Signal:** A vector $x \in \mathbb{R}^N$ is $k$-sparse if $\|x\|_0 = |\text{supp}(x)| \le k$. We denote the set of all $k$-sparse vectors in $\mathbb{R}^N$ by $\Sigma_k = \{x \in \mathbb{R}^N : \|x\|_0 \le k\}$.
   *(Note: $\Sigma_k$ is a union of $\binom{N}{k}$ coordinate subspaces of dimension $k$, not a single subspace!)*
2. **Best $k$-Term Approximation $x_{\text{top-}k}$:** For any vector $x \in \mathbb{R}^N$, let $S_k \subset \{1, \dots, N\}$ be the indices of the $k$ largest entries of $x$ in absolute value. The **top-$k$ approximation** $x_{\text{top-}k}$ (also written $x_{S_k}$) keeps those $k$ entries and sets the remaining $N - k$ entries to $0$.
3. **Best $k$-Term Approximation Error $\sigma_k(x)_p$:** For any $p \ge 1$, the distance from $x$ to the closest $k$-sparse vector in the $\ell_p$ norm is:
   $$\sigma_k(x)_p = \min_{z \in \Sigma_k} \|x - z\|_p = \|x - x_{\text{top-}k}\|_p$$
   Specifically, for $p = 1$ (which governs $\ell_1$ recovery bounds!):
   $$\sigma_k(x)_1 = \sum_{j \notin S_k} |x_j| = \sum_{i = k+1}^N |x_{(i)}|$$
   Notice that $\sigma_k(x)_1$ is the **$\ell_1$ tail sum** of the $N - k$ smallest entries of $x$.
4. **Compressible (Power-Law Decay) Signal:** A signal $x$ is called **compressible** if its sorted magnitudes decay according to a power law $|x_{(i)}| \le C \cdot i^{-s}$ with exponent **$s > 1$**. Why $s > 1$? Because integrating the $\ell_1$ tail gives:
   $$\sigma_k(x)_1 = \sum_{i=k+1}^N |x_{(i)}| \approx C \int_k^N t^{-s} \, dt \propto k^{-(s - 1)}$$
   - If **$s > 1$** (fast decay, e.g., wavelet coefficients of natural images), $\sigma_k(x)_1 \to 0$ rapidly as $k$ grows.
   - If **$s \le 1$** (slow decay or flat/Gaussian-like entries, as in most neural network gradient blocks!), the $\ell_1$ tail sum $\sum_{i=k+1}^N |x_{(i)}|$ **diverges** with $N$ and actually dwarfs the $\ell_1$ norm of the top-$k$ coordinates! This observation will be key to understanding why $\ell_1$ fails on gradients in Section 4.7 and Chapter 6.

---

## 4.2 $\ell_0$ Minimization and Why It Is Intractable

### Intuition & Statement
If we know the true vector $x$ is sparse, the most direct decoder is **$\ell_0$ minimization**: find the sparsest vector consistent with $y = \Phi x$:
$$(\text{P}_0) \qquad \hat{x}_{\ell_0} = \arg\min_{z \in \mathbb{R}^N} \|z\|_0 \quad \text{subject to} \quad \Phi z = y$$

**Theorem 4.1 (Exact Recovery via $\ell_0$ Minimization).**
*Suppose every subset of $2k$ columns of $\Phi \in \mathbb{R}^{M \times N}$ is linearly independent (which holds with probability $1$ for i.i.d. Gaussian $\Phi$ as soon as **$M \ge 2k$**). Then for every $k$-sparse vector $x \in \Sigma_k$, $(\text{P}_0)$ recovers $\hat{x}_{\ell_0} = x$ uniquely.*

**Proof:** Suppose $z$ satisfies $\Phi z = y = \Phi x$ and $\|z\|_0 \le \|x\|_0 \le k$. Then $h = z - x$ satisfies $\Phi h = 0$, and $\|h\|_0 = \|z - x\|_0 \le \|z\|_0 + \|x\|_0 \le 2k$. Since no non-zero vector supported on $\le 2k$ columns of $\Phi$ can map to zero, $h = 0 \implies z = x$. $\blacksquare$

### Why Can't We Use $(\text{P}_0)$?
Because $(\text{P}_0)$ is **NP-hard** in general (Natarajan, 1995)! To solve $(\text{P}_0)$ directly when $N = 1024$ and $k = 50$, you would have to test which subset of $k$ columns of $\Phi$ spans $y$. The number of subsets is:
$$\binom{1024}{50} \approx 3.4 \times 10^{84}$$
which exceeds the number of atoms in the observable universe ($\sim 10^{80}$).

---

## 4.3 $\ell_1$ as Convex Relaxation and the "Diamond Touches the Plane" Geometry

### Intuition
Look at how $\|z\|_p^p = \sum_{j=1}^N |z_j|^p$ behaves as $p$ varies from $2$ down to $0$:
- At $p = 2$: Smooth sphere (convex, favors dense minimum-energy vectors).
- At $1 < p < 2$: Smooth rounded balls (convex, no sharp corners on the axes).
- At **$p = 1$**: Cross-polytope / diamond (**still convex**, AND has sharp pointy corners on the coordinate axes!).
- At $0 < p < 1$: Inward-curved star shapes (sparse corners, but **non-convex** with exponentially many local minima).

Thus, **$p = 1$ is the unique sweet spot where convexity and axis-aligned corners meet!**

### The "Diamond Touches the Hyperplane" Picture
Consider solving **Basis Pursuit (BP)**:
$$(\text{BP}) \qquad \hat{x}_{\text{BP}} = \arg\min_{z \in \mathbb{R}^N} \|z\|_1 \quad \text{subject to} \quad \Phi z = y$$
Geometrically, imagine blowing up an $\ell_1$ diamond $B_1(R) = \{z : \|z\|_1 \le R\}$ starting from radius $R = 0$ at the origin until it first touches the affine solution space $\mathcal{H}_y = x + \text{null}(\Phi)$:

```
           Compare L2 Sphere (Pseudo-Inverse) vs. L1 Diamond (Basis Pursuit) in R^2:

        z_2                                             z_2
         ^      \ H_y: Φz = y                            ^      \ H_y: Φz = y
         |       \                                       |       \
         |     ..-* x_raw = Φ⁺y                          |        * x = [0, 3]^T (Corner!)
         |   .'    \  '.                                 |       /|\
         |  /       \   \                                |     /  |  \  L1 Diamond
      ---+-----------+---+---> z_1                    ---+----+---+----+---> z_1
         |  \           /\                               |     \  |  /  |z_1|+|z_2| <= 3
         |   '.       .'  \                              |       \|/
         |     '-----'     \                             |        '
     L2 Ball touches H_y in the                     L1 Diamond touches H_y right at
     dense interior (perpendicular)!                the sparse axis corner [0, 3]^T!
```

When does the $\ell_1$ diamond fail to touch $\mathcal{H}_y$ at the true sparse point $x$? Only if the affine flat $\mathcal{H}_y = x + \text{null}(\Phi)$ is tilted at a steep enough angle that it **slices into the interior** of the $\ell_1$ ball $\{z : \|z\|_1 \le \|x\|_1\}$. That geometric condition leads directly to the **Null Space Property** in Section 4.5!

---

## 4.4 Basis Pursuit (BP), Basis Pursuit Denoising (BPDN), and LASSO

In practice, when signals are only approximately sparse or measurements contain noise, solving the equality-constrained linear program $(\text{BP})$ is either too rigid or too slow (interior-point LP solvers scale as $O(N^3)$). Instead, compressive sensing uses three closely related convex formulations:

| Name | Optimization Problem | Parameters & Use Case |
| :--- | :--- | :--- |
| **Basis Pursuit (BP)** (Chen, Donoho, Saunders, 1998) | $\displaystyle \min_{z \in \mathbb{R}^N} \|z\|_1 \quad \text{s.t.} \quad \Phi z = y$ | Zero parameters; used when measurements $y = \Phi x$ are noiseless and we want exact equality $\Phi \hat{x} = y$. |
| **Basis Pursuit Denoising (BPDN) — Constrained Form** (Candès, Romberg, Tao, 2006b) | $\displaystyle \min_{z \in \mathbb{R}^N} \|z\|_1 \quad \text{s.t.} \quad \|\Phi z - y\|_2 \le \varepsilon$ | Parameter $\varepsilon \ge 0$ bounds the measurement residual; used in theoretical stability theorems. |
| **LASSO / Unconstrained BPDN** (Tibshirani, 1996) | $\displaystyle \min_{z \in \mathbb{R}^N} \frac{1}{2}\|\Phi z - y\|_2^2 + \lambda \|z\|_1$ | Parameter $\lambda > 0$ balances data fit vs. sparsity; **solved directly by first-order proximal algorithms (ISTA / FISTA)**. |

### How Do BP, BPDN, and LASSO Relate?
1. **Equivalence of Constrained BPDN and Unconstrained LASSO (via Lagrangian Duality):**
   Because both $\|\Phi z - y\|_2^2$ and $\|z\|_1$ are convex, Lagrangian duality guarantees a one-to-one correspondence between $\varepsilon > 0$ and $\lambda > 0$: for every $\lambda > 0$, the LASSO solution $\hat{x}(\lambda)$ is also the solution to constrained BPDN with $\varepsilon = \|\Phi \hat{x}(\lambda) - y\|_2$.
2. **Limit as $\lambda \to 0^+$ Recovers Basis Pursuit:**
   As $\lambda \to 0^+$, the penalty on $\|\Phi z - y\|_2^2$ dominates over $\lambda \|z\|_1$, forcing $\Phi z = y$ while breaking ties inside $\mathcal{H}_y$ by minimizing $\|z\|_1$. Thus:
   $$\lim_{\lambda \to 0^+} \hat{x}_{\text{LASSO}}(\lambda) = \hat{x}_{\text{BP}}$$
3. **What Happens for Finite $\lambda > 0$ (The Shrinkage Bias):**
   At any finite $\lambda > 0$, the optimality condition of LASSO requires $\Phi^T(y - \Phi \hat{x}) \in \lambda \partial \|\hat{x}\|_1$, so $\Phi \hat{x} \neq y$: LASSO deliberately leaves a non-zero residual $y - \Phi \hat{x}$ in order to **shrink** the magnitudes of $\hat{x}$ toward zero!

---

## 4.5 The Null Space Property (NSP) and Restricted Isometry Property (RIP)

Why and when do random Gaussian or Rademacher matrices $\Phi \in \mathbb{R}^{M \times N}$ guarantee that $\ell_1$ minimization recovers $k$-sparse vectors? Two fundamental properties explain this completely (Foucart & Rauhut, 2013).

### 1. The Null Space Property (NSP) — The Exact Necessary & Sufficient Condition

**Intuition:** Suppose $x$ is supported on a set $S \subset \{1, \dots, N\}$ of size $|S| \le k$. Every other candidate $z \in \mathcal{H}_y$ has the form $z = x + h$ where $h \in \text{null}(\Phi) \setminus \{0\}$. For $\|x + h\|_1 > \|x\|_1$ to hold, adding $h$ must increase the $\ell_1$ norm on the off-support indices $S^c = \{1, \dots, N\} \setminus S$ by **more** than it can possibly decrease the $\ell_1$ norm on $S$! In other words: **no vector $h \in \text{null}(\Phi) \setminus \{0\}$ is allowed to concentrate half or more of its $\ell_1$ norm on any $k$ coordinates.**

**Theorem 4.2 (Null Space Property; Cohen, Dahmen, DeVore, 2009).**
*Every $k$-sparse vector $x \in \Sigma_k$ is the **unique** solution to Basis Pursuit $(\text{BP})$ with $y = \Phi x$ if and only if $\Phi$ satisfies the **Null Space Property of order $k$**: for every non-zero $h \in \text{null}(\Phi) \setminus \{0\}$ and every index set $S \subset \{1, \dots, N\}$ with $|S| \le k$,*
$$\|h_S\|_1 < \|h_{S^c}\|_1 \quad \left(\text{equivalently, } \|h_S\|_1 < \frac{1}{2}\|h\|_1\right)$$

**Proof (Sufficiency — 4 lines!):**
Let $x$ be supported on $S$ ($|S| \le k$, so $x_{S^c} = 0$), and let $z = x + h$ with $h \in \text{null}(\Phi) \setminus \{0\}$. Split the $\ell_1$ norm into $S$ and $S^c$ and apply the reverse triangle inequality on $S$:
$$\|x + h\|_1 = \|x_S + h_S\|_1 + \|h_{S^c}\|_1 \ge \|x_S\|_1 - \|h_S\|_1 + \|h_{S^c}\|_1 = \|x\|_1 + \underbrace{(\|h_{S^c}\|_1 - \|h_S\|_1)}_{> 0 \text{ by NSP}} > \|x\|_1 \quad \blacksquare$$

---

### 2. The Restricted Isometry Property (RIP) — Geometry Preservation on Sparse Vectors

While NSP is exact, it is hard to quantify directly in presence of measurement noise. Candès & Tao (2005) introduced a stronger, wonderfully geometric condition: the **Restricted Isometry Property (RIP)**.

**Intuition:** An $M \times N$ matrix with $M < N$ cannot preserve the Euclidean length $\|\Phi v\|_2 \approx \|v\|_2$ of *every* vector $v \in \mathbb{R}^N$ (because $N - M$ dimensions are in $\text{null}(\Phi)$). However, if we restrict our attention to **$k$-sparse vectors** $v \in \Sigma_k$, multiplying $\Phi v$ only uses $k$ columns of $\Phi$ at a time! If $k \ll M$, every $M \times k$ submatrix $\Phi_S$ is a **tall** matrix whose columns can be nearly orthonormal!

**Definition 4.1 (Restricted Isometry Property; Candès & Tao, 2005).**
*A matrix $\Phi \in \mathbb{R}^{M \times N}$ satisfies the **Restricted Isometry Property of order $k$** with constant $\delta_k \in (0, 1)$ if for **all** $k$-sparse vectors $v \in \Sigma_k$:*
$$(1 - \delta_k) \|v\|_2^2 \le \|\Phi v\|_2^2 \le (1 + \delta_k) \|v\|_2^2$$
*(Note: For this definition, the columns of $\Phi$ are scaled to unit expected norm, i.e., $\Phi_{ij} \sim \mathcal{N}(0, 1/M)$ or $\{\pm 1/\sqrt{M}\}$. Equivalently, all eigenvalues of $\Phi_S^T \Phi_S$ for every $|S| \le k$ lie in $[1 - \delta_k, 1 + \delta_k]$.)*

**Theorem 4.3 (RIP Implies NSP and Exact Recovery; Candès, 2008).**
*If $\Phi$ satisfies the RIP of order $2k$ with $\delta_{2k} < \sqrt{2} - 1 \approx 0.414$ (later sharpened to $\delta_{2k} < 1/\sqrt{2} \approx 0.707$ by Cai & Zhang, 2014), then $\Phi$ satisfies the robust Null Space Property of order $k$, and Basis Pursuit recovers every $k$-sparse $x$ exactly.*

**Proof Sketch (Why RIP of order $2k$ prevents $h \in \text{null}(\Phi)$ from being concentrated on $S$):**
Take $h \in \text{null}(\Phi)$ and partition its indices in decreasing order of magnitude into blocks $S_0$ (the $k$ largest), $S_1$ (the next $k$ largest), $S_2$, etc. Since $\Phi h = 0$, we have $\Phi(h_{S_0} + h_{S_1}) = -\sum_{m \ge 2} \Phi h_{S_m}$. Because $h_{S_0} + h_{S_1}$ is $2k$-sparse, RIP gives $\|\Phi(h_{S_0} + h_{S_1})\|_2 \ge \sqrt{1 - \delta_{2k}} \|h_{S_0}\|_{2}$. On the other hand, each $h_{S_m}$ ($m \ge 2$) has entries smaller than the average entry of $h_{S_{m-1}}$, so $\|h_{S_m}\|_2 \le \frac{1}{\sqrt{k}}\|h_{S_{m-1}}\|_1$. Summing the triangle inequality over $m \ge 2$ and applying Cauchy–Schwarz $\|h_{S_0}\|_1 \le \sqrt{k}\|h_{S_0}\|_2$ directly yields $\|h_{S_0}\|_1 \le \rho \|h_{S_0^c}\|_1$ with $\rho < 1$. $\blacksquare$

---

## 4.6 The Measurement Bound $M \gtrsim C k \log(N/k)$ and Why Gaussian & Rademacher Matrices Satisfy RIP

### Intuition & Derivation Sketch (Baraniuk, Davenport, DeVore, Wakin, 2008)
How large must $M$ be so that an $M \times N$ random Gaussian or Rademacher matrix $\Phi$ (with entry variance $1/M$) satisfies the RIP of order $k$ with high probability? Let us derive the famous $M \gtrsim C k \log(N/k)$ bound in 3 transparent steps:

1. **Step 1: Concentration for a Single Vector $v \in \mathbb{R}^N$.**
   For both i.i.d. Gaussian $\mathcal{N}(0, 1/M)$ and i.i.d. Rademacher $\{\pm 1/\sqrt{M}\}$ matrices, $\mathbb{E}[\|\Phi v\|_2^2] = \|v\|_2^2$, and the random variable $\|\Phi v\|_2^2$ is a sum of $M$ independent sub-exponential terms. By Bernstein's / sub-Gaussian concentration inequality, for any fixed $v$ and $\epsilon \in (0, 1)$:
   $$\mathbb{P}\Big( \big|\|\Phi v\|_2^2 - \|v\|_2^2\big| > \epsilon \|v\|_2^2 \Big) \le 2 \exp(-c_0 M \epsilon^2)$$
2. **Step 2: Covering a Single $k$-Dimensional Coordinate Subspace $\mathbb{R}^k$.**
   Fix one support set $S \subset \{1, \dots, N\}$ of size $|S| = k$. By a standard $\epsilon$-net covering argument on the unit sphere in $\mathbb{R}^k$ (which requires at most $(3/\epsilon)^k$ points), the matrix $\Phi_S$ fails to be an $\epsilon$-isometry on $\text{span}(e_j : j \in S)$ with probability at most:
   $$2 \left(\frac{9}{\delta_k}\right)^k \exp(-c_0 M \delta_k^2)$$
3. **Step 3: Union Bound Over All $\binom{N}{k}$ Coordinate Subspaces!**
   There are $\binom{N}{k} \le \left(\frac{e N}{k}\right)^k = \exp\left(k \log\frac{e N}{k}\right)$ possible support sets $S$ of size $k$. Taking a union bound over all $\binom{N}{k}$ subspaces, the probability that RIP fails on *any* $k$-sparse vector is at most:
   $$\mathbb{P}(\text{RIP}_k \text{ fails}) \le 2 \exp\left( k \log\left(\frac{eN}{k}\right) + k \log\left(\frac{9}{\delta_k}\right) - c_0 M \delta_k^2 \right)$$
   For this failure probability to be tiny ($\le e^{-\gamma M}$), the positive exponent $k \log(eN/k)$ must be smaller than $c_0 M \delta_k^2$:
   $$\boxed{M \ge C \cdot k \log\left(\frac{N}{k}\right)}$$

> **Crucial Takeaway on Gaussian vs. Rademacher for $\ell_1$ Recovery:**
> Because both Gaussian and Rademacher entries are independent, zero-mean, unit-variance (after scaling), and **sub-Gaussian** with nearly identical sub-Gaussian norms, **both Gaussian and Rademacher matrices satisfy the RIP with the exact same asymptotic scaling $M \gtrsim C k \log(N/k)$** and exhibit the exact same empirical phase transition for $N = 1024$!

---

## 4.7 The Donoho–Tanner Phase Transition

### Intuition
The bound $M \ge C k \log(N/k)$ hides the constant $C$. When $N = 1024$ and $M = 256$ ($r = 0.25$), what is the **exact maximum number of non-zeros $k_{\max}$** that $\ell_1$ minimization can actually recover?
Donoho & Tanner (2005, 2009) solved this problem exactly using high-dimensional polytope geometry (computing the probability that a random $(N-M)$-dimensional plane misses the interior of the $N$-dimensional cross-polytope).

### Statement (Standard Result: Donoho & Tanner, 2009)
Define two dimensionless ratios:
- **Undersampling ratio:** $\delta = \frac{M}{N} \in (0, 1)$ *(in our notation, $\delta = r = 0.25$)*.
- **Sparsity-to-measurements ratio:** $\rho = \frac{k}{M} \in (0, 1)$ *(so the overall sparsity fraction is $\frac{k}{N} = \delta \cdot \rho$)*.

As $N, M, k \to \infty$ with fixed ratios $(\delta, \rho)$, there is a sharp **weak phase transition curve** $\rho_W(\delta)$ in the $(\delta, \rho)$ plane:
- **Below the curve ($\rho < \rho_W(\delta)$):** Basis Pursuit recovers a generic $k$-sparse vector $x$ with probability $\to 1$.
- **Above the curve ($\rho > \rho_W(\delta)$):** Basis Pursuit **fails** to recover $x$ with probability $\to 1$!

Here are the exact numerical values of the Donoho–Tanner phase transition $\rho_W(\delta)$ across key compression ratios:

| Compression Ratio $r = \delta = M/N$ | Critical Ratio $\rho_W(\delta) = k_{\max}/M$ | Max Recoverable Sparsity Fraction $k_{\max}/N = r \cdot \rho_W(r)$ | Max Recoverable Non-Zeros $k_{\max}$ at $N = 1024$ |
| :---: | :---: | :---: | :---: |
| $0.10$ ($M = 102$) | $\approx 0.193$ | $1.9\%$ of entries | **$k_{\max} \approx 20$** out of $1024$ |
| **$0.25$ ($M = 256$)** | **$\approx 0.241$** | **$6.0\%$ of entries** | **$k_{\max} \approx 62$ out of $1024$** |
| $0.50$ ($M = 512$) | $\approx 0.332$ | $16.6\%$ of entries | **$k_{\max} \approx 170$** out of $1024$ |
| $0.75$ ($M = 768$) | $\approx 0.471$ | $35.3\%$ of entries | **$k_{\max} \approx 362$** out of $1024$ |

> **Look at the row for your setting ($r = 0.25, M = 256, N = 1024$):**
> Even for an **idealized, noiseless, strictly sparse** vector $x \in \mathbb{R}^{1024}$, $\ell_1$ minimization can only recover $x$ if at most **$k_{\max} \approx 62$ out of $1024$ entries ($6.0\%$)** are non-zero! As soon as a block has $70, 100,$ or $1024$ active coordinates, $\ell_1$ minimization sits **above the Donoho–Tanner phase transition** and breaks down completely.

---

## 4.8 Stability Bounds for Compressible Signals and Noisy Measurements

What happens when $x \in \mathbb{R}^N$ is **not** strictly $k$-sparse, or when measurements have error $y = \Phi x + e$ with $\|e\|_2 \le \varepsilon$? This is governed by the celebrated **Candès–Romberg–Tao (2006b) $\ell_2$-$\ell_1$ instance-optimality theorem**.

### Statement (Standard Result: Candès, Romberg, Tao, 2006b; Foucart & Rauhut, 2013, Thm 6.12)
**Theorem 4.4 (Noisy and Compressible $\ell_1$ Recovery Bound).**
*Suppose $\Phi \in \mathbb{R}^{M \times N}$ (scaled so columns have unit norm) satisfies the RIP of order $2k$ with $\delta_{2k} < \sqrt{2} - 1$. Let $y = \Phi x + e$ with $\|e\|_2 \le \varepsilon$, and let $\hat{x}$ be the solution to BPDN ($\min \|z\|_1 \text{ s.t. } \|\Phi z - y\|_2 \le \varepsilon$). Then:*
$$\|\hat{x} - x\|_2 \le C_0 \frac{\sigma_k(x)_1}{\sqrt{k}} + C_1 \varepsilon$$
*where $\sigma_k(x)_1 = \|x - x_{\text{top-}k}\|_1$ is the $\ell_1$ tail error of $x$ beyond its $k$ largest entries, and $C_0, C_1 > 0$ are constants depending only on $\delta_{2k}$ (for instance, at $\delta_{2k} = 0.2$, $C_0 \approx 4.2$ and $C_1 \approx 8.5$).*

### Why $\frac{\sigma_k(x)_1}{\sqrt{k}}$ Explains the Collapse of $\ell_1$ on Dense Gradients
Let us plug a dense Gaussian-like gradient block $x \in \mathbb{R}^{1024}$ (with noiseless measurements $\varepsilon = 0$) into Theorem 4.4 at $M = 256$:
- For $\Phi$ to have a small RIP constant $\delta_{2k}$ at $M = 256, N = 1024$, the effective sparsity order $k$ is at most $k \approx 30\text{–}50$.
- For a dense vector $x \in \mathbb{R}^{1024}$, almost all of its entries lie outside the top $k = 40$ coordinates, so by Cauchy–Schwarz:
  $$\sigma_k(x)_1 = \|x - x_{\text{top-}k}\|_1 \approx \|x\|_1 \approx \sqrt{\frac{2}{\pi} N} \, \|x\|_2 \approx 0.8 \sqrt{N} \, \|x\|_2$$
- Therefore, the error term in Theorem 4.4 scales as:
  $$\frac{\sigma_k(x)_1}{\sqrt{k}} \approx 0.8 \sqrt{\frac{N}{k}} \, \|x\|_2 \approx 0.8 \sqrt{\frac{1024}{40}} \, \|x\|_2 \approx 4.0 \, \|x\|_2$$
Notice the contrast:
- For **strictly sparse** $x$ ($\sigma_k(x)_1 = 0$), Theorem 4.4 gives $\|\hat{x} - x\|_2 = 0$ (**exact recovery!**).
- For **dense** $x$ ($\sigma_k(x)_1 \sim \sqrt{N}\|x\|_2$), the $\ell_1$ tail $x - x_{\text{top-}k}$ leaks through $\Phi$ just like giant measurement noise of size $\sqrt{N/k}\|x\|_2$, destroying the recovery of even the top-$k$ coordinates!

---

## 4.9 Empirical Verification in NumPy: The Donoho–Tanner Phase Transition

This runnable script sweeps the sparsity $k$ across the Donoho–Tanner boundary ($k_{\max} \approx 0.241 M$) at ratio $r = M/N = 0.25$ using FISTA to solve Basis Pursuit ($\lambda \to 0$) and verifies the sharp cliff from $100\%$ recovery to $0\%$ recovery:

```python
import numpy as np

def fista_basis_pursuit(Phi, y, lam_final=1e-4, stages=5, iter_per_stage=120):
    """Solve Basis Pursuit (min ||z||_1 s.t. Phi z = y) via warm-started FISTA continuation."""
    M, N = Phi.shape
    L = np.linalg.norm(Phi, ord=2) ** 2
    alpha = 1.0 / L
    lam_start = 0.2 * np.max(np.abs(Phi.T @ y))
    lams = np.geomspace(lam_start, lam_final, stages)

    z = np.zeros(N)
    for lam in lams:
        tau = alpha * lam
        w = z.copy()
        t = 1.0
        for _ in range(iter_per_stage):
            grad = Phi.T @ (Phi @ w - y)
            u = w - alpha * grad
            z_next = np.sign(u) * np.maximum(np.abs(u) - tau, 0.0)
            t_next = 0.5 * (1.0 + np.sqrt(1.0 + 4.0 * t * t))
            w = z_next + ((t - 1.0) / t_next) * (z_next - z)
            z, t = z_next, t_next
    return z

rng = np.random.default_rng(7)
# Use N=256, M=64 (same r = 0.25) so the full phase transition sweep runs in ~2 seconds
N, M = 256, 64
r = M / N

print(f"Donoho-Tanner Phase Transition Sweep at r = M/N = {r:.2f} (N={N}, M={M})")
print(f"Theoretical critical sparsity k_max ≈ 0.241 * M = {0.241*M:.1f}\n")
print(f"{'Sparsity k':>10} | {'k / M':>7} | {'L1 Rel Error':>14} | {'Pinv Rel Error':>15} | {'L1 Success Rate':>15}")
print("-" * 72)

for k in [4, 8, 12, 15, 18, 24, 32, 64]:
    l1_errs, pinv_errs, successes = [], [], 0
    trials = 10
    for _ in range(trials):
        Phi = rng.normal(0.0, 1.0 / np.sqrt(M), size=(M, N))
        x = np.zeros(N)
        supp = rng.choice(N, size=k, replace=False)
        x[supp] = rng.standard_normal(k)
        y = Phi @ x

        x_l1 = fista_basis_pursuit(Phi, y, lam_final=1e-4)
        x_raw = np.linalg.pinv(Phi) @ y

        rel_l1 = np.linalg.norm(x_l1 - x) / np.linalg.norm(x)
        rel_pinv = np.linalg.norm(x_raw - x) / np.linalg.norm(x)
        l1_errs.append(rel_l1)
        pinv_errs.append(rel_pinv)
        if rel_l1 < 1e-2:
            successes += 1

    print(f"{k:10d} | {k/M:7.3f} | {np.mean(l1_errs):14.4f} | {np.mean(pinv_errs):15.4f} | {100*successes/trials:14.0f}%")
```

---

## 4.10 Check Your Understanding

*(Full solutions are in [Chapter 99](./99-solutions-and-references.md).)*

1. **Verifying the Null Space Property on a Concrete $2 \times 3$ Matrix:** Return to the matrix $\Phi = \begin{bmatrix} 1 & 0 & 1 \\ 0 & 1 & 1 \end{bmatrix}$ from Chapter 2, Example 2. Find a basis vector $h$ for $\text{null}(\Phi)$ and check directly whether $\|h_S\|_1 < \|h_{S^c}\|_1$ holds for **every** subset $S \subset \{1, 2, 3\}$ of size $k = 1$. What does Theorem 4.2 then guarantee for all 1-sparse vectors $x \in \mathbb{R}^3$?
2. **Why $0 < p < 1$ Fails Convexity:** Take two 1-sparse points on the axes in $\mathbb{R}^2$: $u = [1, 0]^T$ and $v = [0, 1]^T$. For $p = 1/2$, compute $\|u\|_{1/2}^{1/2} = \sum |u_j|^{1/2}$, $\|v\|_{1/2}^{1/2}$, and the midpoint value $\|\frac{1}{2}u + \frac{1}{2}v\|_{1/2}^{1/2}$. Why does this prove that minimizing $\sum |z_j|^p$ on a line can trap gradient-based solvers in a non-optimal corner?
3. **Power-Law Compressibility Calculation:** Suppose a block $x \in \mathbb{R}^{1024}$ has sorted magnitudes $|x_{(i)}| = i^{-s}$. Compute the ratio of the tail $\ell_1$ norm $\sigma_{62}(x)_1 = \sum_{i=63}^{1024} i^{-s}$ to the top-62 $\ell_1$ norm $\sum_{i=1}^{62} i^{-s}$ for (a) $s = 2.0$ (highly compressible) vs. (b) $s = 0.5$ (weakly decaying, closer to real gradients). How does this explain why Theorem 4.4 succeeds for (a) and fails for (b)?
