# Wave 3 Canonicalization Adjudication: Shared Graph & PSMSL Substrate

**Status**: `W3_ADJUDICATED`  
**Date**: 2026-10-07  
**Scope**: Canonicalization of Graph (`mapeogeo.graph`) and PSMSL (`mapeogeo.psmsl`) Substrates  

---

## 1. Executive Rationale

The historical repository `NB11B/MAPEOGEO` contains multiple branches touching graph structures, mechanism joints, operator algebras, and latent-generator observability. In accordance with the governing invariant:

$$\boxed{\text{Nothing enters v2 because it is newer; it enters because it is canonical, traceable, and requalified.}}$$

we evaluated each historical branch on whether its mechanisms survived formal qualification, whether it preserved essential semantic boundaries, and whether its abstractions are strictly domain-neutral.

---

## 2. Graph Substrate Archaeology & Decisions

### 2.1 Evaluated Sources
- **`agent/e32-typed-parallel-decision-graph-spec` (`8035070`)**:
  Formulated formal normative contracts for typed parallel decision DAGs, port bindings, guards, execution roles, and transactional proposal/validation lifecycles.
- **`agent/joint-layer-v0-21` (`21dd869`)**:
  Formulated multi-view mechanism joints connecting structural views. Critically, it established the explicit hierarchy:
  $$\boxed{\texttt{CANDIDATE\_REPRESENTS} < \texttt{REPRESENTS} < \texttt{SAME\_SEMANTICS}}$$
  and banned asserting semantic identity (`SAME_SEMANTICS`, `EQUIVALENT_TO`) on structural joints without verified proof certificates.
- **`asymptotic-family-layer-v1` (`b403099`)**:
  Provided parameter-scaling families. Its generic relation aspects are subsumed into general graph invariant contracts, while asymptotic mathematical semantics remain in the mathematics domain adapter.

### 2.2 Canonical Decisions for `mapeogeo.graph`
1. **Structural Topology**: Adopt the typed DAG topology (`Node`, `Edge`, `NodeRegistry`, `EdgeContract`, `DecisionGraph`) from `e32`.
2. **Evidentiary Hierarchy**: Incorporate the joint-layer's fail-closed relation model (`RelationType`). Structural candidacy cannot masquerade as representation, and representation cannot masquerade as semantic identity.
3. **Transaction Lifecycle**: Implement graph mutations via strict transactions (`GraphTransaction`, `GraphSnapshot`, `GraphInvariant`):
   $$\text{proposal} \longrightarrow \text{validation} \longrightarrow \text{certificate} \longrightarrow \text{commit}$$
4. **Domain Neutrality**: The graph substrate has zero knowledge of theorems, physics, waveforms, or software systems.

---

## 3. PSMSL Substrate Archaeology & Decisions

### 3.1 Evaluated Sources
- **`psmsl-operator-algebra-v1` (`ac63dde`)**:
  Implemented linear operator algebra over finite dimensions, operator word composition ($T_2 \circ T_1$), commutator analysis ($[A, B] = AB - BA$), Frobenius commutator norms for parallel safety, and linear operator basis discovery.
- **`latent-generator-qualification-v1` (`3491b94`)**:
  Implemented forward projection ($y = Px$) and exact null-space linear inversion ($x = P^+ y + N z$), rigorously establishing that non-zero nullity ($n - r > 0$) prevents asserting source identification.
- **`latent-generator-observability-v2` (`2e12009`)**:
  Extended static projection to dynamic multi-step trajectory observability ($O = [C; CA; CA^2; \dots]$) and inverse reconstruction.

### 3.2 Canonical Decisions for `mapeogeo.psmsl`
1. **Mathematical Mechanics, Not Domain Claims**:
   Recover the algebraic mechanics of `psmsl-operator-algebra-v1` and `latent-generator-observability-v2` in pure numeric/linear terms.
2. **Boundary Between Observation and Inference**:
   $$\boxed{\text{observed quantity} \neq \text{inferred generator}}$$
   The API allows constructing `Observation` records and `LatentGenerator` instances with `status="unknown"` whenever nullity is non-zero or source identity is unproven.
3. **Strict Domain Insulation**:
   Zero physical claims (`force`, `energy`, `mass`, `field`, `sensor`, `physical conservation`) are permitted in `src/mapeogeo/psmsl/`. They belong strictly in `domains/physics/`.

---

## 4. Canonical Type Mapping

| Historical Source | Historical Artifact | Canonical v2 Type / Function | Destination Module |
|---|---|---|---|
| `e32` | `Node` (e32 contract) | `Node`, `NodeKind`, `NodeRole` | `mapeogeo.graph.node` |
| `e32` | `Edge` (port binding) | `Edge`, `EdgeContract` | `mapeogeo.graph.edge` |
| `v0.21` joint layer | `MechanismJoint.relationship` | `RelationType` | `mapeogeo.graph.relation` |
| `e32` | `DecisionGraph` | `DecisionGraph` | `mapeogeo.graph.decision_graph` |
| `e32` | Snapshot / transaction | `GraphSnapshot`, `GraphTransaction`, `GraphInvariant` | `mapeogeo.graph.transaction` |
| `psmsl-v1` | `InformationSemantics` | `InformationSemantics` | `mapeogeo.psmsl.algebra` |
| `psmsl-v1` | `OrderingSemantics` | `OrderingSemantics` | `mapeogeo.psmsl.algebra` |
| `psmsl-v1` | Matrix ops / commutator | `TransformationOperator`, `OperatorWord` | `mapeogeo.psmsl.operator` |
| `latent-v1` | `linear_inverse` / `P` | `StateProjection`, `InverseProjection` | `mapeogeo.psmsl.projection` |
| `latent-v1/v2`| `InverseResult` / generator | `LatentGenerator`, `Observation`, `ObservableSignature` | `mapeogeo.psmsl.latent` |

---

## 5. Wave 3 Falsification & Exit Gates

The migration fails if:
1. Any graph relation strength collapses or automatically promotes (e.g. `CANDIDATE_REPRESENTS` treated as `REPRESENTS`).
2. Any uncertified equality is admitted.
3. Graph transaction allows committing without passing registered invariants.
4. Physical vocabulary (`force`, `energy`, etc.) appears in `src/mapeogeo/psmsl/`.
5. Non-deterministic serialization occurs across repeated runs.
6. Any historical comparison produces a `REGRESSION`.
