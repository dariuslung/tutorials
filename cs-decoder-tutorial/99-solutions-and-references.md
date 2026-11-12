# Chapter 99: Complete Solutions to Check-Your-Understanding Questions & Annotated References

---

## Part I: Solutions to Check-Your-Understanding Questions

### Chapter 1 Solutions

#### Question 1.1: Effective Sparsity Ratio $k_{\text{eff}}(x) = (\|x\|_1 / \|x\|_2)^2$
- **Bounds $1 \le k_{\text{eff}}(x) \le \|x\|_0 \le N$:**
  From Section 1.1, for any non-zero $x \in \mathbb{R}^N$ with $\|x\|_0 = k \ge 1$, we proved:
  $$\|x\|_2 \le \|x\|_1 \le \sqrt{\|x\|_0}\,\|x\|_2 \le \sqrt{N}\,\|x\|_2$$
  Dividing through by $\|x\|_2 > 0$ and squaring every term yields:
  $$1 \le \left(\frac{\|x\|_1}{\|x\|_2}\right)^2 = k_{\text{eff}}(x) \le \|x\|_0 \le N$$
- **Value for i.i.d. $\mathcal{N}(0, 1)$ vector ($N = 1024$):**
  For $X_j \sim \mathcal{N}(0, 1)$, $\mathbb{E}[|X_j|] = \sqrt{2/\pi}$ and $\mathbb{E}[X_j^2] = 1$. By the Law of Large Numbers, for large $N$:
  $$\frac{1}{N}\|x\|_1 \approx \sqrt{\frac{2}{\pi}}, \qquad \frac{1}{N}\|x\|_2^2 \approx 1 \implies k_{\text{eff}}(x) = \frac{\|x\|_1^2}{\|x\|_2^2} \approx \frac{(N\sqrt{2/\pi})^2}{N \cdot 1} = \frac{2}{\pi} N \approx 0.6366 \times 1024 \approx \mathbf{651.9}$$

#### Question 1.2: Projector Energy Bound $\|P_{\mathcal{R}} x\|_2 \le \|x\|_2$
- Write the unique orthogonal decomposition $x = x_{\mathcal{R}} + x_{\mathcal{N}}$ where $x_{\mathcal{R}} = P_{\mathcal{R}} x \in \text{row}(\Phi)$, $x_{\mathcal{N}} = P_{\mathcal{N}} x \in \text{null}(\Phi)$, and $x_{\mathcal{R}} \perp x_{\mathcal{N}}$.
- By Pythagoras:
  $$\|x\|_2^2 = \|P_{\mathcal{R}} x\|_2^2 + \|P_{\mathcal{N}} x\|_2^2 \ge \|P_{\mathcal{R}} x\|_2^2$$
- Taking square roots gives $\|P_{\mathcal{R}} x\|_2 \le \|x\|_2$. Equality holds if and only if $\|P_{\mathcal{N}} x\|_2^2 = 0 \iff P_{\mathcal{N}} x = 0 \iff x \in \text{row}(\Phi)$.

#### Question 1.3: Lipschitz Constant of Scaled Gaussian $\Phi$ ($\Phi_{ij} \sim \mathcal{N}(0, 1/M)$)
- Here $\sigma = 1/\sqrt{M}$, $N = 1024$, $M = 256$, and $r = M/N = 0.25$.
- By the Marchenko–Pastur bound (Section 1.7):
  $$\sigma_{\max}(\Phi) \approx \sigma\left(\sqrt{N} + \sqrt{M}\right) = \frac{\sqrt{N} + \sqrt{M}}{\sqrt{M}} = \frac{1}{\sqrt{r}} + 1 = \frac{1}{0.5} + 1 = 3.0$$
- Therefore, the Lipschitz constant of $\nabla f(z) = \Phi^T(\Phi z - y)$ is:
  $$L = \|\Phi\|_2^2 = \sigma_{\max}(\Phi)^2 \approx 3.0^2 = \mathbf{9.0}$$
  which gives a maximum safe step size of $\alpha = 1/L \approx \mathbf{0.111}$.

