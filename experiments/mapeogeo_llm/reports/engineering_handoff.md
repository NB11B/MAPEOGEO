# MAPEOGEO-LLM: Codex Local Engineering Handoff

**Date:** 2026-10-28  
**Priority:** Build and test a complete runnable mathematical LLM, not just another isolated pilot.  
**Target repository:** `NB11B/MAPEOGEO`, branch `experiment/mapeogeo-llm-recurrent`  
**Baseline branch (immutable):** `experiment/mapeogeo-llm-compositional`, baseline commit `28e5689` (short SHA supplied by local operator; verify full SHA).  
**Execution host:** Lenovo Legion Pro 5, Intel Ultra 9 275HX, Windows 11, RTX 5070 Laptop GPU (12 GB), RAM >=32 GB, Python 3.13 and PyTorch 2.11 reported by the local operator.  
**External sources:** `NB11B/GeometricElementaryOperators`, `NB11B/MAPEOGEOv2`, installed Lean 4 toolchain / Mathlib when relevant.  
**Historical artifact:** `MAPEOGEO_recurrent_pilot.zip` from ChatGPT; use as reference, not as a replacement for repository code.

## Mission and nonnegotiable definition of done

Build a small, *actually trained* LLM that can take natural-language or structured mathematical goals, produce an executable plan, call deterministic EO and GEO operators, persist intermediate results, inspect observations and proof obligations, continue or revise the plan, and return a result labeled VERIFIED, REFUTED, UNSOLVED, or INVALID_INPUT on the basis of independent checks. The final application must run locally, expose a CLI and minimal chat-style interface, load a trained checkpoint, and pass a reproducible suite of held-out tasks. Training and inference must both be demonstrated, with complete artifact provenance.

**Do not call the project complete merely because a parser can transcribe explicit operator phrases.** Demonstrate goal-conditioned search where the prompt does *not* supply the complete program. Do not use an LLM judge for proof acceptance. Do not claim that floating-point results constitute exact proofs. Do not silently replace the spectral model with a GRU; GRU is a valid separate policy baseline.

A 13.6M-parameter FFT Spectral LM is the historical target architecture, described as decoder-only with causal FFT spectral depthwise convolutions, local causal depthwise branch, SwiGLU, and SentencePiece BPE vocab 4096. This model is **not confirmed present in the current repository**. Search code/history and user's local working trees, then recover its canonical source and compatible checkpoint. If unavailable, create and validate a faithful documented implementation and train it from scratch; do not pretend pretrained weights exist.

## 0. Operational rules for Codex

1. Work on `experiment/mapeogeo-llm-recurrent` under `experiments/mapeogeo_llm/`. Do not modify `main` or the preserved compositional branch. Check `git status`, active branch, parent, and commit before changing files; do not overwrite unrelated user changes.
2. Read existing `compositional.py`, `operators.py`, pilot, tests, result JSON, and any existing project conventions. Verify paths before assuming them.
3. First reproduce the previous baseline as closely as practical. Document any version drift, hardware differences, failures, or numerical nondeterminism.
4. Make incremental commits with working tests; generate one comprehensive final report and runnable commands. Do not claim that unexecuted full runs passed.
5. Use pinned dependencies and recorded Git SHA of each dependency, data manifest/checksum, seed, command, environment, device, precision, source/target vocab, checkpoint digest, and evaluation run ID.
6. Prefer independent oracles. Fail closed on unsupported operators, invalid types, stale certificates, parse errors, timeout, and budgets.
7. Distinguish deterministic *execution* correctness, learned *planning* accuracy, and formal *proof* correctness at all stages.
8. Run unit tests continuously; run full three-seed campaigns when feasible. If unavailable due to machine limitations, mark the gate OPEN with an exact reproduction command, not PASS.

## 1. Architecture and authoritative boundaries

```
User problem (text / structured goal / Lean proposition)
   -> prompt normalization + typed problem schema
   -> Spectral LM tokenizer + learned planner
   -> validated action AST / typed IR
   -> step executor (EO, GEO, graph lookup, assert, verify, stop)
   -> immutable state/register store + observations + budget
   -> learned next-action policy (repeat until stop or limit)
   -> independent checking: integer oracle / GEO reference / Lean kernel
   -> answer + trace + provenance + verification status
```

Authority hierarchy:

