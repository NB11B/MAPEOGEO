# MAPEOGEO Rigor-First Mathematics Expansion Design

Date: 2026-09-16
Branch: `agent/math-expansion-rigor-v0-21`
Base: accepted `main` at v0.20 mathematical-integrity baseline

## 1. Objective

Expand MAPEOGEO substantially in both foundational and advanced mathematics without weakening epistemic rigor.

The governing rule is:

> **Coverage may grow quickly; authority may grow only with evidence. Prefer an honest hole over a fabricated bridge.**

The expansion must preserve the v0.20 distinction between source identity, canonical identity, executable evidence, formal linkage, kernel verification, and proof-eligible grounding.

No new stage may restore the historical anti-patterns that v0.20 corrected: hand-authored material masquerading as extracted source declarations, silent semantic upgrades, representative examples promoted to theorem evidence, or graph reachability described as proof.

## 2. Current baseline and why expansion is needed

The accepted v0.20 projection contains 2,135 admissible source declarations. Its 176-row foundation catalog spans logic, sets, relations/functions, number systems, elementary algebra, order/sequences, Euclidean geometry/trigonometry, and elementary calculus.

However, v0.20 also establishes the present rigor boundary:

- declaration-level executable evidence: 1 / 176 foundation declarations;
- kernel-verified foundation declarations: 0 / 176;
- proof-eligible grounding: 0 / 235 advanced canonical objects;
- raw topology reachability is descriptive only and is not proof.

The next expansion therefore has two simultaneous goals:

1. deepen the mathematical graph into missing foundational and connective areas;
2. improve source fidelity and statement-specific validation so the graph becomes more trustworthy as it grows.

## 3. Expansion architecture

This is not a new graph subsystem. It is a stricter intake discipline applied to the existing MAPEOGEO architecture.

```text
REAL SOURCE ARTIFACT
  ↓
source document / source tree identity
  ↓
exact extracted statement + locator + statement hash
  ↓
SOURCE_DECLARATION
  ↓
canonicalization candidate
  ↓
semantic relation contract
  ├── SAME_SEMANTICS
  ├── SCOPED_OVERLAP
  ├── RELATED_TO
  └── UNRESOLVED / WOUND
  ↓
optional statement-specific executable evidence
  ↓
optional FORMAL representation
  ↓
optional Lean kernel verification
```

No stage may bypass this flow by creating a source declaration directly from an internally written paraphrase.

## 4. Non-negotiable source-admission rules

### 4.1 Source declarations

A `SOURCE_DECLARATION` must originate in a concrete source artifact.

Required fields:

- source ID;
- author/title/edition or repository revision;
- source artifact SHA-256 or immutable source revision;
- exact locator: chapter/section/theorem/definition/lemma/proposition/page when available;
- exact extracted source statement in transient processing memory;
- deterministic normalized statement hash;
- extraction mode (`SOURCE_PARSE`, `SOURCE_TREE_PARSE`, or explicitly labeled `CURATED_TRANSCRIPTION` when literal extraction is technically impossible);
- structural references explicitly present in the source.

A canonical description may be written by MAPEOGEO, but it must never be labeled as the source statement.

### 4.2 Curated transcription fallback

Curated transcription is a fallback, not the default.

When used:

- it must be labeled `CURATED_TRANSCRIPTION`;
- the source locator must be exact;
- the transcription must be reviewed against the source artifact;
- it may not be described as automatically extracted;
- a second source or formal check is preferred for high-centrality declarations.

### 4.3 No Mathlib-as-source

Mathlib remains a verifier/tester and is never ingested as provenance for the mathematics graph.

## 5. Formulation integrity checks

Every new theorem-level or definition-level source statement must be checked for the following before semantic promotion:

- quantifier scope;
- exact domain and codomain;
- finite/infinite dimensionality assumptions;
- compactness, connectedness, completeness, separability, sigma-finiteness, smoothness, orientation, boundary, regularity, measurability, integrability, or boundedness hypotheses where relevant;
- equality conditions;
- exceptional cases;
- local versus global scope;
- existence versus uniqueness;
- one-way implication versus equivalence;
- pointwise versus uniform versus norm/topology convergence;
- algebraic versus topological versus measure-theoretic notions that share names but differ in scope.

