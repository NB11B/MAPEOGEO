# Wave F5 — functional analysis, operator theory and ordinary differential equations

Date: 2026-09-17. Status: reviewable engineering design; no F5 ingestion, executable implementation or certification is claimed yet.

Design baseline: NB11B/MAPEOGEO commit `21dd869c214ad48c3eb0ce4e8784a253a75055f0`, branch `agent/joint-layer-v0-21`. Proposed expansion version: v0.22. Companion: [mathematical coverage atlas](2026-09-17-mathematical-coverage-atlas-design.md).

## 1. Purpose and deliverables

Make substantial source-grounded mathematics available to MAPEOGEO while the existing engineering layer evolves. Wave F5 deepens and unifies the historical topology, analysis, measure, algebra and geometry material, adds a substantial functional-analysis/operator-theory corpus, and treats ordinary differential equations—existence, uniqueness, stability and certified solution flows—as a first-class intake pillar.

Deliver a cumulative active graph, exact source and formulation registries, explicit dependencies and mechanisms, selected executable witnesses, visible missing evidence, and visualization descriptors. Accept mathematical source coverage independently of executable certificate coverage. Do not constrain intake to a small equal-sized collection of demonstrations.

A Wave F5 release is a finite set of accepted package manifests. Each manifest states its selected source sections and exact item denominator. Unbounded future scope belongs to the atlas. A release with incomplete mandatory selections is labeled partial; useful complete subpackages may be released independently.

## 2. Packages and dependency order

| Package | Scope | Required predecessors | Independent acceptance |
|---|---|---|---|
| F5.0 | Source discovery, pinning and baseline reconciliation | Pinned repository; atlas | Yes; emits inventory and mappings |
| F5A | Topology/metric/measure prerequisites and function spaces | F5.0; relevant F4 formulations | Yes |
| F5B | Structural functional analysis | F5A and linear algebra | Yes |
| F5C | Operator and spectral theory | F5B; complex scalars where needed | Yes; advanced operators separately scoped |
| F5D | ODE IVPs, linear systems, continuation and flows | F5A; contraction and Grönwall; F5B as relevant | Yes; does not wait for all F5C |
| F5E | Stability, qualitative dynamics and boundary-value problems | F5D; selected F5C | Yes |
| F5F | Exact/symbolic/enclosure evidence and visual descriptors | Selected F5B–F5E claims | Yes for each fixed contract set |
| F5G | Joint adapters, cumulative graph and acceptance reporting | Source batches; integration checks for promoted evidence | Yes; graph intake can precede certificate promotion |

Do not make advanced functional analysis an artificial prerequisite for elementary finite-dimensional ODE intake. Relevant dependency chains include Banach contraction to Picard iteration; Baire to uniform boundedness/open mapping; Hilbert geometry to projection/adjoints; compact operators to regular Sturm–Liouville spectral problems; and Grönwall to flow sensitivity and residual bounds.

## 3. Mathematical inventory

The codes below identify planning families, not final canonical IDs. Each semicolon-separated mathematical item is a candidate for a distinct definition, theorem or construction row. Split further whenever scopes or source statements differ. Reuse existing canonical IDs after reconciliation; new namespace proposal: `canonical:fa:*`, `canonical:operator:*`, `canonical:ode:*`. Never replace existing IDs merely for naming consistency.

### A. Topology, metric structure and function spaces

| Family | Required inventory | Critical scope distinctions |
|---|---|---|
| A01 | Topology; bases/subbases; neighborhood systems; open/closed sets; closure/interior/boundary; continuity; homeomorphism | General topology versus metric topology |
| A02 | Subspace/product/quotient topology; initial topology; continuous images; topological embeddings | Product versus box topology; quotient map versus bijection |
| A03 | Hausdorff/regular/normal spaces; first/second countability; separability; Lindelöf property | Preserve separation conventions and hypotheses |
| A04 | Compactness; local compactness; sequential compactness; countable compactness; connectedness; path connectedness | Metric equivalences must not be generalized to every space |
| A05 | Nets; filters; convergence; uniform structures; uniform continuity | Sequential tests alone do not characterize all topological phenomena |
| A06 | Metrics/pseudometrics; completeness; Cauchy sequences; completion; total boundedness; compact iff complete and totally bounded | Distinguish boundedness from total boundedness |
| A07 | Baire category; nowhere dense/meager sets; complete-metric Baire theorem | Category is not measure |
| A08 | Norms/seminorms; equivalent norms; finite-dimensional norm equivalence; normed spaces; Banach spaces; closed subspaces; quotient norms | Quotient by a closed subspace for a normed quotient; finite dimension explicit |
| A09 | Inner products; Cauchy–Schwarz; parallelogram identity; Hilbert completeness; orthogonality; orthonormal systems/bases | Real/complex scalar conventions; algebraic versus Hilbert basis |
| A10 | Sequence spaces c00, c0 and ell-p; continuous-function spaces C(K), C0(X), Cb(X); sup norms | Compact K; topology on X; completeness; p range |
| A11 | Lp spaces; almost-everywhere equivalence classes; essential supremum; Hölder/Minkowski; Riesz–Fischer completeness | Measure hypotheses and endpoint p=1/infinity kept separate |
| A12 | Pointwise/uniform/Lp/weak convergence; equicontinuity; Arzelà–Ascoli; Stone–Weierstrass | No automatic interchange of convergence modes |
| A13 | Dense embeddings; finite-dimensional subspaces; Riesz lemma; failure of compactness of infinite-dimensional unit balls | Exact scope of relative compactness |
| A14 | Weak derivatives; distributions; test functions; Sobolev examples and norms | Initial bridge definitions; general PDE regularity is a later batch |

