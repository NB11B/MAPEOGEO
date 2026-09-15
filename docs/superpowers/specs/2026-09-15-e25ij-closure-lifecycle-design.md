# E25I–E25J Closure Promotion, Revocation, and Staleness Design

**Date:** 2026-09-15  
**Branch:** `agent/pct-computational-architecture`  
**Status:** Approved design, frozen before implementation

## Purpose

E25D–E25H established a layered closure model for four real source-bound MAPEOGEO contracts. The frozen E25D atlas currently places all four at C2, with C3/C4 explicitly not applicable and C5 previously not established. E25G subsequently established witness-bearing C5a exact-morphism equality and C5b provenance binding for all four contracts, while E25H established that the strict conjunctive C5 policy rejects all preregistered single-axis adversaries.

The next requirement is lifecycle safety: closure must be **derived, revocable, stale-aware, recoverable, and historically auditable**. E25I and E25J introduce a deterministic closure lifecycle without mutating the semantic graph or rewriting prior evidence.

The governing principle is:

```text
Trust is derived from currently authoritative evidence.
Historical evidence is never erased.
Downstream trust becomes stale when a dependency changes.
Recovery requires new evidence receipts; old trust never silently reactivates.
```

# 1. Scope and non-goals

This stage applies only to the four frozen `REAL_SOURCE_BOUND` contracts:

- rank-nullity (`source-bound:rank:theorem_6_16`);
- convexity (`source-bound:convex:definition_44_6`);
- positive one-dimensional LP duality (`source-bound:lp:theorem_47_9`);
- Gaussian exponent identity (`source-bound:gauss:definition_53_4`).

This stage does **not**:

- modify `main`;
- mutate existing semantic edge types;
- rewrite E25D evidence in place;
- delete or overwrite historical receipts;
- infer C3/C4 applicability from C5;
- promote synthetic controls as real evidence;
- introduce a blended trust score;
- use wall-clock age alone as a scientific invalidation criterion.

# 2. Mathematical verdict and lifecycle authority are separate

Existing mathematical verdicts remain unchanged:

```text
PASS
FAIL
NOT_APPLICABLE
NOT_ESTABLISHED
INVALID
ERROR
INCONCLUSIVE
```

Lifecycle authority is a derived, separate axis:

```text
ACTIVE       evidence may contribute to current closure
STALE        evidence was valid for an older dependency set but is not current
REVOKED      evidence was explicitly withdrawn from authority
SUPERSEDED   a newer receipt replaces this receipt for the same role
INVALID      the receipt is internally contradictory or bound to the wrong identity
```

A mathematically `PASS` receipt may therefore be lifecycle `STALE`. Dependency changes do not rewrite historical mathematical results as failures.

# 3. Immutable evidence receipts

Every lifecycle-relevant item is represented by an immutable canonical receipt.

Minimum receipt schema:

```text
{
  receipt_id,
  component_id,
  component_epoch,
  layer,
  role,
  mathematical_verdict,
  content_sha256,
  dependency_receipt_ids,
  source_statement_sha256,
  evidence_refs,
  predecessor_receipt_id,
  issuance_revision
}
```

`receipt_id` is the SHA-256 of the canonical receipt payload excluding `receipt_id` itself. `issuance_revision` is a deterministic integer revision within the experiment ledger; no wall-clock timestamp participates in state derivation.

Receipts are append-only. They never contain a mutable authority field. `ACTIVE`, `STALE`, `REVOKED`, `SUPERSEDED`, and `INVALID` are computed by replaying lifecycle events over the immutable receipt graph.

# 4. Lifecycle events and authority derivation

Lifecycle changes are append-only canonical events:

```text
{
  event_id,
  revision,
  event_type,
  target_receipt_id,
  component_id,
  reason_code,
  replacement_receipt_id,
  prior_state_digest,
  resulting_state_digest
}
```

Allowed direct event classes for this stage:

```text
ISSUE
REVOKE
SUPERSEDE
IDENTITY_CONFLICT
IDENTITY_REBIND
REVALIDATE
```

`STALE` is not directly assigned by an event. It is derived when an otherwise usable receipt depends on a receipt that is no longer authoritative, or when its `component_epoch` no longer matches the current identity epoch.

Direct authority precedence for a receipt is deterministic:

```text
IDENTITY_CONFLICT / invalid binding -> INVALID
explicit REVOKE                    -> REVOKED
explicit SUPERSEDE                 -> SUPERSEDED
otherwise, dependency mismatch     -> STALE
otherwise                          -> ACTIVE
```

A later replacement receipt does not change the state of an older stale/superseded receipt. New authority is carried by a distinct new receipt.

Events do not mutate semantic graph edges. They affect only the derived lifecycle view.

# 5. Closure dependency graph

For the four current scalar/decision contracts, receipt dependencies are frozen as follows:

```text
C0_IDENTITY
    |
    v
C1_CERTIFICATE_BINDING
    |
    v
C2_EXECUTABLE_CONTRACT
    |
    +-----------------------+
    |                       |
    v                       v
C5A_EXACT_MORPHISM     C5B_PROVENANCE_BINDING
    \                       /
     \                     /
      +--- GLOBAL_C5_STRICT_POLICY
                    |
                    v
              C5_ELIGIBILITY
```

Explicit dependency rules:

```text
C1 depends on C0.
C2 depends on C0 and C1.
C5a depends on C2.
C5b depends on C0, C1, and C2.
C5 eligibility depends on C0, C1, C2, C5a, C5b, and GLOBAL_C5_STRICT_POLICY.
```

C5a and C5b remain independent sibling evidence axes. Neither depends on the other. Their conjunction occurs only at C5 eligibility.

C3 and C4 remain `NOT_APPLICABLE` for these four contracts. Their absence is explicit and does not block C5 because applicability masks govern the path.

A C5 result is authoritative only when all of the following are true:

1. C0, C1, and C2 are currently `ACTIVE` and mathematically `PASS`;
2. C3 and C4 are either `PASS` or explicitly `NOT_APPLICABLE` under the component applicability mask;
3. C5a is `ACTIVE` and `PASS`;
4. C5b is `ACTIVE` and `PASS`;
5. the E25H strict-policy receipt is `ACTIVE` and marks `STRICT_AND` acceptable;
6. the active C5 eligibility receipt explicitly names the exact active dependency receipt ids above.

No lower-layer evidence may manufacture or infer a missing higher-layer receipt.

# 6. Derived component state

The state machine derives a snapshot rather than editing a stored trust level.

Per-component output:

```text
{
  component_id,
  component_epoch,
  closure_vector,
  effective_frontier,
  receipt_authority,
  authoritative_receipt_ids,
  stale_receipt_ids,
  revoked_receipt_ids,
  superseded_receipt_ids,
  invalid_receipt_ids,
  blocking_reason,
  state_digest
}
```

The `effective_frontier` is the highest **applicable** closure level whose required evidence is currently authoritative and whose dependencies are satisfied.

For the current applicability mask, a valid component may move in the reporting frontier from C2 to C5 while retaining:

```text
C3 = NOT_APPLICABLE
C4 = NOT_APPLICABLE
```

This is not a claim that C3/C4 passed.

# E25I — Closure Promotion State Machine

## 7. Baseline construction

E25I consumes only already-frozen evidence:

```text
evidence/pct_e25d_real_component_manifest.json
evidence/pct_e25d_closure_atlas.json
evidence/pct_e25g_exact_morphism_audit.json
evidence/pct_e25g_provenance_bindings.json
evidence/pct_e25h_policy_comparison.json
```

It emits a new lifecycle ledger and derived snapshot. E25D remains untouched as the historical pre-C5 atlas.

## 8. Initial receipt roles

Each real component receives receipt roles sufficient to reconstruct its current state:

```text
C0_IDENTITY
C1_CERTIFICATE_BINDING
C2_EXECUTABLE_CONTRACT
C5A_EXACT_MORPHISM
C5B_PROVENANCE_BINDING
C5_ELIGIBILITY
```

One shared receipt represents the frozen E25H `STRICT_AND` policy result:

```text
GLOBAL_C5_STRICT_POLICY
```

C5 eligibility must depend on the component's exact active C0/C1/C2/C5a/C5b receipt ids plus the exact active shared strict-policy receipt id.

## 9. E25I acceptance criteria

E25I passes only if:

1. exactly four real components are present;
2. all four reconstruct the E25D C0–C2 states exactly before C5 receipts are applied;
3. no synthetic component enters the real ledger;
4. all four derive C5 after C5a, C5b, and strict-policy receipts are issued;
5. C3/C4 remain `NOT_APPLICABLE` and are never rewritten as `PASS`;
6. removing any required active receipt from reconstruction prevents C5;
7. replaying the same ordered receipt/event ledger produces the same state digests byte-for-byte;
8. no lifecycle output mutates the semantic graph or E25D atlas.

Expected valid baseline frontier after replay:

```text
C5: 4
```

This expected result is contingent on fresh execution reproducing the frozen E25G/H evidence; it is not hard-coded as a promotion assertion.

## 10. E25I outputs

```text
evidence/pct_e25i_closure_receipt_ledger.json
evidence/pct_e25i_derived_closure_snapshot.json
```

# E25J — Revocation and Staleness Propagation

## 11. Core downgrade rule

A direct evidence withdrawal affects only the receipt explicitly targeted. Descendants become `STALE` through dependency evaluation; they are not rewritten as mathematical failures.

The derived frontier is then recomputed from currently authoritative evidence.

Preregistered downgrade expectations:

```text
C5a or C5b withdrawal          C5 -> C2
C2 executable withdrawal      C5 -> C1
C1 certificate withdrawal     C5 -> C0
C0 identity conflict          C5 -> INVALID / no authoritative frontier
```

These outcomes must emerge from the dependency graph rather than from special-case frontier assignments.

## 12. Per-component synthetic lifecycle scenarios

Each of the four real components receives five isolated synthetic lifecycle scenarios.

### J1 — exact-morphism evidence superseded

Target: `C5A_EXACT_MORPHISM` only. The adapter identity/provenance lineage is held fixed so this scenario isolates the C5a evidence axis.

Expected:

```text
old C5a -> SUPERSEDED
C5 eligibility -> STALE
C5b remains ACTIVE
C0/C1/C2 remain ACTIVE
frontier -> C2
```

A replacement C5a receipt alone is insufficient to reactivate old C5 eligibility. A new C5 eligibility receipt bound to the replacement C5a is required.

If adapter identity/version itself changes in future work, C5b must also be replaced or revalidated; that broader case is outside J1's isolated-axis control.

### J2 — provenance binding revoked

Target: `C5B_PROVENANCE_BINDING`.

Expected:

```text
old C5b -> REVOKED
C5 eligibility -> STALE
C5a remains ACTIVE
C0/C1/C2 remain ACTIVE
frontier -> C2
```

Recovery requires a new C5b receipt and a new C5 eligibility receipt.

### J3 — executable contract superseded

Target: `C2_EXECUTABLE_CONTRACT`.

Expected:

```text
old C2 -> SUPERSEDED
C5a -> STALE
C5b -> STALE
C5 eligibility -> STALE
C0/C1 remain ACTIVE
frontier -> C1
```

Recovery requires a new C2 receipt and explicit revalidation/new receipts for every downstream C5 dependency. Existing C5 receipts may not silently become active merely because C2 is replaced.

### J4 — certificate binding revoked

Target: `C1_CERTIFICATE_BINDING`.

Expected:

```text
old C1 -> REVOKED
C2 -> STALE
C5a -> STALE
C5b -> STALE
C5 eligibility -> STALE
C0 remains ACTIVE
frontier -> C0
```

Recovery requires a new C1 receipt followed by explicit downstream revalidation.

### J5 — source identity conflict

Target: `C0_IDENTITY`.

Expected:

```text
C0 -> INVALID
all descendants -> STALE
component state -> INVALID
no authoritative closure frontier
```

Recovery requires an explicit `IDENTITY_REBIND` event that increments `component_epoch`. Every downstream receipt must then be reissued or revalidated against the new epoch. Evidence from the prior epoch remains historical and can never become authoritative in the new epoch.

## 13. Shared-policy invalidation scenario

E25J also includes one global scenario.

### J6 — strict-policy receipt superseded

Target: `GLOBAL_C5_STRICT_POLICY`.

Expected across all four components:

```text
old policy receipt -> SUPERSEDED
C5 eligibility receipts -> STALE
C5a/C5b remain ACTIVE
C0/C1/C2 remain ACTIVE
all frontiers -> C2
```

