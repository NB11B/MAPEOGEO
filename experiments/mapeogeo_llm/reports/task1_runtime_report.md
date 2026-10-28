# Task 1 canonical runtime implementation report

Date: 2026-10-28  
Branch/worktree: `experiment/mapeogeo-llm-recurrent` / `mapeogeo-llm-worktree`  
Scope: Task 1 only; no commits, pushes, adapter/model edits, or changes to the preserved original `operators.py`.

## Implementation completed

- Added immutable, canonical JSON contracts with schema `mapeogeo.llm.action.v1`, strict typed values, deep snapshots, canonical SHA-256 digests, and `to_dict`/`from_dict` replay helpers.
- Added strict duplicate-key/NaN/oversize-safe JSON action parsing; no `eval` or executable text path.
- Added transactional `Engine` execution over the preserved `CompiledALU`, typed register memory, action arity/kwargs/destination validation, bounded steps/registers/graph expansion/input/wall time, and structured fail-closed errors.
- Added independent goal verification for canonical integer expressions, typed targets, answer-free GEO expressions, restricted Lean adapter results, and fail-closed graph metadata.
- Bound verification to the current state digest. Register changes make certificates stale; failed actions and post-timeout actions do not mutate registers, trace, obligations, verification, or counters.
- Added explicit HALT semantics: checked VERIFIED/REFUTED output or explicit UNSOLVED only; open assertions prevent verified halt.
- Added an independent plain-Python uint8 operator oracle, safe AST evaluator with canonical `ADD/SUB/XOR/AND/OR/EQ` calls, and independent dense bitmask GEO product/grade references.

## Files changed

- `experiments/mapeogeo_llm/contracts.py`
- `experiments/mapeogeo_llm/executor.py`
- `experiments/mapeogeo_llm/parser.py`
- `experiments/mapeogeo_llm/datasets/oracle.py`
- `experiments/mapeogeo_llm/tests/test_contracts.py`
- `experiments/mapeogeo_llm/tests/test_executor.py`
- `experiments/mapeogeo_llm/tests/test_memory.py`
- `experiments/mapeogeo_llm/tests/test_parser.py`
- `experiments/mapeogeo_llm/tests/test_halt.py`
- `experiments/mapeogeo_llm/tests/test_verification.py`

## Behavioral and verification boundaries

- ALU computation uses the original compiled circuit; verification never trusts the circuit result and evaluates the task goal through separate code.
- `REFUTED` means the proposed candidate does not satisfy the independently evaluated goal (`scope=candidate_vs_goal`); it is not a proof that no solution exists.
- Lean kernel rejection is `UNSOLVED`, not proposition refutation.
- Graph query metadata is never independently replayed proof and cannot produce VERIFIED.
- GEO verification accepts only public expression operands/signature/grade/tolerance and computes the expected numerical result privately; expected answers are not included in observations/evidence.
- Expression and target expected values are likewise omitted from verification evidence.

## Tests added and updated

47 Task 1 tests cover canonical contracts/replay, malformed JSON/types, duplicate keys, NaN, register bounds, ADD/XOR/AND DAG reuse, overflow, wrong-action verification, stale verification, immutable failures, early/explicit HALT, budget exhaustion, open obligations, safe/unsafe expressions, nested canonical calls, typed target equality, graph non-promotion, Lean rejection semantics, independent GEO goals, post-timeout immutability, and deterministic replay digests.

The state-machine differential test runs 40 deterministic episodes of 20 randomly selected EO actions (800 transitions total) against the independent plain-Python interpreter.

## Commands and results

1. Baseline before Task 1:
   - `python -m pytest -q experiments/mapeogeo_llm/tests`
   - Result: `10 passed, 1 warning` (the parent/root separately observed 18 tests after concurrent files settled).
2. Initial focused RED:
   - Task 1 focused pytest command.
   - Result: six collection errors because `contracts.py` did not exist; expected RED.
3. Focused GREEN after initial runtime:
   - Task 1 focused pytest command.
   - Result: `35 passed, 1 warning`.
4. Strict typed/digest RED:
   - Contract/executor tests.
   - Result: five expected failures (four typed-value validation cases and stale returned observation digest).
5. Strict typed/digest GREEN:
   - Full Task 1 focused tests.
   - Result: `40 passed, 1 warning`.
