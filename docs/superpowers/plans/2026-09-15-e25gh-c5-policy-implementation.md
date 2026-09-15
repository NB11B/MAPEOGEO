# E25G–E25H C5 Exact-Morphism and Provenance Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build exact witness-bearing C5a adapters and provenance-bound C5b records for the four real source-bound contracts, then compare strict and permissive C5 policies against preregistered adversarial controls.

**Architecture:** Extend the isolated PCT experiment surface with independent EO/GEO/FORMAL witness generators, canonical serialization/comparison, provenance bindings, policy evaluation, and contract-specific adversaries. No production ontology or semantic edge is mutated. Frozen JSON evidence is generated from fresh execution and checked byte-for-byte in regression tests.

**Tech Stack:** Python 3.12, pytest, fractions.Fraction, SymPy exact symbolic algebra, hashlib/json canonical serialization, existing PCT E25D/E25F evidence and CI workflow.

**Spec:** `docs/superpowers/specs/2026-09-15-e25gh-c5-policy-design.md`

## Global Constraints

- Work only on `agent/pct-computational-architecture`; do not merge to `main`.
- C5a and C5b are independent subgates; governing C5 policy is `STRICT_AND`.
- EO/GEO/FORMAL witness routes must compute their mathematical records independently; they may share only canonical serialization/comparison helpers.
- No floating tolerance is permitted in exact C5a equality.
- Synthetic adversaries may validate detector policy but may never promote real component closure.
- E25G/H may emit `strict_c5_eligible=true`; they must not rewrite the E25D atlas or semantic graph.
- Missing witness or provenance data is fail-closed (`NOT_ESTABLISHED` or `FAIL`), never inferred `PASS`.

---

### Task 1: Independent exact-morphism adapters

**Files:**
- Create: `experiments/pct_e25gh/__init__.py`
- Create: `experiments/pct_e25gh/morphisms.py`
- Create: `experiments/pct_e25gh/test_e25gh.py`

**Interfaces:**
- Produces: `run_c5a_audit() -> dict`
- Produces: contract route functions returning canonical Python records for `rank`, `convex`, `lp`, and `gauss`.
- Produces: `canonical_json(value) -> str` and exact equality helpers used by later tasks.

- [ ] **Step 1: Write failing tests for independent witness equality**

Add tests asserting:

```python
from experiments.pct_e25gh.morphisms import run_c5a_audit


def test_c5a_all_four_real_contracts_agree_exactly():
    result = run_c5a_audit()
    assert result["status"] == "PASS"
    assert result["component_count"] == 4
    assert all(c["all_routes_agree"] for c in result["components"])
    assert sum(c["inputs_tested"] for c in result["components"]) > 3000


def test_lp_c5a_preserves_all_active_minimizers():
    result = run_c5a_audit()
    lp = next(c for c in result["components"] if c["contract"] == "lp")
    assert lp["tie_case_count"] > 0
    assert lp["all_active_minimizers_preserved"] is True
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest -q experiments/pct_e25gh/test_e25gh.py -k 'c5a or active_minimizers'
```

Expected: collection/import failure because `morphisms.py` does not exist.

- [ ] **Step 3: Implement canonical serialization only**

Implement:

```python
def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
```

Canonicalize `Fraction` as `[numerator, denominator]` and GF(2) vectors/matrices as integer lists.

- [ ] **Step 4: Implement three independent routes per contract**

Implement separate EO/GEO/FORMAL functions for each contract. Do not route them through one mathematical witness helper.

Rank route records must include:

```python
{
    "matrix": ...,
    "rank": ...,
    "rref": ...,
    "pivot_columns": ...,
    "nullity": ...,
    "canonical_nullspace_basis": ...,
}
```

Convexity records must include exact membership and barycentric/separation witnesses. LP records must include all minimizers in `active_indices` and exact active witnesses. Gaussian records must include coefficient vector `[-1/2,-1/2,1]` plus normalized symbolic expression.

- [ ] **Step 5: Run C5a tests to verify GREEN**

Run:

```bash
python -m pytest -q experiments/pct_e25gh/test_e25gh.py -k 'c5a or active_minimizers'
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add experiments/pct_e25gh

git commit -m "feat: add independent E25G exact morphism adapters"
```

---

### Task 2: Provenance-bound C5b records

**Files:**
- Create: `experiments/pct_e25gh/provenance.py`
- Modify: `experiments/pct_e25gh/test_e25gh.py`

**Interfaces:**
- Consumes: E25D real component manifest and canonical serializer from Task 1.
- Produces: `run_c5b_audit() -> dict`
- Produces: `build_provenance_record(component, adapter_id, adapter_sha256) -> dict`