The intake validator must fail closed when a required scope distinction is unresolved.

## 6. Hypothesis-mutation and falsification tests

For statements with nontrivial hypotheses, add mutation tests where computationally or formally tractable:

- drop one hypothesis;
- weaken one hypothesis;
- perturb a boundary/equality case;
- generate finite counterexample searches when applicable;
- use symbolic counterexample search where feasible;
- record whether the hypothesis appears essential, redundant in the tested scope, or untested.

A failed mutation test is not a source error by itself; it is evidence about scope.

## 7. Evidence promotion rules

### 7.1 Executable evidence

Executable evidence must bind to one exact declaration hash or one exact semantic relation endpoint pair.

Acceptable evidence classes include:

- exhaustive finite enumeration;
- exact symbolic identity checking;
- exact integer/rational arithmetic;
- property-based testing over a preregistered finite or generated domain;
- independently implemented algorithm agreement;
- scoped numerical falsification tests for analytic claims.

Representative numerical examples are never sufficient for theorem-level verification.

### 7.2 Formal evidence

Maintain the existing hierarchy:

```text
FORMAL_LINKED != KERNEL_VERIFIED
```

A formal declaration is promoted to `KERNEL_VERIFIED` only after the pinned Lean kernel accepts it under the declared scope.

### 7.3 Proof-eligible grounding

A foundation-to-advanced path is proof-eligible only when:

- the root declaration is source-validated;
- every edge is endpoint-bound;
- every traversed semantic/proof relation has closed evidence;
- no edge is wounded, unresolved, inactive, or merely structural.

Raw graph reachability remains a separate descriptive metric.

## 8. Cross-source semantic contracts

Use the conservative lattice already established by v0.20:

```text
RELATED_TO < SCOPED_OVERLAP < SAME_SEMANTICS
```

Promotion requirements:

- `SAME_SEMANTICS`: formulation-equivalent in the declared scope;
- `SCOPED_OVERLAP`: one is a specialization, restriction, coordinate form, finite-dimensional case, or otherwise limited overlap;
- `RELATED_TO`: mathematically connected but not semantically identical;
- unresolved conflicts become wounds, never silently upgraded.

High-centrality canonical nodes should have at least two independent sources before becoming stable cross-domain hubs when practical.

## 9. Foundational mathematics expansion

The existing eight-layer foundation remains, but it must be deepened with real-source coverage rather than enlarged by internally authored primitive rows.

### Wave F1 — Logic, proof, set theory, discrete mathematics

Primary targets:

- propositional syntax and semantics;
- first-order syntax, structures, satisfaction;
- natural deduction / sequent-style proof systems where the source provides them;
- soundness and completeness;
- compactness;
- computability / Turing machines / undecidability;
- cardinality and countability;
- Cantor-Schröder-Bernstein;
- ZFC axioms with source-bound formulations;
- ordinals/cardinals at introductory depth;
- induction and recursive definitions;
- counting principles;
- inclusion-exclusion;
- recurrences;
- generating functions;
- graph theory: paths, cycles, trees, connectivity, Euler/Hamilton concepts, matching basics.

Preferred sources:

- Open Logic Project, source LaTeX, CC BY 4.0;
- Tim Button / Open Logic `Set Theory: An Open Introduction`, source LaTeX, CC BY 4.0;
- Oscar Levin, *Discrete Mathematics: An Open Introduction*, source available; prefer an edition whose license and source tree can be frozen exactly;
- Richard Hammack, *Book of Proof*, as an independent secondary source for proof/sets/relations/functions/cardinality where reuse terms permit source-bound extraction.

### Wave F2 — Elementary number theory and abstract algebra

Targets:

- divisibility, gcd, Euclidean algorithm, Bézout;
- primes and unique factorization;
- congruences and modular arithmetic;
- Chinese remainder theorem;
- Fermat/Euler theorems;
- groups, subgroups, cyclic groups;
- homomorphisms, kernels, images;
- normal subgroups and quotient groups;
- isomorphism theorems;
- group actions and orbit-stabilizer;
- Sylow theory;
- rings, ideals, quotient rings;
- polynomial rings;
- integral domains/UFD/PID/Euclidean domains where source scope supports them;
- modules at introductory depth;
- fields and field extensions;
- finite fields;
- Galois groups and the fundamental theorem of Galois theory.

