# SPDX-License-Identifier: MIT
"""Latency Profiler for PDI-135M-v0.3.

Provides precise wall-clock latency measurement for:
1. Candidate Generation
2. State Projection
3. Selector Inference / Decision
4. Serialization and Adaptation
5. End-to-End Pipeline
"""

from __future__ import annotations

import time
from typing import Dict, Optional


class LatencyProfiler:
    """Scoped stopwatch timer for benchmark stages."""

    def __init__(self) -> None:
        self._starts: Dict[str, float] = {}
        self.measurements_ms: Dict[str, float] = {}

    def start(self, stage: str) -> None:
        self._starts[stage] = time.perf_counter()

    def stop(self, stage: str) -> float:
        if stage not in self._starts:
            raise KeyError(f"Stage '{stage}' was not started.")
        elapsed_ms = (time.perf_counter() - self._starts[stage]) * 1000.0
        self.measurements_ms[stage] = elapsed_ms
        return elapsed_ms

    def get(self, stage: str, default: float = 0.0) -> float:
        return self.measurements_ms.get(stage, default)

    def reset(self) -> None:
        self._starts.clear()
        self.measurements_ms.clear()
