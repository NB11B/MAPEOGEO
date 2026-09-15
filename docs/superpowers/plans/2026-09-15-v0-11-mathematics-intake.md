# MAPEOGEO v0.11 Mathematics Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote the four graph-selected v0.9 pinch nodes through a source-bound, fail-closed intake cycle that preserves detector history, records explicit computational or `UNTESTED` state, attempts scoped Lean formalization for every auditable scope, and emits graph/certificate/wound artifacts without changing the MAPEOGEO architecture.

**Architecture:** v0.11 consumes the accepted v0.9 graph as its base. It regenerates and hash-checks the four source declarations, freezes a per-node source-audited formal scope before scientific execution, preserves EO/GEO detector output unchanged, runs only preregistered executable contracts where justified, attempts Lean formalization, and extends the graph only with evidence actually earned. PCT v0.10 remains an optional S3 provider and is not a dependency of this plan.

**Tech Stack:** Python 3.12; `pytest>=8,<9`; existing PyMuPDF/SymPy ingestion stack; Lean `leanprover/lean4:v4.33.1`; Mathlib `v4.33.1`; GitHub Actions `ubuntu-latest`; local Windows verification through the same pinned repository toolchain.

**Spec:** `docs/superpowers/specs/2026-09-15-v0-11-mathematics-intake-design.md`

## Global Constraints

- Work only on `agent/math-intake-v0-11` until v0.11 acceptance is sealed.
- Frozen source identities are:
  - `srcdecl:proposition:3_14` — `6e09e18756aefdaf8cdd2c03aca61548d1126fb3d30d70b49c58359f37c64b8e`
  - `srcdecl:proposition:3_13` — `0eef6ce3b699ddef7c209eb28b500b75aab07d9e540b7746b631f8db653addac`
  - `srcdecl:theorem:27_10` — `d205d7c5313b841e6afafc9d619fa059dfe50a2f6c11a48ca2cff466cc84d4fa`
  - `srcdecl:proposition:4_4` — `37e5dc6afdbd3d026c4f7ef71c3531fc74eaeb04bf21ed45c4a9add39fcb6ecf`
- Historical direct-view states remain immutable: 3.14 EO-only, 3.13 EO-only, 27.10 dual-direct, 4.4 EO-only.
- Only explicit source references become source `DEPENDS_ON` edges.
- Formal/library prerequisites are metadata, not invented source citations.
- Every accepted node finishes with explicit `Test` state: scoped executable/PCT contract, `KERNEL_VERIFIED`, or `UNTESTED`.
- `DUAL_CANDIDATE`, `EQUIVALENT_TO`, `SAME_SEMANTICS`, `KERNEL_VERIFIED`, `KERNEL_ACCEPTED_PATH`, `WOUND`, and `UNTESTED` remain distinct.
- Lean success cannot create or rewrite EO/GEO detector evidence.
- No accepted Lean source may contain `sorry`, `admit`, a custom `axiom`, or an `unsafe` declaration.
- Source prose/page images are transient only and never enter repository or CI artifacts.
- Existing v0.6/v0.7 routing metrics are carried forward as historical values; v0.11 does not tune them.
- A refused or failed formalization is valid scientific output and leaves the source node unpromoted.

## File Structure

Create or modify:

```text
formal/pinch_bindings_v0_11.json
MAPEOGEOFormal/PinchV011.lean
MAPEOGEOFormal.lean
scripts/audit_pinch_source_v0_11.py
scripts/pinch_contracts_v0_11.py
scripts/pinch_intake_v0_11.py
scripts/local_verify_v0_11.ps1
tests/test_pinch_source_audit_v0_11.py
tests/test_pinch_intake_v0_11.py
tests/validate_pinch_intake_v0_11.py
evidence/v0_11_preregistration.json
docs/V0_11_MATHEMATICS_INTAKE_SPEC.md
.github/workflows/math-intake-v0-11.yml
```

Create only after an accepted CI artifact exists:

```text
evidence/v0_11_acceptance_manifest.json
docs/V0_11_MATHEMATICS_INTAKE_REPORT.md
README.md
```

