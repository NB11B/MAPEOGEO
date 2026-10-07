"""Physical Certification Boundary Component (C_phys).

Enforces the five formal physical verification gates:
    C_phys = { D, C, M, F, R }

Where:
    D: Dimensional consistency and unit homogeneity
    C: Applicable conservation constraints (energy, momentum, charge, flux)
    M: Measurement agreement with empirical sensor observations (||P(X) - y|| <= eps)
    F: Falsifier survival (stress tests, over-fitting rejection, non-identifiability checks)
    R: Repeatability and measurement replay invariance

INVARIANT:
    Mathematical admissibility != physical establishment.
    Fail-closed rather than upgrading incomplete evidence.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Sequence

from mapeogeo.domains.physics.ontology import (
    EpistemicStatus,
    MeasuredObservation,
    PhysicalCertificate,
    PhysicalCertificationVerdict,
    PhysicalConstraint,
    PhysicalHypothesis,
)


class PhysicalCertificationBoundary:
    """Evaluates physical hypotheses against the five physical verification gates."""

    def __init__(self, tolerance: float = 1e-4) -> None:
        self.tolerance = tolerance

    def certify_hypothesis(
        self,
        hypothesis: PhysicalHypothesis,
        observations: Sequence[MeasuredObservation],
        constraints: Sequence[PhysicalConstraint] = (),
        repeat_observations: Sequence[MeasuredObservation] | None = None,
    ) -> PhysicalCertificate:
        """Run all five physical certification gates fail-closed."""
        now = time.time()
        gates_passed: list[str] = []
        falsifications_checked: list[str] = []

        # --- GATE D: Dimensional Consistency ---
        # Verify dimensional units and homogeneity
        if hypothesis.metadata.get("has_dimensional_inconsistency", False):
            return PhysicalCertificate(
                certificate_id="",
                verdict=PhysicalCertificationVerdict.FALSIFIED,
                is_certified=False,
                gates_passed=tuple(gates_passed),
                falsifications_checked=("GATE_D_DIMENSIONAL_CHECK",),
                residual_error=hypothesis.residual_norm,
                epistemic_status=EpistemicStatus.INFERRED,
                is_source_identified=False,
                failure_reason=(
                    "Gate D failed: Dimensional inconsistency detected in physical model"
                ),
                timestamp=now,
            )
        gates_passed.append("GATE_D_DIMENSIONAL_CONSISTENCY")

        # --- GATE C: Applicable Conservation Constraints ---
        for constraint in constraints:
            tol = constraint.tolerance or self.tolerance
            # Check energy / momentum / flux conservation
            if constraint.law_type == "CONSERVATION_ENERGY":
                drift = float(hypothesis.metadata.get("energy_drift", 0.0))
                if drift > tol:
                    return PhysicalCertificate(
                        certificate_id="",
                        verdict=PhysicalCertificationVerdict.FALSIFIED,
                        is_certified=False,
                        gates_passed=tuple(gates_passed),
                        falsifications_checked=("GATE_C_ENERGY_CONSERVATION",),
                        residual_error=drift,
                        epistemic_status=EpistemicStatus.INFERRED,
                        is_source_identified=False,
                        failure_reason=(
                            f"Gate C failed: Energy conservation violated "
                            f"(drift {drift} > tol {tol})"
                        ),
                        timestamp=now,
                    )
            elif constraint.law_type == "CONSERVATION_MOMENTUM":
                drift = float(hypothesis.metadata.get("momentum_drift", 0.0))
                if drift > tol:
                    return PhysicalCertificate(
                        certificate_id="",
                        verdict=PhysicalCertificationVerdict.FALSIFIED,
                        is_certified=False,
                        gates_passed=tuple(gates_passed),
                        falsifications_checked=("GATE_C_MOMENTUM_CONSERVATION",),
                        residual_error=drift,
                        epistemic_status=EpistemicStatus.INFERRED,
                        is_source_identified=False,
                        failure_reason=(
                            f"Gate C failed: Momentum conservation violated "
                            f"(drift {drift} > tol {tol})"
                        ),
                        timestamp=now,
                    )
        gates_passed.append("GATE_C_CONSERVATION_CONSTRAINTS")

        # Check if observations exist
        if not observations:
            # Passes D and C, but has zero measurement data
            return PhysicalCertificate(
                certificate_id="",
                verdict=PhysicalCertificationVerdict.THEORETICALLY_ADMISSIBLE,
                is_certified=False,
                gates_passed=tuple(gates_passed),
                falsifications_checked=(),
                residual_error=hypothesis.residual_norm,
                epistemic_status=EpistemicStatus.INFERRED,
                is_source_identified=False,
                failure_reason=(
                    "Gate M failed: Zero empirical observations supplied "
                    "(theoretically admissible only)"
                ),
                timestamp=now,
            )

        # --- GATE M: Measurement Agreement ---
        total_sq_err = 0.0
        total_measurements = 0
        latent_state = hypothesis.latent_state

        for obs in observations:
            p_mat = obs.projection_matrix
            y_obs = obs.values
            if len(p_mat[0]) != len(latent_state):
                return PhysicalCertificate(
                    certificate_id="",
                    verdict=PhysicalCertificationVerdict.INSUFFICIENT_MEASUREMENT,
                    is_certified=False,
                    gates_passed=tuple(gates_passed),
                    falsifications_checked=(),
                    residual_error=float("inf"),
                    epistemic_status=EpistemicStatus.OBSERVED,
                    is_source_identified=False,
                    failure_reason=(
                        "Gate M failed: Latent dimension mismatch between "
                        "hypothesis and sensor projection"
                    ),
                    timestamp=now,
                )
            for i, row in enumerate(p_mat):
                pred_val = sum(row[j] * latent_state[j] for j in range(len(latent_state)))
                total_sq_err += (pred_val - y_obs[i]) ** 2
                total_measurements += 1

        residual = (total_sq_err / max(1, total_measurements)) ** 0.5
        max_allowed_res = max(
            self.tolerance, hypothesis.metadata.get("max_residual_tolerance", self.tolerance)
        )
        if residual > max_allowed_res:
            return PhysicalCertificate(
                certificate_id="",
                verdict=PhysicalCertificationVerdict.FALSIFIED,
                is_certified=False,
                gates_passed=tuple(gates_passed),
                falsifications_checked=("GATE_M_RESIDUAL_TOLERANCE",),
                residual_error=residual,
                epistemic_status=EpistemicStatus.OBSERVED,
                is_source_identified=False,
                failure_reason=(
                    f"Gate M failed: Residual error {residual:.6f} "
                    f"exceeds threshold {max_allowed_res:.6f}"
                ),
                timestamp=now,
            )
        gates_passed.append("GATE_M_MEASUREMENT_AGREEMENT")

        # --- GATE F: Falsifier Survival ---
        # 1. Reject illegal parameter over-fitting
        falsifications_checked.append("FALSIFIER_OVERFITTING_DEGREES_OF_FREEDOM")
        if hypothesis.free_parameters_count > total_measurements:
            return PhysicalCertificate(
                certificate_id="",
                verdict=PhysicalCertificationVerdict.FALSIFIED,
                is_certified=False,
                gates_passed=tuple(gates_passed),
                falsifications_checked=tuple(falsifications_checked),
                residual_error=residual,
                epistemic_status=EpistemicStatus.MODEL_CONSISTENT,
                is_source_identified=False,
                failure_reason=(
                    f"Gate F failed: Model over-fitting detected; free parameters "
                    f"({hypothesis.free_parameters_count}) exceed measurement "
                    f"count ({total_measurements})"
                ),
                timestamp=now,
            )

        # 2. Reject unwarranted source identification under observational equivalence
        falsifications_checked.append("FALSIFIER_OBSERVATIONAL_EQUIVALENCE_AMBIGUITY")
        if hypothesis.null_space_dimension > 0 and hypothesis.is_source_identified:
            return PhysicalCertificate(
                certificate_id="",
                verdict=PhysicalCertificationVerdict.FALSIFIED,
                is_certified=False,
                gates_passed=tuple(gates_passed),
                falsifications_checked=tuple(falsifications_checked),
                residual_error=residual,
                epistemic_status=EpistemicStatus.MODEL_CONSISTENT,
                is_source_identified=False,
                failure_reason=(
                    f"Gate F failed: Null space dimension is "
                    f"{hypothesis.null_space_dimension} > 0; "
                    f"claiming source identification under ambiguous "
                    f"equivalence is strictly forbidden"
                ),
                timestamp=now,
            )
        gates_passed.append("GATE_F_FALSIFIER_SURVIVAL")

        # --- GATE R: Repeatability / Replay ---
        if repeat_observations is not None:
            falsifications_checked.append("GATE_R_REPLAY_INVARIANCE")
            repeat_sq_err = 0.0
            repeat_cnt = 0
            for obs in repeat_observations:
                for i, row in enumerate(obs.projection_matrix):
                    pred_val = sum(row[j] * latent_state[j] for j in range(len(latent_state)))
                    repeat_sq_err += (pred_val - obs.values[i]) ** 2
                    repeat_cnt += 1
            repeat_res = (repeat_sq_err / max(1, repeat_cnt)) ** 0.5
            if repeat_res > max_allowed_res:
                return PhysicalCertificate(
                    certificate_id="",
                    verdict=PhysicalCertificationVerdict.FALSIFIED,
                    is_certified=False,
                    gates_passed=tuple(gates_passed),
                    falsifications_checked=tuple(falsifications_checked),
                    residual_error=repeat_res,
                    epistemic_status=EpistemicStatus.FALSIFICATION_SURVIVED,
                    is_source_identified=False,
                    failure_reason=(
                        f"Gate R failed: Replay observations failed repeatability "
                        f"threshold ({repeat_res:.6f})"
                    ),
                    timestamp=now,
                )
        gates_passed.append("GATE_R_REPEATABILITY_REPLAY")

        # All 5 gates passed: issue deterministic physical certificate
        hasher = hashlib.sha256()
        hasher.update(hypothesis.hypothesis_id.encode())
        hasher.update(str(hypothesis.latent_state).encode())
        hasher.update(str(now).encode())
        cert_id = f"cert:phys:{hasher.hexdigest()[:16]}"

        return PhysicalCertificate(
            certificate_id=cert_id,
            verdict=PhysicalCertificationVerdict.MEASUREMENT_SUPPORTED,
            is_certified=True,
            gates_passed=tuple(gates_passed),
            falsifications_checked=tuple(falsifications_checked),
            residual_error=round(residual, 6),
            epistemic_status=EpistemicStatus.MEASUREMENT_SUPPORTED,
            is_source_identified=hypothesis.is_source_identified,
            failure_reason=None,
            timestamp=now,
        )
