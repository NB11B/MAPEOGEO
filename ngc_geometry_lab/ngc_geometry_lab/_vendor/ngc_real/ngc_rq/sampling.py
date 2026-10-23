"""Sampling summary helpers for real-phase circuit outputs."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Mapping

from .real_phase import RealPhaseError


_Z_BY_CONFIDENCE = {
    0.80: 1.2815515655446004,
    0.90: 1.6448536269514722,
    0.95: 1.959963984540054,
    0.98: 2.3263478740408408,
    0.99: 2.5758293035489004,
}
_BOUNDARY_EPS = 1e-15


@dataclass(frozen=True)
class SampleEstimate:
    """Estimated probability for a sampled basis outcome."""

    outcome: str
    count: int
    shots: int
    probability: float
    standard_error: float
    ci_low: float
    ci_high: float
    confidence: float


def _z_for_confidence(confidence: float) -> float:
    confidence = float(confidence)
    if confidence in _Z_BY_CONFIDENCE:
        return _Z_BY_CONFIDENCE[confidence]
    raise RealPhaseError(
        f"unsupported confidence {confidence}; use one of {sorted(_Z_BY_CONFIDENCE)} or extend _Z_BY_CONFIDENCE."
    )


def _clamp_probability(value: float) -> float:
    value = float(value)
    if value <= _BOUNDARY_EPS:
        return 0.0
    if value >= 1.0 - _BOUNDARY_EPS:
        return 1.0
    return min(1.0, max(0.0, value))


def wilson_interval(count: int, shots: int, *, confidence: float = 0.95) -> tuple[float, float]:
    """Return a Wilson score interval for a binomial proportion."""
    count = int(count)
    shots = int(shots)
    if shots <= 0:
        raise RealPhaseError("shots must be positive for confidence intervals.")
    if count < 0 or count > shots:
        raise RealPhaseError(f"count must be in [0, shots]; got count={count}, shots={shots}.")
    z = _z_for_confidence(confidence)
    phat = count / shots
    denom = 1.0 + z * z / shots
    center = (phat + z * z / (2.0 * shots)) / denom
    spread = z * sqrt((phat * (1.0 - phat) + z * z / (4.0 * shots)) / shots) / denom
    return _clamp_probability(center - spread), _clamp_probability(center + spread)


def summarize_counts(
    counts: Mapping[str, int],
    *,
    num_qubits: int | None = None,
    shots: int | None = None,
    confidence: float = 0.95,
    include_zeros: bool = False,
) -> dict[str, SampleEstimate]:
    """Summarize basis-sample counts with standard error and Wilson intervals.

    If ``num_qubits`` and ``include_zeros`` are supplied, every computational
    basis outcome is included in the returned dictionary.
    """
    clean_counts = {str(k): int(v) for k, v in counts.items()}
    if any(v < 0 for v in clean_counts.values()):
        raise RealPhaseError("counts must be non-negative.")
    total = int(sum(clean_counts.values()) if shots is None else shots)
    if total <= 0:
        raise RealPhaseError("shots must be positive for sampling summaries.")

    outcomes = set(clean_counts)
    if include_zeros:
        if num_qubits is None:
            raise RealPhaseError("num_qubits is required when include_zeros=True.")
        outcomes.update(format(i, f"0{int(num_qubits)}b") for i in range(2 ** int(num_qubits)))

    summary: dict[str, SampleEstimate] = {}
    for outcome in sorted(outcomes):
        count = int(clean_counts.get(outcome, 0))
        if count > total:
            raise RealPhaseError(f"count for outcome {outcome} exceeds shots.")
        p = count / total
        se = sqrt(p * (1.0 - p) / total)
        lo, hi = wilson_interval(count, total, confidence=confidence)
        summary[outcome] = SampleEstimate(
            outcome=outcome,
            count=count,
            shots=total,
            probability=float(p),
            standard_error=float(se),
            ci_low=float(lo),
            ci_high=float(hi),
            confidence=float(confidence),
        )
    return summary
