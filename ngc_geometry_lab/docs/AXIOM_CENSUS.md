# Structural Axiom Census: Dependency Graph & Epistemological Ledger

> **Governing Question:** Does the Geometric / MAPEOGEO framework actually reduce the amount of independent mathematical structure required to recover the tested quantum phenomena, or does it merely rewrite conventional formalism into real coordinates?
>
> **Core Epistemological Principle:**
> \[\boxed{\text{Renamed Assumption} \;\ne\; \text{Compressed Assumption} \;\ne\; \text{Derived Consequence}}\]

---

## 1. Granular Decomposition of Mathematical Primitives

To avoid superficial "axiom counting" where a single bullet bundles massive structural machinery, we expand every candidate primitive into its independent mathematical components:

| Candidate Primitive Bundle | Contained Independent Structure | Epistemological Status | Role in Geometric Reconstruction |
|---|---|:---:|---|
| **Convex Physical State Space** | Closure under statistical mixtures ($\sum p_i \rho_i$) | **[A] Assumed** | Basic operational requirement for probabilistic mixture theories. |
| **Spatial Invariance Group** | Dimension $= 3$; Euclidean metric $G = I_3$; continuous Lie group $SO(3)$ acting transitively on spatial directions | **[A] Assumed** | Roots state representation in external physical space orientation. |
| **Compactness & Scale Calibration** | Boundedness, topological compactness, existence of extremal states, calibrated radius $R = 1$ | **[A] Assumed** | Prevents unbounded dilation; defines pure state boundary. |
| **Planar Phase & Symplectic Structure** | Real dual lanes $(u, v) \in \mathbb{R}^{2d}$ equipped with canonical symplectic structure $J = \begin{pmatrix} 0 & -I \\ I & 0 \end{pmatrix}$ ($J^2 = -I$) | **[A] Assumed** | Supplies planar orientation without postulating $\sqrt{-1}$ as primitive ontology. |
| **Readout Functional** | Affine mixture mapping $p(r) = \alpha + \beta \cdot r$; probability validity $0 \le p(r) \le 1$; sharp antipodal calibration $p(\pm n) = \frac{1 \pm 1}{2}$ | **[A] Assumed** | Operational definition of a calibrated measurement detector. |
| **Composite Multi-Linear Grammar** | Joint state space is the bilinear connection of local systems: $(r_A, r_B, T)$ with $T \in \mathbb{R}^{3 \times 3}$ and $\|T\|_{\text{op}} \le 1$ | **[A] Assumed** | Bilinear pairing of local observation spaces; local marginal consistency. |
| **Relational Admissibility** | A local operation $E$ is physically admissible $\iff (E \otimes I_k)$ preserves joint-state positivity for all required extensions $k$ | **[A] Assumed** | Relational requirement of joint composition (structurally equivalent to complete positivity). |
| **Relational Compatibility Hypergraph** | Observables form vertices $V$; compatible measurement contexts form hyperedges $\mathcal{C}$; required context parity products $\sigma(C) \in \{\pm 1\}$ | **[A] Assumed** | Relational incidence structure of jointly executable observations. |

---

## 2. Epistemological Ledger: Derived vs. Represented Structure

With primitives granularly identified, we classify what is genuinely **[D] Derived**, what is **[R] Represented**, and what is **[V] Verified**:

| Structural Claim | Standard Hilbert-Space Status | Geometric/MAPEOGEO Status | Precise Scope & Boundary of the Result |
|---|---|:---:|---|
| **Qubit Bloch Ball $\mathcal{B}_1$** | Derived from $2 \times 2$ density matrices $\text{Tr}\rho=1, \rho \ge 0$. | **[D] Derived** | **Scoped:** Convexity + compactness + transitive $SO(3)$ rotational symmetry uniquely forces the Euclidean unit ball in $\mathbb{R}^3$. |
| **Born Rule ($p = \cos^2\frac{\theta}{2}$)** | Postulated as independent axiom (Lüders/Born). | **[D] Derived** | **Scoped strictly to binary qubit measurements:** Mixture affinity + sharp calibration + global positivity forces $\alpha=1/2, \beta=n/2$. Rotational covariance is eliminated as an independent premise. |
| **Unitary Evolution** | Postulated via Schrödinger equation $i\hbar \dot\psi = H\psi$. | **[R] Represented / [V] Verified** | **Scoped:** Realification homomorphism $\Phi(UV) = \Phi(U)\Phi(V)$ faithfully executes unitary dynamics in real dual lanes. *Does not yet derive that all quantum dynamics must be unitary.* |
| **Observable Lie / Jordan Algebra** | Postulated associative matrix product $A B$. | **[D] Derived / [V] Verified** | **Scoped to single-qubit observables:** Jordan product $A \circ B$ extracts Euclidean inner product; Lie bracket $[A, B]$ extracts oriented bivector cross product $2i (a \times b) \cdot \sigma$. |
| **Geometric Robertson Bound** | Postulated via Hilbert-space operator variances. | **[D] Derived / [V] Verified** | **Scoped to traceless qubit observables:** $\Delta A \Delta B \ge |(a \times b) \cdot r| = |\det[a, b, r]|$ is the oriented volume lower bound. *Distinguishes lower bound from actual variance product on non-saturating states.* |
| **Tsirelson Bound ($|S| \le 2\sqrt{2}$)** | Derived via non-commuting operator C* algebra (Cirel'son). | **[D] Derived within Euclidean Bilinear Geometry** | **Scoped:** Follows from the parallelogram identity $\|b+b'\|^2 + \|b-b'\|^2 = 4$ combined with Cauchy-Schwarz on operator norm $\|T\|_{\text{op}} \le 1$. *Leaves open why nature selects Euclidean bilinear correlation geometry over general non-signaling box theories.* |
| **Contextuality Obstruction** | Kochen-Specker projector coloring contradiction. | **[D] Derived / [V] Verified** | **Scoped to Peres-Mermin incidence hypergraph:** Parity inconsistency $\sum \text{deg}(v) \equiv 0 \pmod 2$ vs $\sum b_e \equiv 1 \pmod 2$ proves algebraic obstruction $0 \equiv 1 \pmod 2$, bounding classical satisfaction to $\le 5/6$. |
| **Complete Positivity Boundary** | Postulated via Kraus representation $\sum K_\alpha \rho K_\alpha^\dagger$. | **[D] Derived from Relational Admissibility** | **Scoped:** Transposition and locally contracting non-CP maps are rejected because their relational extension to $|\Phi^+\rangle$ produces negative joint eigenvalues (e.g. $-0.5$ on singlet). *Relational admissibility is not a weaker premise than CP; it is the physical operational meaning of CP.* |
| **Continuous Lindblad Flow** | Postulated via Gorini-Kossakowski-Sudarshan-Lindblad master equation. | **[D] Derived / [V] Verified** | **Scoped:** Observation generator $(\mathcal{L}_{\text{obs}})_{ij} = \frac{n_i \cdot v + 3 n_i \cdot (M n_j)}{4}$ has zero column sum. Preserves probability normalization, while complete positivity strictly requires the relaxation rate triangle inequality $\Gamma_z \le \Gamma_x + \Gamma_y$. |

---

## 3. The Core MAPEOGEO Insight

Rather than claiming a simplistic compression percentage, the genuine scientific advance of the geometric reconstruction is encapsulated in one foundational principle:

\[
\boxed{\text{Physical Validity is Relational, Not Merely Local.}}
\]

1. **The Transpose Adversary:** Local appearance is insufficient ($\|A_T r\| \le 1$ passes locally, but fails relationally on entangled states).
2. **The Qutrit Adversary:** Low-order quadratic geometry is insufficient (passes quadratic Casimir purity $\|r\|^2 \le 4/3$ and all SIC probabilities $p_k > 0$, but fails higher-order cubic determinant/positivity $\det\rho < 0$).
3. **The Lindblad Adversaries:** Normalization preservation is insufficient ($\sum_i \mathcal{L}_{ij} = 0$), and local contraction is insufficient; complete positivity requires the relational rate triangle inequality.
4. **The Contextuality Hypergraph:** Locally consistent classical valuations are globally impossible ($0 \equiv 1 \pmod 2$).

The relational geometry carries the physical admissibility constraints needed to recognize quantum mechanics from within spatial and compositional geometry.

