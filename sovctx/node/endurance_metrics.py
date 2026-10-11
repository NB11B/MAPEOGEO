from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResourcePause(Exception):
    """Raised when hardware resource guard thresholds (RAM, swap, thermal, RSS, disk) are breached."""


class EpistemicPause(Exception):
    """Raised when epistemic boundaries (contamination, broken provenance, false promotion) are breached."""


@dataclass
class EpochRecord:
    epoch_id: str
    epoch_index: int
    start_time: str
    end_time: str
    duration_sec: float
    sources_attempted: int
    sources_admitted: int
    frontier_delta: int
    graph_delta: int
    new_contradictions: int
    new_synthesis_candidates: int
    rates: dict[str, float]
    frontier_entropy: float
    growth_efficiency: float
    resource_telemetry: dict[str, Any]
    error_counts: dict[str, int]
    state_hash: str
    sentinel_school_states: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EnduranceMetricsTracker:
    """Tracks time-series rates, frontier entropy, growth efficiency, and supervises circuit breakers for Gate N5."""

    def __init__(
        self,
        evidence_dir: Path,
        max_duplicate_ratio: float = 0.50,
        max_unresolved_ratio: float = 0.65,
        max_generic_ratio: float = 0.25,
    ) -> None:
        self.evidence_dir = evidence_dir
        self.max_duplicate_ratio = max_duplicate_ratio
        self.max_unresolved_ratio = max_unresolved_ratio
        self.max_generic_ratio = max_generic_ratio

        self.epochs: list[EpochRecord] = []
        self.total_epistemic_errors: int = 0
        self.resource_pause_active: bool = False
        self.epistemic_pause_active: bool = False

    def compute_frontier_entropy(self, frontier_by_type: dict[str, int]) -> float:
        """Compute Shannon entropy H_F = - sum p_i log2(p_i) across frontier categories."""
        total = sum(frontier_by_type.values())
        if total == 0:
            return 0.0

        entropy = 0.0
        for count in frontier_by_type.values():
            if count > 0:
                p_i = count / total
                entropy -= p_i * math.log2(p_i)
        return round(entropy, 4)

    def compute_rates(
        self,
        delta_sources: int,
        delta_frontier: int,
        delta_unresolved: int,
        delta_duplicates: int,
        delta_contradictions: int,
        delta_epistemic_errors: int,
        delta_seconds: float,
    ) -> dict[str, float]:
        dt = max(delta_seconds, 0.001)
        return {
            "r_sources": round(delta_sources / dt, 4),
            "r_frontier": round(delta_frontier / dt, 4),
            "r_unresolved": round(delta_unresolved / dt, 4),
            "r_duplicates": round(delta_duplicates / dt, 4),
            "r_contradictions": round(delta_contradictions / dt, 4),
            "r_epistemic_errors": round(delta_epistemic_errors / dt, 4),
        }

    def compute_growth_efficiency(self, useful_items: int, acquisition_attempts: int) -> float:
        """Compute E_g = new independently useful evidence objects / acquisition attempts."""
        if acquisition_attempts == 0:
            return 1.0 if useful_items > 0 else 0.0
        return round(useful_items / acquisition_attempts, 4)

    def check_circuit_breakers(
        self,
        resource_sample: Any,
        epistemic_invariants: dict[str, int],
        drift_metrics: dict[str, float],
    ) -> None:
        """Evaluate both resource and epistemic pause triggers fail-closed."""
        # 1. Resource Pause
        if resource_sample:
            # Check thermal
            if resource_sample.thermal_max_c and resource_sample.thermal_max_c >= 75.0:
                self.trigger_resource_pause(f"Thermal peak {resource_sample.thermal_max_c} C exceeded 75.0 C ceiling")

            # Check RSS
            if hasattr(resource_sample, "worker_rss_mb") and resource_sample.worker_rss_mb and resource_sample.worker_rss_mb >= 450.0:
                self.trigger_resource_pause(f"Worker RSS {resource_sample.worker_rss_mb} MB exceeded 450.0 MB ceiling")

            # Check RAM available
            if resource_sample.ram_available_mb and resource_sample.ram_available_mb < 150.0:
                self.trigger_resource_pause(f"RAM available {resource_sample.ram_available_mb} MB dropped below 150.0 MB floor")

            # Check Swap
            if resource_sample.swap_used_gb and (resource_sample.swap_used_gb * 1024) > 800.0:
                self.trigger_resource_pause(f"Swap used {resource_sample.swap_used_gb * 1024:.1f} MB exceeded 800.0 MB ceiling")

        # 2. Epistemic Pause
        violations = []
        if epistemic_invariants.get("canonical_promotion_violations", 0) > 0:
            violations.append("CANONICAL_PROMOTION_VIOLATION")
        if epistemic_invariants.get("mapeogeo_cross_graph_access", 0) > 0:
            violations.append("MAPEOGEO_CROSS_GRAPH_ACCESS")
        if epistemic_invariants.get("orphaned_sources", 0) > 0:
            violations.append("BROKEN_PROVENANCE_CHAIN")
        if epistemic_invariants.get("unresolved_to_exact_promotions", 0) > 0:
            violations.append("FALSE_EXACT_PROMOTION")
        if epistemic_invariants.get("unsupported_same_as_collapses", 0) > 0:
            violations.append("UNSUPPORTED_SAME_AS")
        if epistemic_invariants.get("temporal_impossibilities", 0) > 0:
            violations.append("TEMPORAL_IMPOSSIBILITY")
        if epistemic_invariants.get("mirror_inflation_violations", 0) > 0:
            violations.append("MIRROR_INFLATION_VIOLATION")

        # Drift thresholds
        d_ratio = drift_metrics.get("duplicate_ratio", 0.0)
        u_ratio = drift_metrics.get("unresolved_ratio", 0.0)
        g_ratio = drift_metrics.get("generic_ratio", 0.0)

        if d_ratio > self.max_duplicate_ratio:
            violations.append(f"RUNAWAY_DUPLICATES (D={d_ratio:.2f})")
        if u_ratio > self.max_unresolved_ratio:
            violations.append(f"UNRESOLVED_DRIFT (U={u_ratio:.2f})")
        if g_ratio > self.max_generic_ratio:
            violations.append(f"GENERIC_DRIFT (G={g_ratio:.2f})")

        if violations:
            self.total_epistemic_errors += len(violations)
            self.trigger_epistemic_pause("; ".join(violations))

    def trigger_resource_pause(self, reason: str) -> None:
        self.resource_pause_active = True
        pause_file = self.evidence_dir / "RESOURCE_PAUSE"
        pause_file.parent.mkdir(parents=True, exist_ok=True)
        pause_file.write_text(
            json.dumps({"triggered_at": utc_now_iso(), "reason": reason}, indent=2),
            encoding="utf-8",
        )
        raise ResourcePause(f"RESOURCE_PAUSE: {reason}")

    def trigger_epistemic_pause(self, reason: str) -> None:
        self.epistemic_pause_active = True
        pause_file = self.evidence_dir / "EPISTEMIC_PAUSE"
        pause_file.parent.mkdir(parents=True, exist_ok=True)
        pause_file.write_text(
            json.dumps({"triggered_at": utc_now_iso(), "reason": reason}, indent=2),
            encoding="utf-8",
        )
        raise EpistemicPause(f"EPISTEMIC_PAUSE: {reason}")

    def record_epoch(self, epoch: EpochRecord) -> None:
        self.epochs.append(epoch)
        epoch_dir = self.evidence_dir / "epochs"
        epoch_dir.mkdir(parents=True, exist_ok=True)
        epoch_file = epoch_dir / f"epoch_{epoch.epoch_index:04d}.json"
        epoch_file.write_text(json.dumps(epoch.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