---

### Chapter 2 Solutions

#### Question 2.1: Failure of $\ell_1$ on $x = [6, 0]^T$ when $\Phi = [1, 2]$
- If $x = [6, 0]^T$, then $y = \Phi x = 1(6) + 2(0) = 6$, which is the **exact same scalar measurement $y = 6$** that $x' = [0, 3]^T$ produced!
- Therefore, the decoder receives $y = 6$ in both cases and cannot possibly tell whether the sender started with $[6, 0]^T$ or $[0, 3]^T$. Since $\|[0, 3]^T\|_1 = 3 < \|[6, 0]^T\|_1 = 6$, Basis Pursuit will output $\hat{x}_{\ell_1} = [0, 3]^T$, failing completely when the true vector is $[6, 0]^T$.
- **General principle:** When $M = 1$, every single column $c_j \in \mathbb{R}^1$ of $\Phi$ is just a scalar, so all columns are linearly dependent! For any two non-zero columns $j_1 \neq j_2$, we can find 1-sparse vectors supported on $j_1$ and $j_2$ that map to the exact same scalar $y$.

#### Question 2.2: Minimum Measurements $M \ge 2k$ for Unique $k$-Sparse Identification
- Suppose two distinct $k$-sparse vectors $x^{(1)} \neq x^{(2)}$ produce the same measurement $\Phi x^{(1)} = \Phi x^{(2)}$.
- Then their difference $h = x^{(1)} - x^{(2)} \neq 0$ lies in $\text{null}(\Phi)$ and has sparsity $\|h\|_0 \le \|x^{(1)}\|_0 + \|x^{(2)}\|_0 \le 2k$.
- To prevent *any* non-zero $2k$-sparse vector $h$ from lying in $\text{null}(\Phi)$, every subset of $2k$ columns of $\Phi \in \mathbb{R}^{M \times N}$ must be linearly independent. Since $2k$ vectors in $\mathbb{R}^M$ can be linearly independent only if the ambient dimension is at least $2k$, we must have **$M \ge 2k$**!

#### Question 2.3: Geometric Proof that $\|\hat{x}_{\text{raw}}\|_2^2 = \|x\|_2^2 - \|\hat{x}_{\text{raw}} - x\|_2^2$
- Since $\hat{x}_{\text{raw}} = P_{\mathcal{R}} x = x_{\mathcal{R}} \in \text{row}(\Phi)$, the error vector is $\hat{x}_{\text{raw}} - x = -x_{\mathcal{N}} \in \text{null}(\Phi)$.
- Because $\text{row}(\Phi) \perp \text{null}(\Phi)$, $\hat{x}_{\text{raw}} \perp (\hat{x}_{\text{raw}} - x)$.
- Applying the Pythagorean theorem to $x = \hat{x}_{\text{raw}} + (x - \hat{x}_{\text{raw}})$ gives $\|x\|_2^2 = \|\hat{x}_{\text{raw}}\|_2^2 + \|\hat{x}_{\text{raw}} - x\|_2^2$, or rearranging:
  $$\|\hat{x}_{\text{raw}}\|_2^2 = \|x\|_2^2 - \|\hat{x}_{\text{raw}} - x\|_2^2$$

---

### Chapter 3 Solutions

#### Question 3.1: Scaling Invariance of $\Phi^+ \Phi x$
- Suppose $\tilde{\Phi} = c \Phi$ for any non-zero scalar $c > 0$.
- Then $\tilde{\Phi}^+ = \tilde{\Phi}^T (\tilde{\Phi} \tilde{\Phi}^T)^{-1} = (c \Phi^T)(c^2 \Phi \Phi^T)^{-1} = c \cdot c^{-2} \Phi^T (\Phi \Phi^T)^{-1} = \frac{1}{c} \Phi^+$.
- Meanwhile, the measurement is $\tilde{y} = \tilde{\Phi} x = c \Phi x = c y$.
- When the receiver decodes $\tilde{y}$ using $\tilde{\Phi}^+$:
  $$\hat{x}_{\text{pinv}} = \frac{N}{M} \tilde{\Phi}^+ \tilde{y} = \frac{N}{M} \left(\frac{1}{c} \Phi^+\right) (c y) = \frac{N}{M} \Phi^+ y$$
  The constant $c$ cancels out identically! Geometrically, scaling $\Phi$ by $c$ does not change the subspace $\text{row}(\Phi)$ at all, so the orthogonal projection matrix $P_{\mathcal{R}} = \Phi^+ \Phi$ is completely invariant to how $\Phi$ is normalized.

