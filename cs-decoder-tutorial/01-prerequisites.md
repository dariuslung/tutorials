# Chapter 1: Prerequisites

Every tool in this chapter is introduced for one reason: a derivation, theorem, or algorithm in Chapters 2–6 relies on it directly. After each topic, we explicitly state **where it is used**.

---

## 1.1 Vectors, Inner Products, and Norms ($\ell_2$, $\ell_1$, $\ell_0$)

### Intuition
A gradient block $x \in \mathbb{R}^N$ is a point in $N$-dimensional space ($N = 1024$). When we compress $x$ into $y \in \mathbb{R}^M$ ($M = 256$) and try to reconstruct it, infinitely many candidate vectors $z \in \mathbb{R}^N$ satisfy $\Phi z = y$. To pick a *single* winner among those candidates, a decoder needs a rule for measuring which candidate is "smallest" or "simplest." Different ways of measuring vector size—different **norms**—produce completely different decoders.

### Statement & Definitions
For two vectors $u, v \in \mathbb{R}^N$, the **standard inner product** (dot product) is:
$$\langle u, v \rangle = u^T v = \sum_{j=1}^N u_j v_j$$
Two vectors are **orthogonal** ($u \perp v$) if $u^T v = 0$.

A **norm** on $\mathbb{R}^N$ is a function $\|\cdot\| : \mathbb{R}^N \to [0, \infty)$ satisfying three axioms for all $u, v \in \mathbb{R}^N$ and $c \in \mathbb{R}$:
1. **Positive definiteness:** $\|u\| \ge 0$, with $\|u\| = 0 \iff u = 0$.
2. **Absolute homogeneity:** $\|c u\| = |c| \, \|u\|$.
3. **Triangle inequality:** $\|u + v\| \le \|u\| + \|v\|$.

In compressive sensing, we focus on three measures of size:

1. **The $\ell_2$ (Euclidean) norm:**
   $$\|x\|_2 = \sqrt{x^T x} = \sqrt{\sum_{j=1}^N x_j^2}$$
   Its square, $\|x\|_2^2 = \sum_{j=1}^N x_j^2$, represents the **energy** of the vector and is smooth everywhere: its gradient with respect to $x$ is simply $\nabla_x \left(\frac{1}{2}\|x\|_2^2\right) = x$. Geometrically, the unit $\ell_2$ ball $B_2 = \{x \in \mathbb{R}^N : \|x\|_2 \le 1\}$ is a round, rotationally symmetric hypersphere.

2. **The $\ell_1$ (Manhattan / Taxicab) norm:**
   $$\|x\|_1 = \sum_{j=1}^N |x_j|$$
   Geometrically, the unit $\ell_1$ ball $B_1 = \{x \in \mathbb{R}^N : \|x\|_1 \le 1\}$ is a **cross-polytope** (a diamond in $\mathbb{R}^2$, an octahedron in $\mathbb{R}^3$). It has $2N$ sharp vertices located at the standard basis vectors $\pm e_1, \pm e_2, \dots, \pm e_N$, where $e_j$ has a $1$ in coordinate $j$ and $0$ everywhere else.

3. **The $\ell_\infty$ (Max) norm:**
   $$\|x\|_\infty = \max_{1 \le j \le N} |x_j|$$

4. **The "$\ell_0$ norm" (Sparsity count):**
   $$\|x\|_0 = \#\{j \in \{1, \dots, N\} : x_j \neq 0\}$$
   The set of non-zero indices is called the **support** of $x$: $\text{supp}(x) = \{j : x_j \neq 0\}$, so $\|x\|_0 = |\text{supp}(x)|$. A vector with $\|x\|_0 \le k$ is called **$k$-sparse**.
   *Note:* $\|x\|_0$ is **not** a true norm because it violates homogeneity: $\|2x\|_0 = \|x\|_0 \neq 2\|x\|_0$.

### Key Norm Inequalities (and Derivation)
For any vector $x \in \mathbb{R}^N$ with $\|x\|_0 = k \le N$:
$$\|x\|_2 \le \|x\|_1 \le \sqrt{k}\,\|x\|_2 \le \sqrt{N}\,\|x\|_2$$

**Derivation:**
* **Left inequality ($\|x\|_2 \le \|x\|_1$):** Square both sides:
  $$\|x\|_1^2 = \left(\sum_{j=1}^N |x_j|\right)^2 = \sum_{j=1}^N x_j^2 + \sum_{i \neq j} |x_i||x_j| \ge \sum_{j=1}^N x_j^2 = \|x\|_2^2$$
  Equality holds if and only if at most one entry of $x$ is non-zero ($\|x\|_0 \le 1$).
