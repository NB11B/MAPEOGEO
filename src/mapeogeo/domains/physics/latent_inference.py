"""Latent Generator Inversion and Observability Engine for Physics.

Enforces:
    y(t) = P(X(t))

Given measured response y(t), infers ONLY what the measurements license about
an unknown generator X without claiming knowledge of its identity.

In particular:
    Sigma(X) = Sigma(Y) ==> AMBIGUOUS
    effect observed != source identified.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from mapeogeo.domains.physics.ontology import (
    EpistemicStatus,
    MeasuredObservation,
    PhysicalHypothesis,
)
from mapeogeo.psmsl.algebra import eye, matmul
from mapeogeo.psmsl.projection import InverseProjection, StateProjection


@dataclass(frozen=True)
class LatentInferenceResult:
    """Result of latent generator inverse projection and observability audit."""

    generator_representative: tuple[float, ...]
    null_space_basis: tuple[tuple[float, ...], ...]
    identifiable_rank: int
    latent_dimension: int
    residual_norm: float
    is_fully_identified: bool
    is_ambiguous: bool
    ambiguity_reason: str | None = None
    epistemic_status: EpistemicStatus = EpistemicStatus.INFERRED
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def null_space_dimension(self) -> int:
        return len(self.null_space_basis)

    def to_hypothesis(
        self, hypothesis_id: str, model_name: str = "LatentGenerator"
    ) -> PhysicalHypothesis:
        """Promote inference result to PhysicalHypothesis preserving epistemic limits."""
        return PhysicalHypothesis(
            hypothesis_id=hypothesis_id,
            model_name=model_name,
            latent_state=self.generator_representative,
            epistemic_status=self.epistemic_status,
            is_source_identified=self.is_fully_identified,
            null_space_dimension=self.null_space_dimension,
            residual_norm=self.residual_norm,
        )


class LatentGeneratorInverter:
    """Performs rigorous empirical inversion and non-identifiability analysis."""

    def __init__(self, tolerance: float = 1e-9) -> None:
        self.tolerance = tolerance

    def stack_observations(
        self,
        observations: Sequence[MeasuredObservation],
    ) -> tuple[tuple[tuple[float, ...], ...], tuple[float, ...]]:
        """Stack multiple observations into an aggregate linear system P_agg * X = y_agg."""
        if not observations:
            raise ValueError("Observation sequence cannot be empty")

        p_rows: list[tuple[float, ...]] = []
        y_vals: list[float] = []
        latent_dim = observations[0].latent_dimension

        for obs in observations:
            if obs.latent_dimension != latent_dim:
                raise ValueError("All observations must share the same latent dimension")
            for row in obs.projection_matrix:
                p_rows.append(tuple(float(v) for v in row))
            for val in obs.values:
                y_vals.append(float(val))

        return tuple(p_rows), tuple(y_vals)

    def invert_observations(
        self,
        observations: Sequence[MeasuredObservation],
    ) -> LatentInferenceResult:
        """Infer latent state constraints from empirical observations.

        Computes the minimal-free-variable representative plus exact null space basis.
        Strictly flags ambiguity when null space dimension > 0.
        """
        p_matrix, y_vector = self.stack_observations(observations)
        latent_dim = len(p_matrix[0]) if p_matrix else 0

        # Invert linear system using PSMSL InverseProjection
        try:
            proj = StateProjection(projection_id="proj:aggregate", matrix=p_matrix)
            inv_res = InverseProjection.reconstruct(proj, y_vector, tol=self.tolerance)
        except ValueError as err:
            # Inconsistent observations: data contradicts itself
            return LatentInferenceResult(
                generator_representative=(0.0,) * latent_dim,
                null_space_basis=(),
                identifiable_rank=0,
                latent_dimension=latent_dim,
                residual_norm=float("inf"),
                is_fully_identified=False,
                is_ambiguous=True,
                ambiguity_reason=f"INCONSISTENT_OBSERVATIONS: {err}",
                epistemic_status=EpistemicStatus.OBSERVED,
            )

        x_rep = inv_res.reconstructed_state
        null_basis = inv_res.null_basis
        rank_p = inv_res.identifiable_rank
        residual = inv_res.residual

        null_dim = len(null_basis)
        is_identified = null_dim == 0 and rank_p == latent_dim and residual <= self.tolerance
        is_ambiguous = null_dim > 0

        ambiguity_reason = None
        if is_ambiguous:
            ambiguity_reason = (
                f"AMBIGUOUS_OBSERVATIONAL_EQUIVALENCE: null space dimension {null_dim} > 0; "
                f"infinitely many distinct generators produce identical observable response"
            )

        epistemic = EpistemicStatus.INFERRED if not is_ambiguous else EpistemicStatus.OBSERVED

        return LatentInferenceResult(
            generator_representative=x_rep,
            null_space_basis=null_basis,
            identifiable_rank=rank_p,
            latent_dimension=latent_dim,
            residual_norm=round(residual, 9),
            is_fully_identified=is_identified,
            is_ambiguous=is_ambiguous,
            ambiguity_reason=ambiguity_reason,
            epistemic_status=epistemic,
        )

    def trajectory_observability_matrix(
        self,
        dynamics_matrix_a: Sequence[Sequence[float]],
        measurement_matrix_c: Sequence[Sequence[float]],
        steps: int | None = None,
    ) -> tuple[tuple[float, ...], ...]:
        """Construct discrete Kalman observability matrix O = [C; C*A; C*A^2; ...; C*A^(k-1)]."""
        c_mat = tuple(tuple(float(v) for v in row) for row in measurement_matrix_c)
        a_mat = tuple(tuple(float(v) for v in row) for row in dynamics_matrix_a)
        n = len(a_mat)
        num_steps = n if steps is None else steps
        power_a = eye(n)
        rows: list[tuple[float, ...]] = []

        for _ in range(num_steps):
            ca = matmul(c_mat, power_a)
            for row in ca:
                rows.append(row)
            power_a = matmul(power_a, a_mat)

        return tuple(rows)

    def check_observational_equivalence(
        self,
        generator_1: Sequence[float],
        generator_2: Sequence[float],
        projection: Sequence[Sequence[float]],
    ) -> bool:
        """Check if Sigma(X1) == Sigma(X2) under projection P."""
        y1 = [
            sum(projection[i][j] * generator_1[j] for j in range(len(generator_1)))
            for i in range(len(projection))
        ]
        y2 = [
            sum(projection[i][j] * generator_2[j] for j in range(len(generator_2)))
            for i in range(len(projection))
        ]
        return all(abs(a - b) <= self.tolerance for a, b in zip(y1, y2, strict=True))