- **Controller:** proposes action sequences; its probability is never proof evidence.
- **Tool adapters:** verify preconditions and execute using the original operator interfaces or documented wrappers.
- **State:** keeps immutable action/observation trace, registers and symbol bindings, type information, and budget accounting.
- **Verifier:** independent mathematical acceptance only. Lean `#print axioms`, replay contracts, or other external certificates must be checked where applicable.
- **Assistant output:** identifies exact status and evidence source; never upgrades empirical sampling to formal certainty.

Initially the compiled 8-bit ALU remains external to the model. *In-network compiled circuitry* is a separate optional ablation. The full model must work first with the explicit typed engine; do not tie project success to recreating Qwenputer's recurrent neural CPU. Floating GEO uses its actual numerical and algebraic contract, not an invented 'exact for all reals' guarantee.

## 2. Required repository layout

```
experiments/mapeogeo_llm/
  README.md
  pyproject.toml (or pinned requirements + lockfile)
  operators.py                    # preserved + qualified ALU
  compositional.py                # preserved baseline, changes only if necessary
  contracts.py                    # typed task/action/state/result contracts
  executor.py                     # deterministic step engine + register memory
  geo_adapter.py                  # original GEO kernel integration
  graph_adapter.py                # MAPEOGEO graph retrieval adapter
  lean_adapter.py                 # optional Lean verification process
  datasets/
    generate.py                   # deterministic train/eval generation
    oracle.py                     # separate ground truth and proof checks
    splits.py                     # leakage checks
    schemas.py
  models/
    spectral_lm.py                # actual FFT Spectral LM
    recurrent_policy.py           # GRU/transformer reference baselines
    action_head.py
    tokenizer.py
  training/
    train_sft.py
    train_policy.py
    train_structural.py           # optional after SFT
  evaluation/
    benchmark.py
    compare_baselines.py
    audit_leakage.py
    report.py
  inference/
    agent.py
    cli.py
    chat.py
  tests/
    test_contracts.py
    test_alu.py
    test_geo.py
    test_executor.py
    test_memory.py
    test_parser.py
    test_halt.py
    test_dataset.py
    test_leakage.py
    test_recurrent.py
    test_spectral.py
    test_train_smoke.py
    test_inference.py
    test_verification.py
    test_end_to_end.py
  configs/
    smoke.yaml
    full_cuda.yaml
    ablations.yaml
  artifacts/                      # outputs, ignored if large
  reports/
    final_qualification.md
```

Reuse present files when possible; avoid duplicating incompatible action definitions. Do not commit large training datasets/checkpoints unless repo policy explicitly permits. Persist manifests and metadata and provide local artifact paths.

## 3. Typed instruction set and runtime semantics

Introduce a versioned canonical JSON AST. Define `Task`, `TypedValue`, `Ref`, `Action`, `Observation`, `ProofObligation`, `Episode`, `VerificationResult`, and `Budget`. Include schema version and canonical digest. Action schema:

```
{
  "schema": "mapeogeo.llm.action.v1",
  "op": "ADD|SUB|XOR|AND|OR|EQ|GEO_GP|GEO_GRADE|GRAPH_QUERY|ASSERT|VERIFY|HALT",
  "src": [{"kind":"input|reg|literal|node", "id":"..."}, ...],
  "dst": "r3",
  "kwargs": {"signature": [1,1,1], "grade": 2},
  "reason_code": "..."
}
```

Requirements:
- Explicit arity and type contracts; `uint8`, integer, rational/symbolic expression, float multivector, boolean, graph node, proposition, proof certificate.
- ALU returns 8-bit wraparound outputs, EQ returns 0/1. Typed flag for modular versus unbounded arithmetic.
- Intermediate registers persist across steps, allow branching/reuse and arbitrary valid operands, and forbid uninitialized/out-of-range references.
- `HALT` is learned or policy-selected and valid only when output is present or an explicit unresolved outcome is requested; max-step timeout is distinct from successful HALT.
- `ASSERT` creates a proof obligation, never automatically certifies it. `VERIFY` invokes the correct independent checker.
- Invalid input/action/tool error yields a structured failure with no mutated state; no partial program accepted as completed.
- Bound CPU/GPU memory, operator-count, maximum graph expansion, tokens, wall-clock time; deterministic replay with serialized state.
- Define independent proof statuses: `VERIFIED`, `REFUTED`, `UNSOLVED`, `INVALID_INPUT`, `EXECUTION_ERROR`, `BUDGET_EXHAUSTED`. Map to MAPEOGEOv2 proof statuses without conflating them.

