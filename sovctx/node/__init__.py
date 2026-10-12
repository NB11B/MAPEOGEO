"""SOVCTX Node Runtime for Jetson Nano.

Provides isolated resource governance, mutable work database,
content-addressed acquisition CAS, candidate pipeline daemons,
and autonomous research question frontier.
"""

from .config import NanoConfig, load_config
from .guard import ResourceGuard, ResourceSample, IsolationViolationError
from .schema import WORK_SCHEMA, WORK_PRAGMAS
from .work_db import WorkDatabase, QueueItem
from .cas import BlobStore, PayloadTooLargeError
from .acquire import AcquisitionDaemon, FetchResult
from .smoke import SmokeQualification, SmokeReceipt
from .research_question import (
    AutonomousBranchingEngine,
    BranchingTrigger,
    CANONICAL_THREAD_FAMILIES,
    InstitutionalChannelType,
    OpenQuestionLedger,
    PriorityComponents,
    QuestionStatus,
    ResearchQuestion,
    ThreadFamily,
    ThreadFamilyId,
    ThreadSaturationDetector,
    ThreadSaturationState,
)
from .research_frontier import (
    CANONICAL_CROSS_THREAD_BRIDGES,
    CrossThreadBridge,
    DiscoveryReport,
    FrontierCycleAllocation,
    ResearchFrontierCoordinator,
)
from .research_probing import (
    CorpusGraphIndex,
    EpochCheckpoint,
    ProbeOutcome,
    ResearchProber,
    ResearchShakedownSupervisor,
)

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
    "ThreadFamilyId",
    "ThreadFamily",
    "CANONICAL_THREAD_FAMILIES",
    "InstitutionalChannelType",
    "QuestionStatus",
    "PriorityComponents",
    "ResearchQuestion",
    "OpenQuestionLedger",
    "BranchingTrigger",
    "AutonomousBranchingEngine",
    "ThreadSaturationDetector",
    "ThreadSaturationState",
    "CrossThreadBridge",
    "CANONICAL_CROSS_THREAD_BRIDGES",
    "FrontierCycleAllocation",
    "DiscoveryReport",
    "ResearchFrontierCoordinator",
    "CorpusGraphIndex",
    "EpochCheckpoint",
    "ProbeOutcome",
    "ResearchProber",
    "ResearchShakedownSupervisor",
]