#### Question 3.2: Cosine Similarity Between $\hat{x}_{\text{pinv}}$ and $x$
- Since $\hat{x}_{\text{pinv}} = \frac{N}{M} P_{\mathcal{R}} x$ with $\frac{N}{M} > 0$, the positive scalar $\frac{N}{M}$ cancels between numerator and denominator:
  $$\cos(\theta) = \frac{x^T \left(\frac{N}{M} P_{\mathcal{R}} x\right)}{\|x\|_2 \left\|\frac{N}{M} P_{\mathcal{R}} x\right\|_2} = \frac{x^T P_{\mathcal{R}} x}{\|x\|_2 \|P_{\mathcal{R}} x\|_2}$$
- Using $P_{\mathcal{R}} = P_{\mathcal{R}}^T P_{\mathcal{R}}$, the numerator is $x^T P_{\mathcal{R}}^T P_{\mathcal{R}} x = \|P_{\mathcal{R}} x\|_2^2$. Canceling one factor of $\|P_{\mathcal{R}} x\|_2$ gives:
  $$\cos(\theta) = \frac{\|P_{\mathcal{R}} x\|_2}{\|x\|_2} \approx \sqrt{\frac{\mathbb{E}[\|P_{\mathcal{R}} x\|_2^2]}{\|x\|_2^2}} = \sqrt{\frac{M}{N}} = \sqrt{r}$$
- At $r = 0.25$, $\cos(\theta) \approx \sqrt{0.25} = \mathbf{0.50}$, which corresponds to an angle of $\theta = \arccos(0.50) = \mathbf{60^\circ}$ in 1024-dimensional space!

#### Question 3.3: Transpose Decoder $\Phi^T$ vs. Pseudo-Inverse Decoder $\Phi^+$
- If $\Phi \in \mathbb{R}^{M \times N}$ has i.i.d. entries with mean $0$ and variance $1/M$, then $(\Phi^T \Phi)_{jk} = \sum_{i=1}^M \Phi_{ij} \Phi_{ik}$. Taking expectations gives $\mathbb{E}[\Phi^T \Phi] = M \cdot \frac{1}{M} I_N = I_N$, so $\hat{x}_{\text{trans}} = \Phi^T \Phi x$ is also unbiased ($\mathbb{E}[\hat{x}_{\text{trans}}] = x$).
- However, what is its variance $\mathbb{E}[\|\Phi^T \Phi x - x\|_2^2] = \mathbb{E}[\|\Phi^T \Phi x\|_2^2] - \|x\|_2^2$?
  For i.i.d. $\mathcal{N}(0, 1/M)$ entries, write $\Phi$ in SVD form $\Phi = U \Sigma V^T$. While $\frac{N}{M}\Phi^+ \Phi = \frac{N}{M} V \begin{bmatrix} I_M & 0 \\ 0 & 0 \end{bmatrix} V^T$ sets all $M$ active eigenvalues to **equal constant $N/M$**, the matrix $\Phi^T \Phi = V \Sigma^T \Sigma V^T$ has $M$ non-uniform eigenvalues $\sigma_1^2, \dots, \sigma_M^2$ whose mean is $N/M$ but whose variance around $N/M$ is positive!