* **Right inequality ($\|x\|_1 \le \sqrt{k}\|x\|_2$):** Recall the **Cauchy–Schwarz inequality**, $|u^T v| \le \|u\|_2 \|v\|_2$. Let $S = \text{supp}(x)$ with $|S| = k$. Define $u \in \mathbb{R}^N$ by $u_j = |x_j|$ and $v \in \mathbb{R}^N$ by $v_j = 1$ if $j \in S$ and $0$ otherwise. Then:
  $$\|x\|_1 = \sum_{j \in S} |x_j| \cdot 1 = u^T v \le \|u\|_2 \|v\|_2 = \sqrt{\sum_{j=1}^N x_j^2} \cdot \sqrt{\sum_{j \in S} 1^2} = \sqrt{k}\,\|x\|_2$$
  Equality holds if and only if all $k$ non-zero entries of $x$ have the exact same magnitude $|x_j| = c$.

### Worked Numerical Example
Consider three vectors in $\mathbb{R}^4$:
- $x^{(1)} = [2, 0, 0, 0]^T$ (1-sparse): $\|x^{(1)}\|_0 = 1$, $\|x^{(1)}\|_2 = 2$, $\|x^{(1)}\|_1 = 2$. Here $\|x^{(1)}\|_1 / \|x^{(1)}\|_2 = 1$.
- $x^{(2)} = [1, 1, 1, 1]^T$ (dense flat): $\|x^{(2)}\|_0 = 4$, $\|x^{(2)}\|_2 = \sqrt{4} = 2$, $\|x^{(2)}\|_1 = 4$. Here $\|x^{(2)}\|_1 / \|x^{(2)}\|_2 = 2 = \sqrt{4}$.
- Notice that $x^{(1)}$ and $x^{(2)}$ have the **exact same $\ell_2$ norm** ($2$), so an $\ell_2$ decoder cannot tell them apart in size! However, the $\ell_1$ norm strongly prefers the sparse vector $x^{(1)}$ ($\|x^{(1)}\|_1 = 2$) over the dense vector $x^{(2)}$ ($\|x^{(2)}\|_1 = 4$).

*Where used:* Section 3.4 (minimum $\ell_2$-norm property of $\Phi^+$); Section 4.1 (effective sparsity ratio $(\|x\|_1/\|x\|_2)^2$); Section 4.3 ($\ell_1$ geometry); Section 4.5 (RIP and Null Space Property proofs).

---

## 1.2 Matrices as Linear Maps, Rank, Row Space, and Null Space

### Intuition
A matrix $\Phi \in \mathbb{R}^{M \times N}$ is a machine that takes an $N$-dimensional input $x \in \mathbb{R}^N$ and outputs an $M$-dimensional measurement $y = \Phi x \in \mathbb{R}^M$. When $M < N$ ($256 < 1024$), the matrix $\Phi$ squashes a 1024-dimensional space down into a 256-dimensional space. By conservation of dimension, $N - M = 768$ dimensions must be completely crushed to zero.

### Statement & Definitions
Let $\Phi \in \mathbb{R}^{M \times N}$ have rows $\phi_1^T, \dots, \phi_M^T \in \mathbb{R}^{1 \times N}$ and columns $c_1, \dots, c_N \in \mathbb{R}^M$:
$$\Phi x = \begin{bmatrix} \phi_1^T x \\ \vdots \\ \phi_M^T x \end{bmatrix} = \sum_{j=1}^N x_j c_j$$
Thus, $y_i = \phi_i^T x$ is the inner product of $x$ with the $i$-th row of $\Phi$.

Every matrix $\Phi \in \mathbb{R}^{M \times N}$ defines **Four Fundamental Subspaces** (Strang, 2016), two of which live in the input space $\mathbb{R}^N$ and two in the output space $\mathbb{R}^M$:

1. **Row Space of $\Phi$ (lives in $\mathbb{R}^N$):** The set of all linear combinations of the rows of $\Phi$ (equivalently, the column space of $\Phi^T$):
   $$\mathcal{R}(\Phi^T) = \text{row}(\Phi) = \{ \Phi^T w : w \in \mathbb{R}^M \} \subseteq \mathbb{R}^N$$
2. **Null Space (Kernel) of $\Phi$ (lives in $\mathbb{R}^N$):** The set of all inputs $z \in \mathbb{R}^N$ that $\Phi$ crushes to zero:
   $$\mathcal{N}(\Phi) = \text{null}(\Phi) = \{ z \in \mathbb{R}^N : \Phi z = 0 \} \subseteq \mathbb{R}^N$$
