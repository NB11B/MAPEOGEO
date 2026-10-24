"""Track A — Left-side triangular reconstruction, arithmetic phase macros, and seed constraints."""

from .triangular_reconstruction import (
    LeftTriangularReconstructionResult,
    reconstruct_left_column_from_orcol,
    reconstruct_orcol_from_left_cone,
    verify_checkpoint_01_reconstruction_completeness,
)
from .arithmetic_phase_macros import (
    LeftPhaseMacroResult,
    evaluate_left_black_step_forcing,
    evaluate_autonomous_no11_left_evolution,
)
from .initial_seed_constraints import (
    LeftConeEliminationSample,
    evaluate_left_cone_elimination,
)
from .spatial_transport import (
    SpatialDepthRelationStep,
    SpatialTransportTrajectoryReport,
    SpatiotemporalAlgebraReport,
    SpatiotemporalPhaseRelation,
    analyze_spatiotemporal_relation_algebra,
    trace_spatial_relation_transport,
)

__all__ = [
    "LeftTriangularReconstructionResult",
    "reconstruct_left_column_from_orcol",
    "reconstruct_orcol_from_left_cone",
    "verify_checkpoint_01_reconstruction_completeness",
    "LeftPhaseMacroResult",
    "evaluate_left_black_step_forcing",
    "evaluate_autonomous_no11_left_evolution",
    "LeftConeEliminationSample",
    "evaluate_left_cone_elimination",
    "SpatialDepthRelationStep",
    "SpatialTransportTrajectoryReport",
    "SpatiotemporalAlgebraReport",
    "SpatiotemporalPhaseRelation",
    "analyze_spatiotemporal_relation_algebra",
    "trace_spatial_relation_transport",
]
