# E32: Typed parallel decision graph engineering specification

Status: DESIGN_ONLY / NOT_EXECUTED. Specification version: 1.2.
Date: 2026-09-17.
Repository: NB11B/MAPEOGEO.
Approved base: 4418df2293cf3e27a5b7d4460a7ecd2ec4fc3acd.
Branch: agent/e32-typed-parallel-decision-graph-spec.

## Purpose

E32 tests a specific architectural hypothesis inspired by the public TypeSafe/Jev programming model without assuming or reproducing unpublished vendor internals: a decision can often be represented as typed atomic judgments over shared immutable state, composed deterministically in code, so executable width becomes cheaper than true dependency depth.

The campaign separates four contributions that must not be conflated:

1. decision factorization into typed atomic judgments;
2. ordinary scheduling of an already exposed dependency graph;
3. graph rewrites such as speculative fan-out and deterministic deduplication;
4. backend effects such as batching, shared-state reuse, teacher-forced option scoring and direct typed readout.

The central E32 question is therefore not merely whether a scheduler can run a DAG faster. It is whether a serial decision formulation can be transformed into a semantically admissible typed decision graph that exposes useful parallelism, and whether MAPEOGEO contributes to discovering that factorization rather than merely scheduling it.

Version 1.2 distinguishes two scopes of model interaction that must not be conflated. Independent sibling questions are isolated computations over declared shared state and are tested for cross-question invariance. The alternatives inside one CHOICE or SCORE are instead an ordered listwise decision object: changing the option order or set creates a new query contract and is measured for sensitivity rather than incorrectly required to preserve probabilities.

This specification also separates local-model backend mechanisms. B0/B1 use teacher-forced answer-string scoring, B2 adds measured shared-state/prefix reuse, and optional B3 uses a sealed direct typed readout from declared hidden-state/logit locations without answer-string scoring. B3 is an experiment in non-generative typed readout, not a claim to reconstruct Jev. Decision-specialized post-training/calibration is B4 and remains outside the v1.2 primary campaign.

Confidence is deterministic post-processing rather than another model judgment. NOUL has no separate normative confidence; CHOICE may use the sealed uniform-baseline concentration formula; SCORE requires an explicitly registered metric. Confidence does not authorize primary actions.

This commit series adds documentation only. It does not implement a compiler, supply frozen benchmark data or model weights, run experiments, certify claims, or change existing evidence. Commands in LOCAL_EXECUTION.md are future implementation requirements unless explicitly marked available now.

## Reading order

1. [ARCHITECTURE.md](ARCHITECTURE.md): factorization model, question/listwise semantics, backend levels, legal rewrites and integration boundaries.
2. [CONTRACTS.md](CONTRACTS.md): normative record schemas, confidence/readout contracts, invariants and interfaces.
3. [PREREGISTRATION.md](PREREGISTRATION.md): campaign matrix, isolation/option probes, controls, gates and conclusions.
4. [LOCAL_EXECUTION.md](LOCAL_EXECUTION.md): CPU/GPU setup, future command contract, backend tests and artifact inspection.

The schemas are language-neutral normative specifications, not executable JSON Schema files. Implementation must supply validators and rejection tests before production behavior.

## Source anchors and integration constraints

The pinned base contains experiments/pct_goal_solver/model.py, planner.py, operators.py, canonical.py and lineage.py. Its model exposes ArtifactType, InputPort, SolverVisibleGoal, GoalSpec.solver_visible(), DerivationStep, SolveTrace, and VerificationResult. These provide integration seams, not an existing E32 compiler.

Preserve the sealed/solver-visible split. Never pass sealed_expected_result or sealed_reference_path to factorization, planning, compilation, inference, readout selection or cost fitting. Existing registry digests and lineage obligations remain authoritative. A parallel trace is not permitted to bypass existing terminal verification or rewrite an ordered lineage obligation.

Future implementation belongs in experiments/typed_parallel_decision_graph/ with tests in that directory. The E32 adapter may read existing solver types and contracts but must not mutate their semantics or import test-only oracle helpers into runtime code. Record exact adapter imports and source hashes in the implementation seal.

Optional joint-layer reference: 21dd869c214ad48c3eb0ce4e8784a253a75055f0.
Optional Wave F5 reference: 736177270530194ee263260c87a2a3445c82ee43.
Neither is merged or required by this design. Any future transplant or rebase requires a separately recorded integration decision and a new campaign seal.

## Authority boundary

An E32 result is executable experimental evidence only. It cannot add SAME_SEMANTICS edges, mint a correspondence certificate, promote PCT levels, alter proof eligibility, or claim kernel verification. Preserve all baseline files byte-for-byte; baseline historical counts are not recomputed or reinterpreted by this package.

No Jev access, paid API, network inference, new textbook ingestion, CI workflow, PR or merge is authorized by this documentation change. Local inference is optional at runtime but required before making a real-model speedup claim.

Public or third-party black-box characterizations may motivate E32 probes, but they are not treated as authoritative descriptions of proprietary internals. E32 claims come only from mechanisms directly implemented and measurements actually produced by the sealed campaign.

## Specification acceptance checklist

- Serial formulation, conventional scheduler, human factorization and automatic factorization/optimization are separated.
- Width and true dependency depth are measured independently.
- Independent sibling-question isolation is distinguished from listwise option interaction.
- Option-order/list-expansion sensitivity is characterized without imposing false probability invariance.
- Typed outputs and deterministic composition are explicit.
- Exact dependency preservation and fail-closed rewrites are mandatory.
- Isolated ground truth and sealed holdouts are required.
- Local deterministic and model planes have separate verdicts.
- End-to-end costs include factorization/compilation, verification and speculative work.
- Reproducible run seals and negative controls are required.
- Backend levels distinguish isolated scoring, batching, shared-state reuse and direct typed readout.
- B3 requires a sealed ReadoutContract and cannot silently retain answer-string scoring.
- Diagnostic confidence metrics are typed, deterministic, sealed and non-authoritative for the primary policy.
- No vendor sampler, RLCD calibration, proprietary architecture or mathematical-equivalence claim may be inferred from timing.

Implementation remains a separate step after review of this written specification.
