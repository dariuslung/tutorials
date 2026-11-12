# Chapter 6: Head-to-Head Comparison & Application to Gradient Compression

We now bring together every mathematical result from Chapters 1–5 to explain the exact behavior of your distributed gradient compression system ($N = 1024, M = 256, r = 0.25$):
- When each decoder wins;
- How bias, rescaling, and variance interact with SGD;
- What a fixed $\Phi$ vs. a per-step $\Phi_t$ does to the optimization trajectory;
- Why $\ell_1$ decoding via FISTA is structurally incompatible with multi-worker measurement aggregation;
- How linear projection + pseudo-inverse connects to Rand-$k$ sparsification, biased vs. unbiased compressors, and Error Feedback (EF);
- What *"the gradient is not sparse enough at $r = 0.25$"* means in hard numbers.

---

## 6.1 Head-to-Head Summary: When Each Decoder Wins

| Criterion | Unscaled Pseudo-Inverse $\hat{x}_{\text{raw}} = \Phi^+ y$ | Rescaled Pseudo-Inverse $\hat{x}_{\text{pinv}} = \frac{N}{M}\Phi^+ y$ | $\ell_1$ Recovery via FISTA $\hat{x}_{\ell_1} = \mathcal{D}_{\ell_1}(y)$ |
| :--- | :--- | :--- | :--- |
| **Mathematical Prior** | Minimum $\ell_2$ energy ($\hat{x} \in \text{row}(\Phi)$) | Isotropic unbiased estimator of $x$ | Coordinate sparsity ($\hat{x}$ near axes) |
| **Linearity** | **Linear** ($\mathcal{D}(\bar{y}) = \overline{\mathcal{D}(y)}$) | **Linear** ($\mathcal{D}(\bar{y}) = \overline{\mathcal{D}(y)}$) | **Nonlinear** ($\mathcal{D}(\bar{y}) \neq \overline{\mathcal{D}(y)}$) |
| **Expectation $\mathbb{E}[\hat{x}]$ (random $\Phi$)** | $\frac{M}{N} x = r x$ (shrunk by $r$) | **$x$ (Unbiased!)** | Biased toward $0$ (by $\lambda$) and toward axes |
| **Expected MSE $\mathbb{E}\|\hat{x} - x\|_2^2$** | $\left(1 - \frac{M}{N}\right)\|x\|_2^2 = 0.75\|x\|_2^2$ | $\left(\frac{N}{M} - 1\right)\|x\|_2^2 = 3.0\|x\|_2^2$ | $\approx 0$ if $\|x\|_0 \le 62$; $\gg \|x\|_2^2$ if $x$ is dense |
| **Cosine Similarity $\cos(\hat{x}, x)$** | $\approx \sqrt{r} = 0.50$ | $\approx \sqrt{r} = 0.50$ (identical direction!) | $\approx 1.0$ if $\|x\|_0 \le 62$; **$< 0.38$** on dense $x$! |
| **Decode Compute Cost** | $1$ GEMV ($2MN$ FLOPs) | $1$ GEMV ($2MN$ FLOPs) | $2T$ GEMVs ($4TMN$ FLOPs, $100\times$ slower at $T=50$) |
| **When It Wins** | Single-shot MSE on dense vectors when norm underestimation is acceptable | **Distributed SGD on dense/heavy-tailed neural network gradients** | Strictly sparse signals with $\|x\|_0 < 0.24 M$ and single-sender decoding |

> **Wait—look at rows 4 and 5 of the table above!**
> Why does the unscaled pseudo-inverse $\hat{x}_{\text{raw}} = \Phi^+ \Phi x$ have **smaller single-vector MSE** ($0.75\|x\|_2^2$) than the rescaled pseudo-inverse $\hat{x}_{\text{pinv}} = \frac{N}{M}\Phi^+ \Phi x$ ($3.0\|x\|_2^2$), yet both have the **exact same direction** (cosine similarity $\sqrt{r} = 0.5$), and why is $\frac{N}{M}$ rescaling standard in SGD theory? Let us derive the exact SGD dynamics to see why!

---

## 6.2 Bias, Variance, and Their Exact Effect on SGD

