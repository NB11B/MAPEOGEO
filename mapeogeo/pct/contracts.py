"""Applicability and verdict enforcement helpers for PCT."""

from __future__ import annotations

from typing import Any

from mapeogeo.pct.models import Applicability, Verdict, VerdictRecord


def make_verdict(
    check_id: str,
    applicability: Applicability,
    verdict: Verdict,
    measured: Any,
    expected: Any,
    tolerance_or_exact_rule: str,
    provenance: dict[str, Any] | None = None,
) -> VerdictRecord:
    """Construct a canonical VerdictRecord."""
    return VerdictRecord(
        check_id=check_id,
        applicability=applicability,
        verdict=verdict,
        measured=measured,
        expected=expected,
        tolerance_or_exact_rule=tolerance_or_exact_rule,
        provenance=provenance if provenance is not None else {},
    )


def require_applicable(
    check_id: str,
    is_applicable: bool,
    measured: Any = None,
    expected: Any = None,
    tolerance_or_exact_rule: str = "APPLICABILITY_PREDICATE",
    provenance: dict[str, Any] | None = None,
) -> VerdictRecord:
    """Return a NOT_APPLICABLE verdict record if predicate is False, or APPLICABLE/PASS record if True."""
    if not is_applicable:
        return make_verdict(
            check_id=check_id,
            applicability=Applicability.NOT_APPLICABLE,
            verdict=Verdict.NOT_APPLICABLE,
            measured=measured,
            expected=expected,
            tolerance_or_exact_rule=tolerance_or_exact_rule,
            provenance=provenance,
        )
    return make_verdict(
        check_id=check_id,
        applicability=Applicability.APPLICABLE,
        verdict=Verdict.PASS,
        measured=measured,
        expected=expected,
        tolerance_or_exact_rule=tolerance_or_exact_rule,
        provenance=provenance,
    )
