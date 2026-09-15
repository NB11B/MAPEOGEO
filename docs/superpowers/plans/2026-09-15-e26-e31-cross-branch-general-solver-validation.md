# E26–E31 Cross-Branch General Solver Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate the frozen E-series solver stack against the larger frozen v0.15.1 knowledge graph, replay branch adversaries against the independently developed `main` PCT implementation, and bind both directions into deterministic E25-style closure without merging either branch.

**Architecture:** Add one isolated `experiments/pct_e26_e31` package on `agent/pct-computational-architecture`. It reads a separate checkout of frozen knowledge baseline `fd2d90c00cb71951fdfd7cd1e7e22a8f0552f97f`, never imports that checkout in-process, and treats full answer data as verifier-only. Solver-visible sanitized graph views, exact ambiguity sets, bounded probe minimization, rule search, adversarial subprocess replay, and receipt generation are separate modules with deterministic JSON interfaces.

**Tech Stack:** Python 3.12, pytest, networkx, numpy, sympy, stdlib `subprocess`/`hashlib`/`json`, existing E25 receipt/lifecycle code, GitHub Actions with two pinned checkouts.

**Spec:** `docs/superpowers/specs/2026-09-15-e26-e31-cross-branch-general-solver-validation-design.md`

## Global Constraints

- Solver baseline is immutable input `6c9333ed3ec48a298ad943a74e72a01fa1ffcd78`.
- Knowledge baseline is immutable input `fd2d90c00cb71951fdfd7cd1e7e22a8f0552f97f`.
- `main` is read-only: no merge, cherry-pick, push, graph mutation, or semantic promotion.
- The frozen `main` checkout is never imported into the experimental Python process.
- Main-side PCT execution occurs only through a JSON subprocess boundary whose `PYTHONPATH` points to the frozen main checkout.
- `SAME_SEMANTICS`, `SCOPED_OVERLAP`, and `RELATED_TO` remain distinct classes.
- `FORMAL_LINKED` must never be promoted to `KERNEL_VERIFIED` without independent kernel evidence.
- Ambiguity is represented by an exact candidate set; no confidence score may override non-uniqueness.
- Every result binds `solver_baseline_sha`, `knowledge_baseline_sha`, `campaign_harness_sha`, `solver_recipe_sha256`, sanitized input hash, output hash, and sealed answer hash.
- Frozen evidence is generated to an uncommitted candidate directory first and committed only after deterministic comparison tests exist.
- Prior E1–E25J implementation/evidence are immutable inputs. If they require modification, stop this campaign and preregister a new solver baseline.

---

### Task 1: E26 Frozen Corpus Binding and Separate-Checkout Contract

**Files:**
- Create: `experiments/pct_e26_e31/__init__.py`
- Create: `experiments/pct_e26_e31/constants.py`
- Create: `experiments/pct_e26_e31/corpus.py`
- Create: `experiments/pct_e26_e31/test_e26.py`
- Modify: `.github/workflows/pct-e1-e25-campaign.yml`

**Interfaces:**
- `load_knowledge_corpus(main_root: Path) -> KnowledgeCorpus`
- `build_e26_manifest(main_root: Path, repo_root: Path, harness_sha: str) -> dict`
- `verify_frozen_checkout(path: Path, expected_sha: str) -> None`
- `KnowledgeCorpus` contains full graph, direct graph counts, semantic edges, canonical/source/domain indexes, artifact digests, and eligibility indexes. It is verifier-side only.

- [ ] **Step 1: Write the RED tests for pinned checkouts and direct graph reconstruction**

