# Physics Domain Adapter

The Physics Domain Adapter (`mapeogeo.domains.physics`) interfaces physical modeling, observation processing, and empirical law discovery with the UoW Kernel.

---

## 1. Epistemic Separation

A foundational distinction enforced by the physics adapter is:

$$\boxed{\text{Mathematical Admissibility} \neq \text{Physical Establishment}}$$

A model may be internally self-consistent and mathematically admissible, but unless grounded in physical observation and dimensional consistency, it cannot be admitted as physical machinery.

---

## 2. Null-Space and Observability

The physics adapter explicitly accounts for partial observability:
- **Null-Space Ambiguity**: When observational data lacks sufficient rank to uniquely resolve generative sources, the adapter returns `CertificationStatus.AMBIGUOUS`. It strictly avoids asserting fictitious source identification.
- **Exact Recovery**: Exact parameter and source identification is admitted if and only if observational rank proves complete observability.

---

## 3. Physical Falsifiers

The adapter implements four active falsification checks:
1. **Dimensional Homogeneity**: Incompatible unit combinations trigger immediate failure.
2. **Conservation Laws**: Breaches of energy, momentum, or charge conservation reject candidates.
3. **Overparameterization**: Excess degrees of freedom without empirical support are penalized and rejected.
4. **Unsupported Source Identification**: Unbacked causal claims fail Gate 2 witness verification.

---

## 4. Module Structure

- `adapter.py`: `PhysicsAdapter` managing physical state and requirements.
- `certification.py`: `PhysicalCertificationBoundary` executing dimensional, conservation, and observational falsification gates.
- `state.py`: Physical state and phase-space snapshot representations.
- `observation.py`: Empirical observation records, sensor feeds, and noise models.
- `generator.py`: Generative physical laws and dynamic evolution models.
- `system_id.py`: System identification routines with null-space detection.