Do not edit `MAPEOGEOFormal/SourceBound.lean` or `MAPEOGEOFormal/ProofPaths.lean`.

---

### Task 1: Freeze identities, dependency expectations, and intake-state schema

**Files:**
- Create: `formal/pinch_bindings_v0_11.json`
- Create: `evidence/v0_11_preregistration.json`
- Create: `docs/V0_11_MATHEMATICS_INTAKE_SPEC.md`
- Create: `tests/test_pinch_source_audit_v0_11.py`

**Interfaces:**
- Binding record fields: `source_id`, `statement_sha256`, `expected_direct_status`, `explicit_dependencies`, `formal_decl`, `formal_scope`, `scope_status`, `s3_test_state`, `s3_contract_id`, `s3_scope`.
- Allowed `scope_status`: `FROZEN`, `REFUSED_SCOPE_MISMATCH`.
- Allowed `s3_test_state`: `EXECUTABLE_CONTRACT`, `PCT_CONTRACT`, `UNTESTED`.

- [ ] **Step 1: Write the failing identity test**

```python
import json
from pathlib import Path

FROZEN = {
    "srcdecl:proposition:3_14": "6e09e18756aefdaf8cdd2c03aca61548d1126fb3d30d70b49c58359f37c64b8e",
    "srcdecl:proposition:3_13": "0eef6ce3b699ddef7c209eb28b500b75aab07d9e540b7746b631f8db653addac",
    "srcdecl:theorem:27_10": "d205d7c5313b841e6afafc9d619fa059dfe50a2f6c11a48ca2cff466cc84d4fa",
    "srcdecl:proposition:4_4": "37e5dc6afdbd3d026c4f7ef71c3531fc74eaeb04bf21ed45c4a9add39fcb6ecf",
}


def test_v011_bindings_freeze_exact_quartet():
    cfg = json.loads(Path("formal/pinch_bindings_v0_11.json").read_text(encoding="utf-8"))
    assert {x["source_id"]: x["statement_sha256"] for x in cfg["targets"]} == FROZEN
    assert len(cfg["targets"]) == 4
    for item in cfg["targets"]:
        assert item["s3_test_state"] in {"EXECUTABLE_CONTRACT", "PCT_CONTRACT", "UNTESTED"}
        assert item["scope_status"] in {"FROZEN", "REFUSED_SCOPE_MISMATCH"}
```

- [ ] **Step 2: Run and confirm failure**

Run: `python -m pytest -q tests/test_pinch_source_audit_v0_11.py::test_v011_bindings_freeze_exact_quartet`

Expected: FAIL because the binding file does not yet exist.

- [ ] **Step 3: Create the initial bindings**

Use these explicit dependency expectations from accepted v0.9:

```python
EXPECTED_DEPS = {
    "srcdecl:proposition:3_14": ["srcdecl:proposition:3_13", "srcdecl:proposition:4_4"],
    "srcdecl:proposition:3_13": ["srcdecl:proposition:3_21", "srcdecl:proposition:2_2", "srcdecl:proposition:2_3", "srcdecl:proposition:4_4"],
    "srcdecl:theorem:27_10": ["srcdecl:theorem:6_16"],
    "srcdecl:proposition:4_4": ["srcdecl:proposition:4_3"],
}
```

Initial formal scope is refused until source audit:

```text
formal_scope = SOURCE_AUDIT_REQUIRED_BEFORE_EXECUTION
scope_status = REFUSED_SCOPE_MISMATCH
s3_test_state = UNTESTED
s3_contract_id = null
s3_scope = null
```

Fixed declaration names are:

```text
MAPEOGEOFormal.proposition_3_14_v011
MAPEOGEOFormal.proposition_3_13_v011
MAPEOGEOFormal.theorem_27_10_v011
MAPEOGEOFormal.proposition_4_4_v011
```

- [ ] **Step 4: Create the preregistration record**

Freeze the four identities, historical detector states, dependency expectations, Lean/Mathlib versions, proof-escape policy, graph-integrity rules, and fail-closed acceptance law. Do not record expected result counts.

- [ ] **Step 5: Run tests**

