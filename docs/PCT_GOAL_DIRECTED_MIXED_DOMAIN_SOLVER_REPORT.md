# PCT Goal-Directed Mixed-Domain Solver Report

**Date:** 2026-09-16  
**Branch:** `agent/pct-computational-architecture`  
**V1 sealed status:** `PARTIAL`  
**V2 sealed status:** `SUPPORTED`  
**V2 frozen execution commit:** `f2e8cc73ef6665e9329d9b3901f7f8672e4dc4e5`  
**V2 Actions run:** `35059952763`

## 1. Scientific question

The E1-E31 program established many useful mathematical mechanisms, but E26-E31 showed that a relational-label classifier is not the same thing as a general mathematical solver. The goal-directed campaign therefore tested a different architecture:

```text
structured goal
  -> admissible operator search
  -> executable operator composition
  -> candidate construction
  -> required evidence / falsification
  -> independent verification
  -> fail-closed verdict
```

No LLM participates in the scored core. Natural-language interpretation is deliberately outside the experiment.

## 2. V1 result: planner capability established, composition boundary exposed

V1 used 12 goal families spanning exact/finite algebra, symbolic mathematics, graphs/topology, and numerical/convex geometry, with 33 executable primitives. It compared explicit, inferred, and hybrid typing, each with primitive-only and validated macro execution.

V1 established:

- all 12 families solved in `EXPLICIT/PRIMITIVE` with zero wrong positives;
- all 12 families solved in inferred mode after original input semantic types were blinded and compatibility was inferred from calibration structure;
- hybrid routing preserved the same family coverage and control safety;
- verified macro replay reduced search-state expansion without changing answers.

However, V1 did **not** establish mixed-domain composition. Only G4, G5, and G10 naturally required multi-step paths and no successful primitive path crossed representation/exactness classes. The failure was informative: many V1 targets could be emitted by one target-producing primitive, so the planner was often routing to an operator rather than composing a mathematical derivation.

The V1 scientific conclusions were therefore:

| Conclusion | Result |
|---|---|
| Goal-directed solving | **SUPPORTED** |
| Inferred compatibility | **SUPPORTED** |
| Mixed-domain composition | **NOT_SUPPORTED** |
| Macro synthesis | **SUPPORTED** |

## 3. V2 prospective composition stress protocol

V2 was specified before any V2 sealed result was scored. It introduced fresh calibration, validation, and sealed parameter bands and froze the architecture before sealed execution.

The key change was **derived-evidence obligations**. A candidate could exist before the solve was complete, but it could not be promoted to `PASS` until the required independently produced evidence artifacts existed. Original inputs could not satisfy those obligations.

Examples:

- G1: recover the Boolean atomic signal, then regenerate a derived zeta signal before promotion;
- G2: produce exact rank evidence as well as the null-space/identifiability result;
- G3: produce the chain-map verdict and an explicit chain residual;
- G6: obtain numerical conditioning evidence before exact-rank closure;
- G7: establish nilpotency evidence before invariant closure;
- G8: fit the numerical invariant coefficient and bridge it into a symbolic expression;
- G9: establish convexity, compute the geometric area prediction, and bridge the area into a symbolic expression;
- G12: construct a symbolic rewrite before identity closure.

V2 also added exactly two generic representation bridges, frozen before sealed execution:

- `NUMERIC_RELATION_SYMBOLIZE`: numerical relation -> symbolic expression;
- `AREA_SYMBOLIZE`: numerical area -> symbolic expression.

The V2 operator universe therefore contained 35 primitives.

## 4. First frozen V2 sealed result

The first V2 sealed scoring occurred at commit `f2e8cc73ef6665e9329d9b3901f7f8672e4dc4e5`. No solver architecture was modified after observing it.

The complete goal-solver suite passed **44/44 tests**, and the historical E1-E25 campaign smoke suite passed **23/23 tests** in the same workflow. The V2 scientific report then completed and was uploaded as a separate CI artifact.

### 4.1 Sealed six-mode results

| Mode | Correct outcomes / 24 | Wrong positives | Families represented by a correct outcome | Multi-step families | Cross-class families | Mean expanded states | Mean primitive executions |
|---|---:|---:|---:|---:|---:|---:|---:|
| EXPLICIT / PRIMITIVE | 23 | 0 | 12 | 11 | 3 | 3.96 | 1.96 |
| EXPLICIT / SYNTHESIZED | 23 | 0 | 12 | 11 | 3 | 2.58 | 2.17 |
| INFERRED / PRIMITIVE | 23 | 0 | 12 | 11 | 3 | 3.96 | 1.96 |
| INFERRED / SYNTHESIZED | 23 | 0 | 12 | 11 | 3 | 3.67 | 2.12 |
| HYBRID / PRIMITIVE | 23 | 0 | 12 | 11 | 3 | 3.96 | 1.96 |
| HYBRID / SYNTHESIZED | 23 | 0 | 12 | 11 | 3 | 3.67 | 2.12 |

Every one of the ten prospectively frozen V2 gates passed.

## 5. Four V2 scientific conclusions

### 5.1 COMPOSITION_DEPTH — SUPPORTED

Eleven of the twelve families produced at least one correct sealed solution using two or more primitive operations:

`G1, G2, G3, G4, G5, G6, G7, G8, G9, G10, G12`.

The only single-step family was G11 (`MIXED_AREA_DEFECT -> VERIFY_CANDIDATE`). The explicit primitive mode produced zero wrong positives.

This is materially different from V1. The planner no longer receives credit merely because a target-producing primitive exists; in most families it has to construct and retain additional mathematical evidence before closure.

### 5.2 CROSS_REPRESENTATION_COMPOSITION — SUPPORTED

Three prospectively required families crossed representation or exactness classes:

- **G6:** `CONDITIONING_RISK_CHECK -> EXACT_MATRIX_RANK_Q -> VERIFY_CANDIDATE`. Numerical conditioning evidence routes the solve into exact rational rank closure.
- **G8:** `NUMERIC_RELATION_FIT -> NUMERIC_RELATION_SYMBOLIZE -> VERIFY_CANDIDATE`. A numerical invariant fit is carried into a symbolic representation before promotion.
- **G9:** on the convex sealed case, `CONVEXITY_CHECK -> STEINER_OFFSET_PREDICT -> AREA_SYMBOLIZE -> VERIFY_CANDIDATE`. Geometric/numerical evidence is carried into a symbolic representation before final verification.

The nonconvex G9 control correctly returned `NOT_APPLICABLE` rather than forcing the Steiner operator outside its domain.

This supports executable cross-class composition in the frozen operator universe. It does **not** yet mean that arbitrary symbolic and numerical theories can be joined automatically. G8/G9 use generic representation bridges whose semantics are deliberately narrow and independently round-trip checked.

### 5.3 TYPE_BLIND_ROUTING — SUPPORTED

For `INFERRED` and `HYBRID` sealed execution, every original input semantic type was replaced by the same opaque placeholder before the planner received the goal.

The compatibility model was fitted only on calibration goals and learned structural type prototypes from representation class, exactness class, value shape, and low-cardinality structural metadata. Derived artifacts retained their operator-declared output contracts.

Under this blinding:

- inferred primitive execution produced a correct outcome in all 12 families;
- hybrid primitive execution produced a correct outcome in all 12 families;
- inferred and hybrid each had zero wrong positives and zero control wrong positives;
- their primitive paths matched the explicit solver on the frozen sealed cases.

This is stronger than the original V1 inferred-routing result because the planner is no longer allowed to consume the supplied input semantic labels during execution.

### 5.4 MACRO_PRESERVATION — SUPPORTED

V2 synthesized 43 candidate macros from calibration traces. Across the three primitive/synthesized mode pairs:

- 26 sealed cases actually used a macro and received credited search reduction;
- there were zero semantic changes on correct primitive baselines;
- no reduction was credited from an incorrect primitive baseline.

The strongest search-state compression was in explicit mode: mean expanded states fell from **3.96 to 2.58**, about a **34.7% reduction**.

This should not be described as an overall compute reduction. Mean primitive executions in explicit mode increased from **1.96 to 2.17** because macro replay expands back into its constituent primitives and can perform extra verified work while skipping intermediate planner states. The supported claim is therefore **search compression with semantic preservation**, not lower arithmetic cost.

## 6. The remaining sealed failure is informative

Every mode had the same one unresolved sealed case: the identical-graph G5 control (`sealed_v2:g5:01`). The expected result was `False` for distinguishability, but the solver returned `NOT_ESTABLISHED`, not an incorrect positive.

This is a specific architectural boundary rather than random failure. Planner state deduplication treats two derived artifacts with identical semantic type, representation, exactness, value, and metadata as equivalent without retaining endpoint multiplicity/provenance in the state signature. For two identical graphs, equal signatures from the two endpoints can therefore collapse into one artifact. The G5 comparison logic needs two endpoint-specific signatures to prove that the frozen signature bank was exhausted without separation.

Consequently the current solver is better at **proving separation** than at **proving non-separation under a finite invariant bank**. Its fail-closed behavior is correct—the case remains `NOT_ESTABLISHED`—but a more general solver will need provenance-sensitive multiplicity or explicit relational slots when equality itself is the target evidence.

Because V2 is frozen, this is not repaired in V2. Any such change belongs to a subsequent campaign version.

## 7. What V2 changes about the overall interpretation

E26-E31 showed that semantic-label recovery alone was not the general solver we were trying to build. V1 then showed that the E-series mechanisms could be organized under a target-driven planner, but exposed an important shortcut: direct target-producing primitives often made composition unnecessary.

V2 closes that specific loophole prospectively. On fresh sealed parameters, a single planner now demonstrably performs:

```text
goal recognition from a structured target
  -> structural compatibility/routing
  -> operator selection
  -> multi-step evidence construction
  -> exact / symbolic / numerical representation transitions
  -> applicability refusal where required
  -> independent final verification
```

and it does so with the original semantic input labels hidden in inferred/hybrid modes.

The strongest justified statement is therefore:

> **MAPEOGEO/PCT now contains a functioning goal-directed, mixed-domain operator solver over its frozen executable mathematical universe. It can compose verified operations across exact, symbolic, numerical, graph/topological, and geometric representations, and can infer input/operator compatibility from structural calibration rather than supplied semantic labels.**

That is a substantially stronger result than relational classification. It is still bounded by the operator registry and structured goal grammar.

## 8. Claim boundary

The campaign does **not** establish:

- unrestricted theorem proving;
- universal mathematical problem solving;
- natural-language mathematical understanding;
- automatic discovery of arbitrary new primitive operators;
- correctness outside the frozen operator and independent-verifier contracts;
- that a synthesized macro is a novel theorem;
- that representation bridges constitute a universal mathematics ontology.

What it establishes is narrower and concrete: **goal-directed executable composition with fail-closed verification over a heterogeneous, frozen mathematical operator space.**

## 9. Reproducibility/provenance

- V2 frozen execution commit: `f2e8cc73ef6665e9329d9b3901f7f8672e4dc4e5`
- GitHub Actions run: `35059952763`
- V2 result artifact: `pct-goal-solver-v2-results`
- V2 artifact ID: `10431654598`
- artifact archive SHA-256: `baf020fa8007e3f721b44264c168249c4abf6689787f23db76f0ba4adee60235`

The archive hash is recorded only to identify the inspected artifact; it is not a scientific pass/fail criterion.
