# MAPEOGEO v0.11 Mathematics Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote the four graph-selected v0.9 pinch nodes through a source-bound, fail-closed intake cycle that preserves detector history, records explicit computational/UNTESTED state, attempts scoped Lean formalization for all four, and emits graph/certificate/wound artifacts without altering the architecture.

**Architecture:** v0.11 consumes the accepted v0.9 graph as its base. It first regenerates and hash-checks the four source declarations, then freezes a per-node source-audited scope record before any scientific execution, keeps EO/GEO detector output immutable, runs only preregistered executable contracts where justified, attempts Lean formalization for every node, and extends the graph only with evidence actually earned. PCT v0.10 remains an optional S3 provider and is not a dependency of v0.11.

**Tech Stack:** Python 3.12; `pytest>=8,<9`; existing PyMuPDF/SymPy source-analysis stack; Lean `leanprover/lean4:v4.33.1`; Mathlib `v4.33.1`; GitHub Actions `ubuntu-latest`; local Windows verification through the same pinned repository toolchain.

**Spec:** `docs/superpowers/specs/2026-09-15-v0-11-mathematics-intake-design.md`

## Global Constraints

- Work only on `agent/math-intake-v0-11` until the v0.11 acceptance artifact is green.
- Frozen source IDs and statement SHA-256 values are exactly:
  - `srcdecl:proposition:3_14` — `6e09e18756aefdaf8cdd2c03aca61548d1126fb3d30d70b49c58359f37c64b8e`
  - `srcdecl:proposition:3_13` — `0eef6ce3b699ddef7c209eb28b500b75aab07d9e540b7746b631f8db653addac`
  - `srcdecl:theorem:27_10` — `d205d7c5313b841e6afafc9d619fa059dfe50a2f6c11a48ca2cff466cc84d4fa`
  - `srcdecl:proposition:4_4` — `37e5dc6afdbd3d026c4f7ef71c3531fc74eaeb04bf21ed45c4a9add39fcb6ecf`
- Existing v0.9 direct-view states are immutable historical evidence: 3.14 EO-only, 3.13 EO-only, 27.10 dual-direct, 4.4 EO-only.
- Only explicit source references become source `DEPENDS_ON` edges. Formal/library prerequisites are separate metadata and must not be rewritten as source citations.
- Every accepted node has explicit `Test` state: scoped executable/PCT contract, `KERNEL_VERIFIED`, or `UNTESTED`.
- `DUAL_CANDIDATE`, `EQUIVALENT_TO`, `SAME_SEMANTICS`, `KERNEL_VERIFIED`, `KERNEL_ACCEPTED_PATH`, `WOUND`, and `UNTESTED` remain distinct.
- Lean success must not create or rewrite EO/GEO detector evidence.
- No `sorry`, `admit`, custom `axiom`, or `unsafe` declaration is allowed in accepted formalization source.
- Source prose/page images are transient only and are never committed or uploaded as v0.11 artifacts.
- The repository remains all-rights-reserved under `LICENSE.md`; external Gallier/Quaintance source material remains external under `THIRD_PARTY_NOTICES.md`.
- Existing v0.6/v0.7 routing metrics are carried forward as historical values; v0.11 does not tune their thresholds.
- A failed or refused formalization is a valid scientific result and leaves the source node unpromoted.

---

## File Structure

Create or modify these focused units:

```text
formal/pinch_bindings_v0_11.json          # frozen identities, audited scopes, deps, test plans
MAPEOGEOFormal/PinchV011.lean             # four scoped source-bound formal candidates
MAPEOGEOFormal.lean                       # import PinchV011
scripts/audit_pinch_source_v0_11.py        # transient source/hash/dependency audit; no prose artifacts
scripts/pinch_intake_v0_11.py              # state transitions, certificates, wounds, graph emission
scripts/local_verify_v0_11.ps1             # reproducible Windows kernel/test command bundle
tests/test_pinch_source_audit_v0_11.py     # binding/hash/dependency policy tests
tests/test_pinch_intake_v0_11.py           # graph-state and promotion discipline tests
tests/validate_pinch_intake_v0_11.py       # artifact validator
evidence/v0_11_preregistration.json        # scientific freeze, no result values
.github/workflows/math-intake-v0-11.yml     # Linux CI run and artifact upload
docs/V0_11_MATHEMATICS_INTAKE_SPEC.md      # human-readable preregistration mirror
```

Create only after an accepted CI run:

```text
evidence/v0_11_acceptance_manifest.json
docs/V0_11_MATHEMATICS_INTAKE_REPORT.md
README.md                                  # add v0.11 accepted result summary
```

Do not modify `MAPEOGEOFormal/SourceBound.lean`, `MAPEOGEOFormal/ProofPaths.lean`, or v0.8/v0.9 acceptance evidence except for import wiring that leaves those files byte-for-byte unchanged.

---

### Task 1: Freeze the executable v0.11 manifest and binding schema

**Files:**
- Create: `formal/pinch_bindings_v0_11.json`
- Create: `evidence/v0_11_preregistration.json`
- Create: `docs/V0_11_MATHEMATICS_INTAKE_SPEC.md`
- Create: `tests/test_pinch_source_audit_v0_11.py`

**Interfaces:**
- Produces: JSON binding records consumed by `audit_pinch_source_v0_11.py`, `pinch_intake_v0_11.py`, and CI.
- Required record fields:
  `source_id`, `statement_sha256`, `expected_direct_status`, `explicit_dependencies`, `formal_decl`, `formal_scope`, `s3_test_state`, `s3_contract_id`, `s3_scope`, `scope_status`.
- `scope_status` is one of `FROZEN`, `REFUSED_SCOPE_MISMATCH`.
- `s3_test_state` is one of `EXECUTABLE_CONTRACT`, `PCT_CONTRACT`, `UNTESTED`.

- [ ] **Step 1: Write a failing binding-schema test**

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
    got = {x["source_id"]: x["statement_sha256"] for x in cfg["targets"]}
    assert got == FROZEN
    assert len(cfg["targets"]) == 4
    for item in cfg["targets"]:
        assert item["s3_test_state"] in {"EXECUTABLE_CONTRACT", "PCT_CONTRACT", "UNTESTED"}
        assert item["scope_status"] in {"FROZEN", "REFUSED_SCOPE_MISMATCH"}
```

- [ ] **Step 2: Run the test and confirm the expected failure**

Run: `python -m pytest -q tests/test_pinch_source_audit_v0_11.py::test_v011_bindings_freeze_exact_quartet`

Expected: FAIL because `formal/pinch_bindings_v0_11.json` does not yet exist.

- [ ] **Step 3: Create the initial bindings with immutable identities and detector history**

Use exactly this outer structure:

```json
{
  "schema_version": "0.11",
  "stage": "PINCH_DRIVEN_MATHEMATICS_INTAKE",
  "source": "GALLIER_QUAINTANCE_MATH_DEEP",
  "targets": [
    {
      "source_id": "srcdecl:proposition:3_14",
      "statement_sha256": "6e09e18756aefdaf8cdd2c03aca61548d1126fb3d30d70b49c58359f37c64b8e",
      "expected_direct_status": "EO_ONLY_DIRECT",
      "explicit_dependencies": ["srcdecl:proposition:3_13", "srcdecl:proposition:4_4"],
      "formal_decl": "MAPEOGEOFormal.proposition_3_14_v011",
      "formal_scope": "SOURCE_AUDIT_REQUIRED_BEFORE_EXECUTION",
      "s3_test_state": "UNTESTED",
      "s3_contract_id": null,
      "s3_scope": null,
      "scope_status": "REFUSED_SCOPE_MISMATCH"
    },
    {
      "source_id": "srcdecl:proposition:3_13",
      "statement_sha256": "0eef6ce3b699ddef7c209eb28b500b75aab07d9e540b7746b631f8db653addac",
      "expected_direct_status": "EO_ONLY_DIRECT",
      "explicit_dependencies": ["srcdecl:proposition:3_21", "srcdecl:proposition:2_2", "srcdecl:proposition:2_3", "srcdecl:proposition:4_4"],
      "formal_decl": "MAPEOGEOFormal.proposition_3_13_v011",
      "formal_scope": "SOURCE_AUDIT_REQUIRED_BEFORE_EXECUTION",
      "s3_test_state": "UNTESTED",
      "s3_contract_id": null,
      "s3_scope": null,
      "scope_status": "REFUSED_SCOPE_MISMATCH"
    },
    {
      "source_id": "srcdecl:theorem:27_10",
      "statement_sha256": "d205d7c5313b841e6afafc9d619fa059dfe50a2f6c11a48ca2cff466cc84d4fa",
      "expected_direct_status": "DUAL_DIRECT",
      "explicit_dependencies": ["srcdecl:theorem:6_16"],
      "formal_decl": "MAPEOGEOFormal.theorem_27_10_v011",
      "formal_scope": "SOURCE_AUDIT_REQUIRED_BEFORE_EXECUTION",
      "s3_test_state": "UNTESTED",
      "s3_contract_id": null,
      "s3_scope": null,
      "scope_status": "REFUSED_SCOPE_MISMATCH"
    },
    {
      "source_id": "srcdecl:proposition:4_4",
      "statement_sha256": "37e5dc6afdbd3d026c4f7ef71c3531fc74eaeb04bf21ed45c4a9add39fcb6ecf",
      "expected_direct_status": "EO_ONLY_DIRECT",
      "explicit_dependencies": ["srcdecl:proposition:4_3"],
      "formal_decl": "MAPEOGEOFormal.proposition_4_4_v011",
      "formal_scope": "SOURCE_AUDIT_REQUIRED_BEFORE_EXECUTION",
      "s3_test_state": "UNTESTED",
      "s3_contract_id": null,
      "s3_scope": null,
      "scope_status": "REFUSED_SCOPE_MISMATCH"
    }
  ]
}
```

This initial file intentionally refuses formal scope until Task 2 audits the current source. It is not an accepted scientific manifest yet.

- [ ] **Step 4: Create preregistration JSON and human-readable spec**

The preregistration must copy the four frozen identities, the immutable historical direct-view states, toolchain pins, forbidden proof escapes, the exact allowed verdicts, and these acceptance rules:

```text
all four identities must match
all four FORMAL candidates must be attempted after scope freeze
successful kernel certificates require lean build + leanchecker
failed/refused scopes remain source-only and emit a wound/refusal
no detector history may be rewritten
all four nodes must finish with an explicit Test state
previous v0.9 wounds remain visible
```

Do not include expected numerical results, expected pass counts, or post-run thresholds.

- [ ] **Step 5: Run the schema test**

Run: `python -m pytest -q tests/test_pinch_source_audit_v0_11.py`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add formal/pinch_bindings_v0_11.json evidence/v0_11_preregistration.json docs/V0_11_MATHEMATICS_INTAKE_SPEC.md tests/test_pinch_source_audit_v0_11.py
git commit -m "Preregister v0.11 pinch mathematics intake"
```