Run: `python -m pytest -q tests/test_pinch_source_audit_v0_11.py`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add formal/pinch_bindings_v0_11.json evidence/v0_11_preregistration.json docs/V0_11_MATHEMATICS_INTAKE_SPEC.md tests/test_pinch_source_audit_v0_11.py
git commit -m "Preregister v0.11 pinch mathematics intake"
```

---

### Task 2: Audit the current source and freeze faithful formal scopes before any result run

**Files:**
- Create: `scripts/audit_pinch_source_v0_11.py`
- Modify: `formal/pinch_bindings_v0_11.json`
- Modify: `evidence/v0_11_preregistration.json`
- Modify: `tests/test_pinch_source_audit_v0_11.py`

**Interfaces:**
- `audit_targets(graph: dict, bindings: dict) -> dict`
- CLI accepts source PDF, regenerated graph, bindings, and output path.
- Serialized audit output is metadata-only: source ID/hash/page locator/character counts/direct status/dependency IDs/scope state/test state.

- [ ] **Step 1: Write failing audit tests**

```python
from scripts.audit_pinch_source_v0_11 import audit_targets


def test_audit_accepts_frozen_identity_and_dependencies(sample_graph, sample_bindings):
    result = audit_targets(sample_graph, sample_bindings)
    assert result["all_hashes_match"] is True
    assert result["all_direct_states_match"] is True
    assert result["all_explicit_dependencies_present"] is True


def test_audit_rejects_hash_drift(sample_graph, sample_bindings):
    sample_bindings["targets"][0]["statement_sha256"] = "0" * 64
    assert audit_targets(sample_graph, sample_bindings)["all_hashes_match"] is False
```

- [ ] **Step 2: Run and confirm failure**

Run: `python -m pytest -q tests/test_pinch_source_audit_v0_11.py`

Expected: FAIL because the audit module does not exist.

- [ ] **Step 3: Implement metadata-only auditing**

Core logic:

```python
def audit_targets(graph, bindings):
    by_id = {n["id"]: n for n in graph["nodes"]}
    dep_map = {}
    for edge in graph["edges"]:
        if edge.get("type") == "DEPENDS_ON":
            dep_map.setdefault(edge["source"], set()).add(edge["target"])

    rows = []
    for target in bindings["targets"]:
        node = by_id.get(target["source_id"])
        profile = None if node is None else node.get("attributes", {}).get("independent_profile", {})
        rows.append({
            "source_id": target["source_id"],
            "hash_match": bool(profile) and profile.get("statement_sha256") == target["statement_sha256"],
            "direct_state_match": bool(profile) and profile.get("direct_status") == target["expected_direct_status"],
            "dependencies_present": set(target["explicit_dependencies"]) <= dep_map.get(target["source_id"], set()),
        })
    return {
        "targets": rows,
        "all_hashes_match": all(r["hash_match"] for r in rows),
        "all_direct_states_match": all(r["direct_state_match"] for r in rows),
        "all_explicit_dependencies_present": all(r["dependencies_present"] for r in rows),
    }
```

- [ ] **Step 4: Regenerate the accepted source graph and run the audit**

Use the existing v0.6/v0.7 regeneration path against the current source PDF. Stop immediately if any frozen hash/direct state/dependency check fails.

- [ ] **Step 5: Inspect the exact four source statements transiently and freeze scope decisions**

For each node, choose the narrowest faithful formal scope from the current PDF. Store only an independently authored uppercase scope identifier and a short independently written scope description. Do not store copied source prose.

Decision law:

```text
faithful source-level or explicitly narrower formal statement available -> scope_status FROZEN
no faithful scope without changing the source claim -> scope_status REFUSED_SCOPE_MISMATCH
```

- [ ] **Step 6: Freeze S3 selection before execution**

Choose exactly one per target:

```text
EXECUTABLE_CONTRACT  when an exact/scoped computational contract is justified
PCT_CONTRACT         only when PCT is merged and its applicability contract is satisfied
UNTESTED             otherwise
```

No node requires an S3 contract in order to proceed to S4.

- [ ] **Step 7: Commit the scope/test freeze before formal execution**

Run source-audit tests again, then commit the audited binding file and preregistration amendment. Record that commit SHA as the v0.11 scope-freeze commit.

---

### Task 3: Implement the four scoped Lean candidates or explicit refusals

**Files:**
- Create: `MAPEOGEOFormal/PinchV011.lean`
- Modify: `MAPEOGEOFormal.lean`
- Create: `tests/test_pinch_intake_v0_11.py`

**Interfaces:**
- A target with `scope_status=FROZEN` must have its fixed declaration name in `PinchV011.lean`.
- A target with `scope_status=REFUSED_SCOPE_MISMATCH` must not receive a substitute theorem.

- [ ] **Step 1: Write failing Lean-policy tests**

```python
import json
from pathlib import Path
from scripts.formal_bridge_v0_8 import proof_escape_hits


