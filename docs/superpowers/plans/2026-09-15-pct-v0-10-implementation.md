# MAPEOGEO PCT v0.10 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first fail-closed Probe–Chain Transform (PCT) reference subsystem inside MAPEOGEO, with exact chain algebra, controlled 2-D probes, correspondence checks, persistence, reconstruction, baseline ablations, immutable artifacts, graph emission, and CI-backed PASS/FAIL evidence.

**Architecture:** PCT represents each probed state as a finite chain complex and each declared relationship as a chain map. Scalar invariants, persistence summaries, geometric measurements, and reconstruction outputs are projections of that richer object. The v0.10 runner executes validity gates V0–V8 before scientific tests S1–S10 and reports `ENGINE_VALIDITY` separately from `SCIENTIFIC_RESULT`.

**Tech Stack:** Python 3.12; `pytest>=8,<9`; `sympy>=1.13,<2` for exact rational matrices; `shapely>=2.0,<3` for deterministic planar geometry; Python stdlib `dataclasses`, `fractions`, `enum`, `hashlib`, `json`, `itertools`, `pathlib`; GitHub Actions on `ubuntu-latest`.

**Spec:** `docs/superpowers/specs/2026-09-15-pct-computational-architecture-design.md`

## Global Constraints

- Preserve MAPEOGEO's separation of EO, GEO, executable evidence, FORMAL, and `KERNEL_VERIFIED`.
- `SAME_SEMANTICS` is never inferred from equal Euler characteristic, equal Betti vectors, or reconstruction similarity alone.
- Authoritative exact v0.10 coefficient backends are `GF(2)` and `Q`; v0.10 does not claim integral torsion recovery.
- Exact chain identities remain exact; floating tolerances are limited to geometric calculations and are frozen in the preregistration manifest.
- `NOT_APPLICABLE` is distinct from `PASS`, `FAIL`, `INVALID`, `ERROR`, and `INCONCLUSIVE`.
- All B0–B5 baselines use the same frozen object/probe schedule whenever that baseline is defined.
- No source prose/page images are persisted in PCT artifacts.
- CPU reference results are authoritative for v0.10; no GPU path is part of this implementation.
- The scientific run must be deterministic from repository commit, manifest, object hashes, and seed `20260915`.
- No acceptance manifest is committed until an actual accepted CI artifact exists.

---

## File Structure

Create or modify the following focused units:

```text
requirements-pct-v0-10.txt              # pinned runtime/test dependency ranges
mapeogeo/__init__.py                     # package marker
mapeogeo/pct/__init__.py                 # public PCT API
mapeogeo/pct/models.py                   # enums/dataclasses shared across modules
mapeogeo/pct/contracts.py                # applicability, equivalence, verdict helpers
mapeogeo/pct/chain.py                    # exact simplicial boundary/rank/homology
mapeogeo/pct/maps.py                     # chain-map residuals and correspondence controls
mapeogeo/pct/fixtures.py                 # analytic/adversarial 2-D control corpus
mapeogeo/pct/geometry.py                 # planar geometry, Euler of geometry, scale scans
mapeogeo/pct/probes.py                   # line/support probe schedules and response fields
mapeogeo/pct/persistence.py              # GF(2) filtered-boundary reduction
mapeogeo/pct/reconstruction.py           # convex support reconstruction and errors
mapeogeo/pct/baselines.py                # B0-B5 feature views and capability matrix
mapeogeo/pct/experiment.py               # V0-V8, S1-S10 orchestration
mapeogeo/pct/artifacts.py                # deterministic serialization/hashing/graph fragment
scripts/pct_v0_10.py                     # CLI runner
scripts/validate_pct_v0_10.py            # artifact validator wrapper
tests/pct/test_models_contracts.py       # contract/model tests
tests/pct/test_chain.py                  # exact chain algebra tests
tests/pct/test_maps.py                   # correspondence positive/negative controls
tests/pct/test_fixtures_geometry.py      # analytic geometry and applicability controls
tests/pct/test_probes.py                 # parameterized Euler/support response tests
tests/pct/test_persistence.py            # persistence pairing tests
tests/pct/test_reconstruction.py         # deterministic reconstruction tests
tests/pct/test_experiment.py             # V/S gate and baseline hierarchy tests
tests/validate_pct_v0_10.py              # repository-style acceptance artifact validator
evidence/v0_10_pct_preregistration.json  # frozen scientific manifest
docs/V0_10_PCT_SPEC.md                   # human-readable preregistration
.github/workflows/pct-v0-10.yml           # CI execution and artifact upload
README.md                                 # add v0.10 only after an accepted run
```

Do not modify the Lean toolchain or v0.8/v0.9 formalization files in this stage.

---

### Task 1: Freeze v0.10 contracts, dependency set, and shared data models

**Files:**
- Create: `requirements-pct-v0-10.txt`
- Create: `mapeogeo/__init__.py`
- Create: `mapeogeo/pct/__init__.py`
- Create: `mapeogeo/pct/models.py`
- Create: `mapeogeo/pct/contracts.py`
- Create: `tests/pct/test_models_contracts.py`

**Interfaces:**
- Produces: `CoefficientField`, `Verdict`, `EquivalenceContract`, `Applicability`, `Simplex`, `FiniteComplex`, `ChainMap`, `VerdictRecord`, `ProbeState`.
- Produces: `make_verdict(...) -> VerdictRecord`, `require_applicable(...) -> VerdictRecord`.
- Consumed by every later task.

- [ ] **Step 1: Write dependency file**

```text
pytest>=8,<9
sympy>=1.13,<2
shapely>=2.0,<3
```

- [ ] **Step 2: Write failing enum/dataclass tests**