---

### Task 2: Audit the exact current source statements and freeze formal scopes before execution

**Files:**
- Create: `scripts/audit_pinch_source_v0_11.py`
- Modify: `formal/pinch_bindings_v0_11.json`
- Modify: `evidence/v0_11_preregistration.json`
- Modify: `tests/test_pinch_source_audit_v0_11.py`

**Interfaces:**
- Consumes: transient current Gallier/Quaintance PDF plus a regenerated v0.6/v0.7 graph.
- Produces: metadata-only `pinch_source_audit_v0_11.json` containing ID/hash/page/dependency/direct-view/scope-status data; never source prose.
- CLI:

```text
python scripts/audit_pinch_source_v0_11.py SOURCE_PDF \
  --graph PATH_TO_REGENERATED_GRAPH \
  --bindings formal/pinch_bindings_v0_11.json \
  --out PINCH_AUDIT_JSON
```

- [ ] **Step 1: Add a failing unit test for hash/direct-status/dependency auditing**

```python
from scripts.audit_pinch_source_v0_11 import audit_targets


def test_audit_rejects_hash_or_detector_drift(sample_graph, sample_bindings):
    result = audit_targets(sample_graph, sample_bindings)
    assert result["all_hashes_match"] is True
    assert result["all_direct_states_match"] is True
    assert result["all_explicit_dependencies_present"] is True
```

Add a second test that mutates one hash and asserts `all_hashes_match is False`.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest -q tests/test_pinch_source_audit_v0_11.py`

Expected: FAIL because `audit_targets` does not exist.

- [ ] **Step 3: Implement metadata-only auditing**

`audit_targets(graph, bindings)` must:

```python
by_id = {node["id"]: node for node in graph["nodes"]}
for target in bindings["targets"]:
    node = by_id[target["source_id"]]
    profile = node["attributes"]["independent_profile"]
    assert_or_record(profile["statement_sha256"] == target["statement_sha256"])
    assert_or_record(profile["direct_status"] == target["expected_direct_status"])
    deps = {
        e["target"] for e in graph["edges"]
        if e.get("type") == "DEPENDS_ON" and e.get("source") == target["source_id"]
    }
    assert_or_record(set(target["explicit_dependencies"]) <= deps)
