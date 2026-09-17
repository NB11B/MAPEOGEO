# MAPEOGEO Joint-Layer Design (v0.21 target)

**Working name:** joint / dual-prover / PCT-attachment layer  
**Status:** Approved design with rigorous semantic constraints  
**Does not merge until:** independent review + full regression + sealed v0.11 digest unchanged  
**Frozen inputs:**
- `data/mapeogeo_v0_11_graph.json.gz` SHA-256 `409a648d8563bc4a027dc3dc29fc53722d11bc489462a0f3d1f71bd4f272544d`
- sealed v0.19 alignments (byte-identical; joints are additive)
- v0.20 integrity amendments (in-memory projection remains the active identity layer)

---

## 1. Purpose & Core Philosophy

Build the first layer whose primary object is a **functional connection (mechanism joint)**, not an identity assertion or textbook declaration.

Identity edges (`SAME_SEMANTICS`, `SCOPED_OVERLAP`, `RELATED_TO`) stay, but they are insufficient to capture mathematical structure across domains. The map exists to surface joints that textbooks keep in separate chapters — the Perelman pattern:
- an evolution flow ($\partial_t g = -2\operatorname{Rc}(g)$),
- a monotone functional ($\mathcal{W}$-entropy),
- a singularity blow-up model ($\mathbb{S}^2 \times \mathbb{R}$ cylinder),
- a surgery rule, and
- a reduced volume comparison

These are **related by mechanism, never by identity**.

In this architecture:
- `EO`, `GEO`, `PCT`, and `FORMAL` become **executable view slots on a canonical object** and **witnesses on a joint**.
- Source provenance (`NATURAL`) is kept **formally outside the executable view registry** as primary declaration identity and provenance metadata.

---

## 2. Explicit Non-Goals

1. **No new source corpus ingestion** in this phase.
2. **No auto-promotion** of PCT signatures, Betti equality, or detector hits to `SAME_SEMANTICS`.
3. **No claim** that Mathlib lemmas reconstruct original source textbook proofs.
4. **No Ricci-flow paper ingestion** until the joint grammar and one non-toy dual certificate (Stokes) exist.
5. **No rewrite** of sealed graphs or historical evidence records.

---

## 3. Integrity Invariants (Inherited + New)

- **I1 (Declaration Identity)**: Corpus + kind + number + lowercase SHA-256 of statement bytes.
- **I2 (View vs Identity Disjointness)**: Executable view states (`ABSENT | CANDIDATE | CERTIFIED(scope)`) are strictly distinct from identity states.
- **I3 (Formal Kernel Distinction)**: `FORMAL_LINKED ≠ KERNEL_VERIFIED`. Kernel verification requires an independent `#print axioms` checker record without `sorry`, `admit`, or custom axioms.
- **I4 (Joint vs Identity Separation)**: A joint edge cannot be an identity edge. Mechanism $\neq$ Sameness. A joint must **never** directly emit `SAME_SEMANTICS` or `SCOPED_OVERLAP`.
- **I5 (Topological Non-Promotion)**: Equal Euler characteristic, Betti numbers, persistence pairing, or reconstruction signature must never emit `SAME_SEMANTICS`.
- **I6 (Finite Evidence Scoping)**: Finite executable evidence is scoped and never implies a universal theorem.
- **I7 (Wound Preservation)**: Wounds stay visible. Joints may point at wounds; they may not hide them.
- **I8 (Grounding Invariant)**: Proof-eligible grounding requires a closed endpoint-bound evidence registry. Joints do not alter the `0 / 235` proof-eligible object count.
- **I9 (Certificate Quorum Invariant)**: `CERTIFIED` status on a correspondence certificate requires at least **two independent, countable witnesses** (`EO`, `GEO`, `PCT` at B4+, `FORMAL` only when `KERNEL_VERIFIED`). `NATURAL` and `FORMAL_LINKED` do not count toward the quorum.
- **I10 (Anti-Alias Invariant)**: Duplicate witness digests, shared-producer aliases, and same-payload derivatives are rejected during certificate evaluation.

---

## 4. Layer Architecture & Models

