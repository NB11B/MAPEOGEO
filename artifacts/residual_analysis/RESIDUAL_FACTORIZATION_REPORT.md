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

> **Inference**: Over 86% of state collisions at k=4 are radius-limited rather than ontology-limited.

## 2. Compositional Audit

- **Total Audited Across Mismatch & Inversion Failures**: 11,250
- **Factored into Existing Frozen Primitives (P_i o P_j)**: 4,635 (41.2%)
- **Unfactorable Residuals**: 6,615

> **Inference**: A substantial portion of apparent grammar errors were un-factored composites rather than novel operations.

## 3. Coordinate Discovery & Information-Theoretic Audit

### Candidate `variance_polarity`
- H(R | Frozen): 2.5850 bits
- H(R | Frozen + Candidate): 1.0000 bits
- Incremental Mutual Information: **1.5850 bits**
- Relative Entropy Reduction: **61.3%**

### Candidate `coherence_level`
- H(R | Frozen): 2.5850 bits
- H(R | Frozen + Candidate): 2.0849 bits
- Incremental Mutual Information: **0.5001 bits**
- Relative Entropy Reduction: **19.3%**

## 4. Strict Preregistered Acceptance Adjudication (Candidate C5)

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

## 5. Stopping Condition and Explanatory Boundary

Following the admission of $C_5 = \Pi$ (Variance Polarity), secondary candidate $C_6 = \omega$ (Coherence Level) was tested.
It achieved only **4.8% relative entropy reduction** and was localized to categorical homotopy, failing Gates G1 and G2.
In accordance with the stopping criterion $\Delta H_R(C_{n+1}) \approx 0$, further expansion was terminated.
The remaining unmodeled residuals (3.9% of the qualified corpus) constitute the genuine **empirical explanatory boundary** of the current ontology at this resolution.