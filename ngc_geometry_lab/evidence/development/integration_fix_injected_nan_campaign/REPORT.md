# NGC / MAPEOGEO geometric reconstruction qualification

**Result: FAIL — 11/12 computational gates passed.**
Master seed: `20261022`. All observations in this campaign are synthetic. Computation uses CPU arithmetic.

| Gate | Result | Criterion |
|---|---|---|
| source_integrity | PASS | All selected source bytes match SHA256 and Git blob SHA1 provenance. |
| connected_operators | PASS | Actual connected operators agree with independent calculations; all unexpected upstream failures are absent; known bad expectation remains visible. |
| exact_closure | PASS | New explicit integer generator fixture: 115 elements, all 13225 products and 1520875 associativity triples verified. |
| metric_and_center | PASS | Recover declared metric and center, classify insufficient/contradictory/numerically unresolved controls correctly. |
| tetra_reconstruction | PASS | 256 independent pure/mixed preparations reconstruct; tetrahedral frame identities and physical-state rejection hold within absolute 1e-10. |
| heldout_rotations | PASS | 3072 held-out rotation predictions agree within absolute 1e-10; a mismatched label/operator frame fails visibly. |
| dual_lane_equivalence | FAIL | Actual real dual-lane backend agrees with independent complex tensor reference for >=1000 local gates, absolute tolerance 1e-10. |
| finite_shot_prediction | PASS | Frozen calibration; mean held-out Bloch error <0.035 and improves over uncorrected detector counts. |
| readout_selection | PASS | Synthetic squared-rule data selects exponent2 from1,2,4; crossed projections give0 and inserted diagonal gives1/4. |
| joint_reconstruction | PASS | 128 two-system states and1024 local-rotation sequences agree with independent density matrices, absolute1e-10. |
| correlation_controls | PASS | Computed singlet CHSH=2sqrt(2), all16 local assignments bounded by2; equal marginals do not fix joints; invalid quantum state rejected. |
| identifiability | PASS | Duplicate/mirrored views add no missing rank; operation sequence restores rank and distinguishes initially equal outputs. |

## Failures are retained

Read `results.json`, stage checkpoints, and any exception files. A failed campaign is not replaced with a success summary.

The complete source and input records remain available for investigation.