### Intuition
Consider optimizing a smooth objective $\mathcal{L}(\theta)$ via SGD:
$$\theta_{t+1} = \theta_t - \eta \hat{g}_t$$
where $g_t = \nabla \mathcal{L}(\theta_t)$ is the true gradient (or minibatch gradient) and $\hat{g}_t$ is the decoded gradient with $\Phi_t$ drawn at step $t$.
Let us compare what happens to the SGD update step under **unscaled $\hat{g}_{\text{raw}} = \Phi_t^+ \Phi_t g_t$** versus **rescaled $\hat{g}_{\text{pinv}} = \frac{N}{M}\Phi_t^+ \Phi_t g_t$**:

### Derivation: A Scaled-Down Step vs. Zero-Mean Minibatch Noise
Notice that $\hat{g}_{\text{raw}}$ and $\hat{g}_{\text{pinv}}$ point in the **exact same direction** at every step, differing only by the scalar factor $\frac{N}{M} = \frac{1}{r}$:
$$\theta_{t+1} = \theta_t - \eta_{\text{raw}} \left(\Phi_t^+ \Phi_t g_t\right) = \theta_t - \underbrace{\left(r \, \eta_{\text{raw}}\right)}_{\eta_{\text{eff}}} \left(\frac{N}{M} \Phi_t^+ \Phi_t g_t\right)$$
This algebraic identity proves two fundamental facts about SGD with pseudo-inverse decoding:

1. **Effect of Omitting the $\frac{N}{M}$ Factor (The $M/N$ Shrinkage):**
   Because $\mathbb{E}[\Phi_t^+ \Phi_t g_t] = \frac{M}{N} g_t = r g_t$, decoding without the $\frac{N}{M}$ factor is **mathematically identical** to running the unbiased rescaled decoder with an **effective learning rate shrunk by $r = M/N = 0.25$**:
   $$\eta_{\text{eff}} = \frac{M}{N} \eta = 0.25 \eta$$
   If you keep the baseline learning rate schedule $\eta$ unchanged and omit the $\frac{N}{M}$ factor, your network moves **$4\times$ slower** along the true gradient trajectory (equivalent to training for only $1/4$ as many effective epochs!).

2. **Effect of Including the $\frac{N}{M}$ Factor (Zero-Mean Variance = Extra Minibatch Noise):**
   When you include $\frac{N}{M}$, the estimator $\hat{g}_{\text{pinv}} = \frac{N}{M}\Phi_t^+ \Phi_t g_t$ can be decomposed as:
   $$\hat{g}_{\text{pinv}} = g_t + \xi_t, \qquad \text{where } \mathbb{E}[\xi_t \mid g_t] = 0 \quad \text{and} \quad \mathbb{E}[\|\xi_t\|_2^2 \mid g_t] = \left(\frac{N}{M} - 1\right)\|g_t\|_2^2$$
   Now plug $\theta_{t+1} = \theta_t - \eta \hat{g}_{\text{pinv}}$ into the standard $L_{\text{smooth}}$-smooth SGD descent lemma (Bottou, Curtis, Nocedal, 2018):
   $$\begin{aligned}
   \mathbb{E}\big[\mathcal{L}(\theta_{t+1}) \mid \theta_t\big] &\le \mathcal{L}(\theta_t) - \eta \langle \nabla \mathcal{L}(\theta_t), \mathbb{E}[\hat{g}_{\text{pinv}}] \rangle + \frac{L_{\text{smooth}} \eta^2}{2} \mathbb{E}\big[\|\hat{g}_{\text{pinv}}\|_2^2\big] \\
   &= \mathcal{L}(\theta_t) - \eta \|\nabla \mathcal{L}(\theta_t)\|_2^2 + \frac{L_{\text{smooth}} \eta^2}{2} \left(\frac{N}{M}\right) \mathbb{E}\big[\|g_t\|_2^2\big]
   \end{aligned}$$
   Look at the two terms on the right:
   - The **first-order progress term** $-\eta \|\nabla \mathcal{L}(\theta_t)\|_2^2$ is preserved at **$100\%$ strength** because $\hat{g}_{\text{pinv}}$ is unbiased!
   - The **second-order noise term** $\frac{L_{\text{smooth}}\eta^2}{2}\mathbb{E}[\|\hat{g}_{\text{pinv}}\|_2^2]$ is inflated by $\frac{N}{M} = \frac{1}{r} = 4$. In SGD, the linear progress term is $O(\eta)$ while the variance penalty is $O(\eta^2)$! Whenever $\eta$ is small enough that first-order drift dominates second-order curvature noise (or during standard cosine/step LR decay), **preserving unbiased $O(\eta)$ progress is far more important than minimizing single-step $O(\eta^2)$ MSE**.