def test_v011_lean_file_has_no_escape_hatches():
    text = Path("MAPEOGEOFormal/PinchV011.lean").read_text(encoding="utf-8")
    assert proof_escape_hits(text) == []


def test_all_frozen_scopes_have_fixed_decl_names():
    cfg = json.loads(Path("formal/pinch_bindings_v0_11.json").read_text(encoding="utf-8"))
    text = Path("MAPEOGEOFormal/PinchV011.lean").read_text(encoding="utf-8")
    expected = [x["formal_decl"].split(".")[-1] for x in cfg["targets"] if x["scope_status"] == "FROZEN"]
    assert all(name in text for name in expected)
```

- [ ] **Step 2: Run and confirm failure**

Run: `python -m pytest -q tests/test_pinch_intake_v0_11.py`

Expected: FAIL because `PinchV011.lean` does not exist.

- [ ] **Step 3: Write each frozen theorem from the already-committed Task-2 scope record**

Every theorem must include only source ID, source statement hash, and the independently authored formal-scope identifier in its doc comment. The theorem statement must implement exactly the scope that was frozen before this task. Use Mathlib lemmas freely, but do not broaden or narrow the scope after observing proof difficulty.

- [ ] **Step 4: Add `#print axioms` for every implemented declaration**

Accepted output may contain standard Lean/Mathlib axioms such as `propext`, `Classical.choice`, and `Quot.sound`; it must not contain `sorryAx` or a project-defined axiom.

- [ ] **Step 5: Import the new file at the library root**

`MAPEOGEOFormal.lean` becomes:

```lean
import MAPEOGEOFormal.SourceBound
import MAPEOGEOFormal.ProofPaths
import MAPEOGEOFormal.PinchV011
```

- [ ] **Step 6: Run direct local verification**

```powershell
lake env lean MAPEOGEOFormal\PinchV011.lean
lake build
python -m pytest -q tests/test_pinch_intake_v0_11.py
```

Expected: every frozen declaration compiles; every refusal remains explicit in bindings rather than being replaced by a weaker theorem.

- [ ] **Step 7: Commit**

```bash
git add MAPEOGEOFormal/PinchV011.lean MAPEOGEOFormal.lean tests/test_pinch_intake_v0_11.py
git commit -m "Add v0.11 pinch formal candidates"
```

---

### Task 4: Implement explicit S3 state without forcing computational coverage

**Files:**
- Create: `scripts/pinch_contracts_v0_11.py`
- Modify: `tests/test_pinch_intake_v0_11.py`

**Interfaces:**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ContractResult:
    source_id: str
    contract_id: str | None
    test_state: str
    applicability: str
    verdict: str
    scope: str | None
    measured: dict
    refused: tuple[str, ...]


def run_contract(target: dict) -> ContractResult:
    ...
```

`run_contract` behavior is fully determined by the Task-2-frozen binding record.

- [ ] **Step 1: Write failing state tests**

```python
from scripts.pinch_contracts_v0_11 import run_contract


def test_untested_is_not_pass():
    result = run_contract({
        "source_id": "srcdecl:proposition:3_14",
        "s3_test_state": "UNTESTED",
        "s3_contract_id": None,
        "s3_scope": None,
    })
    assert result.verdict == "UNTESTED"
    assert result.refused