```python
from experiments.pct_e26_e31.constants import KNOWLEDGE_BASELINE_SHA, SOLVER_BASELINE_SHA
from experiments.pct_e26_e31.corpus import build_e26_manifest


def test_e26_manifest_binds_both_frozen_shas(main_checkout, repo_root):
    m = build_e26_manifest(main_checkout, repo_root, "HARNESS_TEST_SHA")
    assert m["solver_baseline_sha"] == SOLVER_BASELINE_SHA
    assert m["knowledge_baseline_sha"] == KNOWLEDGE_BASELINE_SHA
    assert m["campaign_harness_sha"] == "HARNESS_TEST_SHA"


def test_e26_reconstructs_graph_counts_from_artifact(main_checkout, repo_root):
    m = build_e26_manifest(main_checkout, repo_root, "HARNESS_TEST_SHA")
    assert m["direct_graph_counts"]["source_declarations"] > 0
    assert m["direct_graph_counts"]["canonical_objects"] > 0
    assert m["direct_graph_counts"]["semantic_bridges"] > 0
    assert set(m["semantic_relation_types"]) >= {"SAME_SEMANTICS", "SCOPED_OVERLAP", "RELATED_TO"}
```

- [ ] **Step 2: Run the new tests and confirm RED**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e26.py`

Expected: collection/import failure because `experiments.pct_e26_e31.corpus` does not yet exist.

- [ ] **Step 3: Implement deterministic corpus discovery and hashing**

Use `git rev-parse HEAD` in each checkout for identity, locate `artifacts/analysis_v0_15_1/mapeogeo_v0_15_1_graph.json.gz`, hash raw artifact bytes with SHA-256, load the gzip JSON, and build indexes without trusting report totals. Represent any report/manifest mismatch as a `discrepancies` record; do not repair source files.

- [ ] **Step 4: Add CI separate checkouts**

Add pinned read-only checkouts beneath the branch workspace:

```yaml
- name: Checkout frozen solver baseline
  uses: actions/checkout@v4
  with:
    ref: 6c9333ed3ec48a298ad943a74e72a01fa1ffcd78
    path: frozen-solver

- name: Checkout frozen knowledge baseline
  uses: actions/checkout@v4
  with:
    ref: fd2d90c00cb71951fdfd7cd1e7e22a8f0552f97f
    path: frozen-main
```

Keep workflow permissions `contents: read`.

- [ ] **Step 5: Run Task 1 GREEN gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e26.py`

Expected: all E26 tests PASS and direct corpus counts are emitted from the pinned graph.

- [ ] **Step 6: Commit Task 1**

```bash
git add experiments/pct_e26_e31 .github/workflows/pct-e1-e25-campaign.yml
git commit -m "test: bind frozen cross-branch solver corpus"
```

---

### Task 2: E27 Sanitization, Probe Bank, Exact Ambiguity Solver, and Baselines

**Files:**
- Create: `experiments/pct_e26_e31/cases.py`
- Create: `experiments/pct_e26_e31/probes.py`
- Create: `experiments/pct_e26_e31/solver.py`
- Create: `experiments/pct_e26_e31/baselines.py`
- Create: `experiments/pct_e26_e31/test_e27_core.py`

**Interfaces:**
- `build_r1_cases(corpus: KnowledgeCorpus) -> list[HeldoutCase]`
- `sanitize_case(corpus: KnowledgeCorpus, case: HeldoutCase) -> SanitizedCase`
- `compute_probe_vector(case: SanitizedCase, candidate_relation: str) -> tuple[tuple[str, object], ...]`
- `solve_case(case: SanitizedCase) -> SolverResult`
- `run_baseline(name: Literal["B0","B1","B2","B3"], case: SanitizedCase) -> SolverResult`
- `SolverResult(verdict, predicted_relation, ambiguity_set, evidence_keys, trace_digest)`.

- [ ] **Step 1: Write answer-isolation and exact-ambiguity RED tests**

```python
def test_sanitized_case_removes_direct_target_edge(corpus, r1_case):
    s = sanitize_case(corpus, r1_case)
    assert r1_case.edge_id not in s.visible_edge_ids
    assert r1_case.sealed_relation not in s.direct_target_labels


def test_solver_refuses_when_two_relation_classes_remain_consistent(ambiguous_case):
    out = solve_case(ambiguous_case)
    assert out.verdict == "NOT_ESTABLISHED"
    assert len(out.ambiguity_set) >= 2
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e27_core.py`

Expected: FAIL because case/probe/solver modules are absent.

- [ ] **Step 3: Implement immutable held-out case records and sanitization**

