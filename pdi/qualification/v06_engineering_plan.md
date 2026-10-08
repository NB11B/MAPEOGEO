# PDI-135M-v0.6 — Engineering Specification: Economic Break-Even & Workload Generalization

**Program:** PDI-135M (Probabilistic-to-Deterministic Integration)  
**Experiment ID:** `PDI-135M-v0.6`  
**Baseline Freeze:** `pdi-v0.5.1-audit` at Commit `4735687`  
**Date:** October 8, 2026  
**Status:** Pre-Execution Engineering Plan  
**Target Hardware Fabric:** MAPEOGEO P0 Fabric (`fabric_p0`)  

---

## 1. Mission & Scientific Mandate

The PDI-135M-v0.5.1 Attribution Audit established that while 86.0% of the hybrid system's utility improvement originates from deterministic safety routing, SmolLM2-135M contributes a statistically significant isolated value-of-inference:
$$\Delta_{\mathrm{neural}\mid\mathrm{guard}} = +1.98\,\text{utility points} \quad (95\%\text{ CI: } [+0.35, +3.60])$$

However, this measurement was made under a fixed benchmark scenario mix where 56.2% of tasks triggered neural tiebreaking. In production, real-world workloads fluctuate dynamically between routine work (unambiguous math, illegal requests, incomplete inputs) and complex ambiguous work.

The mission of PDI-v0.6 is to **determine the economic break-even frontier of neural inference under workload shifts without any neural retraining**.

$$\boxed{ V_{\mathrm{net}}(p) = p \cdot \Delta U_{\mathrm{hard}} - C_{\mathrm{inference}}(p) }$$

---

## 2. Timing Protocol Resolution & Baseline Parameters

Following the formal timing protocol audit (`pdi_timing_protocol_benchmark.json`), the discrepancy between v0.5 (~22 ms) and v0.5.1 (~26 ms) is formally resolved:

| Execution Path | Proportion in v0.5 Suite | Latency Metric | Synchronized Measurement |
|:---|:---:|:---:|:---:|
| **Gating (REFUSE / CLARIFY)** | 37.5% | Mean / p50 | **0.003 ms** (sub-microsecond) |
| **Deterministic Rule Fast-Path** | 6.2% | Mean / p50 | **0.020 ms** (20 $\mu\text{s}$) |
| **SmolLM2-135M Slow-Path (8 Cands)** | 56.2% | Mean / p50 / p95 | **34.23 ms / 30.47 ms / 56.94 ms** |
| **Blended Workload Latency** | 100.0% | Mean / p50 / p95 | **19.26 ms / 29.37 ms / 54.93 ms** |

*Key Takeaway:* The hybrid router bypasses neural inference on 43.8% of inputs at zero measurable latency (<0.02 ms). When neural deliberation is required, the 8-candidate batched forward pass on the RTX 5070 executes at a median of 30.47 ms.

---

## 3. Mathematical Model of Economic Break-Even

Let $p \in [0.0, 1.0]$ denote the prevalence of **hard / ambiguous requests** in the workload stream that cannot be unambiguously resolved by deterministic rules ($\Delta s < \tau$).

The remaining fraction $(1 - p)$ consists of **routine / governed requests** (unambiguous rules $\Delta s \ge \tau$, inadmissible security violations, or missing state).

### Net Utility Formulation

$$U_{\mathrm{guarded\_rules}}(p) = p \cdot U_{\mathrm{rule}\mid\mathrm{hard}} + (1 - p) \cdot U_{\mathrm{governed}\mid\mathrm{routine}}$$

$$U_{\mathrm{hybrid}}(p) = p \cdot \left( U_{\mathrm{neural}\mid\mathrm{hard}} - C_{\mathrm{lat}} \cdot \bar{L}_{\mathrm{neural}} \right) + (1 - p) \cdot \left( U_{\mathrm{governed}\mid\mathrm{routine}} - C_{\mathrm{lat}} \cdot \bar{L}_{\mathrm{fast}} \right)$$

Taking the difference yields the net value of maintaining the neural inference engine:

$$V_{\mathrm{net}}(p) = p \cdot \left( \Delta U_{\mathrm{hard}} - C_{\mathrm{lat}} \cdot \bar{L}_{\mathrm{neural}} \right) - (1 - p) \cdot \left( C_{\mathrm{lat}} \cdot \bar{L}_{\mathrm{fast}} \right)$$

Since $\bar{L}_{\mathrm{fast}} \approx 0.01\,\text{ms}$, the routine overhead term is negligible ($< 0.0005$ points):

$$\boxed{ V_{\mathrm{net}}(p) \approx p \cdot \left[ \Delta U_{\mathrm{hard}} - C_{\mathrm{lat}} \cdot \bar{L}_{\mathrm{neural}} \right] }$$

### Break-Even Condition

For the neural engine to deliver positive net value:
1. **Marginal Utility Surplus:** The learned discrimination surplus must exceed its own inference cost:
   $$\Delta U_{\mathrm{hard}} > C_{\mathrm{lat}} \cdot \bar{L}_{\mathrm{neural}} \approx 0.05 \times 34.23 = 1.71\,\text{utility points}$$
2. **Break-Even Workload Threshold ($p^*$):**
   If an auxiliary fixed infrastructure/standby cost $C_{\mathrm{fixed}}$ is present (e.g. host DRAM footprint or GPU idle power amortized over $N$ requests):
   $$p^* = \frac{C_{\mathrm{fixed}} / N}{\Delta U_{\mathrm{hard}} - C_{\mathrm{lat}} \cdot \bar{L}_{\mathrm{neural}}}$$

---

## 4. Phase-by-Phase Execution Plan

### Phase 1: Workload Mixture Sweeps ($p \in [0.0, 1.0]$)
Simulate dynamic operational environments by sweeping $p$ across 11 discrete mixture points:
- **Regime I: Routine Production ($p = 0.00 \to 0.10$):** Heavy routine data processing; rare ambiguous requests.
- **Regime II: Balanced Mixed Workload ($p = 0.20 \to 0.50$):** Standard interactive CAD / geometric exploration.
- **Regime III: High-Ambiguity Exploration ($p = 0.60 \to 1.00$):** Novel operator exploration and non-commutative geometry.

### Phase 2: Independent Generalization & Operator Transfer
Construct an independently authored evaluation suite (64 scenarios) evaluating:
1. **Multi-Operator Chains:** Sequential multivector transformations (e.g., $(A \wedge B) \cdot C$).
2. **Out-of-Distribution Rotors:** Conformal rotors and non-standard geometric algebra signatures ($Cl(3,0)$ and $Cl(1,3)$).
3. **Paraphrased Natural Language Goals:** Prompt templates authored independently of training templates.

### Phase 3: Cost-Ratio Sensitivity Matrix
Map the break-even boundaries across varying utility parameters:
- Error penalty sweep: $C_{\mathrm{unsafe}} \in [-50, -100, -250, -500]$
- Latency penalty sweep: $C_{\mathrm{latency}} \in [0.01, 0.05, 0.10, 0.20]\,\text{pts}/\text{ms}$
- Abstention reward sweep: $R_{\mathrm{clarify}} \in [0.0, 5.0, 10.0]$

---

## 5. Deliverables & Acceptance Criteria

1. `pdi/qualification/evaluate_v06_breakeven.py`: Execution engine for mixture sweeps and sensitivity matrices.
2. `pdi/qualification/pdi_v06_breakeven_benchmark.json`: Raw empirical data across all mixtures and cost sweeps.
3. `pdi/qualification/qualification_report_v0.6.md`: Formal qualification report documenting $p^*$, transfer results, and the production deployment boundary.
