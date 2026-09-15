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
- Main-side PCT execution occurs only through a JSON subprocess boundary whose `PYTHONPATH` contains frozen `main` plus normal site-packages, never the experimental branch root.
- `SAME_SEMANTICS`, `SCOPED_OVERLAP`, and `RELATED_TO` remain distinct classes.
- `FORMAL_LINKED` must never be promoted to `KERNEL_VERIFIED` without independent kernel evidence.
- Ambiguity is represented by an exact candidate set; no confidence score may override non-uniqueness.
- `campaign_harness_sha` means the deterministic SHA-256 digest of the executable E26–E31 harness source set, not the mutable branch HEAD. `compute_harness_sha()` hashes sorted relative paths plus exact bytes for the production `.py` files under `experiments/pct_e26_e31`, excluding `test_*.py`, generated evidence, caches, and documentation. This avoids a circular identity when evidence/report commits advance the branch.
- Every result binds `solver_baseline_sha`, `knowledge_baseline_sha`, `campaign_harness_sha`, `solver_recipe_sha256`, sanitized input hash, output hash, and sealed answer hash.
- Frozen evidence is generated to an uncommitted candidate directory first and committed only after deterministic comparison tests exist.
- Prior E1–E25J implementation/evidence are immutable inputs. If they require modification, stop this campaign and preregister a new solver baseline.

---

### Task 1: E26 Frozen Corpus Binding and Separate-Checkout Contract

**Files:**
- Create: `experiments/pct_e26_e31/__init__.py`
- Create: `experiments/pct_e26_e31/constants.py`
- Create: `experiments/pct_e26_e31/identity.py`
- Create: `experiments/pct_e26_e31/corpus.py`
- Create: `experiments/pct_e26_e31/test_e26.py`
- Modify: `.github/workflows/pct-e1-e25-campaign.yml`

**Interfaces:**
- `compute_harness_sha(repo_root: Path) -> str`
- `verify_frozen_checkout(path: Path, expected_sha: str) -> None`
- `load_knowledge_corpus(main_root: Path) -> KnowledgeCorpus`
- `build_e26_manifest(main_root: Path, repo_root: Path) -> dict`
- `KnowledgeCorpus` contains full graph, direct graph counts, semantic edges, canonical/source/domain indexes, artifact digests, and eligibility indexes. It is verifier-side only.

- [ ] **Step 1: Write the RED tests for pinned checkouts, harness hashing, and graph reconstruction**

```python
from experiments.pct_e26_e31.constants import KNOWLEDGE_BASELINE_SHA, SOLVER_BASELINE_SHA
from experiments.pct_e26_e31.corpus import build_e26_manifest
from experiments.pct_e26_e31.identity import compute_harness_sha


def test_harness_sha_is_content_derived(repo_root):
    h = compute_harness_sha(repo_root)
    assert len(h) == 64
    assert int(h, 16) >= 0


def test_e26_manifest_binds_frozen_inputs(main_checkout, repo_root):
    m = build_e26_manifest(main_checkout, repo_root)
    assert m["solver_baseline_sha"] == SOLVER_BASELINE_SHA
    assert m["knowledge_baseline_sha"] == KNOWLEDGE_BASELINE_SHA
    assert m["campaign_harness_sha"] == compute_harness_sha(repo_root)


def test_e26_counts_come_from_graph(main_checkout, repo_root):
    m = build_e26_manifest(main_checkout, repo_root)
    assert m["direct_graph_counts"]["source_declarations"] > 0
    assert m["direct_graph_counts"]["canonical_objects"] > 0
    assert m["direct_graph_counts"]["semantic_bridges"] > 0
    assert set(m["semantic_relation_types"]) >= {"SAME_SEMANTICS", "SCOPED_OVERLAP", "RELATED_TO"}
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e26.py`

Expected: collection/import failure because the package does not yet exist.

- [ ] **Step 3: Implement identity and corpus reconstruction**

`verify_frozen_checkout()` runs `git -C <path> rev-parse HEAD`. `compute_harness_sha()` hashes sorted production file paths and bytes with length-delimited framing. `load_knowledge_corpus()` locates `artifacts/analysis_v0_15_1/mapeogeo_v0_15_1_graph.json.gz`, hashes the raw artifact bytes, loads it, and builds direct indexes. Report/manifest disagreement is recorded under `discrepancies`; source files are never repaired.