Build case IDs from canonical JSON hashes. Keep sealed answer fields on verifier objects only. `SanitizedCase` must contain no target edge, answer relation, verifier grouping key, or answer-manifest path.

- [ ] **Step 4: Implement the frozen discrete probe bank**

Probe families must include endpoint node types, source identities, visible representation profile, typed one-hop neighborhoods, typed path signatures up to the frozen depth, dependency orientation, multipath signatures, and available cross-view evidence. Return sorted immutable key/value tuples so probe vectors hash deterministically.

- [ ] **Step 5: Implement exact candidate-set solver and B0–B3 controls**

For B4, enumerate all candidate relation classes and retain only classes consistent with the sanitized evidence and fail-closed rules. Emit a positive class only when one candidate remains. B0–B3 operate on the same cases but with restricted evidence surfaces.

- [ ] **Step 6: Run GREEN gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e27_core.py`

Expected: PASS, including refusal on constructed ambiguity.

- [ ] **Step 7: Commit Task 2**

```bash
git add experiments/pct_e26_e31
git commit -m "feat: add sealed relational solver core"
```

---

### Task 3: E27 R1–R4 Campaign, Cluster/Domain Holdouts, and Solver-Signal Metrics

**Files:**
- Create: `experiments/pct_e26_e31/e27.py`
- Create: `experiments/pct_e26_e31/test_e27_campaign.py`

**Interfaces:**
- `build_r2_cluster_cases(corpus: KnowledgeCorpus) -> list[HeldoutCase]`
- `build_r3_domain_cases(corpus: KnowledgeCorpus) -> list[HeldoutCase]`
- `build_r4_controls(corpus: KnowledgeCorpus) -> list[HeldoutCase]`
- `run_e27(corpus: KnowledgeCorpus, harness_sha: str) -> dict`
- `evaluate_solver_signal(report: dict) -> dict` returning explicit H1 support gates.

- [ ] **Step 1: Write RED tests for verifier-only grouping and corruption refusal**

```python
def test_r2_group_key_is_not_solver_visible(corpus):
    case = build_r2_cluster_cases(corpus)[0]
    s = sanitize_case(corpus, case)
    assert "canonical_holdout_group" not in s.metadata


def test_r4_false_certainty_is_zero(corpus):
    report = run_e27(corpus, "HARNESS_TEST_SHA")
    assert report["R4"]["false_certainty_count"] == 0
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e27_campaign.py`

Expected: FAIL because campaign builders do not exist.

- [ ] **Step 3: Implement exhaustive R1, canonical-cluster R2, leave-one-domain-out R3, and deterministic R4 controls**

Generate the holdout blocks from verifier-side metadata, then construct solver-visible sanitized graphs. R4 must include endpoint swap, source-binding corruption, scope corruption, relation-type corruption, and evidence-erasure ambiguity controls.

- [ ] **Step 4: Implement paired B0–B4 scoring**

For each tier, record total, answered, `NOT_ESTABLISHED`, exact class accuracy, selective accuracy, false certainty, confusion matrix, ambiguity-set histogram, and per-case baseline outputs. Evaluate the frozen solver-signal criterion exactly as written in the spec.

- [ ] **Step 5: Run GREEN gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e27_campaign.py`

Expected: PASS of validity tests. Scientific H1 support may be true or false; tests assert deterministic calculation, not a desired scientific outcome.

- [ ] **Step 6: Commit Task 3**

```bash
git add experiments/pct_e26_e31
git commit -m "feat: run sealed held-out solver campaign"
```

---

### Task 4: E28 Minimal Evidence, Erasure Robustness, and Null-Space Audit

**Files:**
- Create: `experiments/pct_e26_e31/e28.py`
- Create: `experiments/pct_e26_e31/test_e28.py`

**Interfaces:**
- `certify_minimum_evidence(case: SanitizedCase, result: SolverResult, probe_bank: tuple[str, ...], max_exact_bank: int) -> MinimumEvidenceResult`
- `run_e28(e27_report: dict, corpus: KnowledgeCorpus, harness_sha: str) -> dict`