```

Serialized output may include only source ID, statement hash, page locator, statement/proof character counts, detector state, dependency IDs, and scope/test metadata. It must not include statement or proof text.

- [ ] **Step 4: Run the transient source audit locally before writing any Lean theorem**

Regenerate the accepted source graph using the existing v0.6/v0.7 path, then run the new audit script. Stop if any frozen hash or direct-view state differs.

The executor must inspect the four exact source statements transiently from the current PDF and choose the narrowest faithful formal scope for each. Store only independently authored scope labels/descriptions, not copied source prose.

The required decision rule is:

```text
If a faithful formal statement can be written for the source claim or an explicitly named proper sub-scope:
    scope_status = FROZEN
    formal_scope = stable uppercase identifier
else:
    scope_status = REFUSED_SCOPE_MISMATCH
    formal_scope = reason code
```

The four Lean declaration names remain fixed even if a scope is refused.

- [ ] **Step 5: Freeze S3 test selection at the same time**

For each target, choose exactly one:

```text
EXECUTABLE_CONTRACT  only if an exact/scoped executable test is justified
PCT_CONTRACT         only if PCT v0.10 has merged and the object satisfies a declared PCT applicability contract
UNTESTED             otherwise
```

Do not create a computational test merely to avoid `UNTESTED`.

If `EXECUTABLE_CONTRACT` is selected, add a stable `s3_contract_id` and exact domain description now, before observing its outcome.

- [ ] **Step 6: Amend preregistration with the frozen scope/test choices**

The amendment must contain no outcome values. Record the commit as `scope_freeze_commit` later in the runner output.

- [ ] **Step 7: Run source-audit tests and commit the freeze**

Run:

```bash
python -m pytest -q tests/test_pinch_source_audit_v0_11.py
python scripts/audit_pinch_source_v0_11.py <current-pdf> --graph <regenerated-graph> --bindings formal/pinch_bindings_v0_11.json --out artifacts/pinch_source_audit_v0_11.json
```

Expected: PASS with four exact hash matches and no prose in the artifact.

Commit the audited bindings and preregistration amendment before Task 3.

---

### Task 3: Add fail-closed Lean formal candidates for the frozen scopes

**Files:**
- Create: `MAPEOGEOFormal/PinchV011.lean`
- Modify: `MAPEOGEOFormal.lean`
- Create: `tests/test_pinch_intake_v0_11.py`

**Interfaces:**
- Consumes: `formal/pinch_bindings_v0_11.json` after Task 2 scope freeze.
- Produces fixed declaration names:
  - `MAPEOGEOFormal.proposition_3_14_v011`
  - `MAPEOGEOFormal.proposition_3_13_v011`
  - `MAPEOGEOFormal.theorem_27_10_v011`
  - `MAPEOGEOFormal.proposition_4_4_v011`
- A refused scope is represented in metadata, not by a fake Lean theorem. The runner must treat missing declaration + `REFUSED_SCOPE_MISMATCH` as an intentional refusal rather than a kernel failure.

- [ ] **Step 1: Write tests for fixed declaration names and forbidden proof escapes**

```python
from pathlib import Path
from scripts.formal_bridge_v0_8 import proof_escape_hits


def test_v011_lean_file_has_no_escape_hatches():
    text = Path("MAPEOGEOFormal/PinchV011.lean").read_text(encoding="utf-8")
    assert proof_escape_hits(text) == []


def test_v011_decl_names_follow_frozen_bindings():
    import json
    cfg = json.loads(Path("formal/pinch_bindings_v0_11.json").read_text(encoding="utf-8"))
    text = Path("MAPEOGEOFormal/PinchV011.lean").read_text(encoding="utf-8")
    for item in cfg["targets"]:
        if item["scope_status"] == "FROZEN":
            assert item["formal_decl"].split(".")[-1] in text
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest -q tests/test_pinch_intake_v0_11.py`

Expected: FAIL because `PinchV011.lean` does not exist.

- [ ] **Step 3: Implement one theorem per `FROZEN` source scope**

Rules for each theorem:

```text
- theorem name exactly matches the binding
- theorem statement is the narrowest Task-2-frozen formal scope
- proof may use Mathlib but no escape hatch
- add a source-ID/hash comment, not copied source prose
- add `#print axioms <decl>` after the theorem
```

Example header pattern:

```lean
/--
MAPEOGEO source binding: srcdecl:proposition:3_14
statement_sha256: 6e09e18756aefdaf8cdd2c03aca61548d1126fb3d30d70b49c58359f37c64b8e
formal_scope: <the frozen uppercase scope identifier from the JSON binding>
-/
theorem proposition_3_14_v011 ... := by
  ...