```
Source declaration ──► Canonical object M
                         ├── identity: {corpus, kind, number, statement_sha256}
                         └── views (4 executable slots):
                               ├── eo:     ABSENT | CANDIDATE | CERTIFIED(scope)
                               ├── geo:    ABSENT | CANDIDATE | CERTIFIED(scope)
                               ├── pct:    ABSENT | INAPPLICABLE | CANDIDATE | CERTIFIED(scope)
                               └── formal: ABSENT | FORMAL_LINKED | KERNEL_VERIFIED(scope)

Joint J (first-class mechanism connection node, NOT an identity edge)
  ├── joint_id: str
  ├── joint_type ∈ {ACTS_ON, LINEARIZATION_OF, MONOTONE_ALONG, OBSTRUCTION_TO,
  │                 BLOWS_UP_AS, SURGERY_OF, NERVE_OF, CHAIN_OF,
  │                 COMPARISON_MODEL, SCOPED_TRANSFER, CONTRACTION_OF}
  ├── feet: ordered role-labelled endpoint refs:
  │     [{"role": "functional", "object_id": "...", "statement_hash": "..."},
  │      {"role": "flow",       "object_id": "...", "statement_hash": "..."}]
  ├── scope: TypedScopeRecord (domain, dim, ring, regularity, orientation, boundary)
  ├── witnesses: {eo?, geo?, pct?, formal?}
  ├── forbidden_promotions: ["SAME_SEMANTICS", "SCOPED_OVERLAP"]
  └── status: CANDIDATE | WOUND | CERTIFIED(scope)
```

---

## 5. Closed Joint Type Registry

| Type | Arity | Semantic Role | Role Labels for Feet | Legal Identity Promotion |
|---|---|---|---|---|
| `ACTS_ON` | 2 | Operator / flow acts on metric or state space | `generator`, `target_space` | **None** |
| `LINEARIZATION_OF` | 2 | Linearized operator of a nonlinear evolution | `linear_operator`, `nonlinear_system` | **None** |
| `CONTRACTION_OF` | 2 | Metric / tensor trace contraction | `contracted_tensor`, `full_tensor` | **None** |
| `MONOTONE_ALONG` | 2–3 | Functional monotone along evolution trajectory | `functional`, `evolution_flow`, `direction` | **None** |
| `OBSTRUCTION_TO` | 2 | Quantity blocking extension or smoothness | `obstruction`, `target_structure` | **None** |
| `BLOWS_UP_AS` | 2–3 | Singularity model and rescaling limit | `singularity_model`, `rescaled_flow` | **None** |
| `SURGERY_OF` | 3+ | Topological cut, discard, and replacement cap | `target_neck`, `cut_interface`, `replacement_cap` | **None** |
| `NERVE_OF` | 2 | PCT simplicial complex as nerve of open cover | `nerve_complex`, `open_cover` | **None** |
| `CHAIN_OF` | 2 | Discrete simplicial chain complex stand-in of $M$ | `chain_complex`, `continuous_manifold` | **None** |
| `COMPARISON_MODEL` | 2 | Soliton / space form comparison geometry | `comparison_geometry`, `ambient_flow` | **None** |
| `SCOPED_TRANSFER` | 2+ | Mathematical property transferred across functor | `source_domain`, `target_domain`, `functor` | Evaluator may emit `SCOPED_OVERLAP` only after independent cert validation; **never `SAME_SEMANTICS`** |

---

## 6. Typed Scope Specification & Deterministic Comparison

