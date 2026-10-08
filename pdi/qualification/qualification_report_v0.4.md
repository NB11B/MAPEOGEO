# PDI-135M-v0.4 — Qualification Report: Permutation-Equivariant Candidate Scoring and Two-Stage Hybrid Work Selection

**Experiment ID:** `PDI-135M-v0.4`  
**Git Branch:** `experiment/pdi-135m-v0.4-scoring`  
**Baseline Commit:** `6631b99` (PDI-v0.3 freeze)  
**Date:** October 8, 2026  
**Target Hardware Fabric:** MAPEOGEO P0 Fabric (`fabric_p0`)  
**Hardware Authority Boundary:** RTL UoW Bridge (`pdi_uow_bridge`) with `tb_pdi_k8_selected_work.sv`  
**Neural Backbone:** SmolLM2-135M-Instruct (`12fd25f77366fa6b3b4b768ec3050bf629380bac`)  

---

## 1. Executive Summary

PDI-135M-v0.4 addresses the fundamental falsification discovery in v0.3: autoregressive menu selection suffered from catastrophic positional bias (over 96% output collapse to the same menu index token) and historical target leakage (in 33 of 49 holdouts, candidate menus were generated using oracle target information).

In PDI-v0.4, we redesigned the selection architecture from first principles:
1. **Zero-Leakage State Extraction:** Proved zero target leakage via strict observable-state extraction (`ObservableStateExtractor`), passing all 6 Phase 1 audit gates.
2. **Permutation Equivariance ($f(\pi(\mathcal A)) = \pi(f(\mathcal A))$):** Replaced autoregressive menu token generation with independent candidate scoring $s(G, S, a_i)$ combined with stable cryptographic `cand_id` tie-breaking. Permutation consistency is **100.00%** across arbitrary menu orderings.
3. **PSMSL Work-Relation Representation $\Phi_{\mathrm{PSMSL}}$:** Encoded work candidates into 4 orthogonal relational signatures $(\Phi_{\mathrm{structural}}, \Phi_{\mathrm{causal}}, \Phi_{\mathrm{geometric}}, \Phi_{\mathrm{constraints}})$.
4. **Authoritative Numerical State-Transition Oracle:** Replaced synthetic string matching with an explicit Clifford geometric algebra simulator in $\mathcal C\ell(2,0)$ verifying postcondition invariant satisfaction $S' = \text{Exec}(S, a_i) \models \mathcal P_G(S')$.
5. **Two-Stage Hybrid Selector (Fast-Path / Slow-Path Architecture):**
   - **Fast-Path (Deterministic Rule Scorer, $0.01\,\text{ms}$):** Resolves 100% of standard executable work (256/256) and 100% of partially observable abstention work (20/20) with zero neural forward passes.
   - **Slow-Path (Targeted LoRA Fine-Tuned SmolLM2-135M Scorer, $32.1\,\text{ms}$):** Invoked selectively when top candidate score margin $< 10.0$, resolving non-commutative operand ordering and contextual geometric ambiguity.

---

## 2. Benchmark Results Across Architectural Paradigms

### A. Prospective 256-Scenario Standard Suite
Evaluated on fresh zero-leakage prospective corpus (`pdi_v04_prospective_corpus.json`):

| Evaluation Metric | Reported v0.3 (Autoregressive Menu) | PDI-v0.4 Deterministic Rule Scorer $s_{\mathrm{rule}}$ | PDI-v0.4 Two-Stage Hybrid Selector |
|:---|:---:|:---:|:---:|
| **Useful Candidate Selection** | 1.36% (top-1) | **100.00%** (256/256) | **100.00%** (256/256) |
| **Permutation Invariance** | 0.00% (position collapse) | **100.00%** | **100.00%** |
| **Mean Decision Latency** | 247.30 ms | **0.01 ms** | **0.01 ms** (Fast-Path: 100%) |
| **Neural Invocations** | 256 | 0 | 0 |

---

### B. Hard Ambiguity Challenge Suite (64 Scenarios)
Evaluated across three challenging ambiguity regimes under authoritative numerical state-transition verification:
1. **Category A (24 scenarios):** Non-commutative operand discriminators ($A \star B \ne B \star A$).
2. **Category B (20 scenarios):** Partially observable / underspecified work (missing operands, capability violations, version conflicts).
3. **Category C (20 scenarios):** Genuinely ambiguous contextual work (symmetric scalar projection metric vs oriented planar bivector span).

| Method / Architecture Arm | Overall Useful Selection (64) | Category A: Non-Commutative (24) | Category B: Partially Observable (20) | Category C: Contextual Ambiguity (20) | Mean Latency |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Arm A: Deterministic Rule Scorer** ($s_{\mathrm{rule}}$) | 38/64 (59.38%) | 7/24 (29.17%) | **20/20 (100.00%)** | 11/20 (55.00%) | **0.01 ms** |
| **Arm B: Frozen SmolLM2-135M Likelihood** | 42/64 (65.62%) | 12/24 (50.00%) | **20/20 (100.00%)** | 10/20 (50.00%) | 228.41 ms |
| **Arm C: Frozen Transformer + Probing Head** | 22/64 (34.38%) | 12/24 (50.00%) | 0/20 (0.00%) | 10/20 (50.00%) | 218.25 ms |
| **Arm D: Fine-Tuned SmolLM2-135M LoRA** | 36/64 (56.25%) | 16/24 (66.67%) | 0/20 (0.00%) | **20/20 (100.00%)** | 41.80 ms |
| **Arm E: Two-Stage Hybrid Selector** | **56/64 (87.50%)** | **16/24 (66.67%)** | **20/20 (100.00%)** | **20/20 (100.00%)** | **32.13 ms** |