def test_unknown_contract_is_invalid():
    result = run_contract({
        "source_id": "synthetic:test",
        "s3_test_state": "EXECUTABLE_CONTRACT",
        "s3_contract_id": "UNKNOWN_CONTRACT",
        "s3_scope": "SYNTHETIC",
    })
    assert result.verdict == "INVALID"
```

- [ ] **Step 2: Run and confirm failure**

Run: `python -m pytest -q tests/test_pinch_intake_v0_11.py`

Expected: FAIL because the contract module does not exist.

- [ ] **Step 3: Implement `UNTESTED`, `PCT_CONTRACT`, and explicit contract dispatch**

`UNTESTED` returns `verdict="UNTESTED"`, `applicability="NOT_RUN"`, empty measurements, and a nonempty refusal list. `PCT_CONTRACT` returns `NOT_APPLICABLE` unless the exact frozen PCT applicability contract is available and satisfied. `EXECUTABLE_CONTRACT` dispatches only to contract IDs already frozen in Task 2.

- [ ] **Step 4: Implement only the contracts actually frozen in Task 2**

Each implemented contract gets deterministic inputs, exact arithmetic when mathematical structure permits, one positive unit test, one mutation/negative control, an explicit domain, and an explicit statement of what remains untested.

- [ ] **Step 5: Run tests and commit**

```bash
python -m pytest -q tests/test_pinch_intake_v0_11.py
git add scripts/pinch_contracts_v0_11.py tests/test_pinch_intake_v0_11.py
git commit -m "Add scoped v0.11 computational test states"
```

---

### Task 5: Implement the sole v0.11 graph mutator and state-transition report

**Files:**
- Create: `scripts/pinch_intake_v0_11.py`
- Modify: `tests/test_pinch_intake_v0_11.py`

**Interfaces:**

```text
python scripts/pinch_intake_v0_11.py \
  --base-graph BASE_GRAPH \
  --bindings formal/pinch_bindings_v0_11.json \
  --lean-file MAPEOGEOFormal/PinchV011.lean \
  --out-dir artifacts/pinch_intake_v0_11 \
  --independent-checker leanchecker \
  --independent-checker-status PASS \
  --scope-freeze-commit SCOPE_FREEZE_SHA
