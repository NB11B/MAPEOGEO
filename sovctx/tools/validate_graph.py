from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]

JSONL_FILES = [
    ROOT / "operator_atlas" / "operators.jsonl",
    ROOT / "corpus" / "sources.jsonl",
    ROOT / "corpus" / "source_fragments.jsonl",
    ROOT / "graph" / "equations.jsonl",
    ROOT / "graph" / "symbols.jsonl",
    ROOT / "graph" / "assumptions.jsonl",
    ROOT / "graph" / "behavioral_tests.jsonl",
    ROOT / "graph" / "invariants.jsonl",
    ROOT / "unresolved" / "open_questions.jsonl",
    ROOT / "graph" / "entities.jsonl",
    ROOT / "graph" / "claims.jsonl",
    ROOT / "graph" / "edges.jsonl",
]

ALLOWED_NAMESPACES = {"ANC", "SOV", "RUS", "WEST", "SYN", "MOD", "CASE", "OPEN", "OP"}
COMPARISON_EDGES = {"PARALLEL_TO", "STRUCTURALLY_ANALOGOUS_TO", "DIFFERS_FROM", "ALTERNATE_INTERPRETATION_OF"}
FORBIDDEN_EDGE_TYPES = {"SAME_OPERATOR", "EQUIVALENT_TO"}
SOURCE_NATIVE_NAMESPACES = {"SOV", "RUS"}


class ValidationError(RuntimeError):
    pass


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
        if not isinstance(obj, dict):
            raise ValidationError(f"{path}:{lineno}: JSONL record must be an object")
        records.append(obj)
    return records


def iter_records() -> Iterable[tuple[Path, dict[str, Any]]]:
    for path in JSONL_FILES:
        for record in read_jsonl(path):
            yield path, record


def validate_common(path: Path, record: dict[str, Any]) -> None:
    for key in ("id", "type", "namespace", "label"):
        if key not in record or record[key] in ("", None):
            raise ValidationError(f"{path}: record missing required field {key}: {record}")
    if record["namespace"] not in ALLOWED_NAMESPACES:
        raise ValidationError(f"{path}: invalid namespace {record['namespace']} for {record['id']}")


def validate_source(path: Path, record: dict[str, Any]) -> None:
    if record["type"] not in {"PUBLICATION", "ARCHIVAL_DOCUMENT"}:
        return
    if record["id"] == "SRC:CHAT_SEED_000":
        return
    for key in ("provenance_class", "knowledge_status", "verification_status"):
        if not record.get(key):
            raise ValidationError(f"{path}: source {record['id']} missing {key}")


