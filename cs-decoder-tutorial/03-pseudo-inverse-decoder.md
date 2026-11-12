# Chapter 3: The Pseudo-Inverse Decoder, Completely

In your distributed gradient compression system, the decoder of record is the rescaled Moore–Penrose pseudo-inverse:
$$\hat{x}_{\text{pinv}} = \frac{N}{M} \Phi^+ y = \frac{N}{M} \Phi^+ \Phi x$$
In this chapter, we derive every algebraic, geometric, statistical, and computational property of $\Phi^+$ from first principles.

---

## 3.1 Definition via the Singular Value Decomposition (SVD)

### Intuition
As we saw in Section 1.4, the SVD $\Phi = U \Sigma V^T$ diagonalizes $\Phi$: it rotates the input $x$ by $V^T$, scales the first $M$ rotated coordinates by the singular values $\sigma_1, \dots, \sigma_M$ while dropping the remaining $N - M$ coordinates, and rotates the $M$-dimensional result by $U$.
How do you "invert" a map like that? You undo the output rotation with $U^T$, divide each active coordinate by $\sigma_i$ (as long as $\sigma_i > 0$), pad the $N - M$ lost coordinates with zeros, and rotate back into $\mathbb{R}^N$ with $V$!

### Statement & Definition
Let $\Phi \in \mathbb{R}^{M \times N}$ ($M \le N$) have SVD:
$$\Phi = U \Sigma V^T = \sum_{i=1}^{r_{\text{rk}}} \sigma_i u_i v_i^T$$
where $r_{\text{rk}} = \text{rank}(\Phi) \le M$ and $\sigma_1 \ge \dots \ge \sigma_{r_{\text{rk}}} > 0$. The **Moore–Penrose pseudo-inverse** $\Phi^+ \in \mathbb{R}^{N \times M}$ (Penrose, 1955) is defined as:
$$\Phi^+ = V \Sigma^+ U^T = \sum_{i=1}^{r_{\text{rk}}} \frac{1}{\sigma_i} v_i u_i^T$$
where $\Sigma^+ \in \mathbb{R}^{N \times M}$ is formed by transposing $\Sigma \in \mathbb{R}^{M \times N}$ and replacing every non-zero singular value $\sigma_i$ with its reciprocal $1/\sigma_i$ (while leaving all zeros as zero):
$$\Sigma^+ = \begin{bmatrix} \text{diag}\left(\sigma_1^{-1}, \dots, \sigma_{r_{\text{rk}}}^{-1}, 0, \dots, 0\right) \\ \mathbf{0}_{(N-M) \times M} \end{bmatrix} \in \mathbb{R}^{N \times M}$$

The matrix $\Phi^+$ is the **unique** matrix in $\mathbb{R}^{N \times M}$ satisfying the four **Moore–Penrose conditions**:
1. $\Phi \Phi^+ \Phi = \Phi$
2. $\Phi^+ \Phi \Phi^+ = \Phi^+$
3. $(\Phi \Phi^+)^T = \Phi \Phi^+$
4. $(\Phi^+ \Phi)^T = \Phi^+ \Phi$

---

## 3.2 Explicit Formula $\Phi^+ = \Phi^T (\Phi \Phi^T)^{-1}$ for Full Row Rank

### Intuition
When $M \le N$ and $\Phi$ has full row rank $M$ (so all $M$ singular values $\sigma_1 \ge \dots \ge \sigma_M > 0$ are strictly positive), we do not need an SVD to write down $\Phi^+$: there is a direct closed-form matrix expression.

### Statement & Derivation
**Proposition 3.1.** *If $\Phi \in \mathbb{R}^{M \times N}$ has full row rank $M$, then $\Phi \Phi^T \in \mathbb{R}^{M \times M}$ is symmetric positive definite (hence invertible), and:*
$$\Phi^+ = \Phi^T (\Phi \Phi^T)^{-1}$$

**Derivation from the SVD:**
When $\text{rank}(\Phi) = M$, the matrix $\Sigma \in \mathbb{R}^{M \times N}$ has the block form $\Sigma = \begin{bmatrix} S & \mathbf{0}_{M \times (N-M)} \end{bmatrix}$, where $S = \text{diag}(\sigma_1, \dots, \sigma_M) \in \mathbb{R}^{M \times M}$ is invertible.
First, compute $\Phi \Phi^T$:
$$\Phi \Phi^T = (U \Sigma V^T)(V \Sigma^T U^T) = U (\Sigma \Sigma^T) U^T = U S^2 U^T$$
Since $U$ and $S$ are invertible, $(\Phi \Phi^T)^{-1} = (U S^2 U^T)^{-1} = U S^{-2} U^T$.
Now multiply on the left by $\Phi^T = V \Sigma^T U^T$:
$$\Phi^T (\Phi \Phi^T)^{-1} = V \begin{bmatrix} S \\ \mathbf{0}_{(N-M) \times M} \end{bmatrix} \underbrace{U^T U}_{I_M} S^{-2} U^T = V \begin{bmatrix} S^{-1} \\ \mathbf{0}_{(N-M) \times M} \end{bmatrix} U^T = V \Sigma^+ U^T = \Phi^+ \quad \blacksquare$$

