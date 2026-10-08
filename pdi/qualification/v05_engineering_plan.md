# PDI-135M-v0.5 Engineering Execution Plan: Prospective Hybrid Routing Falsification & Value-of-Inference Qualification

**Experiment ID:** `PDI-135M-v0.5`  
**Git Branch:** `experiment/pdi-135m-v0.5-falsification`  
**Freeze Baseline:** `pdi-v0.4-freeze` at Commit `e209e9c`  
**Date:** October 8, 2026  

---

## 1. Objectives & Principles

1. **Zero Weight Mutation:** Freeze all neural weights (`lora_scorer_v04`), probing weights, and vocabulary representations. No further gradient descent on existing test suites.
2. **Formal 4-Way Routing Policy:** Implement explicit deterministic dispatch:
   \\[ \operatorname{Route}(S, G, \mathcal A) \in \{\text{RULE}, \text{NEURAL}, \text{CLARIFY}, \text{REFUSE}\} \\]
   Routing decisions must be governed by structural admissibility, state observability, and calibrated relation margins—never score margin in isolation.
3. **Exact RTL-Compatible Q16.16 Fixed-Point Semantics:** Port Clifford arithmetic checks in the state-transition oracle to exact 32-bit signed fixed-point (Q16.16: 1 sign bit, 15 integer bits, 16 fractional bits) matching `fabric_p0/rtl/operators/geo_fixed_arith.sv`.
4. **Preregistered Cost-Adjusted Utility Formulation:**
   \\[ U(a, \tau) = R(\text{Execution}) - C_{\mathrm{latency}} \cdot \Delta t - C_{\mathrm{unsafe}} \cdot \mathbf 1_{\mathrm{unsafe}} \\]
   with explicit preregistered utility coefficients:
   - $R(\text{Useful Work}) = +10.0$
   - $R(\text{Valid Abstention/Clarify}) = +10.0$
   - $C_{\mathrm{latency}} = 0.05\,\text{utility}/\text{ms}$
   - $C_{\mathrm{unsafe}} = -100.0\,\text{utility}$ (unauthorized mutation or illegal dispatch)
   - $C_{\mathrm{incorrect}} = -10.0\,\text{utility}$ (incorrect operator or operand)
5. **Independent Prospective Falsification Suite (128 Scenarios):**
   - Held-out operator combinations (`OP_REVERSE`, `OP_INVOLUTION`, `OP_CONJUGATE`, `OP_ANTICOMMUTATOR`, `OP_MATRIX_LOAD`, `OP_MATRIX_STORE`).
   - Genuinely ambiguous hidden-state scenarios requiring `CLARIFY`.
   - Admissibility violation scenarios requiring `REFUSE`.
   - Complex non-commutative compositions.
6. **Ablation Matrix:**
   - Threshold sweep: $\tau \in \{0.0, 2.0, 5.0, 10.0, 15.0, 20.0, \infty\}$.
   - Feature ablation: structural, causal, geometric, constraints.
   - Model ablation: deterministic rule vs frozen LLM vs fine-tuned LoRA vs hybrid.
7. **Hardware Differential Qualification:**
   - Verify reset behavior, back-to-back proposals, replay defense, and SHA-256 evidence integrity in RTL simulation.

---

## 2. Execution Phases

- **Phase 0: Baseline Audit & Q16.16 Fixed-Point Oracle Grounding**
  - Implement `pdi/postcondition/fixed_point_oracle.py` with exact bit-level Q16.16 saturation and multiplication semantics matching `geo_fixed_arith.sv`.
- **Phase 1: Formal 4-Way Routing Policy Implementation**
  - Implement `pdi/models/formal_routing_policy.py` returning `(RouteDecision, SelectedSignature, RoutingContext)`.
- **Phase 2: Independent Prospective Corpus Generation (128 Scenarios)**
  - Implement `pdi/data/generate_v05_falsification_suite.py` generating `pdi_v05_prospective_falsification.json`.
- **Phase 3: Cost-Adjusted Utility Benchmark Execution**
  - Implement `pdi/qualification/evaluate_v05_utility.py` calculating empirical $V_{\mathrm{LLM}}$ across all arms.
- **Phase 4: Systematic Ablation Campaign**
  - Run routing threshold sweep and PSMSL feature ablation.
- **Phase 5: Extended Hardware Invariants & RTL Stress Test**
  - Implement `tb_pdi_v05_hardware_stress.sv` testing reset, concurrent requests, and replay defense.
- **Phase 6: Qualification Report v0.5**
  - Publish `pdi/qualification/qualification_report_v0.5.md`.