```python
from fractions import Fraction
from mapeogeo.pct.models import (
    Applicability, ChainMap, CoefficientField, EquivalenceContract,
    FiniteComplex, ProbeState, Simplex, Verdict,
)


def test_contract_enums_are_stable_strings():
    assert CoefficientField.GF2.value == "GF2"
    assert CoefficientField.Q.value == "Q"
    assert Verdict.NOT_APPLICABLE.value == "NOT_APPLICABLE"
    assert EquivalenceContract.SUBDIVISION.value == "SUBDIVISION"


def test_simplex_is_canonical_and_oriented():
    s = Simplex(vertices=(2, 0, 1))
    assert s.vertices == (2, 0, 1)
    assert s.dimension == 2


def test_probe_state_serializes_scientific_parameters():
    p = ProbeState(
        probe_id="probe:theta0:p0",
        probe_family="LINE_EULER",
        parameters={"theta": 0.0, "offset": 0.0},
        scale=0.0,
        observation_operator="INTERSECTION",
        coefficient_backend=CoefficientField.GF2,
        applicability_contract="PLANAR_TAME_GEOMETRY",
    )
    assert p.parameters["theta"] == 0.0
```

- [ ] **Step 3: Run tests to verify import failure**

Run: `python -m pytest -q tests/pct/test_models_contracts.py`

Expected: FAIL because `mapeogeo.pct.models` does not exist.

- [ ] **Step 4: Implement the shared types**

Use frozen string enums and immutable dataclasses. `FiniteComplex.simplices` is a tuple of oriented simplices; matrix objects are not stored in this model.

```python
class CoefficientField(str, Enum):
    GF2 = "GF2"
    Q = "Q"

class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INVALID = "INVALID"
    ERROR = "ERROR"
    INCONCLUSIVE = "INCONCLUSIVE"

class EquivalenceContract(str, Enum):
    EXACT = "EXACT"
    RELABELING = "RELABELING"
    SUBDIVISION = "SUBDIVISION"
    RIGID_MOTION_2D = "RIGID_MOTION_2D"
    RIGID_MOTION_AND_SCALE_2D = "RIGID_MOTION_AND_SCALE_2D"
    HOMEOMORPHISM_CONTROL = "HOMEOMORPHISM_CONTROL"
    CHAIN_HOMOTOPY_CONTROL = "CHAIN_HOMOTOPY_CONTROL"

class Applicability(str, Enum):
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"

@dataclass(frozen=True)
class Simplex:
    vertices: tuple[int, ...]
    @property
    def dimension(self) -> int:
        return len(self.vertices) - 1

@dataclass(frozen=True)
class FiniteComplex:
    complex_id: str
    simplices: tuple[Simplex, ...]
    metadata: dict[str, object]

@dataclass(frozen=True)
class ChainMap:
    map_id: str
    source_id: str
    target_id: str
    matrices_by_degree: dict[int, object]
    construction_method: str

@dataclass(frozen=True)
class ProbeState:
    probe_id: str
    probe_family: str
    parameters: dict[str, float | int | str]
    scale: float
    observation_operator: str
    coefficient_backend: CoefficientField
    applicability_contract: str
```

`VerdictRecord` contains `check_id`, `applicability`, `verdict`, `measured`, `expected`, `tolerance_or_exact_rule`, and `provenance` exactly as named in the approved design.

- [ ] **Step 5: Add verdict helper tests and implementation**

```python
def test_non_applicable_never_becomes_pass():
    r = require_applicable("tube", False, provenance={"fixture": "reentrant"})
    assert r.verdict is Verdict.NOT_APPLICABLE
    assert r.applicability is Applicability.NOT_APPLICABLE
```

`require_applicable` returns `NOT_APPLICABLE` immediately when its predicate is false; it never accepts a success value in that branch.

- [ ] **Step 6: Run tests**

Run: `python -m pytest -q tests/pct/test_models_contracts.py`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add requirements-pct-v0-10.txt mapeogeo tests/pct/test_models_contracts.py
git commit -m "feat: add PCT v0.10 contracts and models"
```

---

### Task 2: Implement exact finite-chain algebra and Euler–Poincaré gates

**Files:**
- Create: `mapeogeo/pct/chain.py`
- Create: `tests/pct/test_chain.py`
- Modify: `mapeogeo/pct/__init__.py`

**Interfaces:**
- Consumes: `FiniteComplex`, `Simplex`, `CoefficientField`.
- Produces: `simplices_by_degree(complex)`, `boundary_matrix(complex, k) -> sympy.Matrix`, `rank_over_field(matrix, field) -> int`, `betti_numbers(complex, field) -> dict[int, int]`, `euler_from_chains(complex) -> int`, `euler_from_homology(complex, field) -> int`, `check_chain_condition(complex) -> bool`.

- [ ] **Step 1: Write failing chain tests**

Use an oriented triangle boundary and filled triangle.

```python
def test_triangle_loop_has_expected_homology():
    c = triangle_loop_complex()
    assert check_chain_condition(c)
    assert betti_numbers(c, CoefficientField.GF2) == {0: 1, 1: 1}
    assert betti_numbers(c, CoefficientField.Q) == {0: 1, 1: 1}
    assert euler_from_chains(c) == 0
    assert euler_from_homology(c, CoefficientField.Q) == 0


def test_filled_triangle_kills_h1():
    c = filled_triangle_complex()
    assert check_chain_condition(c)
    assert betti_numbers(c, CoefficientField.Q) == {0: 1, 1: 0, 2: 0}
    assert euler_from_chains(c) == 1
