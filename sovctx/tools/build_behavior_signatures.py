from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from graph_io import ROOT, load_records, split_records


def build_signatures() -> list[dict[str, Any]]:
    records = load_records()
    nodes, edges = split_records(records)
    node_by_id = {node["id"]: node for node in nodes}

    family_by_equation: dict[str, list[str]] = {}
    for edge in edges:
        if edge["edge_type"] == "MEMBER_OF_EQUATION_FAMILY":
            family_by_equation.setdefault(edge["source"], []).append(edge["target"])

    signatures: list[dict[str, Any]] = []
    for equation in sorted(
        (node for node in nodes if node["type"] == "EQUATION"),
        key=lambda node: node["id"],
    ):
        test_types = sorted({
            node_by_id[test_id]["test_type"]
            for test_id in equation.get("behavioral_test_ids", [])
            if test_id in node_by_id
        })
        signatures.append({
            "equation_id": equation["id"],
            "namespace": equation["namespace"],
            "equation_kind": equation.get("equation_kind"),
            "family_ids": sorted(family_by_equation.get(equation["id"], [])),
            "operator_ids": sorted(equation.get("operator_ids", [])),
            "behavioral_test_types": test_types,
            "assumption_ids": sorted(equation.get("assumption_ids", [])),
            "invariant_ids": sorted(equation.get("invariant_ids", [])),
            "verification_status": equation.get("verification_status"),
            "transcription_status": equation.get("transcription_status"),
        })
    return signatures


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SOVCTX equation behavioral signatures.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    signatures = build_signatures()
    text = "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in signatures) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(json.dumps({"output": str(args.output), "count": len(signatures)}, indent=2))
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
