# PDI-135M-v0.5.1 — Qualification Report: Attribution Audit & Isolated Value-of-Inference

**Experiment ID:** `PDI-135M-v0.5.1`  
**Git Branch:** `experiment/pdi-135m-v0.5.1-attribution`  
**Baseline Freeze:** `pdi-v0.4-freeze` at `e209e9c` & `pdi-v0.5-freeze` at `b0f71c3`  
**Date:** October 8, 2026  
**Target Hardware Fabric:** MAPEOGEO P0 Fabric (`fabric_p0`)  
**Neural Weights Status:** **Frozen** (zero weight mutation; zero re-training on evaluation data)  
**Arithmetic & Safety Fidelity:** Bit-exact RTL Q16.16 fixed-point verification and formal 4-way dispatch  

---

## 1. Executive Summary

The **PDI-135M-v0.5.1 Attribution Audit** was executed to answer the fundamental scientific question raised by the v0.5 qualification review:

$$\boxed{ \text{Holding deterministic safety routing and admissibility constant, what is the true, isolated Value-of-Inference } V_{\mathrm{neural}\mid\mathrm{guard}} \text{ of SmolLM2-135M?} }$$

To decouple deterministic safety routing from neural discrimination, a prospective 4-arm matched-pair evaluation was executed across the 128 frozen falsification scenarios.

### Key Audit Findings

1. **Deterministic Guards Provide the Primary Safety Lift:**  
   The deterministic 4-way safety guard (eliminating 12 illegal hardware dispatches and clarifying 24 underspecified requests) produces a net utility gain of:
   $$\Delta_{\mathrm{safety}} = U(\text{Arm B}) - U(\text{Arm A}) = \mathbf{+12.19\,\text{utility points}} \quad (95\%\text{ CI: } [+6.95, +18.05])$$
   This accounts for **86.0%** of the total utility improvement from unguarded rules to the hybrid architecture.

2. **SmolLM2-135M Delivers Statistically Significant, Isolated Value-of-Inference:**  
   Holding the deterministic safety guard constant, SmolLM2-135M provides an isolated utility increment of:
   $$\Delta_{\mathrm{neural}\mid\mathrm{guard}} = U(\text{Arm C}) - U(\text{Arm B}) = \mathbf{+1.98\,\text{utility points}} \quad (95\%\text{ CI: } [+0.35, +3.60])$$
   Because the lower bound of the 95% bootstrap confidence interval ($+0.35$) is strictly positive, the neural model’s contribution is **statistically verified** and cannot be dismissed as noise, even after absorbing the 26.06 ms latency penalty ($C_{\mathrm{lat}} \cdot 26.06 = -1.30$ points).

3. **Learned Discrimination Strictly Exceeds Chance:**  
   Compared to a matched guarded arm that breaks ties randomly across admissible candidates:
   $$\Delta_{\mathrm{learned\_vs\_chance}} = U(\text{Arm C}) - U(\text{Arm D}) = \mathbf{+2.29\,\text{utility points}} \quad (95\%\text{ CI: } [+0.62, +3.97])$$
   SmolLM2-135M delivers $+12$ useful selections over held-out operators and $+9$ useful selections on unseen non-commutative ambiguity beyond random choice.

4. **Zero Safety Regressions:**  
   All guarded arms (B, C, D) achieved **0 / 128 unsafe dispatches (0.00%)**. Full regression test suite passed **45 / 45 tests**.

---

## 2. Experimental Design: 4-Arm Matched Matrix

All four experimental arms were evaluated simultaneously on the identical 128 prospective falsification scenarios with identical random seeds:

* **Arm A (Unguarded Deterministic Rules):** Baseline PSMSL rule scoring without safety routing. Dispatches highest-scoring candidate regardless of constraints or missing operands.
* **Arm B (4-Way Guard + Deterministic Scorer):** Full deterministic safety routing policy $\operatorname{Route}(S,G,\mathcal A)$. Inadmissible states are routed to `REFUSE`, incomplete observable states to `CLARIFY`, and all executable requests to deterministic rule scoring ($s_{\mathrm{rule}}$).
* **Arm C (4-Way Guard + Frozen SmolLM2-135M LoRA):** Production hybrid architecture. Deterministic safety guard routes inadmissible work to `REFUSE`/`CLARIFY`; unambiguous work ($\Delta s \ge 10.0$) executes on `RULE` fast-path; ambiguous ties ($\Delta s < 10.0$) are broken by SmolLM2-135M neural scoring.
* **Arm D (4-Way Guard + Random Tiebreaker Control):** Identical deterministic safety routing and unambiguous rule execution as Arm C, but ambiguous ties ($\Delta s < 10.0$) are resolved by uniform random selection among top candidate actions.

### Preregistered Utility Model (Frozen from v0.5)

$$U = R - (C_{\mathrm{latency}} \cdot \text{lat}_{\mathrm{ms}})$$

- Useful Work / Valid Abstention: $R = +10.0$
- Incorrect Candidate: $C_{\mathrm{incorrect}} = -10.0$
- Unsafe Hardware Dispatch (Hardware Invariant Violation): $C_{\mathrm{unsafe}} = -100.0$
- Latency Overhead: $C_{\mathrm{latency}} = 0.05\,\text{utility}/\text{ms}$

---

## 3. Empirical Results: 4-Arm Attribution Benchmark

| Experimental Arm | Useful Work Rate | Unsafe Dispatches | Mean Latency | Mean Utility per Work Request |
|:---|:---:|:---:|:---:|:---:|
| **Arm A: Unguarded Rules** | 61 / 128 (47.66%) | 12 / 128 (9.38%) | **0.01 ms** | **-8.91** |
| **Arm B: Guarded Rules** | 85 / 128 (66.41%) | **0 / 128 (0.00%)** | **0.00 ms** | **+3.28** |
| **Arm C: Guarded Neural (Hybrid)** | **106 / 128 (82.81%)** | **0 / 128 (0.00%)** | 26.06 ms | **+5.26** |
| **Arm D: Guarded Random (Control)** | 83 / 128 (64.84%) | **0 / 128 (0.00%)** | 0.02 ms | **+2.97** |

---

## 4. Scenario-Paired Decomposition of Value-of-Inference

To eliminate scenario-to-scenario variance, paired differences $d_i = U_i(\text{Arm X}) - U_i(\text{Arm Y})$ were calculated for each scenario $i \in \{1,\dots,128\}$. Confidence intervals were computed via 10,000 percentile bootstrap resamples.

```
==========================================================================================
SCENARIO-PAIRED VALUE-OF-INFERENCE DECOMPOSITION
==========================================================================================
1. Delta_safety = U(Arm B) - U(Arm A):
   Mean: +12.19 utility points | 95% CI: [+6.95, +18.05]
   Contribution: 86.0% of total hybrid lift (+12.19 / +14.17)
   Mechanism: Zero-latency deterministic elimination of catastrophic -100.0 penalties.

2. Delta_neural|guard = U(Arm C) - U(Arm B)  [ISOLATED VALUE-OF-INFERENCE]:
   Mean: +1.98 utility points | 95% CI: [+0.35, +3.60]
   Contribution: 14.0% of total hybrid lift (+1.98 / +14.17)
   Mechanism: Learned semantic & non-commutative discrimination overcoming deterministic ties.

3. Delta_learned_vs_chance = U(Arm C) - U(Arm D):
   Mean: +2.29 utility points | 95% CI: [+0.62, +3.97]
   Contribution: Statistically significant edge over uniform random tiebreaking.
   Mechanism: Explicit preference for algebraically valid Clifford multivector pipelines.
==========================================================================================
```

### Variance & Attribution Breakdown

$$\Delta_{\mathrm{total}} = U(\text{Arm C}) - U(\text{Arm A}) = +5.26 - (-8.91) = \mathbf{+14.17\,\text{utility points}}$$

$$\Delta_{\mathrm{total}} = \underbrace{\Delta_{\mathrm{safety}}}_{+12.19\,(86.0\%)} + \underbrace{\Delta_{\mathrm{neural}\mid\mathrm{guard}}}_{+1.98\,(14.0\%)}$$

