# Goal-Directed Mixed-Domain Operator Solver Implementation Plan

> **Historical implementation plan — not current v0.20 authority.** The macro
> execution and support language below is preserved as a record of the original
> V1/V2 design. It does not describe current v0.20 behavior: v0.20 treats macro
> proposals as inert and grants them no execution, conservation, or efficiency
> authority.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and test a structured-goal mathematical solver that searches and composes exact, symbolic, and numerical operators, comparing explicit, inferred, and hybrid typing with and without validated macro synthesis.

**Architecture:** A new `experiments/pct_goal_solver` package contains immutable goal/artifact/operator contracts, a deterministic operator registry, a best-first planner, inferred compatibility calibration, macro synthesis, parameterized mixed-domain goal generators, independent verifiers, and a campaign scorer. Existing E1-E31 code remains an immutable historical oracle; `main` remains read-only.

**Tech Stack:** Python 3.12, dataclasses, heapq, fractions, itertools, NumPy, SymPy, NetworkX, Shapely, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-16-goal-directed-mixed-domain-operator-solver-design.md`

## Global Constraints

- Work only on `agent/pct-computational-architecture`; do not mutate `main`.
- Scored inputs are structured goals only; no LLM calls inside the scientific core.
- One mixed operator space must include exact, symbolic, and numerical tasks.
- Score `EXPLICIT`, `INFERRED`, and `HYBRID` typing modes.
- Score `PRIMITIVE` and `SYNTHESIZED` composition modes.
- Every positive answer must end in an independent verifier result.
- Search-budget exhaustion returns `NOT_ESTABLISHED`; inapplicability returns `NOT_APPLICABLE`.
- Byte-for-byte evidence freezing is not a scientific gate; CI artifacts are sufficient for campaign output.

---

### Task 1: Core Contracts and Deterministic Goal Fixtures

**Files:**
- Create: `experiments/pct_goal_solver/__init__.py`
- Create: `experiments/pct_goal_solver/model.py`
- Create: `experiments/pct_goal_solver/goals.py`
- Create: `experiments/pct_goal_solver/test_model_goals.py`

**Interfaces:**
- Produces: `Artifact`, `TargetSpec`, `GoalSpec`, `SolverVisibleGoal`, `Applicability`, `VerificationResult`, `OperatorFailure`, `SolveTrace`.
- Produces: `build_goal_corpus() -> dict[str, list[GoalSpec]]` with `CALIBRATION`, `VALIDATION`, and `SEALED` partitions.

- [ ] **Step 1: Write failing schema/isolation tests**

```python
from experiments.pct_goal_solver.goals import build_goal_corpus


def test_sealed_answers_are_not_solver_visible():
    corpus = build_goal_corpus()
    goal = corpus["SEALED"][0]
    visible = goal.solver_visible()
    assert not hasattr(visible, "sealed_expected_result")
    assert goal.sealed_expected_result is not None


def test_corpus_covers_all_goal_families_and_exactness_classes():
    corpus = build_goal_corpus()
    families = {g.family for split in corpus.values() for g in split}
    assert families == {f"G{i}" for i in range(1, 13)}
    classes = {a.exactness_class for split in corpus.values() for g in split for a in g.inputs.values()}
    assert {"EXACT", "SYMBOLIC", "NUMERICAL"} <= classes
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `python -m pytest -q experiments/pct_goal_solver/test_model_goals.py`

Expected: import/module failure.

- [ ] **Step 3: Implement immutable contracts and deterministic seeded goal generators**

Key signatures:

```python
@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    semantic_type: str
    representation_class: str
    value: Any
    exactness_class: str
    metadata: tuple[tuple[str, Any], ...] = ()
    provenance: tuple[str, ...] = ()

@dataclass(frozen=True)
class GoalSpec:
    goal_id: str
    family: str
    inputs: dict[str, Artifact]
    target: TargetSpec
    constraints: tuple[tuple[str, Any], ...]
    allowed_numeric_tolerance: float
    required_verifier_class: str
    sealed_expected_result: Any
    sealed_reference_path: tuple[str, ...]

    def solver_visible(self) -> SolverVisibleGoal: ...
```