> **Special Case — Semi-Orthogonal (Tight Frame) $\Phi$:**
> If the rows of $\Phi$ are mutually orthonormal so that $\Phi \Phi^T = I_M$ (or $\Phi \Phi^T = c I_M$), then $(\Phi \Phi^T)^{-1} = I_M$ (or $\frac{1}{c} I_M$), and the pseudo-inverse reduces to the simple transpose: $\Phi^+ = \Phi^T$ (or $\frac{1}{c}\Phi^T$)! For i.i.d. Gaussian or Rademacher matrices with $\sigma^2 = 1/N$, $\Phi \Phi^T \approx I_M + O(\sqrt{M/N})$, which is why $\Phi^T y$ is a common cheap approximation to $\Phi^+ y$, though with slightly higher variance (see Question 3 in Section 3.10).

---

## 3.3 Why $\Phi \Phi^+ = I_M$ While $\Phi^+ \Phi$ Is a Rank-$M$ Projection

### Intuition
Why doesn't $\Phi^+ \Phi$ equal the identity matrix $I_N$? Because $\Phi$ maps $\mathbb{R}^N \to \mathbb{R}^M$ ($1024 \to 256$) and $\Phi^+$ maps $\mathbb{R}^M \to \mathbb{R}^N$ ($256 \to 1024$). A map that passes through a $256$-dimensional bottleneck cannot possibly have rank $1024$!

### Statement & Derivation
Assume $\Phi \in \mathbb{R}^{M \times N}$ has full row rank $M$.

1. **Right Inverse Property ($\Phi \Phi^+ = I_M \in \mathbb{R}^{M \times M}$):**
   $$\Phi \Phi^+ = \Phi \Phi^T (\Phi \Phi^T)^{-1} = I_M$$
   *Meaning:* If you take any measurement $y \in \mathbb{R}^M$, decode it to $\hat{x}_{\text{raw}} = \Phi^+ y \in \mathbb{R}^N$, and re-encode it with $\Phi$, you get back the **exact measurement** $\Phi \hat{x}_{\text{raw}} = \Phi \Phi^+ y = y$. Thus, $\hat{x}_{\text{raw}} = \Phi^+ y$ is always a valid solution to $\Phi z = y$.

2. **Row-Space Projector Property ($\Phi^+ \Phi = P_{\mathcal{R}} \in \mathbb{R}^{N \times N}$):**
   $$\Phi^+ \Phi = \Phi^T (\Phi \Phi^T)^{-1} \Phi = P_{\mathcal{R}}$$
   Comparing this with Section 1.3, we see that $\Phi^+ \Phi$ is the **exact orthogonal projection matrix onto $\text{row}(\Phi)$**! Using the SVD $\Phi = U \Sigma V^T$, we can also see its structure in the right singular basis $V = [v_1, \dots, v_N]$:
   $$\Phi^+ \Phi = V \Sigma^+ U^T U \Sigma V^T = V \begin{bmatrix} I_M & \mathbf{0} \\ \mathbf{0} & \mathbf{0}_{N-M} \end{bmatrix} V^T = \sum_{i=1}^M v_i v_i^T$$
   *Meaning:* When you encode $x \in \mathbb{R}^N$ as $y = \Phi x$ and decode via $\hat{x}_{\text{raw}} = \Phi^+ y = \Phi^+ \Phi x$, the combined operator $\Phi^+ \Phi$ keeps the components of $x$ along the first $M$ right singular vectors $\{v_1, \dots, v_M\}$ (which span $\text{row}(\Phi)$) with gain $1$, and zeroes out the components along the remaining $N - M$ right singular vectors $\{v_{M+1}, \dots, v_N\}$ (which span $\text{null}(\Phi)$).

---

## 3.4 The Minimum-Norm Least-Squares Property (with Proof)

### Statement
**Theorem 3.2 (Minimum $\ell_2$-Norm Solution).**
*Let $\Phi \in \mathbb{R}^{M \times N}$ have full row rank $M$, and let $y \in \mathbb{R}^M$. Among all vectors $z \in \mathbb{R}^N$ satisfying $\Phi z = y$, the vector $\hat{x}_{\text{raw}} = \Phi^+ y$ is the **unique** vector with the smallest Euclidean norm:*
$$\Phi^+ y = \arg\min_{z \in \mathbb{R}^N} \|z\|_2 \quad \text{subject to} \quad \Phi z = y$$

### Proof (via Orthogonal Decomposition and Pythagoras)
1. First, verify feasibility: by Section 3.3, $\Phi(\Phi^+ y) = (\Phi \Phi^+) y = I_M y = y$, so $\hat{x}_{\text{raw}} = \Phi^+ y$ satisfies the constraint.
2. Notice where $\hat{x}_{\text{raw}}$ lives: since $\Phi^+ y = \Phi^T \big((\Phi \Phi^T)^{-1} y\big)$, $\hat{x}_{\text{raw}}$ is a linear combination of the rows of $\Phi$, meaning:
   $$\hat{x}_{\text{raw}} \in \text{row}(\Phi)$$
