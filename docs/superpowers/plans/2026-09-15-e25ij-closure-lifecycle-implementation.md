# E25I–E25J Closure Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a deterministic, append-only closure lifecycle that derives C0–C5 authority for the four frozen source-bound contracts, propagates revocation/staleness correctly, and requires explicit new receipts for recovery.

**Architecture:** E25I/J remains an isolated experiment package under `experiments/pct_e25ij/`. Immutable content-addressed receipts and append-only events are replayed by a pure lifecycle evaluator to derive authority states and effective frontiers; scenario code constructs the 21 preregistered downgrade/recovery controls. Frozen JSON evidence is generated deterministically and compared against fresh execution in CI. Existing semantic graph data and E25D–H evidence are read-only inputs.

**Tech Stack:** Python 3.12, standard library (`dataclasses`, `hashlib`, `json`, `copy`, `pathlib`), pytest, existing PCT evidence JSON.

**Spec:** `docs/superpowers/specs/2026-09-15-e25ij-closure-lifecycle-design.md`

## Global Constraints

- Work only on `agent/pct-computational-architecture`; do not modify `main`.
- Receipts and lifecycle events are append-only and content-addressed; no wall-clock timestamp, UUID, runner id, or machine path may enter digests.
- Receipt payloads do **not** store mutable authority state. Authority is derived by event replay.
- C3/C4 remain explicitly `NOT_APPLICABLE` for the four current contracts.
- C5 requires active C0/C1/C2/C5a/C5b plus the active E25H `STRICT_AND` policy receipt.
- Replacing an ancestor never silently reactivates a stale descendant; downstream evidence must be reissued/revalidated.
- Identity rebinding increments `component_epoch`; prior-epoch descendants can never become authoritative in the new epoch.
- Synthetic controls never count as real repository closure evidence.
- Existing E25D, E25G, and E25H evidence files remain unchanged.
- Lifecycle evaluation never edits semantic graph edges.

---

### Task 1: Immutable Receipt Model and E25I Baseline Promotion

**Files:**
- Create: `experiments/pct_e25ij/__init__.py`
- Create: `experiments/pct_e25ij/receipts.py`
- Create: `experiments/pct_e25ij/lifecycle.py`
- Create: `experiments/pct_e25ij/test_e25ij.py`

**Interfaces:**
- Produces: `canonical_sha256(value: object) -> str`
- Produces: `make_receipt(*, component_id: str, component_epoch: int, layer: str, role: str, mathematical_verdict: str, content: object, dependency_receipt_ids: list[str], source_statement_sha256: str, evidence_refs: list[str], predecessor_receipt_id: str | None, issuance_revision: int) -> dict`
- Produces: `make_event(*, revision: int, event_type: str, target_receipt_id: str, component_id: str, reason_code: str, replacement_receipt_id: str | None = None, new_component_epoch: int | None = None) -> dict`
- Produces: `build_baseline_ledger() -> dict`
- Produces: `replay_lifecycle(ledger: dict, events: list[dict] | None = None) -> dict`
- Produces: `run_e25i_audit() -> dict`

- [ ] **Step 1: Write the failing baseline tests**

Add tests that require deterministic immutable receipts, exact reconstruction of E25D C0–C2, explicit C3/C4 `NOT_APPLICABLE`, exclusion of synthetic controls, and derived C5 promotion only when all required receipts exist:

```python
from copy import deepcopy

from experiments.pct_e25ij.receipts import make_receipt
from experiments.pct_e25ij.lifecycle import build_baseline_ledger, replay_lifecycle, run_e25i_audit


def test_receipt_id_is_deterministic_and_authority_is_not_stored():
    kwargs = dict(
        component_id="source-bound:rank:theorem_6_16",
        component_epoch=0,
        layer="C0",
        role="C0_IDENTITY",
        mathematical_verdict="PASS",
        content={"x": 1},
        dependency_receipt_ids=[],
        source_statement_sha256="abc",
        evidence_refs=["fixture"],
        predecessor_receipt_id=None,
        issuance_revision=1,
    )
    a = make_receipt(**kwargs)
    b = make_receipt(**deepcopy(kwargs))
    assert a == b
    assert len(a["receipt_id"]) == 64
    assert "authority_state" not in a


def test_e25i_reconstructs_then_promotes_four_real_components():
    result = run_e25i_audit()
    assert result["status"] == "PASS"
    assert result["real_component_count"] == 4
    assert result["synthetic_components_counted_as_real"] == 0
    assert result["pre_c5_frontier_histogram"] == {"C2": 4}
    assert result["post_c5_frontier_histogram"] == {"C5": 4}
    for component in result["components"]:
        assert component["pre_c5"]["closure"]["C3"]["state"] == "NOT_APPLICABLE"
        assert component["pre_c5"]["closure"]["C4"]["state"] == "NOT_APPLICABLE"
        assert component["post_c5"]["effective_frontier"] == "C5"


def test_missing_required_receipt_prevents_c5_without_inventing_pass():
    ledger = build_baseline_ledger()
    c5a = next(r for r in ledger["receipts"] if r["role"] == "C5A_EXACT_MORPHISM")
    reduced = deepcopy(ledger)
    reduced["receipts"] = [r for r in reduced["receipts"] if r["receipt_id"] != c5a["receipt_id"]]
    snapshot = replay_lifecycle(reduced)
    component = next(c for c in snapshot["components"] if c["component_id"] == c5a["component_id"])
    assert component["effective_frontier"] == "C2"
    assert component["closure"]["C5"]["state"] == "NOT_ESTABLISHED"
```

- [ ] **Step 2: Run the new test file and verify RED**

Run:

```bash
python -m pytest -q experiments/pct_e25ij/test_e25ij.py
```

Expected: collection fails because `experiments.pct_e25ij.receipts` / `lifecycle` do not yet exist.

- [ ] **Step 3: Implement canonical receipts and baseline ledger**

`receipts.py` canonicalization must use:

```python
def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
```

`make_receipt` builds the payload without `receipt_id`, hashes that payload, then returns `{"receipt_id": digest, **payload}`. `make_event` follows the same content-addressed rule for `event_id`.

`build_baseline_ledger()` loads only these frozen inputs:

```text
evidence/pct_e25d_real_component_manifest.json
evidence/pct_e25d_closure_atlas.json
evidence/pct_e25g_exact_morphism_audit.json
evidence/pct_e25g_provenance_bindings.json
evidence/pct_e25h_policy_comparison.json
```

For each of four `REAL_SOURCE_BOUND` components issue deterministic roles:

```text
C0_IDENTITY
C1_CERTIFICATE_BINDING
C2_EXECUTABLE_CONTRACT
C5A_EXACT_MORPHISM
C5B_PROVENANCE_BINDING
C5_ELIGIBILITY
```

and one global `GLOBAL_C5_STRICT_POLICY` receipt. `C5_ELIGIBILITY` depends on the component's C0/C1/C2/C5a/C5b receipts plus the global strict-policy receipt.

- [ ] **Step 4: Implement pure baseline replay**

`replay_lifecycle` must derive authority from receipt existence/dependencies even with no events. It must construct per-component closure entries C0–C5, preserve C3/C4 as `NOT_APPLICABLE`, and derive C5 only from a valid active `C5_ELIGIBILITY` receipt whose dependencies are all active in the current component epoch.

- [ ] **Step 5: Run Task 1 tests and full existing PCT suite**

Run:

```bash
python -m pytest -q experiments/pct_e25ij/test_e25ij.py
python -m pytest -q experiments/pct_e1_e25/test_campaign.py experiments/pct_e25bc/test_audit.py experiments/pct_e25def/test_e25def.py experiments/pct_e25gh/test_e25gh.py experiments/pct_e25ij/test_e25ij.py
```

Expected: all tests PASS.

- [ ] **Step 6: Commit Task 1**

```bash
git add experiments/pct_e25ij
 git commit -m "feat: add E25I closure receipt state machine"
```

---

### Task 2: Revocation, Supersession, Staleness, and Epoch Semantics

**Files:**
- Modify: `experiments/pct_e25ij/lifecycle.py`
- Modify: `experiments/pct_e25ij/test_e25ij.py`