- [ ] **Step 1: Write failing provenance tests**

```python
from experiments.pct_e25gh.provenance import run_c5b_audit


def test_c5b_binds_every_real_component_to_source_and_adapter():
    result = run_c5b_audit()
    assert result["status"] == "PASS"
    assert result["component_count"] == 4
    for c in result["components"]:
        assert c["provenance_state"] == "PASS"
        assert len(c["provenance_sha256"]) == 64
        assert c["source_statement_sha256"]
        assert c["formal_scope"]
        assert c["certificate_ids"]
        assert c["adapter_sha256"]
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest -q experiments/pct_e25gh/test_e25gh.py -k c5b
```

Expected: import failure for missing `provenance.py`.

- [ ] **Step 3: Implement deterministic provenance binding**

Bind exactly:

```text
component_id
source_statement_sha256
contract
formal_scope
source_artifact_digest
source_commit_sha
eo_id
geo_id
formal_id
certificate_ids
adapter_id
adapter_sha256
predecessor_evidence_ids
```

Compute `provenance_sha256 = sha256(canonical_json(record).encode()).hexdigest()`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python -m pytest -q experiments/pct_e25gh/test_e25gh.py -k c5b
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add experiments/pct_e25gh/provenance.py experiments/pct_e25gh/test_e25gh.py

git commit -m "feat: bind E25G morphisms to exact provenance"
```

---

### Task 3: Adversarial C5 policy comparison

**Files:**
- Create: `experiments/pct_e25gh/adversaries.py`
- Create: `experiments/pct_e25gh/policies.py`
- Modify: `experiments/pct_e25gh/test_e25gh.py`

**Interfaces:**
- Consumes: C5a and C5b valid records.
- Produces: `run_e25h_policy_comparison() -> dict`
- Produces policies: `STRICT_AND`, `MAP_ONLY`, `PROVENANCE_ONLY`, `ANY_AXIS`.

- [ ] **Step 1: Write failing policy tests**

```python
from experiments.pct_e25gh.policies import run_e25h_policy_comparison


def test_strict_policy_has_zero_false_accepts():
    result = run_e25h_policy_comparison()
    strict = result["policies"]["STRICT_AND"]
    assert strict["false_accepts"] == 0
    assert strict["valid_rejects"] == 0


def test_single_axis_policies_are_exposed_by_axis_specific_faults():
    result = run_e25h_policy_comparison()
    assert result["policies"]["MAP_ONLY"]["false_accepts"] > 0
    assert result["policies"]["PROVENANCE_ONLY"]["false_accepts"] > 0
    assert result["policies"]["ANY_AXIS"]["false_accepts"] >= max(
        result["policies"]["MAP_ONLY"]["false_accepts"],
        result["policies"]["PROVENANCE_ONLY"]["false_accepts"],
    )


def test_every_contract_has_both_single_axis_fault_classes():
    result = run_e25h_policy_comparison()
    for contract in result["contracts"]:
        cases = {x["fault_class"] for x in contract["adversarial_cases"]}
        assert "CORRECT_MAP_WRONG_PROVENANCE" in cases
        assert "WRONG_MAP_CORRECT_PROVENANCE" in cases
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest -q experiments/pct_e25gh/test_e25gh.py -k 'policy or single_axis or fault_classes'
```

Expected: import failure for missing policy modules.

- [ ] **Step 3: Implement adversaries**

For each contract produce at least:

```text
CORRECT_MAP_WRONG_PROVENANCE
WRONG_MAP_CORRECT_PROVENANCE
SAME_ENDPOINT_WRONG_WITNESS
CORRECT_LINEAGE_ALTERED_TRANSFORMATION
EXACT_MAP_COPIED_ACROSS_IDENTITIES
```

Keep C5a and C5b expected states explicit on every case.

- [ ] **Step 4: Implement policy evaluator**

```python
POLICIES = {
    "STRICT_AND": lambda a, b: a and b,
    "MAP_ONLY": lambda a, b: a,
    "PROVENANCE_ONLY": lambda a, b: b,
    "ANY_AXIS": lambda a, b: a or b,
}
```

Record valid accepts/rejects, false accepts/rejects, rates, and per-contract results.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
python -m pytest -q experiments/pct_e25gh/test_e25gh.py -k 'policy or single_axis or fault_classes'
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add experiments/pct_e25gh

git commit -m "test: compare strict and permissive C5 policies"
```

---

### Task 4: Frozen E25G/H evidence and C5 eligibility