Free-text scope matching is replaced by a structured schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TypedScopeRecord",
  "type": "object",
  "required": [
    "domain",
    "dimension",
    "coefficient_ring",
    "regularity",
    "orientation_convention",
    "boundary_convention"
  ],
  "properties": {
    "domain": {
      "type": "string",
      "enum": ["SMOOTH_MANIFOLDS", "SIMPLICIAL_COMPLEXES", "EUCLIDEAN_SPACES", "METRIC_SPACES", "RIEMANNIAN_MANIFOLDS"]
    },
    "dimension": {
      "type": "array",
      "items": { "type": "integer" }
    },
    "coefficient_ring": {
      "type": "string",
      "enum": ["Z", "Q", "R", "C"]
    },
    "regularity": {
      "type": "string",
      "enum": ["C_INFINITY", "C_K", "PIECEWISE_LINEAR", "DISCRETE"]
    },
    "orientation_convention": {
      "type": "string",
      "enum": ["STANDARD_SIMPLEX", "INDUCED_BOUNDARY_OUTWARD_NORMAL", "NONE"]
    },
    "boundary_convention": {
      "type": "string",
      "enum": ["SIMPLICIAL_CHAIN", "SMOOTH_SUBMANIFOLD", "EMPTY"]
    },
    "parameter_range": {
      "type": "object",
      "properties": {
        "t_min": { "type": ["number", "string"] },
        "t_max": { "type": ["number", "string"] }
      }
    },
    "exceptional_cases": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

A deterministic comparator `ScopeComparator.are_compatible(scope_a, scope_b)` evaluates:
1. `dimension` overlap (non-empty intersection).
2. `coefficient_ring` sub-ring inclusion (e.g. $\mathbb{Z} \subseteq \mathbb{Q} \subseteq \mathbb{R}$).
3. Matching `orientation_convention` and `boundary_convention`.
4. Disjointness of declared `exceptional_cases`.

---

## 7. Dual-Prover Correspondence Certificate

```
CorrespondenceCertificate
  ├── id: str
  ├── subject_ids: list[str]
  ├── subject_hashes: list[str]
  ├── scope: TypedScopeRecord
  ├── witnesses:
  │     ├── eo_witness:     ContractDigest | null
  │     ├── geo_witness:    ContractDigest | null
  │     ├── pct_witness:    {b_level: "B4"|"B5", complex_digest: "...", applicability: "CANDIDATE"|"CERTIFIED"} | null
  │     └── formal_witness: {lean_decl: "...", kernel_verified: bool, axiom_record: [...]} | null
  ├── nonclaims: list[str]  # Non-empty list of what is NOT claimed
  ├── status: CANDIDATE | CERTIFIED | REJECTED
  └── evidence_digest: str  # SHA-256 over canonical JSON representation
```

### Strict Quorum & Promotion Rules
- `CERTIFIED` strictly requires **$\ge 2$ independent, countable witnesses**:
  1. `EO` witness
  2. `GEO` witness
  3. `PCT` witness with $B \ge \text{B4}$
  4. `FORMAL` witness with `kernel_verified = true` and 0 unapproved axioms
- Merely `FORMAL_LINKED` or `NATURAL` source citations **do not count** toward the quorum.
- Duplicate digests, shared-producer aliases, and same-fixture derivatives are rejected.
- Non-empty `nonclaims` required.

---

## 8. Worked Packages

### Package S: Stokes Correspondence Dual Certificate (First Accepted Certificate)
- **Mathematical Object**: Discrete/simplicial Stokes on oriented $n$-simplices ($n \in \{1, 2\}$) over $\mathbb{Q}$.
- **EO View**: Discrete exterior derivative matrix $D$ on cochains; pairing $\langle d\alpha, \sigma \rangle = \langle \alpha, \partial\sigma \rangle$.
- **GEO View**: Oriented Euclidean simplex with standard simplicial orientation and piecewise-linear boundary.
- **PCT View**: B4 chain complex $(C_n, \partial_n)$ with B5 boundary-commuting chain map ($\partial^2 = 0$, $d^2 = 0$, $B = D^T$).
- **Formal View**: `ABSENT` (unless real Mathlib theorem bound in Task 4).
- **Nonclaims**:
  - Does NOT claim smooth de Rham theorem on general smooth manifolds.
  - Does NOT claim Stokes theorem for general geometric measure currents.
  - Does NOT claim text-reconstruction proof of full Gallier/Lebl chapters.

### Package P: Perelman Mechanism Grammar Suite (Falsification & Candidate Suite)
Six pre-registered candidate mechanism joints (all `status = CANDIDATE`, 0 identity edges):
1. **Contraction Joint**: Riemann curvature $\xrightarrow{\text{CONTRACTION\_OF}}$ Ricci curvature ($R_{ij} = g^{kl} R_{klij}$).
2. **Evolution Joint**: Ricci flow $\xrightarrow{\text{ACTS\_ON}}$ Riemannian metric ($\partial_t g = -2\operatorname{Rc}(g)$).
3. **Entropy Monotonicity**: Perelman $\mathcal{W}$-entropy $\xrightarrow{\text{MONOTONE\_ALONG}}$ Ricci flow ($\frac{d}{dt}\mathcal{W} \ge 0$).
4. **Singularity Model**: Neck pinch $\xrightarrow{\text{BLOWS\_UP\_AS}}$ shrinking cylinder ($\mathbb{S}^2 \times \mathbb{R}$).
5. **Topological Surgery**: Surgery operation $\xrightarrow{\text{SURGERY\_OF}}$ neck region (cut $S^2 \times [-1, 1]$, glue standard caps $D^3$).
6. **Volume Monotonicity**: Reduced volume $\tilde{V}(\tau) \xrightarrow{\text{MONOTONE\_ALONG}}$ backward Ricci flow ($\frac{d}{d\tau}\tilde{V} \le 0$).

---

## 9. Preregistered Horn Query

```
horn(M) :=
  betweenness_centrality(M, projection="active_cross_corpus") >= tau_b (0.05)
  AND view_shear(M) >= tau_s (0.50)
  AND has_valid_dual_certificate(M) == false
```

- **Graph Projection**: Active in-memory graph (v0.20 identity projection + v0.21 joints).
- **Betweenness**: Undirected Brandes betweenness normalized by $(N-1)(N-2)/2$.
- **Shear Formula**: $\operatorname{shear}(u) = \frac{|\operatorname{views}(u)_{\text{present}} \setminus \operatorname{views}(u)_{\text{certified}}|}{|\operatorname{views}(u)_{\text{present}}| + 1}$.
- **Null Calibration**: 100 degree-sequence preserving randomized rewiring iterations.
- **Output**: Written exclusively to `evidence/v0_21_horn_report.json` (strictly evidence-only, 0 graph modifications).
