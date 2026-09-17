# Local execution and implementation handoff

## Available now: retrieve specifications

In an existing NB11B/MAPEOGEO checkout, preserve any local changes and use:

```bash
git fetch origin agent/e32-typed-parallel-decision-graph-spec
git worktree add ../MAPEOGEO-e32-spec origin/agent/e32-typed-parallel-decision-graph-spec
```

Choose an unused worktree directory. These commands retrieve documentation; they do not run E32. Do not reset or overwrite an existing checkout.

## Required implementation surface

Future modules under experiments/typed_parallel_decision_graph/:
contracts.py, graph.py, rewrites.py, receipt_checker.py, scheduler.py, solver_adapter.py, deterministic_backend.py, local_model_backend.py, fixtures.py, metrics.py, campaign.py, cli.py and test_*.py.

The CPU deterministic profile must work offline without model libraries. Use Python 3.11 as the initial compatibility target; produce tested exact dependency locks per supported platform. Local model dependencies belong to a separate optional lock. Do not claim a dependency combination is validated until installation and preflight pass on that environment.

Target environments: Windows PowerShell and Linux shell; CPU required, CUDA optional. Record actual GPU/VRAM rather than assuming capacity from its model name. The user's RTX 5070 Laptop GPU is a target for local validation, not hardware available or tested in this spec-writing session.

No model download is implicit. The user supplies a local weights directory and records its licensing/source. Preflight computes weight/tokenizer hashes and checks exact dependency versions, tokenization boundaries, option-score normalization, deterministic repeatability, isolated-vs-batched drift and available memory. Incompatible CUDA/library combinations stop with actionable diagnostics.

## Future command contract: NOT IMPLEMENTED in this branch

The following is the required CLI for a subsequent implementation. Every command must have --help, return structured JSON diagnostics and avoid network access by default.

```bash
python -m experiments.typed_parallel_decision_graph.cli preflight --profile cpu --output runs/e32/preflight.json
python -m experiments.typed_parallel_decision_graph.cli seal --profile cpu --output runs/e32/run-lock.json
python -m experiments.typed_parallel_decision_graph.cli run --lock runs/e32/run-lock.json --plane deterministic --arms S M G T --output runs/e32/deterministic
python -m experiments.typed_parallel_decision_graph.cli verify --run runs/e32/deterministic
```

Local-model sequence, with the model path supplied interactively by preflight so no path placeholder is executable:

```bash
python -m experiments.typed_parallel_decision_graph.cli preflight --profile local-model --choose-model-directory --output runs/e32/model-preflight.json
python -m experiments.typed_parallel_decision_graph.cli seal --preflight runs/e32/model-preflight.json --output runs/e32/model-lock.json
python -m experiments.typed_parallel_decision_graph.cli run --lock runs/e32/model-lock.json --plane local-model --arms S M G T --output runs/e32/model
python -m experiments.typed_parallel_decision_graph.cli verify --run runs/e32/model
python -m experiments.typed_parallel_decision_graph.cli report --runs runs/e32/deterministic runs/e32/model --output runs/e32/report
```

Each run command executes the complete frozen matrix, controls and ablations without repeated user intervention. Resumption requires matching lock hashes and appends immutable trial records; it never replaces failed trials. Existing output directories fail unless --resume is explicitly selected. No automatic uploads.

Exit codes: 0 complete and valid (scientific support may still be absent), 2 invalid configuration/provenance, 3 incomplete execution, 4 engine-validity failure. Reports must distinguish completion from supported hypotheses. A separate --require-support flag may make failed scientific gates nonzero but is not the default.

## Artifact layout

- run-lock.json: immutable inputs/environment/limits.
- fixtures-manifest.json and split-manifest.json: exact case identities and isolation.
- compilation.jsonl: all candidates, rejected rewrites and checked receipts.
- trials.jsonl: complete per-trial records, including errors.
- answers.jsonl: option scores/probabilities and decision outputs.
- metrics.json: per-case and aggregate metrics with intervals.
- controls.json: every attack and ablation outcome.
- hashes.json: raw SHA-256 inventory of all other artifacts.
- REPORT.md: separate deterministic/model findings and claim limits.

Timing fields are excluded from semantic reproducibility hashes but included in raw artifact hashes. Never expect wall-clock measurements to reproduce bit-for-bit. Exact fixtures, selected deterministic outputs, registry bindings and receipt checks must reproduce exactly.

Seal generation must refuse absent pins, missing fixtures and missing local model files. It must never insert fake model hashes or reuse this documentation's base commit as the implementation commit.

## Implementation acceptance order

1. Write and run rejection tests for contracts, hidden oracle access and invalid DAGs.
2. Implement exact S/T execution and independent terminal verification.
3. Implement M fixtures and G receipt-checked rewrites, with mutation tests.
4. Verify all deterministic controls before allowing model efficacy reporting.
5. Add teacher-forced local scoring and resource/timing instrumentation.
6. Freeze the complete implementation, data, costs and environment; run the full matrix once.
7. Publish raw failures and bounded conclusions, then decide whether any further work is justified.

These are construction dependencies, not separate moving-goalpost scientific campaigns. There is one frozen evaluation campaign; a material fix after test exposure requires a new version and untouched holdout.

Existing solver and historical tests must also run in implementation validation. Their exact invocation and fixture hydration must follow the pinned repository instructions; do not claim the prior 1,014-test integration has been rerun by writing this specification.