Generate at least 3 calibration, 1 validation, and 2 sealed goals per family, with seeded parameters and adversarial controls in G2/G3/G6/G9.

- [ ] **Step 4: Run schema tests GREEN**

Run: `python -m pytest -q experiments/pct_goal_solver/test_model_goals.py`

- [ ] **Step 5: Commit**

```bash
git add experiments/pct_goal_solver
 git commit -m "feat: add mixed-domain solver goal contracts"
```

---

### Task 2: Primitive Operator Registry

**Files:**
- Create: `experiments/pct_goal_solver/operators.py`
- Create: `experiments/pct_goal_solver/verifiers.py`
- Create: `experiments/pct_goal_solver/test_operators.py`

**Interfaces:**
- Consumes: `Artifact`, `Applicability`, `VerificationResult`.
- Produces: `OperatorSpec` and `build_operator_registry() -> dict[str, OperatorSpec]`.
- Registry must expose the 33 operator IDs frozen in the spec.

- [ ] **Step 1: Write failing registry/parity tests**

```python
from experiments.pct_goal_solver.operators import build_operator_registry


def test_registry_contains_frozen_operator_ids():
    reg = build_operator_registry()
    assert len(reg) == 33
    assert {"MOBIUS_INVERT_BOOLEAN", "CHAIN_MAP_CHECK", "SYMBOLIC_IDENTITY_CHECK",
            "CONDITIONING_RISK_CHECK", "STEINER_OFFSET_PREDICT",
            "SEPARATION_ESCALATE", "FALSIFY_CANDIDATE", "VERIFY_CANDIDATE"} <= set(reg)


def test_mobius_round_trip_exact():
    reg = build_operator_registry()
    # fixture helper builds atomic -> zeta cumulative artifact
    atomic, cumulative = boolean_signal_fixture()
    recovered = reg["MOBIUS_INVERT_BOOLEAN"].execute({"cumulative": cumulative}, ())
    assert recovered.value == atomic.value
    assert reg["MOBIUS_INVERT_BOOLEAN"].verify((cumulative,), recovered).passed
```

Add parity tests for chain residual, exact-vs-numeric Hilbert rank, barcode->Betti->Euler loss, symbolic invariant checking, Steiner applicability refusal, graph signature escalation, and numerical residual verification.

- [ ] **Step 2: Run tests RED**

Run: `python -m pytest -q experiments/pct_goal_solver/test_operators.py`

- [ ] **Step 3: Implement focused primitives**

Use exact `Fraction`/SymPy arithmetic for exact operators; NumPy only for explicitly numerical operators. Numerical verifiers must return `NUMERICALLY_UNSAFE` when conditioning policy requires exact escalation.

Operator shape:

```python
@dataclass(frozen=True)
class OperatorSpec:
    operator_id: str
    input_types: tuple[str, ...]
    output_type: str
    representation_class: str
    exactness_class: str
    cost: int
    applicability: Callable[..., Applicability]
    execute: Callable[..., Artifact | OperatorFailure]
    verify: Callable[..., VerificationResult]
    structural_signature: tuple[str, ...]
```

- [ ] **Step 4: Run operator tests GREEN**

Run: `python -m pytest -q experiments/pct_goal_solver/test_operators.py`

- [ ] **Step 5: Run historical parity smoke tests**

Run: `python -m pytest -q experiments/pct_e1_e25/test_campaign.py`

Expected: historical E-series remains green.

- [ ] **Step 6: Commit**

```bash
git add experiments/pct_goal_solver
 git commit -m "feat: add exact symbolic numerical operator registry"
```

---

### Task 3: Best-First Planner with Explicit Typing

