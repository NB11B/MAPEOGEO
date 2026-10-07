# Transformation Algebra: Primitive Characterization

## 1. The 20 Primitives

### P1: `P_IDENTIFY`
- **Delta (Δ)**: structural_modification
- **Invariant (I)**: measure
- **Witness (W)**: commutative_diagram
- **Scope (σ)**: EQUIVALENT_TO
- **Frequency**: 2603
- **Effective Domain Count**: 5.17
- **Properties**: Idempotent=True, HasInverse=False
- **Minimality Delta**: 0.0648

### P2: `P_QUOTIENT`
- **Delta (Δ)**: structural_modification
- **Invariant (I)**: metric
- **Witness (W)**: homotopy
- **Scope (σ)**: SAME_SEMANTICS
- **Frequency**: 1973
- **Effective Domain Count**: 4.36
- **Properties**: Idempotent=False, HasInverse=True
- **Minimality Delta**: 0.0422

### P3: `P_EMBED`
- **Delta (Δ)**: structural_modification
- **Invariant (I)**: cardinality
- **Witness (W)**: universal_property
- **Scope (σ)**: SCOPED_OVERLAP
- **Frequency**: 2297
- **Effective Domain Count**: 6.88
- **Properties**: Idempotent=False, HasInverse=False
- **Minimality Delta**: 0.1489

### P4: `P_RESTRICT`
- **Delta (Δ)**: structural_removal
- **Invariant (I)**: cardinality
- **Witness (W)**: isomorphism
- **Scope (σ)**: SAME_SEMANTICS
- **Frequency**: 4095
- **Effective Domain Count**: 2.48
- **Properties**: Idempotent=True, HasInverse=False
- **Minimality Delta**: 0.032

### P5: `P_EXTEND`
- **Delta (Δ)**: structural_addition
- **Invariant (I)**: cardinality
- **Witness (W)**: factorization
- **Scope (σ)**: SAME_SEMANTICS
- **Frequency**: 2199
- **Effective Domain Count**: 7.71
- **Properties**: Idempotent=False, HasInverse=False
- **Minimality Delta**: 0.086

### P6: `P_LIFT`
- **Delta (Δ)**: structural_removal
- **Invariant (I)**: metric
- **Witness (W)**: homotopy
- **Scope (σ)**: EQUIVALENT_TO
- **Frequency**: 4626
- **Effective Domain Count**: 5.39
- **Properties**: Idempotent=False, HasInverse=False
- **Minimality Delta**: 0.0721

### P7: `P_PROJECT`
- **Delta (Δ)**: structural_modification
- **Invariant (I)**: measure
- **Witness (W)**: factorization
- **Scope (σ)**: EQUIVALENT_TO
- **Frequency**: 2824
- **Effective Domain Count**: 3.53
- **Properties**: Idempotent=False, HasInverse=False
- **Minimality Delta**: 0.1471

### P8: `P_NORMALIZE`
- **Delta (Δ)**: structural_modification
- **Invariant (I)**: metric
- **Witness (W)**: isomorphism
- **Scope (σ)**: EQUIVALENT_TO
- **Frequency**: 4854
- **Effective Domain Count**: 6.43
- **Properties**: Idempotent=True, HasInverse=True
- **Minimality Delta**: 0.0101

### P9: `P_FACTOR`
- **Delta (Δ)**: structural_removal
- **Invariant (I)**: metric
- **Witness (W)**: bijection
- **Scope (σ)**: EQUIVALENT_TO
- **Frequency**: 1854
- **Effective Domain Count**: 6.55
- **Properties**: Idempotent=True, HasInverse=True
- **Minimality Delta**: 0.0985

### P10: `P_COMPLETE`
- **Delta (Δ)**: structural_modification
- **Invariant (I)**: measure
- **Witness (W)**: universal_property
- **Scope (σ)**: SAME_SEMANTICS
- **Frequency**: 4424
- **Effective Domain Count**: 2.89
- **Properties**: Idempotent=False, HasInverse=False
- **Minimality Delta**: 0.1236

### P11: `P_DUALIZE`
- **Delta (Δ)**: structural_modification
- **Invariant (I)**: topology
- **Witness (W)**: factorization
- **Scope (σ)**: EQUIVALENT_TO
- **Frequency**: 2809
- **Effective Domain Count**: 6.31
- **Properties**: Idempotent=False, HasInverse=False
- **Minimality Delta**: 0.0628

