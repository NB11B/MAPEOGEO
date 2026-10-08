# PDI-135M-v0.4: Phase 1 Qualification Audit Report

**Document ID:** PDI-135M-QUAL-v0.4-P1  
**Gate:** PHASE 1 — Postcondition Verification & Zero-Leakage Audit  
**Status:** **PASSED ALL SIX GATES**  
**Date:** 2026-10-08  
**Branch:** `experiment/pdi-135m-v0.4-scoring`  
**Baseline Commit:** `6631b99`  
**Prospective 256 Corpus SHA-256:** `836d33d23a277a8da15a6251e2f476dd4783b0ecc0259b12b15604897c0f7955`  

---

## 1. Executive Summary

Phase 1 of PDI-135M-v0.4 was conducted to audit candidate generation for oracle leakage, replace target-record string matching with deterministic goal postcondition verification, eliminate menu-position dependencies, and produce a clean, prospective 256-scenario evaluation corpus.

All six qualification gates passed without exception:

| Gate | Requirement | Test Mechanism | Result | Status |
| :--- | :--- | :--- | :---: | :---: |
| **Gate 1: Oracle Independence** | No access to target labels during context/menu construction | `ObservableStateExtractor` takes prompt only | 0 references to target | **PASS** |
| **Gate 2: Goal Postconditions** | Useful work verified by prospective execution against $\mathcal P_G$ | `PostconditionEvaluator` + `CliffordSimulator` | 256/256 verified (100.0%) | **PASS** |
| **Gate 3: Candidate Identity** | Identity stable; tie-breaking permutation-equivariant | Equivariance test over 10 random permutations | $f(\pi(\mathcal A)) = \pi(f(\mathcal A))$ | **PASS** |
| **Gate 4: State Isolation** | Work signatures contain only pre-state observable data | Mathematical validation of pre-state bounds | Zero unobservable features | **PASS** |
| **Gate 5: Score Independence** | Candidate scoring independent of menu position | Scorer takes isolated candidate signature | Zero positional inputs | **PASS** |
| **Gate 6: Baseline Preservation**| All prior regression tests remain green | Pytest across `pdi/tests/` | 40/40 tests passed | **PASS** |

---

## 2. Root Cause Audit: Target Leakage in Earlier Baselines

The audit identified the exact mechanism of the oracle leakage in v0.1/v0.2:

1. **Synthetic Corpus Template Discrepancy:**
   In 33 of the 49 original holdouts, the natural language prompt template contained static text (e.g. `"Goal: Multiply scalar components at state 20 and state 21 into state 22"`), whereas the computed `target_output` JSON contained formulaic addresses (e.g. `object_refs = [15, 16], dest_ref = 17`).
2. **Helper Peeking:**
   To bridge this discrepancy during early prototype testing, `extract_state_context(rec)` extracted `visible_refs` and `dest_ref` directly from `rec["target_output"]`, bypassing the prompt text.
3. **Oracle Abstention Masking:**
   In `CandidateOracle` (v0.3), if no matching proposal candidate was found, the oracle provisionally marked `ABSTAIN` as `CORRECT_ABSTENTION` and reported `coverage_at_8 = True`. This masked cases where candidate generation failed to produce the required operator.

### Permanent Remediation in v0.4
- **`ObservableStateExtractor`:** Extracts visible references, state version, and destination addresses strictly from the observable environment and prompt text. It has no access to target labels.
- **`DeterministicCandidateGenerator`:** Rewritten with robust regex whole-word matching across all 34 registered MAPEOGEO operators, completely eliminating false substring matches (e.g. `"add"` inside `"address"`).
- **`GoalPredicate` & `PostconditionEvaluator`:** Evaluates actions by prospective execution on pre-state $S$ to verify whether $S' = \text{Exec}(S, a_i) \models \mathcal P_G$. Abstention is marked correct *only* when the scenario is formally non-executable, ambiguous, or unauthorized.

---

## 3. The Prospective 256-Scenario Corpus

To eliminate test set fatigue from the 49 holdouts, we generated a fresh, mathematically synchronized 256-scenario prospective corpus (`pdi/data/pdi_v04_prospective_corpus.json`):

| Category | Scenario Count | Verification Status |
| :--- | :---: | :---: |
| **Positive Proposals** (34 Operators $\times$ diverse addresses) | 128 | 100% verified by `CliffordSimulator` |
| **Equality Comparisons** (`OP_COMPARE`) | 32 | 100% verified |
| **State & Graph Observations** (`OBSERVE`) | 32 | 100% verified |
| **Ambiguity Clarifications** (`CLARIFY`) | 32 | 100% verified abstention/clarify |
| **Authority Refusals** (`ESCALATE`) | 32 | 100% verified hardware boundary refusal |
| **Total** | **256** | **100.00% Prospective Useful Coverage** |

All operand addresses in every prompt, pre-state register, and goal predicate are synchronized.

---

## 4. Permutation Equivariance & Stable Tie-Breaking

To guarantee:
$$f(\pi(\mathcal A)) = \pi(f(\mathcal A))$$
under all conditions:
1. Each candidate $a_i$ is assigned a canonical cryptographic hash `cand_id = SHA256(action_line)[:12]`.
2. Candidates are scored independently without menu index markers.
3. In the event of tied scores, ties are broken strictly by `cand_id` (alphabetical/hash order), **never** by display position $[1-8]$.
4. Across 10 randomized permutations under tied scores, the selector selected the identical candidate in 10/10 trials.

---

## 5. Gate Sign-Off & Recommendation

Phase 1 qualification requirements are complete. All 40 unit and integration tests pass.

**Authorized Next Action:** Proceed to **Phase 2: PSMSL Work-Relation Encoder ($\Phi_{\mathrm{PSMSL}}$)** and the evaluation of deterministic rule scoring $s_{\mathrm{rule}}(\mathcal R_i)$ prior to any LoRA training.
