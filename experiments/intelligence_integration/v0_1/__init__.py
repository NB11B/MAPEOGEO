"""MAPEOGEO Intelligence Integration (v0.1).

Read-only adapter and integration test suite bridging MAPEOGEO records into the
intel_uow reference model.
"""

from .contract import (
    AdapterContract,
    ClockDomain,
    GraphLayer,
    ProjectionStatus,
)
from .adapter import (
    AttributedAnalysisResult,
    MAPEOGEOAnalysisAdapter,
    ProjectedAnalysisCase,
)

__all__ = [
    "AdapterContract",
    "ClockDomain",
    "GraphLayer",
    "ProjectionStatus",
    "AttributedAnalysisResult",
    "MAPEOGEOAnalysisAdapter",
    "ProjectedAnalysisCase",
]