### P12: `P_INVERT`
- **Delta (Δ)**: structural_preservation
- **Invariant (I)**: algebraic_structure
- **Witness (W)**: factorization
- **Scope (σ)**: SAME_SEMANTICS
- **Frequency**: 4600
- **Effective Domain Count**: 7.51
- **Properties**: Idempotent=False, HasInverse=True
- **Minimality Delta**: 0.0239

### P13: `P_DEFORM`
- **Delta (Δ)**: structural_removal
- **Invariant (I)**: cardinality
- **Witness (W)**: universal_property
- **Scope (σ)**: SAME_SEMANTICS
- **Frequency**: 2454
- **Effective Domain Count**: 3.33
- **Properties**: Idempotent=False, HasInverse=False
- **Minimality Delta**: 0.1025

### P14: `P_EQUIVALENCE`
- **Delta (Δ)**: structural_removal
- **Invariant (I)**: metric
- **Witness (W)**: isomorphism
- **Scope (σ)**: SCOPED_OVERLAP
- **Frequency**: 1750
- **Effective Domain Count**: 7.41
- **Properties**: Idempotent=True, HasInverse=False
- **Minimality Delta**: 0.0416

### P15: `P_ADJOIN`
- **Delta (Δ)**: structural_removal
- **Invariant (I)**: cardinality
- **Witness (W)**: homotopy
- **Scope (σ)**: SAME_SEMANTICS
- **Frequency**: 3103
- **Effective Domain Count**: 5.93
- **Properties**: Idempotent=False, HasInverse=True
- **Minimality Delta**: 0.0837

### P16: `P_STRIP`
- **Delta (Δ)**: structural_modification
- **Invariant (I)**: algebraic_structure
- **Witness (W)**: homotopy
- **Scope (σ)**: EQUIVALENT_TO
- **Frequency**: 4375
- **Effective Domain Count**: 2.14
- **Properties**: Idempotent=False, HasInverse=False
- **Minimality Delta**: 0.1196

### P17: `P_ENRICH`
- **Delta (Δ)**: structural_modification
- **Invariant (I)**: cardinality
- **Witness (W)**: factorization
- **Scope (σ)**: SAME_SEMANTICS
- **Frequency**: 969
- **Effective Domain Count**: 5.63
- **Properties**: Idempotent=True, HasInverse=False
- **Minimality Delta**: 0.0994

### P18: `P_LOCALIZE`
- **Delta (Δ)**: structural_addition
- **Invariant (I)**: measure
- **Witness (W)**: bijection
- **Scope (σ)**: SAME_SEMANTICS
- **Frequency**: 3592
- **Effective Domain Count**: 5.74
- **Properties**: Idempotent=True, HasInverse=False
- **Minimality Delta**: 0.0714

### P19: `P_PULLBACK`
- **Delta (Δ)**: structural_addition
- **Invariant (I)**: measure
- **Witness (W)**: isomorphism
- **Scope (σ)**: SAME_SEMANTICS
- **Frequency**: 1895
- **Effective Domain Count**: 6.54
- **Properties**: Idempotent=False, HasInverse=False
- **Minimality Delta**: 0.1205

### P20: `P_PUSHOUT`
- **Delta (Δ)**: structural_removal
- **Invariant (I)**: algebraic_structure
- **Witness (W)**: universal_property
- **Scope (σ)**: EQUIVALENT_TO
- **Frequency**: 4612
- **Effective Domain Count**: 3.19
- **Properties**: Idempotent=True, HasInverse=True
- **Minimality Delta**: 0.0419

## 2. Composition Table (Sample)

| P1 \ P2 | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|
| P1 | FORBIDDEN | DEFINED | UNOBSERVED | FORBIDDEN | DEFINED |
| P2 | CONDITIONALLY DEFINED | DEFINED | CONDITIONALLY DEFINED | UNOBSERVED | CONDITIONALLY DEFINED |
| P3 | CONDITIONALLY DEFINED | CONDITIONALLY DEFINED | CONDITIONALLY DEFINED | DEFINED | UNOBSERVED |
| P4 | DEFINED | DEFINED | DEFINED | DEFINED | DEFINED |
| P5 | CONDITIONALLY DEFINED | CONDITIONALLY DEFINED | UNOBSERVED | DEFINED | CONDITIONALLY DEFINED |
