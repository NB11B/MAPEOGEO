"""SOVCTX Node Runtime for Jetson Nano.

Provides isolated resource governance, mutable work database,
content-addressed acquisition CAS, and candidate pipeline daemons.
"""

from .config import NanoConfig, load_config
from .guard import ResourceGuard, ResourceSample, IsolationViolationError
from .schema import WORK_SCHEMA, WORK_PRAGMAS
from .work_db import WorkDatabase, QueueItem
from .cas import BlobStore, PayloadTooLargeError
from .acquire import AcquisitionDaemon, FetchResult
from .smoke import SmokeQualification, SmokeReceipt

__all__ = [
    "NanoConfig",
    "load_config",
    "ResourceGuard",
    "ResourceSample",
    "IsolationViolationError",
    "WORK_SCHEMA",
    "WORK_PRAGMAS",
    "WorkDatabase",
    "QueueItem",
    "BlobStore",
    "PayloadTooLargeError",
    "AcquisitionDaemon",
    "FetchResult",
    "SmokeQualification",
    "SmokeReceipt",
]