def validate_fragment(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "SOURCE_FRAGMENT":
        return
    for key in ("source_id", "locator", "evidence_basis", "verification_status"):
        if not record.get(key):
            raise ValidationError(f"{path}: source fragment {record['id']} missing {key}")
    source = nodes.get(record["source_id"])
    if not source or source.get("type") not in {"PUBLICATION", "ARCHIVAL_DOCUMENT"}:
        raise ValidationError(f"{path}: source fragment {record['id']} references invalid source {record['source_id']}")


def validate_claim(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "CLAIM":
        return
    status = record.get("knowledge_status")
    sources = record.get("source_ids", [])
    if status not in {"I", "H", "M", "A"} and not sources:
        raise ValidationError(f"{path}: claim {record['id']} requires source_ids or explicit inferred/synthesis status")

    fragments = record.get("source_fragment_ids", [])
    if record.get("verification_status") == "verified_primary":
        if not fragments:
            raise ValidationError(f"{path}: verified_primary claim {record['id']} requires source_fragment_ids")
        for fragment_id in fragments:
            fragment = nodes.get(fragment_id)
            if not fragment or fragment.get("type") != "SOURCE_FRAGMENT":
                raise ValidationError(f"{path}: claim {record['id']} references invalid fragment {fragment_id}")
            if fragment.get("verification_status") not in {"verified_primary", "verified_scan"}:
                raise ValidationError(
                    f"{path}: verified_primary claim {record['id']} relies on non-primary fragment {fragment_id}"
                )
            if fragment.get("source_id") not in sources:
                raise ValidationError(
                    f"{path}: claim {record['id']} fragment {fragment_id} comes from uncited source {fragment.get('source_id')}"
                )



def validate_equation(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "EQUATION":
        return
    for key in ("latex", "equation_kind", "source_ids", "transcription_status", "verification_status"):
        if not record.get(key):
            raise ValidationError(f"{path}: equation {record['id']} missing {key}")
    for source_id in record.get("source_ids", []):
        source = nodes.get(source_id)
        if not source or source.get("type") not in {"PUBLICATION", "ARCHIVAL_DOCUMENT"}:
            raise ValidationError(f"{path}: equation {record['id']} references invalid source {source_id}")
    for fragment_id in record.get("source_fragment_ids", []):
        fragment = nodes.get(fragment_id)
        if not fragment or fragment.get("type") != "SOURCE_FRAGMENT":
            raise ValidationError(f"{path}: equation {record['id']} references invalid fragment {fragment_id}")
        if fragment.get("source_id") not in record.get("source_ids", []):
            raise ValidationError(
                f"{path}: equation {record['id']} fragment {fragment_id} comes from uncited source"
            )
    typed_lists = {
        "symbol_ids": "SYMBOL",
        "assumption_ids": "ASSUMPTION",
        "invariant_ids": "INVARIANT",
        "behavioral_test_ids": "BEHAVIORAL_TEST",
    }
    for field, expected_type in typed_lists.items():
        for node_id in record.get(field, []):
            node = nodes.get(node_id)
            if not node or node.get("type") != expected_type:
                raise ValidationError(
                    f"{path}: equation {record['id']} {field} references non-{expected_type} {node_id}"
                )


def validate_behavioral_test(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "BEHAVIORAL_TEST":
        return
    for key in ("equation_id", "test_type", "expected", "qualification_role"):
        if not record.get(key):
            raise ValidationError(f"{path}: behavioral test {record['id']} missing {key}")
    equation = nodes.get(record["equation_id"])
    if not equation or equation.get("type") != "EQUATION":
        raise ValidationError(f"{path}: behavioral test {record['id']} references invalid equation")
    if record["id"] not in equation.get("behavioral_test_ids", []):
        raise ValidationError(
            f"{path}: behavioral test {record['id']} not declared by equation {equation['id']}"
        )


def validate_edge(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "EDGE":
        return
    edge_type = record.get("edge_type")
    if not edge_type:
        raise ValidationError(f"{path}: edge {record['id']} missing edge_type")
    if edge_type in FORBIDDEN_EDGE_TYPES:
        raise ValidationError(f"{path}: forbidden strong semantic edge {edge_type}: {record['id']}")
    source_id = record.get("source")
    target_id = record.get("target")
    if not source_id or not target_id:
        raise ValidationError(f"{path}: edge {record['id']} missing source/target")
    s = nodes.get(source_id)
    t = nodes.get(target_id)
    if not s or not t:
        raise ValidationError(f"{path}: edge {record['id']} references unknown node(s)")
    namespaces = {s["namespace"], t["namespace"]}
    if "WEST" in namespaces and namespaces & SOURCE_NATIVE_NAMESPACES and edge_type not in COMPARISON_EDGES:
        raise ValidationError(f"{path}: WEST/SOV-RUS edge must be comparison-only: {record['id']}")

    if edge_type == "SUPPORTS":
        if s.get("type") != "SOURCE_FRAGMENT" or t.get("type") != "CLAIM":
            raise ValidationError(f"{path}: SUPPORTS must connect SOURCE_FRAGMENT -> CLAIM: {record['id']}")
        if s["id"] not in t.get("source_fragment_ids", []):
            raise ValidationError(f"{path}: SUPPORTS edge not declared by claim fragment list: {record['id']}")

    if edge_type == "EXTRACTED_FROM":
        if s.get("type") != "SOURCE_FRAGMENT" or t.get("type") not in {"PUBLICATION", "ARCHIVAL_DOCUMENT"}:
            raise ValidationError(f"{path}: EXTRACTED_FROM must connect SOURCE_FRAGMENT -> source record: {record['id']}")
        if s.get("source_id") != t.get("id"):
            raise ValidationError(f"{path}: EXTRACTED_FROM target disagrees with fragment source_id: {record['id']}")

    if edge_type == "ASSERTS":
        if s.get("type") not in {"PUBLICATION", "ARCHIVAL_DOCUMENT"} or t.get("type") != "CLAIM":
            raise ValidationError(f"{path}: ASSERTS must connect source record -> CLAIM: {record['id']}")
        if s["id"] not in t.get("source_ids", []):
            raise ValidationError(f"{path}: ASSERTS source is not cited by target claim: {record['id']}")

    if edge_type == "USES_OPERATOR" and t.get("type") != "OPERATOR":
        raise ValidationError(f"{path}: USES_OPERATOR target must be OPERATOR: {record['id']}")

    if edge_type == "ENCODES_EQUATION":
        if s.get("type") != "SOURCE_FRAGMENT" or t.get("type") != "EQUATION":
            raise ValidationError(f"{path}: ENCODES_EQUATION must connect SOURCE_FRAGMENT -> EQUATION: {record['id']}")
        if s.get("source_id") not in t.get("source_ids", []):
            raise ValidationError(f"{path}: ENCODES_EQUATION fragment source is not cited by equation: {record['id']}")

    if edge_type == "MEMBER_OF_EQUATION_FAMILY":
        if s.get("type") != "EQUATION" or t.get("type") != "EQUATION_FAMILY":
            raise ValidationError(f"{path}: MEMBER_OF_EQUATION_FAMILY must connect EQUATION -> EQUATION_FAMILY: {record['id']}")

    if edge_type == "SOURCE_TARGETS_EQUATION_FAMILY":
        if s.get("type") not in {"PUBLICATION", "ARCHIVAL_DOCUMENT"} or t.get("type") != "EQUATION_FAMILY":
            raise ValidationError(f"{path}: SOURCE_TARGETS_EQUATION_FAMILY must connect source -> EQUATION_FAMILY: {record['id']}")

    if edge_type == "IMPLEMENTS_OPERATOR":
        if s.get("type") != "EQUATION" or t.get("type") != "OPERATOR":
            raise ValidationError(f"{path}: IMPLEMENTS_OPERATOR must connect EQUATION -> OPERATOR: {record['id']}")

    typed_targets = {
        "HAS_SYMBOL": "SYMBOL",
        "HAS_ASSUMPTION": "ASSUMPTION",
        "HAS_BEHAVIORAL_TEST": "BEHAVIORAL_TEST",
        "PRESERVES_INVARIANT": "INVARIANT",
    }
    if edge_type in typed_targets:
        if s.get("type") != "EQUATION" or t.get("type") != typed_targets[edge_type]:
            raise ValidationError(
                f"{path}: {edge_type} has invalid endpoint types on {record['id']}"
            )


def validate_temporal_edge(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record.get("type") != "EDGE":
        return
    if record.get("edge_type") not in {"DOCUMENTED_INFLUENCE", "USES_CONCEPT_FROM", "USES_EQUATION_FROM", "CITES"}:
        return
    s = nodes.get(record.get("source"))
    t = nodes.get(record.get("target"))
    if not s or not t:
        return
    s_date = str(s.get("publication_date") or s.get("valid_from") or "")
    t_date = str(t.get("publication_date") or t.get("valid_from") or "")
    # Only compare leading ISO years; ambiguous or absent dates fail open here and must be audited separately.
    if len(s_date) >= 4 and len(t_date) >= 4 and s_date[:4].isdigit() and t_date[:4].isdigit():
        if int(t_date[:4]) > int(s_date[:4]):
            raise ValidationError(
                f"{path}: temporal violation on {record['id']}: source-side event {s_date} depends on later target {t_date}"
            )


def main() -> int:
    records = list(iter_records())
    seen: dict[str, Path] = {}
    nodes: dict[str, dict[str, Any]] = {}

    for path, record in records:
        validate_common(path, record)
        rid = record["id"]
        if rid in seen:
            raise ValidationError(f"duplicate id {rid} in {seen[rid]} and {path}")
        seen[rid] = path
        if record["type"] != "EDGE":
            nodes[rid] = record

    for path, record in records:
        validate_source(path, record)
        validate_fragment(path, record, nodes)
        validate_claim(path, record, nodes)
        validate_equation(path, record, nodes)
        validate_behavioral_test(path, record, nodes)

    support_pairs: set[tuple[str, str]] = set()
    for path, record in records:
        validate_edge(path, record, nodes)
        validate_temporal_edge(path, record, nodes)
        if record.get("type") == "EDGE" and record.get("edge_type") == "SUPPORTS":
            support_pairs.add((record["source"], record["target"]))

    for record in nodes.values():
        if record.get("type") != "CLAIM":
            continue
        for fragment_id in record.get("source_fragment_ids", []):
            if (fragment_id, record["id"]) not in support_pairs:
                raise ValidationError(
                    f"claim {record['id']} lists fragment {fragment_id} but lacks SUPPORTS edge"
                )

    print(f"SOVCTX validation PASS: {len(records)} records, {len(nodes)} nodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
