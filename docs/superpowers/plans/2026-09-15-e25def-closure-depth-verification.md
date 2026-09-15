# E25D–E25F Closure-Depth Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a fail-closed closure-depth atlas, deterministic upgrade planner, and layered C0–C5 fault-coverage matrix for the real source-bound PCT trust components.

**Architecture:** Extend the existing `experiments/pct_e25bc` experimental surface with a new focused `experiments/pct_e25def` package. E25D recomputes per-component closure vectors from the frozen real-component manifest and existing E25B/C evidence; E25E derives exactly one next-action class per real component; E25F uses synthetic controls only to verify which closure layer first detects each fault class. Frozen JSON outputs and a human-readable report are regenerated from the same functions and compared byte-for-byte in tests.

**Tech Stack:** Python 3.12, pytest, NetworkX, SymPy exact arithmetic, existing PCT E25B/C evidence and helpers.

**Spec:** `docs/superpowers/specs/2026-09-15-e25def-closure-depth-verification-design.md`

## Global Constraints

- Real repository closure coverage may be assigned only to `REAL_SOURCE_BOUND` components.
- The twenty E25B synthetic triangles remain `SYNTHETIC_CONTROL` calibration fixtures and cannot raise a real component's closure depth.
- Allowed level states are exactly `PASS`, `FAIL`, `NOT_APPLICABLE`, `NOT_ESTABLISHED`, `INVALID`, `ERROR`.
- Missing evidence yields `NOT_ESTABLISHED`; failed applicability yields `NOT_APPLICABLE`.
- Identity failure blocks C1+ evaluation; certificate failure blocks C2+ evaluation.
- C2 success cannot imply C3, C4, or C5.
- C3/C4 are applicable only to explicit chain-map/homology contracts.
- C5 requires explicit exact morphism/provenance evidence.
- No automatic semantic promotion, no `main` merge, and no README claim promotion are part of this stage.
- Outputs must be deterministic and byte-stable under repeated execution.

---

### Task 1: Freeze the real component manifest and shared closure contracts

**Files:**
- Create: `experiments/pct_e25def/__init__.py`
- Create: `experiments/pct_e25def/model.py`
- Create: `evidence/pct_e25d_real_component_manifest.json`
- Create: `experiments/pct_e25def/test_e25def.py`

**Interfaces:**
- Consumes: `evidence/pct_e25b_trust_projection.json`, `evidence/pct_e25c_executable_cycle_audit.json`.
- Produces: `load_real_component_manifest() -> dict`, `validate_manifest(manifest: dict) -> dict`, `LEVELS`, `ALLOWED_STATES`, and deterministic component records used by Tasks 2–4.

- [ ] **Step 1: Write failing manifest tests**

```python
from experiments.pct_e25def.model import load_real_component_manifest, validate_manifest


def test_real_manifest_contains_only_four_source_bound_cycles():
    m = load_real_component_manifest()
    assert m["source_artifact"]["artifact_id"] == 10382242654
    assert len(m["components"]) == 4
    assert {c["provenance_class"] for c in m["components"]} == {"REAL_SOURCE_BOUND"}
    assert {c["contract"] for c in m["components"]} == {"rank", "convex", "lp", "gauss"}


def test_manifest_has_unique_component_ids_and_source_hashes():
    m = load_real_component_manifest()
    r = validate_manifest(m)
    assert r == {"status": "PASS", "components": 4}
    assert len({c["component_id"] for c in m["components"]}) == 4
    assert all(len(c["source_statement_sha256"]) == 64 for c in m["components"])
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest -q experiments/pct_e25def/test_e25def.py -k manifest`

Expected: import/file failures because `pct_e25def` and the manifest do not yet exist.

- [ ] **Step 3: Create the exact manifest**

Create four records copied from the real E25C cycles, each containing:

```json
{
  "component_id": "source-bound:rank:theorem_6_16",
  "provenance_class": "REAL_SOURCE_BOUND",
  "contract": "rank",
  "anchor_id": "srcdecl:theorem:6_16",
  "eo_id": "repr:eo:theorem:6_16",
  "geo_id": "repr:geo:theorem:6_16",
  "formal_id": "formal:lean:theorem_6_16",
  "formal_scope": "GENERAL_FINITE_DIMENSIONAL_DIVISION_RING",
  "source_statement_sha256": "9bb700afa17cb554b5d6962f561b2a75778073461cf7836eb19d894d06005a98"
}
```

Repeat with the convexity, LP-duality, and Gaussian identities from `pct_e25b_trust_projection.json`. Bind the manifest to the exact v0.9 commit, workflow run, artifact id, and artifact digest frozen in the spec.

- [ ] **Step 4: Implement shared model validation**

`model.py` must define:

```python
LEVELS = ("C0", "C1", "C2", "C3", "C4", "C5")
ALLOWED_STATES = {"PASS", "FAIL", "NOT_APPLICABLE", "NOT_ESTABLISHED", "INVALID", "ERROR"}


def load_real_component_manifest() -> dict: ...
def validate_manifest(manifest: dict) -> dict: ...
```

`validate_manifest` rejects duplicate component ids, non-real provenance classes, missing source identity/hash/scope fields, and any source-artifact mismatch.

- [ ] **Step 5: Run manifest tests and verify GREEN**

Run: `python -m pytest -q experiments/pct_e25def/test_e25def.py -k manifest`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add experiments/pct_e25def evidence/pct_e25d_real_component_manifest.json
git commit -m "Add E25D real component manifest"
```

---

### Task 2: Implement E25D closure-vector atlas

**Files:**
- Create: `experiments/pct_e25def/atlas.py`
- Modify: `experiments/pct_e25def/test_e25def.py`
- Create: `evidence/pct_e25d_closure_atlas.json`

**Interfaces:**
- Consumes: `load_real_component_manifest()`, existing `run_e25c()` result, frozen E25B trust evidence.
- Produces: `evaluate_component(component: dict) -> dict`, `run_e25d() -> dict`.

- [ ] **Step 1: Add failing atlas tests**

```python
from experiments.pct_e25def.atlas import run_e25d


def test_e25d_assigns_complete_c0_c5_vectors():
    r = run_e25d()
    assert r["status"] == "PASS"
    assert r["real_components"] == 4
    assert r["synthetic_components_counted_as_real"] == 0
    assert all(set(x["closure"]) == {"C0", "C1", "C2", "C3", "C4", "C5"} for x in r["components"])


def test_existing_four_cycles_stop_at_c2_without_overclaiming():
    r = run_e25d()
    assert {x["closure_frontier"] for x in r["components"]} == {"C2"}
    for x in r["components"]:
        assert x["closure"]["C0"]["state"] == "PASS"
        assert x["closure"]["C1"]["state"] == "PASS"
        assert x["closure"]["C2"]["state"] == "PASS"
        assert x["closure"]["C3"]["state"] == "NOT_APPLICABLE"
        assert x["closure"]["C4"]["state"] == "NOT_APPLICABLE"
        assert x["closure"]["C5"]["state"] == "NOT_ESTABLISHED"
```

- [ ] **Step 2: Run atlas tests and verify RED**

Run: `python -m pytest -q experiments/pct_e25def/test_e25def.py -k e25d`

Expected: FAIL because `atlas.py` does not exist.

- [ ] **Step 3: Implement C0 and C1 recomputation**

For each manifest component, load the frozen trust projection and require:

```python
C0 = PASS only if anchor/EO/GEO/formal ids exist, source hashes agree, and the component has one source identity.
C1 = PASS only if C0 passed and the semantic/certificate bindings referenced by that component are present and PASS.
```

Do not copy the text of earlier verdicts as the decision source.

- [ ] **Step 4: Implement C2 binding to fresh E25C execution**

Call `run_e25c()` once. Index its cycles by contract. C2 passes only if contract, source hash, formal scope, and ids match the manifest and `all_paths_agree is True`.

- [ ] **Step 5: Implement C3–C5 applicability and gap records**

For the four scalar/decision contracts, emit:

```python
C3 = {"state": "NOT_APPLICABLE", "reason": "NO_EXPLICIT_CHAIN_MAP_CONTRACT"}
C4 = {"state": "NOT_APPLICABLE", "reason": "NO_INDUCED_HOMOLOGY_CONTRACT"}
C5 = {"state": "NOT_ESTABLISHED", "reason": "EXACT_MORPHISM_PROVENANCE_NOT_SERIALIZED"}
```

Every `PASS` must include an `evidence_refs` entry. Every non-pass state must include a reason.

- [ ] **Step 6: Generate deterministic atlas JSON and assert byte stability**

Serialize with `sort_keys=True`, compact separators, and trailing newline. Add a test that generates twice and compares exact strings.

- [ ] **Step 7: Run E25D tests and verify GREEN**

Run: `python -m pytest -q experiments/pct_e25def/test_e25def.py -k e25d`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add experiments/pct_e25def/atlas.py experiments/pct_e25def/test_e25def.py evidence/pct_e25d_closure_atlas.json
git commit -m "Add E25D closure depth atlas"
```

---

### Task 3: Implement E25E deterministic upgrade planner

**Files:**
- Create: `experiments/pct_e25def/planner.py`
- Modify: `experiments/pct_e25def/test_e25def.py`
- Create: `evidence/pct_e25e_upgrade_plan.json`

**Interfaces:**
- Consumes: `run_e25d() -> dict`.
- Produces: `classify_next_action(component: dict) -> dict`, `run_e25e() -> dict`.