### B. Structural functional analysis

| Family | Required inventory | Critical scope distinctions |
|---|---|---|
| B01 | Bounded linear maps; continuity iff boundedness; operator norm; composition; completeness of L(X,Y) | Y complete for the operator space completeness result |
| B02 | Continuous dual; bidual; evaluation embedding; annihilators; dual norms | Algebraic dual versus continuous dual |
| B03 | Hahn–Banach extension; dominated extension; separating functionals; norming functionals | Real/complex versions and sublinear domination |
| B04 | Geometric separation; supporting hyperplanes; Minkowski functionals; polars | Closed/convex/open and strict-separation hypotheses |
| B05 | Uniform boundedness; Banach–Steinhaus; resonance counterexamples | Pointwise bounded family on Banach domain |
| B06 | Open mapping; bounded inverse; closed graph theorem | Banach domain/codomain; bijective versus surjective |
| B07 | Weak and weak-star topologies; weak lower semicontinuity of norm; weak convergence of sequences | Weak-star requires a specified predual/dual pairing |
| B08 | Banach–Alaoglu; weak-star compact unit ball; separable-predual metrizability | Compactness versus sequential compactness; named topology |
| B09 | Reflexivity; weak compactness of unit ball; reflexivity of Lp for 1<p<infinity; uniformly convex examples | General endpoint claims rejected |
| B10 | Hilbert projection theorem; orthogonal decomposition; Hilbert Riesz representation; adjoints | Closed subspaces; convention for complex inner products |
| B11 | Bessel inequality; Parseval; orthonormal expansions; least-squares projection | Complete orthonormal system versus arbitrary system |
| B12 | Measure representation of functionals on C(K)/C0(X); regularity of representing measures | Separate canonical family from Hilbert Riesz theorem |
| B13 | Mazur lemma; convex combinations; weak closure of convex sets; Krein–Milman | Locally convex topology and compact convex hypotheses |
| B14 | Schauder bases; unconditional convergence; locally convex and Fréchet spaces | Do not assert every Banach space has a Schauder basis |
| B15 | Banach contraction theorem; iterative error estimates; fixed-point dependence | Nonempty complete invariant domain and q<1 |
| B16 | Brouwer/Schauder fixed points; compact mappings | Distinct from contractions and uniqueness; broader batch may remain source-only |

### C. Operator and spectral theory

| Family | Required inventory | Critical scope distinctions |
|---|---|---|
| C01 | Banach algebras; identity/invertibility; Neumann series; resolvent set; spectrum | Complex unital setting for standard nonempty-spectrum theorem |
| C02 | Point/continuous/residual/approximate-point spectra; spectral radius; resolvent identity | Definitions vary: freeze conventions |
| C03 | Finite-rank and compact operators; compact integral operators; closure properties | Matrix examples do not prove general compactness |
| C04 | Riesz–Schauder theory; Fredholm alternative; Fredholm operators; kernel/cokernel; index | Range closure and finite-dimensional defect hypotheses |
| C05 | Symmetric/self-adjoint/normal/unitary/positive operators; bounded adjoints | Unbounded symmetric is not automatically self-adjoint |
| C06 | Compact self-adjoint spectral theorem; eigenspace projections; positive square roots | Compact spectrum versus arbitrary spectral measure |
| C07 | Bounded normal spectral theorem; continuous/Borel functional calculus; spectral measures | Source-general admission can precede executable realization |
| C08 | Unbounded operators; dense domains; closed/closable operators; graph norms; extensions | Operator identity includes domain, not just expression |
| C09 | Sesquilinear forms; coercivity; Lax–Milgram; form-associated operators | Uniform coercivity and scalar conventions |
| C10 | Strongly continuous semigroups; generators; exponential bounds; resolvent connection; Hille–Yosida | Full hypotheses/source variants required; not every bounded family is C0 |
| C11 | Unitary groups; Stone theorem; Duhamel formula; variation of constants | Unitary group generator convention and domain |
| C12 | Multiplication/shift/convolution operators; integral kernels; Fourier multipliers | Function space and boundary conditions determine spectrum |
| C13 | Singular values; compact-operator approximation; conditioning; pseudospectra | Numerical enclosures must distinguish pseudospectrum from spectrum |
| C14 | Regular Sturm–Liouville operators; Green functions; resolvent compactness; orthogonal eigenfunction expansions | Separated self-adjoint boundary conditions; singular endpoints separate |

