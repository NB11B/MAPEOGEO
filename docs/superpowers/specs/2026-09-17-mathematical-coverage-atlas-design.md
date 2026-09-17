# MAPEOGEO mathematical coverage atlas — design

Date: 2026-09-17. Status: reviewable specification; implementation and ingestion have not been performed by this document.

Repository: NB11B/MAPEOGEO. Pinned design baseline: `21dd869c214ad48c3eb0ce4e8784a253a75055f0` on `agent/joint-layer-v0-21`. Expansion working label: v0.22; Wave F5 remains the first intake tranche, not a claim that a release already exists.

Companion: [Wave F5 functional analysis and ODE design](2026-09-17-wave-f5-functional-analysis-ode-design.md).

## 1. Objective and delivery model

Deepen and widen the mathematical knowledge graph through source-grounded mathematics. Its long-term purpose is to support operator-, functional-, and transformation-based interrogation across mathematical domains, with geometric and visual interrogation of the same scoped objects and mechanisms. This does not assume that every branch of mathematics reduces to a Banach-space problem.

Coverage is the immediate priority. Intake must not wait for universal formalization, two executable views, a new user interface, or completion of an entire textbook. Definitions, theorems, constructions, examples, counterexamples, algorithms, dependencies, and distinct proof routes are all useful intake units. Executable evidence and formal verification enrich those units independently.

Use an open-ended coverage atlas with finite, reviewable batches. There is no 32-concept ceiling and no fixed number of source declarations. Each batch freezes a finite chapter/section/statement selection before evaluation, accounts for every selected item, and records unresolved dependencies explicitly. New discoveries enter the next manifest revision, not an invisible change to an evaluated denominator.

Alternatives considered: one monolithic release makes review and failure attribution difficult; acquisition-order intake produces accidental coverage gaps. The selected approach combines a dependency-led first tranche with parallel subject lanes and a persistent discovery queue. Independent packages can be accepted separately; the umbrella atlas is never described as all mathematics completed.

## 2. Baseline and interpretation of existing coverage

The repository contains historical intake and newer evidence campaigns. A named domain, a curated canonical object, a hashed source transcription, and a general verified theorem are different coverage states.

| Existing component | Reuse in the expansion | Required interpretation |
|---|---|---|
| v0.11 Gallier graph and bindings | Original declaration identities and lineage | Keep historical bytes; use current amendments and wounds for active claims |
| v0.12–v0.14 linear algebra, VMLS, convex optimization | Linear maps, duality, matrix geometry, convexity | Check exact field, dimension and formulation before alignment |
| v0.15 and F4 analysis | Completeness, limits, continuity, calculus, quantified contracts | F4 evidence tiers do not automatically certify neighboring claims |
| v0.16 topology and metric structure | Topological prerequisites and anchors | Section anchors are not extracted theorem declarations |
| v0.17 measure and probability | Integration, function spaces and probabilistic links | Reconcile current amendments before using historical equivalence claims |
| v0.18 differential geometry | Manifolds, fields, forms and geometric mechanisms | Split composite concepts where their hypotheses differ |
| v0.19 complex analysis | Analytic and spectral bridges | Respect current wounds and source-edition distinctions |
| F1–F3 foundations and algebra | Logic, sets, finite structures, rings and fields | Finite contracts stay finite |
| v0.21 joint layer and PCT | Mechanism vocabulary and attachment interfaces | Presence of a certificate object does not establish independent replay |

The pinned `scripts/reconstruct_pipeline.py` runs through F4 and the joint layer, but F2–F4 are campaign invocations rather than proof that their entire inventories are merged into one cumulative graph. F5 must inventory both graph records and campaign manifests. It must explicitly materialize reconciled F3/F4 records where missing, with ID mappings and deltas, instead of counting campaign rows as graph nodes.

The supplied local completion report states 307 tests passing and a successful Lean build. These are user-reported baseline results, not tests rerun for this documentation change. Remote branch and source inspection confirm the commit and interfaces; this specification does not claim a fresh CI pass.

## 3. Coverage vocabulary

Track independent axes rather than a single green/red badge:

1. Discovery: `DISCOVERED`, `SOURCE_LOCATED`, `EDITION_PINNED`, `EXTRACTED`, `REVIEWED`, `REGISTERED`.
2. Existing-object disposition: `REUSE_EXACT`, `REFINE_SCOPE`, `SPLIT_COMPOSITE`, `ADD_VARIANT`, `NEW`, `UNRESOLVED`.
3. Evidence: source-attested, checked symbolic family, exact bounded instance, certified enclosure, numerical probe, formal-general certificate, certified counterexample, or no executable evidence.
4. Provenance: exact source transcription, source normalization, curator formulation, translation, exercise, or external reference. Hashes must state which of these they identify.
5. Dependency: resolved source citation, reviewed mathematical prerequisite, unresolved external prerequisite, or proof-path dependency. Do not conflate these edges.
6. Visualization: structural diagram, exact geometric realization, validated enclosure, or illustrative projection.

Evidence types are not a simple total order: a counterexample may refute a broader statement while leaving a narrower theorem valid. Store evidence against a claim and scope, not just a topic label.

## 4. Subject atlas

The table is a target inventory, not a claim of verified absence from the current graph. Initial priority means an intake lane, not a compulsory serial prerequisite for every other lane.

| Lane | Mathematical inventory | Principal interfaces | Initial priority |
|---|---|---|---|
| Foundations and logic | Propositional/first-order logic; model theory; compactness; completeness; computability; recursion; proof theory; constructive analysis; set-theoretic choice principles; type theory | Existing F1 logic; proof scopes; formal foundations | Extend where prerequisites expose gaps |
| Category and universal algebra | Categories; functors; natural transformations; universal properties; Yoneda; limits/colimits; adjunctions; monads; Kan extensions; enriched categories; categorical logic | Cross-domain constructions and diagram semantics | Broad discovery; elementary intake early |
| Linear and multilinear algebra | Tensor products; bilinear/sesquilinear forms; exterior/symmetric powers; Jordan/rational canonical forms; canonical decompositions; matrix inequalities | Operators, geometry, numerics | Reconcile existing coverage immediately |
| Abstract algebra | Modules; exact sequences; localization; ideals; Noetherian/Artinian structures; PID modules; field extensions; Galois theory; Lie algebras | Spectra, topology, arithmetic | Extend F3 |
| Representation theory | Group/algebra representations; characters; irreducibility; Maschke; Schur; induced representations; compact-group representations; Lie groups/algebras | Harmonic analysis and symmetry actions | Early cross-domain lane |
| Number theory | Congruences; Diophantine equations; arithmetic functions; algebraic integers; ideals; valuations; local fields; analytic number theory; elliptic curves; modular forms | Algebra, complex analysis, spectral methods | Extend existing elementary theory |
| Combinatorics and discrete mathematics | Enumerative methods; generating functions; posets; incidence algebras; Möbius inversion; matroids; extremal/probabilistic combinatorics; designs | PCT reconstruction, algebra, probability | Early independent lane |
| Graph theory | Connectivity; flows/cuts; matchings; planar graphs; graph spectra; random graphs; graph limits; discrete Laplacians | Visual structure, operators, algorithms | Early independent lane |
| General topology | Bases/subbases; products; quotients; separation; compactness; connectedness; nets/filters; metrization; paracompactness; uniform spaces | Function spaces, manifolds and weak topologies | F5 prerequisite reconciliation |
| Metric and geometric analysis | Completeness; total boundedness; compactness criteria; contractions; equicontinuity; metric measure spaces; Hausdorff measure/dimension | Fixed points, flows and approximation | F5 immediate |
| Measure and integration | Sigma-algebras; measures; outer measure; completion; integration; convergence; products; Fubini/Tonelli; signed measures; Radon–Nikodym; disintegration | Function spaces, probability, PDE | F5 prerequisite reconciliation |
| Functional analysis | Normed/Banach/Hilbert spaces; duality; weak topologies; compactness; Baire; Hahn–Banach; open mapping; closed graph; uniform boundedness; reflexivity | Core F5 bridge across domains | F5 immediate |
| Operator theory | Bounded/unbounded operators; adjoints; spectrum/resolvent; compact/Fredholm operators; spectral measures; functional calculus; semigroups; operator algebras | Dynamics, quantum theory, PDE | F5 immediate, advanced batches extend |
| Harmonic and complex analysis | Fourier/Laplace transforms; convolution; distributions; singular integrals; wavelets; harmonic functions; holomorphic functions; several complex variables; Riemann surfaces | Existing v0.19; spectral and PDE methods | F5 bridge; broad next lane |
| Special functions and asymptotics | Orthogonal polynomials; Bessel/Airy/hypergeometric functions; integral representations; differential equations; asymptotic expansions; saddle-point methods | ODE, spectra, transforms, numerical validation | Early source discovery |
| ODE and dynamical systems | Existence; uniqueness; continuation; dependence; linear systems; stability; invariant sets; periodic orbits; bifurcation; Hamiltonian dynamics; chaos | Core F5 flows and visual interrogation | F5 immediate |
| PDE and integral equations | Elliptic/parabolic/hyperbolic problems; weak solutions; Sobolev spaces; boundary traces; energy estimates; regularity; conservation laws; integral operators | Functional analysis and ODE evolution | Foundations admitted in F5; dedicated next packages |
| Variational and nonlinear analysis | Euler–Lagrange; direct method; lower semicontinuity; coercivity; degree theory; nonlinear fixed points; monotone operators; critical points; Gamma-convergence | Optimization, PDE, geometry | F5 interfaces; extend progressively |
| Differential geometry | Smooth manifolds; bundles; connections; curvature; geodesics; Riemannian comparison; symplectic/contact geometry; Lie groups; geometric flows | Existing v0.18 and ODE flows | Reconcile then deepen |
| Algebraic and differential topology | Fundamental groups; covering spaces; homology/cohomology; cup/cap products; exact sequences; de Rham; homotopy; characteristic classes; obstruction theory; cobordism; K-theory | PCT, forms, bundles and invariants | Broad next lane |
| Algebraic geometry | Commutative algebra; varieties; schemes; sheaves; divisors; cohomology; algebraic spaces; stacks; arithmetic geometry | Category theory and number theory | Dependency-led long-running lane |
| Probability and stochastic analysis | Conditional expectation; independence; laws of large numbers; CLT; martingales; Markov processes; Brownian motion; stochastic integration; SDEs; generators | Measure, semigroups and deterministic ODE | Reconcile v0.17 then deepen |
| Statistics and information | Estimation; sufficiency; exponential families; testing; Bayesian probability; entropy; information inequalities; coding | Probability, convexity and geometry | Independent lane with measure prerequisites |
| Numerical analysis and approximation | Conditioning; rounding; interpolation; quadrature; linear/nonlinear solvers; Krylov methods; ODE/PDE schemes; interval methods; a posteriori bounds | Executable and certified evidence | F5 exact/enclosure subset first |
| Optimization and control | Convex/nonconvex optimization; duality; variational inequalities; optimal control; controllability/observability; Hamilton–Jacobi–Bellman; Pontryagin principle | Existing convex corpus and F5 ODE | Early bridge lane |
| Mathematical physics | Analytical mechanics; fluid/continuum mechanics; quantum theory; statistical mechanics; relativity; scattering and inverse problems | Operator, geometry and PDE packages | Source discovery now; staged intake |
| Computation and algorithms | Automata; formal languages; computability/complexity; algebraic algorithms; symbolic computation; coding/cryptography; computational geometry | Executable contracts and discrete mathematics | Independent lane |
| Further structures | Tropical/non-Archimedean mathematics; fractal geometry; ergodic theory; noncommutative geometry; higher categories; derived structures | Scoped extensions of previous lanes | Register candidates; admit when sources/dependencies resolve |