**Files:**
- Create: `evidence/pct_e25g_exact_morphism_audit.json`
- Create: `evidence/pct_e25g_provenance_bindings.json`
- Create: `evidence/pct_e25h_policy_comparison.json`
- Modify: `experiments/pct_e25gh/test_e25gh.py`

**Interfaces:**
- Consumes: fresh execution from Tasks 1–3.
- Produces: deterministic evidence files.

- [ ] **Step 1: Add failing frozen-evidence tests**

```python
def test_frozen_e25gh_evidence_matches_fresh_execution():
    root = Path(__file__).resolve().parents[2]
    assert json.loads((root / "evidence/pct_e25g_exact_morphism_audit.json").read_text()) == run_c5a_audit()
    assert json.loads((root / "evidence/pct_e25g_provenance_bindings.json").read_text()) == run_c5b_audit()
    assert json.loads((root / "evidence/pct_e25h_policy_comparison.json").read_text()) == run_e25h_policy_comparison()


def test_strict_c5_eligibility_requires_both_component_and_policy_success():
    result = run_e25h_policy_comparison()
    assert result["strict_policy_acceptable"] is True
    assert all(c["strict_c5_eligible"] for c in result["contracts"])
```

- [ ] **Step 2: Run RED**

Run:

```bash
python -m pytest -q experiments/pct_e25gh/test_e25gh.py -k 'frozen or eligibility'
```

Expected: fail because evidence files do not yet exist.

- [ ] **Step 3: Generate canonical JSON evidence**

Serialize with `sort_keys=True`, compact separators, newline at EOF. Do not hand-edit result fields.

- [ ] **Step 4: Run GREEN**

Run:

```bash
python -m pytest -q experiments/pct_e25gh/test_e25gh.py
```

Expected: all E25G/H tests PASS.

- [ ] **Step 5: Commit**

```bash
git add evidence/pct_e25g_* evidence/pct_e25h_* experiments/pct_e25gh/test_e25gh.py

git commit -m "evidence: freeze E25G E25H C5 audit results"
```

---

### Task 5: Human-readable report and CI integration

**Files:**
- Create: `docs/PCT_E25G_E25H_C5_POLICY_REPORT.md`
- Modify: `.github/workflows/pct-e1-e25-campaign.yml`

**Interfaces:**
- Consumes: frozen E25G/H evidence.
- Produces: report and CI regression coverage.

- [ ] **Step 1: Extend CI paths and commands**

Add `experiments/pct_e25gh/**`, the three E25G/H evidence files, and the report path to push/pull-request filters. Add:

```bash
python -m compileall -q experiments/pct_e25gh
```

and add `experiments/pct_e25gh/test_e25gh.py` to the pytest command.

- [ ] **Step 2: Write report from frozen evidence**

Report per-contract C5a/C5b status and per-policy false accept/reject counts. Explicitly state whether `STRICT_AND` is empirically justified or whether a single-axis policy survives all preregistered adversaries.

- [ ] **Step 3: Run full regression**

Run:

```bash
python -m pytest -q \
  experiments/pct_e1_e25/test_campaign.py \
  experiments/pct_e25bc/test_audit.py \
  experiments/pct_e25def/test_e25def.py \
  experiments/pct_e25gh/test_e25gh.py
```

Expected: 0 failures.

- [ ] **Step 4: Static compile check**

Run:

```bash
python -m py_compile experiments/pct_e1_e25/campaign.py experiments/pct_e1_e25/test_campaign.py
python -m compileall -q experiments/pct_e25bc experiments/pct_e25def experiments/pct_e25gh
```

Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/pct-e1-e25-campaign.yml docs/PCT_E25G_E25H_C5_POLICY_REPORT.md

git commit -m "ci: verify E25G E25H C5 policy campaign"
```

---

### Task 6: Branch-level verification and completion gate

**Files:**
- No new production files.

**Interfaces:**
- Consumes: entire branch state.
- Produces: verified development-branch status only; no merge/PR unless user later requests it.

- [ ] **Step 1: Verify GitHub Actions on branch head**

Confirm workflow `MAPEOGEO PCT E1-E25H campaign regression` runs on the exact branch-head SHA and concludes `success`.

- [ ] **Step 2: Read CI logs**

Verify static compilation and the full pytest suite both completed with zero failures. Record exact test count.

- [ ] **Step 3: Verify evidence files at branch head**

Fetch all three frozen JSON files and confirm the report's aggregate numbers match them exactly.

- [ ] **Step 4: Stop before integration**

Keep `agent/pct-computational-architecture` isolated. Do not merge to `main`, create a PR, or mutate semantic graph state without a new explicit user request.