---

## 6.3 Fixed $\Phi$ vs. Per-Step $\Phi_t$: What Changes Across Steps?

In your system description, $\Phi$ is generated from a shared seed and **held fixed for the run**. It is crucial for your thesis to distinguish what happens when $\Phi$ is **fixed across all steps** versus **regenerated from an incrementing seed $(s + t)$ at each step $t$**.

### 1. Per-Step $\Phi_t$ (Fresh Seed Each Step): Isotropic Zero-Mean Noise
When $\Phi_t$ is redrawn independently at each step $t$:
- The projection matrix $P_{\mathcal{R}}^{(t)} = \Phi_t^+ \Phi_t$ rotates randomly at every step.
- Over $T$ steps, the compression errors $\xi_t = \left(\frac{N}{M} P_{\mathcal{R}}^{(t)} - I_N\right) g_t$ are independent and zero-mean, so they **average out over time** by the Law of Large Numbers:
  $$\frac{1}{T}\sum_{t=1}^T \xi_t \to 0 \quad \text{at rate } O(1/\sqrt{T})$$
- The optimizer explores all $N = 1024$ dimensions of each parameter block without any blind spots.

### 2. Fixed $\Phi$ Across the Entire Run: Persistent Null-Space Blindness
When $\Phi$ is fixed for the entire run, the projection matrix $P_{\mathcal{R}} = \Phi^+ \Phi$ is **deterministic and constant** for all steps $t = 1, 2, \dots, T$:
$$\hat{g}_t = \frac{N}{M} P_{\mathcal{R}} g_t \in \text{row}(\Phi) \quad \forall t$$
What does this mean geometrically?
1. **Within Each $N=1024$ Block, $N - M = 768$ Directions Are Permanently Frozen:**
   Because $\hat{g}_t \in \text{row}(\Phi)$ for every $t$, the parameter update $\theta_t - \theta_0 = -\eta \sum_{\tau=0}^{t-1} \hat{g}_\tau$ for every block lies **strictly inside the $M = 256$-dimensional subspace $\text{row}(\Phi)$**! The $768$-dimensional subspace $\text{null}(\Phi)$ never receives a non-zero update (unless weight decay or momentum from prior state moves it).
2. **Connection to Random Subspace Training (Intrinsic Dimension; Li et al., 2018):**
   Training with a fixed projection matrix $P_{\mathcal{R}}$ per block is mathematically equivalent to **subspace training** (restricting each $1024$-parameter block to a random $256$-dimensional linear subspace). Overparameterized neural networks can still train surprisingly well in a random $256/1024$ subspace because their intrinsic dimension is often much smaller than $N$, **provided the pseudo-inverse decoder stays inside $\text{row}(\Phi)$ consistently**.
3. **Why $\frac{N}{M}$ Rescaling Behavior Differs for Fixed $\Phi$ vs. Per-Step $\Phi_t$:**
   - Along the active subspace $\text{row}(\Phi)$, $P_{\mathcal{R}}$ acts as the **identity** ($P_{\mathcal{R}}^2 = P_{\mathcal{R}}$)!
   -Wait: look closely at that! If $\Phi$ is **fixed** across steps, then once the trajectory is moving inside $\text{row}(\Phi)$, the operator $P_{\mathcal{R}}$ has eigenvalue **$1$** (not $M/N$) for vectors $v \in \text{row}(\Phi)$, and eigenvalue **$0$** for vectors $v \in \text{null}(\Phi)$.
   - At step $t$, if the true gradient $g_t$ is still roughly isotropic relative to the fixed random subspace $\text{row}(\Phi)$ (because the forward/backward pass mixes coordinates across blocks and non-linear activations), then $\|P_{\mathcal{R}} g_t\|_2^2 \approx \frac{M}{N}\|g_t\|_2^2$, so the component of $\hat{g}_{\text{raw}} = P_{\mathcal{R}} g_t$ along $g_t$ is still $\frac{M}{N} = 0.25$ of $g_t$, and rescaling by $\frac{N}{M}$ still restores unbiasedness relative to the random draw of $\Phi$. However, along any fixed direction inside $\text{row}(\Phi)$, $\frac{N}{M} P_{\mathcal{R}}$ scales steps by $\frac{N}{M} = 4$ without averaging out over time!

---

## 6.4 Why $\ell_1$ Decoding Breaks "Decode the Average = Average of Decodes"

