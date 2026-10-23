# NGC-RQ Real Phase Sandbox

This repository tracks a small, self-contained Python test module for real-valued phase-plane representations of finite-dimensional complex state systems.

It tests the engineering claim:

> Complex-like phase evolution, composition, interference, measurement, reduced subsystem extraction, and noisy channels can be represented using structured real-valued arrays.

It does **not** prove a new interpretation of quantum mechanics. It only validates the finite-dimensional computational equivalence used by this sandbox.

## Representation

Complex vector:

```text
psi = a + i b
```

Real phase vector:

```text
psi_R = [a, b]
```

Complex operator:

```text
M = A + i B
```

Real block operator:

```text
M_R = [[A, -B],
       [B,  A]]
```

Structured real composition:

```text
(a,b) ⊗Ω (c,d) = (a⊗c - b⊗d, a⊗d + b⊗c)
```

## Files

```text
ngc_rq/real_phase.py              Core implementation and wrappers
ngc_rq/gates.py                   Real-phase gate constructors, including controlled gates
ngc_rq/circuit.py                 Real-phase circuit runner
ngc_rq/observables.py             Pauli-string observable helpers
ngc_rq/backends/local_gate.py     Real-only local gate backend
ngc_rq/backends/dual_lane.py      Explicit q/p dual-lane backend
tests/test_*.py                   Pytest unit/regression tests
tests/run_equivalence_tests.py    Compatibility runner for the full suite
benchmarks/bench_composition_depth.py  Composition-depth scaling benchmark
benchmarks/bench_precision_drift.py    Repeated-evolution precision benchmark
benchmarks/bench_backend_compare.py    Real local/dual-lane vs complex reference benchmark
benchmarks/bench_backend_sweep.py      Backend sweep with text/CSV/JSON output
examples/real_only_interference.py     Real-only runtime demo
docs/roadmap.md                        Practical adoption roadmap / to-do list
docs/math_ledger.md                    Math claims and test mapping
docs/execution_math.md                 Runtime execution math supplement
docs/architecture.md                   Runtime architecture notes
docs/kernel_notes.md                   Dual-lane/kernel planning notes
docs/testing_strategy.md               Testing strategy and coverage notes
requirements.txt                  Minimal Python dependency list
```

## Run

From the repository root:

```bash
pip install -r requirements.txt
python tests/run_equivalence_tests.py
```

or directly:

```bash
pytest -q
```

Optional benchmark/demo smoke tests:

```bash
python benchmarks/bench_composition_depth.py --max-depth 8 --local-dim 2
python benchmarks/bench_precision_drift.py --steps 50000
python benchmarks/bench_backend_compare.py --qubits 8 --layers 20
python benchmarks/bench_backend_sweep.py --min-qubits 4 --max-qubits 10 --layers 8 --repeats 3 --format json
python examples/real_only_interference.py
```

Expected result:

```text
NGC-RQ real-phase equivalence test suite: PASS
```

## Tested

- Vector/operator realification round trips
- Structural block validation
- `RealPhaseState` and `RealPhaseOperator` wrappers
- Interference equivalence
- Three-party local-unitary equivalence
- Structured real composition associativity
- Projective measurement update
- Partial trace / reduced subsystem extraction
- Mixed-state noisy channels
- CHSH-style two-party correlation
- GHZ/Mermin-style three-party correlation
- Float64/float32 precision drift under repeated evolution
- Composition-depth scaling smoke benchmark
- Backend comparison and backend sweep benchmarks
- Real-only runtime interference smoke demo
- Seeded property-style randomized invariants
- Real-phase gate constructors, controlled gates, Toffoli/CCNOT, and controlled phase
- Bell/GHZ circuit runner outputs
- Real-only local gate backend, including non-adjacent targets
- Dual-lane backend equivalence and execution counters
- Marginal probabilities, Z expectations, Pauli-string expectations, and seeded sampling
- Math ledger mapping tested identities to code/tests
- Roadmap tracking practical adoption milestones

## Current status

This is now a sandbox-grade Python package with split pytest coverage, precision-drift tests, property-style randomized invariants, a math ledger, a roadmap, real-phase gates, controlled gates, Pauli observables, a circuit runner, a real-only local gate backend, an explicit dual-lane backend, backend comparison/sweep benchmarks, a composition-depth benchmark, a precision-drift benchmark, and a real-only runtime demo. The next step is a vectorized local-gate backend prototype and larger backend sweeps.
