"""Compatibility entrypoint for the authoritative v0.20 terminal verifier.

The public :func:`verify_terminal_candidate` name predates the closed v0.20
contracts.  It deliberately contains no independent validation logic: every
call is delegated to :func:`v0_20_verifiers.verify_v0_20_goal` so legacy
imports cannot bypass the current goal, candidate, certificate, or pipeline
receipt checks.
"""

from __future__ import annotations

from .model import Artifact, GoalSpec, SolverVisibleGoal, VerificationResult
from .v0_20_verifiers import verify_v0_20_goal


GoalLike = GoalSpec | SolverVisibleGoal


def verify_terminal_candidate(
    goal: GoalLike,
    candidate: Artifact | None,
) -> VerificationResult:
    """Delegate the legacy public name to the sole strict authority."""

    return verify_v0_20_goal(goal, candidate)  # type: ignore[arg-type]