```

The placeholder shown above is a documentation pattern only: during implementation the executor must substitute the already-frozen scope identifier and complete Lean statement from Task 2 in the same commit. No `<...>` token may remain in the repository.

- [ ] **Step 4: Import the file at the library root**

`MAPEOGEOFormal.lean` must become:

```lean
import MAPEOGEOFormal.SourceBound
import MAPEOGEOFormal.ProofPaths
import MAPEOGEOFormal.PinchV011
```

- [ ] **Step 5: Run direct kernel verification**

Run:

```powershell
lake env lean MAPEOGEOFormal\PinchV011.lean
lake build
```

Expected: every `FROZEN` declaration compiles and `#print axioms` contains no `sorryAx` or custom axiom. A scope that cannot be made faithful must be changed to `REFUSED_SCOPE_MISMATCH` in the bindings through a visible preregistration amendment **before** re-running the scientific runner; do not weaken the theorem post-result.

- [ ] **Step 6: Run unit tests**

Run: `python -m pytest -q tests/test_pinch_intake_v0_11.py`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add MAPEOGEOFormal/PinchV011.lean MAPEOGEOFormal.lean tests/test_pinch_intake_v0_11.py formal/pinch_bindings_v0_11.json evidence/v0_11_preregistration.json
git commit -m "Add v0.11 pinch formal candidates"
```

---

### Task 4: Implement preregistered S3 executable contracts without forcing coverage

**Files:**
- Create: `scripts/pinch_contracts_v0_11.py`
- Modify: `tests/test_pinch_intake_v0_11.py`

**Interfaces:**
- Produces:

```python
@dataclass(frozen=True)
class ContractResult:
    source_id: str
    contract_id: str | None
    test_state: str
    applicability: str
    verdict: str
    scope: str | None
    measured: dict
    refused: list[str]


def run_contract(target: dict) -> ContractResult
```

- `UNTESTED` targets return `verdict="UNTESTED"`, `applicability="NOT_RUN"`, an empty `measured`, and a nonempty `refused` explaining what was not claimed.
- `PCT_CONTRACT` is legal only if the PCT package is present and the frozen applicability contract passes; otherwise return fail-closed `NOT_APPLICABLE`, not PASS.
- `EXECUTABLE_CONTRACT` dispatches only by preregistered `s3_contract_id`.

- [ ] **Step 1: Add failing tests for UNTESTED and unknown contracts**

```python
from scripts.pinch_contracts_v0_11 import run_contract


def test_untested_is_explicit_not_pass():
    r = run_contract({
        "source_id": "srcdecl:proposition:3_14",
        "s3_test_state": "UNTESTED",
        "s3_contract_id": None,
        "s3_scope": None,
    })
    assert r.verdict == "UNTESTED"
    assert r.refused


def test_unknown_executable_contract_fails_closed():
    r = run_contract({
        "source_id": "x",
        "s3_test_state": "EXECUTABLE_CONTRACT",
        "s3_contract_id": "DOES_NOT_EXIST",
        "s3_scope": "X",
    })
    assert r.verdict == "INVALID"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest -q tests/test_pinch_intake_v0_11.py`

Expected: FAIL because the contract runner does not exist.

- [ ] **Step 3: Implement the minimal explicit dispatcher**

Use a dictionary keyed only by contract IDs frozen in Task 2. If Task 2 froze no executable/PCT contracts, the dispatcher intentionally contains no scientific contract implementation and all four nodes remain computationally `UNTESTED`; that is a valid implementation, not missing work.

- [ ] **Step 4: Implement each frozen executable contract exactly as preregistered**

For every contract actually selected in Task 2:

```text
- deterministic input domain
- exact arithmetic wherever the contract is algebraic/discrete
- explicit applicability
- exact expected rule or preregistered tolerance
- explicit refused/untested remainder
```

Add one positive and one mutation/negative-control unit test per implemented contract.

- [ ] **Step 5: Run contract tests**

Run: `python -m pytest -q tests/test_pinch_intake_v0_11.py`

Expected: PASS without changing any Task-2-frozen contract ID/domain.

- [ ] **Step 6: Commit**

```bash
git add scripts/pinch_contracts_v0_11.py tests/test_pinch_intake_v0_11.py
git commit -m "Add scoped v0.11 computational test states"
```

---

### Task 5: Build the v0.11 graph-state transition runner

**Files:**
- Create: `scripts/pinch_intake_v0_11.py`
- Modify: `tests/test_pinch_intake_v0_11.py`

**Interfaces:**
- CLI:

```text
python scripts/pinch_intake_v0_11.py \
  --base-graph BASE_V09_GRAPH \
  --bindings formal/pinch_bindings_v0_11.json \
  --lean-file MAPEOGEOFormal/PinchV011.lean \
  --out-dir artifacts/pinch_intake_v0_11 \
  --independent-checker leanchecker \
  --independent-checker-status PASS \
  --scope-freeze-commit COMMIT_SHA