```

Define the two fixture constructors locally in this test file until Task 3 centralizes fixtures.

- [ ] **Step 2: Run the focused tests**

Run: `python -m pytest -q tests/pct/test_chain.py`

Expected: FAIL because chain functions do not exist.

- [ ] **Step 3: Implement oriented boundary construction**

For an oriented simplex `(v0, ..., vk)`, construct

```python
faces = [
    ((-1) ** i, simplex.vertices[:i] + simplex.vertices[i + 1:])
    for i in range(len(simplex.vertices))
]
```

Canonical face lookup must account for orientation: sort the face vertices for lookup and multiply by the permutation sign required to convert the oriented face to that canonical ordering.

- [ ] **Step 4: Implement exact field ranks**

For `Q`, use `sympy.Matrix.rank()` on integer/rational matrices.

For `GF2`, implement deterministic Gaussian elimination over integers reduced modulo 2:

```python
def rank_gf2(matrix: Matrix) -> int:
    rows = [[int(matrix[r, c]) & 1 for c in range(matrix.cols)]
            for r in range(matrix.rows)]
    rank = 0
    for col in range(matrix.cols):
        pivot = next((r for r in range(rank, len(rows)) if rows[r][col]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for r in range(len(rows)):
            if r != rank and rows[r][col]:
                rows[r] = [a ^ b for a, b in zip(rows[r], rows[rank])]
        rank += 1
    return rank
```

- [ ] **Step 5: Implement Betti and Euler formulas**

For each degree `k`, use

```python
beta_k = dim_C_k - rank(d_k) - rank(d_{k+1})
```

and assert non-negativity. `check_chain_condition` multiplies exact matrices and requires the exact zero matrix.

- [ ] **Step 6: Add a deliberately invalid complex test**

Construct matrices directly through a private test helper and verify the validator rejects a nonzero `d0*d1` composition rather than coercing it to tolerance-based success.

- [ ] **Step 7: Run exact tests**

Run: `python -m pytest -q tests/pct/test_chain.py`

Expected: PASS for both `GF2` and `Q` cases.

- [ ] **Step 8: Commit**

```bash
git add mapeogeo/pct/chain.py mapeogeo/pct/__init__.py tests/pct/test_chain.py
git commit -m "feat: add exact PCT chain algebra"
```

---

### Task 3: Build the analytic/adversarial 2-D fixture corpus

**Files:**
- Create: `mapeogeo/pct/fixtures.py`
- Create: `tests/pct/test_fixtures_geometry.py`

**Interfaces:**
- Produces: `ControlFixture` dataclass and `build_control_corpus() -> dict[str, ControlFixture]`.
- Each fixture may carry `complex`, `geometry`, `expected_betti`, `expected_euler`, `equivalence_contract`, `applicability`.
- Consumed by maps, probes, persistence, reconstruction, and experiment tasks.

- [ ] **Step 1: Write fixture identity tests**

Require at least these IDs:

```python
REQUIRED = {
    "triangle_loop", "triangle_loop_subdivided", "two_loops",
    "filled_triangle", "equal_area_square", "equal_area_triangle",
    "square_annulus", "two_separated_squares", "reentrant_control",
}
```

Verify `triangle_loop` has `(b0,b1)=(1,1)`, `two_loops` has `(2,2)`, and both have Euler characteristic `0`.

- [ ] **Step 2: Add equal-area geometry tests**

Construct the square with side `sqrt(pi)` and the equilateral triangle with side `sqrt(4*pi/sqrt(3))`; center both at the origin. Assert `abs(area - pi) <= 1e-12`.

- [ ] **Step 3: Implement combinatorial fixtures**

Use explicit simplices. The subdivided triangle loop uses vertices `0..5` and edges `(0,1),(1,2),(2,3),(3,4),(4,5),(5,0)`; coarse vertices correspond to fine vertices `0,2,4`.

`two_loops` is the disjoint union of two triangles with vertex sets `{0,1,2}` and `{3,4,5}`.

- [ ] **Step 4: Implement scale-event geometry fixtures**

Use Shapely:

```python
square_annulus = box(-3, -3, 3, 3).difference(box(-1, -1, 1, 1))
two_separated_squares = box(-2, -1, -1, 1).union(box(1, -1, 2, 1))
```

Both have an analytically known event at offset `s=1`: the annulus hole closes and the two components merge.

- [ ] **Step 5: Mark applicability explicitly**

`equal_area_square` and `equal_area_triangle` are convex and may use convex parallel-set tests. `square_annulus` / `reentrant_control` must refuse any regular positive-reach tube-law test that the manifest labels inapplicable.

- [ ] **Step 6: Run fixture tests**

Run: `python -m pytest -q tests/pct/test_fixtures_geometry.py tests/pct/test_chain.py`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add mapeogeo/pct/fixtures.py tests/pct/test_fixtures_geometry.py
git commit -m "test: add PCT analytic control corpus"
```

---

### Task 4: Implement chain maps and the correspondence-failure control

**Files:**
- Create: `mapeogeo/pct/maps.py`
- Create: `tests/pct/test_maps.py`

**Interfaces:**
- Consumes: exact boundary matrices from `chain.py`.
- Produces: `triangle_subdivision_map(corrupt: bool = False) -> ChainMap`, `chain_map_residual(source, target, map, k) -> Matrix`, `check_chain_map(...) -> dict`.

- [ ] **Step 1: Write the positive chain-map test**

For the coarse triangle loop to the six-edge subdivided loop:

```python
def test_valid_subdivision_commutes_with_boundary():
    coarse = corpus["triangle_loop"].complex
    fine = corpus["triangle_loop_subdivided"].complex
    f = triangle_subdivision_map(corrupt=False)
    assert check_chain_map(coarse, fine, f)["pass"] is True
    assert all(v == 0 for v in check_chain_map(coarse, fine, f)["residual_nonzero_entries"].values())
```

Use `F0` to send coarse vertices `0,1,2` to fine vertices `0,2,4`; use `F1` to send each coarse edge to the oriented sum of its two subdivided edges.

- [ ] **Step 2: Write the corrupted-map negative control**

Corrupt only the image of one coarse edge so the source/target complexes and all state-level Betti/Euler values remain unchanged.

```python
def test_corrupted_map_is_detected_while_state_invariants_match():
    result = check_chain_map(coarse, fine, triangle_subdivision_map(corrupt=True))
    assert result["pass"] is False
    assert result["residual_nonzero_entries"][1] > 0
    assert euler_from_homology(coarse, CoefficientField.Q) == 0
    assert euler_from_homology(fine, CoefficientField.Q) == 0
```

- [ ] **Step 3: Run tests to verify failure**

Run: `python -m pytest -q tests/pct/test_maps.py`

Expected: FAIL before implementation.

- [ ] **Step 4: Implement exact residuals**

For every relevant degree:

```python
residual = d_target[k] * F[k] - F[k - 1] * d_source[k]
```

The exact path passes only when every residual entry equals integer/rational zero.

- [ ] **Step 5: Add residual support localization**

Return row/column coordinates and values of nonzero residual entries. This becomes cancellation/correspondence provenance for S3/S8.

- [ ] **Step 6: Run tests**

Run: `python -m pytest -q tests/pct/test_maps.py tests/pct/test_chain.py`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add mapeogeo/pct/maps.py tests/pct/test_maps.py
git commit -m "feat: add PCT chain-map integrity checks"
```

---

### Task 5: Implement planar geometry, applicability, and scale-event scans

**Files:**
- Create: `mapeogeo/pct/geometry.py`
- Expand: `tests/pct/test_fixtures_geometry.py`

**Interfaces:**
- Produces: `euler_of_geometry(geom) -> int`, `component_hole_counts(geom) -> tuple[int,int]`, `parallel_metrics(geom, scales) -> list[dict]`, `check_convex_steiner(geom, scales, tol) -> VerdictRecord`, `scan_topology_events(geom, scales) -> list[dict]`.

- [ ] **Step 1: Add Euler-of-geometry tests**

Require:

```python
assert euler_of_geometry(corpus["square_annulus"].geometry) == 0
assert euler_of_geometry(corpus["two_separated_squares"].geometry) == 2
assert euler_of_geometry(corpus["equal_area_square"].geometry) == 1
```

For polygons/multipolygons use `components - total_interior_rings`.

- [ ] **Step 2: Add scale-event tests**

Use frozen schedule:

```python
SCALES = [0.0, 0.25, 0.5, 0.75, 0.99, 1.0, 1.01, 1.25]
```

Require the annulus to transition from Euler `0` to `1` at `1.0 ± 0.011`, and the separated squares from Euler `2` to `1` at the same tolerance.

- [ ] **Step 3: Add applicability refusal test**

```python
def test_regular_tube_law_refuses_reentrant_control():
    result = check_convex_steiner(corpus["reentrant_control"].geometry, [0.1, 0.2], 1e-9)
    assert result.verdict is Verdict.NOT_APPLICABLE
```

- [ ] **Step 4: Implement geometry utilities**

Normalize Shapely collections by discarding empty geometries. `euler_of_geometry` handles `Polygon`, `MultiPolygon`, `LineString`, `MultiLineString`, `Point`, `MultiPoint`, and generic collections through connected-component decomposition appropriate to the control corpus.

- [ ] **Step 5: Implement convex Steiner control**

For convex planar controls compare measured buffer area against

```python
A(s) = A0 + P0*s + pi*s*s
```

because all convex filled controls in this v0.10 channel have `chi=1`. Do not apply this checker to nonconvex fixtures; the applicability layer refuses them before calculating a verdict.

- [ ] **Step 6: Run geometry tests**

Run: `python -m pytest -q tests/pct/test_fixtures_geometry.py`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add mapeogeo/pct/geometry.py tests/pct/test_fixtures_geometry.py
git commit -m "feat: add PCT planar geometry and scale events"
```

---

### Task 6: Implement parameterized probes and response consistency

**Files:**
- Create: `mapeogeo/pct/probes.py`
- Create: `tests/pct/test_probes.py`

**Interfaces:**
- Produces: `line_euler_response(geom, theta, offset, extent) -> int`, `line_response_field(geom, directions, offsets, extent) -> dict`, `support_samples(geom, directions) -> dict[float,float]`, `validate_convex_line_response(field) -> dict`.

- [ ] **Step 1: Freeze the v0.10 probe schedule in tests**

Directions:

```python
DIRECTIONS = [k * math.pi / 6 for k in range(12)]
```

Offsets:

```python
OFFSETS = [x / 4 for x in range(-16, 17)]  # -4.0 ... 4.0
```

Line extent: `10.0`.

- [ ] **Step 2: Write line-response tests**

For each convex filled fixture, every direction's nonzero responses must form one contiguous block in the ordered offset schedule. For the square annulus, at a horizontal line through the hole, the intersection Euler response must be `2`.

- [ ] **Step 3: Add corruption localization test**

Flip one interior response bit from `1` to `0` for one direction. `validate_convex_line_response` must flag exactly that direction because the nonzero support is no longer contiguous.

- [ ] **Step 4: Implement line probes**

Construct a finite line segment centered at

```python
p = offset * (cos(theta), sin(theta))
```

with tangent direction `(-sin(theta), cos(theta))` and total half-length `extent`. Intersect with Shapely geometry and compute Euler via `geometry.euler_of_geometry`.

- [ ] **Step 5: Implement support samples**

For polygonal geometries, calculate the maximum dot product over exterior coordinates. The support channel is a GEO projection and is not mislabeled as an Euler transform.

- [ ] **Step 6: Run probe tests**

Run: `python -m pytest -q tests/pct/test_probes.py`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add mapeogeo/pct/probes.py tests/pct/test_probes.py
git commit -m "feat: add PCT parameterized probe responses"
```

---

### Task 7: Implement GF(2) persistence and the cancellation ledger

**Files:**
- Create: `mapeogeo/pct/persistence.py`
- Create: `tests/pct/test_persistence.py`

**Interfaces:**
- Produces: `FilteredSimplex(simplex, filtration)`, `persistent_pairs_gf2(items) -> list[PersistencePair]`, `betti_at(pairs, t, max_dim)`, `euler_at(pairs, t)`, `pairing_ledger(pairs) -> list[dict]`.

- [ ] **Step 1: Write a loop-birth/death persistence test**

Use a filtration in which three vertices appear at `0`, three boundary edges at `1`, and the filled triangle at `2`. Require an H1 interval born at `1` and dead at `2`.

- [ ] **Step 2: Write an H0 merge test**

Use two vertices born at `0` and their connecting edge at `1`; require two H0 births and one finite H0 death at `1`, leaving one essential component.

- [ ] **Step 3: Implement standard column reduction over GF(2)**

Represent each boundary column as a Python `set[int]` of row indices. Repeatedly XOR (`symmetric_difference`) with the column owning the same lowest pivot until the pivot is unique or the column becomes empty.

- [ ] **Step 4: Preserve provenance**

Each `PersistencePair` stores:

```text
dimension
birth
birth_simplex
death
death_simplex
essential
```

The ledger is serialized directly from these pairings; it is not reconstructed from Betti curves afterward.

- [ ] **Step 5: Verify Euler projection**

At each test filtration value, assert

```python
euler_at(pairs, t) == sum((-1) ** k * b for k, b in betti_at(pairs, t, 2).items())
```

- [ ] **Step 6: Run persistence tests**

Run: `python -m pytest -q tests/pct/test_persistence.py`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add mapeogeo/pct/persistence.py tests/pct/test_persistence.py
git commit -m "feat: add PCT persistence and event ledger"
```

---

### Task 8: Implement deterministic convex reconstruction from support probes

**Files:**
- Create: `mapeogeo/pct/reconstruction.py`
- Create: `tests/pct/test_reconstruction.py`

**Interfaces:**
- Consumes: support samples from `probes.py`.
- Produces: `clip_polygon_halfspace(vertices, normal, bound)`, `reconstruct_from_support(samples, initial_extent) -> Polygon`, `reconstruction_metrics(original, reconstructed) -> dict`.

- [ ] **Step 1: Write square and triangle reconstruction tests**

Use the 12 frozen directions from Task 6. Require:

```python
metrics["hausdorff"] <= 1e-9
abs(metrics["area_error"]) <= 1e-9
metrics["euler_match"] is True
```

for the equal-area square and the oriented equal-area triangle whose supporting normals are included in the 30° schedule.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest -q tests/pct/test_reconstruction.py`

Expected: FAIL before implementation.

- [ ] **Step 3: Implement Sutherland–Hodgman halfspace clipping**

Start from the square `[-initial_extent, initial_extent]^2`. For each support sample `(theta, h)`, clip against

```text
cos(theta)*x + sin(theta)*y <= h.
```

Interpolate crossing points with the exact line parameter in floating arithmetic and emit the resulting polygon to Shapely only after all clips are complete.

- [ ] **Step 4: Implement reconstruction metrics**

Return Hausdorff distance, absolute area error, perimeter error, and Euler match. The scientific runner decides which fields are mandatory for a given contract.

- [ ] **Step 5: Add deterministic one-probe ablation enumeration**

For each omitted direction, reconstruct and record metrics. Do not select the best omission after inspection; emit all 12 one-probe erasure cases.

- [ ] **Step 6: Run reconstruction tests**

Run: `python -m pytest -q tests/pct/test_reconstruction.py tests/pct/test_probes.py`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add mapeogeo/pct/reconstruction.py tests/pct/test_reconstruction.py
git commit -m "feat: add deterministic PCT reconstruction"
```

---

### Task 9: Build B0–B5 baseline views and scientific capability scoring

**Files:**
- Create: `mapeogeo/pct/baselines.py`
- Create: `tests/pct/test_experiment.py`

**Interfaces:**
- Produces: `baseline_features(fixture, probe_data, persistence_data, map_data) -> dict[str, object]`, `lowest_capable_baseline(capability_results) -> str | None`.
- Baseline names are exactly `B0`, `B1`, `B2`, `B3`, `B4`, `B5`.

- [ ] **Step 1: Write the S1 hierarchy test**

For `triangle_loop` versus `two_loops`, require:

```text
B0: collision (both chi=0)
B1: separated (Betti vectors differ)
```

The test proves the harness credits the lowest sufficient baseline rather than B5 automatically.

- [ ] **Step 2: Write the S3 hierarchy test**

Compare valid and corrupted subdivision correspondences over exactly the same source/target object states. Require B0–B4 to have identical state features, while B5 includes a different map residual and detects the corrupted correspondence.

- [ ] **Step 3: Implement baseline feature extraction**

Use these definitions:

```text
B0 = global Euler characteristic
B1 = ordered Betti tuple
B2 = sorted persistence tuples (dimension,birth,death,essential)
B3 = frozen parameterized Euler-response field
B4 = serialized chain dimensions + exact boundary matrices, excluding map edges
B5 = B4 + chain-map matrices/residual support + event provenance
```

- [ ] **Step 4: Implement lowest-capability attribution**

Given ordered baselines, return the first baseline that satisfies the capability predicate. The scientific report must never claim B5 credit when B0–B4 already pass.

- [ ] **Step 5: Run tests**

Run: `python -m pytest -q tests/pct/test_experiment.py`

Expected: PASS for the two hierarchy controls.

- [ ] **Step 6: Commit**

```bash
git add mapeogeo/pct/baselines.py tests/pct/test_experiment.py
git commit -m "feat: add PCT baseline hierarchy"
```

---

### Task 10: Implement V0–V8 and S1–S10 orchestration

**Files:**
- Create: `mapeogeo/pct/experiment.py`
- Expand: `tests/pct/test_experiment.py`
- Create: `evidence/v0_10_pct_preregistration.json`
- Create: `docs/V0_10_PCT_SPEC.md`

**Interfaces:**
- Produces: `run_pct_experiment(manifest: dict) -> dict`.
- Report top-level keys: `run_id`, `stage`, `engine_validity`, `scientific_result`, `validity_gates`, `scientific_tests`, `baseline_matrix`, `negative_controls`, `claim_boundary`.

- [ ] **Step 1: Freeze the preregistration JSON**

Use these values exactly:

```json
{
  "run_id": "MAPEOGEO-PCT-V0.10",
  "stage": "v0.10",
  "seed": 20260915,
  "coefficient_backends": ["GF2", "Q"],
  "directions_radians": [0.0, 0.5235987755982988, 1.0471975511965976, 1.5707963267948966, 2.0943951023931953, 2.6179938779914944, 3.141592653589793, 3.6651914291880923, 4.1887902047863905, 4.71238898038469, 5.235987755982989, 5.759586531581287],
  "offsets": [-4.0, -3.75, -3.5, -3.25, -3.0, -2.75, -2.5, -2.25, -2.0, -1.75, -1.5, -1.25, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0],
  "scale_schedule": [0.0, 0.25, 0.5, 0.75, 0.99, 1.0, 1.01, 1.25],
  "tolerances": {
    "analytic_geometry": 1e-9,
    "reconstruction_hausdorff": 1e-9,
    "scale_event": 0.011,
    "support_stability_slack": 1e-10
  },
  "required_validity_gates": ["V0", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"],
  "baselines": ["B0", "B1", "B2", "B3", "B4", "B5"]
}
```

The implementation may add descriptive fields, fixture IDs, and artifact policy before the first scientific run, but it may not alter these numeric schedules/tolerances after results are inspected.

- [ ] **Step 2: Write gate tests before the orchestrator**

Require all V-gate keys to exist. Add one test where a mandatory chain-map control is corrupted and verify `engine_validity` becomes `FAIL` if the corrupted control is incorrectly accepted; the expected scientific negative control itself counts as PASS only when the engine detects the corruption.

- [ ] **Step 3: Implement V0–V8**

Definitions:

```text
V0 deterministic rerun hashes of core in-memory result sections match
V1 every exact fixture satisfies d^2=0
V2 every finite exact fixture satisfies Euler–Poincare
V3 valid declared maps commute and corrupted-map negative control is rejected
V4 every persistence filtration orders faces no later than cofaces
V5 relabel/subdivision controls preserve required invariants
V6 analytic area/perimeter/topology controls match preregistered values
V7 theorem-backed geometry either passes its applicability predicate or returns NOT_APPLICABLE
V8 every result record has object/probe/backend/provenance identifiers
```

- [ ] **Step 4: Implement S1–S10 using frozen controls**

Use these decision rules:

```text
S1 PASS if B0 collision triangle_loop/two_loops is separated by B1 or richer.
S2 PASS if relabeling and valid subdivision retain declared invariant signatures.
S3 PASS if corrupted subdivision map is invisible to B0-B4 and detected/localized by B5.
S4 PASS if square and triangle reconstruction meet 1e-9 Hausdorff and topology criteria.
S5 PASS if the full 12-probe result and all one-probe ablation metrics are emitted; report the smallest passing subset found by deterministic subset search, but do not require a specific minimum cardinality.
S6 PASS if deterministic vertex perturbations bounded by epsilon change every sampled support value by at most epsilon + 1e-10 for epsilon in [1e-6,1e-4,1e-3].
S7 PASS if square-vs-triangle separation survives every single-direction erasure from the frozen 12-direction field.
S8 PASS if the injected noncontiguous response corruption is detected and localized to the exact direction.
S9 PASS if annulus hole closure and two-component merger are both detected at 1.0 ± 0.011 with no extra Euler transitions on the frozen scale schedule.
S10 PASS if orientation-preserving and orientation-reversing polygon correspondences are distinguished when orientation is part of the contract while state Euler/Betti data remain unchanged.
```

- [ ] **Step 5: Implement scientific result logic**

```python
if engine_validity != "PASS":
    scientific_result = "INCONCLUSIVE"
elif b5_has_preregistered_unique_capability and not mandatory_stability_failure:
    scientific_result = "H1_SUPPORTED"
else:
    scientific_result = "H1_NOT_SUPPORTED"
```

`b5_has_preregistered_unique_capability` is satisfied by a passing S3 only if B0–B4 are explicitly recorded as unable to distinguish the two correspondence states.

- [ ] **Step 6: Write `docs/V0_10_PCT_SPEC.md`**

The document states the governing question, frozen corpus, exact/numeric boundary, manifest hash, V0–V8, S1–S10, B0–B5, acceptance logic, and claim boundary. It explicitly says this stage tests a computational architecture rather than asserting a new theorem.

- [ ] **Step 7: Run orchestration tests**

Run: `python -m pytest -q tests/pct/test_experiment.py`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add mapeogeo/pct/experiment.py tests/pct/test_experiment.py evidence/v0_10_pct_preregistration.json docs/V0_10_PCT_SPEC.md
git commit -m "feat: preregister PCT v0.10 experiment"
```

---

### Task 11: Add deterministic artifact sealing and MAPEOGEO graph-fragment emission

**Files:**
- Create: `mapeogeo/pct/artifacts.py`
- Create: `tests/pct/test_artifacts.py`
- Expand: `tests/pct/test_experiment.py`

**Interfaces:**
- Produces: `canonical_json(value) -> str`, `sha256_bytes(data) -> str`, `write_run_artifacts(result, out_dir, manifest) -> dict[str,str]`, `build_graph_fragment(result) -> dict`.

- [ ] **Step 1: Write canonical serialization tests**

```python
def test_canonical_json_is_key_order_independent():
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})
```

No timestamps or machine-specific paths are allowed in hashed scientific payloads.

- [ ] **Step 2: Write required artifact test**

Require these files/directories after one run:

```text
manifest.json
hashes.json
objects/fixtures.json
probes/responses.json
complexes/chain_data.json
maps/chain_maps.json
homology/betti.json
persistence/pairs.json
geometry/metrics.json
event_ledger/events.json
reconstruction/results.json
negative_controls/results.json
residuals/results.json
validity.json
scientific_result.json
pct_graph_fragment.json
summary.md
```

- [ ] **Step 3: Implement deterministic writers**

Write JSON with `sort_keys=True`, `indent=2`, newline termination, finite floats only, and stable list ordering by ID.

`hashes.json` contains SHA-256 for every persisted artifact except itself; recomputing the run in a second temporary directory must produce the same artifact hashes.

- [ ] **Step 4: Emit a graph fragment**

Use schema-compatible top-level fields:

```json
{
  "graph_id": "mapeogeo-pct-v0-10-fragment",
  "schema_version": "0.10",
  "required_views": ["EO", "GEO"],
  "nodes": [],
  "edges": []
}
```

Add scoped nodes for `PCT_RUN`, `PCT_OBSERVATION`, `PCT_MAP`, `PCT_EVENT`, and `CERTIFICATE`. Add only endpoints present in the fragment. Certificate class is executable PCT evidence; never `KERNEL_VERIFIED`.

- [ ] **Step 5: Add graph-integrity tests**

Assert unique node IDs, unique edge IDs, all edge endpoints exist, and forbidden persisted source keys are absent:

```python
FORBIDDEN = {"statement_text", "proof_text", "source_prose", "page_image"}
```

- [ ] **Step 6: Run artifact tests**

Run: `python -m pytest -q tests/pct/test_artifacts.py tests/pct/test_experiment.py`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add mapeogeo/pct/artifacts.py tests/pct/test_artifacts.py tests/pct/test_experiment.py
git commit -m "feat: seal PCT v0.10 evidence artifacts"
```