- [ ] **Step 4: Add two pinned read-only CI checkouts**

```yaml
permissions:
  contents: read

- name: Checkout frozen solver baseline
  uses: actions/checkout@v4
  with:
    ref: 6c9333ed3ec48a298ad943a74e72a01fa1ffcd78
    path: .crossbranch/frozen-solver

- name: Checkout frozen knowledge baseline
  uses: actions/checkout@v4
  with:
    ref: fd2d90c00cb71951fdfd7cd1e7e22a8f0552f97f
    path: .crossbranch/frozen-main
```

- [ ] **Step 5: Run GREEN gate and commit**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e26.py`

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

- [ ] **Step 1: Write answer-isolation and ambiguity RED tests**

```python
def test_sanitized_case_removes_direct_target_edge(corpus, r1_case):
    s = sanitize_case(corpus, r1_case)
    assert r1_case.edge_id not in s.visible_edge_ids
    assert r1_case.sealed_relation not in s.direct_target_labels


def test_solver_refuses_nonunique_case(ambiguous_case):
    out = solve_case(ambiguous_case)
    assert out.verdict == "NOT_ESTABLISHED"
    assert len(out.ambiguity_set) >= 2
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e27_core.py`

- [ ] **Step 3: Implement immutable held-out case records and sanitization**

Case IDs are SHA-256 hashes of canonical JSON. Sealed relation, cluster grouping, answer manifest paths, and verifier-only metadata never appear in `SanitizedCase`.

- [ ] **Step 4: Implement the frozen discrete probe bank**

Probe families: endpoint node types, source identities, visible representation profile, typed one-hop neighborhoods, dependency orientation, typed path signatures, multipath signatures, and available cross-view evidence. Return sorted immutable key/value tuples.

- [ ] **Step 5: Implement B4 exact candidate-set solving and B0–B3 controls**

Enumerate candidate relation classes and retain only those compatible with visible evidence and fail-closed rules. Positive output requires a singleton ambiguity set. B0–B3 use the same cases with progressively restricted information.

- [ ] **Step 6: Run GREEN gate and commit**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e27_core.py`

```bash
git add experiments/pct_e26_e31
git commit -m "feat: add sealed relational solver core"
```

---

### Task 3: E27 R1–R4 Campaign and Solver-Signal Metrics

**Files:**
- Create: `experiments/pct_e26_e31/e27.py`
- Create: `experiments/pct_e26_e31/test_e27_campaign.py`

**Interfaces:**
- `build_r2_cluster_cases(corpus: KnowledgeCorpus) -> list[HeldoutCase]`
- `build_r3_domain_cases(corpus: KnowledgeCorpus) -> list[HeldoutCase]`
- `build_r4_controls(corpus: KnowledgeCorpus) -> list[HeldoutCase]`
- `run_e27(corpus: KnowledgeCorpus, repo_root: Path) -> dict`
- `evaluate_solver_signal(report: dict) -> dict`

- [ ] **Step 1: Write RED tests for verifier-only grouping and refusal controls**

```python
def test_r2_group_key_is_not_solver_visible(corpus):
    case = build_r2_cluster_cases(corpus)[0]
    s = sanitize_case(corpus, case)
    assert "canonical_holdout_group" not in s.metadata


def test_r4_false_certainty_is_zero(corpus, repo_root):
    report = run_e27(corpus, repo_root)
    assert report["R4"]["false_certainty_count"] == 0
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e27_campaign.py`

- [ ] **Step 3: Implement exhaustive R1, cluster R2, leave-one-domain-out R3, and deterministic R4**

R4 includes endpoint swap, source-binding corruption, scope corruption, relation-type corruption, and deliberate evidence-erasure ambiguity. Holdout grouping is generated on the verifier side and stripped before solving.

- [ ] **Step 4: Implement paired B0–B4 metrics and frozen H1 gates**

Record totals, answered, `NOT_ESTABLISHED`, exact class accuracy, selective accuracy, false certainty, confusion matrices, ambiguity histograms, per-case baseline outputs, and stratification by domain/relation/source multiplicity/richness. Tests verify deterministic metric calculation, not a desired scientific outcome.