```

- Produces:
  - `pinch_v0_11_results.json`
  - `pinch_v0_11_certificates.json`
  - `pinch_v0_11_wounds.json`
  - `mapeogeo_v0_11_graph.json.gz`
  - `V0_11_SUMMARY.md`

- [ ] **Step 1: Add failing transition tests**

Test these exact rules:

```python
# kernel verification never changes historical independent_profile.direct_status
# successful FORMAL creates FORMAL representation + KERNEL_VERIFIED certificate
# failed/refused FORMAL creates WOUND/refusal and no KERNEL_VERIFIED edge
# UNTESTED is serialized explicitly
# EQUIVALENT_TO/SAME_SEMANTICS are never created merely from Lean success
# previous v0.9 WOUND nodes/edges remain present
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest -q tests/test_pinch_intake_v0_11.py`

Expected: FAIL because the runner functions do not exist.

- [ ] **Step 3: Implement frozen identity and graph-integrity gates**

The runner must fail before promotion when:

```python
actual_hash != expected_hash
actual_direct_status != expected_direct_status
missing explicit dependency
source node missing
duplicate node or edge IDs
edge endpoint missing
```

- [ ] **Step 4: Execute S3 state for every node**

Call `run_contract(target)` and attach a `TEST_STATE` record to the result table. Only add executable certificate nodes for `PASS` results under a declared contract. `UNTESTED`, `NOT_APPLICABLE`, `FAIL`, and `INVALID` remain visible and do not create semantic-promotion edges.

- [ ] **Step 5: Execute S4 kernel status**

Run `lake env lean MAPEOGEOFormal/PinchV011.lean` once. Declaration presence is checked per target.

Promotion rule:

```text
scope_status == FROZEN
AND declaration present
AND Lean file compiles
AND independent_checker_status == PASS
AND no forbidden proof escapes
=> add FORMAL representation + KERNEL_VERIFIED certificate
```

Otherwise emit a wound/refusal with one of:

```text
REFUSED_SCOPE_MISMATCH
FORMAL_DECLARATION_MISSING
LEAN_KERNEL_FAIL
INDEPENDENT_CHECKER_FAIL
PROOF_ESCAPE_HATCH
```

- [ ] **Step 6: Preserve view history exactly**

The source node's `independent_profile` must remain byte-equivalent at the JSON-object level to the base graph for:

```text
statement_sha256
statement_chars
eo_direct_families
geo_direct_families
direct_status
```

New EO/GEO candidate representations may be added only if separately introduced by an explicit evidence record; the v0.11 runner itself must not infer one from FORMAL success.

- [ ] **Step 7: Emit the state-transition table**

Each target result must contain:

```json
{
  "source_id": "...",
  "identity": "MATCH|FAIL",
  "deps": "PASS|WOUND",
  "historical_direct_status": "...",
  "s3": {"test_state": "...", "verdict": "...", "scope": "..."},
  "s4": {"scope_status": "...", "kernel": "PASS|FAIL|REFUSED", "certificate": "KERNEL_VERIFIED|null"},
  "final_state": "SOURCE_ONLY|SOURCE_PLUS_FORMAL|WOUND",
  "refused": []
}
```

- [ ] **Step 8: Carry forward the five batch-metric families**

Report historical v0.6/v0.7 values separately from new v0.11 counts:

```text
source declarations/proofs/unresolved-ref rate
EO/GEO/dual direct historical coverage
dual-union held-out recall + fallback-required flag
new certificates by class
kernel-accepted path count
```

Do not recompute old values with modified data and label them as historical.

- [ ] **Step 9: Run tests**

Run: `python -m pytest -q tests/test_pinch_intake_v0_11.py`

Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add scripts/pinch_intake_v0_11.py tests/test_pinch_intake_v0_11.py
git commit -m "Add v0.11 fail-closed intake runner"
```

---

### Task 6: Add independent artifact validation and local Windows reproduction

**Files:**
- Create: `tests/validate_pinch_intake_v0_11.py`
- Create: `scripts/local_verify_v0_11.ps1`