```

Outputs:

```text
pinch_v0_11_results.json
pinch_v0_11_certificates.json
pinch_v0_11_wounds.json
mapeogeo_v0_11_graph.json.gz
V0_11_SUMMARY.md
```

- [ ] **Step 1: Write failing transition-policy tests**

Cover these rules:

```text
hash mismatch stops promotion
direct-status mismatch stops promotion
missing expected explicit dependency stops promotion
Lean success never changes historical direct-status fields
frozen+present+kernel+leanchecker creates FORMAL + KERNEL_VERIFIED
refused/failed target creates wound/refusal and no KERNEL_VERIFIED
UNTESTED remains explicit
Lean success alone creates neither EQUIVALENT_TO nor SAME_SEMANTICS
all v0.9 wounds remain present
```

- [ ] **Step 2: Run and confirm failure**

Run: `python -m pytest -q tests/test_pinch_intake_v0_11.py`

Expected: FAIL because runner helpers do not exist.

- [ ] **Step 3: Implement identity/dependency/integrity gates**

Fail before promotion on source-node absence, hash drift, detector drift, expected dependency absence, duplicate node IDs, duplicate edge IDs, or missing edge endpoints.

- [ ] **Step 4: Attach one S3 result to every target**

Call `run_contract` once per target. Only a passing declared contract may create an executable certificate node. `UNTESTED`, `NOT_APPLICABLE`, `FAIL`, and `INVALID` are serialized but create no semantic-promotion edge.

- [ ] **Step 5: Attach S4 state**

A target earns `KERNEL_VERIFIED` only when all conditions hold:

```text
scope_status == FROZEN
fixed declaration name present
PinchV011.lean compiles
independent checker status == PASS
proof escape scan empty
```

Otherwise record one of:

```text
REFUSED_SCOPE_MISMATCH
FORMAL_DECLARATION_MISSING
LEAN_KERNEL_FAIL
INDEPENDENT_CHECKER_FAIL
PROOF_ESCAPE_HATCH
```

- [ ] **Step 6: Preserve historical detector data exactly**

For each source node, compare these fields before and after mutation and fail if any differ:

```text
statement_sha256
statement_chars
eo_direct_families
geo_direct_families
direct_status
```

- [ ] **Step 7: Emit a per-node transition row**

Each row records source ID, identity verdict, dependency verdict, historical direct state, S3 state/verdict/scope, S4 scope/kernel/certificate state, final graph state, and explicit refused/not-tested claims.

- [ ] **Step 8: Carry forward the five intake metric families**

Report historical corpus topology/view/routing numbers separately from new certificate counts and kernel-accepted path count.

- [ ] **Step 9: Run tests and commit**

```bash
python -m pytest -q tests/test_pinch_intake_v0_11.py
git add scripts/pinch_intake_v0_11.py tests/test_pinch_intake_v0_11.py
git commit -m "Add v0.11 fail-closed intake runner"
```

---

### Task 6: Add independent artifact validation and Windows reproduction

**Files:**
- Create: `tests/validate_pinch_intake_v0_11.py`
- Create: `scripts/local_verify_v0_11.ps1`
- Modify: `tests/test_pinch_intake_v0_11.py`

- [ ] **Step 1: Implement independent artifact checks**

Validator must re-check four frozen IDs/hashes, explicit Test state, no historical view mutation, certificate-to-FORMAL-to-source linkage, no kernel certificate on refused/failed targets, graph IDs/endpoints, retained v0.9 wounds, and absence of persisted source/proof text payload fields.

- [ ] **Step 2: Add mutation tests**

Validator must fail after independently mutating each of these in a temporary artifact copy: one source hash, one `direct_status`, one refused target certificate, one edge endpoint, and one injected `source_text` field.

- [ ] **Step 3: Add Windows verification script**

Script runs:

```powershell
$ErrorActionPreference = "Stop"
$env:PATH = "$HOME\.elan\bin;" + $env:PATH
lean --version
lake --version
python -m pytest -q tests/test_pinch_source_audit_v0_11.py tests/test_pinch_intake_v0_11.py
lake env lean MAPEOGEOFormal\PinchV011.lean
lake build
python tests\validate_pinch_intake_v0_11.py artifacts\pinch_intake_v0_11
```

It writes metadata only: commit SHA, tool versions, exit states, and hashes of Lean/binding/result files.

- [ ] **Step 4: Run full local regression**

```powershell
pytest
python tests\validate_v0_3.py
lake build
```

Expected: all existing and v0.11 tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/validate_pinch_intake_v0_11.py scripts/local_verify_v0_11.ps1 tests/test_pinch_intake_v0_11.py
git commit -m "Add v0.11 artifact and Windows verification"
```

---

### Task 7: Add sealed Linux CI from v0.9 base to v0.11 evidence

**Files:**
- Create: `.github/workflows/math-intake-v0-11.yml`

- [ ] **Step 1: Use read-only repository permission**

```yaml
permissions:
  contents: read
```

- [ ] **Step 2: Install Python 3.12 and the existing v0.9 dependencies**

Do not add PCT dependencies unless the frozen Task-2 binding actually contains a `PCT_CONTRACT`.

- [ ] **Step 3: Download the source PDF only into runner temporary storage**

Cleanup runs under `if: always()` and deletes the PDF before artifact upload.

- [ ] **Step 4: Reconstruct accepted upstream evidence**

Run the existing frozen v0.6, v0.7, v0.8, and v0.9 commands to obtain the base v0.9 graph in runner temporary storage.

- [ ] **Step 5: Run v0.11 source audit before Lean**

A frozen identity/direct-state/dependency mismatch terminates the job.

- [ ] **Step 6: Install Lean/Mathlib and run build plus `leanchecker`**

Use the repository-pinned `v4.33.1` stack and the same `leanprover/lean-action` pattern as v0.9.

- [ ] **Step 7: Resolve the scope-freeze commit deterministically from Git history**

