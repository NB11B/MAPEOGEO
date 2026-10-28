# MAPEOGEO-LLM implementation plan

> For agentic workers: use the supplied bounded task and test-first implementation. Root orchestrates executor and independent reviewer roles; no worker commits or spawns reviewers.

Goal: implement the supplied engineering handoff as a bounded mathematical agent, retaining an explicitly new causal FFT Spectral LM when canonical source is unavailable.

Spec: C:/Users/nateb/Downloads/MAPEOGEO_LLM_CODEX_ENGINEERING_HANDOFF.md (user supplied specification, not measured evidence).

Repository: C:/Users/nateb/Documents/MAPEOGEO-frozen-main/mapeogeo-llm-worktree
Base: 28e56892f7965805c9689c3b423cdbb9d399a96e, experiment/mapeogeo-llm-recurrent.
Runtime: C:/Users/nateb/AppData/Local/Programs/Python/Python313/python.exe; PyTorch 2.11.0.dev20260127+cu128; RTX 5070 Laptop, 8150 MB. Access requires escalated exec in this environment.

## Constraints and decisions

- Preserve operators.py, compositional.py, and pre-existing untracked recurrent/ and tests/test_recurrent.py. No main/compositional branch changes, push, merge, or external messaging.
- Existing handoff supplies the architecture and autonomous execution request; no redundant design approval required. Root decides implementation details and records deviations.
- Never accept a model score, generated assertion, graph status label, numerical tolerance, or parser transcription as independent proof.
- Native C GEO is preferred. Python reference is a declared development backend, never native qualification.
- Graph returns provenance and candidate distinctions; certified metadata alone is not independently replayed proof.
- Lean supports a restrictive generated theorem interface with fixed prelude and named checked theorem. Never accept arbitrary Lean command programs as proof.
- Exact integer EO is modular uint8. Floating GEO verification is numerical and labeled accordingly.
- All model actions traverse one canonical executor. No teacher program or private oracle label in inference state.
- Training artifacts stay local, with manifests and hashes. Qualification reports contain actual denominators, failures, OPEN gates and commands.
- No historical Spectral source/checkpoint found in bounded local/history search. New implementation is not weight-compatible by claim.

## Acceptance and review focus

Execute the handoff phases through a fresh-process trained CLI, documenting unmet empirical gates rather than redefining them. Review malformed JSON/types and NaN, stale verification after register overwrite, early HALT, graph candidate promotion, hidden goal/label leakage, post-timeout state mutation, theorem source injection, future-token leakage and checkpoint reload.

## Task 1: canonical runtime

Owner: runtime executor. Files: contracts.py, executor.py, parser.py, datasets/oracle.py, tests/test_contracts.py, test_executor.py, test_memory.py, test_parser.py, test_halt.py, test_verification.py.

Interfaces: frozen/dataclass Task(problem:str, inputs:dict[str,TypedValue], goal:dict, budget:Budget); TypedValue(kind,value); Ref(kind,id,value optional); Action(op,src tuple,dst optional,kwargs dict,reason_code optional); canonical to_dict/from_dict helpers. Engine(task, geo=None, graph=None, lean=None), step(action)->Observation, result()->dict, observation()->dict. Provide exact signatures early to root/integration owner. Version canonical schema mapeogeo.llm.action.v1. ALU execution uses original CompiledALU. Independent checker uses Python integer operators and separate expression evaluator. Task goal kinds expression (safe AST), target (uint8 goal value), geo_expression, graph, lean; unsupported goals fail closed. ASSERT adds obligation, VERIFY checks goal against current state independently, HALT requires current checked output or explicit unresolved status. Verification binds state/output digest. Failed action does not mutate registers/trace; structured error is returned. Bound steps, registers, graph expansion, token/input size and wall time; no eval.

- [ ] Add failing tests for ADD/XOR/AND DAG reuse, overflow, malformed types, missing/invalid registers, unsafe expressions, early HALT, changed verified register, explicit UNSOLVED, exhausted budget, replay/canonical digests.
- [ ] Implement smallest complete runtime with exact contracts and independent verification.
- [ ] Run focused tests and deterministic random state-machine differential test against independent plain interpreter; preserve full original test suite.
- [ ] Independent review and correction before integration acceptance.

## Task 2: operator and evidence adapters

Owner: adapters executor. Files: geo_adapter.py, graph_adapter.py, lean_adapter.py, tests/test_geo.py, test_graph.py, test_lean.py, fixtures/, scripts/build_geo.ps1. No runtime/model files.
Interfaces: GeoAdapter.gp(a:list,b:list,signature:list)->list and grade(a,grade,signature)->list; validated native ABI and explicit backend metadata. GraphAdapter.query(node_id,relation=None,max_results=32)->dict with source commit/snapshot digest and node/edges; no candidate certification. LeanAdapter.verify(proposition:str,proof:str,timeout_seconds:float=10)->dict status/evidence. Interface accepts restricted propositions/proofs or structured approved theorem families, rejects unsafe unrestricted source; communicate exact supported subset.