3. Now take *any* candidate vector $z \in \mathbb{R}^N$ that satisfies $\Phi z = y$, and define the difference vector $h = z - \hat{x}_{\text{raw}}$. Notice that:
   $$\Phi h = \Phi z - \Phi \hat{x}_{\text{raw}} = y - y = 0 \implies h \in \text{null}(\Phi)$$
4. By the Fundamental Theorem of Linear Algebra (Section 1.2), $\text{row}(\Phi) \perp \text{null}(\Phi)$. Since $\hat{x}_{\text{raw}} \in \text{row}(\Phi)$ and $h \in \text{null}(\Phi)$, we have $\hat{x}_{\text{raw}}^T h = 0$.
5. Apply the Pythagorean theorem to $z = \hat{x}_{\text{raw}} + h$:
   $$\|z\|_2^2 = \|\hat{x}_{\text{raw}} + h\|_2^2 = \|\hat{x}_{\text{raw}}\|_2^2 + 2\underbrace{\hat{x}_{\text{raw}}^T h}_{=0} + \|h\|_2^2 = \|\hat{x}_{\text{raw}}\|_2^2 + \|z - \hat{x}_{\text{raw}}\|_2^2$$
6. Since $\|z - \hat{x}_{\text{raw}}\|_2^2 \ge 0$ with equality if and only if $z = \hat{x}_{\text{raw}}$, we conclude that $\|z\|_2 > \|\hat{x}_{\text{raw}}\|_2$ for every $z \neq \hat{x}_{\text{raw}}$ satisfying $\Phi z = y$. $\blacksquare$

---

## 3.5 Derivation of $\mathbb{E}[\Phi^+ \Phi] = \frac{M}{N} I_N$ for Rotationally Invariant $\Phi$

### Intuition
When we project a fixed vector $x \in \mathbb{R}^N$ onto a *uniformly random* $M$-dimensional subspace $\text{row}(\Phi)$ inside $\mathbb{R}^N$, no coordinate direction in $\mathbb{R}^N$ is favored over any other. Because $M$ out of $N$ orthogonal directions are preserved on average, each coordinate of $x$ retains a fraction $M/N = r$ of its value in expectation!

### Statement & Rigorous Proof
**Theorem 3.3 (Expected Projection Operator).**
*Let $\Phi \in \mathbb{R}^{M \times N}$ ($M \le N$) be a random matrix that has full row rank $M$ almost surely and whose distribution is **right-orthogonally invariant**—meaning that for every deterministic orthogonal matrix $Q \in \mathbb{R}^{N \times N}$ ($Q^T Q = I_N$), the matrix $\Phi Q$ has the same distribution as $\Phi$ (which holds for i.i.d. $\mathcal{N}(0, \sigma^2)$ entries for any $\sigma > 0$). Then:*
$$\mathbb{E}[\Phi^+ \Phi] = \frac{M}{N} I_N$$
*Consequently, for any deterministic gradient block $x \in \mathbb{R}^N$:*
$$\mathbb{E}[\hat{x}_{\text{raw}}] = \mathbb{E}[\Phi^+ \Phi x] = \frac{M}{N} x, \qquad \mathbb{E}[\hat{x}_{\text{pinv}}] = \mathbb{E}\left[\frac{N}{M}\Phi^+ \Phi x\right] = x$$

**Proof (Two Complementary Ways):**

#### Proof Method 1: Symmetry + Trace (Algebraic Proof)
1. Let $P = \Phi^+ \Phi = \Phi^T (\Phi \Phi^T)^{-1} \Phi$. For any fixed orthogonal matrix $Q \in \mathbb{R}^{N \times N}$, replace $\Phi$ by $\tilde{\Phi} = \Phi Q$. Its projection matrix is:
   $$\tilde{P} = \tilde{\Phi}^+ \tilde{\Phi} = Q^T \Phi^T (\Phi \underbrace{Q Q^T}_{I_N} \Phi^T)^{-1} \Phi Q = Q^T P Q$$
2. Since $\tilde{\Phi} \stackrel{d}{=} \Phi$, their projection matrices have the same expectation: $\mathbb{E}[\tilde{P}] = \mathbb{E}[P]$, which means:
   $$Q^T \mathbb{E}[P] Q = \mathbb{E}[P] \iff \mathbb{E}[P] Q = Q \mathbb{E}[P] \quad \text{for all orthogonal } Q \in \mathbb{R}^{N \times N}$$
3. A symmetric matrix that commutes with every orthogonal matrix must be a scalar multiple of the identity matrix, $\mathbb{E}[P] = c I_N$ for some scalar $c \in \mathbb{R}$. *(Why? Diagonalize $\mathbb{E}[P] = W \Lambda W^T$; choosing $Q$ to permute or flip eigenvectors forces all eigenvalues in $\Lambda$ to be equal.)*
4. To find the scalar $c$, take the trace of both sides of $\mathbb{E}[P] = c I_N$ and use linearity of expectation:
   $$\text{tr}(\mathbb{E}[P]) = \mathbb{E}[\text{tr}(P)] = \mathbb{E}\left[\text{tr}\big(\Phi^T (\Phi \Phi^T)^{-1} \Phi\big)\right]$$
   Apply the cyclic trace trick $\text{tr}(AB) = \text{tr}(BA)$ with $A = \Phi^T$ and $B = (\Phi \Phi^T)^{-1} \Phi$:
   $$\mathbb{E}[\text{tr}(P)] = \mathbb{E}\left[\text{tr}\big((\Phi \Phi^T)^{-1} \Phi \Phi^T\big)\right] = \mathbb{E}[\text{tr}(I_M)] = M$$