- Specifically, a direct fourth-moment Gaussian calculation gives:
  $$\mathbb{E}\left[\|\Phi^T \Phi x\|_2^2\right] = \left(\frac{N + M + 1}{M}\right)\|x\|_2^2 \implies \mathbb{E}\left[\|\Phi^T \Phi x - x\|_2^2\right] = \left(\frac{N + 1}{M}\right)\|x\|_2^2 > \left(\frac{N}{M} - 1\right)\|x\|_2^2$$
  Thus, replacing $\frac{N}{M}\Phi^+$ with $\Phi^T$ increases the variance by $\|x\|_2^2 \left(1 + \frac{1}{M}\right)$ (for instance, at $r = 0.25$, the variance increases from $3\|x\|_2^2$ to $4.004\|x\|_2^2$, a $33\%$ increase in compression noise!).

---

### Chapter 4 Solutions

#### Question 4.1: Verifying the Null Space Property on $\Phi = \begin{bmatrix} 1 & 0 & 1 \\ 0 & 1 & 1 \end{bmatrix}$
- From Chapter 2, Example 2, $\text{null}(\Phi)$ is spanned by $v = [1, 1, -1]^T$, so every non-zero $h \in \text{null}(\Phi)$ has the form $h = c [1, 1, -1]^T$ for $c \neq 0$.
- For any subset $S \subset \{1, 2, 3\}$ of size $|S| = k = 1$, $S$ contains 1 index and $S^c$ contains 2 indices:
  $$\|h_S\|_1 = |c| \cdot 1 = |c|, \qquad \|h_{S^c}\|_1 = |c| \cdot (1 + 1) = 2|c|$$
- Since $|c| < 2|c|$ for all $c \neq 0$, $\|h_S\|_1 < \|h_{S^c}\|_1$ holds for every $|S| = 1$!
- By Theorem 4.2, Basis Pursuit is **guaranteed** to uniquely recover *every* 1-sparse vector $x \in \mathbb{R}^3$ (whether supported on coordinate 1, 2, or 3).

#### Question 4.2: Why $0 < p < 1$ Fails Convexity
- Let $u = [1, 0]^T$ and $v = [0, 1]^T$, and consider $h(z) = \|z\|_{1/2}^{1/2} = \sqrt{|z_1|} + \sqrt{|z_2|}$.
- At the endpoints: $h(u) = \sqrt{1} + 0 = 1$, and $h(v) = 0 + \sqrt{1} = 1$.
- At the midpoint $m = \frac{1}{2}u + \frac{1}{2}v = [0.5, 0.5]^T$:
  $$h(m) = \sqrt{0.5} + \sqrt{0.5} = \sqrt{2} \approx 1.414 > 1 = \frac{1}{2}h(u) + \frac{1}{2}h(v)$$
- Because the midpoint has a strictly *higher* value than the average of the endpoints, $h(z)$ is **concave** along the line segment connecting $u$ and $v$, creating a mountain peak in the middle and two separate local minima at the two axes!

#### Question 4.3: Power-Law Compressibility Calculation ($N = 1024, k = 62$)
- **(a) Fast decay $s = 2.0$ ($|x_{(i)}| = i^{-2}$):**
  - Top-62 $\ell_1$ norm: $\sum_{i=1}^{62} i^{-2} \approx 1.629$.
  - Tail $\ell_1$ norm: $\sigma_{62}(x)_1 = \sum_{i=63}^{1024} i^{-2} \approx \int_{62.5}^{1024.5} t^{-2}\,dt \approx 0.015$.
  - Ratio $\sigma_{62}(x)_1 / \|x_{\text{top-}62}\|_1 \approx 0.015 / 1.629 \approx \mathbf{0.0092}$ (**$< 1\%$ tail!**). Theorem 4.4 gives tiny error: $\frac{\sigma_{62}(x)_1}{\sqrt{62}} \approx 0.0019$.