Preferred source:

- Thomas W. Judson, *Abstract Algebra: Theory and Applications*, frozen source revision from the official open-source repository;
- an independently sourced elementary number theory text, frozen by exact version/revision, before promoting high-centrality number-theory objects.

### Wave F3 — Rigorous real analysis deepening

Targets:

- sequences and series of functions;
- uniform convergence;
- interchange of limits, continuity, differentiation, and integration;
- metric-space continuity and compactness;
- completeness and contraction mapping;
- multivariable differentiability;
- inverse and implicit function theorems;
- Taylor theorem with remainder;
- parameter-dependent integrals where source coverage supports them.

Preferred source:

- Jiří Lebl, *Basic Analysis*, frozen official version/source where available;
- Gallier remains an existing cross-source comparator rather than sole authority.

## 10. Advanced connective expansion

Advanced growth should follow dependency order rather than novelty.

### Wave A1 — ODE and dynamical systems

Targets:

- existence/uniqueness;
- Picard iteration;
- linear systems and matrix exponential;
- autonomous systems and flows;
- equilibria and linearization;
- stability;
- phase portraits;
- Sturm-Liouville structures where source scope supports them.

Preferred source:

- Gerald Teschl, *Ordinary Differential Equations and Dynamical Systems*, official author-hosted edition.

### Wave A2 — Functional analysis and operator theory

Targets:

- normed and Banach spaces;
- bounded linear operators;
- dual spaces;
- Hahn-Banach;
- uniform boundedness;
- open mapping and closed graph theorems;
- Hilbert spaces;
- Riesz representation;
- adjoints;
- compact operators;
- spectral theorem in carefully scoped forms;
- distributions and Fourier methods where source treatment supports them.

Preferred source:

- Hunter & Nachtergaele, *Applied Analysis*, official freely hosted text;
- add a second source before promoting high-centrality functional-analytic theorems to strong cross-source identity.

### Wave A3 — Algebraic topology

Targets:

- homotopy;
- fundamental group;
- covering spaces;
- singular homology;
- chain complexes;
- exact sequences;
- cohomology;
- cup products at introductory depth;
- homotopy groups where source scope supports them.

Preferred source:

- Allen Hatcher, *Algebraic Topology*, official author-hosted text.

This wave should connect to the existing PCT chain-complex machinery without equating matching invariants with semantic identity.

### Wave A4 — PDE / harmonic / Fourier analysis

Targets:

- classical PDE types;
- weak derivatives;
- distributions;
- Sobolev spaces;
- Fourier transform;
- convolution;
- elliptic/parabolic/hyperbolic examples;
- variational formulations;
- maximum principles;
- weak solutions and energy estimates at source-supported depth.

### Wave A5 — Numerical analysis and scientific computing

Targets:

- floating-point error;
- conditioning and stability;
- root finding;
- interpolation;
- quadrature;
- numerical differentiation;
- linear-system solvers;
- eigenvalue algorithms;
- ODE integration;
- approximation/convergence/error bounds.

Preferred source:

- Driscoll & Braun, *Fundamentals of Numerical Computation*, official online text/source where available.

### Wave A6 — Stochastic processes

Targets:

- Markov chains;
- transition kernels;
- stationary distributions;
- martingales;
- stopping times;
- Brownian motion;
- stochastic integration only after measure/probability prerequisites are sufficiently represented.

## 11. Deferred domains

Do not yet make these primary expansion targets:

- schemes and advanced algebraic geometry;
- derived categories;
- infinity-categories;
- advanced representation theory;
- class field theory;
- sheaf cohomology beyond what is already present as a scoped advanced object;
- category theory as a broad standalone ontology layer.

These should wait until their prerequisites are represented deeply enough to prevent decorative or circular semantic links.

## 12. Source hierarchy and ingestion order

Recommended order:

```text
Open Logic / Set Theory
  ↓
Discrete Mathematics
  ↓
Abstract Algebra + Elementary Number Theory
  ↓
Rigorous Real Analysis Deepening
  ↓
ODE / Dynamical Systems
  ↓
Functional Analysis / Operator Theory
  ↓
Algebraic Topology
  ↓
PDE / Harmonic Analysis
  ↓
Numerical Analysis
  ↓
Stochastic Processes
```