Include action schema examples for 2+ intermediate results and nested DAG, e.g., `r0=ADD(a,b); r1=XOR(r0,c); r2=AND(r0,r1); RETURN r2`. Ensure no accidental oracle answers in model observations.

## 4. EO/GEO binding

**EO:** Preserve original `CompiledALU` in `operators.py`, with exhaustive 6 x 65,536 independent Python comparisons and binary validation, plus negative tests. Optimized cached/device-backed bit encoding is allowed only if exact results remain identical.

**GEO:** Bind the actual `NB11B/GeometricElementaryOperators` kernel and pin commit. Existing inspected API in `include/geo/operator_kernel.h` includes `geo_operator_gp_f64`, `geo_operator_plan_fixed_blade_i32`, `geo_operator_apply_f64`, `geo_operator_apply_parametric_f64`, and `geo_operator_apply_parametric_f64_vjp`; dimension max 6, max blades 64, ABI version `0x00050100u` in the inspected revision. Verify against live checkout; compile C library on Windows with documented compiler steps, and add a Python ctypes/cffi wrapper with layout checks and safety validation. If native build is unavailable, use a clearly named independently tested pure-Python reference implementation for dev, but leave native gate OPEN.

Independent tests must include: signed basis products under Cl(3,0) using independently defined Pauli matrices; arbitrary signature tests (including negative-square basis vectors); grade/metric identities; bilinearity and associativity over random small integer multivectors; zero, sign, basis convention, and dimension boundaries; floating tolerance and numerical stability with an explicit reference. Avoid self-oracle (testing generated matrix against its own generator). For symbolic identity proofs, use exact rational/integer logic or a verifier, not only `isclose`.

**Graph:** Read actual `MAPEOGEOv2` schemas and proof bridges. Build version-pinned read-only adapter for node lookup, relation adjacency, operator applicability, proof dependencies, candidate/verified distinction, and provenance. Never treat a candidate edge as established proof. Add a small synthetic graph fixture and optional real graph integration tests.

**Lean:** Integrate existing Lean tooling as a subprocess with fixed command arguments, timeout, and artifact logging. Only accept verified closure if the Lean kernel checks generated theorem under explicitly recorded axioms/assumptions. Reject `sorry`, `admit`, unsanctioned `axiom`, and hypothesis-smuggling. Build fixture theorem, false theorem, malformed theorem, and timeout tests. If Lean not installed or actual bridge unavailable, expose optional capability with clear OPEN gate and no false proof claims.

## 5. Data curriculum, including genuinely unseen goals

Five data families, generated deterministically from pinned manifest:

- **D0 exact EO:** all operations and operand positions; program trace + independently evaluated output; input validation.
- **D1 compositional instruction following:** lengths 1-8, paraphrases, forward/reverse, nested parentheses, multi-register reuse, intermediate observations, explicit HALT. Include parser challenge where lexical cues don't uniquely specify operation.
- **D2 goal-conditioned planning:** provide initial typed state, allowable operators, a target value/property, and a budget, *not the target program*. Search with a separate bounded solver to label existence and demonstrate at least one validated solution. Include non-unique solutions and unsatisfiable bounded goals. Prevent leakage by separating label generation and the learned agent.
- **D3 GEO:** basis-blade identities, products of multivectors, signature-sensitive goals, grade selection, equivalent alternate derivations, basis permutation and perturbations, and invalid domains.
- **D4 graph/proof:** graph path discovery, prerequisite planning, assertions with open obligations, valid and invalid claims, and a small Lean-checked theorem subset. Never promote candidates to certified without independent replay.

Partition at **program/operator-pattern family, AST canonicalization, template, graph motif, theorem family, and underlying mathematical goal** levels rather than random row splitting. Hold out entire adjacency pairs, triples, DAG motifs, program lengths 4-8 when training <=3, operator parameter ranges, and paraphrase families. For goal-conditioned tasks, hold out target-generating programs but also report alternate valid solutions; don't use exact-program-match as sole goal metric. Include distribution-matched simple baselines; sample operands so constant/majority outputs cannot inflate scores (especially EQ and bitwise zero).