- **(b) Slow decay $s = 0.5$ ($|x_{(i)}| = i^{-0.5}$):**
  - Top-62 $\ell_1$ norm: $\sum_{i=1}^{62} i^{-0.5} \approx 2\sqrt{62} - 1.46 \approx 14.29$.
  - Tail $\ell_1$ norm: $\sigma_{62}(x)_1 = \sum_{i=63}^{1024} i^{-0.5} \approx 2(\sqrt{1024} - \sqrt{62}) \approx 2(32 - 7.87) = 48.25$.
  - Ratio $\sigma_{62}(x)_1 / \|x_{\text{top-}62}\|_1 \approx 48.25 / 14.29 \approx \mathbf{3.38}$ (**the tail is $3.4\times$ larger than the head!**).

---

### Chapter 5 Solutions

#### Question 5.1: Proximal Operator of Ridge ($\ell_2^2$) Regularization
- We want to minimize $\frac{1}{2}\|z - u\|_2^2 + \frac{\alpha \lambda}{2}\|z\|_2^2$.
- Since both terms are smooth, take the gradient with respect to $z$ and set it to zero:
  $$(z - u) + \alpha \lambda z = 0 \implies (1 + \alpha \lambda) z = u \implies z^* = \frac{1}{1 + \alpha \lambda} u$$
- Unlike soft thresholding $\mathcal{S}_{\alpha\lambda}(u)$, which subtracts a constant threshold $\alpha\lambda$ and zeroes out $[- \alpha\lambda, \alpha\lambda]$, the $\ell_2^2$ proximal operator simply multiplies every coordinate by the uniform factor $\frac{1}{1 + \alpha\lambda} \in (0, 1)$, so no non-zero coordinate $u_j \neq 0$ ever becomes zero!

#### Question 5.2: Subdifferential Optimality Condition of LASSO from ISTA Fixed Point
- Suppose $z^* = \mathcal{S}_{\alpha\lambda}\big(z^* + \alpha r^*\big)$, where $r^* = \Phi^T(y - \Phi z^*)$ and $\tau = \alpha\lambda$.
- Coordinate-by-coordinate:
  - If $z_j^* > 0$: the active branch of $\mathcal{S}_\tau$ is $z_j^* = (z_j^* + \alpha r_j^*) - \alpha\lambda \implies \alpha r_j^* = \alpha\lambda \implies r_j^* = +\lambda = \lambda \,\text{sign}(z_j^*)$.
  - If $z_j^* < 0$: the active branch of $\mathcal{S}_\tau$ is $z_j^* = (z_j^* + \alpha r_j^*) + \alpha\lambda \implies \alpha r_j^* = -\alpha\lambda \implies r_j^* = -\lambda = \lambda \,\text{sign}(z_j^*)$.
  - If $z_j^* = 0$: the deadzone condition of $\mathcal{S}_\tau$ requires $|0 + \alpha r_j^*| \le \alpha\lambda \implies |r_j^*| \le \lambda$. $\blacksquare$

#### Question 5.3: Why FISTA Can Be Non-Monotone
- In ISTA, each step $z^{(k+1)}$ explicitly minimizes a global quadratic upper bound $Q_\alpha(z; z^{(k)}) + \lambda \|z\|_1$ evaluated at the current point $z^{(k)}$, which algebraically guarantees $F(z^{(k+1)}) \le F(z^{(k)})$.
- In FISTA, the step is taken from the **extrapolated momentum point** $w^{(k)} = z^{(k-1)} + \beta_k(z^{(k-1)} - z^{(k-2)})$. As $k$ grows and $\beta_k \to 1$, the momentum carries $w^{(k)}$ past the bottom of the valley along high-curvature directions, causing occasional small ripples in $F(z^{(k)})$ (just like a heavy ball rolling through the bottom of a bowl).

---

### Chapter 6 Solutions