**Interfaces:**
- Consumes: `build_baseline_ledger`, `make_receipt`, `make_event`
- Produces: `apply_event_state(receipts: list[dict], events: list[dict]) -> dict[str, str]`
- `replay_lifecycle` must expose `authoritative_receipt_ids`, `stale_receipt_ids`, `revoked_receipt_ids`, `superseded_receipt_ids`, `invalid_receipt_ids`, `component_epoch`, `effective_frontier`, and `state_digest`.

- [ ] **Step 1: Add failing authority-propagation tests**

```python

def test_c5a_supersession_drops_only_to_c2_and_does_not_resurrect_old_c5():
    ledger = build_baseline_ledger()
    component_id = "source-bound:rank:theorem_6_16"
    old_c5a = next(r for r in ledger["receipts"] if r["component_id"] == component_id and r["role"] == "C5A_EXACT_MORPHISM")
    replacement = make_receipt(
        component_id=component_id,
        component_epoch=0,
        layer="C5",
        role="C5A_EXACT_MORPHISM",
        mathematical_verdict="PASS",
        content={"replacement": "exact-map-v2"},
        dependency_receipt_ids=list(old_c5a["dependency_receipt_ids"]),
        source_statement_sha256=old_c5a["source_statement_sha256"],
        evidence_refs=["synthetic:J1"],
        predecessor_receipt_id=old_c5a["receipt_id"],
        issuance_revision=100,
    )
    ledger["receipts"].append(replacement)
    event = make_event(
        revision=101,
        event_type="SUPERSEDE",
        target_receipt_id=old_c5a["receipt_id"],
        component_id=component_id,
        reason_code="J1_C5A_REPLACED",
        replacement_receipt_id=replacement["receipt_id"],
    )
    snapshot = replay_lifecycle(ledger, [event])
    c = next(x for x in snapshot["components"] if x["component_id"] == component_id)
    assert c["effective_frontier"] == "C2"
    assert old_c5a["receipt_id"] in c["superseded_receipt_ids"]
    assert replacement["receipt_id"] in c["authoritative_receipt_ids"]
    assert c["closure"]["C5"]["state"] == "NOT_ESTABLISHED"


def test_identity_conflict_invalidates_component_and_epoch_rebind_isolated():
    ledger = build_baseline_ledger()
    component_id = "source-bound:rank:theorem_6_16"
    c0 = next(r for r in ledger["receipts"] if r["component_id"] == component_id and r["role"] == "C0_IDENTITY")
    conflict = make_event(
        revision=200,
        event_type="IDENTITY_CONFLICT",
        target_receipt_id=c0["receipt_id"],
        component_id=component_id,
        reason_code="J5_SOURCE_HASH_CONFLICT",
    )
    broken = replay_lifecycle(ledger, [conflict])
    c = next(x for x in broken["components"] if x["component_id"] == component_id)
    assert c["effective_frontier"] is None
    assert c["component_state"] == "INVALID"
```

Also add tests for C5b revoke -> C2, C2 supersede -> C1, C1 revoke -> C0, and shared strict-policy supersession -> all four C2.

- [ ] **Step 2: Run the new tests and verify RED**

Expected: lifecycle replay does not yet implement event authority propagation.

- [ ] **Step 3: Implement event replay and descendant staleness**

Rules:

```text
REVOKE(target)       target -> REVOKED
SUPERSEDE(target)    target -> SUPERSEDED; replacement may be ACTIVE
IDENTITY_CONFLICT    target -> INVALID; component state INVALID
```

After direct event state is resolved, repeatedly mark an otherwise-active receipt `STALE` when any dependency is non-active, belongs to the wrong component epoch, or is missing. This fixed-point propagation must be graph-derived rather than hard-coded by role.

`IDENTITY_REBIND` changes the derived current epoch and permits only receipts issued for that epoch to become authoritative. Prior-epoch receipts remain historical.

- [ ] **Step 4: Run Task 2 tests and full regression suite**

Expected: all tests PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add experiments/pct_e25ij/lifecycle.py experiments/pct_e25ij/test_e25ij.py
 git commit -m "feat: propagate E25J revocation and staleness"