**Interfaces:**
- Validator CLI: `python tests/validate_pinch_intake_v0_11.py ARTIFACT_DIR`
- PowerShell output directory: `artifacts/local_windows_v0_11/`

- [ ] **Step 1: Write the artifact validator**

It must independently re-check:

```text
four exact source IDs/hashes
all four explicit Test states
no silent direct-view mutation
certificate -> FORMAL -> source linkage
KERNEL_VERIFIED only on kernel+leanchecker PASS
no KERNEL_VERIFIED on refused/failed targets
unique graph IDs/endpoints
previous v0.9 wound retained
no stored source prose/page-image payload
summary/result/certificate/graph SHA-256 availability
```

- [ ] **Step 2: Add validator mutation tests**

Create temporary artifact copies and verify the validator fails if:

```text
one source hash changes
one `direct_status` changes
one refused node is given KERNEL_VERIFIED
one edge endpoint is missing
one artifact record contains a `source_text` or `proof_text` field
```

- [ ] **Step 3: Create the Windows verification script**

Use explicit UTF-8 and repository pins:

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

The script writes a metadata-only JSON containing commit SHA, Lean/Lake versions, test exit codes, and hashes of `PinchV011.lean`, bindings, and result artifacts. It must not create a stronger certificate class than `KERNEL_VERIFIED`.

- [ ] **Step 4: Run tests locally**

Run:

```powershell
pytest
python tests\validate_v0_3.py
lake build
```

Expected: all existing tests plus v0.11 tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/validate_pinch_intake_v0_11.py scripts/local_verify_v0_11.ps1 tests/test_pinch_intake_v0_11.py
git commit -m "Add v0.11 artifact and Windows verification"
```

---

### Task 7: Add sealed CI execution from accepted v0.9 to v0.11

**Files:**
- Create: `.github/workflows/math-intake-v0-11.yml`

**Interfaces:**
- CI artifact name: `mapeogeo-math-intake-v0.11`
- CI reconstructs v0.6 -> v0.7 -> v0.8 -> v0.9 before v0.11, rather than trusting an unverified local graph snapshot.

- [ ] **Step 1: Create the workflow with read-only repository permissions**

Use:

```yaml
permissions:
  contents: read
```

and pinned Python 3.12.

- [ ] **Step 2: Install the existing Python dependency set**

Use the same requirements required by v0.9 and do not add PCT dependencies unless PCT has actually merged and the frozen v0.11 binding uses `PCT_CONTRACT`.

- [ ] **Step 3: Download the Gallier/Quaintance PDF transiently**

Store only in `$RUNNER_TEMP`; delete it in an `if: always()` cleanup step.

- [ ] **Step 4: Regenerate accepted upstream states**

Run the frozen commands used by v0.6, v0.7, v0.8, and v0.9 to produce the base v0.9 graph in `$RUNNER_TEMP`.

- [ ] **Step 5: Audit v0.11 identities before Lean execution**

Run:

```bash
python scripts/audit_pinch_source_v0_11.py \
  "$RUNNER_TEMP/mapeogeo-source/math-deep.pdf" \
  --graph "$RUNNER_TEMP/mapeogeo-v09/mapeogeo_s5_v0_9_graph.json.gz" \
  --bindings formal/pinch_bindings_v0_11.json \
  --out "$RUNNER_TEMP/pinch_source_audit_v0_11.json"
```

A hash/direct-state/dependency mismatch stops the job.

- [ ] **Step 6: Install Lean/Mathlib and run `lake build` + `leanchecker`**

Use the existing `leanprover/lean-action` pattern, with repository toolchain `v4.33.1`, `build: true`, and `leanchecker: true`.

- [ ] **Step 7: Run v0.11 intake and validator**

```bash
python scripts/pinch_intake_v0_11.py \
  --base-graph "$RUNNER_TEMP/mapeogeo-v09/mapeogeo_s5_v0_9_graph.json.gz" \
  --bindings formal/pinch_bindings_v0_11.json \
  --lean-file MAPEOGEOFormal/PinchV011.lean \
  --out-dir artifacts/pinch_intake_v0_11 \
  --independent-checker leanchecker \
  --independent-checker-status PASS \
  --scope-freeze-commit <the committed Task-2 freeze SHA>