- [ ] **Step 5: Run GREEN gate and commit**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e27_campaign.py`

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
- `run_e28(e27_report: dict, corpus: KnowledgeCorpus, repo_root: Path) -> dict`

- [ ] **Step 1: Write RED tests that forbid false exact-minimum claims**

```python
def test_exact_minimum_requires_all_smaller_sizes_excluded(small_case):
    r = certify_minimum_evidence(small_case.case, small_case.result, small_case.bank, 64)
    assert r.status == "EXACT_MINIMUM_CERTIFIED"
    assert all(r.infeasible_by_size[k] for k in range(r.minimum_size))


def test_resource_bound_is_inconclusive(large_case):
    r = certify_minimum_evidence(large_case.case, large_case.result, large_case.bank, 4)
    assert r.status == "INCONCLUSIVE_MINIMUM"
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e28.py`

- [ ] **Step 3: Implement deterministic subset search and erasure/null-space analysis**

Enumerate subset cardinalities from zero upward when exact certification is feasible. For larger banks retain only an upper bound and `INCONCLUSIVE_MINIMUM`. Re-run the exact ambiguity solver after every critical evidence removal.

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
- `run_e29(corpus: KnowledgeCorpus, e27_report: dict, repo_root: Path) -> dict`

- [ ] **Step 1: Write RED tests for support threshold and counterexample precedence**

```python
def test_rule_support_threshold(training_cases):
    rules = enumerate_candidate_rules(training_cases)
    assert all(r.support_edge_count >= 3 for r in rules)
    assert all(r.support_canonical_count >= 2 for r in rules)


def test_counterexample_defeats_rule(rule_with_counterexample, cases):
    audit = falsify_rule(rule_with_counterexample, cases)
    assert audit.status == "DEFEATED_BY_COUNTEREXAMPLE"
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e29.py`

- [ ] **Step 3: Implement frozen one-to-three-predicate rule enumeration and exhaustive visible-corpus falsification**

Freeze candidate rules before sealed evaluation. Record counterexamples and any narrower rescued scope explicitly. Survivors remain `CANDIDATE_SURVIVED_VISIBLE_SEARCH`, never theorem status.

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
- `invoke_main_pct(repo_root: Path, main_root: Path, request: dict) -> dict`
- `run_e30(repo_root: Path, main_root: Path) -> dict`

- [ ] **Step 1: Write RED tests for process isolation and adapter honesty**

```python
def test_main_invocation_is_frozen_and_isolated(repo_root, frozen_main):
    out = invoke_main_pct(repo_root, frozen_main, {"op": "runtime_identity"})
    assert out["checkout_sha"] == KNOWLEDGE_BASELINE_SHA
    assert out["experimental_branch_on_sys_path"] is False


def test_unexposed_capability_is_not_scored_failure(repo_root, frozen_main):
    report = run_e30(repo_root, frozen_main)
    for row in report["replays"]:
        if row["classification"] == "CAPABILITY_NOT_EXPOSED":
            assert row["scored"] is False
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e30.py`

- [ ] **Step 3: Implement the JSON subprocess boundary without importing branch code into main**

Invoke the protocol by absolute file path, not `-m`:

```python
cmd = [sys.executable, str(repo_root / "experiments/pct_e26_e31/main_runner_protocol.py")]
env = os.environ.copy()
env["PYTHONPATH"] = str(main_root)
subprocess.run(cmd, input=json.dumps(request), text=True, cwd=main_root, env=env, ...)
```

`main_runner_protocol.py` imports only stdlib plus `mapeogeo.pct` from the frozen main checkout. It returns runtime identity and operation results as JSON. The adapter may translate data representation only; it may not implement the tested capability.

- [ ] **Step 4: Implement the E5/E9/E11/E14/E16/E17/E18/E23/E24 replay matrix**

Classify each row first as `DIRECT_REPLAY`, `ADAPTER_REQUIRED`, `NOT_APPLICABLE`, or `CAPABILITY_NOT_EXPOSED`; only the first two are scored pass/fail.

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
- `build_e31_receipts(e27: dict, e28: dict, e29: dict, e30: dict, repo_root: Path) -> dict`
- `derive_e31_closure(receipts: dict) -> dict`
- `run_e31(...) -> dict`

- [ ] **Step 1: Write RED tests for complete cryptographic bindings and explicit applicability**

```python
def test_every_scored_case_has_complete_bindings(e31):
    for receipt in e31["receipts"]:
        p = receipt["payload"]
        assert p["solver_baseline_sha"] == SOLVER_BASELINE_SHA
        assert p["knowledge_baseline_sha"] == KNOWLEDGE_BASELINE_SHA
        assert len(p["campaign_harness_sha"]) == 64
        assert p["solver_recipe_sha256"]
        assert p["input_sha256"] and p["output_sha256"] and p["answer_sha256"]