3. **Column Space (Range) of $\Phi$ (lives in $\mathbb{R}^M$):** The set of all reachable measurement vectors:
   $$\mathcal{R}(\Phi) = \text{col}(\Phi) = \{ \Phi x : x \in \mathbb{R}^N \} \subseteq \mathbb{R}^M$$
4. **Left Null Space of $\Phi$ (lives in $\mathbb{R}^M$):** $\mathcal{N}(\Phi^T) = \{ w \in \mathbb{R}^M : \Phi^T w = 0 \} \subseteq \mathbb{R}^M$.

The **rank** of $\Phi$, denoted $\text{rank}(\Phi)$, is the dimension of its column space, which always equals the dimension of its row space:
$$\text{rank}(\Phi) = \dim(\text{col}(\Phi)) = \dim(\text{row}(\Phi)) \le \min(M, N)$$
When $M \le N$ and $\text{rank}(\Phi) = M$, we say $\Phi$ has **full row rank**. For a continuous random matrix (like i.i.d. Gaussian), $\Phi$ has full row rank $M$ with probability $1$.

### Fundamental Theorem of Linear Algebra (Orthogonal Decomposition of $\mathbb{R}^N$)
1. **Rank-Nullity Theorem:**
   $$\dim(\text{row}(\Phi)) + \dim(\text{null}(\Phi)) = N$$
   When $\Phi$ has full row rank $M$, $\dim(\text{row}(\Phi)) = M$ and $\dim(\text{null}(\Phi)) = N - M$ ($256 + 768 = 1024$).
2. **Orthogonality of Row Space and Null Space:** Every vector in $\text{row}(\Phi)$ is orthogonal to every vector in $\text{null}(\Phi)$:
   $$\text{row}(\Phi) \perp \text{null}(\Phi)$$
   **Proof:** Take any $u \in \text{row}(\Phi)$ and any $z \in \text{null}(\Phi)$. By definition, $u = \Phi^T w$ for some $w \in \mathbb{R}^M$, and $\Phi z = 0$. Their inner product is:
   $$u^T z = (\Phi^T w)^T z = w^T \Phi z = w^T 0 = 0$$
3. **Unique Orthogonal Decomposition:** Because $\text{row}(\Phi)$ and $\text{null}(\Phi)$ are orthogonal and their dimensions sum to $N$, every gradient block $x \in \mathbb{R}^N$ splits **uniquely** into two orthogonal pieces:
   $$x = x_{\mathcal{R}} + x_{\mathcal{N}}, \quad \text{where } x_{\mathcal{R}} \in \text{row}(\Phi), \; x_{\mathcal{N}} \in \text{null}(\Phi), \; x_{\mathcal{R}} \perp x_{\mathcal{N}}$$
   By the Pythagorean theorem:
   $$\|x\|_2^2 = \|x_{\mathcal{R}}\|_2^2 + \|x_{\mathcal{N}}\|_2^2$$
   When the encoder computes $y = \Phi x$, notice what happens:
   $$y = \Phi(x_{\mathcal{R}} + x_{\mathcal{N}}) = \Phi x_{\mathcal{R}} + \underbrace{\Phi x_{\mathcal{N}}}_{=0} = \Phi x_{\mathcal{R}}$$
   **The measurement $y$ sees $x_{\mathcal{R}}$ completely and is $100\%$ blind to $x_{\mathcal{N}}$!**

*Where used:* Chapter 2 (geometry of underdetermined systems); Section 3.3 and 3.4 (why $\Phi^+ y = x_{\mathcal{R}}$ recovers the exact row-space component and sets the null-space component to zero).

---

## 1.3 Orthogonal Projections

### Intuition
Given the decomposition $x = x_{\mathcal{R}} + x_{\mathcal{N}}$, how do we compute the visible piece $x_{\mathcal{R}}$ and the invisible piece $x_{\mathcal{N}}$ using matrix multiplication? We use **orthogonal projection matrices**.

### Statement & Derivation
A matrix $P \in \mathbb{R}^{N \times N}$ is an **orthogonal projector** onto a subspace $\mathcal{S} \subseteq \mathbb{R}^N$ if and only if it satisfies two algebraic properties:
1. **Idempotence (projecting twice does nothing new):** $P^2 = P$.
2. **Symmetry (the projection direction is orthogonal to $\mathcal{S}$):** $P^T = P$.