Independent waves may be developed in parallel only when they do not share unresolved canonicalization decisions.

## 13. Intake implementation requirements

Each source adapter must expose the same interface:

```text
source_identity()
extract_declarations()
extract_structural_refs()
validate_locators()
serialize_zero_prose_manifest()
```

Each emitted declaration must be reproducible from the pinned source artifact.

Each canonical alignment generator must produce:

```text
source_id
canonical_id
relation_type
scope_contract
formulation_check
status
wound_if_any
```

The active graph must never infer `SAME_SEMANTICS` merely from name similarity, embedding similarity, shared invariants, or shared neighbors.

## 14. Testing strategy

### Source fidelity tests

- source artifact hash matches pinned identity;
- every declaration locator resolves;
- every persisted statement hash reproduces from source extraction;
- no source prose/page image is persisted in graph artifacts;
- curated transcription rows are explicitly labeled and audited;
- parser failure is fail-closed.

### Formulation tests

- quantifier/domain/hypothesis fields present when required;
- known scope distinctions are preserved;
- source statement and canonical contract cannot silently disagree;
- mutation/counterexample tests for selected high-risk theorem classes.

### Semantic relation tests

- `SAME_SEMANTICS` requires a scope contract;
- conflicts meet conservatively;
- no section anchor may become declaration-level identity;
- no wound may enter proof-eligible grounding.

### Executable evidence tests

- evidence binds exact statement hash or exact edge endpoints;
- representative examples cannot promote theorem verification;
- exhaustive/symbolic/exact contracts are distinguished from numerical falsification tests.

### Formal tests

- Lean toolchain pinned;
- formal declarations build;
- kernel verification status generated from actual Lean acceptance;
- formal links never imply source identity.

### Reconstruction tests

- two clean exported trees reconstruct byte-identical deterministic artifacts;
- sealed v0.11 and v0.19 historical inputs remain unchanged;
- v0.20 amendment registries remain content-addressed and immutable unless superseded by a new explicit amendment.

## 15. Scientific reporting

Each expansion wave reports at least:

- number of real source declarations ingested;
- extraction-mode distribution;
- parser/locator wounds;
- canonical objects added;
- `SAME_SEMANTICS`, `SCOPED_OVERLAP`, `RELATED_TO`, and unresolved counts;
- executable evidence count by evidence class;
- formal-linked count;
- kernel-verified count;
- raw topology reachability;
- proof-eligible grounding;
- number of hypothesis-mutation tests and counterexamples found;
- source/version hashes.

No dashboard may collapse these into one confidence score.

## 16. Stop conditions

A wave stops after one repair pass if:

- source parsing remains ambiguous;
- locator fidelity cannot be established;
- a semantic relation remains contested;
- executable testing cannot resolve scope;
- formalization becomes disproportionately expensive.

The unresolved item is recorded as `WOUND`, `UNTESTED`, `UNFORMALIZED`, or `UNRESOLVED`, and mathematical coverage proceeds elsewhere.

## 17. Acceptance criteria for the first rigor-first expansion wave

The first implemented wave should be accepted only if all of the following hold:

1. every new `SOURCE_DECLARATION` is reproducibly bound to a real source artifact;
2. zero internally authored paraphrases masquerade as source text;
3. every persisted locator resolves against the pinned source;
4. every strong semantic relation has an explicit formulation/scope contract;
5. all unresolved conflicts remain visible;
6. executable evidence is declaration- or edge-specific;
7. Lean verification remains fail-closed and separate from source ingestion;
8. deterministic clean reconstruction passes twice;
9. historical sealed inputs remain byte-identical;
10. the full repository test suite passes;
11. the scientific report states exactly what was verified and what remains merely mapped.

## 18. First implementation target

The first implementation plan should cover only **Wave F1**:

- Open Logic Project logic source;
- Open Logic Set Theory source;
- one frozen edition of Levin's discrete mathematics text;
- source-bound parser/adapters;
- formulation-contract schema;
- conservative canonical alignments into the existing graph;
- statement-specific executable tests only where exact finite checking is appropriate;
- CI reconstruction and integrity gates.

Wave F2 and all advanced waves remain out of scope for the first implementation plan. They should reuse the F1 intake contract after F1 is verified.