---

### Task 12: Add CLI runner and repository-style artifact validator

**Files:**
- Create: `scripts/pct_v0_10.py`
- Create: `scripts/validate_pct_v0_10.py`
- Create: `tests/validate_pct_v0_10.py`
- Create: `tests/pct/test_cli.py`

**Interfaces:**
- CLI: `python scripts/pct_v0_10.py --manifest evidence/v0_10_pct_preregistration.json --out-dir artifacts/pct_v0_10 --repository-commit <sha>`.
- Validator: `python tests/validate_pct_v0_10.py artifacts/pct_v0_10`.

- [ ] **Step 1: Write CLI smoke test**

Use `tmp_path` and call the runner through `subprocess.run`. Require exit code `0`, required artifacts present, and `validity.json["ENGINE_VALIDITY"] == "PASS"`.

- [ ] **Step 2: Implement runner**

The script loads the manifest, injects only the supplied repository commit into provenance, calls `run_pct_experiment`, then `write_run_artifacts`. It exits nonzero only for invalid/error execution; an engine-valid `H1_NOT_SUPPORTED` run still exits zero because the experiment itself completed correctly.

- [ ] **Step 3: Implement strict validator**

Validator requirements:

```text
all required files exist
manifest run_id is MAPEOGEO-PCT-V0.10
all artifact hashes recompute correctly
ENGINE_VALIDITY is PASS
V0-V8 are present and no mandatory gate is FAIL/INVALID/ERROR/INCONCLUSIVE
negative controls have their expected detected/refused status
scientific_result is one of H1_SUPPORTED/H1_NOT_SUPPORTED/INCONCLUSIVE
baseline matrix contains B0-B5
S1-S10 all have explicit verdict records
PCT graph fragment IDs are unique and endpoints exist
forbidden source-payload keys are absent
```

