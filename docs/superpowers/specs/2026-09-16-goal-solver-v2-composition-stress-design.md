# Goal Solver V2 — Composition Stress and Cross-Representation Bridge Design

> **Historical V2 protocol — superseded for current v0.20.** Support and
> macro-preservation statements below are scoped to the frozen V2 implementation
> and evidence. Current v0.20 disables runtime macro execution and must be judged
> from its own freshly regenerated report.
>
> **Current disposition: `NOT_VALID_UNDER_CURRENT_STANDARD`.** Hardened review found
> that G8/G9's bridge artifacts were not ancestors of the accepted candidates,
> several frozen terminal checks were mathematically insufficient, and current
> builders no longer reconstruct the frozen corpus. The frozen output remains a
> provenance record, not accepted current capability evidence. Current-runtime
> V2 report generation is intentionally quarantined.

**Status:** FROZEN BEFORE V2 SEALED EXECUTION  
**Date:** 2026-09-16  
**Branch:** `agent/pct-computational-architecture`

## 1. Why V2 exists

The first goal-directed mixed-domain campaign established three supported capabilities on its frozen corpus: goal-directed solving, inferred compatibility, and verified macro synthesis. Its mixed-domain composition gate was not supported: only G4, G5, and G10 required multi-step primitive paths and no successful explicit path crossed exactness/representation classes.

This is not treated as a failed implementation test and V1 is not retuned. V2 is a new prospective campaign whose purpose is to test the missing composition layer with fresh calibration, validation, and sealed cases.

The V1 sealed outcomes are historical input to the V2 design only. V2 uses fresh goal IDs and parameter indices and may not be modified after the first V2 sealed run.

## 2. Governing question

Can the same goal-directed planner solve structured mathematical goals that *require* evidence-producing operator composition, including at least three successful paths crossing exactness or representation classes, without increasing wrong-positive behavior?

Target mechanism:

```text
structured goal
  -> candidate-producing operator(s)
  -> required derived evidence obligations
  -> representation bridge(s) where applicable
  -> candidate falsification / independent verification
  -> fail-closed verdict
```

## 3. Fresh data split

V2 reuses the deterministic G1-G12 mathematical generators but with disjoint parameter-index bands and V2-specific goal IDs:

- `CALIBRATION_V2`: base index 1000
- `VALIDATION_V2`: base index 2000
- `SEALED_V2`: base index 3000

Counts remain 3 calibration, 1 validation, and 2 sealed cases per family.

No V2 sealed expected result or reference path is exposed to the solver.

## 4. Semantic-type blinding

`EXPLICIT` mode receives explicit input semantic types.

`INFERRED` and `HYBRID` modes receive every original V2 input with its semantic type replaced by the same opaque placeholder. The compatibility model is trained only from V2 calibration goals and their explicit-mode traces. Structural descriptors may use representation class, exactness class, shape, and low-cardinality structural metadata, but not the hidden semantic labels at inference time.

The V2 campaign must report a separate `ALL_FAMILIES_TYPE_BLIND` gate requiring at least one correct sealed result in every G1-G12 family under `INFERRED/PRIMITIVE` while inputs are blinded.

## 5. Derived-evidence obligations

V2 goals add a solver-visible constraint:

```text
required_derived_types = (...)
```

A required type counts only if an artifact of that semantic type was produced by an operator during the current solve (`provenance` non-empty). Original inputs never satisfy a derived-evidence obligation.

A target artifact is not promotable to `PASS` until all required derived types are present. Candidate generation before obligation closure is allowed; search must continue from that state.

Frozen obligations:

| Family | Required derived evidence |
|---|---|
| G1 | `BOOLEAN_ZETA_SIGNAL` |
| G2 | `MATRIX_RANK` |
| G3 | `CHAIN_RESIDUAL_MATRIX` |
| G4 | none beyond its existing barcode→Betti→Euler comparison |
| G5 | none beyond its existing adaptive graph-signature comparison |
| G6 | `CONDITIONING_RISK` |
| G7 | `NILPOTENCY_RESULT` |
| G8 | `SYMBOLIC_EXPRESSION` |
| G9 | `CONVEXITY_VERDICT`, `SYMBOLIC_EXPRESSION` |
| G10 | none beyond support sampling→spectrum |
| G11 | none |
| G12 | `SYMBOLIC_EXPRESSION` |

These obligations describe mathematical evidence classes, not exact operator IDs.

## 6. Generic representation bridges

V1 exposed a genuine registry gap: no primitive could carry a discovered numerical relation or numerical geometric quantity into the symbolic representation class. V2 adds exactly two generic bridge primitives before sealed execution:

34. `NUMERIC_RELATION_SYMBOLIZE`
   - input: `NUMERIC_RELATION`
   - output: `SYMBOLIC_EXPRESSION`
   - representation/exactness: `SYMBOLIC`
   - semantics: deterministic symbolic rendering / `nsimplify` of the numerical coefficient; no access to a sealed answer.

35. `AREA_SYMBOLIZE`
   - input: `AREA`
   - output: `SYMBOLIC_EXPRESSION`
   - representation/exactness: `SYMBOLIC`
   - semantics: deterministic symbolic rendering / `nsimplify` of the numerical area; no access to a sealed answer.

No additional bridge may be added after the first V2 sealed run.

## 7. Composition gates

Primary V2 gates are prospective and fixed:

1. `EXPLICIT/PRIMITIVE` has zero wrong positives on V2 controls.
2. At least 10 of 12 families have at least one correct sealed primitive path containing >=2 primitive operators.
3. At least 3 families have at least one correct sealed primitive path containing operators from >1 exactness class or >1 representation class.
4. G6, G8, and G9 each have at least one correct sealed cross-class path.
5. Every positive result ends in the independent family verifier.
6. `INFERRED/PRIMITIVE` has zero control wrong positives and at least one correct sealed result in every G1-G12 family under semantic-type blinding.
7. `HYBRID/PRIMITIVE` has zero control wrong positives and solves no fewer families than `INFERRED/PRIMITIVE`.
8. Macro synthesis may reduce search only by replaying already verified primitive sequences. A synthesized run is never credited when its corresponding primitive-mode case was not semantically correct.
9. Macro support requires zero semantic changes relative to the corresponding correct primitive baseline and at least one reduction in expanded search states.

V2 scientific conclusions are reported separately:

```text
COMPOSITION_DEPTH
CROSS_REPRESENTATION_COMPOSITION
TYPE_BLIND_ROUTING
MACRO_PRESERVATION
```

Each is `SUPPORTED`, `NOT_SUPPORTED`, or `INCONCLUSIVE`.

## 8. Anti-retuning rule

Implementation may be tested on `CALIBRATION_V2` and `VALIDATION_V2` before sealed execution. The first execution that scores `SEALED_V2` freezes the V2 scientific result. After that point:

- no search-budget changes;
- no bridge additions or contract changes;
- no evidence-obligation changes;
- no compatibility-feature changes;
- no macro-threshold changes;
- no sealed-case replacement.

Any later architectural change is V3.

## 9. Claim boundary

The protocol intended a positive result to support executable goal-directed
composition over its frozen G1-G12 operator universe. The recorded result no
longer meets the hardened evidentiary standard described above and must not be
presented as a current support claim. Even as originally designed, it did not
address unrestricted theorem proving, natural-language mathematical
understanding, or correctness beyond its tested operator and verifier contracts.
