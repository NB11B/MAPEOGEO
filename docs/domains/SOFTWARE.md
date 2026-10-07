# Software Domain Adapter

The Software Domain Adapter (`mapeogeo.domains.software`) interfaces software synthesis, refactoring, and automated testing with the UoW Kernel.

---

## 1. Domain Semantics

In the software domain:
- **Requirements ($Q \in \Omega$)**: Functional specifications, test suites, API contracts, or bug reports.
- **Machinery Nodes ($M \in G$)**: Certified functions, classes, modules, or verified refactoring patches.
- **Deficiencies ($D$)**: Failing test cases, unmet type constraints, or unimplemented functions.
- **Witness Certificates**: Deterministic test execution traces, static analysis reports, and lint passes.

---

## 2. Epistemic Separation from Mathematics and Physics

While software modules expose signatures similar to mathematical operations, their truth criteria are distinct:

$$\boxed{\text{Signature Equality} \not\implies \text{Cross-Domain Equivalence}}$$

Software verification is empirical against executable specifications (tests and formal types) rather than deductive derivations (mathematics) or physical measurement compatibility (physics).

---

## 3. Module Structure

- `adapter.py`: `SoftwareAdapter` orchestrating software tasks, dependency resolution, and test evaluation.
- `certification.py`: `SoftwareCertificationBoundary` enforcing regression boundaries and type invariants.
- `machinery.py`: Software machinery definitions (`SoftwareMachinery`, `SoftwareEvidence`).
- `test_runner.py`: Deterministic, isolated test execution and output capture.
- `patch.py`: Structured code modifications and AST transformation representations.