**Derivation of the Projector $P_{\mathcal{R}}$ onto $\text{row}(\Phi)$:**
Assume $\Phi \in \mathbb{R}^{M \times N}$ has full row rank $M$. Then the $M \times M$ matrix $\Phi \Phi^T$ is symmetric and invertible (because $\Phi\Phi^T w = 0 \implies w^T\Phi\Phi^T w = \|\Phi^T w\|_2^2 = 0 \implies \Phi^T w = 0 \implies w = 0$ since the rows of $\Phi$ are linearly independent).
We want to decompose any $x \in \mathbb{R}^N$ into $x_{\mathcal{R}} + x_{\mathcal{N}}$ where:
- $x_{\mathcal{R}} \in \text{row}(\Phi)$, meaning $x_{\mathcal{R}} = \Phi^T w$ for some unknown coefficient vector $w \in \mathbb{R}^M$.
- $x_{\mathcal{N}} = x - x_{\mathcal{R}} \in \text{null}(\Phi)$, meaning $\Phi(x - \Phi^T w) = 0$.

Expand $\Phi(x - \Phi^T w) = 0$:
$$\Phi x - (\Phi \Phi^T) w = 0 \implies w = (\Phi \Phi^T)^{-1} \Phi x$$
Now substitute $w$ back into $x_{\mathcal{R}} = \Phi^T w$:
$$x_{\mathcal{R}} = \underbrace{\Phi^T (\Phi \Phi^T)^{-1} \Phi}_{P_{\mathcal{R}}} x$$
Let us check that $P_{\mathcal{R}} = \Phi^T (\Phi \Phi^T)^{-1} \Phi$ is an orthogonal projector:
- **Symmetric:** $P_{\mathcal{R}}^T = (\Phi^T (\Phi \Phi^T)^{-1} \Phi)^T = \Phi^T ((\Phi \Phi^T)^{-1})^T \Phi = P_{\mathcal{R}}$.
- **Idempotent:** $P_{\mathcal{R}}^2 = \Phi^T (\Phi \Phi^T)^{-1} \underbrace{\Phi \Phi^T (\Phi \Phi^T)^{-1}}_{I_M} \Phi = \Phi^T (\Phi \Phi^T)^{-1} \Phi = P_{\mathcal{R}}$.

Immediately, the orthogonal projector onto the **null space** $\text{null}(\Phi)$ is the complementary projector:
$$P_{\mathcal{N}} = I_N - P_{\mathcal{R}} = I_N - \Phi^T (\Phi \Phi^T)^{-1} \Phi$$
For any orthogonal projector $P$ onto an $M$-dimensional subspace, its eigenvalues are $\underbrace{1, 1, \dots, 1}_{M \text{ times}}$ and $\underbrace{0, 0, \dots, 0}_{N-M \text{ times}}$, so its **trace** (sum of diagonal entries = sum of eigenvalues) equals the dimension of the subspace:
$$\text{tr}(P_{\mathcal{R}}) = M, \qquad \text{tr}(P_{\mathcal{N}}) = N - M$$

*Where used:* Section 3.3 ($\Phi^+ \Phi = P_{\mathcal{R}}$); Section 3.5 (using $\text{tr}(P_{\mathcal{R}}) = M$ to prove $\mathbb{E}[\Phi^+\Phi] = \frac{M}{N}I_N$).

---

## 1.4 The Singular Value Decomposition (SVD) and Matrix Norms

### Intuition
Any matrix $\Phi \in \mathbb{R}^{M \times N}$, no matter how rectangular or complicated, is secretly just a diagonal scaling matrix when you rotate the input space $\mathbb{R}^N$ and output space $\mathbb{R}^M$ into the right orthonormal coordinate systems.

### Statement
Every matrix $\Phi \in \mathbb{R}^{M \times N}$ (with $M \le N$) admits a **Singular Value Decomposition (SVD)**:
$$\Phi = U \Sigma V^T = \sum_{i=1}^M \sigma_i u_i v_i^T$$
where:
- $U = [u_1, \dots, u_M] \in \mathbb{R}^{M \times M}$ is **orthogonal** ($U^T U = U U^T = I_M$); its columns $u_i$ are the **left singular vectors** (an orthonormal basis for $\mathbb{R}^M$).
- $V = [v_1, \dots, v_N] \in \mathbb{R}^{N \times N}$ is **orthogonal** ($V^T V = V V^T = I_N$); its columns $v_j$ are the **right singular vectors** (an orthonormal basis for $\mathbb{R}^N$).
- $\Sigma \in \mathbb{R}^{M \times N}$ has non-negative **singular values** $\sigma_1 \ge \sigma_2 \ge \dots \ge \sigma_M \ge 0$ on its main diagonal and zeros everywhere else:
  $$\Sigma = \begin{bmatrix} \text{diag}(\sigma_1, \dots, \sigma_M) & \mathbf{0}_{M \times (N-M)} \end{bmatrix}$$

