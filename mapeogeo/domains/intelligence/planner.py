"""Analytical Course-of-Action (COA) Planner & Multi-Step Authority Exploration.

Discovers and evaluates multi-step courses of action across the functional network:
1. Generates candidate sequences of operational actions toward an objective.
2. Step-by-step authority evaluation using AuthorityEvaluator.
3. Invariant: Analytical Finding != Operational Admission.
   Exploring a COA does not commit work; each step requires separate certification.
4. Identifies unconventional but admissible courses of action when direct pathways
   are legally obstructed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from mapeogeo.domains.authority.certification import (
    AuthorityCertificateWitness,
    CertificateOutcome,
)
from mapeogeo.domains.authority.evaluator import AuthorityEvaluator
from mapeogeo.domains.intelligence.analysis import NetworkIntelligenceGraph
from mapeogeo.domains.intelligence.functions import (
    FunctionalEdge,
    OrganizationalFunction,
)


class CourseStatus(str, Enum):
    """Feasibility and legal admissibility status of a candidate COA."""
    ADMISSIBLE = "admissible"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"
    UNCONVENTIONAL_ADMISSIBLE = "unconventional_admissible"


@dataclass(frozen=True)
class CourseStep:
    """A discrete operational step within a candidate course of action."""
    step_index: int
    actor_id: str
    target_id: str
    operation: str
    action_case: Dict[str, Any]
    disposition: str
    outcome: CertificateOutcome
    decisive_rules: List[str] = field(default_factory=list)
    obstruction_reason: Optional[str] = None


@dataclass
class CandidateCourse:
    """A multi-step course of action evaluated across intelligence and authority profiles."""
    course_id: str
    objective: str
    start_actor: str
    target_actor: str
    steps: List[CourseStep]
    status: CourseStatus
    is_unconventional: bool = False
    blocked_step_index: Optional[int] = None
    diagnostics: List[str] = field(default_factory=list)

    @property
    def is_fully_admissible(self) -> bool:
        return self.status in (CourseStatus.ADMISSIBLE, CourseStatus.UNCONVENTIONAL_ADMISSIBLE)


class CoursePlanner:
    """Explores, discovers, and qualifies candidate courses of action."""

    def __init__(
        self,
        network_graph: NetworkIntelligenceGraph,
        authority_context: Dict[str, Any],
    ) -> None:
        self.network = network_graph
        self.authority_context = authority_context
        self.evaluator = AuthorityEvaluator(authority_context)

    def evaluate_step(
        self,
        step_index: int,
        actor_id: str,
        target_id: str,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> CourseStep:
        """Evaluates legal authority for a single step in a candidate course."""
        case = {
            "id": f"case:coa:step_{step_index:02d}:{operation}",
            "actor_ref": {"id": actor_id, "revision": 1},
            "capacity_ref": {"id": f"cap:{actor_id.split(':')[1] if ':' in actor_id else 'default'}", "revision": 1},
            "affected_scope": {
                "bindings": [
                    {"entity_ref": {"id": target_id, "revision": 1}}
                ]
            },
            "operation_ref": {"id": operation, "revision": 1},
            "parameters": parameters or {},
        }

        assessment = self.evaluator.assess_case(case)
        witness = self.evaluator.certify_work(case)

        disp = assessment.get("disposition", "unresolved")
        obs_reason = None
        if witness.is_obstructed:
            obs_reason = f"Step obstructed: disposition is {disp} under {witness.decisive_rule_refs}"

        return CourseStep(
            step_index=step_index,
            actor_id=actor_id,
            target_id=target_id,
            operation=operation,
            action_case=case,
            disposition=disp,
            outcome=witness.outcome,
            decisive_rules=witness.decisive_rule_refs,
            obstruction_reason=obs_reason,
        )

    def evaluate_path_as_course(
        self,
        course_id: str,
        objective: str,
        path_edges: List[FunctionalEdge],
        is_unconventional: bool = False,
    ) -> CandidateCourse:
        """Evaluates a multi-hop graph path as an analytical course of action."""
        steps: List[CourseStep] = []
        overall_status = CourseStatus.ADMISSIBLE
        blocked_idx = None
        diagnostics = []

        for idx, edge in enumerate(path_edges):
            step = self.evaluate_step(
                step_index=idx,
                actor_id=edge.actor,
                target_id=edge.target_actor,
                operation=edge.operation,
            )
            steps.append(step)

            if step.outcome == CertificateOutcome.OBSTRUCTED:
                overall_status = CourseStatus.BLOCKED
                blocked_idx = idx
                diagnostics.append(f"Step {idx} ({edge.operation}) legally obstructed")
                break
            elif step.outcome == CertificateOutcome.UNRESOLVED and overall_status != CourseStatus.BLOCKED:
                overall_status = CourseStatus.UNRESOLVED

        if overall_status == CourseStatus.ADMISSIBLE and is_unconventional:
            overall_status = CourseStatus.UNCONVENTIONAL_ADMISSIBLE

        start_actor = path_edges[0].actor if path_edges else "unknown"
        target_actor = path_edges[-1].target_actor if path_edges else "unknown"

        return CandidateCourse(
            course_id=course_id,
            objective=objective,
            start_actor=start_actor,
            target_actor=target_actor,
            steps=steps,
            status=overall_status,
            is_unconventional=is_unconventional,
            blocked_step_index=blocked_idx,
            diagnostics=diagnostics,
        )

    def plan_candidate_courses(
        self,
        start_actor: str,
        target_actor: str,
        objective: str,
        max_hops: int = 5,
    ) -> List[CandidateCourse]:
        """Discovers direct and alternative unconventional courses between actors."""
        paths = self.network.find_functional_paths(start_actor, target_actor, max_hops=max_hops)
        courses: List[CandidateCourse] = []

        for i, path in enumerate(paths):
            # If path length > 1, it represents an indirect / alternative routing
            is_unconventional = len(path) > 1
            cid = f"COA-{start_actor.split(':')[-1]}-to-{target_actor.split(':')[-1]}-{i+1:02d}"
            course = self.evaluate_path_as_course(
                course_id=cid,
                objective=objective,
                path_edges=path,
                is_unconventional=is_unconventional,
            )
            courses.append(course)

        # Sort: Admissible first (unconventional then direct), then unresolved, then blocked
        def sort_key(c: CandidateCourse) -> int:
            if c.status == CourseStatus.UNCONVENTIONAL_ADMISSIBLE:
                return 0
            if c.status == CourseStatus.ADMISSIBLE:
                return 1
            if c.status == CourseStatus.UNRESOLVED:
                return 2
            return 3

        return sorted(courses, key=sort_key)
