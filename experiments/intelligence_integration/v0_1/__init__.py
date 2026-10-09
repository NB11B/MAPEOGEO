"""MAPEOGEO Intelligence Integration (v0.1).

Read-only adapter and integration test suite bridging MAPEOGEO records into the
intel_uow reference model.
"""

from .contract import (
    AdapterContract,
    CLOCK_IDENTITY_PREFIX,
    ClockDomain,
    GraphLayer,
    ProjectionStatus,
    decode_clock_identity,
    encode_clock_identity,
)
from .adapter import (
    AttributedAnalysisResult,
    MAPEOGEOAnalysisAdapter,
    ProjectedAnalysisCase,
)

__all__ = [
    "AdapterContract",
    "CLOCK_IDENTITY_PREFIX",
    "ClockDomain",
    "GraphLayer",
    "ProjectionStatus",
    "AttributedAnalysisResult",
    "MAPEOGEOAnalysisAdapter",
    "ProjectedAnalysisCase",
    "decode_clock_identity",
    "encode_clock_identity",
]