The validator does **not** require `H1_SUPPORTED`; scientific falsification must not make a valid artifact structurally invalid.

- [ ] **Step 4: Run CLI and validator tests**

Run:

```bash
python -m pytest -q tests/pct/test_cli.py
python scripts/pct_v0_10.py --manifest evidence/v0_10_pct_preregistration.json --out-dir /tmp/pct-v010 --repository-commit TEST-COMMIT
python tests/validate_pct_v0_10.py /tmp/pct-v010
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/pct_v0_10.py scripts/validate_pct_v0_10.py tests/validate_pct_v0_10.py tests/pct/test_cli.py
git commit -m "feat: add PCT v0.10 runner and validator"
```

---

### Task 13: Add CI and run the complete preregistered stage

**Files:**
- Create: `.github/workflows/pct-v0-10.yml`
- Modify only after accepted run: `README.md`
- Do not create `evidence/v0_10_pct_acceptance_manifest.json` until CI has produced an accepted artifact.

**Interfaces:**
- GitHub Actions artifact name: `mapeogeo-pct-v0.10`.

- [ ] **Step 1: Add workflow**

Use this structure:

```yaml
name: MAPEOGEO v0.10 PCT audit

on:
  workflow_dispatch:
  pull_request:
    paths:
      - "mapeogeo/pct/**"
      - "scripts/pct_v0_10.py"
      - "scripts/validate_pct_v0_10.py"
      - "tests/pct/**"
      - "tests/validate_pct_v0_10.py"
      - "evidence/v0_10_pct_preregistration.json"
      - "docs/V0_10_PCT_SPEC.md"
      - "requirements-pct-v0-10.txt"
      - ".github/workflows/pct-v0-10.yml"
  push:
    branches: [main]
    paths:
      - "mapeogeo/pct/**"
      - "scripts/pct_v0_10.py"
      - "scripts/validate_pct_v0_10.py"
      - "tests/pct/**"
      - "tests/validate_pct_v0_10.py"
      - "evidence/v0_10_pct_preregistration.json"
      - "docs/V0_10_PCT_SPEC.md"
      - "requirements-pct-v0-10.txt"
      - ".github/workflows/pct-v0-10.yml"

permissions:
  contents: read

jobs:
  pct-audit:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: requirements-pct-v0-10.txt
      - run: python -m pip install -r requirements-pct-v0-10.txt
      - run: python -m pytest -q tests/pct
      - run: |
          rm -rf artifacts/pct_v0_10
          python scripts/pct_v0_10.py \
            --manifest evidence/v0_10_pct_preregistration.json \
            --out-dir artifacts/pct_v0_10 \
            --repository-commit "${GITHUB_SHA}"
      - run: python tests/validate_pct_v0_10.py artifacts/pct_v0_10
      - uses: actions/upload-artifact@v4
        with:
          name: mapeogeo-pct-v0.10
          path: artifacts/pct_v0_10/
          if-no-files-found: error
          retention-days: 30
```

