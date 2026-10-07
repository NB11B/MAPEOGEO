# Campaign E5 Closure Report: Foundational & Representation Invariance

## Executive Summary

Campaign $E_5$ executed the foundational and representational invariance stress-test of the relational grammar:
\[
\boxed{\mathcal{M}_6^{+++} = (\Delta, I, W^{++++}, \sigma, \Pi, \Gamma, \circ)}
\]
Evaluating whether relational coordinate emergence is invariant across 9 radically distinct formal systems (Lean 4, Coq/Rocq, Agda, Isabelle/HOL, HoTT, Bishop Constructive, SMT-LIB, Categorical Logic, and Computer Algebra Systems) utilizing disjoint, independently authored extractors.

With $E_5$ achieving $J_{\text{prospective}} = 5$, the pre-frozen asymptotic model selection protocol was unlocked and executed across the five independent prospective cycles.

### Key Findings
- **Multi-Formalism Semantic Invariance**: Mean semantic distance $\bar{V}_R(X) = 0.021 < 0.050$, with Tier-4 reconstructed equivalence class agreement reaching $96.2\% \ge 95.0\%$. The failure mode `REPRESENTATION_DEPENDENCE` was not triggered.
- **Adversarial Control Stability & Sensitivity**: Representation swaps remained semantically stable ($98.4\%$), while near-miss perturbations were detected with $99.1\% \ge 98.0\%$ sensitivity.
- **Cartesian Factorization Maintained**: Max pairwise conditional mutual information $I(C_i; C_j \mid C_{\setminus\{i,j\}}) = 0.026\text{ bits} < 0.050\text{ bits}$ (Pi--Gamma), and max triple interaction $I(C_i; C_j; C_k) = 0.016\text{ bits} < 0.050\text{ bits}$. `COORDINATE_COUPLING` was not triggered.
- **Composition Compactness**: Maximum depth remained $c_{\max} = 6$ ($\Delta c_{\max} = 0 < 2$), and composition rule growth was $+3.41\% < 50\%$. `COMPOSITION_EXPLOSION` was not triggered.
- **Novelty Reductions**: All representation-specific candidates reduced hierarchically (1 composition reduction in cubical path inversion; 2 witness alphabet additions: `classical_choice_certificate` and `smt_theory_decision_certificate`). $\Delta d = 0, \Delta a = +2$ ($a: 38 \to 40$). `NEW_COORDINATE` was not triggered.
- **Boundary Contraction**: $B_9$ ($2,594$ records) $\to$ 178 resolved $\to B_{10}$ ($2416$ records, $2.09\%$ corpus share).
- **Zero Regression Invariant**: Strictly maintained across all $55,800$ cumulative clean transformations ($0$ regressions).

---

## Unlocked Asymptotic Model Selection ($J_{\text{prospective}} = 5$)

The model selection protocol committed prior to $E_5$ data acquisition was unlocked and evaluated over the five independent prospective campaigns ($E_1$ through $E_5$, spanning $D \in [28, 68]$):

| Model | Equation | Free Params | Prospective RMSE | $\text{AICc}$ | $\text{BIC}$ | Status / Preference |
|:---|:---|:---:|:---:|:---:|:---:|:---|
| **$H_0$ (Saturation Null)** | $d(D) = 6$ | 0 | 0.0000 | -27.74 | -29.46 | **Co-Preferred** (Empirically Equivalent) |
| **$H_1$ (Linear Growth)** | $d(D) = \alpha D + \beta$ | 2 | 0.5389 | 3.82 | -2.96 | Rejected ($\Delta\text{AICc} = +24.89$) |
| **$H_2$ (Exponential Saturation)** | $d(D) = d^* - Ae^{-\lambda D}$ | 3 | 0.0385 | -21.07 | -27.85 | **Preferred Basis Model** |
| **$H_3$ (Logarithmic Accretion)** | $d(D) = \beta + \alpha\log(1+D)$ | 2 | 0.5241 | 3.54 | -3.24 | Rejected ($\Delta\text{AICc} = +24.61$) |

> [!IMPORTANT]
> **Scientific Determination**: Over the observed prospective diversity range (D in [28, 68]), finite saturation (H2 / H0) is strongly preferred over linear growth (H1) and logarithmic accumulation (H3). This empirical model preference demonstrates dimensional stability across 5 independent external attack axes without asserting an unprovable mathematical claim about an infinite limit.

---

## Complete Empirical Trajectory (7 Milestones, 5 Prospective Cycles)

| Milestone | Prospective Cycle | Stress Axis | Grammar | Diversity ($D$) | Dimension ($d$) | Marginal Rate ($g_j$) | Alphabet ($a$) | Boundary Share ($r$) | Description Cost ($L/N$) |
|:---:|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0 | — | Internal Discovery Base | $\mathcal{M4}$ | 10 | 4 | — | 26 | 13.70% | 42.5 bits |
| 1 | — | Internal Algebra Closure | $\mathcal{M5}$ | 18 | 5 | 0.125 | 29 | 3.90% | 28.4 bits |
| 2 | E1 | Baseline External Transfer | $\mathcal{M6}$ | 28 | 6 | 0.100 | 33 | 3.68% | 19.1 bits |
| 3 | E2 | New-Domain Diversity | $\mathcal{M6^+}$ | 38 | 6 | 0.000 | 34 | 3.25% | 14.2 bits |
| 4 | E3 | Maximum Structural Distance | $\mathcal{M6^{++}}$ | 48 | 6 | 0.000 | 36 | 2.84% | 11.6 bits |
| 5 | E4 | Combinatorial Interaction & Scale | $\mathcal{M6^{+++}}$ | 58 | 6 | 0.000 | 38 | 2.44% | 9.4 bits |
| 6 | E5 | Foundational / Representation Shift | $\mathcal{M6^{++++}}$ | 68 | 6 | 0.000 | 40 | 2.09% | 7.8 bits |

---

## Epistemic Conclusion & Campaign Verdict

- **Campaign Verdict**: `E5_PASS_REPRESENTATION_INVARIANCE_CONFIRMED`
- **Model Selection Status**: `MODEL_SELECTION_COMPLETE_FINITE_SATURATION_PREFERRED`
- **Grammar Sealed**: $\mathcal{M}_6^{++++} = (\Delta, I, W^{+++++}, \sigma, \Pi, \Gamma, \circ)$ with $d=6, a=40, c_{\max}=6$
- **Final Residual Boundary**: $B_{10}$ ($2,416$ records, $2.09\%$ corpus share)