#### Question 6.1: Minibatch Noise + Shared-Seed Pseudo-Inverse Variance Across $W$ Workers
- Let $\mu = \nabla \mathcal{L}(\theta)$. The true averaged minibatch gradient across $W$ workers with independent minibatch noise $\zeta_i$ is $\bar{g} = \mu + \bar{\zeta}$, where $\mathbb{E}[\bar{\zeta}] = 0$ and $\mathbb{E}[\|\bar{\zeta}\|_2^2] = \frac{\sigma_{\text{mb}}^2}{W}$.
- Because $\Phi$ is independent of the minibatch draw and $\hat{g}_{\text{pinv}} = \frac{N}{M}\Phi^+ \Phi \bar{g}$, we apply the Law of Total Expectation conditioning on $\bar{g}$:
  $$\mathbb{E}_{\bar{g}, \Phi}\left[\|\hat{g}_{\text{pinv}} - \mu\|_2^2\right] = \mathbb{E}_{\bar{g}}\Big[ \underbrace{\|\bar{g} - \mu\|_2^2}_{\text{minibatch error}} + \underbrace{\mathbb{E}_\Phi\left[\|\hat{g}_{\text{pinv}} - \bar{g}\|_2^2 \mid \bar{g}\right]}_{\left(\frac{N}{M} - 1\right)\|\bar{g}\|_2^2} \Big]$$
- Using $\mathbb{E}[\|\bar{g}\|_2^2] = \|\mu\|_2^2 + \frac{\sigma_{\text{mb}}^2}{W}$, we obtain:
  $$\mathbb{E}\left[\|\hat{g}_{\text{pinv}} - \mu\|_2^2\right] = \frac{\sigma_{\text{mb}}^2}{W} + \left(\frac{N}{M} - 1\right)\left(\|\mu\|_2^2 + \frac{\sigma_{\text{mb}}^2}{W}\right) = \left(\frac{N}{M} - 1\right)\|\mu\|_2^2 + \frac{N}{M}\frac{\sigma_{\text{mb}}^2}{W}$$
  Notice how cleanly both sources of variance appear: the minibatch noise variance $\frac{\sigma_{\text{mb}}^2}{W}$ is amplified by $\frac{N}{M} = \frac{1}{r} = 4$, and an extra variance term $\left(\frac{N}{M} - 1\right)\|\mu\|_2^2 = 3\|\mu\|_2^2$ proportional to the true gradient norm is added!

#### Question 6.2: Maximum Cosine Similarity of Any $M$-Sparse Vector with a Flat Dense Vector
- Suppose $x \in \mathbb{R}^N$ has $|x_j| = c > 0$ for all $j = 1, \dots, N$, so $\|x\|_2 = c\sqrt{N}$.
- Take *any* vector $z \in \mathbb{R}^N$ with support $S = \text{supp}(z)$ of size $|S| \le M$. By the Cauchy–Schwarz inequality on $S$:
  $$x^T z = \sum_{j \in S} x_j z_j \le \sqrt{\sum_{j \in S} x_j^2} \sqrt{\sum_{j \in S} z_j^2} = \big(c\sqrt{|S|}\big) \|z\|_2 \le c\sqrt{M} \|z\|_2$$
- Dividing by $\|x\|_2 \|z\|_2 = c\sqrt{N}\|z\|_2$ gives:
  $$\cos(z, x) = \frac{x^T z}{\|x\|_2 \|z\|_2} \le \frac{c\sqrt{M}\|z\|_2}{c\sqrt{N}\|z\|_2} = \sqrt{\frac{M}{N}} = \sqrt{r}$$
- Equality $\cos(z, x) = \sqrt{r}$ is achieved **only** if $z$ sets its $M$ non-zero entries equal to the exact values of $x_S$ without any distortion. In Basis Pursuit, however, $\Phi_S z_S = y = \Phi_S x_S + \Phi_{S^c} x_{S^c}$, so the $N - M$ discarded coordinates $x_{S^c}$ inject massive interference $\Phi_S^{-1} \Phi_{S^c} x_{S^c}$ into $z_S$, knocking the cosine similarity of $\hat{x}_{\text{BP}}$ down from $\sqrt{r} = 0.50$ to $\approx 0.37$!