- [ ] **Step 1: Write RED tests that prevent false exact-minimum claims**

```python
def test_minimum_is_exact_only_after_all_smaller_sizes_excluded(small_case):
    r = certify_minimum_evidence(small_case.case, small_case.result, small_case.bank, 64)
    assert r.status == "EXACT_MINIMUM_CERTIFIED"
    assert all(r.infeasible_by_size[k] for k in range(r.minimum_size))


def test_resource_bound_returns_inconclusive_not_exact(large_case):
    r = certify_minimum_evidence(large_case.case, large_case.result, large_case.bank, 4)
    assert r.status == "INCONCLUSIVE_MINIMUM"
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e28.py`

Expected: FAIL because E28 does not exist.

- [ ] **Step 3: Implement deterministic subset search, erasure tolerance, and ambiguity/null-space reporting**

Enumerate subset cardinalities from 0 upward for exact-sized banks. For larger banks, keep the best upper bound and return `INCONCLUSIVE_MINIMUM` unless every smaller size is excluded. Re-run the exact ambiguity solver after every critical evidence removal.

- [ ] **Step 4: Run GREEN gate and commit**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e28.py`

```bash
git add experiments/pct_e26_e31
git commit -m "feat: audit minimal evidence and graph null spaces"
```

---

### Task 5: E29 Structural Rule Discovery and Counterexample Falsification

**Files:**
- Create: `experiments/pct_e26_e31/e29.py`
- Create: `experiments/pct_e26_e31/test_e29.py`

**Interfaces:**
- `enumerate_candidate_rules(training_cases: list[SanitizedCase], max_width: int = 3, min_support_edges: int = 3, min_canonical_objects: int = 2) -> list[CandidateRule]`
- `falsify_rule(rule: CandidateRule, visible_cases: list[SanitizedCase]) -> RuleAudit`
- `run_e29(corpus: KnowledgeCorpus, e27_report: dict, harness_sha: str) -> dict`

- [ ] **Step 1: Write RED tests for support threshold and counterexample precedence**

```python
def test_rule_requires_three_edges_and_two_canonical_objects(training_cases):
    rules = enumerate_candidate_rules(training_cases)
    assert all(r.support_edge_count >= 3 for r in rules)
    assert all(r.support_canonical_count >= 2 for r in rules)


def test_one_counterexample_defeats_universal_rule(rule_with_counterexample, cases):
    audit = falsify_rule(rule_with_counterexample, cases)
    assert audit.status == "DEFEATED_BY_COUNTEREXAMPLE"
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e29.py`

Expected: FAIL because E29 does not exist.

- [ ] **Step 3: Implement frozen low-complexity rule enumeration and exhaustive visible-corpus falsification**

Candidate antecedents are conjunctions of one to three probe predicates. Freeze candidates before sealed holdout evaluation. Record rescued scope restrictions separately; never rewrite an overbroad rule into success without showing the counterexample that forced narrowing.

- [ ] **Step 4: Run GREEN gate and commit**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e29.py`

```bash
git add experiments/pct_e26_e31
git commit -m "feat: add relational rule discovery and falsification"
```

---

### Task 6: E30 Main-PCT Subprocess Adapter and Adversarial Replay

**Files:**
- Create: `experiments/pct_e26_e31/main_adapter.py`
- Create: `experiments/pct_e26_e31/main_runner_protocol.py`
- Create: `experiments/pct_e26_e31/e30.py`
- Create: `experiments/pct_e26_e31/test_e30.py`

**Interfaces:**
- `classify_main_capabilities(main_root: Path) -> dict[str, str]`
- `invoke_main_pct(main_root: Path, request: dict) -> dict`
- `run_e30(main_root: Path, harness_sha: str) -> dict`

- [ ] **Step 1: Write RED tests for process isolation and adapter honesty**