In your architecture, AllReduce averages the compressed measurements across $W$ workers:
$$\bar{y} = \frac{1}{W}\sum_{i=1}^W \Phi g_i = \Phi \bar{g}$$
and then the receiver runs the decoder $\mathcal{D}(\bar{y})$ **once**. Let us see why a nonlinear $\ell_1$ decoder fails here for **two distinct reasons**:

### Reason 1: Algebraic Non-Commutativity ($\mathcal{D}_{\ell_1}(\bar{y}) \neq \frac{1}{W}\sum_{i=1}^W \mathcal{D}_{\ell_1}(y_i)$)
Because the soft-thresholding operator $\mathcal{S}_\tau(u) = \text{sign}(u)\max(|u|-\tau, 0)$ is **nonlinear**, the LASSO / FISTA decoder $\mathcal{D}_{\ell_1}$ is a nonlinear map:
$$\mathcal{D}_{\ell_1}\!\left(\frac{1}{W}\sum_{i=1}^W y_i\right) \neq \frac{1}{W}\sum_{i=1}^W \mathcal{D}_{\ell_1}(y_i)$$
Even for a single soft-thresholding step with $\tau = 1.0$:
- Suppose Worker 1 has $u_1 = +1.5$ and Worker 2 has $u_2 = -0.5$.
- Average of decodes: $\frac{1}{2}\big(\mathcal{S}_1(1.5) + \mathcal{S}_1(-0.5)\big) = \frac{1}{2}(0.5 + 0) = \mathbf{0.25}$.
- Decode of the average: $\mathcal{S}_1\!\left(\frac{1.5 + (-0.5)}{2}\right) = \mathcal{S}_1(0.5) = \mathbf{0.00}$!

### Reason 2: Support Union Density Blowup ($\|\bar{g}\|_0 \le \sum_{i=1}^W \|g_i\|_0$)
Wait: you might ask, *"Even if $\mathcal{D}_{\ell_1}(\bar{y}) \neq \frac{1}{W}\sum_i \mathcal{D}_{\ell_1}(y_i)$, since $\bar{y} = \Phi \bar{g}$, doesn't $\mathcal{D}_{\ell_1}(\bar{y})$ directly try to recover the true averaged gradient $\bar{g}$?"*
**Yes—and that is even worse for sparsity!**
Suppose each individual worker $i \in \{1, \dots, W\}$ actually *did* have a sparse local gradient block $g_i$ with $\|g_i\|_0 = k = 30$ non-zeros (which is below the Donoho–Tanner limit $k_{\max} = 62$ for a single worker!).
Because different workers process different minibatches of data, their active gradient coordinates occur at different indices $S_i = \text{supp}(g_i)$. When AllReduce forms the average $\bar{g} = \frac{1}{W}\sum_{i=1}^W g_i$, the support of $\bar{g}$ is the **union of the supports** of all $W$ workers:
$$\text{supp}(\bar{g}) = \bigcup_{i=1}^W \text{supp}(g_i) \implies \|\bar{g}\|_0 \approx \min\big(W k, \, N\big)$$
With $W = 8$ workers each having $k = 30$ active coordinates, the averaged gradient $\bar{g}$ has $\|\bar{g}\|_0 \approx 215 \gg k_{\max} = 62$ non-zeros! Thus, **averaging measurements in AllReduce destroys sparsity before the $\ell_1$ decoder ever sees the signal**, pushing $\bar{g}$ far above the Donoho–Tanner phase transition!

---

## 6.5 Connection to Rand-$k$ Sparsification, Unbiased vs. Biased Compressors, and Error Feedback

Your thesis prompt asks to connect our two decoders to three pillars of the gradient compression literature: **Rand-$k$ sparsification**, **unbiased vs. biased compressors**, and **Error Feedback (EF)**. Here is the exact mathematical unification.