- [ ] **Step 1: Add failing planner tests**

```python
from experiments.pct_e25def.planner import run_e25e


def test_e25e_assigns_exactly_one_priority_class_per_real_component():
    r = run_e25e()
    assert r["status"] == "PASS"
    assert len(r["queue"]) == 4
    assert len({x["component_id"] for x in r["queue"]}) == 4
    assert all(x["priority_class"] in {
        "P0_CONFLICT_REMEDIATION", "P1_EXECUTABLE_ADAPTER_READY",
        "P2_EVIDENCE_SERIALIZATION_GAP", "P3_CHAIN_OR_HOMOLOGY_MODEL_REQUIRED",
        "P4_EXACT_MORPHISM_PROVENANCE_REQUIRED", "P5_FORMALIZATION_OR_SCOPE_REQUIRED",
        "NO_ACTION_NOT_APPLICABLE_OR_COMPLETE"
    } for x in r["queue"])


def test_current_four_components_are_not_semantically_promoted():
    r = run_e25e()
    assert {x["priority_class"] for x in r["queue"]} == {"P4_EXACT_MORPHISM_PROVENANCE_REQUIRED"}
    assert all(x["expected_next_level"] == "C5" for x in r["queue"])
    assert all(x["semantic_promotion"] is False for x in r["queue"])
```

- [ ] **Step 2: Run planner tests and verify RED**

Run: `python -m pytest -q experiments/pct_e25def/test_e25def.py -k e25e`

Expected: FAIL because planner is absent.

- [ ] **Step 3: Implement lexicographic classification**

`classify_next_action` must inspect the closure vector in order and emit exactly one record with:

```python
{
    "component_id": ...,
    "priority_class": ...,
    "why_now": ...,
    "blocking_gap": ...,
    "required_inputs": [...],
    "expected_next_level": ...,
    "semantic_promotion": False,
}
```

Use the spec's P0→P5→NO_ACTION order exactly. Stable-sort the queue by priority rank then component id.

- [ ] **Step 4: Generate frozen planner JSON and byte-stability test**

Repeated calls must produce identical JSON bytes.

- [ ] **Step 5: Run planner tests and verify GREEN**

Run: `python -m pytest -q experiments/pct_e25def/test_e25def.py -k e25e`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add experiments/pct_e25def/planner.py experiments/pct_e25def/test_e25def.py evidence/pct_e25e_upgrade_plan.json
git commit -m "Add E25E verification upgrade planner"
```

---

### Task 4: Implement E25F C0–C5 first-capable-layer fault matrix

**Files:**
- Create: `experiments/pct_e25def/fault_matrix.py`
- Modify: `experiments/pct_e25def/test_e25def.py`
- Create: `evidence/pct_e25f_fault_coverage.json`

**Interfaces:**
- Consumes: E25B/C trust evidence plus exact synthetic correspondence controls internal to this module.
- Produces: `run_e25f() -> dict`.

- [ ] **Step 1: Add failing fault-matrix tests**

```python
from experiments.pct_e25def.fault_matrix import run_e25f


def test_e25f_covers_every_layer_exactly_once_or_more():
    r = run_e25f()
    assert r["status"] == "PASS"
    assert {x["expected_first_detector"] for x in r["faults"]} == {"C0", "C1", "C2", "C3", "C4", "C5"}
    assert all(x["observed_first_detector"] == x["expected_first_detector"] for x in r["faults"])
    assert all(x["false_positive_before_expected"] is False for x in r["faults"])
    assert all(x["missed_at_expected"] is False for x in r["faults"])


def test_e25f_controls_are_never_real_repository_evidence():
    r = run_e25f()
    assert {x["provenance_class"] for x in r["faults"]} == {"SYNTHETIC_CONTROL"}
```

- [ ] **Step 2: Run fault tests and verify RED**

Run: `python -m pytest -q experiments/pct_e25def/test_e25def.py -k e25f`

Expected: FAIL because `fault_matrix.py` is absent.

- [ ] **Step 3: Implement C0–C2 controls using E25BC semantics**

Construct deterministic synthetic copies where:

```text
C0: source anchor/hash is swapped while all later payloads are left untouched.
C1: identity stays correct but the bound certificate is missing/FAIL.
C2: identity and certificates stay correct but one EO/GEO/formal executable result is mutated.
```

Execute layers in order and stop at the first failure.

- [ ] **Step 4: Implement exact C3 chain-map corruption control**

Use the oriented three-edge circle to six-edge subdivision control from E5. Flip one entry in `F1` and require:

```python
Dt * F1_bad != F0 * Ds
```

C0–C2 synthetic metadata must remain valid; C3 is the first detector.

- [ ] **Step 5: Implement exact C4 induced-homology control**

Add a target cycle to one edge image so `Dt * F1 == F0 * Ds` still holds but the induced H1 degree changes from +1 to +2. Require C3 PASS and C4 FAIL.

- [ ] **Step 6: Implement exact C5 provenance-only control**

Add cycle injections with coefficients `(1, -1, 0)` so the map remains a chain map and the induced H1 degree remains +1, but its exact edge-image matrix differs from the declared subdivision map. Require C0–C4 PASS and C5 FAIL.

- [ ] **Step 7: Build first-detector table and frozen JSON**

Each fault record must include states for C0–C5, `expected_first_detector`, `observed_first_detector`, `false_positive_before_expected`, and `missed_at_expected`.

- [ ] **Step 8: Run E25F tests and verify GREEN**

Run: `python -m pytest -q experiments/pct_e25def/test_e25def.py -k e25f`

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add experiments/pct_e25def/fault_matrix.py experiments/pct_e25def/test_e25def.py evidence/pct_e25f_fault_coverage.json
git commit -m "Add E25F layered fault coverage matrix"
```

