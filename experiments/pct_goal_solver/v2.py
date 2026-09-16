"""Explicitly non-frozen fixtures shaped like the archived V2 protocol.

The fixture builder below calls current goal builders. It exists only for
closed-contract rejection tests and cannot be used as the historical V2 corpus.
The old scientific API fails closed rather than returning substitute data.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Mapping, NoReturn

from .goals import FAMILIES, _BUILDERS
from .model import GoalSpec
from .v2_campaign import (
    FrozenV2ReplayError,
    V2_FROZEN_EXECUTION_COMMIT,
)


V2_SPLIT_COUNTS = {"CALIBRATION_V2": 3, "VALIDATION_V2": 1, "SEALED_V2": 2}
V2_SPLIT_BASES = {"CALIBRATION_V2": 1000, "VALIDATION_V2": 2000, "SEALED_V2": 3000}
V2_REQUIRED_DERIVED_TYPES: dict[str, tuple[str, ...]] = {
    "G1": ("BOOLEAN_ZETA_SIGNAL",),
    "G2": ("MATRIX_RANK",),
    "G3": ("CHAIN_RESIDUAL_MATRIX",),
    "G4": (),
    "G5": (),
    "G6": ("CONDITIONING_RISK",),
    "G7": ("NILPOTENCY_RESULT",),
    "G8": ("SYMBOLIC_EXPRESSION",),
    "G9": ("CONVEXITY_VERDICT", "SYMBOLIC_EXPRESSION"),
    "G10": (),
    "G11": (),
    "G12": ("SYMBOLIC_EXPRESSION",),
}


@dataclass(frozen=True)
class LegacyV2ShapedFixture:
    """Current-builder fixture with its non-frozen status inseparably attached."""

    status: str
    splits: Mapping[str, tuple[GoalSpec, ...]]


def _with_legacy_v2_extensions(goal: GoalSpec) -> GoalSpec:
    inputs = dict(goal.inputs)
    if goal.family == "G2":
        observation = inputs["observation_matrix"]
        inputs["rational_matrix"] = replace(
            observation,
            artifact_id=f"{goal.goal_id}:rational_matrix",
            semantic_type="RATIONAL_MATRIX",
        )
    constraints = tuple(goal.constraints) + (
        ("required_derived_types", V2_REQUIRED_DERIVED_TYPES[goal.family]),
    )
    return replace(goal, inputs=inputs, constraints=constraints)


def build_legacy_v2_shaped_fixture() -> LegacyV2ShapedFixture:
    """Build rejection fixtures from current builders, never V2 evidence."""
    splits: dict[str, tuple[GoalSpec, ...]] = {}
    for split in ("CALIBRATION_V2", "VALIDATION_V2", "SEALED_V2"):
        base = V2_SPLIT_BASES[split]
        rows: list[GoalSpec] = []
        for family_index, family in enumerate(FAMILIES):
            for local_index in range(V2_SPLIT_COUNTS[split]):
                goal_id = f"{split.lower()}:{family.lower()}:{local_index:02d}"
                parameter_index = base + 10 * family_index + local_index
                rows.append(
                    _with_legacy_v2_extensions(
                        _BUILDERS[family](goal_id, parameter_index)
                    )
                )
        splits[split] = tuple(rows)
    return LegacyV2ShapedFixture(
        status="CURRENT_BUILDERS_NOT_FROZEN_CORPUS",
        splits=MappingProxyType(splits),
    )


def build_v2_corpus() -> NoReturn:
    """Refuse substitution of current-builder fixtures for frozen V2 data."""
    raise FrozenV2ReplayError(
        "the frozen V2 corpus is unavailable from current builders; inspect "
        f"the historical artifact at commit {V2_FROZEN_EXECUTION_COMMIT}"
    )
