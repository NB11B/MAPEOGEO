# Unit-of-Work Control Kernel Architecture

The Unit-of-Work (UoW) Kernel (`mapeogeo.kernel`) is the domain-neutral execution and capability engine of MAPEOGEO v2.

---

## 1. Mathematical Formalism: The 9-Tuple $\mathcal K$

The kernel is formally specified by the nine-tuple:

$$\boxed{\mathcal K = (\mathcal M_6, \Omega, \rho, G, D, P, U, C, A)}$$

Where:
- $\mathcal M_6$: Literal 6-coordinate work grammar $(\Delta, I, W, \sigma, \Pi, \Gamma) + \circ$.
- $\Omega$: Universe of required work specifications and problem statements.
- $\rho$: Deficiency extraction mapping from requirements and current certified state to active deficiencies: $\rho: (\Omega \times G) \to D$.
- $G$: Certified state graph of available machinery nodes $G_t = (V_t, E_t)$.
- $D$: Deficiency distribution representing required work minus reachable certified work: $D_t = \Omega \setminus \operatorname{Reach}(G_t)$.
- $P$: Prospective planner proposing admissible candidate machinery packages $\mathcal C_t = \{M_1, M_2, \dots\}$.
- $U$: Utility evaluation function computing marginal efficiency $J(M) = \widehat{\Delta A}(M) / \operatorname{Cost}(M)$.
- $C$: 4-gate kernel certification boundary verifying candidate admissibility.
- $A$: Autonomous state transition engine updating $G_t \to G_{t+1}$ or invoking terminal refusal $\texttt{REFUSE}$.

---

## 2. Fundamental Operative Invariants

### 2.1 The Ability Equation
At any discrete transition step $t$, the system ability over required work $Q$ is strictly defined as:

$$\boxed{\operatorname{Ability}_t(Q) = \operatorname{ReachableCertifiedWork}(Q \mid G_t)}$$

### 2.2 Deficiency Conservation Law
No work may silently appear or disappear during state transitions. For any transition from state $G_t$ to $G_{t+1}$ with acquired machinery $M$:

$$\boxed{D_{\rm prior} - D_{\rm resolved} = D_{\rm posterior} \iff \Delta D = 0}$$

Any deviation triggers `DeficiencyConservationError` fail-closed.

### 2.3 Rational Refusal Stopping Criterion
Given prospective candidates evaluated with efficiency $J$, the engine acquires the top candidate if and only if its prospective efficiency meets the threshold $\tau_J = 1.5$:

$$\boxed{\max_{M \in \mathcal C_t} J(M) \ge \tau_J \implies \texttt{TRANSITION} \quad \text{else} \quad \texttt{REFUSE}}$$

---

## 3. Kernel Subsystem Modules

The kernel is structured under `src/mapeogeo/kernel/`:

- `state.py`: Immutable, hashable `KnowledgeState` capturing certified machinery nodes, active signatures, and witness certificates.
- `deficiency.py`: `WorkRequirement`, `DeficiencyDistribution`, and `DeficiencyExtractor` enforcing deficiency conservation.
- `machinery.py`: `MachineryNode` and `MachineryCandidate` representing atomic and composite execution units.
- `planning.py`: `ProspectivePlanner` estimating reachability expansion and projected capability unlock.
- `utility.py`: `UtilityModel` computing $J = \Delta A / \text{cost}$ and marginal efficiency ordering.
- `certification.py`: `CertificationBoundary` evaluating Gate 1 (dependencies), Gate 2 (witnesses), Gate 3 (invariants), and Gate 4 (reproducibility).
- `transition.py`: `StateTransitionEngine` executing atomic transitions with conservation assertions and stopping rules.
- `reach.py`: `ReachabilityMatrix` mapping certified nodes to satisfied signatures.
- `spec.py`: Formal specification of the 9-tuple and kernel components.
- `serialization.py`: Deterministic, byte-for-byte serialization and deserialization.

---

## 4. Strict Domain Neutrality

The kernel maintains absolute domain neutrality:
$$\boxed{\texttt{src/mapeogeo/kernel/} \;\not\rightarrow\; \texttt{src/mapeogeo/domains/}}$$
Static AST inspection forbids any import from `mapeogeo.domains`. Domain concepts (mathematical lemmas, physical sensors, software APIs) exist strictly in domain adapters that translate into domain-neutral kernel contracts.