5. On the other hand, $\text{tr}(c I_N) = c N$. Equating the two gives:
   $$c N = M \implies c = \frac{M}{N} \implies \mathbb{E}[\Phi^+ \Phi] = \frac{M}{N} I_N \quad \blacksquare$$

#### Proof Method 2: SVD Haar Measure (Coordinate Intuition)
In the SVD $\Phi = U \Sigma V^T$, right-orthogonal invariance means the right singular vectors $V = [v_1, \dots, v_N]$ are distributed uniformly at random on the orthogonal group $O(N)$, so each individual column $v_i$ is distributed uniformly on the unit sphere $\mathbb{S}^{N-1}$ with $\mathbb{E}[v_i v_i^T] = \frac{1}{N} I_N$. Since $\Phi^+ \Phi = \sum_{i=1}^M v_i v_i^T$, linearity of expectation immediately gives:
$$\mathbb{E}[\Phi^+ \Phi] = \sum_{i=1}^M \mathbb{E}[v_i v_i^T] = M \cdot \frac{1}{N} I_N = \frac{M}{N} I_N \quad \blacksquare$$

---

## 3.6 Derivation of the Error $\mathbb{E}\left\|\frac{N}{M}\Phi^+\Phi x - x\right\|_2^2 = \left(\frac{N}{M} - 1\right)\|x\|_2^2$

### Intuition
Let us trace carefully what happens to $x$ both **without** and **with** the $\frac{N}{M}$ rescaling factor:
1. **Without rescaling ($\hat{x}_{\text{raw}} = \Phi^+ \Phi x = x_{\mathcal{R}}$):**
   Since $x = x_{\mathcal{R}} + x_{\mathcal{N}}$ with $x_{\mathcal{R}} \perp x_{\mathcal{N}}$, the expected squared length of the kept piece $x_{\mathcal{R}}$ is $\frac{M}{N}\|x\|_2^2$, and the expected squared length of the discarded piece $x_{\mathcal{N}} = x - \hat{x}_{\text{raw}}$ is $\left(1 - \frac{M}{N}\right)\|x\|_2^2$.
   Furthermore, along the direction of the true vector $x$, the component of $\hat{x}_{\text{raw}}$ is:
   $$\frac{x^T \hat{x}_{\text{raw}}}{\|x\|_2^2} x = \frac{x^T P_{\mathcal{R}} x}{\|x\|_2^2} x = \frac{\|P_{\mathcal{R}} x\|_2^2}{\|x\|_2^2} x \approx \frac{M}{N} x$$
   So $\hat{x}_{\text{raw}}$ shrinks the true gradient component to $\frac{M}{N} = 0.25$ of its length, plus an orthogonal error component!
2. **With $\frac{N}{M}$ rescaling ($\hat{x}_{\text{pinv}} = \frac{N}{M}\Phi^+ \Phi x = \frac{N}{M} x_{\mathcal{R}}$):**
   Multiplying $x_{\mathcal{R}}$ by $\frac{N}{M} = 4$ restores the component along $x$ to full unit strength on average ($\mathbb{E}[\hat{x}_{\text{pinv}}] = x$), **but it also amplifies the orthogonal leakage in $\text{row}(\Phi)$ by $\frac{N}{M}$!** Let us compute the resulting variance exactly.

### Statement & Complete Derivation
**Theorem 3.4 (Exact MSE and Variance of Unscaled and Rescaled Pseudo-Inverse).**
*Under the conditions of Theorem 3.3 (specifically $\mathbb{E}[P_{\mathcal{R}}] = \frac{M}{N}I_N$ and $P_{\mathcal{R}}^2 = P_{\mathcal{R}}^T = P_{\mathcal{R}}$), for any deterministic vector $x \in \mathbb{R}^N$:*
1. **Expected squared norm of raw decode:**
   $$\mathbb{E}\left[\|\Phi^+ \Phi x\|_2^2\right] = \frac{M}{N}\|x\|_2^2$$
2. **Expected squared error of raw (unscaled) decode $\hat{x}_{\text{raw}} = \Phi^+ \Phi x$:**
   $$\mathbb{E}\left[\|\Phi^+ \Phi x - x\|_2^2\right] = \left(1 - \frac{M}{N}\right)\|x\|_2^2$$
3. **Expected squared norm of rescaled decode $\hat{x}_{\text{pinv}} = \frac{N}{M}\Phi^+ \Phi x$:**
   $$\mathbb{E}\left[\left\|\frac{N}{M}\Phi^+ \Phi x\right\|_2^2\right] = \frac{N}{M}\|x\|_2^2$$
