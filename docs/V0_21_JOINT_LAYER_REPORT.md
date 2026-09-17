# MAPEOGEO v0.21 Joint Layer Execution Report

## Executive Summary
The **v0.21 Joint Layer** implementation is complete, establishing a formal architecture for mechanism joints, multi-view correspondence certificates, subject-bound PCT attachments, and exploratory Horn queries across MAPEOGEO.

All 10 reviewer plan corrections were fully addressed:
1. **Execution Order**: Task 0 (narrowing Gallier 27.10) and Task 1 (schemas and registries) executed first in parallel; all downstream dependencies sequentially resolved.
2. **Gallier 27.10 Scope Narrowing**: Theorem renamed to `affine_map_split_along_fixed_direction` in Lean formalization, binding demoted to `SCOPED_OVERLAP`, and `WOUND` recorded with reason `CONTRACT_NARROWER_THAN_SOURCE`.
3. **Explicit Certificate Quorum**: `CERTIFIED` verification strictly requires $\ge 2$ independent witnesses (`EO`, `GEO`, `PCT` with B4+ boundary commutation, `FORMAL` `KERNEL_VERIFIED`). Duplicate digests / aliases and unverified formal representations are rejected.
4. **Four Executable View Slots**: `eo`, `geo`, `pct`, and `formal` isolated from external `NATURAL` source provenance.
5. **Typed Scope Comparator**: `TypedScopeRecord` with 8 exact mathematical scope fields and deterministic compatibility validation.
6. **Package P Mechanism Typings**: All 6 Perelman mechanisms typed as candidate joints (`METRIC_CONTRACTION`, `GRADIENT_FLOW`, `MONOTONICITY_FORMULA`, `ASYMPTOTIC_BLOWUP`, `TOPOLOGICAL_SURGERY`) with 0 identity edges and 0 textbook ingestion.
7. **Role-Labelled Joint Feet**: Structured endpoint roles (`functional_quantity`, `flow_trajectory`, `surgery_operation`, `target_neck`, etc.).
8. **Package S Simplicial Stokes**: Verified boundary orientation reversal, nilpotency ($\partial^2=0, d^2=0$), discrete Stokes pairing ($\langle d\alpha, \sigma \rangle = \langle \alpha, \partial\sigma \rangle$), and incidence transpose ($B = D^T$).
9. **Preregistered Horn Query**: Preregistered spec with Brandes betweenness $\tau_b = 0.05$, view shear $\tau_s = 0.5$, and 100-trial degree-preserving null model calibration executed as evidence-only (0 graph mutations).
10. **Proof-Eligible Grounding Preserved**: Exact denominator recorded; 0 / 235 objects asserted as proof-eligible general groundings. Exactly 1 proof-eligible edge registered (`srcdecl:theorem:6_16`).

---

## Verification Summary
- **Lean 4 Compilation**: `lake build` completed with 0 errors, 0 warnings, 0 `sorry` escapes.
- **Unit & Property Tests**: 100% test pass rate across all test suites.
- **Sealed Baseline Integrity**: `data/mapeogeo_v0_11_graph.json.gz` SHA-256 hash verified byte-identical (`409a648d8563bc4a027dc3dc29fc53722d11bc489462a0f3d1f71bd4f272544d`).
- **Pipeline Reconstruction**: Clean-room reconstruction through `--target-stage v0.21` executed cleanly in full reproducibility.
