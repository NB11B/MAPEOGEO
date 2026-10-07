# MAPEOGEO Residual Factorization Campaign Report

## Executive Summary

- **Total Qualified Residual Population Tested**: 11,340
- **Partition**: Discovery 60% (6,804), Sealed Holdout 40% (4,536)
- **Final Triage**: 
  - `DEPTH`: 78 (0.7%)
  - `COMPOSITION`: 4,635 (40.9%)
  - `NEW_COORDINATE (C5: Polarity)`: 3,409 (30.1%)
  - `ONTOLOGICAL_BOUNDARY / UNRESOLVED`: 3,218 (28.4%)

**Core Outcome**: Candidate C5 (Variance Polarity) officially accepted. C6 rejected by stopping criterion. Boundary mapped.

## 1. Depth Control vs Coordinate Deficiency (0.2% k=4 Collisions)

- **Total k=4 Collisions Audited**: 90
- **Resolved at k=5**: 62
- **Resolved at k=6**: 16
- **Depth Resolution Rate**: 86.7%
- **Persistent Collisions (k >= 6)**: 12 (13.33%)

> **Inference**: Over 86% of state collisions at k=4 are radius-limited (`DEPTH`) rather than ontology-limited.

## 2. Compositional Audit

- **Total Audited Across Mismatch & Inversion Failures**: 11,250
- **Factored into Existing Frozen Primitives (P_i o P_j)**: 4,635 (41.2%)
- **Unfactorable Residuals**: 6,615

> **Inference**: Over 41% of apparent transformation anomalies decompose into words over the existing alphabet.

## 3. Coordinate Discovery & Information-Theoretic Audit

### Candidate `variance_polarity`
- H(R | Frozen M4): 2.5850 bits
- H(R | Frozen M4 + Candidate): 1.0000 bits
- Marginal Mutual Information vs M4: **1.5850 bits**
- Marginal Relative Entropy Reduction: **61.3%**

### Candidate `coherence_level`
- H(R | Frozen M4): 2.5850 bits
- H(R | Frozen M4 + Candidate): 2.0849 bits
- Marginal Mutual Information vs M4: **0.5001 bits**
- Marginal Relative Entropy Reduction: **19.3%**

## 4. Strict Preregistered Acceptance Adjudication (Candidate C5: Variance Polarity)

**Target Candidate**: `variance_polarity`
**Final Adjudication**: `ACCEPTED_C5`

| Gate | Requirement | Observed Metric | Status |
|---|---|---|---|
| G1: Entropy Reduction | >= 20.0% | 61.3% | PASS |
| G2: Cross-Domain Breadth | >= 4 domains | 8 domains | PASS |
| G3: Multi-Projection | >= 2 projections | 3 projections | PASS |
| G4: Shuffled Controls | Shuffled MI <= 0.02 | 0.0084 bits | PASS |
| G5: Sealed Holdout | Retention >= 85.0% | 96.2% | PASS |
| G6: Semantic Safety | 0 false promotions | 0 | PASS |
| G7: Depth Independence | Persistent at k>=5 | True | PASS |
| G8: Structural Meaning | Validated work | Variance / Polarity of structural transport (Covar... | PASS |

## 5. Candidate C6 (Coherence Level): Marginal vs. Conditional Resolution

A critical numerical distinction separates C6's behavior across baselines:
- **Marginal Entropy Reduction against M4**: **19.3%** ($\Delta H(C_6 \mid \mathcal{M}_4) = 0.5001$ bits). While close to the 20% discovery gate, it exhibited severe collinearity with variance.
- **Conditional Entropy Reduction against M5**: **4.8%** ($\Delta H(C_6 \mid \mathcal{M}_5) = 0.048$ bits). Once Variance Polarity $\Pi$ is conditioned out, coherence level provides negligible cross-domain information.
- **Conclusion**: C6 is firmly rejected. The stopping rule $\Delta H_R(C_{n+1}) \approx 0$ prevents overfitting to homotopical exceptions.

## 6. Sealing M5 and the B5 Explanatory Boundary

The transformation grammar is permanently sealed as:
$$\boxed{\mathcal{M}_5 = (\Delta, I, W, \sigma, \Pi, \circ)}$$

The 3,218 unresolved instances (representing **3.9% of the qualified corpus** and 28.4% of the residual mass) are sealed into artifact `B5_explanatory_boundary.jsonl`.

### Future Admission Policy (The Prospective Growth Loop)
No further coordinate $C_6'$ may be added by post-hoc fitting. Any proposed growth to $\mathcal{M}_6$ must arise from **independent new mathematics** and must **prospectively explain structure within the frozen $B_5$ boundary** without regressing $\mathcal{M}_5$ accuracy.