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


def __getattr__(name: str):
    """Load adapter exports only when explicitly requested.

    Shared clock and contract utilities do not need the optional intel_uow
    reference package. Adapter users still receive its original import errors.
    """
    if name in {
        "AttributedAnalysisResult",
        "MAPEOGEOAnalysisAdapter",
        "ProjectedAnalysisCase",
    }:
        from . import adapter

        return getattr(adapter, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

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