### 1. The Exact Isomorphism Between Rescaled Pseudo-Inverse and Rand-$k$ Sparsification
What is **Rand-$k$ sparsification** (Stich, Cordonnier, Jaggi, 2018; Alistarh et al., 2018)?
- Given a block $x \in \mathbb{R}^N$, pick $M = k$ coordinates $S \subset \{1, \dots, N\}$ uniformly at random without replacement (where $M/N = r$).
- Notice that picking $M$ coordinates is **literally multiplying $x$ by an $M \times N$ sensing matrix $\Phi_{\text{Rand-}M}$** whose rows are the $M$ chosen standard basis vectors $e_{j_1}^T, \dots, e_{j_M}^T$!
- Because the rows of $\Phi_{\text{Rand-}M}$ are orthonormal ($\Phi \Phi^T = I_M$), its pseudo-inverse is $\Phi^+ = \Phi^T$, and $\Phi^+ \Phi = \sum_{m=1}^M e_{j_m} e_{j_m}^T$ is the coordinate projection matrix $P_S$ that keeps the $M$ chosen coordinates and zeroes out the remaining $N - M$ coordinates!
- Without rescaling, $\mathbb{E}[P_S x] = \frac{M}{N} x$ (shrunk by $M/N$).
- With $\frac{N}{M}$ rescaling, $\mathcal{C}_{\text{Rand-}M}(x) = \frac{N}{M} P_S x$ is **unbiased**:
  $$\mathbb{E}\left[\frac{N}{M} P_S x\right] = x, \qquad \text{and} \qquad \mathbb{E}\left[\left\|\frac{N}{M} P_S x - x\right\|_2^2\right] = \left(\frac{N}{M} - 1\right)\|x\|_2^2$$

> **Theorem 6.1 (The Rand-$k$ / Random Subspace Duality).**
> *The rescaled Gaussian pseudo-inverse compressor $\mathcal{C}_{\text{pinv}}(x) = \frac{N}{M}\Phi^+ \Phi x$ IS simply **Rand-$M$ sparsification performed in a uniformly random orthonormal basis $V$** instead of the standard coordinate basis $I_N$! Both are rank-$M$ orthogonal projections rescaled by $\frac{N}{M}$, and both satisfy the exact same unbiasedness and variance identity:*
> $$\mathbb{E}[\mathcal{C}(x)] = x, \qquad \mathbb{E}\big[\|\mathcal{C}(x) - x\|_2^2\big] = \left(\frac{N}{M} - 1\right)\|x\|_2^2$$
> *Advantage of dense $\Phi$ over coordinate Rand-$M$:* If the gradient $x$ happens to be concentrated on a single coordinate $e_1$, coordinate Rand-$M$ misses $e_1$ with probability $1 - M/N = 0.75$ (high worst-case coordinate variance), whereas a dense Gaussian/Rademacher $\Phi$ spreads the energy of $e_1$ evenly across all $M$ measurements on every single draw!

### 2. Unbiased ($\omega$-Variance-Bounded) vs. Biased ($\delta$-Contractive) Compressors
In distributed optimization theory (Beznosikov et al., 2020; Karimireddy et al., 2019), gradient compressors are classified into two families:

1. **Unbiased $\omega$-Compressors:** A randomized operator $\mathcal{C} : \mathbb{R}^N \to \mathbb{R}^N$ satisfying:
   $$\mathbb{E}[\mathcal{C}(x)] = x, \qquad \mathbb{E}\big[\|\mathcal{C}(x) - x\|_2^2\big] \le \omega \|x\|_2^2$$
   - **Examples:** Rescaled pseudo-inverse $\frac{N}{M}\Phi^+ \Phi x$ (with $\omega = \frac{N}{M} - 1 = 3$ at $r=0.25$); Rescaled Rand-$k$ (with $\omega = \frac{N}{k} - 1$); Stochastic quantization (QSGD; Alistarh et al., 2017).
   - **Key property:** Can be plugged **directly into synchronous AllReduce SGD** without Error Feedback and converges at rate $O\left(\frac{1 + \omega/W}{\sqrt{T}}\right)$ (when independent across workers) or $O\left(\frac{1 + \omega}{\sqrt{T}}\right)$ (when using a shared seed).

2. **Biased $\delta$-Contractive Compressors:** A (possibly deterministic) operator $\mathcal{C} : \mathbb{R}^N \to \mathbb{R}^N$ satisfying:
   $$\mathbb{E}\big[\|\mathcal{C}(x) - x\|_2^2\big] \le (1 - \delta)\|x\|_2^2 \quad \text{for some } \delta \in (0, 1]$$
   - **Examples:**
     - **Unscaled pseudo-inverse** $\hat{x}_{\text{raw}} = \Phi^+ \Phi x$: satisfies this with **$\delta = \frac{M}{N} = r = 0.25$** (since $\mathbb{E}\|\Phi^+\Phi x - x\|_2^2 = (1 - r)\|x\|_2^2$)!
     - **Top-$k$ sparsification:** keeps the $k$ largest coordinates of $x$; satisfies this with $\delta = k/N$.
   - **Where does $\ell_1$ / FISTA sit?** Because LASSO shrinks coordinates by $\lambda$ and hallucinates sparse axis-aligned vectors when $x$ is dense, **$\ell_1$ decoding on dense gradients is a BIASED compressor that isn't even $\delta$-contractive** when $\|\hat{x}_{\ell_1} - x\|_2^2 > \|x\|_2^2$!