4. **Expected squared error (variance) of rescaled decode $\hat{x}_{\text{pinv}} = \frac{N}{M}\Phi^+ \Phi x$:**
   $$\mathbb{E}\left[\left\|\frac{N}{M}\Phi^+ \Phi x - x\right\|_2^2\right] = \left(\frac{N}{M} - 1\right)\|x\|_2^2$$

**Proof:**
Let $P = \Phi^+ \Phi$. Recall the three facts we established:
$$P^T = P, \qquad P^2 = P, \qquad \mathbb{E}[P] = \frac{M}{N}I_N$$

- **Part 1:** Expand $\|\Phi^+ \Phi x\|_2^2 = \|P x\|_2^2$:
  $$\|P x\|_2^2 = (P x)^T (P x) = x^T P^T P x = x^T P^2 x = x^T P x$$
  Now take the expectation using linearity of expectation:
  $$\mathbb{E}\left[\|P x\|_2^2\right] = \mathbb{E}[x^T P x] = x^T \mathbb{E}[P] x = x^T \left(\frac{M}{N} I_N\right) x = \frac{M}{N} x^T x = \frac{M}{N}\|x\|_2^2$$

- **Part 2:** Since $I_N - P = P_{\mathcal{N}}$ is also an orthogonal projector ($(I_N - P)^2 = I_N - P$), we have:
  $$\mathbb{E}\left[\|P x - x\|_2^2\right] = \mathbb{E}\left[x^T (I_N - P)^2 x\right] = x^T (I_N - \mathbb{E}[P]) x = \left(1 - \frac{M}{N}\right)\|x\|_2^2$$

- **Part 3:** Scale Part 1 by $\left(\frac{N}{M}\right)^2$:
  $$\mathbb{E}\left[\left\|\frac{N}{M} P x\right\|_2^2\right] = \left(\frac{N}{M}\right)^2 \mathbb{E}\left[\|P x\|_2^2\right] = \left(\frac{N}{M}\right)^2 \left(\frac{M}{N}\|x\|_2^2\right) = \frac{N}{M}\|x\|_2^2$$

- **Part 4 (Two ways to see it):**
  *Direct algebraic expansion:*
  $$\left\|\frac{N}{M} P x - x\right\|_2^2 = \left\|\frac{N}{M} P x\right\|_2^2 - 2 \frac{N}{M} x^T P x + \|x\|_2^2 = \left(\frac{N}{M}\right)^2 x^T P x - 2\frac{N}{M} x^T P x + \|x\|_2^2$$
  Take the expectation of each term using $\mathbb{E}[x^T P x] = \frac{M}{N}\|x\|_2^2$:
  $$\begin{aligned}
  \mathbb{E}\left[\left\|\frac{N}{M} P x - x\right\|_2^2\right] &= \left(\frac{N}{M}\right)^2 \left(\frac{M}{N}\|x\|_2^2\right) - 2\frac{N}{M}\left(\frac{M}{N}\|x\|_2^2\right) + \|x\|_2^2 \\
  &= \frac{N}{M}\|x\|_2^2 - 2\|x\|_2^2 + \|x\|_2^2 \\
  &= \left(\frac{N}{M} - 1\right)\|x\|_2^2
  \end{aligned}$$
  *Or via the Bias-Variance identity (Section 1.6):* Since $\mu = \mathbb{E}[\hat{x}_{\text{pinv}}] = x$, for any unbiased estimator:
  $$\mathbb{E}\left[\|\hat{x}_{\text{pinv}} - x\|_2^2\right] = \mathbb{E}\left[\|\hat{x}_{\text{pinv}}\|_2^2\right] - \|x\|_2^2 = \frac{N}{M}\|x\|_2^2 - \|x\|_2^2 = \left(\frac{N}{M} - 1\right)\|x\|_2^2 \quad \blacksquare$$

### Worked Numerical Check at Your Operating Point ($N = 1024, M = 256, r = 0.25$)
Suppose $\|x\|_2^2 = 10.0$ and $r = M/N = 256/1024 = 0.25$ (so $N/M = 4$):
- **Unscaled $\hat{x}_{\text{raw}} = \Phi^+ \Phi x$:**
  - Expected vector: $\mathbb{E}[\hat{x}_{\text{raw}}] = 0.25 x$ (shrunk by $4\times$!).
  - Expected energy: $\mathbb{E}[\|\hat{x}_{\text{raw}}\|_2^2] = 0.25 \times 10.0 = 2.5$.
  - Expected MSE: $\mathbb{E}[\|\hat{x}_{\text{raw}} - x\|_2^2] = (1 - 0.25) \times 10.0 = 7.5$.
- **Rescaled $\hat{x}_{\text{pinv}} = 4 \Phi^+ \Phi x$:**
  - Expected vector: $\mathbb{E}[\hat{x}_{\text{pinv}}] = 1.0 x$ (**unbiased!**).
  - Expected energy: $\mathbb{E}[\|\hat{x}_{\text{pinv}}\|_2^2] = 4 \times 10.0 = 40.0$.
  - Expected MSE (variance): $\mathbb{E}[\|\hat{x}_{\text{pinv}} - x\|_2^2] = (4 - 1) \times 10.0 = 30.0 = 3\|x\|_2^2$.

