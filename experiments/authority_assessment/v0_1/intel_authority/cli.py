"""Command Line Interface for intel_authority Task T09.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.catalog (Record envelope, Reference, Diagnostic)
2. Interface Reused:
   - assess_case (intel_authority.evaluator)
   - enumerate_actions, enumerate_actors (intel_authority.queries)
   - derive_authority_gaps (intel_authority.gaps)
   - compare_courses (intel_authority.courses)
   - render_explanation, render_reverse_query_report, render_course_comparison_report (intel_authority.reporting)
3. Additional Semantic Responsibility:
   - Explicit CLI arguments for case, context, budget, mode, and output.
   - Zero-implicit-state: No implicit latest pack selection or live source fetch occurs.
   - Deterministic execution with JSON and structured text formats.
4. Qualification Evidence Delta:
   - AQ05, AQ09, AQ20, AQ24, AQ30, AQ37, AQ41, AQ56 CLI contract assertions.
================================================================================
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from experiments.authority_assessment.v0_1.intel_authority.courses import compare_courses
from experiments.authority_assessment.v0_1.intel_authority.evaluator import assess_case
from experiments.authority_assessment.v0_1.intel_authority.gaps import derive_authority_gaps
from experiments.authority_assessment.v0_1.intel_authority.queries import (
    enumerate_actions,
    enumerate_actors,
)
from experiments.authority_assessment.v0_1.intel_authority.reporting import (
    AccessContext,
    filter_assessment_for_reader,
    render_course_comparison_report,
    render_explanation,
    render_reverse_query_report,
)


def _load_json_file(path_str: str) -> Dict[str, Any]:
    p = Path(path_str)
    if not p.is_file():
        raise FileNotFoundError(f"Input file not found: {path_str}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_output(content: str, out_path_str: Optional[str]) -> None:
    if out_path_str:
        out_p = Path(out_path_str)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    else:
        sys.stdout.write(content + "\n")


def cmd_assess(args: argparse.Namespace) -> int:
    case_data = _load_json_file(args.case)
    context_data = _load_json_file(args.context)

    # Invariant: No implicit latest pack or live network fetch
    budget = {"max_rules": args.budget, "max_candidates": args.budget} if args.budget else None

    res = assess_case(case_data, context_data, budget=budget)

    # Derive gaps and attach
    gaps = derive_authority_gaps(res, context_data)
    res["derived_gaps"] = gaps

    audiences = [a.strip() for a in args.reader_audience.split(",")] if args.reader_audience else ["public"]
    access_ctx = AccessContext(
        reader_actor=args.reader_actor or "reader:cli_user",
        clearance_level=args.reader_clearance or "public",
        allowed_audiences=audiences,
    )

    if args.format == "json":
        filtered = filter_assessment_for_reader(res, access_ctx)
        out_text = json.dumps(filtered, indent=2)
    else:
        out_text = render_explanation(res, access_ctx=access_ctx, format_mode="text")

    _write_output(out_text, args.out)
    return 0


def cmd_enumerate(args: argparse.Namespace) -> int:
    domain_data = _load_json_file(args.candidate_domain)
    context_data = _load_json_file(args.context)

    budget = {"max_candidates": args.budget} if args.budget else None

    if "domain" in domain_data:
        query_dict = domain_data
    elif "case_bindings" in domain_data:
        query_dict = {"domain": domain_data}
    else:
        candidates = domain_data.get("candidates", [])
        query_dict = {
            "domain": {
                "ref": domain_data.get("domain_id", "domain:default"),
                "case_bindings": candidates,
            }
        }

    if args.mode == "actions":
        res = enumerate_actions(query_dict, context_data, budget=budget)
    elif args.mode == "actors":
        res = enumerate_actors(query_dict, context_data, budget=budget)
    else:
        raise ValueError(f"Unknown enumerate mode: {args.mode}")

    if args.format == "json":
        out_text = json.dumps(res, indent=2)
    else:
        out_text = render_reverse_query_report(res, format_mode="text")

    _write_output(out_text, args.out)
    return 0


def cmd_gaps(args: argparse.Namespace) -> int:
    case_data = _load_json_file(args.case)
    context_data = _load_json_file(args.context)

    res = assess_case(case_data, context_data)
    gaps = derive_authority_gaps(res, context_data)

    if args.format == "json":
        out_text = json.dumps({"case_id": case_data.get("case_id"), "derived_gaps": gaps}, indent=2)
    else:
        lines = [
            f"DERIVED AUTHORITY GAPS FOR CASE: {case_data.get('case_id')}",
            "--------------------------------------------------------------------------------",
        ]
        if not gaps:
            lines.append("  (No authority gaps identified; conditions satisfied or resolved)")
        else:
            for g in gaps:
                lines.append(f"  - Gap Type: {g.get('gap_type')} | Missing: {g.get('missing_target')}")
                lines.append(f"    Route:    {g.get('resolution_route')}")
        out_text = "\n".join(lines)

    _write_output(out_text, args.out)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    courses_data = _load_json_file(args.courses)
    context_data = _load_json_file(args.context)

    if isinstance(courses_data, list):
        courses_dict = {"courses": courses_data}
    else:
        courses_dict = courses_data

    budget = {"max_courses": args.budget} if args.budget else None
    res = compare_courses(courses=courses_dict, context=context_data, budget=budget)

    if args.format == "json":
        out_text = json.dumps(res, indent=2)
    else:
        out_text = render_course_comparison_report(res, format_mode="text")

    _write_output(out_text, args.out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="intel-authority",
        description="Deterministic intel_authority CLI for actor-to-actor legal authority assessment.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. assess
    p_assess = subparsers.add_parser("assess", help="Assess direct legal authority for an ActionCase.")
    p_assess.add_argument("--case", required=True, help="Path to ActionCase JSON file.")
    p_assess.add_argument("--context", required=True, help="Path to AssessmentContext JSON file.")
    p_assess.add_argument("--budget", type=int, default=1024, help="Budget for rule evaluations (default 1024).")
    p_assess.add_argument("--reader-actor", help="Reader identity for access filtering.")
    p_assess.add_argument("--reader-clearance", default="public", help="Clearance level ('public', 'confidential', 'restricted').")
    p_assess.add_argument("--reader-audience", default="public", help="Comma-separated allowed audiences.")
    p_assess.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    p_assess.add_argument("--out", help="Output file path (default stdout).")

    # 2. enumerate
    p_enum = subparsers.add_parser("enumerate", help="Enumerate supported actions or actors.")
    p_enum.add_argument("--mode", choices=["actions", "actors"], required=True, help="Enumeration mode.")
    p_enum.add_argument("--candidate-domain", required=True, help="Path to CandidateDomain JSON file.")
    p_enum.add_argument("--context", required=True, help="Path to AssessmentContext JSON file.")
    p_enum.add_argument("--actor", help="Actor ID (optional context filter).")
    p_enum.add_argument("--capacity", default="cap:agent", help="Capacity ID.")
    p_enum.add_argument("--operation", help="Operation ID (optional context filter).")
    p_enum.add_argument("--budget", type=int, default=1024, help="Evaluation budget.")
    p_enum.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    p_enum.add_argument("--out", help="Output file path (default stdout).")

    # 3. gaps
    p_gaps = subparsers.add_parser("gaps", help="Derive authority gaps and resolution routes.")
    p_gaps.add_argument("--case", required=True, help="Path to ActionCase JSON file.")
    p_gaps.add_argument("--context", required=True, help="Path to AssessmentContext JSON file.")
    p_gaps.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    p_gaps.add_argument("--out", help="Output file path (default stdout).")

    # 4. compare
    p_comp = subparsers.add_parser("compare", help="Compare multiple courses of action (display_only mode).")
    p_comp.add_argument("--courses", required=True, help="Path to courses JSON file.")
    p_comp.add_argument("--context", required=True, help="Path to AssessmentContext JSON file.")
    p_comp.add_argument("--budget", type=int, default=1024, help="Evaluation budget.")
    p_comp.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    p_comp.add_argument("--out", help="Output file path (default stdout).")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "assess":
            return cmd_assess(args)
        elif args.command == "enumerate":
            return cmd_enumerate(args)
        elif args.command == "gaps":
            return cmd_gaps(args)
        elif args.command == "compare":
            return cmd_compare(args)
        else:
            parser.print_help()
            return 1
    except Exception as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