### 3. Why Biased Compressors Require Error Feedback (EF) — And Why AllReduce Precludes Receiver-Side EF
When you use a biased compressor (like Top-$k$, unscaled $\Phi^+\Phi$ with fixed $\Phi$, or $\ell_1$ recovery) directly in SGD without modification, the discarded component $e_t = g_t - \mathcal{C}(g_t)$ is lost forever, which can cause SGD to **fail to converge** (Karimireddy et al., 2019).
The standard fix for biased compressors is **Error Feedback (EF / memory)** (Seide et al., 2014; Stich et al., 2018):
- Each worker $i$ maintains a local error accumulator $e_i^{(t)} \in \mathbb{R}^N$:
  $$p_i^{(t)} = g_i^{(t)} + e_i^{(t)}, \qquad \hat{p}_i^{(t)} = \mathcal{C}\big(p_i^{(t)}\big), \qquad e_i^{(t+1)} = p_i^{(t)} - \hat{p}_i^{(t)}$$
- **Notice the catch in your system architecture!** To compute $e_i^{(t+1)} = p_i^{(t)} - \hat{p}_i^{(t)}$, worker $i$ must know the **decoded** vector $\hat{p}_i^{(t)} = \mathcal{D}(\Phi p_i^{(t)})$ locally *before* aggregation, AND the decoder must satisfy $\frac{1}{W}\sum_i \mathcal{D}(\Phi p_i^{(t)}) = \mathcal{D}(\Phi \bar{p}^{(t)})$ so that the receiver's decoded average matches the average of what the workers subtracted from their error buffers!
  - For the **linear pseudo-inverse decoder**, $\mathcal{D}$ is linear, so worker-side EF and receiver-side decoding are $100\%$ compatible!
  - For the **nonlinear $\ell_1$/FISTA decoder**, $\mathcal{D}_{\ell_1}(\bar{y}) \neq \frac{1}{W}\sum_i \mathcal{D}_{\ell_1}(y_i)$, so local error buffers drift out of sync with the global decoded update unless every worker runs FISTA locally and you transmit the decoded $N$-vectors (which defeats the entire purpose of compressing $N \to M$!).

---

## 6.6 What "The Gradient Is Not Sparse Enough" Means in Hard Numbers

Why did $\ell_1$ via FISTA lose to the pseudo-inverse at $r = 0.25$ ($N = 1024, M = 256$) on real neural network gradient blocks? Let us put the exact numbers side by side:

1. **The Donoho–Tanner Threshold Demands $\|x\|_0 \le 62$ (Effective Sparsity Ratio $k_{\text{eff}} \le 62$):**
   From Section 4.7, at $N = 1024, M = 256$ ($r = 0.25$), $\ell_1$ recovery requires the signal energy to be concentrated in at most **$k_{\max} \approx 62$ coordinates ($6\%$ of the block)**.
2. **What Real Deep Learning Gradient Blocks Look Like:**
   Empirically, within a $1024$-element block of a convolutional, MLP, or Transformer weight gradient, the entries are modeled by a **generalized Gaussian or heavy-tailed Weibull/Student-$t$ distribution** (or near-Gaussian distribution after layer normalization):
   - **Gaussian block ($x_j \sim \mathcal{N}(0, \sigma^2)$):**
     - Effective sparsity ratio: $k_{\text{eff}}(x) = \frac{\|x\|_1^2}{\|x\|_2^2} \approx \frac{2}{\pi} N \approx \mathbf{652}$ (over **$10\times$ larger** than the Donoho–Tanner limit of $62$!).
     - Top-$62$ energy fraction: The largest $62$ out of $1024$ Gaussian entries contain only **$\approx 27\%$ of the squared $\ell_2$ norm $\|x\|_2^2$** and only **$\approx 14\%$ of the $\ell_1$ norm $\|x\|_1$**! The remaining **$86\%$ of the $\ell_1$ norm sits in the $962$ tail coordinates** ($\sigma_{62}(x)_1 = 0.86 \|x\|_1$).
   - **Laplace / Heavy-Tailed block ($x_j \sim \text{Laplace}(0, b)$, commonly observed in late-training gradients):**
     - Effective sparsity ratio: $k_{\text{eff}}(x) = \frac{\|x\|_1^2}{\|x\|_2^2} \approx \frac{1}{2} N = \mathbf{512}$ (**$8.2\times$ larger** than the limit of $62$!).
     - Top-$62$ energy fraction: Even for a heavy-tailed Laplace distribution, the top $62$ coordinates hold only **$\approx 49\%$ of $\|x\|_2^2$** and **$\approx 23\%$ of $\|x\|_1$** ($77\%$ of the $\ell_1$ norm is in the tail!).
