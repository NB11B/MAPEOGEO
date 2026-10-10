"""MAPEOGEO Authority Domain CLI Entrypoint.

Usage:
    python -m mapeogeo.authority verify-pack --pack-file <path> [--text-file <path>]
    python -m mapeogeo.authority assess --case-file <path> --pack-file <path>
    python -m mapeogeo.authority certify --case-file <path> --pack-file <path>
    python -m mapeogeo.authority inspect-matrix --actor <id> --affected <id> --operation <id> --pack-file <path>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from mapeogeo.domains.authority import (
    AuthorityCertificateWitness,
    AuthorityEvaluator,
    LegalPackIntake,
)


def cmd_verify_pack(args: argparse.Namespace) -> int:
    """Validates rule pack schema, source text digest, and reviewer record."""
    pack_path = Path(args.pack_file)
    if not pack_path.exists():
        print(f"Error: Rule pack file not found: {pack_path}", file=sys.stderr)
        return 1

    with open(pack_path, "r", encoding="utf-8") as f:
        pack_data = json.load(f)

    source_text = None
    if args.text_file:
        text_path = Path(args.text_file)
        if text_path.exists():
            with open(text_path, "r", encoding="utf-8") as f:
                source_text = f.read()

    result = LegalPackIntake.validate_and_ingest(pack_data, source_text=source_text)
    out = {
        "valid": result.valid,
        "pack_id": result.pack_id,
        "rules_count": len(result.rule_pack.rules) if result.rule_pack else 0,
        "diagnostics": result.diagnostics,
    }
    print(json.dumps(out, indent=2))
    return 0 if result.valid else 1


def cmd_assess(args: argparse.Namespace) -> int:
    """Evaluates an ActionCase against a rule pack and outputs complete LegalAssessment."""
    case_path = Path(args.case_file)
    pack_path = Path(args.pack_file)

    if not case_path.exists() or not pack_path.exists():
        print("Error: Input files not found", file=sys.stderr)
        return 1

    with open(case_path, "r", encoding="utf-8") as f:
        case_data = json.load(f)
    with open(pack_path, "r", encoding="utf-8") as f:
        pack_data = json.load(f)

    context = {
        "ref": {"id": "ctx:cli_assessment", "revision": 1},
        "packs": [pack_data],
        "evidence": {},
    }
    evaluator = AuthorityEvaluator(context)
    assessment = evaluator.assess_case(case_data)
    print(json.dumps(assessment, indent=2))
    return 0


def cmd_certify(args: argparse.Namespace) -> int:
    """Evaluates an ActionCase and outputs domain certification witness C_A."""
    case_path = Path(args.case_file)
    pack_path = Path(args.pack_file)

    if not case_path.exists() or not pack_path.exists():
        print("Error: Input files not found", file=sys.stderr)
        return 1

    with open(case_path, "r", encoding="utf-8") as f:
        case_data = json.load(f)
    with open(pack_path, "r", encoding="utf-8") as f:
        pack_data = json.load(f)

    context = {
        "ref": {"id": "ctx:cli_certification", "revision": 1},
        "packs": [pack_data],
        "evidence": {},
    }
    evaluator = AuthorityEvaluator(context)
    witness = evaluator.certify_work(case_data)
    out = {
        "work_id": witness.work_id,
        "outcome": witness.outcome.value,
        "status": witness.status,
        "is_certified": witness.is_certified,
        "is_obstructed": witness.is_obstructed,
        "is_unresolved": witness.is_unresolved,
        "decisive_rule_refs": witness.decisive_rule_refs,
        "obstruction_reason": witness.obstruction_reason,
    }
    print(json.dumps(out, indent=2))
    return 0 if witness.is_certified else (2 if witness.is_unresolved else 3)


def cmd_inspect_matrix(args: argparse.Namespace) -> int:
    """Queries authority matrix cell M_A(a, b | o)."""
    pack_path = Path(args.pack_file)
    if not pack_path.exists():
        print("Error: Rule pack file not found", file=sys.stderr)
        return 1

    with open(pack_path, "r", encoding="utf-8") as f:
        pack_data = json.load(f)

    context = {
        "ref": {"id": "ctx:cli_matrix", "revision": 1},
        "packs": [pack_data],
        "evidence": {},
    }
    evaluator = AuthorityEvaluator(context)
    res = evaluator.evaluate_matrix_cell(
        actor_id=args.actor,
        affected_actor_id=args.affected,
        operation_id=args.operation,
    )
    print(json.dumps(res, indent=2))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m mapeogeo.authority",
        description="MAPEOGEO Deterministic Legal Authority Subsystem CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # verify-pack
    p_verify = subparsers.add_parser("verify-pack", help="Verify rule pack integrity and reviewer record")
    p_verify.add_argument("--pack-file", required=True, help="Path to rule pack JSON file")
    p_verify.add_argument("--text-file", required=False, help="Path to authoritative source text file")
    p_verify.set_defaults(func=cmd_verify_pack)

    # assess
    p_assess = subparsers.add_parser("assess", help="Assess action case against reviewed rule pack")
    p_assess.add_argument("--case-file", required=True, help="Path to action case JSON file")
    p_assess.add_argument("--pack-file", required=True, help="Path to rule pack JSON file")
    p_assess.set_defaults(func=cmd_assess)

    # certify
    p_cert = subparsers.add_parser("certify", help="Certify action case for UoW admission")
    p_cert.add_argument("--case-file", required=True, help="Path to action case JSON file")
    p_cert.add_argument("--pack-file", required=True, help="Path to rule pack JSON file")
    p_cert.set_defaults(func=cmd_certify)

    # inspect-matrix
    p_mat = subparsers.add_parser("inspect-matrix", help="Inspect authority matrix cell M_A(a, b | o)")
    p_mat.add_argument("--actor", required=True, help="Actor ID")
    p_mat.add_argument("--affected", required=True, help="Affected Actor ID")
    p_mat.add_argument("--operation", required=True, help="Operation ID")
    p_mat.add_argument("--pack-file", required=True, help="Path to rule pack JSON file")
    p_mat.set_defaults(func=cmd_inspect_matrix)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
