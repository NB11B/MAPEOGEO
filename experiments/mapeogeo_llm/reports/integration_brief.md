# Task 4 integration brief

Implement the full Task4 of reports/implementation_plan.md after reading final Task1/Task3 interfaces. Scope is datasets/{generate,splits,schemas}.py, training/, inference/, evaluation/, configs/, integration tests. Preserve preexisting operators/compositional/recurrent and other workers' new modules.

## Decided architecture

Use the causal Spectral LM with typed action heads fed by the last nonpadding hidden state of the complete public prompt plus current state/observations. Train the LM next-token loss as well as structured action prediction (op, source1, source2, destination and termination/outcome as needed). This is an actual trained spectral language backbone, explicitly specialized rather than a broadly pretrained conversational model. Original natural-language or expression prompt remains intact; no supplied action boundaries or teacher target in inference. A small finite grammar/domain is acceptable only when clearly reported; do not call unsupported English understood.

Canonical Engine from Task1 is sole authority. Invoke one predicted action, append public observation, reencode and predict again. VERIFY/HALT are policy decisions. Do not automatically append a known solution to make the neural policy pass. Explicit deterministic-search mode/baseline may solve supported tasks, but its successes must never count as neural successes. Invalid actions return error feedback and may be revised within bounded attempts; account for invalid-action attempts separately so unchanged failed state cannot bypass total agent budget.

Train action heads and causal LM jointly. Model.hidden_states(ids,mask)->[B,T,D] is being added. Use SentencePieceTokenizer provided by Task3 with vocab4096. Include model/tokenizer/action-head configs, data hashes, source hashes, seeds, optimizer config, training loss and pre/post heldout metrics in checkpoint metadata. Use weights_only=True on torch.load and validate format/dimensions; checkpoint digest before fresh-process replay.

## Public task and action encoding

Use exact Task1 contracts. Problems include expression tasks, target-value synthesis, GEO, graph retrieval context and restricted Lean. Model observation may include task goal and input values but never target action or private expected answer. For training examples, teacher rollout must be separate field omitted from inference text formatter. Avoid including a hidden verifier output that gives the answer before model executes.

Learned action head categorical vocabulary should include six EO, GEO_GP/GEO_GRADE, GRAPH_QUERY, ASSERT, VERIFY, HALT and UNSOLVED termination. Argument pointers select known input names a..h and r0..r15; destination r0..r15. Invalid selections are handled by Engine. Any validity masking must be based on public types/initialized registers and grammar, not parsed desired program/op. Verification args can bind current predicted output. For explicit unresolved use HALT kwargs status UNSOLVED.

The prompt normalizer can safely recognize supported expressions and input bindings (e.g. Compute XOR(ADD(a,b),c) with a=17,b=9,c=3), structured JSON Task, bounded synthesis goals, supported GEO expressions and closed Lean arithmetic. Parsing the goal for independent checking is permitted; compiling it into an action program is only permitted for dataset labels or declared grammar baseline.

## Data and splits

Generate reproducibly >=24000 training examples default, 256 smoke, seeds0,1,2. D0 EO, D1 chains/DAG and unsegmented forward/reverse/nested prompts, D2 bounded target synthesis without program (separate bounded search teacher), D3 signature/grade tasks, D4 graph/proof capability cases. Ensure non-unique target programs accepted by goal verification. For unsolvable target labels, only claim bounded unsatisfiable when exhaustive same-budget search completed; otherwise UNSOLVED.

Training max length3 versus heldout length4,5,6,7,8 distinct splits. Hold out operator pairs/triples, AST families, reuse motifs, templates and canonical goals explicitly; avoid pretending arbitrary random rows satisfy those tests. Keep separate IID and strict structural splits when some partitions overlap by design, report overlap dimensions honestly. Build audit function rejecting intersections for each split's declared excluded keys. Store stable sample IDs, goal/AST/pattern/template/motif hashes and source manifest. Need tests showing changed labels cannot affect public model input, repeatability, and contamination rejection.

## Training and evaluation

train_sft --config path [--seed --device --epochs overrides] runnable. CPU smoke tiny model; full_cuda primary ~13.6M with 8GB-safe batches, 24k examples. No heavy GPU job until root baseline run finishes; short smoke allowed in coordination. train_policy can share supervised episode trainer explicitly, do not imply reinforcement learning. Comparable transformer/GRU and direct answer baselines must be runnable, with compute/parameter count disclosed. Deterministic search, constant and grammar baselines use same tasks/budgets.

benchmark loads saved weights fresh and reports raw n, correct counts, Wilson interval for proportions, seed mean/std/CI described; exact program vs valid alternative vs executed answer vs verified output vs legal/HALT/errors/timeouts separate. Show R1/R2 each length and R3 reuse, R4 nested; no weighted pooled score substitutes. R7 negative result valid; R8 requires actual learned fresh-process success with trace, not only checkpoint file creation. Gates remain OPEN/FAIL if unsupported/unrun/under threshold.

CLI target --checkpoint (alias --model), --problem, --json and --interactive. Chat loops over ordinary text and :quit, prints result and grounded trace explanation. Unsupported text yields INVALID_INPUT/UNSOLVED instead of fabricated fluent answer. Expose explicit --policy search for bounded search baseline, default spectral learned. Core inference offline.

## Validation

Tests first: data determinism/overlap and private-label independence, one real training batch changes weights/loss, checkpoint reload equivalence, learned action-loop uses observations and halts, corrupted/invalid input failure, CLI subprocess JSON. Then real CPU smoke, full CUDA Spectral seeds0/1/2; baseline comparisons and fresh-process verified/invalid/unresolved demos. Independent reviewer audits labels and inference paths. Report exact limits and changed files to root; no commits/push/subagents.