Record generator seed, sample IDs, canonical hashes, overlap audit, difficulty, graph snapshot, oracle digest, and split name. Validate `train ∩ test = empty` under all specified canonicalizations. Require tests for data leakage and reproducibility.

## 6. Trainable models and training

### A. Baselines (all runnable)
1. Deterministic search with same tool set, timeout, action budget, and goal oracle.
2. Majority/constant predictor and syntax-to-operator grammar baseline for instruction following.
3. Small GRU recurrent controller producing actions and STOP with no presegmented *target* program.
4. Comparable-size autoregressive Transformer policy.
5. Direct neural answer predictor without external operators; match training examples and report compute/parameter differences.

### B. Primary model — actual Spectral LM
Find/recover original decoder-only FFT Spectral LM and checkpoint; establish param count (~13,576,704 historic), tokenizer (4096), model revision, and run equivalence smoke tests. At minimum: causal FFT depthwise conv; local causal depthwise conv; multi-resolution spectral filters (historically groups 16/32/128, or tested variants); SwiGLU; causal next-token loss; variable-length generation, padding, and masking. Validate causality against future perturbations, incremental decode versus full forward, and CPU/GPU consistency. Address FFT stream/state caching correctly; don't assert O(1) online inference if not true.

Add structured action tokens or heads, typed pointer selection for arguments and destinations, state/observation formatting, tool result delimiters, explicit `<HALT>`, `<VERIFY>`, `<UNSOLVED>`, and error tokens. Train supervised action prediction with teacher forcing, then train on complete observation-driven episodes. Auxiliary operator type and graph relation losses are optional ablations. Critically ensure model *actually* trains by verifying loss decrease and post-training versus randomly initialized held-out performance.

