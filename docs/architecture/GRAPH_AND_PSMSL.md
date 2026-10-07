# Relational Graph & PSMSL Subsystem Architecture

The Relational Graph (`mapeogeo.graph`) and Phase-Space Macro-State Language (`mapeogeo.psmsl`) form the foundational shared state and representation substrate of MAPEOGEO v2.

---

## 1. Graph Subsystem (`mapeogeo.graph`)

The graph subsystem provides a certified, transactional dependency network for machinery nodes and capability signatures.

### 1.1 Mathematical Model
The state graph is a directed acyclic graph (DAG):

$$G_t = (V_t, E_t)$$

Where:
- $V_t$ is the set of certified machinery nodes and capability signatures.
- $E_t \subseteq V_t \times V_t$ represents direct dependency and enablement edges.

### 1.2 Core Invariants
1. **Acyclicity**: $\forall v \in V_t, \; v \not\to^+ v$. Cycles in dependency resolution trigger `CyclicDependencyError`.
2. **Certified Transaction Boundaries**: Graph mutations only occur via certified transactions. If any verification step fails, the transaction is aborted and state rolls back fail-closed.
3. **Immutable Query Interface**: Reading operations (reachability evaluation, path exploration) operate over immutable snapshots.

---

## 2. PSMSL Subsystem (`mapeogeo.psmsl`)

Phase-Space Macro-State Language (PSMSL) provides an operator algebra for describing macro-states, observations, and generator dynamics.

### 2.1 Separation of Observation and Inferred Generators
A central tenet of the PSMSL substrate is the strict boundary between:
- **Empirical Observations ($O$)**: Directly recorded evidence or measurements.
- **Inferred Generators ($\Gamma$)**: Hypothesized generative models or structural laws explaining observations.

$$\boxed{O \neq \Gamma}$$

An observation cannot be retroactively modified to fit a generator, nor can a generator be asserted as fact without explicit witness certificates.

### 2.2 Operator Algebra
PSMSL defines symbolic operations over macro-states:
- **Projection ($\pi$)**: Mapping high-dimensional micro-states to discrete macro-features.
- **Conjunction ($\wedge$)**: Co-occurrence of macro-state invariants.
- **Transition ($\delta$)**: Admissible state transformations governed by certified machinery.