- [ ] **Step 2: Run the entire local/reference suite**

Run:

```bash
python -m pytest -q tests/pct
rm -rf artifacts/pct_v0_10
python scripts/pct_v0_10.py --manifest evidence/v0_10_pct_preregistration.json --out-dir artifacts/pct_v0_10 --repository-commit "$(git rev-parse HEAD)"
python tests/validate_pct_v0_10.py artifacts/pct_v0_10
```

Expected: unit suite PASS, runner completes, validator prints a single `MAPEOGEO_PCT_V0_10_ARTIFACT_VALIDATION: PASS ...` line.

- [ ] **Step 3: Commit CI**

```bash
git add .github/workflows/pct-v0-10.yml
git commit -m "ci: add PCT v0.10 audit workflow"
```

- [ ] **Step 4: Push branch and open PR**

Push `agent/pct-computational-architecture`, open a PR against `main`, and wait for the PCT workflow plus repository-required checks to pass.

- [ ] **Step 5: Review the actual scientific artifact before acceptance**

Inspect `validity.json`, `scientific_result.json`, `baseline_matrix.json` or its artifact equivalent, negative controls, reconstruction metrics, and artifact hashes. Do not edit thresholds in response to the result. If execution exposes an implementation bug, fix the bug without changing the preregistered scientific decision rule. If a scientific assumption is wrong, report the corresponding FAIL/INCONCLUSIVE result and preserve it.