### D. ODE existence, uniqueness and solution structure

| Family | Required inventory | Critical scope distinctions |
|---|---|---|
| D01 | IVP; order; autonomous/nonautonomous systems; first-order reduction; solution and maximal interval | State/time domain, initial data and parameter range |
| D02 | Separable equations; integrating factors; exact equations; scalar linear equations; Bernoulli/Riccati examples | Division by zero and lost equilibria must be tracked |
| D03 | Integral formulation; Picard operator; successive approximations; contraction proof | Invariant function-space ball and time-step conditions |
| D04 | Picard–Lindelöf; local Lipschitz; uniform local bounds; local existence/uniqueness | Local versus global; finite-dimensional versus Banach-space versions |
| D05 | Peano existence; compactness construction; nonuniqueness examples; Carathéodory solutions | Peano's finite-dimensional theorem is not a general Banach-space theorem |
| D06 | Grönwall integral/differential estimates; comparison principles; continuous dependence | Integrability, sign and coefficient assumptions |
| D07 | Maximal solutions; continuation; escape from compact subsets; finite-time blow-up | Boundary escape need not mean norm divergence on a proper open domain |
| D08 | Global existence under growth bounds; invariant regions; a priori estimates | Local Lipschitz alone does not guarantee global existence |
| D09 | Parameter dependence; differentiable dependence; variational equations; sensitivity matrices | Joint regularity of vector field and parameters |
| D10 | Linear systems; fundamental matrices; matrix exponential; variation of constants; Wronskian/Abel identity | Nonautonomous solution uses a two-time evolution operator |
| D11 | Periodic linear systems; Floquet multipliers; monodromy; Liouville determinant formula | Period and coefficient regularity explicit |
| D12 | Autonomous local flow; maximal flow domain; group law on common domain; semiflow; evolution process | Global group law requires completeness; nonautonomous law is two-time |
| D13 | Complex ODE; power-series solutions; regular singular points; Frobenius method | Analytic coefficient scope and resonance exceptions |
| D14 | Boundary-value problems; shooting; Green operator; Sturm comparison and oscillation | Existence/uniqueness can fail at eigenvalues |

### E. Stability and qualitative dynamics

| Family | Required inventory | Critical scope distinctions |
|---|---|---|
| E01 | Equilibria; positive/negative invariant sets; orbits; omega-limit sets | Forward/backward existence domains |
| E02 | Lyapunov/asymptotic/exponential stability; attraction; basin | Definitions retain epsilon/delta and time quantifiers |
| E03 | Linear stability; spectral abscissa; Jordan blocks; matrix exponential growth; transient growth | Imaginary-axis eigenvalues and nonnormality require care |
| E04 | Nonlinear linearization; indirect Lyapunov method; hyperbolic equilibria | Zero-real-part spectrum is generally inconclusive |
| E05 | Lyapunov functions; orbital derivative; positive definiteness; invariant sublevel sets | Local versus global; radial unboundedness when used |
| E06 | LaSalle invariance principle; dissipativity; absorbing sets | Compact positively invariant set and largest invariant zero-derivative subset |
| E07 | Stable/unstable manifolds; Hartman–Grobman; center-manifold interface | Topological conjugacy is not differentiable conjugacy |
| E08 | Phase planes; nullclines; limit cycles; Poincaré sections/maps; return-time regularity | Transversality and domain of return |
| E09 | Poincaré–Bendixson; Bendixson–Dulac | Planar hypotheses cannot be dropped |
| E10 | Periodic orbit stability; Floquet transverse stability; invariant manifolds | Autonomous orbit has a neutral time-shift direction |
| E11 | Saddle-node/transcritical/pitchfork/Hopf bifurcations; normal forms | Nondegeneracy, parameter transversality and symmetry |
| E12 | Gradient flows; energy decay; Hamiltonian flows; symplectic structure; conservation laws | Dissipation versus conservation; not every flow is gradient |
| E13 | Integrability; action-angle variables; perturbation; averaging; KAM interface | Source-led advanced batches; no finite-trace claim of KAM proof |
| E14 | Discrete maps; symbolic dynamics; horseshoes; chaos; Lyapunov exponents | Numerical positive exponent is evidence, not automatic chaos certification |

