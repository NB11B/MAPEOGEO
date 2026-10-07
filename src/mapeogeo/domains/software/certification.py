"""5-Gate Software Certification Boundary.

Implements the qualified boundary:
    C_sw = { T, U, S, L, F }
where:
    - T: Type/interface safety
    - U: Unit/behavioral tests
    - S: Static/contract analysis
    - L: Latency/performance SLA contract
    - F: Concurrency/fault invariants

Governing rule:
    source code exists != software capability certified.
A software component must not become certified merely because tests pass.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime

from mapeogeo.domains.software.ontology import (
    EpistemicSoftwareStatus,
    SoftwareCertificate,
    SoftwareCertificationVerdict,
    SoftwareEvidence,
    SoftwareMachinery,
    SoftwareRequirement,
)


class SoftwareCertificationBoundary:
    """Evaluates software candidates against the 5-Gate Boundary C_sw = { T, U, S, L, F }."""

    def __init__(self, default_latency_bound_ms: float = 100.0) -> None:
        self.default_latency_bound_ms = default_latency_bound_ms

    def certify_software(
        self,
        machinery: SoftwareMachinery,
        evidence: SoftwareEvidence | None = None,
        requirements: Sequence[SoftwareRequirement] = (),
        execution_authority: str = "STANDARD",
    ) -> SoftwareCertificate:
        """Evaluate a software machinery candidate through the 5-gate certification boundary."""
        now = datetime.now(UTC).isoformat()
        ev = evidence or machinery.evidence

        gates_passed: list[str] = []
        falsifications_checked: list[str] = []

        # Authority Check
        if (
            machinery.required_authority != "STANDARD"
            and execution_authority != machinery.required_authority
        ):
            return SoftwareCertificate(
                certificate_id="",
                machinery_id=machinery.machinery_id,
                verdict=SoftwareCertificationVerdict.AUTHORITY_DENIED,
                is_certified=False,
                gates_passed=(),
                falsifications_checked=("AUTHORITY_VERIFICATION",),
                epistemic_status=EpistemicSoftwareStatus.SOURCE_SPECIFIED,
                measured_latency_ms=ev.measured_latency_ms,
                failure_reason=(
                    f"Authority verification failed: required {machinery.required_authority}, "
                    f"caller possesses {execution_authority}"
                ),
                timestamp=now,
            )

        # Invariant: source code exists != software capability certified
        if ev is None or (
            not ev.type_safety_pass
            and not ev.unit_tests_pass
            and not ev.static_analysis_pass
            and not ev.fault_tolerance_pass
        ):
            return SoftwareCertificate(
                certificate_id="",
                machinery_id=machinery.machinery_id,
                verdict=SoftwareCertificationVerdict.INCOMPLETE_CONTRACT,
                is_certified=False,
                gates_passed=(),
                falsifications_checked=("EMPTY_EVIDENCE_CHECK",),
                epistemic_status=EpistemicSoftwareStatus.SOURCE_SPECIFIED,
                measured_latency_ms=999.0,
                failure_reason=(
                    "Incomplete verification evidence: source code exists but "
                    "no verification contracts have been executed"
                ),
                timestamp=now,
            )

        # --- GATE T: Type / Interface Safety ---
        falsifications_checked.append("GATE_T_TYPE_INTERFACE_SAFETY")
        if not ev.type_safety_pass:
            return SoftwareCertificate(
                certificate_id="",
                machinery_id=machinery.machinery_id,
                verdict=SoftwareCertificationVerdict.FALSIFIED,
                is_certified=False,
                gates_passed=tuple(gates_passed),
                falsifications_checked=tuple(falsifications_checked),
                epistemic_status=EpistemicSoftwareStatus.SOURCE_SPECIFIED,
                measured_latency_ms=ev.measured_latency_ms,
                failure_reason=(
                    f"Gate T failed: Type / interface contract violation in "
                    f"{machinery.machinery_id}"
                ),
                timestamp=now,
            )
        gates_passed.append("GATE_T_TYPE_SAFETY")

        # --- GATE U: Unit / Behavioral Tests ---
        falsifications_checked.append("GATE_U_UNIT_BEHAVIORAL_TESTS")
        if not ev.unit_tests_pass:
            return SoftwareCertificate(
                certificate_id="",
                machinery_id=machinery.machinery_id,
                verdict=SoftwareCertificationVerdict.FALSIFIED,
                is_certified=False,
                gates_passed=tuple(gates_passed),
                falsifications_checked=tuple(falsifications_checked),
                epistemic_status=EpistemicSoftwareStatus.STATICALLY_TYPED,
                measured_latency_ms=ev.measured_latency_ms,
                failure_reason=(
                    f"Gate U failed: Unit / behavioral test failure in {machinery.machinery_id}"
                ),
                timestamp=now,
            )
        gates_passed.append("GATE_U_UNIT_TESTS")

        # --- GATE S: Static / Contract Analysis ---
        falsifications_checked.append("GATE_S_STATIC_CONTRACT_ANALYSIS")
        if not ev.static_analysis_pass:
            return SoftwareCertificate(
                certificate_id="",
                machinery_id=machinery.machinery_id,
                verdict=SoftwareCertificationVerdict.FALSIFIED,
                is_certified=False,
                gates_passed=tuple(gates_passed),
                falsifications_checked=tuple(falsifications_checked),
                epistemic_status=EpistemicSoftwareStatus.BEHAVIORALLY_TESTED,
                measured_latency_ms=ev.measured_latency_ms,
                failure_reason=(
                    f"Gate S failed: Static analysis / invariant contract violation in "
                    f"{machinery.machinery_id}"
                ),
                timestamp=now,
            )
        gates_passed.append("GATE_S_STATIC_ANALYSIS")

        # --- GATE L: Latency / Performance SLA Contract ---
        falsifications_checked.append("GATE_L_LATENCY_SLA_CONTRACT")
        # Find minimum latency bound from relevant requirements
        applicable_bounds = [
            req.contracts.latency_bound_ms
            for req in requirements
            if any(sig in req.required_signatures for sig in machinery.provided_signatures)
            and req.contracts.latency_bound_ms > 0
        ]
        max_allowed_latency = (
            min(applicable_bounds) if applicable_bounds else self.default_latency_bound_ms
        )

        if ev.measured_latency_ms > max_allowed_latency:
            return SoftwareCertificate(
                certificate_id="",
                machinery_id=machinery.machinery_id,
                verdict=SoftwareCertificationVerdict.FALSIFIED,
                is_certified=False,
                gates_passed=tuple(gates_passed),
                falsifications_checked=tuple(falsifications_checked),
                epistemic_status=EpistemicSoftwareStatus.CONTRACT_VERIFIED,
                measured_latency_ms=ev.measured_latency_ms,
                failure_reason=(
                    f"Gate L failed: Measured latency {ev.measured_latency_ms:.2f}ms exceeds "
                    f"contract SLA bound {max_allowed_latency:.2f}ms"
                ),
                timestamp=now,
            )
        gates_passed.append("GATE_L_LATENCY_SLA")

        # --- GATE F: Concurrency / Fault Invariants ---
        falsifications_checked.append("GATE_F_FAULT_CONCURRENCY_INVARIANTS")
        if not ev.fault_tolerance_pass:
            return SoftwareCertificate(
                certificate_id="",
                machinery_id=machinery.machinery_id,
                verdict=SoftwareCertificationVerdict.FALSIFIED,
                is_certified=False,
                gates_passed=tuple(gates_passed),
                falsifications_checked=tuple(falsifications_checked),
                epistemic_status=EpistemicSoftwareStatus.CONTRACT_VERIFIED,
                measured_latency_ms=ev.measured_latency_ms,
                failure_reason=(
                    f"Gate F failed: Fault tolerance or concurrency invariant violated in "
                    f"{machinery.machinery_id}"
                ),
                timestamp=now,
            )
        gates_passed.append("GATE_F_FAULT_INVARIANTS")

        # All 5 gates passed: issue deterministic certificate
        hasher = hashlib.sha256()
        hasher.update(machinery.machinery_id.encode())
        for g in gates_passed:
            hasher.update(g.encode())
        hasher.update(f"{ev.measured_latency_ms:.4f}".encode())
        cert_id = f"cert:sw:{hasher.hexdigest()[:16]}"

        return SoftwareCertificate(
            certificate_id=cert_id,
            machinery_id=machinery.machinery_id,
            verdict=SoftwareCertificationVerdict.CERTIFIED,
            is_certified=True,
            gates_passed=tuple(gates_passed),
            falsifications_checked=tuple(falsifications_checked),
            epistemic_status=EpistemicSoftwareStatus.CERTIFIED_CAPABILITY,
            measured_latency_ms=ev.measured_latency_ms,
            failure_reason=None,
            timestamp=now,
            metadata={"gates_count": len(gates_passed)},
        )