- [ ] **Step 6: Create the acceptance manifest only for an accepted run**

After a successful CI run, create `evidence/v0_10_pct_acceptance_manifest.json` with:

```text
evidence_id
status
scientific_preregistration_commit
accepted_ci_head
github_actions_run_id
github_actions_job_id
github_actions_artifact_id
artifact_name
artifact_zip_sha256
repository_commit
engine_validity
scientific_result
artifact_file_sha256
gates
claim_boundary
```

Populate these fields from the actual accepted workflow/artifact; do not use synthetic values.

- [ ] **Step 7: Update README with measured, not planned, results**

Add a `v0.10 — Probe–Chain Transform executable evidence` section only after the accepted run. Report the actual `ENGINE_VALIDITY`, `SCIENTIFIC_RESULT`, lowest capable baseline for each supported capability, and explicit claim boundary. Do not describe H1 as supported unless the sealed result says `H1_SUPPORTED`.

- [ ] **Step 8: Commit acceptance metadata**

```bash
git add evidence/v0_10_pct_acceptance_manifest.json README.md
git commit -m "docs: record accepted PCT v0.10 evidence"
```

---

## Final Verification Checklist

Before claiming v0.10 complete, run all of the following on the final branch head:

```bash
python -m pytest -q tests/pct
python -m py_compile scripts/pct_v0_10.py scripts/validate_pct_v0_10.py tests/validate_pct_v0_10.py
rm -rf artifacts/pct_v0_10
python scripts/pct_v0_10.py \
  --manifest evidence/v0_10_pct_preregistration.json \
  --out-dir artifacts/pct_v0_10 \
  --repository-commit "$(git rev-parse HEAD)"
python tests/validate_pct_v0_10.py artifacts/pct_v0_10
```

Then verify manually from the emitted JSON that:

```text
ENGINE_VALIDITY is PASS
V0-V8 are explicit
S1-S10 are explicit
corrupted chain map is rejected/localized
reentrant tube-law control is NOT_APPLICABLE
annulus and component event scales are recovered at 1.0 ± 0.011
B0-B5 are all present
scientific result logic credits the lowest capable baseline
artifact hashes reproduce on rerun
PCT graph fragment has unique IDs and valid endpoints
no executable certificate is mislabeled KERNEL_VERIFIED
```

Only after these checks and CI artifact validation may the acceptance manifest and README results be committed.

## Claim Boundary for the Implementation

A completed v0.10 implementation establishes a reproducible fail-closed reference architecture for controlled PCT experiments. It does not establish universal transform injectivity, universal reconstruction, arbitrary-mesh robustness, whole-corpus applicability, a new theorem of integral geometry, integral-homology torsion support, or replacement of MAPEOGEO's formal verifier layer.
