#!/usr/bin/env python3
"""
Data Models for Milestone SOVCTX-DEV3 Regulatory Qualification.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Dev3GateResult:
    gate_id: str
    description: str
    passed: bool
    observed_value: Any
    threshold: Any
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Dev3QualificationReport:
    milestone: str
    hardware: str
    status: str
    execution_time_seconds: float
    total_gates: int
    gates_passed: int
    gates_failed: int
    summary_metrics: Dict[str, Any]
    gate_results: List[Dev3GateResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "milestone": self.milestone,
            "hardware": self.hardware,
            "status": self.status,
            "execution_time_seconds": self.execution_time_seconds,
            "total_gates": self.total_gates,
            "gates_passed": self.gates_passed,
            "gates_failed": self.gates_failed,
            "summary_metrics": self.summary_metrics,
            "gate_results": [g.to_dict() for g in self.gate_results],
        }