**Files:**
- Create: `experiments/pct_goal_solver/planner.py`
- Create: `experiments/pct_goal_solver/test_planner_explicit.py`

**Interfaces:**
- Consumes: `SolverVisibleGoal`, operator registry.
- Produces: `solve(goal, registry, typing_mode="EXPLICIT", macros=()) -> SolveTrace`.

- [ ] **Step 1: Write failing composition tests**

```python
def test_explicit_planner_solves_multistep_exact_goal():
    goal = sealed_fixture("G1")
    trace = solve(goal.solver_visible(), build_operator_registry(), typing_mode="EXPLICIT")
    assert trace.final_verdict == "PASS"
    assert len(trace.operator_path) >= 2
    assert trace.verifier_chain[-1].passed


def test_explicit_planner_refuses_nonconvex_steiner_goal():
    goal = nonconvex_g9_fixture()
    trace = solve(goal.solver_visible(), build_operator_registry(), typing_mode="EXPLICIT")
    assert trace.final_verdict == "NOT_APPLICABLE"
```

Also test budget exhaustion => `NOT_ESTABLISHED`, canonical deterministic tie-breaking, and no positive result without final verifier.

- [ ] **Step 2: Run RED**

Run: `python -m pytest -q experiments/pct_goal_solver/test_planner_explicit.py`

- [ ] **Step 3: Implement deterministic best-first search**

Use heap key:

```python
(unresolved_obligations, accumulated_cost, unverified_artifacts, path_length, operator_id_sequence)
```

Deduplicate states by canonical digest of artifacts + obligations. Expand only explicitly type-compatible operators. Call `FALSIFY_CANDIDATE` before `VERIFY_CANDIDATE` where the target declares falsification applicable.

- [ ] **Step 4: Run explicit planner tests GREEN**

Run: `python -m pytest -q experiments/pct_goal_solver/test_planner_explicit.py`

- [ ] **Step 5: Commit**

```bash
git add experiments/pct_goal_solver/planner.py experiments/pct_goal_solver/test_planner_explicit.py
 git commit -m "feat: add goal-directed explicit operator planner"
```

---

### Task 4: Inferred and Hybrid Typing

**Files:**
- Create: `experiments/pct_goal_solver/compatibility.py`
- Create: `experiments/pct_goal_solver/test_typing_modes.py`
- Modify: `experiments/pct_goal_solver/planner.py`

**Interfaces:**
- Produces: `CompatibilityModel.fit(calibration_goals, traces, registry)`.
- Planner accepts `typing_mode in {"EXPLICIT", "INFERRED", "HYBRID"}` and optional compatibility model.

- [ ] **Step 1: Write failing inference tests**

```python
def test_inferred_model_never_reads_sealed_goals():
    model = CompatibilityModel.fit(calibration_goals(), calibration_traces(), build_operator_registry())
    assert not model.goal_ids & {g.goal_id for g in sealed_goals()}


def test_inferred_mode_transfers_across_exact_symbolic_numeric():
    model = calibrated_model()
    for family in ("G1", "G7", "G9"):
        trace = solve(sealed_fixture(family).solver_visible(), build_operator_registry(),
                      typing_mode="INFERRED", compatibility_model=model)
        assert trace.final_verdict in {"PASS", "NOT_ESTABLISHED", "NOT_APPLICABLE"}
```

Add a hybrid safety test ensuring representation-class mismatches are never executed.

- [ ] **Step 2: Run RED**

Run: `python -m pytest -q experiments/pct_goal_solver/test_typing_modes.py`

- [ ] **Step 3: Implement transition-signature calibration**

Represent successful input states by a frozenset of structural descriptors such as representation class, container shape, algebraic field marker, matrix/graph/geometry flags, and available metadata keys. Rank inferred operator candidates by exact descriptor match then symmetric-difference distance; deterministic operator ID breaks ties. Do not expose semantic type names in inferred scoring.

Hybrid mode retains hard representation/safety classes but uses the inferred ranking inside the admissible set.

