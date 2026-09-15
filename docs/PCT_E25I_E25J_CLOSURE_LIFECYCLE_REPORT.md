# PCT E25I–E25J Closure Lifecycle Report

**Branch:** `agent/pct-computational-architecture`  
**Stage:** E25I–E25J  
**Status:** COMPLETE / PASS

## Purpose and preregistration

E25D–E25H established a layered closure model in which four real source-bound MAPEOGEO contracts reached C2, then independently passed C5a exact witness-bearing morphism equality, C5b provenance binding, and the E25H strict conjunctive C5 policy.

E25I–E25J tests a different requirement: whether closure can be treated as a deterministic lifecycle rather than a permanent accumulated label. The preregistered design required trust to be derived from immutable evidence receipts, explicitly revocable, stale-aware, recoverable only through new receipts, and historically auditable.

This stage is restricted to four `REAL_SOURCE_BOUND` components:

- rank-nullity (`source-bound:rank:theorem_6_16`)
- convexity (`source-bound:convex:definition_44_6`)
- positive one-dimensional LP duality (`source-bound:lp:theorem_47_9`)
- Gaussian exponent identity (`source-bound:gauss:definition_53_4`)

Synthetic lifecycle faults are controls only and do not represent defects in the real graph.

## E25I — deterministic closure promotion

E25I constructs an append-only receipt ledger from the already-frozen E25D, E25G, and E25H evidence.

The baseline ledger contains **25 immutable receipts**:

- four `C0_IDENTITY` receipts
- four `C1_CERTIFICATE_BINDING` receipts
- four `C2_EXECUTABLE_CONTRACT` receipts
- four `C5A_EXACT_MORPHISM` receipts
- four `C5B_PROVENANCE_BINDING` receipts
- four `C5_ELIGIBILITY` receipts
- one shared `GLOBAL_C5_STRICT_POLICY` receipt

Receipt ids are SHA-256 hashes of canonical receipt payloads. Mutable lifecycle authority is not stored inside a receipt; it is derived by replay.

The pre-C5 reconstruction reproduces the historical E25D frontier exactly:

```text
C2: 4
```

with C3 and C4 remaining explicitly `NOT_APPLICABLE` for all four scalar/decision contracts.

After the frozen C5a, C5b, and strict-policy receipts are included, the derived frontier becomes:

```text
C5: 4
```

No C3/C4 state is rewritten to `PASS`. The current baseline snapshot digest is:

```text
961b35f4422319c74495a3e4a78e528fa04db0ec3035ffdf4c5740be2b5ccba2
```

This promotion is therefore not a stored trust score. It is the result of evaluating the active receipt dependency graph.

## Receipt and event model

Mathematical verdict and lifecycle authority are separate axes. A receipt may remain mathematically `PASS` while no longer being authoritative.

The derived authority states are:

```text
ACTIVE
STALE
REVOKED
SUPERSEDED
INVALID
```

Lifecycle events are append-only. Direct events alter the authority interpretation of a targeted receipt; descendants become `STALE` by generic dependency propagation. No role-specific downgrade table is used by the replay engine to set a frontier.

The effective frontier is recomputed from the strongest remaining applicable, authoritative evidence.

## E25J — 21-scenario revocation and recovery matrix

E25J executed exactly **21 preregistered synthetic lifecycle scenarios**:

```text
J1 C5a superseded        4
J2 C5b revoked           4
J3 C2 superseded         4
J4 C1 revoked            4
J5 identity conflict     4
J6 strict policy replaced 1
TOTAL                    21
```

All 21 scenarios passed.

### Downgrade behavior

The observed downgrade frontier matched the preregistered dependency model in every component:

| Scenario | Direct change | Derived result |
|---|---|---|
| J1 | C5a superseded | C5 → C2 |
| J2 | C5b revoked | C5 → C2 |
| J3 | C2 superseded | C5 → C1 |
| J4 | C1 revoked | C5 → C0 |
| J5 | C0 identity conflict | C5 → INVALID / no frontier |
| J6 | shared strict-policy receipt superseded | all four C5 → C2 |

The important result is that these frontiers emerge from dependency invalidation. For example, superseding C2 makes both C5a and C5b stale because both depend on C2; their common C5 eligibility receipt consequently becomes stale as well.