```python
def test_main_invocation_runs_in_separate_process(frozen_main):
    out = invoke_main_pct(frozen_main, {"op": "runtime_identity"})
    assert out["checkout_sha"] == KNOWLEDGE_BASELINE_SHA
    assert "experiments.pct_e25" not in out["loaded_modules"]


def test_capability_not_exposed_is_not_scored_failure(frozen_main):
    report = run_e30(frozen_main, "HARNESS_TEST_SHA")
    for row in report["replays"]:
        if row["classification"] == "CAPABILITY_NOT_EXPOSED":
            assert row["scored"] is False
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e30.py`

Expected: FAIL because the subprocess protocol is absent.

- [ ] **Step 3: Implement JSON subprocess protocol**

Launch `sys.executable -m experiments.pct_e26_e31.main_runner_protocol` with environment containing only the frozen-main root plus required site-packages on `PYTHONPATH`. The protocol may translate request payloads into existing `mapeogeo.pct` calls but must not reimplement the tested mathematics.

- [ ] **Step 4: Implement the preregistered E5/E9/E11/E14/E16/E17/E18/E23/E24 replay matrix**

Classify every row before scoring as `DIRECT_REPLAY`, `ADAPTER_REQUIRED`, `NOT_APPLICABLE`, or `CAPABILITY_NOT_EXPOSED`. Preserve branch-oracle expected behavior as immutable test fixtures.

- [ ] **Step 5: Run GREEN gate and commit**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e30.py`

```bash
git add experiments/pct_e26_e31
git commit -m "feat: replay E-series adversaries against frozen main PCT"
```

---

### Task 7: E31 Bidirectional Closure and Lifecycle-Bound Receipts

**Files:**
- Create: `experiments/pct_e26_e31/e31.py`
- Create: `experiments/pct_e26_e31/test_e31.py`
- Reuse without modification: `experiments/pct_e25ij/receipts.py`, `experiments/pct_e25ij/lifecycle.py`

**Interfaces:**
- `build_e31_receipts(e27: dict, e28: dict, e29: dict, e30: dict, harness_sha: str) -> dict`
- `derive_e31_closure(receipts: dict) -> dict`
- `run_e31(...) -> dict`

- [ ] **Step 1: Write RED tests for complete bindings and explicit C3/C4 applicability**

```python
def test_every_scored_case_binds_both_baselines_recipe_harness_and_hashes(e31):
    for receipt in e31["receipts"]:
        p = receipt["payload"]
        assert p["solver_baseline_sha"] == SOLVER_BASELINE_SHA
        assert p["knowledge_baseline_sha"] == KNOWLEDGE_BASELINE_SHA
        assert p["campaign_harness_sha"]
        assert p["solver_recipe_sha256"]
        assert p["input_sha256"] and p["output_sha256"] and p["answer_sha256"]


def test_c3_c4_are_never_implicit_pass(e31):
    assert all(x["C3"] in {"PASS", "NOT_APPLICABLE", "NOT_ESTABLISHED"} for x in e31["closure"])
    assert all(x["C4"] in {"PASS", "NOT_APPLICABLE", "NOT_ESTABLISHED"} for x in e31["closure"])
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e31.py`

Expected: FAIL because E31 does not exist.

- [ ] **Step 3: Implement receipts using existing E25I/J immutable receipt semantics**

Direction A binds solver output to sealed-main answer evidence. Direction B binds main-PCT replay output to branch adversarial oracle evidence. Use C3/C4 only for actually applicable chain/homology cases; otherwise store explicit `NOT_APPLICABLE`.

- [ ] **Step 4: Add stale-input lifecycle test**

Create a synthetic event that changes one required artifact digest or harness SHA and assert dependent E31 receipts become stale without reactivating historical descendants.

- [ ] **Step 5: Run GREEN gate and commit**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e31.py`

```bash
git add experiments/pct_e26_e31
git commit -m "feat: bind bidirectional solver verification receipts"
```

---

### Task 8: Deterministic Evidence Generation, Frozen Regression, Report, and Full CI

**Files:**
- Create: `experiments/pct_e26_e31/generate_evidence.py`
- Create: `experiments/pct_e26_e31/test_evidence.py`
- Create after inspected generation:
  - `evidence/pct_e26_cross_branch_manifest.json`
  - `evidence/pct_e27_heldout_relational_recovery.json`
  - `evidence/pct_e28_minimal_evidence_nullspace.json`
  - `evidence/pct_e29_rule_discovery_falsification.json`
  - `evidence/pct_e30_main_pct_adversarial_replay.json`
  - `evidence/pct_e31_bidirectional_closure.json`
