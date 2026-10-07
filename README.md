# MAPEOGEO v2: Canonical Unit-of-Work Architecture

$$\boxed{\operatorname{Ability}_t(Q) = \operatorname{ReachableCertifiedWork}(Q \mid G_t)}$$

`MAPEOGEOv2` is the canonical production implementation of the Unit-of-Work (UoW) paradigm, establishing an autonomous, domain-neutral control kernel coupled with modular domain adapters.

---

## 1. Mathematical Formalism & Invariants

At any transition step $t$, the system ability over required work $Q$ is strictly defined as the reachable certified work conditioned on certified state $G_t$.

The execution kernel is governed by the formal 9-tuple:

$$\boxed{\mathcal{K} = (\mathcal{M}_6, \Omega, \rho, G, D, P, U, C, A)}$$

- **$\mathcal M_6$**: 6-coordinate work grammar $(\Delta, I, W, \sigma, \Pi, \Gamma) + \circ$.
- **$\Omega$**: Universal requirement space.
- **$\rho$**: Deficiency extraction mapping $(\Omega \times G) \to D$.
- **$G$**: Certified state graph $G_t = (V_t, E_t)$.
- **$D$**: Deficiency distribution $D_t = \Omega \setminus \operatorname{Reach}(G_t)$.
- **$P$**: Prospective planner generating candidate packages $\mathcal C_t$.
- **$U$**: Utility model evaluating marginal efficiency $J = \Delta A / \text{cost}$.
- **$C$**: 4-gate certification boundary (dependencies, witnesses, invariants, reproducibility).
- **$A$**: Autonomous state transition engine enforcing deficiency conservation ($\Delta D = 0$) and stopping rules ($\max J < 1.5 \implies \texttt{REFUSE}$).

---

## 2. Repository Roles & Custody Boundary

| Repository | Role | Custody & Lineage |
|---|---|---|
| **`NB11B/MAPEOGEO`** | **Historical Research & Provenance** | Historical research laboratory, full branch lineage, frozen experiment provenance, and scientific custody archive (frozen at commit `74e51bd`). |
| **`NB11B/MAPEOGEOv2`** | **Canonical Production Architecture** | Clean Git ancestry bootstrapped from initial commit `d664f8c`. Contains canonical, clean-roomed, and qualified components ported under strict provenance tracking. |

---

## 3. Strict Three-Layer Architecture

$$\boxed{\text{UoW Kernel} \longrightarrow \text{Domain Adapters} \longrightarrow \text{Experiments / Qualification}}$$

1. **UoW Kernel Layer (`src/mapeogeo/kernel/`)**: Domain-neutral capability and transition engine. Strictly forbidden from importing any domain adapter.
2. **Domain Adapters Layer (`src/mapeogeo/domains/`)**: Modular adapters for target fields (`mathematics`, `physics`, `software`). Adapters translate domain requirements into kernel contracts; the kernel never adapts to domains.
3. **Subsystem Layers**:
   - `grammar`: 6-coordinate work algebra and composition.
   - `graph`: Relational topology and transactional dependency graphs.
   - `routing`: Path admissibility and work dispatch.
   - `proof`: Proof certificates and independent falsification gates.
   - `psmsl`: Phase-space macro-state language and operator algebra.

---

## 4. Architectural Invariants & Verification

Automated architectural tests (`tests/architecture/`) enforce key constraints:
- **Directional Isolation**: `mapeogeo.kernel` $\not\rightarrow$ `mapeogeo.domains`.
- **Cross-Domain Isolation**: Domain adapters are mutually isolated (no imports across math, physics, software).
- **Namespace Hygiene**: No historical research tokens in canonical code.
- **Fail-Closed Certification**: Adversarial tests verify $N_{\rm false\ acceptance} = 0$.
- **Deterministic Replay**: Subprocess replay proves $H(R_1) = H(R_2)$.

---

## 5. Development & Testing

```powershell
# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Run full test suite (124 tests)
pytest

# Static typing and linting
mypy src tests
ruff check .
ruff format --check .
```
