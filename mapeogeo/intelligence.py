"""MAPEOGEO Intelligence Domain CLI Entrypoint.

Usage:
    python -m mapeogeo.intelligence matrix-query --source <func> --target <func> [--graph-file <path>]
    python -m mapeogeo.intelligence detect-gaps [--graph-file <path>]
    python -m mapeogeo.intelligence plan-coa --start <actor> --target <actor> --objective <text> --pack-file <path> [--graph-file <path>]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from mapeogeo.domains.intelligence import (
    ALL_FUNCTIONS,
    CoursePlanner,
    FunctionalEdge,
    FunctionalMatrix,
    IntelligenceGapEngine,
    NetworkIntelligenceGraph,
    OrganizationalFunction,
)


def _load_or_create_graph(graph_file: Optional[str]) -> NetworkIntelligenceGraph:
    """Loads a graph from JSON file or provides a standard reference topology."""
    graph = NetworkIntelligenceGraph()
    if graph_file:
        p = Path(graph_file)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            for n in data.get("nodes", []):
                graph.add_node(n["id"], OrganizationalFunction(n["function"]))
            for e in data.get("edges", []):
                edge = FunctionalEdge(
                    edge_id=e["id"],
                    source_function=OrganizationalFunction(e["source_function"]),
                    target_function=OrganizationalFunction(e["target_function"]),
                    actor=e["actor"],
                    target_actor=e["target_actor"],
                    operation=e["operation"],
                    epistemic_state=e.get("epistemic_state", "supported"),
                )
                graph.add_edge(edge)
            return graph

    # Default reference topology
    graph.add_node("actor:collector:alpha", OrganizationalFunction.INTELLIGENCE)
    graph.add_node("actor:analyst:beta", OrganizationalFunction.INTELLIGENCE)
    graph.add_node("actor:director:gamma", OrganizationalFunction.GOVERNANCE)
    graph.add_node("actor:marshal:delta", OrganizationalFunction.ENFORCEMENT)
    graph.add_edge(
        FunctionalEdge(
            edge_id="edge:col_ana",
            source_function=OrganizationalFunction.INTELLIGENCE,
            target_function=OrganizationalFunction.INTELLIGENCE,
            actor="actor:collector:alpha",
            target_actor="actor:analyst:beta",
            operation="op:feed_raw_sensor",
        )
    )
    graph.add_edge(
        FunctionalEdge(
            edge_id="edge:ana_dir",
            source_function=OrganizationalFunction.INTELLIGENCE,
            target_function=OrganizationalFunction.GOVERNANCE,
            actor="actor:analyst:beta",
            target_actor="actor:director:gamma",
            operation="op:brief_intelligence",
        )
    )
    graph.add_edge(
        FunctionalEdge(
            edge_id="edge:dir_mar",
            source_function=OrganizationalFunction.GOVERNANCE,
            target_function=OrganizationalFunction.ENFORCEMENT,
            actor="actor:director:gamma",
            target_actor="actor:marshal:delta",
            operation="op:issue_operational_order",
        )
    )
    return graph


def cmd_matrix_query(args: argparse.Namespace) -> int:
    """Queries cells in the 7x7 organizational functional matrix."""
    graph = _load_or_create_graph(args.graph_file)
    matrix = graph.to_functional_matrix()

    try:
        src_func = OrganizationalFunction(args.source)
        tgt_func = OrganizationalFunction(args.target)
    except ValueError as e:
        print(f"Error: Invalid functional coordinate. Must be one of {[f.value for f in ALL_FUNCTIONS]}", file=sys.stderr)
        return 1

    cells = matrix.query_cell(src_func, tgt_func)
    out = {
        "source_function": src_func.value,
        "target_function": tgt_func.value,
        "edge_count": len(cells),
        "edges": [
            {
                "edge_id": c.edge_id,
                "actor": c.actor,
                "target_actor": c.target_actor,
                "operation": c.operation,
            }
            for c in cells
        ],
    }
    print(json.dumps(out, indent=2))
    return 0


def cmd_detect_gaps(args: argparse.Namespace) -> int:
    """Scans the functional matrix and generates PIRs and deficiency queue."""
    graph = _load_or_create_graph(args.graph_file)
    matrix = graph.to_functional_matrix()
    engine = IntelligenceGapEngine(matrix)

    pirs = engine.detect_matrix_gaps()
    queue = engine.compile_deficiency_queue()

    out = {
        "pir_count": len(pirs),
        "pirs": [
            {
                "pir_id": p.pir_id,
                "priority": p.priority,
                "target_function": p.target_function.value,
                "target_entity": p.target_entity,
                "gap_kind": p.gap_kind.value,
                "required_operator": p.required_operator,
                "collection_directive": p.collection_directive,
            }
            for p in pirs
        ],
        "deficiency_queue": queue,
    }
    print(json.dumps(out, indent=2))
    return 0


def cmd_plan_coa(args: argparse.Namespace) -> int:
    """Explores candidate multi-step courses of action across the network."""
    pack_path = Path(args.pack_file)
    if not pack_path.exists():
        print(f"Error: Rule pack file not found: {pack_path}", file=sys.stderr)
        return 1

    with open(pack_path, "r", encoding="utf-8") as f:
        pack_data = json.load(f)

    context = {
        "ref": {"id": "ctx:cli_coa", "revision": 1},
        "packs": [pack_data],
        "evidence": {},
    }

    graph = _load_or_create_graph(args.graph_file)
    planner = CoursePlanner(graph, context)
    courses = planner.plan_candidate_courses(
        start_actor=args.start,
        target_actor=args.target,
        objective=args.objective,
    )

    out = {
        "objective": args.objective,
        "start_actor": args.start,
        "target_actor": args.target,
        "courses_discovered": len(courses),
        "courses": [
            {
                "course_id": c.course_id,
                "status": c.status.value,
                "is_unconventional": c.is_unconventional,
                "steps_count": len(c.steps),
                "steps": [
                    {
                        "step_index": s.step_index,
                        "actor": s.actor_id,
                        "target": s.target_id,
                        "operation": s.operation,
                        "outcome": s.outcome.value,
                        "disposition": s.disposition,
                    }
                    for s in c.steps
                ],
            }
            for c in courses
        ],
    }
    print(json.dumps(out, indent=2))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m mapeogeo.intelligence",
        description="MAPEOGEO Intelligence Domain Subsystem CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # matrix-query
    p_mat = subparsers.add_parser("matrix-query", help="Query cell in 7x7 organizational functional matrix")
    p_mat.add_argument("--source", required=True, help="Source organizational function")
    p_mat.add_argument("--target", required=True, help="Target organizational function")
    p_mat.add_argument("--graph-file", required=False, help="Path to network graph JSON file")
    p_mat.set_defaults(func=cmd_matrix_query)

    # detect-gaps
    p_gaps = subparsers.add_parser("detect-gaps", help="Detect intelligence gaps and generate PIRs")
    p_gaps.add_argument("--graph-file", required=False, help="Path to network graph JSON file")
    p_gaps.set_defaults(func=cmd_detect_gaps)

    # plan-coa
    p_coa = subparsers.add_parser("plan-coa", help="Plan candidate multi-step courses of action")
    p_coa.add_argument("--start", required=True, help="Start actor ID")
    p_coa.add_argument("--target", required=True, help="Target actor ID")
    p_coa.add_argument("--objective", required=True, help="Strategic objective description")
    p_coa.add_argument("--pack-file", required=True, help="Path to reviewed legal rule pack JSON file")
    p_coa.add_argument("--graph-file", required=False, help="Path to network graph JSON file")
    p_coa.set_defaults(func=cmd_plan_coa)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