A replacement policy receipt does not resurrect old C5 eligibility receipts. Each component requires a new C5 eligibility receipt that explicitly depends on the replacement policy receipt.

This tests cross-component staleness propagation from a shared dependency.

# 14. Recovery tests

Every J1–J5 scenario is followed by explicit recovery. J6 is also recovered globally.

Recovery acceptance requires:

1. the pre-fault receipt remains present in the ledger;
2. its derived historical authority state remains visible;
3. the replacement/revalidation receipt has a distinct `receipt_id`;
4. downstream stale receipts remain stale;
5. new downstream receipts depend only on currently authoritative ancestors;
6. the component returns to C5 only after all required new receipts exist;
7. replay from revision zero reproduces every intermediate downgrade and recovery digest exactly.

No event may directly set `effective_frontier = C5`; the frontier must emerge from receipt evaluation.

# 15. Scenario counts

Preregistered lifecycle scenarios:

```text
4 components x 5 isolated component scenarios = 20
1 shared strict-policy scenario                = 1
TOTAL                                           = 21
```

Each scenario includes both downgrade and recovery checkpoints.

# 16. Fault interpretation

Synthetic lifecycle scenarios are `SYNTHETIC_CONTROL` and do not imply a real defect in MAPEOGEO's current graph. They validate state-machine behavior only.

Directly targeted receipts receive the event-derived authority transition (`REVOKED`, `SUPERSEDED`, or `INVALID`). Descendants become `STALE` through dependency evaluation unless independently contradicted. This preserves the distinction between:

```text
"this evidence is wrong"
```

and

```text
"this evidence is no longer authoritative under the current dependencies"
```

# 17. Architecture and files

Implementation should remain isolated under:

```text
experiments/pct_e25ij/
    __init__.py
    receipts.py
    lifecycle.py
    scenarios.py
    generate_evidence.py
    test_e25ij.py

evidence/
    pct_e25i_closure_receipt_ledger.json
    pct_e25i_derived_closure_snapshot.json
    pct_e25j_revocation_staleness.json

docs/
    PCT_E25I_E25J_CLOSURE_LIFECYCLE_REPORT.md
```

The existing PCT CI workflow will be extended to compile and execute E25I/J, regenerate candidate evidence in a separate directory, and compare committed frozen evidence against fresh execution.

# 18. Determinism requirements

- Canonical JSON uses sorted keys and compact separators.
- Receipt and event ids are content-derived SHA-256 values.
- Experiment revisions are deterministic integers.
- No current timestamp, random UUID, machine path, or runner id enters state digests.
- Event replay is pure: same ledger + same source evidence => same snapshots and digests.
- Scenario order is frozen and explicit.

# 19. Fail-closed rules

1. Missing required receipt => dependent closure is `NOT_ESTABLISHED`, never inferred `PASS`.
2. Non-active dependency => descendant cannot remain authoritative.
3. A replacement ancestor never automatically reactivates a stale descendant.
4. Identity epoch mismatch makes a descendant ineligible for authority.
5. A revoked receipt cannot be reused as a dependency.
6. A stale receipt may remain mathematically `PASS` but cannot contribute to the frontier.
7. `NOT_APPLICABLE` layers remain explicit; they are not converted to `PASS` for convenience.
8. C5 requires the strict policy receipt; MAP_ONLY/PROVENANCE_ONLY/ANY_AXIS are never accepted for production closure.
9. Synthetic lifecycle controls never promote real repository semantics.
10. Lifecycle evaluation never edits the semantic graph.

# 20. Scientific questions

E25I asks:

```text
Can the current C0–C5 evidence be reconstructed as a deterministic dependency-derived closure state rather than a hand-assigned level?
```

E25J asks:

```text
When an evidence dependency is revoked, superseded, or invalidated, does trust fall to exactly the strongest remaining supported frontier, while preserving historical evidence and preventing silent resurrection?
```

# 21. Claim boundary

A passing E25I/E25J stage establishes a deterministic promotion/revocation/staleness lifecycle for the four frozen source-bound contracts and 21 preregistered synthetic lifecycle scenarios. It does not establish universal truth maintenance for every future MAPEOGEO object, automatic semantic promotion, universal temporal freshness criteria, or whole-repository lifecycle coverage.
