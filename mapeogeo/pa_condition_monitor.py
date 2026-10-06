"""Condition monitoring in PA operator coordinates.

The monitor is intentionally diagnostic rather than causal: it learns a robust
normal region from measured operator coordinates and flags held-out departures.
A flag is not a fault label.  Missing required coordinates produce
UNDERDETERMINED rather than an inferred diagnosis.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from statistics import median
from typing import Iterable, Sequence


LABELS = ("gain", "phase", "delta_gain", "delta_phase")


@dataclass(frozen=True)
class RobustRegion:
    center: tuple[float, ...]
    scale: tuple[float, ...]
    threshold: float


@dataclass(frozen=True)
class MonitorDecision:
    state: str
    score: float | None
    dominant_coordinate: str | None
    missing: tuple[str, ...] = ()


def _quantile(values: Sequence[float], q: float) -> float:
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must be in [0,1]")
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def fit_region(rows: Sequence[Sequence[float]], *, quantile: float = 0.999) -> RobustRegion:
    if not rows:
        raise ValueError("training rows required")
    width = len(rows[0])
    if width != len(LABELS) or any(len(row) != width for row in rows):
        raise ValueError("expected four operator coordinates")
    center=[]; scale=[]
    for j in range(width):
        values=[float(row[j]) for row in rows]
        c=median(values)
        mad=median(abs(v-c) for v in values)
        center.append(c)
        scale.append(max(1e-12, 1.4826*mad))
    scores=[math.sqrt(sum(((row[j]-center[j])/scale[j])**2 for j in range(width))) for row in rows]
    return RobustRegion(tuple(center), tuple(scale), _quantile(scores, quantile))


def evaluate(region: RobustRegion, coordinates: dict[str, float]) -> MonitorDecision:
    missing=tuple(label for label in LABELS if label not in coordinates)
    if missing:
        return MonitorDecision("UNDERDETERMINED", None, None, missing)
    z=tuple((coordinates[label]-region.center[j])/region.scale[j] for j,label in enumerate(LABELS))
    score=math.sqrt(sum(value*value for value in z))
    dominant=LABELS[max(range(len(z)), key=lambda j: abs(z[j]))]
    return MonitorDecision("DEPARTURE" if score>region.threshold else "NORMAL", score, dominant)