```bash
SCOPE_FREEZE_COMMIT="$(git log -n 1 --format=%H -- formal/pinch_bindings_v0_11.json evidence/v0_11_preregistration.json)"
test -n "$SCOPE_FREEZE_COMMIT"
```

Pass that value to the v0.11 runner. This avoids hard-coding a future commit value in the plan.

- [ ] **Step 8: Run runner and validator**

```bash
python scripts/pinch_intake_v0_11.py \
  --base-graph "$RUNNER_TEMP/mapeogeo-v09/mapeogeo_s5_v0_9_graph.json.gz" \
  --bindings formal/pinch_bindings_v0_11.json \
  --lean-file MAPEOGEOFormal/PinchV011.lean \
  --out-dir artifacts/pinch_intake_v0_11 \
  --independent-checker leanchecker \
  --independent-checker-status PASS \
  --scope-freeze-commit "$SCOPE_FREEZE_COMMIT"

python tests/validate_pinch_intake_v0_11.py artifacts/pinch_intake_v0_11
```

- [ ] **Step 9: Upload derived evidence only**

Artifact name: `mapeogeo-math-intake-v0.11`.

- [ ] **Step 10: Commit workflow**

```bash
git add .github/workflows/math-intake-v0-11.yml
git commit -m "Add v0.11 mathematics intake CI"
```

---

### Task 8: Seal accepted evidence without outcome-driven scientific changes

**Files:**
- Create after green CI: `evidence/v0_11_acceptance_manifest.json`
- Create after green CI: `docs/V0_11_MATHEMATICS_INTAKE_REPORT.md`
- Modify after green CI: `README.md`

- [ ] **Step 1: Inspect the first complete scientific run without changing frozen mathematics**

Formal scope, source binding, S3 domain, detector history, and acceptance law cannot be changed because of an unfavorable result. Mechanical packaging/validator corrections are allowed only when they do not change computed scientific evidence and are documented.

- [ ] **Step 2: Require a green complete workflow**

The workflow may be green with explicit mathematical refusals because refusal is a valid preregistered state; the runner and validator themselves must pass.

- [ ] **Step 3: Create acceptance manifest**

Record preregistration commit, scope-freeze commit, accepted CI head, workflow/job/artifact IDs, artifact ZIP hash, Lean/Mathlib versions, per-target transition states, certificate counts by class, path count, wound/refusal counts, result-file hashes, copyright boundary, and claim boundary.

- [ ] **Step 4: Write the report as a state-transition table**

Columns:

```text
source node | historical views | S3 state/verdict | formal scope | kernel result | final graph state | refused/not-tested
```

- [ ] **Step 5: Update README only with accepted facts**

Keep PCT described as optional computational evidence and Lean as kernel verifier.

- [ ] **Step 6: Run final local regression and validator**

```powershell
pytest
python tests\validate_v0_3.py
lake build
python tests\validate_pinch_intake_v0_11.py artifacts\pinch_intake_v0_11
```

- [ ] **Step 7: Commit accepted evidence**

```bash
git add evidence/v0_11_acceptance_manifest.json docs/V0_11_MATHEMATICS_INTAKE_REPORT.md README.md
git commit -m "Record accepted v0.11 mathematics intake"
```

## Self-Review

**Spec coverage:** The tasks cover frozen identities, explicit source dependencies, immutable EO/GEO history, explicit Test state, scoped Lean, refusal handling, graph-integrity gates, five intake metric families, Windows/Linux reproducibility, previous-wound preservation, transient-source handling, and delayed second-source ingestion.

**Completeness:** Every generated scientific choice is frozen before the result run. Future values such as the scope-freeze commit are resolved deterministically from repository history rather than left as unbound text.

**Interface consistency:** `formal/pinch_bindings_v0_11.json` is the single source of target identities/scopes/S3 selection. `run_contract` is the sole S3 dispatcher. `pinch_intake_v0_11.py` is the sole v0.11 graph mutator. `validate_pinch_intake_v0_11.py` independently checks serialized evidence. Lean declaration names are fixed before formalization and consumed unchanged by the runner.
