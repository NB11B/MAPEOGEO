# E25D–E25F Closure-Depth Verification Design

**Date:** 2026-09-15  
**Branch:** `agent/pct-computational-architecture`  
**Status:** Approved design, frozen before implementation

## Purpose

E25B and E25C established two different forms of redundancy in MAPEOGEO:

1. path-level identity/certificate consistency; and
2. executable agreement for four source-bound EO/GEO/FORMAL cycles.

The next stage turns those results into a governed verification program. The system must answer, for each real semantic trust component:

- what closure evidence is actually established;
- what evidence is applicable but missing;
- what evidence is not applicable;
- what failure, if any, blocks advancement; and
- what the next legitimate verification action is.

This stage does **not** create an opaque trust score and does **not** automatically promote graph semantics.

## Important provenance correction

The current `evidence/pct_e25b_trust_projection.json` contains four real source-bound cycles plus twenty **synthetic equivalence triangles** used to reconstruct/calibrate the E25B topology after the full source artifact could not be persisted reliably through the connector path.

Therefore:

- the four source-bound cycles are real MAPEOGEO evidence;
- the twenty synthetic triangles are calibration fixtures only;
- synthetic fixtures must never be counted as real repository closure coverage; and
- E25D must distinguish `REAL_SOURCE_BOUND` from `SYNTHETIC_CONTROL` explicitly.

The production closure atlas will only assign repository closure states from real, source-bound evidence. Synthetic components may appear only in fault-coverage/calibration outputs.

This correction supersedes any interpretation of the E25B count of 24 components as 24 independently sourced real MAPEOGEO semantic components.

## Governing model: closure vector, not scalar confidence

Each real semantic component receives a closure vector:

- **C0 — Identity closure:** endpoint existence, one semantic/source anchor, consistent source hash/identity, no cross-object collapse.
- **C1 — Certificate closure:** C0 plus valid referenced executable/kernel certificates and valid scope/provenance metadata for the semantic edges being claimed.
- **C2 — Executable contract closure:** C1 plus independent executable EO/GEO/FORMAL adapters evaluated on the declared contract domain, with all required paths agreeing.
- **C3 — Chain-map closure:** where applicable, exact `d_Y F = F d_X` verification for explicit chain maps.
- **C4 — Induced-homology closure:** where applicable, the induced action on homology satisfies the declared semantic contract.
- **C5 — Exact morphism/provenance closure:** where required, exact map identity/provenance agrees with the declared correspondence, beyond homology-level equivalence.

Allowed per-level states are:

`PASS`, `FAIL`, `NOT_APPLICABLE`, `NOT_ESTABLISHED`, `INVALID`, `ERROR`.

A component also records an `applicability_mask`, an `evidence_refs` map, and a `closure_frontier`. `closure_frontier` is the highest established point before the next applicable but unestablished/failed level. `NOT_APPLICABLE` never silently counts as a pass.

Example:

```text
C0 PASS
C1 PASS
C2 PASS
C3 NOT_APPLICABLE
C4 NOT_APPLICABLE
C5 NOT_ESTABLISHED
closure_frontier = C2
```

The hierarchy is therefore inspectable without pretending that every mathematical object must support every layer.

# E25D — Closure Depth Atlas

## Inputs

E25D is bound to the audited v0.9 source artifact:

- commit `9420f19953f56198630f86eb25fa5d6eb0828ea7`
- workflow run `34933361147`
- artifact id `10382242654`
- artifact digest `sha256:d487602dd3c0b3a3c5302edde108758eda2b11975f5e0c2c4e659db63da2aabc`

The implementation must provide a deterministic source-bound component manifest. No missing real component may be replaced by a generated synthetic one.

## Component record

Each atlas entry contains at least:

```text
component_id
provenance_class: REAL_SOURCE_BOUND | SYNTHETIC_CONTROL
source_artifact_digest
anchor_ids
representation_ids
formal_ids
semantic_edge_ids
source_statement_hashes
closure.C0 ... closure.C5
applicability_mask
evidence_refs
closure_frontier
blocking_gap
```

## Assignment rules

C0 and C1 are recomputed from persisted evidence rather than copied from prior verdict text.

C2 may be `PASS` only when an executable adapter is bound to the same source identity, contract name, and formal scope and the preregistered comparison passes. The four E25C cycles are expected to meet this condition, but the implementation must compute the result rather than hard-code it.

C3/C4 are only applicable when explicit chain-complex/map semantics are part of the contract. Scalar rank/convexity/LP/Gaussian adapters do not become chain tests merely to increase depth.

C5 is `PASS` only when an exact morphism/provenance contract is explicitly represented and verified. C2 success cannot imply C5.

## E25D acceptance

E25D passes when:

1. every real source-bound component in the frozen manifest receives a complete C0–C5 vector;
2. no synthetic calibration component is reported as real closure coverage;
3. every `PASS` has an evidence reference;
4. every `NOT_APPLICABLE` has an explicit applicability reason;
5. every `NOT_ESTABLISHED` has a specific missing-evidence reason; and
6. fresh execution reproduces the frozen atlas exactly.

# E25E — Verification Upgrade Planner

## Purpose

E25E converts the atlas into a deterministic work queue. It does not assign a probabilistic or weighted trust score.

Each real component receives one next-action classification based on the first unresolved applicable requirement.

## Priority classes

Priority is lexicographic, not a blended score:

1. **P0 — CONFLICT_REMEDIATION**: any `FAIL`, `INVALID`, or identity/certificate contradiction.
2. **P1 — EXECUTABLE_ADAPTER_READY**: C0/C1 pass, a declared executable contract exists, but C2 is not established.
3. **P2 — EVIDENCE_SERIALIZATION_GAP**: evidence is known to exist but is not bound/serialized strongly enough for the next closure check.
4. **P3 — CHAIN_OR_HOMOLOGY_MODEL_REQUIRED**: C3/C4 are applicable but the required chain/homology representation has not been built.
5. **P4 — EXACT_MORPHISM_PROVENANCE_REQUIRED**: C5 is applicable but exact map/provenance evidence is missing.
6. **P5 — FORMALIZATION_OR_SCOPE_REQUIRED**: the next executable comparison cannot be defined without a stronger formal statement/scope.
7. **NO_ACTION — NOT_APPLICABLE_OR_COMPLETE**: no legitimate next closure action exists under the declared contract.

Ties are broken deterministically by stable component id. The planner must explain `why_now`, `blocking_gap`, `required_inputs`, and `expected_next_level`.

## E25E acceptance

E25E passes when every real component is placed in exactly one priority class, all recommendations can be derived from E25D evidence, repeated execution is byte-stable, and no recommendation proposes semantic promotion merely because a lower layer passed.

# E25F — Layered Fault-Coverage Matrix

## Purpose

E25F measures what each closure layer can detect and verifies that the layers are complementary rather than redundant labels.

Synthetic controls are appropriate here, but must be labeled `SYNTHETIC_CONTROL` and never counted as real graph failures.

## Required fault classes

The matrix must include at least one fault whose first capable detector is each layer:

| Fault | Expected first capable layer |
|---|---|
| source/anchor swap or hash identity mismatch | C0 |
| certificate failure/missing or invalid certificate binding | C1 |
| wrong executable EO/GEO/FORMAL result with metadata unchanged | C2 |
| explicit chain-map corruption producing nonzero `dF-Fd` | C3 |
| zero-chain-residual map with wrong induced homology action/degree | C4 |
| homology-equivalent but wrong exact map/provenance correspondence | C5 |

C3–C5 controls reuse the exact correspondence lessons from E5: ordinary chain-map corruption, cycle injection that preserves `dF=Fd` but changes degree, and same-homology correspondence changes that require exact provenance.

## First-capable-layer rule

For each injected fault, E25F executes layers in order and records:

```text
fault_id
provenance_class = SYNTHETIC_CONTROL
expected_first_detector
observed_first_detector
layer_results C0..C5
false_positive_before_expected
missed_at_expected
```

A later layer detecting a fault does not compensate for an earlier expected layer missing it.

## E25F acceptance

E25F passes when every required fault class is detected first at its preregistered layer, no earlier layer produces an unintended false positive, and controls remain fail-closed when a layer is not applicable.

# Architecture and files

The implementation should extend the existing experimental surface rather than the production ontology:

```text
experiments/pct_e25def/
    __init__.py
    atlas.py
    planner.py
    fault_matrix.py
    test_e25def.py

evidence/
    pct_e25d_real_component_manifest.json
    pct_e25d_closure_atlas.json
    pct_e25e_upgrade_plan.json
    pct_e25f_fault_coverage.json

docs/
    PCT_E25D_E25F_CLOSURE_PROGRAM_REPORT.md
```

The existing PCT campaign CI workflow will be extended to compile and run this suite. No `main`-branch merge, README claim promotion, or core EO/GEO/FORMAL semantic mutation is part of this stage.

# Data flow

```text
Audited source-bound evidence
        |
        v
Real component manifest
        |
        v
E25D closure-vector evaluator
        |
        +--> frozen closure atlas
        |
        v
E25E deterministic gap classifier
        |
        +--> upgrade work queue

Synthetic layer-specific controls
        |
        v
E25F C0-C5 fault matrix
```

Real evidence and synthetic calibration data remain separate at every step.

# Fail-closed rules

1. Missing evidence yields `NOT_ESTABLISHED`, never inferred `PASS`.
2. Failed applicability preconditions yield `NOT_APPLICABLE`, not theorem failure.
3. Identity inconsistency blocks evaluation of higher layers.
4. Certificate inconsistency blocks C2+ promotion.
5. C2 cannot imply C3, C4, or C5.
6. A synthetic fixture can validate machinery but can never raise the closure level of a real MAPEOGEO component.
7. Historical E25B aggregate topology is retained as calibration evidence but is not used as proof that twenty synthetic reconstructed components were real repository components.

# Scientific / engineering outputs

The principal output is not a claim that MAPEOGEO is universally self-verifying. It is a reproducible map of **where** the current graph has independent verification closure, **which kind** of closure it has, **what is missing**, and **which layer catches which failure class**.

The intended project-level consequence is:

```text
Graph growth asks: what mathematical relations have we represented?
Closure depth asks: how independently and at what semantic level can those relations be checked?
Upgrade planning asks: what is the next legitimate verification action?
```

# Claim boundary

A passing E25D–E25F stage establishes a closure-accounting and verification-prioritization architecture on the frozen audited component set and synthetic layer controls. It does not establish universal mathematical truth, whole-repository executable commutativity, automatic proof, or permission to promote graph semantics without the existing formal/evidence contracts.
