"""Representation-independent invariant query layer for Work Router v0.4."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .work_router import WorkDecision, WorkRequest, WorkRouter
from .multidomain_routes import multidomain_router
from .power_control_routes import power_control_router


class Invariant(str, Enum):
    MAGNITUDE = "magnitude"
    THRESHOLD = "threshold"
    ALIGNMENT = "alignment"
    STABILITY = "stability"
    AREA_CHANGE = "area_change"
    RATE = "rate"
    SPECTRAL_CONTENT = "spectral_content"


@dataclass(frozen=True)
class InvariantQuery:
    invariant: Invariant
    domain: str
    require_materialized: bool = False


TARGETS: dict[tuple[str, Invariant], str] = {
    ("vector", Invariant.MAGNITUDE): "work.vector_norm",
    ("vector", Invariant.THRESHOLD): "work.norm_above_threshold",
    ("vector", Invariant.ALIGNMENT): "work.vector_alignment",
    ("vibration", Invariant.MAGNITUDE): "work.window_rms",
    ("vibration", Invariant.THRESHOLD): "work.vibration_above_threshold",
    ("vibration", Invariant.SPECTRAL_CONTENT): "work.dominant_frequency",
    ("power", Invariant.MAGNITUDE): "work.apparent_power",
    ("power", Invariant.ALIGNMENT): "work.power_factor",
    ("power", Invariant.SPECTRAL_CONTENT): "work.voltage_thd",
    ("control", Invariant.STABILITY): "work.asymptotically_stable",
    ("psmsl", Invariant.STABILITY): "work.asymptotically_stable",
    ("psmsl", Invariant.AREA_CHANGE): "work.area_expanding",
    ("psmsl", Invariant.RATE): "work.operator_motion",
}


def _merge(*routers: WorkRouter) -> WorkRouter:
    edges=[]
    for router in routers:
        edges.extend(router._edges)  # bounded internal composition; tested below
    return WorkRouter(edges)


def invariant_router(base: WorkRouter) -> WorkRouter:
    return _merge(base, multidomain_router(), power_control_router())


def resolve_invariant(
    base: WorkRouter,
    query: InvariantQuery,
    *,
    available: Iterable[str],
    known_answers: Iterable[str] = (),
) -> WorkDecision:
    key=(query.domain, query.invariant)
    if key not in TARGETS:
        return invariant_router(base).decide(
            WorkRequest("work.__unsupported_invariant__"),
            available=available,
            known_answers=known_answers,
        )
    return invariant_router(base).decide(
        WorkRequest(TARGETS[key], require_materialized=query.require_materialized),
        available=available,
        known_answers=known_answers,
    )