## 5. Source research register

Access checks below occurred on 2026-09-17. `PAGE_VERIFIED` means the author/project/publisher page was opened; it does not mean every theorem, edition checksum, permission, or locator has been validated. `DISCOVERY` means catalog use only. Admission always pins the actual source bytes or repository revision. Free online access is not automatically permission to republish text.

| Key | Source and verified entry point | Intended contribution | Access/disposition |
|---|---|---|---|
| VN | Jan van Neerven, [Functional Analysis, arXiv v7](https://arxiv.org/abs/2112.11166v7) | Banach/Hilbert theory, Fredholm, forms, spectra, semigroups | PAGE_VERIFIED; author version; check artifact license before redistribution |
| TE | Gerald Teschl, [Ordinary Differential Equations and Dynamical Systems](https://www.mat.univie.ac.at/~gerald/ftp/book-ode/) | IVPs, linear systems, stability, dynamics | PAGE_VERIFIED; author-hosted edition permits personal download; metadata/locators by default |
| LR | Jiří Lebl, [Basic Analysis](https://www.jirka.org/ra/) | Existing F4 bridge, metric spaces and fixed points | PAGE_VERIFIED; version 6.3 listed; pin matching volume and source license |
| LD | Jiří Lebl, [Notes on Diffy Qs](https://www.jirka.org/diffyqs/) | Elementary ODE formulations and worked examples | PAGE_VERIFIED; inspect exact edition/license at ingestion |
| AX | Sheldon Axler, [Measure, Integration & Real Analysis](https://measure.axler.net/) | Measure, integration and function-space prerequisites | PAGE_VERIFIED; record book-specific license independently of LADR |
| HU | John Hunter, [PDE notes](https://www.math.ucdavis.edu/~hunter/pdes/pde_notes.pdf) | Sobolev, weak formulations, elliptic/evolution equations | PAGE_VERIFIED; notes acknowledge reliance on Evans; track that lineage |
| FN | Driscoll and Braun, [Fundamentals of Numerical Computation](https://fncbook.com/) | Approximation, ODE/BVP and numerical operator interfaces | PAGE_VERIFIED; pin content and code versions separately |
| ST | [Stacks Project](https://stacks.math.columbia.edu/about) | Commutative algebra and algebraic geometry with stable tags | PAGE_VERIFIED; pin repository revision plus permanent tags |
| HA | Allen Hatcher, [Algebraic Topology](https://pi.math.cornell.edu/~hatcher/AT/ATpage.html) | Fundamental groups, homology and homotopy | PAGE_VERIFIED; author edition and errata; source notice governs reuse |
| MY | J. P. May, [A Concise Course in Algebraic Topology](https://www.math.uchicago.edu/~may/CONCISE/ConciseRevised.pdf) | Additional topology routes, categorical and homological links | PAGE_VERIFIED; author-hosted PDF; no blanket redistribution assumption |
| RI | Emily Riehl, [Category Theory in Context](https://math.jhu.edu/~eriehl/context/) | Categories, universal properties, adjunctions | PAGE_VERIFIED; personal-use PDF terms; metadata/locators by default |
| KE | [Kerodon tags](https://kerodon.net/tags) | Higher categorical and homotopy-coherent structures | PAGE_VERIFIED; use tag plus revision, inspect license before extraction publication |
| HT | [Homotopy Type Theory book](https://homotopytypetheory.org/book/) | Type-theoretic foundations and homotopy | PAGE_VERIFIED; Creative Commons release; pin exact version marker/license |
| MI | J. S. Milne, [Course Notes](https://www.jmilne.org/math/CourseNotes/) | Algebra, number theory and geometry | PAGE_VERIFIED index; pin individual volume before statement intake |
| ET | Etingof et al., [Introduction to Representation Theory](https://math.mit.edu/~etingof/reprbook.pdf) | Representations and algebraic symmetry | PAGE_VERIFIED; inspect edition and notice |
| EC | Richard Stanley, [Enumerative Combinatorics](https://math.mit.edu/~rstan/ec/) | Enumerative and algebraic combinatorics | PAGE_VERIFIED index; distinguish available chapters and editions |
| NI | [NIST DLMF](https://dlmf.nist.gov/) | Special-function definitions, identities and parameter domains | PAGE_VERIFIED; equation identifiers and release version required |
| BV | Boyd and Vandenberghe, [Convex Optimization](https://web.stanford.edu/~boyd/cvxbook/) | Reconcile existing corpus; optimization bridges | PAGE_VERIFIED; avoid duplicate Source D intake |
| HY | Hank Yang, [Optimal Control and Estimation](https://hankyang.seas.harvard.edu/OptimalControlEstimation/) | Control/dynamical interfaces | PAGE_VERIFIED; pin chapter revision and license |
| AR | Arnold, [Ordinary Differential Equations, MIT Press](https://mitpress.mit.edu/9780262510189/ordinary-differential-equations/) | Soviet-school geometric ODE source candidate | Publisher entry verified; user's edition still required |
| AI | [AIM approved-textbook initiative](https://textbooks.aimath.org/) | Find additional algebra, analysis and discrete texts | DISCOVERY index; each book gets its own source record |
| RU | [Math.ru library](https://math.ru/lib/) | Russian-language bibliographic discovery | DISCOVERY index; no blanket scan-reuse permission inferred |

AMS Open Math Notes and CAPD's website could not be retrieved during this search. Retain them as discovery/tooling candidates, not verified source acquisitions. Some multi-query searches returned irrelevant results; those results are excluded. This atlas is a researched starting register, not an exhaustive literature search or completed corpus download.

Additional searches should cover author repositories, university course collections, publisher-author editions, arXiv versions, Russian-language catalogs, and references of accepted sources. A discovery record contains query/date, discovered URL, domain, reason for inclusion, access result and next concrete acquisition step. Do not ingest search snippets as theorem statements.

## 6. Soviet and Russian-language intake lane

The user has physical Soviet textbooks; their titles, editions and contents are not yet supplied. The following are candidate author/work families, not verified holdings or extracted declarations:

| Candidate family | Mathematical value to seek |
|---|---|
| Kolmogorov–Fomin | Real analysis, metric/linear spaces, measures and functional analysis |
| Kantorovich–Akilov; Lyusternik–Sobolev | Functional methods and applications |
| Akhiezer–Glazman | Hilbert-space operators and spectral theory |
| Gelfand–Shilov | Generalized functions and distributions |
| Gelfand–Fomin | Variational calculus |
| Arnold; Nemytskii–Stepanov | Geometric ODE, qualitative dynamics and mechanics |
| Pontryagin and collaborators | ODE, topology and optimal control; distinguish individual works |
| Krasnosel'skii and collaborators | Nonlinear operators, fixed points and integral equations |
| Ladyzhenskaya; Sobolev | PDE, function spaces, energy methods and fluids |
| Gnedenko–Kolmogorov; Khinchin | Probability, limit theorems and information |
| Aleksandrov; Postnikov | Topology and geometry |
| Shafarevich; Gelfand; Vilenkin | Algebra, geometry, representations and special functions |
| Smirnov; Fikhtengolts; Faddeev–Sominskii | Broad analysis, higher mathematics, algebra and problem corpora |

First intake material from the user's collection: title page, publication/translation page, table of contents, index, and selected theorem pages. Record Cyrillic names and exact title, transliteration aliases, edition, printing, translator, language and page mapping. Preserve original statement and translated statement as distinct identities linked by a reviewed translation relation. A translated edition is not an independent mathematical source for quorum or cross-tradition counts.

OCR must retain page references and correction history. Review signs, subscripts, quantifier order, inequalities, interval endpoints and hypotheses against the page image. Hash raw scan, OCR output, corrected transcription and normalized mathematical statement separately. Unresolved OCR/translation stays quarantined from semantic identity and evidence promotion. Public graph export includes permitted metadata, locators and attributable original summaries; scans/prose follow the exact source's permissions.

## 7. Intake contract and mathematical identity

Each declaration record must include: stable source ID; edition and artifact digest; statement locator; declaration kind; raw-statement digest where actual text was obtained; normalization version/digest; language; extraction method; review status; license/export policy; hypothesis list; ordered quantifiers; conclusion; source-declared dependencies; and unresolved references.

Missing fields are explicit states. Never generate a plausible theorem number, page, source hash or original-language title to fill a gap. Source-attested records can enter before executable witnesses exist. A catalog-only source or chapter anchor cannot count as a source-attested theorem.

Each canonical formulation must include ambient objects, fields/rings, topology/norm, finite/infinite dimension, regularity, compactness/completeness, boundary/initial conditions, quantifier order and permitted parameter dependence. Preserve source formulations alongside a separately authored normalized claim. A hash establishes byte identity, not mathematical correctness or source fidelity.

Alignment outcomes: exact formulation match; scoped overlap; implication/specialization; construction; mechanism; translation; related; unresolved. Each has a reviewed reason. Avoid collapsing Hilbert Riesz representation with measure representation, contraction mappings with tensor contraction, analytic open mapping with Banach open mapping, or finite-dimensional spectra with general operator spectra.

## 8. Dependency and batch acceptance

Batch preparation:

1. Inventory selected source sections and every numbered mathematical item; unnumbered items receive stable structural locators.
2. Compare candidates against the current amended graph and F1–F4 campaign manifests.
3. Record reuse/refinement/split/new decisions before mutating an active projection.
4. Resolve dependencies or retain typed external placeholders with visible wounds.
5. Publish reviewed declarations and justified relationships; attach evidence when available.
6. Reconstruct twice from pinned inputs and compare semantic artifacts.

Acceptance requires 100% accounting of the frozen selection, not 100% proof coverage. Report admitted, reused, split, rejected, pending-review and blocked items with reasons. No dangling reference may silently become a resolved proof dependency. Partial batches may be published as partial; a closed package requires every mandatory selected item resolved or an explicit manifest revision accepted before rerun.

Two source formulations are desirable for central concepts, but not an admission prerequisite. Measure mathematical-source lineage separately from author nationality, publication language, textbook count and translation count. Shared proofs and translations must not inflate independent evidence.

## 9. Interfaces to the joint layer

Use the four executable slots `eo`, `geo`, `pct`, `formal`; `NATURAL` remains provenance. PCT means Probe-Chain Transform, not a generic numerical test runner. ODE residual checks and interval solvers should have their own evidence types; PCT is attached only when an actual chain/probe correspondence is constructed.

The baseline implementation needs targeted extensions before F5 promotion:

- Joint enum specializes in geometry; general operator action, contraction fixed points and non-gradient ODE evolution need versioned types. Do not relabel every vector field as `GRADIENT_FLOW`.
- `compare_scopes` compares eight strings exactly. Use it as a legacy equality check, not an implication solver for hypotheses or parameter intervals.
- `verify_certificate_quorum` trusts status fields, accepts PCT references without checking B-levels, and does not replay formal results. F5 must validate artifacts and producer lineage before using its result for promotion.
- EO/GEO source-statement hashes may legitimately be equal when two independent witnesses prove the same statement. Independence belongs to derivation/producer/input lineage; equal statement hashes are not sufficient evidence of duplication, and unequal hashes are not proof of independence.
- Both schema `$id` values point to `google/mapeogeo`; correct ownership during a versioned schema change.
- Legacy joint schema allows `SCOPED_OVERLAP`. F5 must enforce mechanism/identity separation in its own producer and validator; a compatibility decoder may retain old records without generating new identity assertions.

These issues are scoped certificate-integration tasks. They must not stop the coverage/source catalog or ordinary declaration intake. Preserve historical artifacts and record active amendments rather than rewriting prior evidence as if it had always met the new contract.

## 10. Visual interrogation requirements

Every admitted record is navigable by subject, source, hypotheses, dependencies and evidence state. Visual summaries must expose their mathematical projection: dimension reduction, sampling, metric, coordinates and time horizon. Layout distance does not imply mathematical similarity.

Store future visualization descriptors now: object/claim ID, supported view, axes/coordinates, parameter domains, invariant overlays, certificate references and limitations. Examples: operator action on a unit ball; weak-vs-strong convergence; compactness failure; flow tubes; energy levels; spectral locations; chain/boundary diagrams. Building a general interactive UI is a separate project and cannot block source coverage.

## 11. Metrics and project outputs

Coverage dashboard axes: domains represented; selected/admitted statements; resolved prerequisite share; new versus reused canonical formulations; source lineage diversity; distinct proof routes; counterexamples; executable scopes; kernel-verified claims; certified mechanisms; and unresolved wounds. Each numerator has its own denominator. Keep historical `0/235` grounding as a named historical cohort; compute new active-cohort denominators rather than freezing 235 for an expanding graph.

Proposed implementation artifacts (not created by this design commit):

- `formal/coverage/source_registry_v0_22.json`: editions, acquisition state and export policies.
- `formal/coverage/domain_atlas_v0_22.json`: lanes, dependencies and coverage states.
- `formal/coverage/batches/*.json`: frozen section selections and dispositions.
- `formal/coverage/legacy_reconciliation_v0_22.json`: legacy/campaign-to-active mappings.
- `evidence/coverage/*`: extraction, reconciliation and acceptance receipts.
- `scripts/coverage_inventory.py`: read-only audit of the actual pinned input set.
- `scripts/coverage_batch_intake.py`: deterministic additive intake and amendment application.

First execution sequence: inventory and source pinning; F5 prerequisite reuse; functional analysis and ODE source intake in dependency order; selected executable contracts; versioned joint adapter; reconstruction/reporting. Continue the other subject lanes through the same intake contract. Publish source discovery promptly without presenting candidates as imported mathematics.

## 12. Design acceptance and limits

This design is ready when the companion F5 inventory covers topology prerequisites, functional analysis, operators, ODE existence/uniqueness/stability, certified flows and cross-domain links; source readiness is distinguished from research candidates; legacy interfaces are described accurately; and reviewers can assign independent implementation packages.

This specification does not certify the entire joint layer, claim exhaustive worldwide source discovery, ingest the user's unsupplied books, or report new mathematical test results. It establishes a repeatable route for growing coverage while making evidence limitations visible.