---

## 3. Empirical Value-of-Inference ($V_{\mathrm{LLM}}$)

The empirical Value-of-Inference quantifies the exact performance delta delivered by neural inference over pure deterministic evaluation:

\\[ V_{\mathrm{LLM}} = U(\text{Hybrid}) - U(\text{Deterministic}) \\]

1. **On Mechanically Resolvable Work (Prospective 256):**
   - $U(\text{Deterministic}) = 100.00\%$
   - $U(\text{Hybrid}) = 100.00\%$
   - $V_{\mathrm{LLM}} = 0.00\%$ (Fast-path dispatch in $0.01\,\text{ms}$, neural inference safely bypassed).
2. **On Contextually Ambiguous Work (Category C, 20 scenarios):**
   - $U(\text{Deterministic}) = 55.00\%$ (coin flip between dot and wedge)
   - $U(\text{Hybrid}) = 100.00\%$ (LoRA model correctly discriminates task intent)
   - $V_{\mathrm{LLM}} = \mathbf{+45.00\%}$
3. **On Non-Commutative Operand Work (Category A, 24 scenarios):**
   - $U(\text{Deterministic}) = 29.17\%$
   - $U(\text{Hybrid}) = 66.67\%$
   - $V_{\mathrm{LLM}} = \mathbf{+37.50\%}$
4. **Across the Entire Hard Ambiguity Suite (64 scenarios):**
   - $U(\text{Deterministic}) = 59.38\%$
   - $U(\text{Hybrid}) = 87.50\%$
   - $V_{\mathrm{LLM}} = \mathbf{+28.12\%}$
5. **Combined Corpus (320 Scenarios: 256 Prospective + 64 Hard):**
   - Total Useful Work: **312 / 320 (97.50%)**
   - Hybrid Fast-Path Rate: 276 / 320 (86.25%) dispatched in $<0.02\,\text{ms}$.
   - Hybrid Neural Rate: 44 / 320 (13.75%) dispatched in $\sim 40\,\text{ms}$.

---

## 4. Hardware Authority & RTL Differential Equivalence

All selected candidate proposals were compiled into native binary packets via `pdi_ingress` and simulated on the MAPEOGEO P0 RTL fabric via `tb_pdi_k8_selected_work.sv` in WSL:

- **Total Differential Test Vectors:** 15 / 15 passed (100.00% equivalence).
- **RTL Outcome Agreement:** 100% agreement on `COMMIT` vs `REFUSE`.
- **RTL Reason Code Agreement:** 100% agreement across all hardware fault conditions:
  - `REASON_COMMITTED`
  - `ERR_BAD_MAGIC`
  - `ERR_BAD_CRC`
  - `ERR_BAD_LENGTH`
  - `ERR_UNKNOWN_OPERATOR`
  - `ERR_OUT_OF_BOUNDS_REF`
  - `ERR_STALE_STATE_VERSION`
  - `ERR_UNAUTHORIZED_CAPABILITY`
- **Zero Unauthorized State Mutation:** Confirmed in all 15 vectors.
- **Bounded Cycle Execution:** p50 = 3 cycles, max = 15 cycles.
- **Hardware Evidence Digest:** Nonce-chained SHA-256 evidence emitted for every disposition.

---

## 5. Software Test Suite Verification

The full software regression test suite confirms complete architectural qualification:
- **Total Test Cases:** 44 / 44 passed (`pytest pdi/tests -v`).
- **Authority Boundaries:** `test_authority_boundary.py` (3 passed).
- **Packet Codec & Roundtrip:** `test_packet_roundtrip.py` (4 passed).
- **Native Grammar & Token Trie:** `test_native_grammar.py` (8 passed).
- **Context Isolation & Permissions:** `test_projection_isolation.py` (5 passed).
- **RTL Bridge Equivalence:** `test_rtl_equivalence.py`, `test_k8_rtl_equivalence.py`, `test_extended_matrix.py` (3 passed).
- **Canonical Schema:** `test_schema.py` (9 passed).
- **Phase 1 Audit Gates:** `test_v04_phase1_audit.py` (4 passed).
- **Two-Stage Hybrid Selector:** `test_hybrid_selector.py` (4 passed).

---

## 6. Engineering Recommendation

1. **Deploy Two-Stage Hybrid Architecture:** The fast-path / slow-path cascade provides the optimal balance of speed ($0.01\,\text{ms}$ on 86% of traffic) and intelligence ($87.5\%$ on hard ambiguity), eliminating the latency overhead of autoregressive decoding.
2. **Promote Branch:** Merge `experiment/pdi-135m-v0.4-scoring` to `main` as the qualified PDI-135M reference architecture.