If $\text{rank}(\Phi) = r_{\text{rk}} \le M$, then $\sigma_1 \ge \dots \ge \sigma_{r_{\text{rk}}} > 0$ and $\sigma_{r_{\text{rk}}+1} = \dots = \sigma_M = 0$. Furthermore, the SVD hands us orthonormal bases for the subspaces of Section 1.2:
- **First $r_{\text{rk}}$ right singular vectors $\{v_1, \dots, v_{r_{\text{rk}}}\}$:** Orthonormal basis for $\text{row}(\Phi)$.
- **Remaining $N - r_{\text{rk}}$ right singular vectors $\{v_{r_{\text{rk}}+1}, \dots, v_N\}$:** Orthonormal basis for $\text{null}(\Phi)$.

### Matrix Norms from the SVD
1. **Spectral (Operator) Norm $\|\Phi\|_2$:** The maximum stretching factor of $\Phi$ on any unit vector:
   $$\|\Phi\|_2 = \max_{\|x\|_2 = 1} \|\Phi x\|_2 = \sigma_1 = \sigma_{\max}(\Phi)$$
   Note also that $\|\Phi^T \Phi\|_2 = \|\Phi \Phi^T\|_2 = \sigma_1^2 = \|\Phi\|_2^2$.
2. **Frobenius Norm $\|\Phi\|_F$:** The Euclidean norm of all matrix entries treated as one long vector:
   $$\|\Phi\|_F = \sqrt{\sum_{i=1}^M \sum_{j=1}^N \Phi_{ij}^2} = \sqrt{\text{tr}(\Phi^T \Phi)} = \sqrt{\sum_{i=1}^M \sigma_i^2}$$

*Where used:* Section 3.1 (general definition of $\Phi^+$ via SVD); Section 5.3 (step size $\alpha = 1/\|\Phi\|_2^2 = 1/\sigma_1^2$ in ISTA/FISTA).

---

## 1.5 Overdetermined vs. Underdetermined Least Squares

When solving $\Phi z \approx y$ for an $M \times N$ matrix $\Phi$:
- **Overdetermined ($M > N$, tall matrix):** More equations than unknowns. Usually no exact solution exists, so we minimize the residual $\min_z \|\Phi z - y\|_2^2$. Setting the gradient $\nabla_z \left(\frac{1}{2}\|\Phi z - y\|_2^2\right) = \Phi^T(\Phi z - y) = 0$ yields the **normal equations** $\Phi^T \Phi z = \Phi^T y$, or $z = (\Phi^T \Phi)^{-1} \Phi^T y$ when $\Phi$ has full column rank $N$.
- **Underdetermined ($M < N$, fat matrix — our compressive sensing setting):** Fewer equations than unknowns. Here $\Phi^T \Phi \in \mathbb{R}^{N \times N}$ has rank at most $M < N$, so **$\Phi^T \Phi$ is NEVER invertible!** Instead, infinitely many $z$ achieve zero residual $\|\Phi z - y\|_2^2 = 0$, and we must use either the pseudo-inverse $\Phi^+ = \Phi^T(\Phi\Phi^T)^{-1}$ (Chapter 3) or regularization like $\ell_1$ (Chapter 4).

*Where used:* Chapters 2, 3, and 4.

---

## 1.6 Random Vectors, Expectation, Covariance, and the Trace Trick

### Intuition
Because $\Phi$ is drawn randomly, the decoded gradient $\hat{x}$ is a random vector. To understand how $\hat{x}$ affects SGD, we need to compute its expected value $\mathbb{E}[\hat{x}]$ (to check if it points in the true gradient direction $x$) and its expected squared error $\mathbb{E}[\|\hat{x} - x\|_2^2]$ (to measure the compression noise).

### Statement & Identities
Let $Z \in \mathbb{R}^N$ be a random vector and $A \in \mathbb{R}^{M \times N}$ be a deterministic matrix.
1. **Linearity of Expectation:** Expectation acts entry-by-entry and commutes with deterministic matrices:
   $$\mathbb{E}[A Z + b] = A \,\mathbb{E}[Z] + b$$
   Similarly, if $R \in \mathbb{R}^{N \times N}$ is a random matrix and $x \in \mathbb{R}^N$ is deterministic, $\mathbb{E}[R x] = \mathbb{E}[R] x$.