---

## 3.7 Gaussian vs. Rademacher $\Phi$: What Changes and What Doesn't?

In your setup, $\Phi$ is either i.i.d. Gaussian ($\Phi_{ij} \sim \mathcal{N}(0, \sigma^2)$) or i.i.d. Rademacher ($\Phi_{ij} \in \{-\sigma, +\sigma\}$ with probability $1/2$). Let us be $100\%$ rigorous about what changes between the two.

| Property | i.i.d. Gaussian $\Phi$ | i.i.d. Rademacher $\Phi \in \{\pm\sigma\}^{M\times N}$ |
| :--- | :--- | :--- |
| **Invertibility of $\Phi\Phi^T$** | Invertible with probability **exactly $1$** | Invertible with probability $1 - 2^{-\Omega(N)}$ (at $N=1024, M=256$, failure probability $< 10^{-200}$) |
| **Symmetry of distribution** | Invariant under **all** orthogonal rotations $Q \in O(N)$ | Invariant under **signed permutations** (hypercube symmetries): permuting coordinates and flipping signs |
| **Off-diagonal of $\mathbb{E}[\Phi^+\Phi]$** | **Exactly $0$** | **Exactly $0$** (by sign-flip symmetry: flipping sign of column $j$ flips sign of $P_{ij}$ for $i \neq j$) |
| **Diagonal of $\mathbb{E}[\Phi^+\Phi]$** | **Exactly $\frac{M}{N}$** | **Exactly $\frac{M}{N}$** (whenever $\text{rank}(\Phi)=M$, by permutation symmetry + $\text{tr}(P) = M$) |
| **$\mathbb{E}[\Phi^+\Phi]$ (conditioned on full rank)** | **Exactly $\frac{M}{N} I_N$** | **Exactly $\frac{M}{N} I_N$!** |
| **$\mathbb{E}\|\frac{N}{M}\Phi^+\Phi x - x\|_2^2$** | **Exactly $\left(\frac{N}{M}-1\right)\|x\|_2^2$** | **Exactly $\left(\frac{N}{M}-1\right)\|x\|_2^2$!** |
| **Distribution of $\|P_{\mathcal{R}} x\|_2^2$ around $\frac{M}{N}\|x\|_2^2$** | Identical for all unit vectors $x$ ($\text{Beta}\left(\frac{M}{2}, \frac{N-M}{2}\right)$) | Depends slightly at $O(1/N)$ on the kurtosis/sparsity $\|x\|_4^4 / \|x\|_2^4$ of $x$ |
| **Memory & Compute Cost** | 32 bits/entry (or PRNG regeneration); FP32 FMA | **1 bit/entry**; multiplication $\Phi x$ requires **only additions/subtractions** |

> **Wait—does $\mathbb{E}[\Phi^+\Phi] = \frac{M}{N} I_N$ really hold *exactly* for Rademacher matrices too?**
> **Yes!** Many practitioners assume $\mathbb{E}[\Phi^+\Phi] = \frac{M}{N} I_N$ requires full continuous rotational invariance. In fact, the proof in Section 3.5 only needs two discrete symmetries to force $\mathbb{E}[P] = c I_N$:
> 1. **Sign-flip invariance:** Let $D \in \text{diag}(\pm 1, \dots, \pm 1)$ be any diagonal sign matrix. If $\Phi$ is Rademacher, $\Phi D \stackrel{d}{=} \Phi$, so $D \mathbb{E}[P] D = \mathbb{E}[P]$. Choosing $D$ with $-1$ in entry $j$ and $+1$ elsewhere gives $-(\mathbb{E}[P])_{ij} = (\mathbb{E}[P])_{ij} \implies (\mathbb{E}[P])_{ij} = 0$ for all $i \neq j$. Thus $\mathbb{E}[P]$ is strictly diagonal!
> 2. **Coordinate-permutation invariance:** Permuting columns of a Rademacher matrix leaves its distribution unchanged, so all diagonal entries $(\mathbb{E}[P])_{jj}$ must be equal to the same constant $c$.
> 3. **Trace identity:** Whenever $\Phi$ has full row rank $M$, $\text{tr}(P) = M$, so $c = M/N$!
>
> **What *does* change between Gaussian and Rademacher?**
> While the **mean** $\mathbb{E}[P x] = \frac{M}{N} x$ and the **expected squared error** $\mathbb{E}[\|\frac{N}{M}Px - x\|_2^2] = (\frac{N}{M}-1)\|x\|_2^2$ are identical (conditioned on full rank), the **fourth-moment fluctuations** (the variance *of* the squared norm $\|Px\|_2^2$ from draw to draw of $\Phi$) differ slightly by an $O(1/N)$ term proportional to $\|x\|_4^4 / \|x\|_2^4$ because Rademacher entries have fourth moment $\mathbb{E}[\Phi_{ij}^4] = \sigma^4$ instead of $3\sigma^4$. At $N = 1024$, this difference is less than $0.1\%$.

---

## 3.8 Linearity and Why the Pseudo-Inverse Commutes with AllReduce