6. Verifier-boundary RED:
   - Verification/HALT tests.
   - Result: five expected failures (function notation, bool/int equality, Lean rejection, GEO answer-free goal, open obligation).
7. Verifier-boundary GREEN:
   - Full Task 1 focused tests.
   - Result: `45 passed, 1 warning`.
8. Replay/timeout RED then GREEN:
   - Contract/executor RED: one expected missing `Episode.from_dict` failure; timeout immutability already passed.
   - Full Task 1 GREEN: `47 passed, 1 warning`.
9. Broad concurrent suite excluding incomplete spectral owner file:
   - `python -m pytest -q experiments/mapeogeo_llm/tests --ignore=experiments/mapeogeo_llm/tests/test_spectral.py`
   - Result: `85 passed, 1 failed, 1 warning`; sole failure was adapter-owned `test_native_build_is_byte_reproducible` because `Get-FileHash` was unavailable inside the spawned PowerShell process. No Task 1 failure.
10. Static compilation:
    - `python -m py_compile experiments/mapeogeo_llm/contracts.py experiments/mapeogeo_llm/executor.py experiments/mapeogeo_llm/parser.py experiments/mapeogeo_llm/datasets/oracle.py`
    - Result: exit 0.

The warning in Python test runs is the environment's existing PyTorch `pynvml` deprecation warning.

## Remaining risks and blockers

- Independent reviewer verdict is pending at this executor handoff.
- Adapter and model owners were still editing concurrently. The full suite could not be reported green at this point: spectral collection was initially incomplete, and the broad non-spectral run had the adapter-owned PowerShell hashing failure documented above.
- GEO verification is numerical and explicitly labeled independent numerical oracle evidence; it is not formal proof.
- Wall-clock checks occur at action boundaries; a blocking adapter must enforce its own timeout contract (Lean exposes one). Runtime prevents state commit after a tool error but cannot forcibly preempt an arbitrary in-process adapter.
- No commit or push was made, per executor instructions.

## Independent review correction pass

The independent reviewer identified five material runtime-boundary gaps. Focused RED→GREEN corrections were applied:

1. Wall deadline is rechecked after tool execution and before the commit closure. A late-returning GEO adapter now yields `BUDGET_EXHAUSTED/WALL_TIME` without changing registers, trace, counters, or verification state.
2. Optional D2 target constraints are canonicalized as `goal.allowed_ops` plus `goal.max_ops`. Both must appear together and are validated against supported EO/GEO operators. EO/GEO program operations alone consume this counter; VERIFY/HALT do not. Disallowed and over-budget actions fail before execution, and constraints/counter are bound into state digests and public observations.
3. Nested contract replay now validates booleans, statuses, object/list shapes, contained dataclass types, and lowercase 64-character SHA-256 digests.
4. Task lexical token limits and canonical/raw action byte/token limits now apply to string, dict, and direct-Action ingress. Tool outputs and evidence are bounded before commit, including adapter metadata and graph payloads.
5. Lean verification now reads the adapter's actual nested `evidence.kernel_checked` and `evidence.axioms` schema. VERIFIED requires status VERIFIED, `kernel_checked=true`, and exactly empty axioms. Absent/malformed evidence fails closed; valid false/malformed/timeout outcomes remain UNSOLVED.

Added review regressions cover slow-returning GEO, D2 disallowed/exhausted operators, strict nested replay, task/action/result size limits, spoofed Lean status, and real Engine+Lean valid/false/malformed/timeout paths.

Review correction verification:

- Focused reviewer regression suite: `47 passed, 1 warning`.
- Real Engine+Lean integration subset: `19 passed, 1 warning`.
- Complete corrected Task 1 suite: `65 passed, 1 warning` before the final raw-JSON size symmetry regression; final closure command is recorded in the parent orchestration report.

Final closure after the raw-JSON regression:

- `py_compile` for the four Task 1 production modules: exit 0.
- Complete corrected Task 1 suite: `65 passed, 1 warning` in 4.79 seconds.
- Whole concurrent `experiments/mapeogeo_llm/tests` collection remained blocked by integration-owner modules not yet present: `training` (two test modules) and `inference` (one test module). These are outside Task 1 ownership and were reported without modification.