```

---

### Task 3: Twenty-One Downgrade/Recovery Scenarios

**Files:**
- Create: `experiments/pct_e25ij/scenarios.py`
- Modify: `experiments/pct_e25ij/test_e25ij.py`

**Interfaces:**
- Produces: `run_e25j_scenarios() -> dict`
- Each scenario record contains: `scenario_id`, `provenance_class`, `target_component_ids`, `downgrade_snapshot`, `recovery_snapshot`, `historical_receipt_checks`, `expected_frontier`, `observed_frontier`, `recovered_frontier`, `status`.

- [ ] **Step 1: Add failing full-scenario tests**

```python
from experiments.pct_e25ij.scenarios import run_e25j_scenarios


def test_e25j_runs_exactly_21_preregistered_scenarios():
    result = run_e25j_scenarios()
    assert result["status"] == "PASS"
    assert result["scenario_count"] == 21
    assert result["component_scenario_count"] == 20
    assert result["shared_policy_scenario_count"] == 1


def test_e25j_downgrades_to_exact_remaining_frontier():
    result = run_e25j_scenarios()
    expected = {
        "J1_C5A_SUPERSEDED": "C2",
        "J2_C5B_REVOKED": "C2",
        "J3_C2_SUPERSEDED": "C1",
        "J4_C1_REVOKED": "C0",
        "J5_IDENTITY_CONFLICT": None,
    }
    for scenario in result["scenarios"]:
        if scenario["scenario_type"] in expected:
            assert scenario["observed_frontier"] == expected[scenario["scenario_type"]]
            assert scenario["recovered_frontier"] == "C5"
            assert scenario["old_downstream_receipts_reactivated"] is False


def test_shared_policy_replacement_drops_all_four_then_requires_new_eligibility():
    result = run_e25j_scenarios()
    j6 = next(x for x in result["scenarios"] if x["scenario_type"] == "J6_STRICT_POLICY_SUPERSEDED")
    assert j6["downgrade_frontiers"] == {"C2": 4}
    assert j6["recovery_frontiers"] == {"C5": 4}
    assert j6["old_downstream_receipts_reactivated"] is False
```

- [ ] **Step 2: Run and verify RED**

Expected: import failure for `scenarios.py`.

- [ ] **Step 3: Implement J1–J6 using generic receipt/event primitives**

For each of four real components execute isolated fresh-ledger scenarios:

```text
J1 C5a supersede + replacement + new C5 eligibility
J2 C5b revoke + new C5b + new C5 eligibility
J3 C2 supersede + new C2 + new C5a + new C5b + new C5 eligibility
J4 C1 revoke + new C1 + new C2 + new C5a + new C5b + new C5 eligibility
J5 C0 identity conflict + IDENTITY_REBIND(epoch+1) + reissue C0/C1/C2/C5a/C5b/C5 eligibility
```

J6 supersedes the shared policy, verifies all four drop to C2, issues a replacement policy, then issues four new C5 eligibility receipts bound to that replacement.

Every recovery must assert that old stale descendants remain non-authoritative and that every replacement receipt id differs from its predecessor.

- [ ] **Step 4: Run Task 3 tests and full suite**

Expected: all tests PASS and scenario count is exactly 21.

- [ ] **Step 5: Commit Task 3**

```bash
git add experiments/pct_e25ij/scenarios.py experiments/pct_e25ij/test_e25ij.py
 git commit -m "test: add E25J lifecycle recovery matrix"
```

---

### Task 4: Frozen Evidence and Reproducibility Gate

**Files:**
- Create: `experiments/pct_e25ij/generate_evidence.py`
- Modify: `experiments/pct_e25ij/test_e25ij.py`
- Create after generated RED gate:
  - `evidence/pct_e25i_closure_receipt_ledger.json`
  - `evidence/pct_e25i_derived_closure_snapshot.json`
  - `evidence/pct_e25j_revocation_staleness.json`

**Interfaces:**
- Produces: `generate(output_dir: Path) -> None`
- Frozen evidence must equal fresh execution as parsed JSON.

- [ ] **Step 1: Add failing frozen-evidence test**

```python

