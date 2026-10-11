from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EpistemicInstabilityPause(Exception):
    """Raised when the recursive expansion exhibits epistemic drift, provenance breakage, or boundary contamination."""


@dataclass
class GenerationDriftMetrics:
    generation: int
    total_nominations: int
    duplicate_nominations: int
    duplicate_nomination_ratio: float
    total_frontier_items: int
    unresolved_frontier_items: int
    unresolved_frontier_ratio: float
    terminology_nominations: int
    generic_rejected_terms: int
    generic_terminology_ratio: float
    canonical_promotions_attempted: int
    orphaned_sources_detected: int
    epistemic_violations: list[str] = field(default_factory=list)
    recorded_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DriftMonitor:
    """Monitors expansion health and drift ratios across crawler generations and triggers EPISTEMIC_PAUSE on boundary breaches."""

    def __init__(
        self,
        max_duplicate_ratio: float = 0.50,
        max_unresolved_ratio: float = 0.65,
        max_generic_ratio: float = 0.25,
    ) -> None:
        self.max_duplicate_ratio = max_duplicate_ratio
        self.max_unresolved_ratio = max_unresolved_ratio
        self.max_generic_ratio = max_generic_ratio
        self.generation_metrics: list[GenerationDriftMetrics] = []

    def evaluate_generation(
        self,
        generation: int,
        total_nominations: int,
        duplicate_nominations: int,
        total_frontier_items: int,
        unresolved_frontier_items: int,
        terminology_nominations: int,
        generic_rejected_terms: int,
        canonical_promotions_attempted: int,
        orphaned_sources_detected: int,
        extra_violations: Optional[list[str]] = None,
    ) -> GenerationDriftMetrics:
        d_ratio = round(duplicate_nominations / total_nominations, 4) if total_nominations > 0 else 0.0
        u_ratio = round(unresolved_frontier_items / total_frontier_items, 4) if total_frontier_items > 0 else 0.0
        g_ratio = round(generic_rejected_terms / (terminology_nominations + generic_rejected_terms), 4) if (terminology_nominations + generic_rejected_terms) > 0 else 0.0

        violations: list[str] = list(extra_violations or [])

        # Hard Epistemic Invariants
        if canonical_promotions_attempted > 0:
            violations.append(f"FORBIDDEN: {canonical_promotions_attempted} canonical promotion attempts detected during recursive expansion")

        if orphaned_sources_detected > 0:
            violations.append(f"FORBIDDEN: {orphaned_sources_detected} orphaned sources lacking acquisition provenance chain")

        # Drift thresholds (evaluated only when sample size is sufficient)
        if total_nominations >= 20 and d_ratio > self.max_duplicate_ratio:
            violations.append(f"DRIFT_BREACH: Duplicate nomination ratio {d_ratio:.2f} exceeded ceiling {self.max_duplicate_ratio:.2f}")

        if total_frontier_items >= 20 and u_ratio > self.max_unresolved_ratio:
            violations.append(f"DRIFT_BREACH: Unresolved frontier ratio {u_ratio:.2f} exceeded ceiling {self.max_unresolved_ratio:.2f}")

        if (terminology_nominations + generic_rejected_terms) >= 15 and g_ratio > self.max_generic_ratio:
            violations.append(f"DRIFT_BREACH: Generic terminology ratio {g_ratio:.2f} exceeded ceiling {self.max_generic_ratio:.2f}")

        metrics = GenerationDriftMetrics(
            generation=generation,
            total_nominations=total_nominations,
            duplicate_nominations=duplicate_nominations,
            duplicate_nomination_ratio=d_ratio,
            total_frontier_items=total_frontier_items,
            unresolved_frontier_items=unresolved_frontier_items,
            unresolved_frontier_ratio=u_ratio,
            terminology_nominations=terminology_nominations,
            generic_rejected_terms=generic_rejected_terms,
            generic_terminology_ratio=g_ratio,
            canonical_promotions_attempted=canonical_promotions_attempted,
            orphaned_sources_detected=orphaned_sources_detected,
            epistemic_violations=violations,
        )

        self.generation_metrics.append(metrics)

        # Trigger EPISTEMIC_PAUSE if any violation occurred
        if violations:
            msg = f"EPISTEMIC_PAUSE triggered at Generation {generation}: {'; '.join(violations)}"
            raise EpistemicInstabilityPause(msg)

        return metrics

    def export_frontier_health(self, output_path: Path) -> None:
        """Export JSON dossier of generation drift metrics and frontier health."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "evaluation_timestamp": utc_now_iso(),
            "status": "HEALTHY" if all(len(m.epistemic_violations) == 0 for m in self.generation_metrics) else "DRIFTING",
            "generations": [m.to_dict() for m in self.generation_metrics],
        }
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