## Recovery and anti-resurrection

Every component-local downgrade was followed by explicit recovery. Recovery returned the component to C5 only after the required replacement or revalidation receipts were issued.

The old downstream receipts remained present as historical evidence but **never became authoritative again**. A new ancestor does not silently reactivate a stale descendant. New C5 eligibility receipts explicitly bind to the new active dependency set.

This gives the lifecycle an anti-resurrection invariant:

```text
replacement ancestor != reactivation of old descendants
```

A prior successful C5 result can remain historically true for its original dependency set while no longer contributing to current closure.

## Identity epochs

J5 treats source identity conflict more strongly than ordinary evidence replacement.

An identity conflict produces:

```text
component_state = INVALID
effective_frontier = none
```

Recovery requires an explicit `IDENTITY_REBIND` and increments the component epoch from 0 to 1. The complete C0/C1/C2/C5a/C5b/C5 chain is then reissued in the new epoch.

Receipts from epoch 0 remain in the history but cannot become authoritative in epoch 1. This prevents evidence attached to an obsolete mathematical identity from silently crossing an identity boundary.

## Shared-policy propagation

J6 superseded the single shared E25H `GLOBAL_C5_STRICT_POLICY` receipt.

The effect propagated across all four real components:

```text
before:  C5: 4
after:   C2: 4
```

C5a and C5b remained individually authoritative; only the C5 eligibility receipts became stale because their shared policy dependency was no longer active.

Issuing a replacement strict-policy receipt was not sufficient by itself to restore C5. Four new C5 eligibility receipts had to bind explicitly to the replacement policy. Recovery then produced:

```text
C5: 4
```

This demonstrates cross-component staleness propagation from a shared dependency without incorrectly invalidating independent mathematical evidence.

## Reproducibility and frozen evidence

The committed evidence files are regenerated deterministically in CI and compared against fresh execution:

```text
evidence/pct_e25i_closure_receipt_ledger.json
evidence/pct_e25i_derived_closure_snapshot.json
evidence/pct_e25j_revocation_staleness.json
```

Canonical JSON uses sorted keys and compact separators. Receipt/event ids and state digests are content-derived. No current timestamp, UUID, machine path, runner id, or wall-clock freshness rule participates in scientific state derivation.

## What is established

For the four frozen real contracts, this stage establishes that:

1. C0–C5 closure can be reconstructed as a deterministic dependency-derived state rather than a manually assigned trust label.
2. C5 may be derived across explicitly `NOT_APPLICABLE` C3/C4 layers without falsely claiming those layers passed.
3. Direct revocation or supersession propagates staleness to dependent evidence.
4. The frontier falls to the strongest still-supported closure level.
5. Mathematical PASS and current authority remain distinct.
6. Recovery requires new dependency-bound receipts; stale descendants do not silently resurrect.
7. Identity conflicts require a new component epoch and complete re-binding.
8. A shared policy dependency can revoke C5 authority across multiple components without invalidating independent C5a/C5b evidence.
9. Ordered replay is deterministic for the preregistered lifecycle scenarios.

## What is not established

This stage does **not** establish:

- universal truth maintenance for arbitrary mathematics
- lifecycle coverage for every current or future MAPEOGEO node/edge
- a universal notion of temporal freshness
- automatic semantic graph mutation or promotion
- that all mathematical contracts should use the same applicability mask
- that C3/C4 are unnecessary in domains where chain/homology structure is meaningful
- that historical evidence should be deleted after revocation

The 21 lifecycle faults are controlled synthetic cases, not observed failures in the current real graph.

## Architectural consequence

The closure model can now be represented as two separate objects:

```text
immutable evidence history
        ↓ replay
current authoritative closure view
```

This is materially different from accumulating a confidence field on a knowledge-graph edge. A verified relationship has a reproducible dependency lineage; when that lineage changes, its current authority changes without rewriting history.

The resulting governing rule is:

```text
Current trust is a derived view over immutable evidence history.
```

That gives MAPEOGEO a basis for fail-closed promotion, revocation, recovery, provenance-preserving audit, and eventually incremental verification across a larger mathematical graph—without requiring the semantic graph itself to be the mutable trust ledger.