#### Question 6.3: When Orthogonal Transforms (Hadamard / DCT) Help vs. Don't Help
- If $x \in \mathbb{R}^N$ is already an isotropic dense Gaussian vector ($x \sim \mathcal{N}(0, \sigma^2 I_N)$), then for *any* orthogonal matrix $H$ ($H^T H = I_N$), $H x \sim \mathcal{N}(0, \sigma^2 I_N)$ has the **exact same dense Gaussian distribution**—no orthogonal transform can make white Gaussian noise sparse!
- Wait—when *does* a Hadamard/DCT transform help in gradient compression?
  1. **When the signal is smooth/correlated across neighboring indices** (so energy concentrates in low frequencies of the DCT).
  2. **For quantization / Rand-$k$ outlier spreading (e.g., Suresh et al., 2017; Alistarh et al., 2017):** A random Hadamard rotation does the exact **opposite** of sparsification—it *flattens* spiky outlier coordinates across all $N$ coordinates so that uniform quantization or coordinate sampling has low worst-case variance, just like our dense random matrix $\Phi$ does naturally!

---

## Part II: Annotated Bibliography (Standard Theorems vs. Practical Heuristics)

### 1. Standard Compressive Sensing & $\ell_1$ Recovery Theorems
- **Candès, E. J., Romberg, J., & Tao, T. (2006a).** *Robust uncertainty principles: Exact signal reconstruction from highly incomplete frequency information.* IEEE Transactions on Information Theory, 52(2), 489–509.
  *(Foundational paper establishing exact recovery via convex $\ell_1$ minimization.)*
- **Candès, E. J., Romberg, J., & Tao, T. (2006b).** *Stable signal recovery from incomplete and inaccurate measurements.* Communications on Pure and Applied Mathematics, 59(8), 1207–1223.
  *(Source of Theorem 4.4: the noisy and compressible $\ell_2$-$\ell_1$ instance-optimality bound $\|\hat{x} - x\|_2 \le C_0 \sigma_k(x)_1 / \sqrt{k} + C_1 \varepsilon$.)*
- **Candès, E. J., & Tao, T. (2005).** *Decoding by linear programming.* IEEE Transactions on Information Theory, 51(12), 4203–4215.
  *(Introduces the Restricted Isometry Property (RIP) and $\delta_k$ constants, Definition 4.1.)*
- **Candès, E. J. (2008).** *The restricted isometry property and its implications for compressed sensing.* Comptes Rendus Mathematique, 346(9–10), 589–592.
  *(Source of Theorem 4.3: clean proof that $\delta_{2k} < \sqrt{2} - 1$ guarantees exact and stable $\ell_1$ recovery.)*
- **Donoho, D. L. (2006).** *Compressed sensing.* IEEE Transactions on Information Theory, 52(4), 1289–1306.
  *(Coins the term "compressed sensing" and establishes high-dimensional polytope recovery bounds.)*
- **Donoho, D. L., & Tanner, J. (2009).** *Observed universality of phase transitions in high-dimensional geometry, with implications for modern data analysis and signal processing.* Philosophical Transactions of the Royal Society A, 367(1906), 4273–4293.
  *(Source of the exact phase transition curve $\rho_W(\delta)$ in Section 4.7, including $\rho_W(0.25) \approx 0.241$.)*
- **Baraniuk, R., Davenport, M., DeVore, R., & Wakin, M. (2008).** *A simple proof of the restricted isometry property for random matrices.* Constructive Approximation, 28(3), 253–263.
  *(Source of the covering-number + sub-Gaussian concentration proof of $M \gtrsim C k \log(N/k)$ in Section 4.6.)*
- **Foucart, S., & Rauhut, H. (2013).** *A Mathematical Introduction to Compressive Sensing.* Birkhäuser.
  *(The definitive graduate textbook reference for Null Space Property (Chapter 4), RIP (Chapter 6), and random matrix concentration (Chapter 9).)*

### 2. Standard Proximal Optimization & Matrix Theory References
- **Beck, A., & Teboulle, M. (2009).** *A fast iterative shrinkage-thresholding algorithm for linear inverse problems.* SIAM Journal on Imaging Sciences, 2(1), 183–202.
  *(Source of the FISTA algorithm, step size $\alpha = 1/\|\Phi\|_2^2$, and the $O(1/k)$ vs. $O(1/k^2)$ convergence proofs in Theorem 5.1.)*