---

### Task 5: Add integrated report generation and CI regression

**Files:**
- Create: `experiments/pct_e25def/report.py`
- Modify: `experiments/pct_e25def/test_e25def.py`
- Create: `docs/PCT_E25D_E25F_CLOSURE_PROGRAM_REPORT.md`
- Modify: `.github/workflows/pct-e1-e25-campaign.yml`

**Interfaces:**
- Consumes: `run_e25d()`, `run_e25e()`, `run_e25f()`.
- Produces: `build_report() -> str`, frozen report Markdown, CI coverage.

- [ ] **Step 1: Add failing integration tests**

```python
from experiments.pct_e25def.report import build_report


def test_report_contains_real_coverage_and_synthetic_boundary():
    text = build_report()
    assert "4 real source-bound components" in text
    assert "synthetic controls do not count as repository closure" in text.lower()
    assert "C0" in text and "C5" in text


def test_frozen_outputs_match_fresh_execution():
    # Load each evidence JSON and compare exactly with fresh run_* output.
    ...
```

Replace the ellipsis in the real test with explicit JSON loads and equality assertions for all E25D/E/F files.

- [ ] **Step 2: Run integrated tests and verify RED**

Run: `python -m pytest -q experiments/pct_e25def/test_e25def.py`

Expected: FAIL because `report.py` and frozen report do not exist.

- [ ] **Step 3: Implement deterministic Markdown report**

Include:

```text
- source artifact identity
- real component count
- closure-frontier histogram
- per-component closure vectors
- E25E ordered upgrade queue
- E25F first-capable-layer matrix
- provenance correction distinguishing real vs synthetic
- claim boundary
```

Do not state that the twenty synthetic E25B triangles are real repository trust components.

- [ ] **Step 4: Extend the existing workflow**

Add `experiments/pct_e25def/**`, the four new evidence files, the report, and the spec/plan paths to the workflow path filters. Extend static compilation with:

```bash
python -m compileall -q experiments/pct_e25def
```

Extend pytest with:

```bash
python -m pytest -q experiments/pct_e1_e25/test_campaign.py experiments/pct_e25bc/test_audit.py experiments/pct_e25def/test_e25def.py
```

- [ ] **Step 5: Run complete local-equivalent test command**

Run the same pytest command as CI. Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add experiments/pct_e25def docs/PCT_E25D_E25F_CLOSURE_PROGRAM_REPORT.md .github/workflows/pct-e1-e25-campaign.yml
git commit -m "Integrate E25D-E25F closure verification program"
```

---

### Task 6: CI verification and fail-closed result review

**Files:**
- No new implementation files unless CI exposes a reproducible defect.

**Interfaces:**
- Consumes: branch CI run for the final implementation commit.
- Produces: verified branch state only; no acceptance promotion to `main`.

- [ ] **Step 1: Push/update `agent/pct-computational-architecture` and wait for the workflow**

Expected workflow: `MAPEOGEO PCT E1-E25C campaign regression` with the extended E25D/E/F paths/tests.

- [ ] **Step 2: If CI fails, inspect the exact failing job/step/log before changing code**

Use systematic debugging: identify root cause, reproduce from logs, make the smallest correction, rerun.

- [ ] **Step 3: Verify final CI evidence**

Required:

```text
checkout PASS
setup-python PASS
install dependencies PASS
static compilation PASS
full PCT pytest suite PASS
```

- [ ] **Step 4: Confirm branch-only scope**

Verify the head branch remains `agent/pct-computational-architecture`; do not merge, open a PR, modify `main`, or add README claim promotion.

- [ ] **Step 5: Final result statement**

Report exact commit SHA, CI run id, total passing tests, E25D closure distribution, E25E queue distribution, E25F detector coverage, and any remaining C3–C5 gaps on real components.
