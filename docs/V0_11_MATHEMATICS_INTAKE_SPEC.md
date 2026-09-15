# MAPEOGEO v0.11 Specification: Pinch-Driven Mathematics Intake

## 1. Governing Objective

MAPEOGEO v0.11 executes the first deliberate mathematics-growth stage following the accepted v0.9 S5 proof-path milestone. The core governing principle is:

$$\boxed{\text{coverage changes; architecture does not}}$$

v0.11 ingests the high-value interface quartet selected deterministically by the v0.9 pinch audit:
1. **Proposition 3.14** (`srcdecl:proposition:3_14`) — Unique coordinate representation with respect to a basis.
2. **Proposition 3.13** (`srcdecl:proposition:3_13`) — Linear independence characterization via submodule spans.
3. **Theorem 27.10** (`srcdecl:theorem:27_10`) — Canonical affine isometry decomposition / spectral theorem control.
4. **Proposition 4.4** (`srcdecl:proposition:4_4`) — Subspace direct sum disjoint kernel criterion.

## 2. Intake Invariants

1. **Identity**: Every target is anchored by its source locator and frozen statement SHA-256 hash.
2. **Explicit Dependencies**: Only citations appearing in the source text become `DEPENDS_ON` edges. No inferred or synthetic dependency edges are fabricated.
3. **Historical View Immutability**: Historical detector states (`EO_ONLY_DIRECT`, `DUAL_DIRECT`) are immutable facts of provenance. Lean proofs do not silently manufacture GEO views.
4. **Explicit Test States**: Every target carries an explicit test state (`EXECUTABLE_CONTRACT`, `PCT_CONTRACT`, or `UNTESTED`).
5. **No Kernel Replacement**: Executable tests cannot create `KERNEL_VERIFIED`. Only the pinned Lean 4 kernel may issue kernel verification.

## 3. Claim Boundary

v0.11 measures whether graph-selected interface nodes can be promoted through scoped executable and formal verification without manufacturing missing structure. It does not claim universal autoformalization, automatic proof synthesis, or replacement of Lean by computational evidence.