- **Daubechies, I., Defrise, M., & De Mol, C. (2004).** *An iterative thresholding algorithm for linear inverse problems with a sparsity constraint.* Communications on Pure and Applied Mathematics, 57(11), 1413–1457.
  *(Foundational analysis of ISTA.)*
- **Penrose, R. (1955).** *A generalized inverse for matrices.* Mathematical Proceedings of the Cambridge Philosophical Society, 51(3), 406–413.
  *(Defines the four Moore–Penrose conditions and minimum-norm least-squares properties of $\Phi^+$ in Chapter 3.)*
- **Vershynin, R. (2018).** *High-Dimensional Probability: An Introduction with Applications in Data Science.* Cambridge University Press.
  *(Standard reference for non-asymptotic singular value bounds of Gaussian and Rademacher matrices in Section 1.7.)*

### 3. Standard Distributed Gradient Compression References
- **Alistarh, D., Grubic, D., Li, J., Tomioka, R., & Vojnovic, M. (2017).** *QSGD: Communication-efficient SGD via gradient quantization and encoding.* NeurIPS 2017.
  *(Establishes the unbiased $\omega$-compressor convergence framework used in Section 6.2 and 6.5.)*
- **Stich, S. U., Cordonnier, J.-B., & Jaggi, M. (2018).** *Sparsified SGD with memory.* NeurIPS 2018.
- **Karimireddy, S. P., Rebjock, Q., Stich, S., & Jaggi, M. (2019).** *Error feedback fixes SignSGD and other gradient compression schemes.* ICML 2019.
  *(Proves why biased compressors can fail without Error Feedback and establishes convergence of $\delta$-contractive compressors with EF.)*

### 4. Summary of Standard Results vs. Practical Heuristics in This Tutorial
- **Standard Mathematical Results (Proven Theorems):**
  - Decomposition $\mathbb{R}^N = \text{row}(\Phi) \oplus \text{null}(\Phi)$, $\Phi^+ = \Phi^T(\Phi\Phi^T)^{-1}$, $\Phi\Phi^+ = I_M$, and $\Phi^+\Phi = P_{\mathcal{R}}$ (Chapters 1–3).
  - Exact expectation $\mathbb{E}[\Phi^+\Phi] = \frac{M}{N}I_N$ and variance $\mathbb{E}\|\frac{N}{M}\Phi^+\Phi x - x\|_2^2 = \left(\frac{N}{M}-1\right)\|x\|_2^2$ for both Gaussian and full-rank Rademacher matrices (Theorems 3.3, 3.4, and Section 3.7).
  - Null Space Property (Theorem 4.2), RIP bound $M \gtrsim C k \log(N/k)$ (Theorem 4.3), Donoho–Tanner phase transition $\rho_W(0.25) \approx 0.241$ (Section 4.7), and Candès–Romberg–Tao stability bound (Theorem 4.4).
  - Derivation of soft-thresholding $\mathcal{S}_{\alpha\lambda}$ as $\text{prox}_{\alpha\lambda\|\cdot\|_1}$, $\lambda_{\max} = \|\Phi^T y\|_\infty$, and $O(1/k)$ vs. $O(1/k^2)$ convergence of ISTA/FISTA (Chapter 5).
- **Practical Engineering Heuristics & Domain Modeling:**
  - Modeling neural network gradient blocks as dense Gaussian or heavy-tailed Laplace vectors to estimate $k_{\text{eff}} \in [512, 652]$ at $N = 1024$ (Section 6.6).
  - Setting $\lambda = \eta \|\Phi^T y\|_\infty$ with $\eta \in [0.01, 0.20]$ to handle cross-layer gradient scale variation without per-layer hyperparameter tuning (Section 5.5).
  - Using the asymptotic Marchenko–Pastur formula $L \approx \sigma^2(\sqrt{N} + \sqrt{M})^2$ with a small safety factor ($1.05\times$) to avoid per-block SVD or power iteration (Section 5.3).