### F. Approximation and validated flows

| Family | Required inventory | Critical scope distinctions |
|---|---|---|
| F01 | Consistency; local truncation error; global error; stability; Euler and Runge–Kutta methods | Numerical accuracy is not by itself a proof of enclosure |
| F02 | Stiffness; implicit steps; absolute stability regions; adaptive stepping | Solver termination versus mathematical validity |
| F03 | Interval arithmetic; directed rounding or exact rational intervals; inclusion functions | Every elementary operation must enclose its true range |
| F04 | Interval Picard inclusion; interval Jacobians; Lipschitz/logarithmic-norm bounds | All points in the declared box/time interval, not a sample grid |
| F05 | Taylor models; remainder bounds; wrapping control; validated continuation | Any chosen backend needs an auditable error model |
| F06 | Residual-to-solution bounds; initial uncertainty; sensitivity tubes | Reference solution existence and tube validity explicit |
| F07 | Event localization; transversal crossings; interval root isolation; invariant-region certificates | Tangencies and unproven crossings yield unresolved results |
| F08 | Exact solutions; polynomial/rational/exponential families; conservation checks; negative controls | Each symbolic identity checked under its domain restrictions |

The full inventory above is an extensible selection framework. It is deliberately broader than the first set of executable contracts. Every family enters the coverage queue; admission depends on source resolution, not whether a convenient numerical demonstration exists.

## 4. Source strategy and acquisition gates

Primary F5 sources:

- [Van Neerven, Functional Analysis v7](https://arxiv.org/abs/2112.11166v7): functional analysis through Fredholm, forms and semigroups.
- [Teschl, Ordinary Differential Equations and Dynamical Systems](https://www.mat.univie.ac.at/~gerald/ftp/book-ode/): IVPs, linear systems, flows, stability and dynamics. His online edition's personal-use conditions do not authorize uploading the book to this repository.
- [Lebl, Basic Analysis](https://www.jirka.org/ra/) and [Notes on Diffy Qs](https://www.jirka.org/diffyqs/): continuity from F4 plus alternate ODE formulations. Two works by one author are not automatically independent corroboration.
- [Axler, Measure, Integration & Real Analysis](https://measure.axler.net/): function-space and integration prerequisites.
- [Hunter, PDE notes](https://www.math.ucdavis.edu/~hunter/pdes/pde_notes.pdf): Sobolev and weak-form/operator bridges; retain acknowledged source lineage.
- [Driscoll–Braun, Fundamentals of Numerical Computation](https://fncbook.com/): numerical approximation and ODE/BVP interfaces; a validated solver requires additional mathematical enclosure arguments.
- Soviet collection: Arnold and the functional-analysis/operator/ODE families listed in the atlas. Exact editions await the user's supplied pages; they are not blocking primary-source intake.

Pin source artifact checksum, edition/version, permitted export mode and per-statement locator before declaring an item source-attested. The source hashes and theorem numbers are outputs of acquisition, not values invented by this design. Errata corrections create new statement identities with supersession edges. Full source text is exported only under an applicable license; locator-plus-hash and original structured formulations are the default for restricted texts.

## 5. Canonicalization and the cumulative active graph

Read historical alignments plus current v0.20 amendments and F1–F4 manifests. Emit a reconciliation ledger mapping every selected F5 item to an existing ID or a new formulation ID, with a reason. Split composite objects such as a node containing both a space definition and a theorem about that space without deleting its historical identity.

A cumulative graph build must include admitted F3/F4 declarations and formulations even when their current campaigns only emit evidence. All edges resolve against the final active node registry. Evidence references that only resolve inside a campaign manifest are materialized or remain explicitly external; neither case is silently counted as a proof path.

Maintain separate counts for declaration instances, canonical formulations, conceptual families, source lineages, dependency edges, mechanism joints and certified claims. Do not add domain counts across overlapping inventories. Do not equate presence of a source with complete coverage of that source.

## 6. Formulation and evidence contract

Every mathematical claim binds its source identities, normalized statement, ambient space, scalar field, topology/norm, dimension, operator domains, regularity, quantifiers, parameters, time interval and exceptional cases. Operator domains and boundary conditions are part of identity. A source statement, its translation and a curator restatement have distinct hashes and relations.

Carry F4 evidence distinctions forward. Add a separately named `VALIDATED_ENCLOSURE` evidence kind through a versioned extension; do not store it as exact rational equality or as general formal proof. Legacy readers receive a conservative bounded-evidence projection plus an explicit kind field in the new registry. No unseen legacy enum is assumed to support this new kind.

Source-attested statements with no execution remain useful records. Certified counterexamples bind the exact overbroad claim they refute. `FORMAL_GENERAL` requires a compiled theorem, its checked type, current source/formulation mapping, toolchain/build artifact and permitted axiom audit; a boolean field is insufficient.

Certificate independence means separately derived witnesses under the same claim and compatible scope. Equal source-statement hashes are expected; witness payload hashes, producer IDs, input ancestry, code revisions and replay receipts establish what was actually computed. Different hash strings alone never establish independence. Shared low-level arithmetic libraries are permitted and disclosed; deriving both semantic outputs from one expected-result table is prohibited.

PCT is optional and remains the Probe-Chain Transform. A numerical residual is not a B4 chain complex. Inapplicability is an attachment receipt state; map it conservatively to an absent/refused legacy view with a reason because the v0.21 certificate schema has no `INAPPLICABLE` enum value.

## 7. Initial executable contract suite

These fixtures are a mandatory bounded validation set for the evidence subsystem, not a limit on source intake. Record exact inputs, scope and expected invariant before running.

| Contract | Positive mathematical instance | Required falsification |
|---|---|---|
| Q01 contraction iteration | T(x)=x/2+1 on closed invariant interval [0,2]; fixed point 2; geometric error | q=1 gives insufficient contraction evidence; noninvariant domain rejected |
| Q02 finite-dimensional adjoint | Rational matrices under declared real inner product; inner-product pairing identity | Transpose/index/sign mutation rejected; complex conjugation case separate |
| Q03 orthogonal projection | Rational full-rank basis; P squared=P; P transpose=P; residual orthogonality | Rank-deficient basis and oblique projection mislabeled orthogonal rejected |
| Q04 Neumann inverse bound | Rational matrix with induced norm <1; truncated series residual plus tail bound | Norm >=1 cannot use this sufficient certificate, even if inverse exists |
| Q05 spectral decomposition | Rational diagonal/symmetric cases with exact eigenpairs and projectors | Dropped eigenspace or nonnormal operator under orthogonal claim rejected |
| Q06 Picard self-map | y'=y, y(0)=1, t in [0,1/4], sup-norm ball of radius 1/2 about the constant function 1; M=3/2, L=1 | Enlarged step violating self-map or q<1 cannot certify |
| Q07 nonuniqueness boundary | y'=2 sqrt(abs(y)), y(0)=0; zero solution and delayed-square family | A unique-solution assertion must fail while existence remains valid |
| Q08 continuation/blow-up | y'=y squared, y(0)=1; y=1/(1-t) for t<1 | A certificate crossing t=1 rejected; local evidence not globalized |
| Q09 autonomous flow composition | Rational solution map x/(1-tx) on its connected maximal time interval | Composition outside common existence domain rejected |
| Q10 nonautonomous evolution | y'=t y; U(t,s)=exp((t squared-s squared)/2) | Incorrect one-parameter time-homogeneous law rejected |
| Q11 linear/Lyapunov stability | A=diag(-1,-2), V=x transpose x; derivative strictly negative off zero | Wrong sign, wrong domain or non-positive-definite V rejected |
| Q12 nonhyperbolic distinction | x'=-x cubed versus x'=x cubed: same zero linearization | Definitive stability inferred solely from zero eigenvalue rejected |
| Q13 transient growth | Upper triangular A=[[-1,10],[0,-2]] | Negative eigenvalues must not imply Euclidean norm decreases at every instant |
| Q14 conservative geometry | Harmonic oscillator; energy constant; planar rotations | Energy-growth mutation and false asymptotic-attraction claim rejected |
| Q15 residual enclosure | Polynomial approximate solution of y'=y with exact residual supremum bound | Missing initial error or underestimated residual prevents acceptance |
| Q16 invariant interval | Logistic equation x'=x(1-x), initial interval within [0,1] | Claimed certificate includes neither full vector-field bound nor valid enclosure |
| Q17 event enclosure | x'=1, x(0)=0; transversal event x=1 at t=1 | Tangential-event example cannot reuse transversal certificate |
| Q18 regular BVP | -u''=f on [0,1], Dirichlet endpoints; polynomial exact case | Boundary mismatch and singular operator parameter rejected |

For Q06, T maps the ball into itself since hM=3/8<=1/2 and is a contraction since hL=1/4<1. This is a function-space argument with an exact bound; evaluating finitely many iterates alone is not the proof. Infinite-dimensional theorem nodes such as Hahn–Banach may remain source-attested or formal-only; do not manufacture a finite proxy and label it a general certificate.

## 8. Certified flow certificate

Initial supported computational class: finite-dimensional real ODEs with polynomial/rational vector fields on compact rational boxes and certified nonzero denominator bounds, followed by explicitly validated elementary-function extensions. Other ODEs remain admissible as source mathematics with an unsupported-execution state.

Required certificate fields: claim and vector-field identity; state dimension; initial time and initial enclosure; parameter box; time slab; state tube; regularity/Lipschitz evidence; self-map/existence evidence; uniqueness evidence when claimed; arithmetic backend/version/rounding policy; step ledger; remainder/residual bound; stopping reason; all input and output hashes; and replay checker ID.

For an approximate path y-hat with residual r=y-hat'-f(t,y-hat), certified residual norm <=R, initial error <=e0 and Lipschitz constant L>=0, a checked comparison gives

    ||y(t)-y-hat(t)|| <= exp(L*(t-t0))*e0 + R*(exp(L*(t-t0))-1)/L,

with the L=0 expression e0+R*(t-t0). The bound is valid only on a certified region containing the compared paths, with existence established; checking only the approximate trajectory is insufficient. Exponentials require validated bounds, not ordinary floating-point evaluation rounded after the fact.

Each slab must prove enclosure on the entire continuous interval. Adjacent slabs propagate all initial uncertainty and parameter uncertainty. Endpoint samples alone are insufficient. On failure, return `NOT_CERTIFIED` with a reason such as width exhaustion, singular denominator, missing regularity, unverified rounding, or domain exit. Failure to certify is not proof that a solution fails to exist.

Do not claim every flow tube is a group action. Autonomous local flows satisfy composition only where both sides exist. Nonautonomous systems use U(t,s) and U(t,r) composed with U(r,s)=U(t,s). Semiflows allow forward time; a globally invertible flow requires additional hypotheses. Flow-law evidence and solution enclosure are distinct receipts.

## 9. Joint and scope integration

Current reusable types include `SPECTRAL_PROJECTION`, `VARIATIONAL_COUPLING`, `MONOTONICITY_FORMULA` and `BOUNDARY_DUALITY`, where their actual role contracts apply. Register versioned additions for `OPERATOR_ACTION`, `FIXED_POINT_CONSTRUCTION`, `EVOLUTION_FLOW`, `LINEARIZATION` and `CONTINUOUS_DEPENDENCE` before emitting these records. Proposed names are design decisions, not existing enum values. A generic ODE is not `GRADIENT_FLOW`; rotation is a mandatory negative typing case.

Keep the eight legacy scope strings as a compatibility summary. The new scope contract adds structured space IDs, field, topology, dimension bounds, hypotheses, operator domain, norm, interval/box bounds, quantifier dependencies and exclusions. Comparison returns `EQUAL`, `CHECKED_RESTRICTION`, `INCOMPATIBLE` or `UNRESOLVED`. Only exact equality or an explicit checked restriction permits transport. Text similarity and arbitrary theorem implication are not supported scope comparators.

Before promoted F5 certificates, address these observed baseline limitations in an isolated integration commit:

1. Resolve certificate subjects and all feet against active statement/formulation identities.
2. Replay evidence; validate digest format/content, producer ancestry and version.
3. Check PCT B-level, actual chain structure and relevant map residuals, not just view_ref.
4. Resolve formal verification to a real build/theorem/axiom receipt.
5. Compare per-witness scopes; compute quorum rather than trusting serialized quorum_count.
6. Require nonclaims and reject unknown keys/statuses at the appropriate schema boundary.
7. Correct schema ownership URLs; version new enums without rewriting old fixture expectations.
8. Prevent mechanism producers from minting `SAME_SEMANTICS` or `SCOPED_OVERLAP`; identity alignment remains a separate reviewed process.

The baseline certificate CLI seeds sample digest strings and the current quorum implementation checks supplied fields. Treat these as fixture behavior, not evidence that F5 witnesses can be promoted without the new checks. This observation is based on source inspection, not a fresh execution of the baseline tests.

## 10. Visual interrogation acceptance

Store reusable descriptors and compact reference fixtures alongside mathematical records. Required views: norm balls/operator images; spectral locations; projections/orthogonal residuals; contraction iterates/error envelopes; flow direction fields; exact versus numerical trajectories; validated tubes; equilibria and invariant sets; Lyapunov contours; parameter dependence; and a dependency graph connecting the supporting claims.

Every view shows source/claim IDs, scope, parameter ranges, evidence kind and exclusions. A 2D projection of a higher-dimensional state is labeled as such. Sampled trajectories cannot be styled as certified tubes. Changing initial data, coefficients, time horizon or projection invalidates a receipt unless its certified parameter scope includes the change. Structural graph layout, phase-space geometry and proof-dependency diagrams are distinct display modes.

Frontend implementation is not an F5 intake gate. The descriptor and fixture contracts ensure the corpus can later be interrogated visually without retrofitting provenance.

## 11. File and integration map

Existing files to inspect/reuse at the pinned baseline:

- `scripts/reconstruct_pipeline.py`: sequential stages through `v0.21`; add explicit F5 targets later.
- `scripts/wave_f4_campaign.py` and `formal/wave_f4_*`: evidence-tier and quantifier patterns.
- `formal/mathematical_integrity_amendments_v0_20.json` and `formal/foundation_mathematical_amendments_v0_20.json`: active corrections.
- `mapeogeo/models/view_slots.py`: legacy view serialization.
- `mapeogeo/analysis/scope_comparator.py`: eight-string equality only.
- `scripts/correspondence_certificate.py`: legacy generator and supplied-field quorum.
- `mapeogeo/pct/attach.py`: PCT attachment bridge; preserve its actual semantics.
- `schema/mapeogeo-joint.schema.json`, `schema/mapeogeo-certificate.schema.json`, `formal/joint_type_registry_v0_21.json`: versioned compatibility work.

Proposed new implementation files:

| Path | Responsibility |
|---|---|
| `formal/wave_f5/source_registry.json` | Exact editions, retrieval/export policy and acquisition receipts |
| `formal/wave_f5/batches/*.json` | Frozen selected-section inventory and disposition |
| `formal/wave_f5/formulations.json` | Structured canonical formulations and reconciled IDs |
| `formal/wave_f5/dependencies.json` | Typed source references and prerequisites |
| `formal/wave_f5/contracts.json` | Preregistered executable/formal contract scopes |
| `formal/wave_f5/relations.json` | Reviewed mathematical mechanisms and candidate status |
| `formal/wave_f5/visualizations.json` | View descriptors and claim bindings |
| `schema/wave-f5-*.schema.json` | Source/formulation/evidence/flow schemas |
| `mapeogeo/wave_f5/intake.py` | Deterministic source-record and graph integration |
| `mapeogeo/wave_f5/scopes.py` | Structured equality and checked restriction |
| `mapeogeo/wave_f5/certificates.py` | Replay, lineage, scope and quorum validation |
| `mapeogeo/wave_f5/operators.py` | Scoped exact operator checks |
| `mapeogeo/wave_f5/ode.py` | IVP and symbolic/flow contract checks |
| `mapeogeo/wave_f5/enclosures.py` | Validated arithmetic and solution-tube checker |
| `scripts/wave_f5_intake.py` | Batch entry point and cumulative graph outputs |
| `scripts/wave_f5_campaign.py` | Contract suite, mutations and evidence receipts |
| `scripts/generate_wave_f5_report.py` | Claims and denominators computed from receipts |
| `tests/wave_f5/` | Provenance, scope, operators, ODE, enclosures and integration tests |
| `artifacts/wave_f5_v0_22/` | Reconstructed graph, ledgers and computed results |
| `.github/workflows/wave-f5-v0-22.yml` | Planned replay and claim-specific gates |

No new implementation file in this table is claimed to exist. The following execution outline is a task decomposition for the later test-first plan; it is not a completed implementation plan with invented APIs.

## 12. Test-first execution slices and commits

| Slice | RED behavior to demonstrate | GREEN outcome | Suggested commit subject |
|---|---|---|---|
| 0 inventory | Campaign-only IDs omitted from cumulative inventory are detected | Complete classified legacy/campaign ledger | `feat(f5): inventory active mathematical coverage` |
| 1 source records | Wrong edition, unresolved locator or curator hash passed as source hash rejected | Exact pinning, extraction and review receipts | `feat(f5): add source-bound intake registry` |
| 2 formulations | Weak/norm or local/global variants falsely merged | Structured scope and canonical reconciliation | `feat(f5): preserve formulation and scope distinctions` |
| 3 prerequisites | Anchor counted as theorem; missing dependency silently resolved | F5A records and explicit dependency wounds | `feat(f5): deepen topology and function-space prerequisites` |
| 4 functional/operator intake | Distinct Riesz/open-mapping claims collapsed | F5B/F5C source batches and relations | `feat(f5): ingest functional analysis and operator theory` |
| 5 ODE intake | Existence promoted to uniqueness; finite-dimensional Peano generalized | F5D/F5E source batches and counterexamples | `feat(f5): ingest ODE well-posedness and stability` |
| 6 replay integration | Fake formal boolean, PCT reference or aliased witness certifies | Real artifact-bound certificate validator | `fix(f5): require replayed scoped correspondence evidence` |
| 7 exact evidence | Q01–Q14 arithmetic/domain mutations accepted | Independent EO/GEO bounded witnesses | `feat(f5): add exact operator and ODE contracts` |
| 8 enclosure evidence | Q15–Q18 residual/rounding/domain defects accepted | Continuous-slab enclosure and event receipts | `feat(f5): certify scoped solution enclosures` |
| 9 graph and views | Missing feet, stale parameters or duplicate source rows survive | Cumulative graph and honest visual descriptors | `feat(f5): integrate functional mechanisms and view metadata` |
| 10 reporting | Supplied counts or skipped formal build reported as pass | Computed report, reconstruction and CI | `ci(f5): gate intake and evidence claims independently` |

At implementation time, create failing tests in the corresponding `tests/wave_f5/test_<slice>.py` before the minimal code; run `python -m pytest tests/wave_f5 -q` as focused integration. Proposed future reconstruction targets: `wave_f5_intake` for source graph and `wave_f5` for intake plus declared campaigns. These targets do not exist at the pinned baseline. All new CLIs must accept explicit output roots; tests must not overwrite tracked source/evidence files.

## 13. Acceptance matrix

| Gate | Required evidence | Failure consequence |
|---|---|---|
| Source integrity | Every admitted source-attested row has pinned edition, real locator and verified source identity | Quarantine affected row/batch |
| Selection accounting | Every item in frozen selection has exactly one disposition | Batch cannot claim complete |
| Reconciliation | Every admitted declaration maps to reviewed formulation or explicit unresolved state | No fabricated identity edge |
| Graph integration | All resolved endpoints exist; campaign-to-graph mapping explicit; no duplicate active IDs | Graph build fails |
| Mathematical scope | Mandatory weak/strong, finite/infinite, domain and local/global negative controls | Affected promotion fails |
| Evidence replay | Every claimed executable/formal artifact rechecked; aliases and missing receipts rejected | Certificate stays provisional/rejected |
| ODE correctness | Q01–Q18 under their exact scopes, including analytical negative controls | Relevant evidence package fails |
| Enclosures | Full-slab inclusion, uncertainty propagation and validated arithmetic | No certified-tube label |
| Formal claims | Kernel build, theorem type/source mapping and axiom audit | Formal claim absent/blocked, never silently passed |
| Determinism | Two clean output roots produce identical semantic graphs/receipts | Reproducibility gate fails |
| Historical lineage | Protected graph digest recorded; generated differences categorized | Report actual drift and cause; never hide with test edits |
| Reporting | Counts derived from registries; historical and active cohorts distinguished | Report generation fails |

The historical v0.11 graph digest remains `409a648d8563bc4a027dc3dc29fc53722d11bc489462a0f3d1f71bd4f272544d`. Preserve it by additive active projection. Legacy artifact checks are one gate among the mathematical acceptance checks; do not let cosmetic regeneration differences consume the source expansion effort.

Replay without a Lean toolchain can pass source/executable gates and report formal work as blocked, but cannot issue a release containing new `FORMAL_GENERAL` claims. Runtime limits must be calibrated against batch size, hardware and contract selection before confirmation; do not inherit the earlier six-second budget for a substantially larger corpus.

Discrimination testing must include hard negatives and legitimate equivalent formulations. Universal off-diagonal rejection is not a mathematical objective: two distinct labels can describe the same scoped theorem, and one concept can have several representations. Use a preregistered truth set distinguishing equivalence, specialization, related mechanisms and incompatibility. Digest diversity measures serialization, not semantic correctness.

## 14. Completion and handoff

First source release: selected F5A/B/D batches admitted and reconciled, dependencies visible, graph reconstructs. Operator/stability batches and executable contracts can follow as independently accepted extensions of F5. The initial source manifest, not this family list alone, determines exact release completeness.

Full first F5 campaign: all selected mandatory source batches accounted for; Q01–Q18 evaluated under declared evidence kinds; versioned joint integration passes; cumulative graph and visual descriptors generated; reports make pending advanced mathematics explicit. No minimum universal proof percentage is invented to force evidence inflation.

Subsequent atlas lanes include harmonic/PDE/variational analysis, deeper topology/geometry, probability/stochastics, representation/algebra/number theory, and numerical/control mathematics. User-supplied Soviet editions join through the same source contract as they arrive. Neither source discovery nor the local joint-layer development is blocked by a missing physical-book title page.

The immediate review is of these two concrete designs. A subsequent implementation plan should turn the slices into exact per-file RED/GREEN commands and reviewed fixtures after the design is accepted; production implementation remains separate from this documentation branch.
