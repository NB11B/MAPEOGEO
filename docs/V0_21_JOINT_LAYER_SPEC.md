# MAPEOGEO v0.21 Joint Layer Specification

## 1. Scope and Governing Principles
This specification defines the architectural and mathematical foundations for the **v0.21 Joint Layer** in MAPEOGEO. The joint layer connects distinct mathematical formalisms across four executable view slots (`eo`, `geo`, `pct`, `formal`) with external provenance tracking (`NATURAL`) without asserting semantic identity (`SAME_SEMANTICS`).

### Core Architectural Rules:
1. **Zero Auto-Promotion**: Mechanism joints and correspondence certificates never assert `SAME_SEMANTICS` or `EQUIVALENT_TO`. All cross-view alignments are governed by structured typed relations (`SCOPED_OVERLAP`, `SCOPED_TRANSFER`, `DUALITY_BETWEEN`, `COMPLEX_OF`, etc.).
2. **Four Executable View Slots**:
   - `eo`: Equation/operator view (direct symbolic/algebraic formulations).
   - `geo`: Geometric/topological view (metric, manifold, and coordinate representations).
   - `pct`: Computational trace / property-based executable test view.
   - `formal`: Interactive theorem prover view (Lean 4 kernel verified).
   - Provenance (`NATURAL`) is isolated as metadata and does not count as an executable view slot.
3. **Strict Certificate Quorum**:
   - Status `CERTIFIED` requires at least $\ge 2$ independent witnesses (`EO`, `GEO`, `PCT` with B4+ boundary commutation, `FORMAL` `KERNEL_VERIFIED`).
   - Duplicate statement digests or alias pairs are rejected ($1 \ne 2$).
   - Unverified formal links (`FORMAL_LINKED` without Lean kernel check) are excluded from quorum.
4. **Typed Scope Comparator**:
   - Every joint and certificate carries a `TypedScopeRecord` (`domain`, `dimension`, `coefficient_ring`, `regularity`, `orientation_convention`, `boundary_convention`, `parameter_range`, `exceptional_cases`).
5. **Frozen Baseline Preservation**:
   - `data/mapeogeo_v0_11_graph.json.gz` remains byte-identical (`409a648d8563bc4a027dc3dc29fc53722d11bc489462a0f3d1f71bd4f272544d`).

---

## 2. Ten Canonical Mechanism Joint Types
| Joint Type | Description | Allowed Roles | Default Relationship |
| :--- | :--- | :--- | :--- |
| `METRIC_CONTRACTION` | Index contraction/trace reducing tensor rank (Riemann $\to$ Ricci) | `ambient_tensor`, `contracted_tensor`, `source_metric` | `CONTRACTION_OF` |
| `GRADIENT_FLOW` | Nonlinear evolution PDE deforming tensors along gradients | `flow_equation`, `evolving_field`, `generator` | `ACTS_ON` |
| `TOPOLOGICAL_SURGERY` | Cutting neck singularities and gluing capped standard manifolds | `surgery_operation`, `target_neck`, `cut_interface`, `replacement_cap` | `SURGERY_OF` |
| `MONOTONICITY_FORMULA` | Non-decreasing/non-increasing integral functional along flows | `functional_quantity`, `flow_trajectory`, `backward_kernel` | `MONOTONE_ALONG` |
| `ASYMPTOTIC_BLOWUP` | Parabolic dilation convergence to standard singularity models | `singularity_model`, `blowup_limit`, `parabolic_dilation` | `BLOWS_UP_AS` |
| `VARIATIONAL_COUPLING` | Euler-Lagrange variational correspondence between action and fields | `action_functional`, `critical_point`, `constraint_manifold` | `COUPLING_OF` |
| `BOUNDARY_DUALITY` | Adjoint pairing between boundary and exterior derivative | `boundary_operator`, `exterior_derivative`, `chain_complex` | `DUALITY_BETWEEN` |
| `SPECTRAL_PROJECTION` | Orthogonal eigenspace projection for self-adjoint operators | `differential_operator`, `eigenspace_decomposition`, `spectral_projector` | `SPECTRAL_DECOMPOSITION_OF` |
| `HOMOLOGICAL_COMPLEX` | Boundary and coboundary chains with nilpotency ($\partial^2=0, d^2=0$) | `chain_group`, `cochain_group`, `boundary_map`, `coboundary_map` | `COMPLEX_OF` |
| `COBORDISM` | Manifold with boundary interpolating between disjoint manifolds | `manifold_source`, `manifold_target`, `cobordism_manifold` | `COBORDISM_BETWEEN` |

---

## 3. Package S: Simplicial Stokes Specification
Package S defines simplicial boundary and exterior derivative duality over $\mathbb{Q}$:
- **Domain**: Simplicial complex $\Delta^k$ over rational coefficients $\mathbb{Q}$.
- **Boundary Operator**: $\partial_k : C_k \to C_{k-1}$ with $\partial \sigma = \sum_{i=0}^k (-1)^i [v_0, \dots, \hat{v}_i, \dots, v_k]$.
- **Orientation**: Odd permutation of vertices reverses orientation sign.
- **Nilpotency**: $\partial^2 = 0$ and $d^2 = 0$.
- **Adjoint Transpose**: Incidence matrices satisfy $B = D^T$.
- **Duality Pairing**: $\langle d\alpha, \sigma \rangle = \langle \alpha, \partial\sigma \rangle$.

---

## 4. Package P: Candidate Mechanism Grammar
Package P specifies 6 candidate mechanism joints for Hamilton/Perelman Ricci flow without ingesting unverified corpus prose:
1. `joint:perelman:riemann_to_ricci_contraction` (`METRIC_CONTRACTION`, `CONTRACTION_OF`)
2. `joint:perelman:ricci_flow_action_on_metric` (`GRADIENT_FLOW`, `ACTS_ON`)
3. `joint:perelman:w_entropy_monotonicity` (`MONOTONICITY_FORMULA`, `MONOTONE_ALONG`)
4. `joint:perelman:neck_singularity_asymptotic_blowup` (`ASYMPTOTIC_BLOWUP`, `BLOWS_UP_AS`)
5. `joint:perelman:topological_surgery_on_neck` (`TOPOLOGICAL_SURGERY`, `SURGERY_OF`)
6. `joint:perelman:reduced_volume_monotonicity` (`MONOTONICITY_FORMULA`, `MONOTONE_ALONG`)

All 6 joints remain strictly in status `CANDIDATE`.

---

## 5. Preregistered Horn Query Specification
- **Metric**: Brandes directed betweenness centrality.
- **Shear**: View shear $|EO - GEO| / (EO + GEO)$.
- **Thresholds**: $\tau_b = 0.05, \tau_s = 0.5$.
- **Null Model**: 100 trials of degree-preserving double edge swaps.
- **Mutation Policy**: Evidence-only; 0 graph edges or node mutations generated.