### Intuition & Derivation
In distributed data-parallel training with $W$ workers, worker $i$ holds local gradient block $g_i \in \mathbb{R}^N$. The optimizer wants the average gradient $\bar{g} = \frac{1}{W}\sum_{i=1}^W g_i$.
With a shared sensing matrix $\Phi$, worker $i$ computes $y_i = \Phi g_i \in \mathbb{R}^M$. An AllReduce operation averages the compressed measurements across all workers:
$$\bar{y} = \frac{1}{W}\sum_{i=1}^W y_i = \frac{1}{W}\sum_{i=1}^W \Phi g_i = \Phi \left(\frac{1}{W}\sum_{i=1}^W g_i\right) = \Phi \bar{g}$$
Now the receiver applies the rescaled pseudo-inverse decoder $\mathcal{D}_{\text{pinv}}(y) = \frac{N}{M}\Phi^+ y$ **once** to $\bar{y}$. Because matrix multiplication by $\frac{N}{M}\Phi^+$ is a **linear operator**, we have:
$$\mathcal{D}_{\text{pinv}}(\bar{y}) = \frac{N}{M}\Phi^+ \left(\frac{1}{W}\sum_{i=1}^W y_i\right) = \frac{1}{W}\sum_{i=1}^W \left(\frac{N}{M}\Phi^+ y_i\right) = \frac{1}{W}\sum_{i=1}^W \mathcal{D}_{\text{pinv}}(y_i)$$
That is:
$$\boxed{\text{Decode of the Average} = \text{Average of the Decodes}}$$
This gives you two massive wins simultaneously:
1. **Computational Win:** You run the decoder **1 time** per block instead of $W$ times (if using AllGather + decode).
2. **Statistical Win:** The variance of the decoded average scales with $\|\bar{g}\|_2^2$, not with $\sum_i \|g_i\|_2^2$. And if the workers had chosen independent $\Phi_i$ (which would preclude AllReduce), or if you used a nonlinear decoder (like $\ell_1$, as we prove in Chapter 6), this exact commutativity breaks down!

---

## 3.9 Computational and Memory Cost

Let us count the exact floating-point operations (FLOPs, where 1 multiply-add = 2 FLOPs) for $N = 1024, M = 256$:

1. **Case A: Fixed $\Phi$ Across the Training Run (Your Setup):**
   - **One-time offline setup at initialization:** Compute $\Phi^+ = \Phi^T (\Phi \Phi^T)^{-1}$ (or via SVD) once.
     Cost: Forming $\Phi \Phi^T$ takes $2 M^2 N \approx 1.34 \times 10^8$ FLOPs; Cholesky/inversion of $M \times M$ takes $\frac{1}{3}M^3 \approx 5.6 \times 10^6$ FLOPs; multiplying $\Phi^T (\Phi\Phi^T)^{-1}$ takes $2 N M^2 \approx 1.34 \times 10^8$ FLOPs. Total one-time cost: **$\sim 2.7 \times 10^8$ FLOPs ($\sim 0.1$ milliseconds on a modern GPU)**, amortized over tens of thousands of training steps!
   - **Memory to store $\Phi$ and $\frac{N}{M}\Phi^+$:** Since the same $256 \times 1024$ matrix is reused across all blocks of the neural network gradient, storing $\Phi$ and $\frac{N}{M}\Phi^+$ in FP32 takes only $2 \times 256 \times 1024 \times 4\text{ bytes} = \mathbf{2\text{ MB}}$ of GPU SRAM/HBM!
   - **Per-block Encode Cost ($y = \Phi x$):** One matrix-vector multiply of size $M \times N$ ($2MN = 524,288$ FLOPs). And if $B$ blocks are stacked into a matrix $X \in \mathbb{R}^{N \times B}$, encoding all $B$ blocks at once is a single **GEMM (General Matrix-Matrix Multiply)** $Y = \Phi X$, which runs at near peak Tensor Core throughput on GPUs!
   - **Per-block Decode Cost ($\hat{x} = (\frac{N}{M}\Phi^+) \bar{y}$):** One matrix-vector multiply of size $N \times M$ ($2NM = 524,288$ FLOPs), or a single GEMM $\hat{X} = (\frac{N}{M}\Phi^+) \bar{Y}$ across all $B$ blocks.

2. **Case B: Regenerating $\Phi_t$ Every Step:**
   If $\Phi_t$ is regenerated at every step $t$, computing $(\Phi_t \Phi_t^T)^{-1}$ costs $\sim 2.7 \times 10^8$ FLOPs once per step (shared across all $B$ blocks of the model). For a model with $10^8$ parameters ($B \approx 10^5$ blocks of size $1024$), this per-step matrix inversion adds $< 0.3\%$ overhead compared to the $2 B M N \approx 5 \times 10^{10}$ FLOPs of encoding/decoding the blocks.

---

## 3.10 Empirical Verification in NumPy

This self-contained script verifies:
1. The SVD definition vs. $\Phi^T(\Phi\Phi^T)^{-1}$.
2. The $M/N = 0.25$ shrinkage without rescaling and unbiased recovery with $N/M = 4$ rescaling.
3. The exact $(N/M - 1)\|x\|_2^2 = 3\|x\|_2^2$ error formula for **both** Gaussian and Rademacher matrices.
4. Exact AllReduce commutativity across $W = 8$ workers.