def test_c3_c4_are_never_implicit_pass(e31):
    allowed = {"PASS", "NOT_APPLICABLE", "NOT_ESTABLISHED"}
    assert all(x["C3"] in allowed and x["C4"] in allowed for x in e31["closure"])
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_e31.py`

- [ ] **Step 3: Implement receipts using existing E25I/J immutable semantics**

Direction A binds branch solver outputs to sealed-main answer evidence. Direction B binds main-PCT replay outputs to branch adversarial oracle evidence. C3/C4 appear only where chain/homology contracts are meaningful.

- [ ] **Step 4: Add lifecycle invalidation tests**

Change one synthetic artifact digest, recipe digest, or harness digest and assert dependent E31 receipts become stale without historical reactivation.

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
- `generate_all(repo_root: Path, frozen_main_root: Path, frozen_solver_root: Path, out_dir: Path) -> dict[str, Path]`

- [ ] **Step 1: Write the frozen-evidence RED test before evidence exists**

```python
def test_frozen_e26_e31_matches_fresh_generation(tmp_path, frozen_main, frozen_solver, repo_root):
    generated = generate_all(repo_root, frozen_main, frozen_solver, tmp_path)
    for name, path in generated.items():
        frozen = repo_root / "evidence" / name
        assert frozen.read_bytes() == path.read_bytes()
```

- [ ] **Step 2: Run RED gate**

Run: `python -m pytest -q experiments/pct_e26_e31/test_evidence.py`

Expected: missing frozen E26–E31 evidence files.

- [ ] **Step 3: Add read-only CI candidate generation/upload**

Generate to `generated-e26-e31/`, upload that directory as an artifact, and keep `contents: read`. CI must also run `compute_harness_sha()` and include it in all generated files.

- [ ] **Step 4: Run candidate campaign and inspect scientific outputs before freezing**

```bash
python -m experiments.pct_e26_e31.generate_evidence \
  --main-root .crossbranch/frozen-main \
  --solver-root .crossbranch/frozen-solver \
  --out-dir generated-e26-e31
```

Inspect E26 discrepancies, E27 H1 gates, E28 exact/inconclusive minimum counts, E29 defeated/surviving rules, E30 replay classifications, and E31 closure. Do not tune solver rules after seeing sealed outcomes.

- [ ] **Step 5: Freeze exact generated bytes and rerun evidence regression**

Copy the six inspected candidate JSON files into the six tracked evidence paths. Because `campaign_harness_sha` is source-content-derived, later evidence/report commits do not alter it unless executable harness code changes.

Run: `python -m pytest -q experiments/pct_e26_e31/test_evidence.py`

Expected: PASS with byte-equivalence.

- [ ] **Step 6: Write the final report from frozen evidence only**

Report three separate conclusions: solver transfer, main implementation replay, and bidirectional trust. Preserve negative/inconclusive results and the spec claim boundary.

- [ ] **Step 7: Run complete regression**

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

Expected: zero failures. Test pass count validates machinery; scientific hypothesis support comes only from frozen evidence.

- [ ] **Step 8: Commit exact files and verify remote CI on exact head**

```bash
git add \
  experiments/pct_e26_e31 \
  evidence/pct_e26_cross_branch_manifest.json \
  evidence/pct_e27_heldout_relational_recovery.json \
  evidence/pct_e28_minimal_evidence_nullspace.json \
  evidence/pct_e29_rule_discovery_falsification.json \
  evidence/pct_e30_main_pct_adversarial_replay.json \
  evidence/pct_e31_bidirectional_closure.json \
  docs/PCT_E26_E31_CROSS_BRANCH_SOLVER_VALIDATION_REPORT.md \
  .github/workflows/pct-e1-e25-campaign.yml
git commit -m "feat: complete E26-E31 cross-branch solver validation"
```

Read the full CI job log for the exact resulting SHA before any completion claim.
