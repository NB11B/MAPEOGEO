from __future__ import annotations

from collections import Counter
from typing import Literal

from .cases import SanitizedCase
from .constants import SEMANTIC_RELATION_TYPES
from .probes import B1_PROBE_KEYS, B2_PROBE_KEYS, B3_PROBE_KEYS, B4_PROBE_KEYS
from .solver import SolverResult, solve_case


BaselineName = Literal["B0", "B1", "B2", "B3", "B4"]


def _prior_only(case: SanitizedCase) -> SolverResult:
    counts: Counter[str] = Counter(
        str(edge.get("type"))
        for edge in case.visible_graph.get("edges", [])
        if edge.get("type") in SEMANTIC_RELATION_TYPES
    )
    if not counts:
        return solve_case(case, probe_keys=())
    top = max(counts.values())
    winners = tuple(sorted(rel for rel, count in counts.items() if count == top))
    if len(winners) != 1:
        return solve_case(case, probe_keys=())
    relation = winners[0]
    return SolverResult(
        verdict="PASS",
        predicted_relation=relation,
        ambiguity_set=(relation,),
        evidence_keys=("GLOBAL_RELATION_PRIOR",),
        unsupported_probe_keys=(),
        trace_digest=f"B0:{relation}:{counts[relation]}",
    )


def run_baseline(name: BaselineName, case: SanitizedCase) -> SolverResult:
    if name == "B0":
        return _prior_only(case)
    if name == "B1":
        return solve_case(case, B1_PROBE_KEYS)
    if name == "B2":
        return solve_case(case, B2_PROBE_KEYS)
    if name == "B3":
        return solve_case(case, B3_PROBE_KEYS)
    if name == "B4":
        return solve_case(case, B4_PROBE_KEYS)
    raise ValueError(f"Unknown baseline: {name}")