```python
import numpy as np

rng = np.random.default_rng(123)
N, M = 1024, 256
r = M / N
scale = N / M  # 4.0

# Create a deterministic "true gradient block" x with known norm
x = rng.standard_normal(N)
x_norm_sq = np.sum(x ** 2)

for dist in ["Gaussian", "Rademacher"]:
    trials = 400
    raw_dots = []
    rescaled_mean = np.zeros(N)
    rescaled_err_sq = []

    for _ in range(trials):
        if dist == "Gaussian":
            Phi = rng.normal(0.0, 1.0 / np.sqrt(N), size=(M, N))
        else:
            Phi = rng.choice([-1.0, 1.0], size=(M, N)) / np.sqrt(N)

        # Explicit formula Phi^+ = Phi^T (Phi Phi^T)^{-1}
        Phi_pinv = Phi.T @ np.linalg.inv(Phi @ Phi.T)
        y = Phi @ x

        x_raw = Phi_pinv @ y
        x_pinv = scale * x_raw

        # Relative projection along x: (x^T x_raw) / ||x||^2
        raw_dots.append(np.dot(x, x_raw) / x_norm_sq)
        rescaled_mean += x_pinv / trials
        rescaled_err_sq.append(np.sum((x_pinv - x) ** 2))

    rel_bias = np.linalg.norm(rescaled_mean - x) / np.linalg.norm(x)
    emp_ratio = np.mean(rescaled_err_sq) / x_norm_sq
    print(f"=== {dist} Sensing Matrix (N={N}, M={M}, {trials} trials) ===")
    print(f"  Mean unscaled shrink (x^T x_raw / ||x||^2): {np.mean(raw_dots):.4f} (Theory M/N = {r:.4f})")
    print(f"  Relative bias of rescaled mean ||E[x_pinv]-x||/||x||: {rel_bias:.4f} (Theory -> 0)")
    print(f"  Mean rescaled error E||x_pinv - x||^2 / ||x||^2: {emp_ratio:.4f} (Theory N/M - 1 = {scale - 1:.4f})")

# Verify AllReduce commutativity across W = 8 workers
W = 8
G = rng.standard_normal((W, N))
Phi = rng.normal(0.0, 1.0 / np.sqrt(N), size=(M, N))
Phi_pinv = Phi.T @ np.linalg.inv(Phi @ Phi.T)

decode_of_avg = scale * (Phi_pinv @ np.mean(Phi @ G.T, axis=1))
avg_of_decodes = np.mean(scale * (Phi_pinv @ (Phi @ G.T)), axis=1)
print(f"\nAllReduce Commutativity Difference: {np.linalg.norm(decode_of_avg - avg_of_decodes):.2e}")
```

---

## 3.11 Check Your Understanding

*(Full solutions are in [Chapter 99](./99-solutions-and-references.md).)*

1. **Scaling Invariance of $\Phi^+ \Phi$:** Suppose Worker A generates $\Phi$ with $\mathcal{N}(0, 1)$ entries, Worker B generates $\Phi$ with $\mathcal{N}(0, 1/M)$ entries, and Worker C generates $\Phi$ with $\mathcal{N}(0, 1/N)$ entries (using the same random seed). Does the decoded vector $\hat{x}_{\text{pinv}} = \frac{N}{M}\Phi^+ y = \frac{N}{M}\Phi^+ \Phi x$ change at all between Workers A, B, and C? Prove your answer algebraically.
2. **Cosine Similarity Between Decoded and True Gradient:** Using $\hat{x}_{\text{pinv}} = \frac{N}{M} P_{\mathcal{R}} x$, show that the cosine similarity between the decoded gradient $\hat{x}_{\text{pinv}}$ (or $\hat{x}_{\text{raw}}$) and the true gradient $x$ is:
   $$\cos(\theta) = \frac{x^T \hat{x}_{\text{pinv}}}{\|x\|_2 \|\hat{x}_{\text{pinv}}\|_2} = \frac{\|P_{\mathcal{R}} x\|_2}{\|x\|_2} \approx \sqrt{\frac{M}{N}} = \sqrt{r}$$
   At $r = 0.25$, what is this expected cosine similarity, and what is the angle $\theta$ in degrees between $\hat{x}_{\text{pinv}}$ and $x$?
3. **Transpose Decoder $\Phi^T$ vs. Pseudo-Inverse Decoder $\Phi^+$:** Suppose $\Phi \in \mathbb{R}^{M \times N}$ has i.i.d. entries with mean $0$ and variance $1/M$, so $\mathbb{E}[\Phi^T \Phi] = \frac{N}{M} I_N$? Wait—check carefully: if $\mathbb{E}[\Phi_{ij}^2] = 1/M$, what is $\mathbb{E}[\Phi^T \Phi]$, and why does the pure transpose decoder $\hat{x}_{\text{trans}} = \Phi^T \Phi x$ have strictly **higher** variance than the rescaled pseudo-inverse $\hat{x}_{\text{pinv}} = \frac{N}{M}\Phi^+ \Phi x$?
