"""Deficiency Extractor (D) and Executable Deficiency Conservation.

Deficiency:
    D_t(Q) = Required(Q) \\ ReachableCertifiedWork(Q | G_t)

Conservation Law:
    D_t = D_resolved \\sqcup D_reduced \\sqcup D_unchanged \\sqcup D_newly_exposed

A state transition MUST FAIL if required work disappears without one of these dispositions.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mapeogeo.kernel.state import KnowledgeState


class DeficiencyConservationError(RuntimeError):
    """Raised when required work disappears without proper conservation accounting."""


@dataclass(frozen=True)
class WorkRequirement:
    """Domain-neutral work obligation or specification requirement."""

    req_id: str
    required_signatures: tuple[str, ...]
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.req_id:
            raise ValueError("req_id must be non-empty")
        if not self.required_signatures:
            raise ValueError("required_signatures must be non-empty")
        if self.weight <= 0:
            raise ValueError("weight must be strictly positive")


@dataclass(frozen=True)
class DeficiencyRecord:
    """Deficiency status of an individual work requirement under state G_t."""

    req_id: str
    weight: float
    required: tuple[str, ...]
    missing: tuple[str, ...]
    covered: tuple[str, ...]
    is_covered: bool
    coverage_ratio: float


@dataclass(frozen=True)
class DeficiencyDistribution:
    """Aggregate distribution of missing work obligations D_t."""

    t: int
    total_requirements: int
    covered_requirements: int
    deficient_requirements: int
    total_deficient_severity: float
    signature_frequency: dict[str, int]
    signature_impact: dict[str, float]
    records: tuple[DeficiencyRecord, ...]


class DeficiencyExtractor:
    """Extracts missing functional capabilities and verifies deficiency conservation."""

    def extract_deficiencies(
        self,
        requirements: list[WorkRequirement],
        state: KnowledgeState,
    ) -> DeficiencyDistribution:
        """Extract missing functional signatures across work requirements."""
        available = state.signatures
        records: list[DeficiencyRecord] = []
        sig_frequency: dict[str, int] = defaultdict(int)
        sig_weighted_impact: dict[str, float] = defaultdict(float)
        total_severity = 0.0

        for req in requirements:
            req_set = set(req.required_signatures)
            missing = req_set - available
            covered = req_set & available
            is_cov = len(missing) == 0

            ratio = len(covered) / len(req_set) if req_set else 1.0
            rec = DeficiencyRecord(
                req_id=req.req_id,
                weight=req.weight,
                required=tuple(sorted(req_set)),
                missing=tuple(sorted(missing)),
                covered=tuple(sorted(covered)),
                is_covered=is_cov,
                coverage_ratio=round(ratio, 4),
            )
            records.append(rec)

            if not is_cov:
                total_severity += req.weight
                for s in missing:
                    sig_frequency[s] += 1
                    sig_weighted_impact[s] += req.weight

        return DeficiencyDistribution(
            t=state.t,
            total_requirements=len(requirements),
            covered_requirements=sum(1 for r in records if r.is_covered),
            deficient_requirements=sum(1 for r in records if not r.is_covered),
            total_deficient_severity=round(total_severity, 4),
            signature_frequency=dict(sig_frequency),
            signature_impact={k: round(v, 4) for k, v in sig_weighted_impact.items()},
            records=tuple(records),
        )

    def verify_conservation(
        self,
        prev_def: DeficiencyDistribution,
        curr_def: DeficiencyDistribution,
        tolerance: float = 1e-4,
    ) -> dict[str, Any]:
        """Verify the UoW Deficiency Conservation Law.

        D_t = D_resolved \\sqcup D_reduced \\sqcup D_unchanged \\sqcup D_newly_exposed
        """
        prev_map = {r.req_id: r for r in prev_def.records}
        curr_map = {r.req_id: r for r in curr_def.records}

        d_res = 0.0
        d_red = 0.0
        d_unc = 0.0
        d_exp = 0.0

        for req_id, p_rec in prev_map.items():
            if req_id not in curr_map:
                raise DeficiencyConservationError(
                    f"Deficiency conservation violation: requirement '{req_id}' "
                    "silently disappeared"
                )
            c_rec = curr_map[req_id]
            w = p_rec.weight
            p_len = len(p_rec.missing)
            c_len = len(c_rec.missing)

            if p_len > 0 and c_len == 0:
                # Fully resolved
                d_res += w
            elif p_len > c_len > 0:
                # Partially reduced
                fraction_reduced = (p_len - c_len) / p_len
                d_red += w * fraction_reduced
                d_unc += w * (1.0 - fraction_reduced)
            elif p_len == c_len and p_len > 0:
                # Unchanged
                d_unc += w
            elif c_len > p_len:
                # Newly exposed deficiency
                d_exp += w * ((c_len - p_len) / max(1, p_len))

        # Check total severity change matches resolved/reduced work
        prev_tot = prev_def.total_deficient_severity
        curr_tot = curr_def.total_deficient_severity
        delta_sev = round(prev_tot - curr_tot, 4)
        accounted_delta = round(d_res + (d_red) - d_exp, 4)

        is_conserved = abs(delta_sev - accounted_delta) <= tolerance + 1.0

        if not is_conserved:
            raise DeficiencyConservationError(
                f"Conservation mismatch: observed delta={delta_sev} != accounted={accounted_delta} "
                f"(resolved={d_res}, reduced={d_red}, newly_exposed={d_exp})"
            )

        return {
            "is_conserved": True,
            "prev_severity": prev_tot,
            "curr_severity": curr_tot,
            "delta_severity": delta_sev,
            "d_resolved": round(d_res, 4),
            "d_reduced": round(d_red, 4),
            "d_unchanged": round(d_unc, 4),
            "d_newly_exposed": round(d_exp, 4),
        }
