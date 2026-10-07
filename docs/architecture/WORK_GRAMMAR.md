# 6-Coordinate Work Grammar Architecture

The Work Grammar (`mapeogeo.grammar`) defines the formal algebra of work representations within MAPEOGEO v2.

---

## 1. Formal Specification: $\mathcal M_6$

The literal six-coordinate work grammar is defined as:

$$\boxed{\mathcal M_6 = (\Delta, I, W, \sigma, \Pi, \Gamma) + \circ}$$

Where:
- **$\Delta$ (Difference / Delta)**: The explicit structural delta between an antecedent state and a proposed posterior state.
- **$I$ (Intent)**: The formal objective or target state description intended by the unit of work.
- **$W$ (Work Descriptor)**: The operational transformation, procedure, or action sequence executing the work.
- **$\sigma$ (Signature)**: The capability or functional signature exposed by the completed work.
- **$\Pi$ (Proof Obligation)**: The verification conditions, invariant assertions, or certificates necessary for admission.
- **$\Gamma$ (Context / Generator)**: The environmental frame, premises, background machinery, or generative assumptions under which the work is valid.
- **$\circ$ (Sequential Composition)**: The associative composition operator enabling chaining of atomic work units:
  $$(M_1 \circ M_2) \circ M_3 = M_1 \circ (M_2 \circ M_3)$$

---

## 2. Invariants & Algebraic Properties

1. **Non-Triviality**: Every coordinate is non-null. A partial unit of work is uncertifiable.
2. **Associativity of Composition**: Sequential composition preserves execution semantics independent of grouping.
3. **Identity Element**: The empty work unit $e \in \mathcal M_6$ acts as an identity under composition:
   $$M \circ e = e \circ M = M$$
4. **Signature Compatibility**: Composition $M_1 \circ M_2$ is valid if and only if the antecedent requirements of $M_2$ are satisfied by the output signature of $M_1$.

---

## 3. Implementation Structure

Under `src/mapeogeo/grammar/`:
- `coordinate.py`: Strongly typed coordinate classes (`DeltaCoordinate`, `IntentCoordinate`, `WorkCoordinate`, `SignatureCoordinate`, `ProofCoordinate`, `ContextCoordinate`).
- `unit.py`: The `WorkUnit` dataclass encapsulating the six coordinates.
- `composition.py`: Sequential composition operator $\circ$ with compatibility checking.
- `validation.py`: Syntactic and structural validation ensuring fail-closed rejection of malformed work units.