python tests/validate_pinch_intake_v0_11.py artifacts/pinch_intake_v0_11
```

When implementing the workflow, replace the angle-bracket token with the literal Task-2 freeze SHA before committing; no placeholder may remain.

- [ ] **Step 8: Upload only derived evidence**

Upload `artifacts/pinch_intake_v0_11/`; never upload the source PDF.

- [ ] **Step 9: Commit and let CI run**

```bash
git add .github/workflows/math-intake-v0-11.yml
git commit -m "Add v0.11 mathematics intake CI"
```

---

### Task 8: Accept results without outcome-driven repair

**Files:**
- Create after green CI: `evidence/v0_11_acceptance_manifest.json`
- Create after green CI: `docs/V0_11_MATHEMATICS_INTAKE_REPORT.md`
- Modify after green CI: `README.md`

**Interfaces:**
- Acceptance manifest records immutable CI provenance and artifact hashes.
- Report presents one row per pinch node and preserves refusals/wounds.

- [ ] **Step 1: Inspect the first complete scientific run**

Do not change formal scope, S3 contract domain, source binding, detector history, or acceptance gates in response to an unfavorable mathematical result.

Allowed post-run fixes without scientific amendment are limited to mechanical artifact-validator or packaging defects that do not change computed evidence. Document any such fix explicitly.

- [ ] **Step 2: Require a green complete run**

Every CI step through artifact validation and upload must succeed. If a mathematical target is refused or fails formalization, the *workflow* may still be green only when the runner/validator correctly records that fail-closed state according to the preregistered rules.

- [ ] **Step 3: Create the acceptance manifest**

Record:

```text
scientific_preregistration_commit
scope_freeze_commit
accepted_ci_head
workflow_run_id
job_id
artifact_id
artifact_zip_sha256
Lean/Mathlib versions
per-target identity/deps/direct-state/S3/S4/final-state
certificate counts by class
kernel-accepted path count
wound/refusal counts
result artifact SHA-256 values
copyright/source-payload boundary
claim boundary
```

- [ ] **Step 4: Write the report**

The main table must have exactly these conceptual columns:

```text
source node | historical views | S3 state/verdict | formal scope | kernel result | final graph state | refused/not-tested
```

Interpretation must answer whether formalization repaired anything legitimately, not merely how many Lean declarations passed.

- [ ] **Step 5: Update README only with accepted evidence**

Add v0.11 after v0.10/v0.9 sections as appropriate to actual merge order. Preserve the project-level statement that PCT is optional computational evidence and Lean remains the kernel verifier.

- [ ] **Step 6: Run final local verification**

Run:

```powershell
pytest
python tests\validate_v0_3.py
lake build
python tests\validate_pinch_intake_v0_11.py artifacts\pinch_intake_v0_11
```

Expected: PASS.

- [ ] **Step 7: Commit accepted evidence**

```bash
git add evidence/v0_11_acceptance_manifest.json docs/V0_11_MATHEMATICS_INTAKE_REPORT.md README.md
git commit -m "Record accepted v0.11 mathematics intake"
```

---

## Plan Self-Review

### Spec coverage

- Two-lane PCT/intake separation: Tasks 1, 4, 7.
- Frozen quartet/identity hashes: Tasks 1, 2, 5, 6.
- Explicit dependencies only: Tasks 1, 2, 5.
- Immutable EO/GEO detector history: Tasks 2, 5, 6.
- Explicit Test state including legal `UNTESTED`: Tasks 1, 4, 5.
- Scoped Lean for all attempted frozen scopes: Task 3.
- Fail-closed refusal: Tasks 2, 3, 5, 8.
- `KERNEL_VERIFIED` authority: Tasks 3, 5, 7.
- Separate promotion edge meanings: Tasks 5, 6.
- Previous wounds retained: Tasks 5, 6.
- Five batch-metric families: Task 5.
- Windows/Linux reproducibility: Tasks 6, 7.
- Copyright/transient-source boundary: Tasks 2, 6, 7.
- No second-source ingestion: explicitly outside this plan, per spec.

### Placeholder scan

The only angle-bracket examples in this plan are explanatory command templates. Each task explicitly requires replacing them with literal values before commit. Repository files must contain no `TBD`, `TODO`, `<...>`, or unbound scientific threshold.

### Type/interface consistency

- `formal/pinch_bindings_v0_11.json` is the single source of target identities, declaration names, formal scopes, and S3 plan.
- `ContractResult` feeds `pinch_intake_v0_11.py` exactly once per target.
- `pinch_intake_v0_11.py` is the only graph mutator for v0.11.
- `validate_pinch_intake_v0_11.py` is independent of the runner and checks serialized artifacts rather than trusting runner return values.
- Lean declaration names are fixed in Task 1 and consumed unchanged in Tasks 3 and 5.