Suggested initial config (tune, don't assume optimum): 512-token context, 4096 original vocabulary plus reserved tool tokens as required, BF16 on supported CUDA hardware, batch accumulation to fit 12 GB, AdamW, clipping, deterministic evaluation, three seeds `[0,1,2]`; use 24k or more curated training examples initially; smoke at 256 examples and 1 epoch. For structural tasks scale dataset only after resolving leakage and baseline failures.

The controller predicts an action at each environment step, receives state and observations, and re-enters model inference until HALT or budget. Training on lengths <=3 and inference length 4-8 is a distinct extrapolation test. Report teacher-forced next-action, autoregressive exact program, executed answer, goal verified, illegal-action rate, HALT precision/recall, length distribution, latency and memory.

### C. Optional Qwenputer-style in-network fixed circuits
Only after external-engine model passes full qualification, implement a separate compiler experiment with fixed circuit weights and explicit recurrent memory. Show bit-exactness and benchmark against external engine with identical problem sets; don't conflate CPU-native EO with weights embedded in neural layers.

## 7. Qualification gates, hard tests, and honest interpretation

| Gate | Required qualification | Proposed target |
|---|---|---|
| G0 | baseline reproduced; independent references; no undocumented drift | all required unit tests PASS |
| R1 | held-out L4 program from unsegmented prompt | >=90% exact program |
| R2 | lengths 5-8 unseen in training | >=80% exact program by length (not pooled) |
| R3 | two+ named intermediate registers, branching and reuse | >=90% exact program |
| R4 | nested expressions, multiple valid topologies | >=85% valid execution and correct answer |
| R5 | uninitialized registers, malformed actions, unsupported values, invalid GEO signatures, HALT cases | >=99% safe rejection, zero unsafe execution |
| R6 | native GEO full adapter & independent reference tests | zero exact-domain mismatches; documented FP tolerances |
| R7 | goal synthesis without explicit program, matched search budgets | statistically supported gain over deterministic/grammar baselines or honest negative result |
| R8 | integrated Spectral LM trained with real weights; CLI loop | verified checkpoints, smoke and held-out end-to-end tests |
| R9 | graph-provenance queries + status enforcement | no candidate edge promoted without evidence |
| R10 | Lean proof checking fixture and fail-closed behavior | valid pass, false/invalid fail; no unsanctioned axioms |
| R11 | 3 seeds and 95% CIs for key metrics; CPU and CUDA reproducibility | report complete with artifacts |

**Targets are desired thresholds, not achieved claims.** If a gate is not met, deliver functional partial system and regression report with next actionable work; do not fabricate completion. The system counts as 'fully functional' for scope only when R8 passes and the interactive interface genuinely solves and checks supported tasks; 'formal-proving-capable' only when R10 and corresponding supported theorem tests pass. Full generalized mathematical intelligence is outside scope.

Evaluator must distinguish `exact_program` (instruction tasks), `valid_alternative_program` (goal tasks), `executed_answer`, `proof_verified`, `HALT_correct`, `rejection_correct`, timeouts, memory, wall-time. For each seed and split provide raw numerator/denominator, mean, standard deviation, 95% interval or clearly described bootstrap, and errors. Add breakdown by operations (especially equality), prompt mode, chain length, reused registers, GEO signature, and graph motif. Compare answer coincidence against exact program identity to detect chance matching.

## 8. Execution plan (carry out end to end)

**Phase 0 — Audit and reproduce.** Check branches/repos and installed versions. Run old tests and compositional benchmark smoke. Document environment + result discrepancy. Commit no code changes yet.

**Phase 1 — Contracts + engine.** Implement typed action schema, program parser, register memory, HALT, execution trace, budgets, independent reference, and negative tests. Run all unit tests and a random state-machine differential fuzzer against a simple Python interpreter. Commit.

**Phase 2 — Real recurrent policy.** Support raw prompt encoding without externally supplied target clause boundaries, predict action + arguments + destination + HALT; test across length and branching splits, run three seeds if GPU available. Keep failure report. Commit.

**Phase 3 — EO/GEO/graph/Lean adapters.** Verify actual library interfaces and pin commits; add native GEO binding, graph snapshot, optional Lean certificate loop, strict provenance and typed errors. Test independently and combined. Commit.

**Phase 4 — Actual Spectral LM integration.** Locate original code/checkpoint; implement tokenizer, action head, state representation, trainer, load/save, inference loop; confirm real gradient flow and weight updates, numeric determinism boundaries, GPU memory footprint. Commit.

**Phase 5 — Training campaigns.** Generate curricula D0-D4; run smoke, full multi-seed training, baselines, ablations (no tool / no graph / no recurrent feedback / no intermediate memory / fixed tool engine). Evaluate withheld composition and goal synthesis; prevent training on held-out split. Save immutable manifests/checkpoints/reports. Commit scripts/reports (not oversized binaries).

**Phase 6 — Application/UI.** Implement `python -m experiments.mapeogeo_llm.inference.cli --model <checkpoint> --interactive` and `--problem "..." --json` plus chat-style prompts. Demonstrate an actual answer, trace, verification status, and grounded explanation for a verified task, an invalid input, and unresolved proof. No network dependency needed for core inference. Commit.

**Phase 7 — Final independent audit.** Fresh-process replay from trained checkpoint (not training model in memory), automated full test suite, smoke train on CPU, long test on GPU, no-regression compositional baseline, code lint/static checks, theorem/graph status audit, input-fuzz run, timing/memory profiling. Produce report containing PASS/FAIL/OPEN per gate, exact commands and artifact digests. Push only after user repository policy allows; do not merge to main without review.

## 9. Suggested executable commands (adjust to observed repo and environment)

PowerShell:

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\nateb\Documents\MAPEOGEO-frozen-main\mapeogeo-llm-worktree'
git status --short --branch
git rev-parse HEAD
git switch experiment/mapeogeo-llm-recurrent
python -m pip install -e '.[dev]'
python -m pytest -q experiments/mapeogeo_llm/tests
python -m experiments.mapeogeo_llm.training.train_sft --config experiments/mapeogeo_llm/configs/smoke.yaml
python -m experiments.mapeogeo_llm.evaluation.benchmark --config experiments/mapeogeo_llm/configs/smoke.yaml
python -m experiments.mapeogeo_llm.training.train_sft --config experiments/mapeogeo_llm/configs/full_cuda.yaml
python -m experiments.mapeogeo_llm.evaluation.benchmark --config experiments/mapeogeo_llm/configs/full_cuda.yaml
python -m experiments.mapeogeo_llm.inference.cli --checkpoint '<checkpoint-path>' --interactive
```

The above commands are **contractual target entrypoints to implement**; they are NOT claims that these files or CLI options already exist. If actual package name differs, update docs and entrypoints consistently. Environment lock must be tested on the local Windows Python and GPU stack; use virtual environment. Collect `nvidia-smi`, CUDA and torch versions, `git diff`, `pytest` summary, and JSON outputs.

## 10. Required end-to-end demonstrations

1. **Instruction execution:** `Compute XOR(ADD(a,b), c)` with concrete inputs, model emits and executes correct multi-step action program; answer matches independent Python oracle.
2. **Intermediate DAG reuse:** `r0=ADD(a,b); r1=XOR(r0,c); r2=AND(r0,r1)`; register reuse is correct; model trace gives exact result.
3. **Unseen-length test:** training <=3 instructions; inference 4,5,6,7,8; report each length separately and HALT correctness.
4. **Goal-based synthesis:** give goal constraints and allowed operations with no target program; controller searches and finds a correct sequence within budget or says UNSOLVED, and compares to matched deterministic search.
5. **Geometric computation:** Cl(3,0) products including anti-commutation and mixed signature; validate independently; demonstrate symbolic exact cases separately from floating tolerance cases.
6. **Graph reasoning:** retrieve source-bound, verified relationships to select next step; refuse promoting candidate edges lacking certificate evidence.
7. **Lean proof:** check a small nontrivial theorem using the real Lean kernel; reject false or sorry/axiom-based spoof. Report all assumptions.
8. **Interactive model:** fresh launched process from checkpoint, natural-language prompt -> structured action trace -> numerical/proof outcome -> status and source.
9. **Negative cases:** missing registers, invalid opcode, bad operand shape, invalid signature, parser injection attempts, impossible bounded goal, HALT too early, step/time budget exhaustion; no false VERIFIED results.

## 11. Deliverables

- Complete runnable source and versioned environment.
- At least one trained Spectral LM checkpoint; baseline recurrent/Transformer checkpoints when feasible.
- Dataset generators + manifests (no evaluation contamination); independent math oracles.
- Exact/native EO and GEO adapters, graph and optional Lean bridge with status contract.
- Fully functioning stateful inference agent, CLI, and minimal interactive interface.
- Tests for every layer; 3-seed evaluation; profiles for GPU 12 GB and CPU.
- `reports/final_qualification.md`, machine-readable `qualification.json`, tables and failed-case exemplars.
- A succinct engineer's summary: what works today, what was actually executed, which gates remain OPEN, and exact next work.

## 12. Final report template

```
Project / branch / HEAD / dependency SHAs:
System: OS, Python, torch, CUDA, GPU, RAM:
Repro command(s):
Datasets / manifests / train-test leakage audit:
Checkpoint(s), hashes, parameter counts:
G0, R1..R11: PASS / FAIL / OPEN with evidence:
Per-seed metrics with n, CI, validity, exact answer, proof correctness:
Baselines, ablations, efficiency:
Live interactive demo transcripts (input/trace/output/status):
Independent verification logs (EO, GEO, graph, Lean):
Known constraints, safety / honesty boundaries:
Commits, remaining work, unmerged changes:
```

## 13. Copy-paste instruction to start local Codex

> Work autonomously through the entire MAPEOGEO-LLM engineering handoff in `experiments/mapeogeo_llm/` on branch `experiment/mapeogeo-llm-recurrent`. Audit the repository before changes, preserve `experiment/mapeogeo-llm-compositional` and its baseline, implement the full typed EO/GEO execution loop with register memory and learned HALT, integrate the actual 13.6M Spectral LM (recover its existing source/checkpoint if available; otherwise implement and train an explicitly new version), bind and independently test real GEO and MAPEOGEO graph interfaces, add optional fail-closed Lean proof checking, generate leak-free datasets with goal-conditioned synthesis, train and compare matched baselines over three seeds, and complete R1–R11 with actual runs. Build a usable local CLI and interactive interface that loads trained weights and returns trace-backed verified/refuted/unresolved answers. Never claim completion from trivial transcript parsing, unverified arithmetic, unrun benchmarks, or proof-shaped text. Make incremental commits, maintain pinned reproducibility manifests, and deliver `reports/final_qualification.md` plus machine-readable `qualification.json`. When blocked, record the blocker and continue with independent work; do not silently weaken acceptance gates.

---

**Scope caveat:** This handoff defines a complete usable research-grade mathematical LLM over a *qualified bounded operator vocabulary*. It does not claim to solve arbitrary mathematical problems, prove open conjectures, or confer general theorem-proving ability. Expand operator/proof domain only after validated results justify it.