- [ ] **Step 4: Run typing tests GREEN**

Run: `python -m pytest -q experiments/pct_goal_solver/test_typing_modes.py`

- [ ] **Step 5: Commit**

```bash
git add experiments/pct_goal_solver/compatibility.py experiments/pct_goal_solver/planner.py experiments/pct_goal_solver/test_typing_modes.py
 git commit -m "feat: add inferred and hybrid operator compatibility"
```

---

### Task 5: Verified Macro Synthesis

**Files:**
- Create: `experiments/pct_goal_solver/macros.py`
- Create: `experiments/pct_goal_solver/test_macros.py`
- Modify: `experiments/pct_goal_solver/planner.py`

**Interfaces:**
- Produces: `synthesize_macros(calibration_traces, registry) -> tuple[MacroOperator, ...]`.
- Macro execution expands to primitive constituents and preserves primitive provenance.

- [ ] **Step 1: Write failing macro tests**

```python
def test_macro_requires_two_distinct_calibration_goals():
    macros = synthesize_macros([single_trace], build_operator_registry())
    assert macros == ()


def test_macro_replay_matches_primitive_result():
    macros = synthesize_macros(calibration_traces_with_repeated_path(), build_operator_registry())
    macro = macros[0]
    primitive = replay_primitives(macro.operator_ids, fixture_state(), build_operator_registry())
    compressed = macro.execute(fixture_state())
    assert compressed.output == primitive.output
    assert compressed.primitive_operator_ids == macro.operator_ids
```

- [ ] **Step 2: Run RED**

Run: `python -m pytest -q experiments/pct_goal_solver/test_macros.py`

- [ ] **Step 3: Implement frozen macro policy**

Enumerate successful path windows of length 2-4; require occurrence in >=2 distinct calibration goals, verifier success, stable endpoint contract, and replay equivalence. Macro cost is one search expansion but primitive execution count remains the expanded constituent count for honest accounting.

- [ ] **Step 4: Run macro tests GREEN**

Run: `python -m pytest -q experiments/pct_goal_solver/test_macros.py`

- [ ] **Step 5: Commit**

```bash
git add experiments/pct_goal_solver/macros.py experiments/pct_goal_solver/planner.py experiments/pct_goal_solver/test_macros.py
 git commit -m "feat: add verified solver macro synthesis"
```

---

### Task 6: Six-Mode Sealed Campaign and Scientific Scoring

**Files:**
- Create: `experiments/pct_goal_solver/campaign.py`
- Create: `experiments/pct_goal_solver/test_campaign.py`
- Create: `experiments/pct_goal_solver/generate_report.py`

**Interfaces:**
- Produces: `run_campaign() -> dict[str, Any]`.
- Produces report file `generated-goal-solver/pct_goal_solver_campaign.json`.

- [ ] **Step 1: Write failing campaign-gate tests**

```python
def test_campaign_scores_all_six_modes_and_twelve_families():
    report = run_campaign()
    assert set(report["modes"]) == {
        "EXPLICIT/PRIMITIVE", "EXPLICIT/SYNTHESIZED",
        "INFERRED/PRIMITIVE", "INFERRED/SYNTHESIZED",
        "HYBRID/PRIMITIVE", "HYBRID/SYNTHESIZED",
    }
    assert {f"G{i}" for i in range(1, 13)} == set(report["families"])


def test_no_wrong_positive_is_hidden_by_campaign_averages():
    report = run_campaign()
    for mode in report["modes"].values():
        assert "wrong_positive_count" in mode
        assert "by_family" in mode
```

- [ ] **Step 2: Run RED**

Run: `python -m pytest -q experiments/pct_goal_solver/test_campaign.py`

- [ ] **Step 3: Implement calibration -> freeze -> sealed execution**

Campaign order is fixed:

```text
build registry
build deterministic corpus
solve CALIBRATION in EXPLICIT/PRIMITIVE
fit CompatibilityModel
synthesize validated macros
run VALIDATION only as execution smoke
freeze model/macros in memory
run SEALED in six modes
score against sealed answers
emit four independent conclusions
```

Conclusions:

```text
GOAL_DIRECTED_SOLVING
INFERRED_COMPATIBILITY
MIXED_DOMAIN_COMPOSITION
MACRO_SYNTHESIS
```

- [ ] **Step 4: Run campaign tests GREEN**

Run: `python -m pytest -q experiments/pct_goal_solver/test_campaign.py`

- [ ] **Step 5: Generate a local-equivalent report in CI-compatible path**

Run: `python -m experiments.pct_goal_solver.generate_report --out-dir generated-goal-solver`

- [ ] **Step 6: Commit**

```bash
git add experiments/pct_goal_solver
 git commit -m "feat: add sealed mixed-domain solver campaign"
```

---

### Task 7: CI Integration Without Artifact-Hash Gate

**Files:**
- Modify: `.github/workflows/pct-e1-e25-campaign.yml`

**Interfaces:**
- Existing E1-E31 regression remains intact.
- Add goal-solver tests and generated report artifact.

- [ ] **Step 1: Add compilation/test/report commands**

Add:

```yaml
- name: Generate goal-directed solver report
  run: python -m experiments.pct_goal_solver.generate_report --out-dir generated-goal-solver

- name: Upload goal-directed solver report
  uses: actions/upload-artifact@v4
  with:
    name: pct-goal-solver-report
    path: generated-goal-solver/*.json
    if-no-files-found: error
```

Extend regression command with:

```text
experiments/pct_goal_solver/test_model_goals.py
experiments/pct_goal_solver/test_operators.py
experiments/pct_goal_solver/test_planner_explicit.py
experiments/pct_goal_solver/test_typing_modes.py
experiments/pct_goal_solver/test_macros.py
experiments/pct_goal_solver/test_campaign.py
```

Do not add byte-equality checks against committed report artifacts.

- [ ] **Step 2: Commit CI change**

```bash
git add .github/workflows/pct-e1-e25-campaign.yml
 git commit -m "ci: run goal-directed mixed-domain solver campaign"
```

- [ ] **Step 3: Push and inspect GitHub Actions**

Expected: historical suite and new solver tests execute; generated scientific report uploads independently of repository evidence freezing.

---

### Task 8: Scientific Analysis and Report

**Files:**
- Create: `docs/PCT_GOAL_DIRECTED_MIXED_DOMAIN_SOLVER_REPORT.md`

**Interfaces:**
- Consumes actual generated campaign JSON from successful/failed CI run.
- Produces a factual report that does not promote unsupported capability.

- [ ] **Step 1: Inspect results by family and mode**

Record at minimum:

```text
correct / wrong / refused by family
path-length distribution
cross-exactness successful paths
expanded states and primitive executions
inferred-vs-explicit deltas
macro search reduction
all control wrong positives
examples of successful compositions
examples of fail-closed refusals
```

- [ ] **Step 2: Apply frozen gates exactly as written in the spec**

Do not tune search budgets, operator rules, inferred compatibility, or macro thresholds after seeing sealed outcomes. Any subsequent improvement is a new campaign version.

- [ ] **Step 3: Write scientific report**

The report must state four separate conclusions and explain the observed solver boundary. It must explicitly distinguish goal-directed operator composition from semantic-label prediction.

- [ ] **Step 4: Final verification**

Run the full workflow. Claim completion only from fresh CI evidence showing the historical regression plus all new goal-solver tests completed without an implementation failure. Scientific gates may legitimately be `NOT_SUPPORTED`; that is a valid campaign result.

- [ ] **Step 5: Commit report**

```bash
git add docs/PCT_GOAL_DIRECTED_MIXED_DOMAIN_SOLVER_REPORT.md
 git commit -m "docs: report goal-directed mixed-domain solver results"
```
