# v0.20 Goal-Solver Rigor Design

**Branch:** `agent/goal-solver-cross-class-v0-20`  
**Frozen base:** `32967600a00a5659e49fa3ef056be02567c74efa`  
**Integration rule:** consume the repaired `main` branch only after its review; never merge this branch into `main` in this work.

## Scientific boundary

The old 10/10 report is historical and superseded. A green test suite cannot establish support unless the prospective campaign also satisfies its frozen, non-vacuous gates. Unsupported mathematics returns a structured refusal. It is never converted into `PASS` by a permissive verifier, inferred label, macro, or scorer.

## Typed execution and planner-owned lineage

Every artifact has a complete `ArtifactType(semantic_type, representation_class, exactness_class)`. Every operator declares named input ports with complete types and one complete output type. The planner enumerates injective port bindings and passes only those bindings to execution. Returned output types must equal the registry contract.

Callers and operators cannot assert authoritative provenance. The planner records roots and immutable derivation steps from the actual port binding. State identity includes value, complete type, root identity, and derivation/lineage state. Candidate selection enumerates all artifacts matching the complete target contract.

`GoalSpec` carries a verifier contract and, for cross-class goals, a candidate-lineage obligation. X1 requires the coefficient root to traverse exact coefficients -> symbolic polynomial -> numerical evaluations, with the grid root joined before certification. X2 requires exact invariants -> symbolic nonsingular Weierstrass curve -> numerical period enclosure -> certificate. A candidate cannot borrow an intermediate from another branch.

Compatibility inference is an immutable routing decision for root bindings. It may rank admissible operators, but cannot mutate artifacts, relax contracts, manufacture lineage, or alter verification.

## Sound no-shortcut evidence

`prove_lineage_obligation` computes a finite closure over the complete operator type hypergraph and `(required-root mask, ordered-stage progress)`. A result is:

- `PROVED`: a replayable obligation-satisfying route exists and no target route lacking the obligation exists;
- `REFUTED`: an unsafe target route exists, with a counterexample path; or
- `UNREACHABLE`: no complete route exists.

The proof is bound to canonical digests of the registry, goal contract, resolved root types, and lineage obligation. Injecting a direct exact-to-target operator refutes the proof; removing either bridge makes it unreachable. Macro proposals are ignored as graph edges because they are inert primitive sequences with no execution authority.

## Mathematical contracts

- **F1:** exact rational lower/upper witnesses for the Dedekind cut of `sqrt(2)`, checked by integer squares.
- **F2:** an exact quadratic mean-value certificate: secant slope and `c=(a+b)/2` with exact derivative equality and `a<c<b`.
- **F3:** integer-only extended gcd with nonnegative gcd, divisibility, Bézout identity, and greatestness. Alternate valid coefficients score as correct.
- **C1:** explicit coordinate symbols and independently recomputed Cauchy-Riemann residuals; non-holomorphic controls must fail.
- **C2:** explicit variable/pole and independently recomputed residues, including nonunit, zero, and higher-order cases.
- **X1:** exact rational polynomial and grid values are the reference; numerical evaluations carry error enclosures; the terminal certificate recomputes every value from roots and enforces the goal tolerance.
- **X2:** curve `y^2=4x^3-g2*x-g3`, exact nonsingularity `g2^3-27g3^2 != 0`, and a scoped positive-discriminant real-root regime. Fundamental full periods are enclosed using root isolation and AGM bounds. The q-series receipt is a non-authoritative diagnostic and does not independently validate the invariants `g2,g3`. Singular/unsupported regimes refuse.
- **G1-G12:** every terminal verifier reconstructs the claimed object from the original inputs. Nullspace bases, chain-map localization, persistence separation, graph comparison, supplied symbolic generator, geometry, symmetry, and homothety are checked rather than inferred from labels or shape counts.

All numerical adapters preserve exact integers/rationals, reject nonfinite and opaque values, and contain exceptions as structured failures.

## Macro conservation

Canonical serialization is domain-separated SHA-256 over tagged types; it distinguishes booleans, integers, floats, exact rationals, strings, lists/tuples/sets/maps, complex values, NumPy scalars/arrays, and SymPy expressions. NaN, infinity, callables, and opaque objects are rejected. Python `hash` and `repr` are not identities.

A macro proposal is a syntactic sequence of primitive operators with calibration witnesses. The present proposal schema does not bind the full executable dependency closure, runtime request/configuration, budget, or complete typed replay ledger, so proposals have no solver authority. `solve()` does not evaluate them; synthesized configurations execute the same primitive path, which makes rescue impossible but earns no macro-conservation or efficiency credit.

Runtime macro execution remains disabled until a certificate can preserve the exact verdict, normalized candidate, structured refusal identity, obligation witnesses, verifier/routing/lineage receipts, registry/goal/configuration bindings, and complete work counters. This fail-closed boundary is a reported capability failure, not a supported macro result.

## Corpus, scoring, and gates

Calibration, validation, and sealed problem fingerprints are content-disjoint. IDs do not establish disjointness. The frozen terminal-control manifest contains exactly 22 external probes: one domain-refusal and one invalid-terminal-certificate control for each of the seven new families (14), valid-negative-result controls for F2, F3, C1, C2, and X1 (5), and external-valid-certificate controls for F2, F3, and X1 (3). Only the F2 and F3 external certificates claim mathematically distinct alternatives; X1 replays its deterministic receipt. Scores use independently recomputed mathematical predicates and declared field tolerances.

Gates freeze exact expected family/case/control counts; empty collections fail. They require zero wrong positives, full required control behavior, X1/X2 shortcut proofs and runtime lineage receipts, explicit/inferred/hybrid target-contract enforcement, zero macro rescues, deterministic evidence, and repaired-main integrity checks. Exact macro conservation remains a capability gate and fails while macro execution is disabled. `SUPPORTED` is emitted only when every gate passes; other results are classified as `EVIDENCE_PARTIAL`, `NOT_SUPPORTED`, or `ENGINE_INVALID` without softening failures.

## Evidence and current main

The report records the frozen feature base, hashes the dependency lock and listed implementation files, records corpus/control and registry-contract digests, serializes inert macro-proposal rows, and embeds the exact repaired-main binding. JSON generation is canonical, accepts an explicit output directory, ends with a newline, and is byte-identical across hash seeds. The repaired-main branch and this feature branch remain separate and unmerged; CI checks out the exact repaired-main commit independently and verifies its bound tree and evidence.
