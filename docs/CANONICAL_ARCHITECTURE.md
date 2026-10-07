# MAPEOGEO — Canonical Architecture Map

## Purpose
MAPEOGEO is a work-directed mathematical representation and execution system. It maps equivalent mathematical representations, chooses routes according to requested work, executes only certified primitives, preserves uncertainty/domain boundaries, and returns durable evidence.

Architectural rule: represent the mathematics needed to perform the work; preserve enough structure to certify the result; do not compute unrelated consequences merely because they are available.

## 1. PSMSL state / representation plane
PSMSL represents state in coordinates appropriate to the work: scalar/vector, complex/imaginary, irrational or symbolic scale, geometric position/orientation/scale/projection, sparse deltas, family/growth coordinates, and explicit unknown/null-space components.

Representation is not authority. A mathematically exact projection may discard structure required by later work.

## 2. MAPEOGEO equivalence graph
Nodes are mathematical representations or typed objects. Edges are transformations/operators with explicit semantics. Core families include geometry <-> linear algebra, complex <-> planar rotation, projection <-> matrix/operator form, differential geometry <-> linear operator decomposition, graph/incidence/hypergraph transforms, and finite object <-> family/asymptotic state.

An edge may be mathematically valid without being executable. Execution requires a registered implementation and contract.

## 3. Geometric operator plane
For q(t)=A(t)[cos(theta(t)),sin(theta(t))]^T,

dq/dt = dA/dt*r_hat + A*dtheta/dt*theta_hat.

This separates scale change from rotation. MAPEOGEO maps those components back to corresponding linear-algebra operators and generalizes the pattern to higher-dimensional rotation, projection, modal coordinates, complex/RF state, and latent generators.

## 4. Latent-generator / inverse-observation plane
Given y(t)=P q(t), the system may recover a generator, a minimal generator family, or an equivalence class. It must never identify an actor/source not determined by observation.

Outputs distinguish identifiable generator components, latent scalar/operator parameters, null/equivalence spaces, underdetermined components, and uncertainty.

Forward reconstruction is the certification boundary: q_hat -> P -> y_hat, with y_hat required to match y within work tolerance.

## 5. Work router
Route ordering is certification > domain validity > work accuracy/tolerance > cost.

A route R is admissible only when Gamma(R) is certified, the input is in Domain(R), and u_W(R) <= tau_W. Cost optimization occurs only inside the admissible set.

## 6. Execution contracts
Executable primitives carry mathematical certification, domain predicates, uncertainty/error propagation, cost, backend identity, and resource compatibility. Initial composition uses conservative additive absolute error; the architectural target is transformation-specific propagation U_out=P_e(U_in).

## 7. Derived/composed work
Certified primitives may compose into routes not authored in advance. Composition preserves contracts and cannot promote uncertified edges.

## 8. Family / quantified / asymptotic plane
Object computation is distinct from family proof: P(x), forall x P(x), forall x exists y P(x,y), eventually P(n), and P(n)=Omega(f(n)) are different work shapes.

For positive P and f, PSMSL may use z(n)=log(P(n)/f(n)). Finite z values are FINITE_EVIDENCE. CERTIFIED eventual/asymptotic state requires a theorem/proof certificate.

## 9. Proof operators
Proof-shape routing includes WITNESS, CONSTRUCTOR, UNIVERSAL, mixed FORALL/EXISTS, INVARIANT, EXTREMAL, EVENTUAL, ASYMPTOTIC_BOUND, and canonical/exhaustive generation. Learned/model proposals become reusable edges only after deterministic verification.

## 10. UoW execution/certification plane
Execution follows propose -> execute -> certify/falsify -> durable state -> next work.

For wide workloads the preferred unit is a frontier/wave, not one orchestration object per candidate:
F_t -> expand -> wide evaluation -> deterministic reduction/canonicalization -> F_(t+1).
Independent cells inside the transition should be parallelized as widely as hardware permits. The wave transition is the durable UoW boundary.

## 11. Certificate / authority plane
Artifacts may include implementation certificates, endpoint-contract evidence, witness/coloring certificates, canonicalization certificates, augmentation ledgers, exhaustion manifests, external theorem authority digests, and Merkle/journal roots. Proposal confidence never substitutes for these artifacts.