2. **Bias-Variance Decomposition for Vector Estimators:** For an estimator $\hat{x}$ of a deterministic vector $x \in \mathbb{R}^N$ with mean $\mu = \mathbb{E}[\hat{x}]$:
   $$\mathbb{E}\left[\|\hat{x} - x\|_2^2\right] = \underbrace{\|\mathbb{E}[\hat{x}] - x\|_2^2}_{\text{Squared Bias}} + \underbrace{\mathbb{E}\left[\|\hat{x} - \mathbb{E}[\hat{x}]\|_2^2\right]}_{\text{Total Variance}}$$
   **Proof:** Write $\hat{x} - x = (\hat{x} - \mu) + (\mu - x)$. Expanding the squared norm gives $\|\hat{x} - \mu\|_2^2 + \|\mu - x\|_2^2 + 2(\hat{x} - \mu)^T(\mu - x)$. Taking $\mathbb{E}[\cdot]$, the cross term vanishes because $\mathbb{E}[\hat{x} - \mu] = 0$.
3. **The Cyclic Trace Trick:** For any matrices $A \in \mathbb{R}^{m \times n}$ and $B \in \mathbb{R}^{n \times m}$, $\text{tr}(AB) = \text{tr}(BA)$. Because a scalar $s \in \mathbb{R}$ is a $1 \times 1$ matrix, $s = \text{tr}(s)$. Thus, for any vector $v \in \mathbb{R}^N$ and matrix $Q \in \mathbb{R}^{N \times N}$:
   $$v^T Q v = \text{tr}(v^T Q v) = \text{tr}(Q v v^T)$$
   Taking expectations (since $\text{tr}$ is just a linear sum of diagonal entries):
   $$\mathbb{E}[v^T Q v] = \text{tr}\left(\mathbb{E}[Q] v v^T\right) = v^T \mathbb{E}[Q] v$$

*Where used:* Section 3.5 and 3.6 (deriving the exact bias and variance of the pseudo-inverse decoder); Section 6.2 (SGD convergence with unbiased vs. biased compressed gradients).

---

## 1.7 Gaussian and Rademacher Random Matrices & Spectral Concentration

### Statement
In our system model, $\Phi \in \mathbb{R}^{M \times N}$ has i.i.d. zero-mean entries $\Phi_{ij}$ with variance $\sigma^2$:
- **Gaussian:** $\Phi_{ij} \sim \mathcal{N}(0, \sigma^2)$. Common scaling choices are $\sigma^2 = 1/M$ (so $\mathbb{E}[\|\Phi x\|_2^2] = \|x\|_2^2$), $\sigma^2 = 1/N$ (so rows have unit expected norm), or $\sigma^2 = 1$.
  Crucial property: **Orthogonal (Rotational) Invariance.** If $\Phi$ has i.i.d. $\mathcal{N}(0, \sigma^2)$ entries and $Q \in \mathbb{R}^{N \times N}$ is any fixed orthogonal matrix ($Q^T Q = I_N$), then $\Phi Q$ has the **exact same probability distribution** as $\Phi$. (Proof: $(\Phi Q)_{ij}$ are jointly Gaussian, zero mean, and $\mathbb{E}[(\Phi Q)_{ij}(\Phi Q)_{kl}] = \sigma^2 \delta_{ik} (Q^T Q)_{jl} = \sigma^2 \delta_{ik} \delta_{jl}$.)
- **Rademacher (Bernoulli $\pm \sigma$):** $\Phi_{ij} = +\sigma$ with probability $1/2$ and $-\sigma$ with probability $1/2$. Rademacher matrices require only 1 bit per entry to represent in hardware and turn matrix multiplication $\Phi x$ into pure additions/subtractions without floating-point multiplies!