def test_frozen_e25ij_evidence_matches_fresh_execution():
    root = Path(__file__).resolve().parents[2]
    i = run_e25i_audit()
    j = run_e25j_scenarios()
    assert json.loads((root / "evidence/pct_e25i_closure_receipt_ledger.json").read_text()) == i["ledger"]
    assert json.loads((root / "evidence/pct_e25i_derived_closure_snapshot.json").read_text()) == i["snapshot"]
    assert json.loads((root / "evidence/pct_e25j_revocation_staleness.json").read_text()) == j
```

- [ ] **Step 2: Run and verify RED because evidence files do not exist**

Expected: `FileNotFoundError` for the first E25I evidence file.

- [ ] **Step 3: Implement deterministic evidence generator**

Use the same writer contract as E25G/H:

```python
path.write_text(
    json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n",
    encoding="utf-8",
)
```

- [ ] **Step 4: Extend CI to generate candidate E25I/J evidence outside `evidence/` and upload it**

Modify `.github/workflows/pct-e1-e25-campaign.yml` to:

```text
compileall experiments/pct_e25ij
python -m experiments.pct_e25ij.generate_evidence --out-dir generated-e25ij
upload generated-e25ij/*.json as pct-e25ij-generated-evidence
run experiments/pct_e25ij/test_e25ij.py in the full regression command
```

The workflow generation step must not copy candidates into `evidence/`; the frozen test must stay red until exact generated files are explicitly committed.

- [ ] **Step 5: Run CI, download the generated artifact, inspect it, and commit the exact generated evidence**

No hand-edited scientific values. If a candidate differs from expectation, debug before freezing.

- [ ] **Step 6: Rerun complete CI**

Expected: static checks, candidate generation, artifact upload, and all tests PASS.

- [ ] **Step 7: Commit Task 4**

```bash
git add experiments/pct_e25ij/generate_evidence.py experiments/pct_e25ij/test_e25ij.py evidence/pct_e25i_closure_receipt_ledger.json evidence/pct_e25i_derived_closure_snapshot.json evidence/pct_e25j_revocation_staleness.json .github/workflows/pct-e1-e25-campaign.yml
 git commit -m "evidence: freeze E25I E25J lifecycle campaign"
```

---

### Task 5: Scientific Report and Final Branch Verification

**Files:**
- Create: `docs/PCT_E25I_E25J_CLOSURE_LIFECYCLE_REPORT.md`
- Modify only if required for path coverage: `.github/workflows/pct-e1-e25-campaign.yml`

**Interfaces:**
- Report consumes only frozen E25I/J evidence and existing E25D–H evidence.

- [ ] **Step 1: Write the report with explicit claim boundaries**

Report sections:

```text
Purpose and preregistration
E25I baseline reconstruction and C5 promotion
Receipt/event model
E25J 21-scenario downgrade matrix
Recovery and anti-resurrection results
Identity epoch behavior
Shared-policy propagation
What is established
What is not established
Architectural consequence for MAPEOGEO
```

The report must not claim universal truth maintenance or whole-repository lifecycle coverage.

- [ ] **Step 2: Ensure CI path filters include E25I/J code/evidence/report/spec/plan**

Paths must include:

```text
experiments/pct_e25ij/**
evidence/pct_e25i_closure_receipt_ledger.json
evidence/pct_e25i_derived_closure_snapshot.json
evidence/pct_e25j_revocation_staleness.json
docs/PCT_E25I_E25J_CLOSURE_LIFECYCLE_REPORT.md
docs/superpowers/specs/2026-09-15-e25ij-closure-lifecycle-design.md
docs/superpowers/plans/2026-09-15-e25ij-closure-lifecycle-implementation.md
```

- [ ] **Step 3: Run final authoritative branch CI**

Require success for:

```text
Python dependency install
static compile checks
E25G/H candidate generation (existing)
E25I/J candidate generation
artifact uploads
full PCT regression suite including E25I/J
```

- [ ] **Step 4: Verify branch head and no merge/PR to main**

Fetch `agent/pct-computational-architecture`, record exact head SHA and successful workflow run id. Do not open a PR and do not merge.

- [ ] **Step 5: Commit final report/cleanup if needed**

```bash
git add docs/PCT_E25I_E25J_CLOSURE_LIFECYCLE_REPORT.md .github/workflows/pct-e1-e25-campaign.yml
 git commit -m "docs: report E25I E25J closure lifecycle results"
```
