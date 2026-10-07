"""State projections and linear inverse reconstruction.

Implements forward projection y = Px and exact null-space inverse reconstruction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from mapeogeo.psmsl.algebra import Matrix, Vector, rref_solve


@dataclass(frozen=True)
class StateProjection:
    """Forward projection matrix mapping latent state vectors to observable vectors."""

    projection_id: str
    matrix: Matrix

    def __post_init__(self) -> None:
        if not self.projection_id:
            raise ValueError("projection_id must be non-empty")
        if not self.matrix or not self.matrix[0]:
            raise ValueError("Projection matrix must be non-empty")
        n = len(self.matrix[0])
        if any(len(r) != n for r in self.matrix):
            raise ValueError("Projection matrix must have uniform columns")

    @property
    def observable_dim(self) -> int:
        return len(self.matrix)

    @property
    def latent_dim(self) -> int:
        return len(self.matrix[0])

    def project(self, state: Vector) -> Vector:
        """Compute observable vector y = P x."""
        if len(state) != self.latent_dim:
            raise ValueError(
                f"State dimension {len(state)} does not match "
                f"projection latent dimension {self.latent_dim}"
            )
        return tuple(
            sum(self.matrix[i][j] * state[j] for j in range(self.latent_dim))
            for i in range(self.observable_dim)
        )


@dataclass(frozen=True)
class InverseResult:
    """Result of linear inverse reconstruction."""

    reconstructed_state: Vector
    null_basis: tuple[Vector, ...]
    identifiable_rank: int
    residual: float
    is_uniquely_identified: bool


class InverseProjection:
    """Reconstructs state estimates and computes exact null-space bases from observations."""

    @staticmethod
    def reconstruct(
        projection: StateProjection,
        observation: Vector,
        tol: float = 1e-9,
    ) -> InverseResult:
        """Invert observation y = P x to find min-norm representative and null space."""
        P = projection.matrix
        y = observation
        if len(P) != len(y):
            raise ValueError(f"Shape mismatch: projection rows {len(P)} != observation {len(y)}")

        m = len(P)
        n = len(P[0])

        rref_matrix, pivots = rref_solve(P, y, tol=tol)

        # Check for inconsistency: 0 = non-zero
        for row in rref_matrix:
            lhs_zero = all(abs(row[j]) <= tol for j in range(n))
            rhs_nonzero = abs(row[n]) > tol
            if lhs_zero and rhs_nonzero:
                raise ValueError(
                    "Inconsistent observation: no latent state can produce this observation"
                )

        # Basic particular solution setting free variables to zero
        particular_x = [0.0] * n
        for i, c in enumerate(pivots):
            particular_x[c] = rref_matrix[i][n]

        # Null-space basis for free variables
        free_vars = [j for j in range(n) if j not in pivots]
        null_vectors: list[Vector] = []
        for f in free_vars:
            z = [0.0] * n
            z[f] = 1.0
            for i, c in enumerate(pivots):
                z[c] = -rref_matrix[i][f]
            null_vectors.append(tuple(z))

        # Reconstructed residual
        yh = [sum(P[i][j] * particular_x[j] for j in range(n)) for i in range(m)]
        residual = math.sqrt(sum((yh[i] - y[i]) ** 2 for i in range(m)))

        is_unique = (len(null_vectors) == 0) and (residual <= tol)

        return InverseResult(
            reconstructed_state=tuple(particular_x),
            null_basis=tuple(null_vectors),
            identifiable_rank=len(pivots),
            residual=residual,
            is_uniquely_identified=is_unique,
        )