### Singular Value Bounds (Marchenko–Pastur Law)
When $\Phi \in \mathbb{R}^{M \times N}$ has i.i.d. entries with mean $0$ and variance $\sigma^2 = 1/N$, as $M, N \to \infty$ with ratio $M/N = r \in (0, 1]$, the Marchenko–Pastur theorem (and non-asymptotic sub-Gaussian concentration; Vershynin, 2018) guarantees that all $M$ singular values of $\Phi$ cluster tightly in the interval:
$$\sigma_{\min}(\Phi) \approx 1 - \sqrt{r}, \qquad \sigma_{\max}(\Phi) = \|\Phi\|_2 \approx 1 + \sqrt{r}$$
More generally, for entry variance $\sigma^2$:
$$\sigma_{\min}(\Phi) \approx \sigma\left(\sqrt{N} - \sqrt{M}\right), \qquad \|\Phi\|_2 = \sigma_{\max}(\Phi) \approx \sigma\left(\sqrt{N} + \sqrt{M}\right)$$
For our setting ($N = 1024, M = 256, r = 0.25$):
- $\sqrt{N} = 32$, $\sqrt{M} = 16$.
- The condition number of $\Phi$ is $\frac{\sigma_{\max}(\Phi)}{\sigma_{\min}(\Phi)} \approx \frac{1 + \sqrt{0.25}}{1 - \sqrt{0.25}} = \frac{1.5}{0.5} = 3.0$! That means $\Phi\Phi^T$ has condition number $\approx 3^2 = 9$, making $(\Phi\Phi^T)^{-1}$ remarkably well-conditioned and numerically stable.

*Where used:* Section 3.2 (well-conditioning of $\Phi\Phi^T$); Section 3.5 & 3.7 (Gaussian rotational invariance vs. Rademacher); Section 5.3 (analytical estimate of Lipschitz constant $L = \|\Phi\|_2^2$).

---

## 1.8 Convex Functions, Lipschitz Gradients, and Proximal Operators

### Intuition
When we decode via $\ell_1$ minimization (LASSO), we want to minimize:
$$F(z) = \underbrace{\frac{1}{2}\|\Phi z - y\|_2^2}_{f(z) \text{ (smooth, convex)}} + \underbrace{\lambda \|z\|_1}_{g(z) \text{ (non-smooth, convex)}}$$
Because $\|z\|_1$ has sharp corners whenever any coordinate $z_j = 0$, standard gradient descent fails. **Proximal gradient descent** solves this by taking a standard gradient step on the smooth part $f(z)$, followed by a **proximal operator** step on the sharp part $g(z)$.

### Definitions & Key Properties
1. **Convex Function:** A function $h : \mathbb{R}^N \to \mathbb{R}$ is **convex** if for all $u, v \in \mathbb{R}^N$ and $\theta \in [0, 1]$:
   $$h(\theta u + (1 - \theta)v) \le \theta h(u) + (1 - \theta)h(v)$$
   Geometrically, the line segment connecting any two points on the graph of $h$ lies on or above the graph.
   - **Fundamental property:** Every local minimum of a convex function is a **global minimum**.
   - All norms ($\|z\|_2, \|z\|_1, \|z\|_\infty$) are convex by the triangle inequality and homogeneity! By contrast, $\|z\|_0$ is wildly non-convex.

2. **$L$-Smoothness (Lipschitz Continuous Gradient):** A differentiable function $f : \mathbb{R}^N \to \mathbb{R}$ has an **$L$-Lipschitz continuous gradient** if there is a constant $L > 0$ such that for all $u, v \in \mathbb{R}^N$:
   $$\|\nabla f(u) - \nabla f(v)\|_2 \le L \|u - v\|_2$$
   For our data-fidelity term $f(z) = \frac{1}{2}\|\Phi z - y\|_2^2$, the gradient is $\nabla f(z) = \Phi^T(\Phi z - y)$. Therefore:
   $$\|\nabla f(u) - \nabla f(v)\|_2 = \|\Phi^T \Phi (u - v)\|_2 \le \|\Phi^T \Phi\|_2 \|u - v\|_2 = \|\Phi\|_2^2 \|u - v\|_2$$
   Thus, the exact smallest Lipschitz constant is **$L = \|\Phi\|_2^2 = \sigma_{\max}(\Phi)^2$**.
   - **The Descent Lemma (Quadratic Upper Bound):** Any $L$-smooth function $f$ lies everywhere below a tangent paraboloid of curvature $L$ around any point $z^{(t)}$:
     $$f(z) \le f(z^{(t)}) + \langle \nabla f(z^{(t)}), z - z^{(t)} \rangle + \frac{L}{2}\|z - z^{(t)}\|_2^2$$
     Minimizing this right-hand quadratic upper bound over $z$ yields standard gradient descent: $z^{(t+1)} = z^{(t)} - \frac{1}{L}\nabla f(z^{(t)})$.