- [ ] Add failing ABI, malformed dimension/signature, Pauli Cl(3,0), mixed metric, associativity/bilinearity/grade tests; native build against actual local checkout and pin SHA.
- [ ] Bind actual MAPEOGEOv2 graph schema read-only; fixture candidate versus certified metadata, no false proof acceptance; test real snapshot integration when feasible.
- [ ] Run real Lean valid/false/malformed/timeout/sorry/axiom/hypothesis injection tests, fixed process arguments, provenance and assumptions.
- [ ] Independent review and correction.

## Task 3: explicitly new Spectral LM

Owner: model executor. Files: models/spectral_lm.py, models/tokenizer.py, models/action_head.py, models/recurrent_policy.py, tests/test_spectral.py. No runtime/training files.
Interfaces: SpectralConfig(vocab_size=4096, d_model configurable, n_layers configurable, max_seq_len configurable); SpectralLM(config).forward(input_ids, attention_mask=None)->logits[B,T,V]; generate(input_ids,max_new_tokens,eos_token_id)->tokens. Expose config as serializable dict, num_parameters. Tokenizer train(texts,model_prefix,vocab_size=4096), encode/decode/save/load with SentencePiece BPE and reserved action/HALT/VERIFY/UNSOLVED/result tokens; no fake tokenizer checkpoint. Tiny test configurations allowed, main config approximately 13.6M parameters and explicit measured count.

- [ ] Add failing causal future-perturbation, padding invariance, prefix-recompute decode equivalence, CPU/GPU numeric consistency, gradient/update/save-load tests.
- [ ] Implement causal zero-padded FFT depthwise conv with multi-resolution kernels 16/32/128, local causal depthwise branch, residual normalization, SwiGLU, causal next-token loss helper. Float32 FFT avoids unsupported half FFT lengths. Prefix recomputation is documented, not constant-time caching.
- [ ] Runnable comparable Transformer and GRU next-token baselines in recurrent_policy.py with matching forward contract.
- [ ] Independent review and correction.

## Task 4: dataset, training, inference, evaluation integration

Owner assigned after interfaces settle. Files: datasets/generate.py, splits.py, schemas.py; training/train_sft.py, train_policy.py; inference/agent.py, cli.py, chat.py; evaluation/benchmark.py, compare_baselines.py, audit_leakage.py, report.py; configs/{smoke,full_cuda,ablations}.yaml; tests/test_dataset.py, test_leakage.py, test_train_smoke.py, test_inference.py, test_end_to_end.py.

- [ ] Deterministic curricula D0-D4 with independent label search and evaluator; canonical goal/program/template/motif split audits. Report unsupported family partitions OPEN rather than fake leakage PASS.
- [ ] Serialize full unsegmented prompt and public state; next-action token prediction with explicit tool observations and HALT. No program fed at evaluation. Learned output strictly parsed/validated by Engine. Deterministic search is separate baseline or explicitly labeled fallback, never attributed to neural policy.
- [ ] Train smoke CPU/CUDA, loss/weight-change checks; train main Spectral at >=24k examples seeds 0,1,2 if feasible within measured resource bounds. Checkpoint includes architecture/tokenizer/config/data manifest/source hashes, seed and weights digest.
- [ ] Match baseline budgets/datasets; compare pretraining and posttraining; per-length R1/R2, reuse/DAG, goal verified, invalid/HALT metrics with n, CIs, latency/peak memory and failures. A low-accuracy trained model is not a qualified release.
- [ ] Fresh-process CLI with --checkpoint/--model, --problem, --json, --interactive and trace-backed grounded response; verified/invalid/unresolved demos.
- [ ] Independent whole-path review and fixes; regression tests and static checks.

## Task 5: provenance and closure

Root: preserve baseline smoke evidence and initial untracked-file hashes, pinned environment and source commits; knowledge-cycle task record. Curator after review records accepted outcomes/contradictions. Produce reports/final_qualification.md and qualification.json with G0 and R1-R11 PASS/FAIL/OPEN strictly supported by artifacts. Copy concise deliverables into this chat outputs. Incremental commits only for authorized owned files; exclude user untracked files and large artifacts.

## Preflight interface audit

| Pair/task | Producer and consumer | Ruling |
|---|---|---|
| 1/2 | Engine uses adapters above | Optional adapters must return structured error; availability cannot certify goal |
| 1/4 | Task/Action/Engine serialization | Runtime owner supplies exact API before integration starts |
| 3/4 | token IDs/logits/config/checkpoint | Integration owns loss/training; model owner supplies causal backbone |
| 2/4 | GEO/graph/Lean observations | Training label provenance separated from inference observations |
| 1 | frozen records versus mutable dict fields | Deep canonical snapshots/digests required; frozen outer dataclass alone insufficient |
| 2 | floating GEO vs proof | Numerical evidence explicitly distinguished from exact/formal |
| 3 | historic architecture vs no canonical source | New implementation, measured parameter count, no pretrained claims |
| 4 | full qualification vs failed empirical targets | Implement/evaluate honestly; retain FAIL/OPEN, never adjust thresholds |
| 5 | preserve user changes vs commits | Stage only newly owned explicit paths |

## Execution ledger

- Phase 0: existing tests 18 passed (2.82s). Small CUDA compositional run completed, 393216 EO cases exact; 1-epoch learned smoke had 0/32 program exact each split and 100% invalid, not baseline accuracy reproduction. Historical three-seed accuracy remains unrerun.
- Pending: Tasks 1-5.
