# Independent foundation review record

Reviewer: reviewer-role agent review_core, read-only inspection of actual new source files and surrounding code, 2026-10-28.

## Model task

Initial verdict FAIL: baseline padded generation selected PAD logits and mishandled finished rows (HIGH); shifted loss included source padding (MEDIUM); dotted SentencePiece prefix path incorrect (LOW). Owner added failing regressions and corrected these behaviors.

Scoped recheck PASS: 19/19 tests passed including actual CUDA in 4.94 s. Independent repro: Transformer expected/generated 5/5; GRU 61/61. Spectral compact vs left-padded loss 23.1398697 vs 23.1398659, within FFT tolerance. No learned-quality or training gate is implied by model mechanics tests.

## Runtime task: corrections in progress

- HIGH: wall deadline checked before tool execution, but not after it; slow successful call could commit late. Require second deadline check before commit and immutable rejection.
- HIGH: target tasks did not enforce allowed operators or program-op budget. Canonical representation decided as goal.allowed_ops and goal.max_ops; exclude VERIFY/HALT from program-op count, include constraints/counter in replay digest.
- MEDIUM: strict nested serialization validation missing in ProofObligation/VerificationResult/Observation/Episode.
- MEDIUM: Action/dict payload size bypassed string-only parser limit; cap canonical bytes and adapter payloads; enforce input token boundary.

Independent runtime test run before corrections: 47 passed in 3.26 s. Passing tests did not cover the reported counterexamples.

## Adapter/runtime integration: correction in progress

HIGH: actual Lean adapter returns axioms and kernel_checked in nested evidence; Engine read top-level axioms. Real valid theorem was downgraded to UNSOLVED. Require one validated schema and real adapter-through-engine tests for valid/false/malformed/timeout paths. Adapter focused suite alone passed 36/36 in 4.70 s and missed this integration fault.

No reviewer edits. Root assigned confirmed corrections to runtime owner.

## Foundation scoped recheck

Runtime and adapters PASS after corrections: 104 focused tests (65 runtime, 39 adapters), 10.70 s. Independent counterexamples re-run: slow successful GEO result after a 5 ms budget rejected without registers; disallowed ADD under XOR-only goal rejected; real Lean 1+1=2 verified through Engine. Nested replay, canonical byte/token bounds, goal operator budget/digest, native receipt/digest and dirty-source regressions present. Unbound same-ABI DLLs remain usable but explicitly unqualified and source_commit is null.

Root accepted Tasks 1-3 foundations subject to their stated domain bounds. This does not qualify training/inference or R1-R11 as a release. Datasets and application integration are separate review gates.
