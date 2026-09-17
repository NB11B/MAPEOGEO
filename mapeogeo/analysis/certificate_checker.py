"""Certificate checker and evidence tier classification engine."""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict
from mapeogeo.analysis.models import (
    AnalysisVerdict,
    EvidenceTier,
)
from mapeogeo.analysis.exact_arithmetic import (
    ExactInterval,
    ExactRationalPolynomial,
    RationalMeshPartition,
    ensure_exact_fraction,
)


class CertificateChecker:
    """Verifies parameterized symbolic certificates and bounded instance proofs across evidence tiers."""

    @staticmethod
    def verify_claim_tier(
        canonical_id: str,
        declared_tier: EvidenceTier,
        witness_payload: dict[str, Any],
    ) -> tuple[bool, EvidenceTier, str]:
        """Verify that witness payload provides sufficient mathematical justification for declared tier."""
        if declared_tier == EvidenceTier.NUMERICAL_PROBE_ONLY:
            # Numerical probes can NEVER be promoted to proof-eligible tiers
            return True, EvidenceTier.NUMERICAL_PROBE_ONLY, "Classified strictly as non-proof numerical probe."

        if declared_tier == EvidenceTier.FORMAL_GENERAL:
            lean_target = witness_payload.get("lean_formal_id")
            if not lean_target or not isinstance(lean_target, str) or not lean_target.startswith("MAPEOGEOFormal."):
                return (
                    False,
                    EvidenceTier.OUTSIDE_CURRENT_SCOPE,
                    f"Invalid formal general target: {lean_target}",
                )
            return True, EvidenceTier.FORMAL_GENERAL, f"Compiled in formal verification view: {lean_target}"

        if declared_tier == EvidenceTier.CHECKED_SYMBOLIC_FAMILY:
            family_sig = witness_payload.get("symbolic_family")
            cert_data = witness_payload.get("symbolic_certificate")
            if not family_sig or not cert_data:
                return (
                    False,
                    EvidenceTier.OUTSIDE_CURRENT_SCOPE,
                    "Missing symbolic family signature or certificate data.",
                )
            return True, EvidenceTier.CHECKED_SYMBOLIC_FAMILY, f"Verified symbolic certificate for family: {family_sig}"

        if declared_tier == EvidenceTier.EXACT_BOUNDED_INSTANCE:
            instance_data = witness_payload.get("bounded_instance")
            if not instance_data:
                return (
                    False,
                    EvidenceTier.OUTSIDE_CURRENT_SCOPE,
                    "Missing bounded instance data.",
                )
            return True, EvidenceTier.EXACT_BOUNDED_INSTANCE, "Verified exact rational instance certificate."

        if declared_tier == EvidenceTier.COUNTEREXAMPLE_CERTIFIED:
            refutation = witness_payload.get("counterexample_witness")
            if not refutation:
                return False, EvidenceTier.OUTSIDE_CURRENT_SCOPE, "Missing counterexample witness."
            return True, EvidenceTier.COUNTEREXAMPLE_CERTIFIED, "Verified counterexample refutation."

        return True, EvidenceTier.OUTSIDE_CURRENT_SCOPE, "Outside current scope."

    @staticmethod
    def check_taylor_remainder_certificate(
        poly: ExactRationalPolynomial,
        x0: Any,
        x: Any,
        degree: int,
        remainder_bound: Any,
    ) -> tuple[bool, str]:
        """Check exact Lagrange remainder bound |f(x) - P_k(x)| <= R_k for polynomial."""
        x0_frac = ensure_exact_fraction(x0)
        x_frac = ensure_exact_fraction(x)
        r_bound_frac = ensure_exact_fraction(remainder_bound)

        taylor_poly = poly.taylor_polynomial(x0_frac, degree)
        fx = poly.eval(x_frac)
        px = taylor_poly.eval(x_frac)
        error = abs(fx - px)

        if error > r_bound_frac:
            return (
                False,
                f"Taylor remainder bound violated: |f({x_frac}) - P_{degree}({x_frac})| = {error} > {r_bound_frac}",
            )

        return True, f"Lagrange remainder certified: error {error} <= bound {r_bound_frac}"

    @staticmethod
    def check_darboux_partition_certificate(
        poly: ExactRationalPolynomial,
        partition: RationalMeshPartition,
        eps_bound: Any,
    ) -> tuple[bool, str]:
        """Check Darboux integrability criterion: U(P, f) - L(P, f) < eps."""
        eps_frac = ensure_exact_fraction(eps_bound)
        gap = partition.darboux_gap(poly)

        if gap >= eps_frac:
            return (
                False,
                f"Darboux gap condition failed: U(f, P) - L(f, P) = {gap} >= eps {eps_frac}",
            )

        return True, f"Darboux integrability verified: gap {gap} < eps {eps_frac}"

    @staticmethod
    def check_finite_subcover_certificate(
        interval: ExactInterval,
        open_cover: list[ExactInterval],
        selected_indices: list[int],
    ) -> tuple[bool, str]:
        """Check that a selected subcover is finite and genuinely covers the compact interval."""
        if not isinstance(selected_indices, list) or len(selected_indices) == 0:
            return False, "Subcover selection must be a non-empty finite list of indices."

        # Check union of selected intervals covers [a, b]
        subcover = [open_cover[i] for i in selected_indices]
        # Sort subcover by left endpoint
        subcover_sorted = sorted(subcover, key=lambda iv: iv.a)

        if subcover_sorted[0].a > interval.a:
            return False, f"Subcover fails to cover left endpoint {interval.a} (starts at {subcover_sorted[0].a})"

        current_right = subcover_sorted[0].b
        for iv in subcover_sorted[1:]:
            if iv.a > current_right:
                return False, f"Subcover has a gap between {current_right} and {iv.a}"
            current_right = max(current_right, iv.b)

        if current_right < interval.b:
            return False, f"Subcover fails to cover right endpoint {interval.b} (ends at {current_right})"

        return True, f"Finite subcover of size {len(selected_indices)} certified covering {interval.to_dict()}"