3. **The Proximal Operator:** For a convex (possibly non-differentiable) function $h : \mathbb{R}^N \to \mathbb{R}$ and step size $\alpha > 0$, the **proximal operator** $\text{prox}_{\alpha h} : \mathbb{R}^N \to \mathbb{R}^N$ is defined as:
   $$\text{prox}_{\alpha h}(v) = \arg\min_{z \in \mathbb{R}^N} \left( \frac{1}{2}\|z - v\|_2^2 + \alpha h(z) \right)$$
   **Intuition:** $\text{prox}_{\alpha h}(v)$ asks: *"Find a point $z$ that makes the penalty $h(z)$ small, without straying too far in Euclidean distance from the input point $v$."* Because $\frac{1}{2}\|z - v\|_2^2$ is strictly convex, the minimizer $z$ is always unique!

*Where used:* Section 5.1 & 5.2 (deriving ISTA and soft-thresholding directly from the Descent Lemma + proximal operator).

---

## 1.9 Empirical Verification in NumPy

Run this self-contained snippet to verify the Four Fundamental Subspaces, projector properties, norm inequalities, and the Marchenko–Pastur singular value bounds at $(N=1024, M=256)$:

```python
import numpy as np

rng = np.random.default_rng(42)
N, M = 1024, 256
r = M / N

# 1. Generate a Gaussian sensing matrix with variance 1/N
Phi = rng.normal(0.0, 1.0 / np.sqrt(N), size=(M, N))

# 2. Orthogonal projector onto row(Phi) and null(Phi)
P_R = Phi.T @ np.linalg.inv(Phi @ Phi.T) @ Phi
P_N = np.eye(N) - P_R

# Verify symmetry, idempotence, and trace
print(f"||P_R - P_R.T||_F = {np.linalg.norm(P_R - P_R.T):.2e}")
print(f"||P_R^2 - P_R||_F = {np.linalg.norm(P_R @ P_R - P_R):.2e}")
print(f"trace(P_R) = {np.trace(P_R):.2f} (expected M = {M})")
print(f"trace(P_N) = {np.trace(P_N):.2f} (expected N - M = {N - M})")

# 3. Verify unique orthogonal decomposition x = x_R + x_N
x = rng.normal(size=N)
x_R = P_R @ x
x_N = P_N @ x
print(f"Orthogonality x_R^T x_N = {np.dot(x_R, x_N):.2e}")
print(f"Pythagoras: ||x||^2 = {np.sum(x**2):.4f}, ||x_R||^2 + ||x_N||^2 = {np.sum(x_R**2) + np.sum(x_N**2):.4f}")
print(f"Measurement blindness ||Phi @ x_N||_2 = {np.linalg.norm(Phi @ x_N):.2e}")

# 4. Verify Marchenko-Pastur singular value bounds (1 - sqrt(r) to 1 + sqrt(r))
svals = np.linalg.svd(Phi, compute_uv=False)
print(f"sigma_min = {svals[-1]:.4f} (MP theory: {1 - np.sqrt(r):.4f})")
print(f"sigma_max = {svals[0]:.4f} (MP theory: {1 + np.sqrt(r):.4f})")
```

---

## 1.10 Check Your Understanding

*(Full solutions are in [Chapter 99](./99-solutions-and-references.md).)*

1. **Effective Sparsity Ratio:** For any non-zero vector $x \in \mathbb{R}^N$, define $k_{\text{eff}}(x) = \left(\frac{\|x\|_1}{\|x\|_2}\right)^2$. Using Section 1.1, prove that $1 \le k_{\text{eff}}(x) \le \|x\|_0 \le N$. What is $k_{\text{eff}}(x)$ if $x \in \mathbb{R}^{1024}$ has i.i.d. $\mathcal{N}(0, 1)$ entries (in expectation for large $N$)?
2. **Projector Energy Bound:** Using $x = x_{\mathcal{R}} + x_{\mathcal{N}}$ and $P_{\mathcal{R}} x = x_{\mathcal{R}}$, prove that for *every* vector $x \in \mathbb{R}^N$, $\|P_{\mathcal{R}} x\|_2 \le \|x\|_2$, with equality if and only if $x \in \text{row}(\Phi)$.
3. **Lipschitz Constant of Scaled Gaussian $\Phi$:** If $\Phi \in \mathbb{R}^{256 \times 1024}$ has i.i.d. $\mathcal{N}(0, 1/M)$ entries (with $M=256$), what is the approximate numerical value of the Lipschitz constant $L = \|\Phi\|_2^2$ of $f(z) = \frac{1}{2}\|\Phi z - y\|_2^2$, and what step size $\alpha = 1/L$ does that imply?
