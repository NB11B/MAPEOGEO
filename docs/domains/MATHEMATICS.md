# Mathematics Domain Adapter

The Mathematics Domain Adapter (`mapeogeo.domains.mathematics`) interfaces mathematical deduction and theorem proving with the UoW Kernel.

---

## 1. Domain Semantics

In the mathematics domain:
- **Requirements ($Q \in \Omega$)**: Conjectures, target theorems, or algebraic equations requiring proof or reduction.
- **Machinery Nodes ($M \in G$)**: Certified definitions, axioms, lemmas, and derivation rules.
- **Deficiencies ($D$)**: Unproven goal assertions or missing inferential bridges.
- **Witness Certificates**: Deductive step traces, formal substitution logs, or proof checker certificates.

---

## 2. Key Capabilities & Behavioral Reproducibility

1. **Deficiency Conservation**: Exactly tracks reduction of open proof obligations as lemmas are admitted.
2. **Terminal Refusal**: Refuses to loop indefinitely when candidate inferences fall below marginal utility threshold $\tau_J = 1.5$.
3. **80-Problem Clean-Room Trajectory**: Fully reproduces the historical mathematics research trajectory across arithmetic, algebra, and number theory with zero regressions.

---

## 3. Module Structure

- `adapter.py`: `MathematicsAdapter` implementing canonical adapter contract.
- `proof.py`: Proof tree representation and deduction step verifiers.
- `ast_utils.py`: Symbolic expression representation and term rewriting rules.
