"""Transformation operators, operator words, and representation transforms.

Provides algebraic representations of mappings X -> Y between state representations.
"""

from __future__ import annotations

from dataclasses import dataclass

from mapeogeo.psmsl.algebra import (
    InformationSemantics,
    Matrix,
    OrderingSemantics,
    analyze_information,
    analyze_ordering,
    matmul,
)


@dataclass(frozen=True)
class TransformationOperator:
    """Discrete linear transformation operator acting on state vectors."""

    operator_id: str
    matrix: Matrix

    def __post_init__(self) -> None:
        if not self.operator_id:
            raise ValueError("operator_id must be non-empty")
        if not self.matrix or not self.matrix[0]:
            raise ValueError("matrix must be non-empty and non-ragged")
        n = len(self.matrix[0])
        if any(len(row) != n for row in self.matrix):
            raise ValueError("matrix must have uniform row lengths")

    @property
    def codomain_dim(self) -> int:
        return len(self.matrix)

    @property
    def domain_dim(self) -> int:
        return len(self.matrix[0])

    def compose(self, inner: TransformationOperator) -> TransformationOperator:
        """Compose this operator after inner: (self o inner)(x) = self(inner(x))."""
        composed_mat = matmul(self.matrix, inner.matrix)
        composed_id = f"({self.operator_id}o{inner.operator_id})"
        return TransformationOperator(operator_id=composed_id, matrix=composed_mat)

    def information_semantics(self, tol: float = 1e-10) -> InformationSemantics:
        """Evaluate information preservation properties."""
        return analyze_information(self.matrix, tol=tol)

    def ordering_semantics(
        self, other: TransformationOperator, tol: float = 1e-10
    ) -> OrderingSemantics:
        """Evaluate commutation with another operator."""
        return analyze_ordering(self.matrix, other.matrix, tol=tol)

    def commutes_with(self, other: TransformationOperator, tol: float = 1e-10) -> bool:
        """Check if self and other commute."""
        return self.ordering_semantics(other, tol=tol).commutes


@dataclass(frozen=True)
class OperatorWord:
    """Sequential sequence of transformation operators executed from right to left."""

    word_id: str
    operators: tuple[TransformationOperator, ...]

    def __post_init__(self) -> None:
        if not self.operators:
            raise ValueError("OperatorWord must contain at least one operator")
        # Validate dimensional chain
        for i in range(len(self.operators) - 1):
            curr_op = self.operators[i]
            next_op = self.operators[i + 1]
            if curr_op.domain_dim != next_op.codomain_dim:
                raise ValueError(
                    f"Dimensional mismatch in word at step {i}: "
                    f"op[{i}].domain={curr_op.domain_dim} != "
                    f"op[{i + 1}].codomain={next_op.codomain_dim}"
                )

    def evaluate(self) -> TransformationOperator:
        """Compute the composite product operator across the word."""
        res = self.operators[-1]
        for op in reversed(self.operators[:-1]):
            res = op.compose(res)
        return res

    def is_reorderable(self, i: int, j: int, tol: float = 1e-10) -> bool:
        """Check if operators at positions i and j commute."""
        return self.operators[i].commutes_with(self.operators[j], tol=tol)


@dataclass(frozen=True)
class RepresentationTransform:
    """Declared transformation between two representation spaces X -> Y."""

    source_space: str
    target_space: str
    operator: TransformationOperator

    def apply(self, vector: tuple[float, ...]) -> tuple[float, ...]:
        """Apply the transformation to a coordinate vector."""
        if len(vector) != self.operator.domain_dim:
            raise ValueError(
                f"Vector dimension {len(vector)} does not match "
                f"operator domain {self.operator.domain_dim}"
            )
        mat = self.operator.matrix
        return tuple(
            sum(mat[i][j] * vector[j] for j in range(len(vector))) for i in range(len(mat))
        )