## Cross-domain qualification surface
The work-router lineage covers measured PA/RF operator data, vector/3-D geometry, vibration/modal work, electrical power, control, graph/incidence/combinatorial work, and formal proof obligations. These share machinery; they are not separate architectures.

## Erdős campaign role
The Erdős work is a stress/qualification branch, not the definition of MAPEOGEO. It exposed quantified proof shapes, family/asymptotic state, constructor operators, finite-evidence boundaries, canonical generation, exhaustive coverage certificates, frontier-wave execution, and solver/authority separation.

## Repository lineage/status

### Qualified / merged baseline
The default branch contains the fail-closed work router, measured PA qualification lineage, and earlier GFYProof bridge work.

### Implemented in stacked research lineage
PRs #12 through #36 continue the architecture in dependency order: multidomain routing; power/control; invariant/derived routes; executable contract loading/registry/composition; validity/error contracts; formal/quantified/asymptotic machinery; proof-object/exhaustive-generation qualification; and UoW/certificate production machinery.

These are implemented on stacked branches and are not represented as merged to the default branch.

### Active MAPEOGEO frontier
Latent-generator recovery:
measured effect -> minimal latent generator/equivalence class -> geometric differential components -> corresponding linear-algebra operators -> forward reconstruction -> tolerance certificate.

## Architectural invariants
1. Equivalent representation is not equivalent authority.
2. A valid transformation may still lose work-relevant information.
3. Unknown/underdetermined components remain explicit.
4. Finite evidence cannot certify a universal/asymptotic theorem.
5. Probabilistic proposal cannot become authoritative without deterministic certification.
6. Cost is optimized only after certification, domain, and tolerance gates.
7. Wide independent work executes in parallel inside deterministic UoW transitions.
8. Every capability promotion leaves replayable evidence.


## 12. Knowledge-acquisition / canonical reconciliation plane

MAPEOGEO now includes a production-qualified external mathematical knowledge
ingestion path.

Qualified OpenAI/math integration status:

    OPENAI/MATH SOURCE + CANONICAL INTEGRATION QUALIFIED

The qualified production artifact contains approximately:

- 4.225 million graph nodes;
- 4.559 million graph edges;
- 3,762,712 OpenAI/math lexical records;
- a 215-object MAPEOGEO canonical registry.

Published artifact SHA-256:

    716a83398d878dd916548d20e68d17b98b35a32499d7209cff17f35a54d9a8d3

The integration is not a raw corpus attachment. Imported OpenAI/math records
are connected to canonical MAPEOGEO objects through a fail-closed reconciliation
relation:

    CANDIDATE_REPRESENTS

This relation is intentionally weaker than established semantic relations:

    CANDIDATE_REPRESENTS != REPRESENTS != SAME_SEMANTICS.

A candidate correspondence therefore supplies searchable evidence and a
promotion target, but it cannot satisfy a certified mathematical transformation
route, semantic-equivalence requirement, or proof obligation.

Promotion requires individual mathematical evidence under the existing
certificate/authority machinery.

The independent verifier rejects at least these invalid promotions:

- treating a candidate correspondence as established representation;
- asserting semantic equivalence without promotion evidence;
- targeting a noncanonical object;
- originating a candidate edge outside the imported corpus authority.

This makes external mathematical knowledge acquisition monotone with respect
to authority: ingestion can add candidates without silently strengthening the
certified graph.

### Relationship to PSMSL and work routing

PSMSL/MAPEOGEO may search candidate correspondences when discovering possible
representations, operators, proofs, or routes. Candidate edges may therefore
inform proposal/discovery work.

However, route certification must exclude candidate-only edges whenever the
requested work requires established semantics.

The intended lifecycle is:

    external lexical/source record
      -> CANDIDATE_REPRESENTS
      -> mathematical review / deterministic evidence
      -> REPRESENTS
      -> stronger semantic proof where justified
      -> SAME_SEMANTICS.

Each transition is an authority promotion and must leave replayable evidence.

This plane separates graph-scale knowledge acquisition from mathematical
authority and allows MAPEOGEO to grow its external knowledge surface without
weakening its fail-closed execution semantics.