- Create: `docs/PCT_E26_E31_CROSS_BRANCH_SOLVER_VALIDATION_REPORT.md`
- Modify: `.github/workflows/pct-e1-e25-campaign.yml`

**Interfaces:**
- `generate_all(repo_root: Path, frozen_main_root: Path, frozen_solver_root: Path, out_dir: Path, harness_sha: str) -> dict[str, Path]`

- [ ] **Step 1: Write frozen-evidence RED test before committing evidence files**

```python
def test_frozen_e26_e31_evidence_matches_fresh_generation(tmp_path, frozen_main, frozen_solver, repo_root):
    generated = generate_all(repo_root, frozen_main, frozen_solver, tmp_path, current_head_sha(repo_root))
    for name, path in generated.items():
        frozen = repo_root / "evidence" / name
        assert json.loads(frozen.read_text()) == json.loads(path.read_text())
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_evidence.py`

Expected: FAIL with missing frozen E26 evidence files.

- [ ] **Step 3: Add CI candidate generation and upload without writes**

Generate to `generated-e26-e31/`, upload as an Actions artifact, and keep workflow `contents: read`. Do not copy generated files into tracked `evidence/` in CI.

- [ ] **Step 4: Run candidate campaign and inspect scientific outputs before freezing**

Run:

```bash
python -m experiments.pct_e26_e31.generate_evidence \
  --main-root frozen-main \
  --solver-root frozen-solver \
  --out-dir generated-e26-e31 \
  --harness-sha "$(git rev-parse HEAD)"
```

Inspect E26 discrepancies, E27 H1 gates, E28 exact/inconclusive minimum counts, E29 defeated/surviving candidate rules, E30 replay classifications, and E31 closure. Do not alter solver rules based on sealed outcomes.

- [ ] **Step 5: Freeze exact generated JSON and rerun evidence regression**

Copy the inspected candidate JSON bytes into the six tracked evidence paths, then run:

`python -m pytest -q experiments/pct_e26_e31/test_evidence.py`

Expected: PASS with byte/semantic equivalence to fresh deterministic generation.

- [ ] **Step 6: Write the final report from frozen evidence only**

The report must give three separate conclusions: solver transfer, main implementation replay, and bidirectional trust. It must report negative/inconclusive outcomes without averaging them into an aggregate score and preserve the claim boundary from the spec.

- [ ] **Step 7: Run the complete branch regression suite**

Run:

```bash
python -m pytest -q \
  experiments/pct_e1_e25/test_campaign.py \
  experiments/pct_e25bc/test_audit.py \
  experiments/pct_e25def/test_e25def.py \
  experiments/pct_e25gh/test_e25gh.py \
  experiments/pct_e25ij/test_e25ij.py \
  experiments/pct_e25ij/test_evidence.py \
  experiments/pct_e26_e31/test_e26.py \
  experiments/pct_e26_e31/test_e27_core.py \
  experiments/pct_e26_e31/test_e27_campaign.py \
  experiments/pct_e26_e31/test_e28.py \
  experiments/pct_e26_e31/test_e29.py \
  experiments/pct_e26_e31/test_e30.py \
  experiments/pct_e26_e31/test_e31.py \
  experiments/pct_e26_e31/test_evidence.py
```

Expected: zero failures. Scientific hypothesis support is read from frozen evidence, not inferred from test pass count.

- [ ] **Step 8: Commit report/evidence/workflow and verify remote CI on exact head**

```bash
git add experiments/pct_e26_e31 evidence/pct_e2*.json docs/PCT_E26_E31_CROSS_BRANCH_SOLVER_VALIDATION_REPORT.md .github/workflows/pct-e1-e25-campaign.yml
git commit -m "feat: complete E26-E31 cross-branch solver validation"
```

Verify the workflow on the exact resulting branch SHA and read the full job log before claiming completion.