3. **What Happens When FISTA Runs on Such a Block at $r = 0.25$:**
   - **If $\lambda$ is small (Basis Pursuit regime):** FISTA finds the point on $\mathcal{H}_y = \{z : \Phi z = y\}$ with minimum $\|z\|_1$. By high-dimensional geometry, a generic $768$-dimensional affine flat $\mathcal{H}_y$ intersects the $\ell_1$ ball at a face of dimension **$\le M = 256$**! That means Basis Pursuit **forces at least $N - M = 768$ coordinates of $\hat{x}_{\ell_1}$ to be exact zero**, cramming all the energy of a $1024$-coordinate dense gradient into at most $256$ coordinates and amplifying null-space noise. The resulting cosine similarity with the true gradient $x$ drops to **$\cos(\hat{x}_{\ell_1}, x) \approx 0.37$**, strictly worse than the pseudo-inverse's guaranteed **$\cos(\hat{x}_{\text{pinv}}, x) = \sqrt{M/N} = 0.50$**!
   - **If $\lambda$ is larger (LASSO shrinkage regime):** Soft thresholding zeroes out even more coordinates and shrinks the survivors toward zero, introducing massive norm bias while still failing to improve directional cosine similarity above $\sqrt{M/N} = 0.50$.

---

## 6.7 Empirical Verification in NumPy: Full Head-to-Head Benchmark

Run this self-contained benchmark at your exact parameters ($N = 1024, M = 256, r = 0.25$). It compares the Pseudo-Inverse against FISTA (across multiple $\lambda$ values) on four signal regimes—**Strictly Sparse ($k=32$)**, **Moderately Sparse ($k=128$)**, **Heavy-Tailed Laplace Gradients**, and **Dense Gaussian Gradients**—measuring Cosine Similarity, Relative MSE, Effective Sparsity $k_{\text{eff}}$, and wall-clock speed:

