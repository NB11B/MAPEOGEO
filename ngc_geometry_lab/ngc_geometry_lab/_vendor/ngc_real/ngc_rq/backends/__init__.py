"""Execution backends for real-phase circuits."""

from .local_gate import apply_local_gate, iter_local_blocks
from .dual_lane import apply_local_gate_dual_lane, DualLaneStats
from .vectorized_local import apply_local_gate_vectorized, VectorizedLocalStats
from .threaded_dual_lane import apply_local_gate_threaded_dual_lane, ThreadedDualLaneStats