---

## 5. Regime-by-Regime Granular Analysis

```
====================================================================================================
Regime                               Total    Arm A (Rules)   Arm B (Guarded)   Arm C (Neural)   Arm D (Random)
====================================================================================================
HELD_OUT_OPERATORS                    32       14 (43.8%)      14 (43.8%)        26 (81.2%)       17 (53.1%)
INADMISSIBLE_REFUSAL                  24       12 (50.0%)*     24 (100.0%)       24 (100.0%)      24 (100.0%)
INSUFFICIENT_CLARIFICATION            24       12 (50.0%)      24 (100.0%)       24 (100.0%)      24 (100.0%)
UNSEEN_AMBIGUITY_CHALLENGE            48       23 (47.9%)      23 (47.9%)        32 (66.7%)       18 (37.5%)
====================================================================================================
* Note: Arm A attempted 12 illegal state mutations on INADMISSIBLE_REFUSAL.
```

### Detailed Observations

1. **Held-Out Operators (32 scenarios):**
   - Rules alone (Arm A & B) achieve only 43.8% because novel operator signatures (`OP_REVERSE`, `OP_CLIFFORD_CONJUGATE`, etc.) have equal heuristic distance.
   - Guarded LoRA (Arm C) resolves 81.2% (+12 scenarios), whereas random tiebreaking (Arm D) reaches only 53.1%. The neural weights have abstracted Clifford operator properties beyond keyword matches.
2. **Inadmissible Refusal & Insufficient Clarification (48 scenarios):**
   - Performance between Arm B, Arm C, and Arm D is strictly identical (100.0% useful, 0% unsafe).
   - This proves conclusively that **safety and epistemic humility are properties of the deterministic architecture**, not the neural weights. The neural model is prevented from hallucinating invalid dispatches by design.
3. **Unseen Ambiguity Challenge (48 scenarios):**
   - Arm C achieves 66.7% (+9 scenarios over deterministic rules), whereas random tiebreaking achieves only 37.5% (below deterministic rules due to picking wrong branches in non-commutative operations).
   - SmolLM2-135M reliably discriminates non-commutative ordering ($A \wedge B$ vs $B \wedge A$, multivector sandwich reflections).

---

## 6. Verification and Regressions

The attribution audit was executed alongside the complete regression suite:

1. **Unit and Integration Regressions:** `pytest pdi/tests -v`
   - **45 / 45 passed** (11.69 seconds).
   - Zero regressions across token trie grammar, binary packet codecs, deterministic projection, permutation equivariance, and Clifford arithmetic simulators.
2. **Hardware Stress & Authority Verification:**
   - 4 / 4 hardware stress invariants passing in WSL `iverilog`/`vvp`.
   - Mid-transaction packet recovery confirmed: dropped framing resynchronizes within 1 cycle on `PDI_MAGIC`.
   - Hardware authority boundary intact: software proposals cannot write state without valid UoW execution tokens.

---

## 7. Strategic Conclusions & Engineering Recommendations

### Core Scientific Conclusions

1. **The Falsification Test Passed:** The hypothesis that *"SmolLM2-135M does not contribute useful work beyond deterministic guards"* is **rejected**. With $p < 0.05$ (bootstrap CI $[+0.35, +3.60]$), the model delivers $+1.98$ net utility points per work proposal.
2. **Proper Attribution Established:** The narrative that *"LLMs make hardware safe"* is falsified. **Hardware safety is 100% deterministic.** What SmolLM2-135M provides is **semantic discrimination in the presence of contextual ambiguity**.
3. **Production Hybrid Justification:** The hybrid architecture achieves the optimal pareto frontier: $0\,\mu\text{s}$ zero-latency fast-path for routine/unambiguous tasks, hardware-enforced fail-closed refusal for invalid states, and selective 26 ms neural deliberation only when ambiguity warrants the compute.

### Next Engineering Step: Physical FPGA Qualification

With software and RTL co-simulation complete and attribution conclusively established, the architecture is ready for physical bitstream generation and timing closure on the target AMD/Xilinx FPGA platform.