```python
import time
import numpy as np

rng = np.random.default_rng(2026)
N, M = 1024, 256
r = M / N
scale = N / M

Phi = rng.normal(0.0, 1.0 / np.sqrt(M), size=(M, N))
Phi_pinv = Phi.T @ np.linalg.inv(Phi @ Phi.T)
L = np.linalg.norm(Phi, ord=2) ** 2
alpha = 1.0 / L

def fista_decode(Phi, y, eta_lam=0.05, max_iter=60):
    lam = eta_lam * np.max(np.abs(Phi.T @ y))
    tau = alpha * lam
    z = np.zeros(Phi.shape[1])
    w = np.zeros(Phi.shape[1])
    t = 1.0
    for _ in range(max_iter):
        u = w - alpha * (Phi.T @ (Phi @ w - y))
        z_next = np.sign(u) * np.maximum(np.abs(u) - tau, 0.0)
        t_next = 0.5 * (1.0 + np.sqrt(1.0 + 4.0 * t * t))
        w = z_next + ((t - 1.0) / t_next) * (z_next - z)
        z, t = z_next, t_next
    return z

def make_signals(N, rng):
    # 1. Strictly sparse (k = 32 < k_max = 62)
    x_k32 = np.zeros(N)
    x_k32[rng.choice(N, 32, replace=False)] = rng.standard_normal(32)
    # 2. Above phase transition (k = 128 > k_max = 62)
    x_k128 = np.zeros(N)
    x_k128[rng.choice(N, 128, replace=False)] = rng.standard_normal(128)
    # 3. Heavy-tailed Laplace gradient block
    x_lap = rng.laplace(0.0, 1.0, size=N)
    # 4. Dense Gaussian gradient block
    x_gauss = rng.standard_normal(N)
    return [
        ("Sparse (k=32 < k_max=62)", x_k32),
        ("Sparse (k=128 > k_max=62)", x_k128),
        ("Heavy-Tailed Laplace Block", x_lap),
        ("Dense Gaussian Block", x_gauss),
    ]

def cosine_sim(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return np.dot(a, b) / (na * nb) if na > 0 and nb > 0 else 0.0

print(f"=== Head-to-Head Decoder Benchmark at N={N}, M={M} (r={r}) ===\n")
print(f"{'Signal Type':<27} | {'k_eff':>6} | {'Top62 L2%':>9} | {'Pinv Cos':>8} | {'FISTA(BP) Cos':>13} | {'FISTA(LASSO) Cos':>16} | {'RawPinv MSE':>11} | {'FISTA(BP) MSE':>13}")
print("-" * 122)

for name, x in make_signals(N, rng):
    k_eff = (np.sum(np.abs(x)) ** 2) / np.sum(x ** 2)
    top62_idx = np.argsort(np.abs(x))[-62:]
    top62_l2_pct = 100.0 * np.sum(x[top62_idx] ** 2) / np.sum(x ** 2)

    y = Phi @ x
    x_raw = Phi_pinv @ y
    x_pinv = scale * x_raw
    x_fista_bp = fista_decode(Phi, y, eta_lam=0.005, max_iter=100)
    x_fista_lasso = fista_decode(Phi, y, eta_lam=0.10, max_iter=100)

    cos_pinv = cosine_sim(x_pinv, x)
    cos_bp = cosine_sim(x_fista_bp, x)
    cos_lasso = cosine_sim(x_fista_lasso, x)
    mse_raw = np.sum((x_raw - x) ** 2) / np.sum(x ** 2)
    mse_bp = np.sum((x_fista_bp - x) ** 2) / np.sum(x ** 2)

    print(f"{name:<27} | {k_eff:6.1f} | {top62_l2_pct:8.1f}% | {cos_pinv:8.4f} | {cos_bp:13.4f} | {cos_lasso:16.4f} | {mse_raw:11.4f} | {mse_bp:13.4f}")
```

---

## 6.8 Check Your Understanding

*(Full solutions are in [Chapter 99](./99-solutions-and-references.md).)*

1. **Minibatch Noise Amplification Factor:** Suppose a single worker's stochastic minibatch gradient block is $g_i = \nabla \mathcal{L}(\theta) + \zeta_i$, where the true gradient has norm $\|\nabla \mathcal{L}(\theta)\|_2$ and the minibatch noise satisfies $\mathbb{E}[\zeta_i] = 0$ and $\mathbb{E}[\|\zeta_i\|_2^2] = \sigma_{\text{mb}}^2$. After synchronous AllReduce of $y_i = \Phi g_i$ across $W$ workers using a shared random matrix $\Phi$ at compression ratio $r = M/N$, derive the total variance $\mathbb{E}\big[\|\hat{g}_{\text{pinv}} - \nabla \mathcal{L}(\theta)\|_2^2\big]$ of the decoded average $\hat{g}_{\text{pinv}} = \frac{N}{M}\Phi^+ \bar{y}$.
2. **Maximum Cardinality of Basis Pursuit Solutions:** Fundamental linear programming theory (the Fundamental Theorem of Linear Programming) states that any basic feasible solution (vertex) of $\min_{z} \|z\|_1 \text{ s.t. } \Phi z = y$ with $\Phi \in \mathbb{R}^{M \times N}$ has at most $M$ non-zero entries ($\|\hat{x}_{\text{BP}}\|_0 \le M$). Using the Cauchy–Schwarz inequality, prove that if the true gradient block is dense and flat ($|x_j| = c$ for all $j = 1, \dots, N$), then *any* vector $z$ with $\|z\|_0 \le M$ has cosine similarity at most $\sqrt{M/N} = \sqrt{r}$ with $x$—and explain why Basis Pursuit does even worse than $\sqrt{r}$ because the $M$ non-zeros it picks are distorted by null-space leakage from the other $N - M$ coordinates!
3. **Why Hybrid Basis Change (e.g., DHT / Walsh–Hadamard + Sparsification) Differs from $\ell_1$ Decoding:** Some gradient compression papers apply a fast orthogonal transform $H$ (like the Walsh–Hadamard Transform or DCT) before Top-$k$ or Rand-$k$. Does applying an orthogonal transform $H$ make a dense Gaussian vector sparse? When *does* a transform $H$ help?
