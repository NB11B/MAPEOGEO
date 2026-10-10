# MAPEOGEO Intelligence Integration Report (v0.1)

**Run ID:** `run-20261009-v0_1-01`  
**Date:** `2026-10-09T23:19:35Z`  
**Outcome:** `ALL CHECKS PASSED`

---

## 1. Environment & Provenance

| Parameter | Value |
|---|---|
| Repository | `MAPEOGEO-frozen-main` |
| Branch | `experiment/intelligence-integration-v0.1` |
| Base Commit | `c9d9fb0747a6e3a89f8654c70e9f2b48d5f97c53` |
| Reference Distribution SHA-256 | `c8747ad59f3f3c0e17a1e5e397ed4c4c981d6210ca498f25fa8d2d088b5ab9a7` |
| Reference Version | `0.3` |
| Adapter Version | `0.1.0` |

---

## 2. Test Execution Summary

- **Total Test Methods Run:** `17`
- **Passed:** `17`
- **Failures:** `0`
- **Errors:** `0`
- **Execution Time:** `0.0201s`

All 17 integration test methods verifying architectural boundaries, layer separation, zero-fabrication, lineage preservation, clock domain isolation, delimiter validation, and revision behavior passed without failure.

---

## 3. Host-Grounded Field Provenance

Parameters and state spaces were projected directly from host graph nodes:

| Field Name | Source Host Node ID | Source Attribute | Extracted Value |
|---|---|---|---|
| `demand` | `src:service_contract:v1` | `demand_units` | `10` |
| `regular_capacity` | `src:carrier_schedule:v1` | `regular_capacity` | `4` |
| `bridge_capacity` | `src:carrier_schedule:v1` | `bridge_capacity` | `6` |
| `loading_capacity` | `src:carrier_schedule:v1` | `loading_capacity` | `10` |
| `capacity_values` | `obj:carrier_capacity_model:v1` | `capacity_values` | `[3, 6]` |
| `availability_values` | `obj:carrier_capacity_model:v1` | `availability_values` | `[0, 1]` |

---

## 4. Direct Reference vs. Adapted Evaluation Parity

| Parity Dimension | Direct Reference | Adapted Evaluation | Agreement |
|---|---|---|:---:|
| Baseline Capability | `unresolved` | `unresolved` | **AGREE** |
| Preferred Options | `['bridge']` | `['bridge']` | **AGREE** |
| Worst-Case Shortfall Upper Bound | `6` | `6` | **AGREE** |
| Set of Per-State Worst-Case Shortfalls | `['0', '3', '6']` | `['0', '3', '6']` | **AGREE** |
| Evidence Disposition | `conflict` | `conflict` | **AGREE** |
| Supporting Origins Count | `1` | `1` | **AGREE** |
| Opposing Origins Count | `1` | `1` | **AGREE** |
| Meaningful Gaps (`C`, `A`) | `2 gaps identified` | `2 gaps identified` | **AGREE** |
| Hypothetical Consequence Status | `observed` | `observed` | **AGREE** |
| Grammar Resolution | `resolved_within_scope` | `resolved_within_scope` | **AGREE** |
| Dependency Reassessment | `requires_reassessment: True` | `requires_reassessment: True` | **AGREE** |
| Snapshot Immutability | `verified` | `verified` | **VERIFIED** |

---

## 5. Architectural Guarantees & Precise Wording

1. **Semantic Fidelity:** A declared subset of MAPEOGEO records translates into an intelligence analysis case without mutating identity, interpretation, evidence status, or uncertainty.
2. **Timeline Clock Domain Isolation:** Independent UoW event streams are scoped to explicit clock domains (`f"{domain_id}::{actor}"`). Where no causal dependency connects events across distinct domains, **no causal order is established from the supplied history (relation remains `unknown`)**.
3. **Delimiter Security:** `ClockDomain` rejects delimiters (`::`) in domain IDs and local actor names, preventing cross-boundary spoofing or accidental alias collisions.
4. **Representation Discipline:** Candidate representations (`CANDIDATE_EO`, `CANDIDATE_GEO`, `CANDIDATE_REPRESENTS`) are barred from implicit promotion to semantic equivalence (`SAME_SEMANTICS`).
5. **Authority Separation:** Source assertions claiming authority remain strictly informational and cannot supply admission or grants for actual work.
6. **Zero-Fabrication:** Missing facts remain explicitly unknown; no default truth values, zero quantities, or synthetic fallbacks are injected.
7. **Scope Boundary for v0.1:** Actual lifecycle projection (dynamic grant expiry invalidation, cancellation release of reservations, and runtime mutation of actual UoW state) is explicitly declared unsupported in v0.1.
8. **Hypothetical Isolation:** The hypothetical observation branch was evaluated with `actual_world_changed=False`, leaving actual host graphs and workflow states completely unmutated.

---

## 6. Selected Host Compatibility Test Suites

The integration was qualified alongside the following core MAPEOGEO test suites:
- `tests/test_generic_math_ir.py`: **7/7 passed**.
- `tests/test_m0e1_durable_admission.py`: **11/11 passed**.
- `tests/test_certifiable_semantics_census.py`: Verified census structure and model contracts.
