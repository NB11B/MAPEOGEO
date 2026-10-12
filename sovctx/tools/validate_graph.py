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
    ROOT / "graph" / "equation_families.jsonl",
    ROOT / "graph" / "symbols.jsonl",
    ROOT / "graph" / "method_episodes.jsonl",
    ROOT / "graph" / "negative_information.jsonl",
    ROOT / "graph" / "method_lenses.jsonl",
    ROOT / "graph" / "problems.jsonl",
    ROOT / "graph" / "perspective_projections.jsonl",
    ROOT / "graph" / "insights.jsonl",
    ROOT / "graph" / "method_primitives.jsonl",
    ROOT / "graph" / "primitive_compositions.jsonl",
    ROOT / "graph" / "lens_normal_forms.jsonl",
    ROOT / "graph" / "synthetic_lenses.jsonl",
    ROOT / "graph" / "assumptions.jsonl",
    ROOT / "graph" / "behavioral_tests.jsonl",
    ROOT / "graph" / "invariants.jsonl",
    ROOT / "unresolved" / "open_questions.jsonl",
    ROOT / "graph" / "entities.jsonl",
    ROOT / "graph" / "claims.jsonl",
    ROOT / "graph" / "edges.jsonl",
]

ALLOWED_NAMESPACES = {"ANC", "SOV", "RUS", "WEST", "SYN", "MOD", "CASE", "OPEN", "OP"}
ALLOWED_REALMS = {
    "HISTORICAL",
    "MATHEMATICAL",
    "METHODOLOGICAL_PERSPECTIVE",
    "EXPERIMENTAL_APPLICATION",
}
COMPARISON_EDGES = {"PARALLEL_TO", "STRUCTURALLY_ANALOGOUS_TO", "DIFFERS_FROM", "ALTERNATE_INTERPRETATION_OF"}
FORBIDDEN_EDGE_TYPES = {"SAME_OPERATOR", "EQUIVALENT_TO"}
SOURCE_NATIVE_NAMESPACES = {"SOV", "RUS"}

TRANSFORMATION_EDGE_TYPES = {
    "REDUCES_TO",
    "SPECIAL_CASE_OF",
    "LINEARIZES_TO",
    "DUAL_TO",
    "ADJOINT_OF",
    "REGULARIZES",
    "DISCRETIZES",
    "VARIATIONAL_FORM_OF",
    "STABILITY_CERTIFICATE_FOR",
    "INVERSE_OF",
    "APPROXIMATES",
    "MOMENT_CLOSURE_OF",
}

HISTORICAL_EDGE_TYPES = {
    "AFFILIATED_WITH",
    "ASSERTS",
    "AUTHORED",
    "CITES",
    "COAUTHORED",
    "DOCUMENTED_ANCESTRY",
    "DOCUMENTED_INFLUENCE",
    "EDITION_OF",
    "EXTRACTED_FROM",
    "MEASURES",
    "MENTIONS",
    "PUBLISHED_BY",
    "REPRODUCES",
    "REQUIRES_SOURCE",
    "SOURCE_TARGETS_EQUATION_FAMILY",
    "SUPPORTS",
    "USES_OPERATOR",
}

MATHEMATICAL_EDGE_TYPES = {
    "ENCODES_EQUATION",
    "HAS_ASSUMPTION",
    "HAS_BEHAVIORAL_TEST",
    "HAS_SYMBOL",
    "IMPLEMENTS_OPERATOR",
    "MEMBER_OF_EQUATION_FAMILY",
    "PRESERVES_INVARIANT",
    "STRUCTURALLY_ANALOGOUS_TO",
} | TRANSFORMATION_EDGE_TYPES

METHODOLOGICAL_PERSPECTIVE_EDGE_TYPES = {
    "AVOIDS_COMPUTING",
    "DERIVED_FROM_METHOD_EPISODE",
    "ENABLES_OMISSION_OF",
    "COMPOSES_WITH",
    "REQUIRES",
    "PRESERVES",
    "DISCARDS",
    "INTRODUCES",
    "NORMALIZES_TO",
    "ORDER_SENSITIVE_WITH",
    "RECONSTRUCTS_METHOD",
    "SYNTHESIZED_FROM",
}

EXPERIMENTAL_APPLICATION_EDGE_TYPES = {
    "APPLIES_TO_PROBLEM",
    "REVEALS",
    "COMPLEMENTS",
    "CONFLICTS_WITH",
    "ENABLES",
    "VALID_FOR_PROBLEM",
}


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
        "operator_ids": "OPERATOR",
    }
    for field, expected_type in typed_lists.items():
        for node_id in record.get(field, []):
            node = nodes.get(node_id)
            if not node or node.get("type") != expected_type:
                raise ValidationError(
                    f"{path}: equation {record['id']} {field} references non-{expected_type} {node_id}"
                )


def validate_method_episode(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "METHOD_EPISODE":
        return
    for key in (
        "s0_initial_problem",
        "q_deficiency",
        "a_admissibility",
        "x_auxiliary_construction",
        "c_constraints_invariants",
        "t_transformation_decision",
        "s1_resulting_conclusion",
        "negative_information",
    ):
        if key not in record or not isinstance(record[key], dict):
            raise ValidationError(f"{path}: method episode {record['id']} missing or non-dict component {key}")

    # S0: initial problem
    s0 = record["s0_initial_problem"]
    if not s0.get("problem_statement") or not s0.get("state_space"):
        raise ValidationError(f"{path}: method episode {record['id']} s0 missing problem_statement or state_space")
    for eq_id in s0.get("visible_equations", []):
        eq = nodes.get(eq_id)
        if not eq or eq.get("type") != "EQUATION":
            raise ValidationError(f"{path}: method episode {record['id']} s0 references invalid equation {eq_id}")

    # Q: deficiency of direct approach
    q = record["q_deficiency"]
    if not q.get("why_direct_solution_fails"):
        raise ValidationError(f"{path}: method episode {record['id']} q missing why_direct_solution_fails")

    # A: admissibility class and assumptions
    a = record["a_admissibility"]
    if not a.get("permissible_domain") or not a.get("admissibility_class"):
        raise ValidationError(f"{path}: method episode {record['id']} a missing permissible_domain or admissibility_class")
    for assump_id in a.get("assumption_ids", []):
        assump = nodes.get(assump_id)
        if not assump or assump.get("type") != "ASSUMPTION":
            raise ValidationError(f"{path}: method episode {record['id']} a references invalid assumption {assump_id}")

    # X: auxiliary construction
    x = record["x_auxiliary_construction"]
    if not x.get("auxiliary_object_name") or not x.get("auxiliary_representation_space") or not x.get("space_change"):
        raise ValidationError(f"{path}: method episode {record['id']} x missing auxiliary_object_name, auxiliary_representation_space, or space_change")

    # C: constraints and invariants
    c = record["c_constraints_invariants"]
    if not c.get("invariants") or not c.get("admissibility_bounds"):
        raise ValidationError(f"{path}: method episode {record['id']} c missing invariants or admissibility_bounds")
    for inv_id in c.get("invariant_ids", []):
        inv = nodes.get(inv_id)
        if not inv or inv.get("type") != "INVARIANT":
            raise ValidationError(f"{path}: method episode {record['id']} c references invalid invariant {inv_id}")

    # T: transformation decision on auxiliary
    t = record["t_transformation_decision"]
    if not t.get("decision_description") or not t.get("computation_on_auxiliary"):
        raise ValidationError(f"{path}: method episode {record['id']} t missing decision_description or computation_on_auxiliary")
    for op_id in t.get("operator_ids", []):
        op = nodes.get(op_id)
        if not op or op.get("type") != "OPERATOR":
            raise ValidationError(f"{path}: method episode {record['id']} t references invalid operator {op_id}")

    # S1: resulting conclusion and certified properties
    s1 = record["s1_resulting_conclusion"]
    if not s1.get("conclusion_statement") or not s1.get("certified_properties"):
        raise ValidationError(f"{path}: method episode {record['id']} s1 missing conclusion_statement or certified_properties")
    for eq_id in s1.get("resulting_equation_ids", []):
        eq = nodes.get(eq_id)
        if not eq or eq.get("type") != "EQUATION":
            raise ValidationError(f"{path}: method episode {record['id']} s1 references invalid equation {eq_id}")

    # Negative information ledger
    neg = record["negative_information"]
    if not neg.get("what_need_not_be_computed") or not isinstance(neg["what_need_not_be_computed"], list):
        raise ValidationError(f"{path}: method episode {record['id']} negative_information missing what_need_not_be_computed")
    if not neg.get("excluded_alternatives") or not isinstance(neg["excluded_alternatives"], list):
        raise ValidationError(f"{path}: method episode {record['id']} negative_information missing excluded_alternatives")

    # Sources and fragments
    for src_id in record.get("source_ids", []):
        src = nodes.get(src_id)
        if not src or src.get("type") not in {"PUBLICATION", "ARCHIVAL_DOCUMENT"}:
            raise ValidationError(f"{path}: method episode {record['id']} references invalid source {src_id}")
    for frag_id in record.get("source_fragment_ids", []):
        frag = nodes.get(frag_id)
        if not frag or frag.get("type") != "SOURCE_FRAGMENT":
            raise ValidationError(f"{path}: method episode {record['id']} references invalid fragment {frag_id}")


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


def validate_negative_information(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "NEGATIVE_INFORMATION":
        return
    for key in ("id", "type", "label", "negative_type", "description", "bypassed_by"):
        if not record.get(key):
            raise ValidationError(f"{path}: negative information {record['id']} missing {key}")


def validate_method_lens(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "METHOD_LENS":
        return
    for key in (
        "core_question",
        "constructed_object",
        "required_conditions",
        "revealed_properties",
        "avoided_operations",
        "method_primitives",
        "derived_from_episode_id",
    ):
        if not record.get(key):
            raise ValidationError(f"{path}: method lens {record['id']} missing {key}")
    ep = nodes.get(record["derived_from_episode_id"])
    if not ep or ep.get("type") != "METHOD_EPISODE":
        raise ValidationError(
            f"{path}: method lens {record['id']} references invalid episode {record.get('derived_from_episode_id')}"
        )
    for neg_id in record.get("enables_omission_of_ids", []):
        neg = nodes.get(neg_id)
        if not neg or neg.get("type") != "NEGATIVE_INFORMATION":
            raise ValidationError(
                f"{path}: method lens {record['id']} references invalid negative information {neg_id}"
            )


def validate_problem(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "PROBLEM":
        return
    for key in (
        "domain",
        "state_representation",
        "known_quantities",
        "unknown_quantities",
        "objective",
        "computational_bottleneck",
    ):
        if not record.get(key):
            raise ValidationError(f"{path}: problem {record['id']} missing {key}")
    banned_keywords = ("soviet", "russian", "leningrad", "moscow", "steklov", "ussr", "western")
    serialized = json.dumps(record).lower()
    for kw in banned_keywords:
        if kw in serialized:
            raise ValidationError(
                f"{path}: problem {record['id']} contains cultural/provenance keyword '{kw}', violating neutrality"
            )


def validate_perspective_projection(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "PERSPECTIVE_PROJECTION":
        return
    for key in (
        "problem_id",
        "method_lens_id",
        "input_state",
        "constructed_objects",
        "discarded_state",
        "new_invariants",
        "new_constraints",
        "predicted_computational_gain",
        "resulting_insight_ids",
    ):
        if not record.get(key):
            raise ValidationError(f"{path}: perspective projection {record['id']} missing {key}")
    prob = nodes.get(record["problem_id"])
    if not prob or prob.get("type") != "PROBLEM":
        raise ValidationError(f"{path}: projection {record['id']} references invalid problem {record['problem_id']}")
    lens = nodes.get(record["method_lens_id"])
    if not lens or lens.get("type") != "METHOD_LENS":
        raise ValidationError(f"{path}: projection {record['id']} references invalid method lens {record['method_lens_id']}")
    for ins_id in record.get("resulting_insight_ids", []):
        ins = nodes.get(ins_id)
        if not ins or ins.get("type") != "INSIGHT":
            raise ValidationError(f"{path}: projection {record['id']} references invalid insight {ins_id}")


def validate_insight(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "INSIGHT":
        return
    for key in ("insight_type", "generated_by_projection_id", "target_problem_id", "description", "epistemic_impact"):
        if not record.get(key):
            raise ValidationError(f"{path}: insight {record['id']} missing {key}")
    allowed_types = {
        "NEW_INVARIANT",
        "ELIMINATED_STATE",
        "NEW_ADMISSIBILITY_BOUNDARY",
        "LOWER_COST_ROUTE",
        "NEW_AUXILIARY_VARIABLE",
    }
    if record["insight_type"] not in allowed_types:
        raise ValidationError(f"{path}: insight {record['id']} has invalid insight_type {record['insight_type']}")
    proj = nodes.get(record["generated_by_projection_id"])
    if not proj or proj.get("type") != "PERSPECTIVE_PROJECTION":
        raise ValidationError(f"{path}: insight {record['id']} references invalid projection {record['generated_by_projection_id']}")
    prob = nodes.get(record["target_problem_id"])
    if not prob or prob.get("type") != "PROBLEM":
        raise ValidationError(f"{path}: insight {record['id']} references invalid problem {record['target_problem_id']}")


def validate_method_primitive(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "METHOD_PRIMITIVE":
        return
    for key in (
        "symbol",
        "input_state_type",
        "output_state_type",
        "preconditions",
        "preserved_invariants",
        "introduced_structures",
        "omitted_information",
        "complexity_weight",
        "verification_status",
    ):
        if key not in record or record.get(key) in ("", None):
            raise ValidationError(f"{path}: method primitive {record['id']} missing {key}")


def validate_primitive_composition(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "PRIMITIVE_COMPOSITION":
        return
    for key in (
        "first_primitive_id",
        "second_primitive_id",
        "composition_status",
        "commutation_type",
        "verification_status",
    ):
        if not record.get(key):
            raise ValidationError(f"{path}: primitive composition {record['id']} missing {key}")
    p1 = nodes.get(record["first_primitive_id"])
    if not p1 or p1.get("type") != "METHOD_PRIMITIVE":
        raise ValidationError(f"{path}: primitive composition {record['id']} references invalid first primitive {record['first_primitive_id']}")
    p2 = nodes.get(record["second_primitive_id"])
    if not p2 or p2.get("type") != "METHOD_PRIMITIVE":
        raise ValidationError(f"{path}: primitive composition {record['id']} references invalid second primitive {record['second_primitive_id']}")
    allowed_statuses = {"COMPOSE", "NORMALIZE", "ABSORB", "IDEMPOTENT", "ORDER_SENSITIVE", "CONFLICT", "UNDEFINED"}
    if record["composition_status"] not in allowed_statuses:
        raise ValidationError(f"{path}: primitive composition {record['id']} invalid status {record['composition_status']}")
    allowed_comm = {"COMMUTES", "ORDER_SENSITIVE", "ONE_DIRECTION_ONLY", "INCOMPATIBLE"}
    if record["commutation_type"] not in allowed_comm:
        raise ValidationError(f"{path}: primitive composition {record['id']} invalid commutation {record['commutation_type']}")


def validate_lens_normal_form(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "LENS_NORMAL_FORM_RULE":
        return
    for key in ("pattern", "replacement", "rationale", "verification_status"):
        if not record.get(key):
            raise ValidationError(f"{path}: lens normal form rule {record['id']} missing {key}")


def validate_synthetic_lens(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "SYNTHETIC_LENS":
        return
    for key in (
        "core_question",
        "constructed_object",
        "primitive_sequence",
        "normalized_sequence",
        "historical_origin",
        "status",
        "derivation_provenance",
        "verification_status",
    ):
        if not record.get(key):
            raise ValidationError(f"{path}: synthetic lens {record['id']} missing {key}")
    if record["historical_origin"] != "NONE":
        raise ValidationError(f"{path}: synthetic lens {record['id']} must have historical_origin: NONE (got {record['historical_origin']})")
    allowed_statuses = {"PROPOSED_SYNTHETIC_LENS", "QUALIFIED_SYNTHETIC_LENS"}
    if record["status"] not in allowed_statuses:
        raise ValidationError(f"{path}: synthetic lens {record['id']} has invalid status {record['status']}")
    for prim_id in record["primitive_sequence"]:
        prim = nodes.get(prim_id)
        if not prim or prim.get("type") != "METHOD_PRIMITIVE":
            raise ValidationError(f"{path}: synthetic lens {record['id']} references invalid primitive {prim_id}")
    banned_keywords = ("soviet", "russian", "leningrad", "moscow", "steklov", "ussr", "western")
    serialized = json.dumps(record).lower()
    for kw in banned_keywords:
        if kw in serialized:
            raise ValidationError(
                f"{path}: synthetic lens {record['id']} contains cultural keyword '{kw}', violating neutrality"
            )


def validate_edge(path: Path, record: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> None:
    if record["type"] != "EDGE":
        return
    edge_type = record.get("edge_type")
    if not edge_type:
        raise ValidationError(f"{path}: edge {record['id']} missing edge_type")
    if edge_type in FORBIDDEN_EDGE_TYPES:
        raise ValidationError(f"{path}: forbidden strong semantic edge {edge_type}: {record['id']}")
    
    relation_realm = record.get("relation_realm")
    if not relation_realm:
        raise ValidationError(f"{path}: edge {record['id']} missing required relation_realm")
    if relation_realm not in ALLOWED_REALMS:
        raise ValidationError(f"{path}: edge {record['id']} has invalid relation_realm '{relation_realm}'")
    if edge_type in HISTORICAL_EDGE_TYPES and relation_realm != "HISTORICAL":
        raise ValidationError(f"{path}: edge {record['id']} of type {edge_type} must have relation_realm HISTORICAL")
    if edge_type in MATHEMATICAL_EDGE_TYPES and relation_realm != "MATHEMATICAL":
        raise ValidationError(f"{path}: edge {record['id']} of type {edge_type} must have relation_realm MATHEMATICAL")
    if edge_type in METHODOLOGICAL_PERSPECTIVE_EDGE_TYPES and relation_realm != "METHODOLOGICAL_PERSPECTIVE":
        raise ValidationError(f"{path}: edge {record['id']} of type {edge_type} must have relation_realm METHODOLOGICAL_PERSPECTIVE")
    if edge_type in EXPERIMENTAL_APPLICATION_EDGE_TYPES and relation_realm != "EXPERIMENTAL_APPLICATION":
        raise ValidationError(f"{path}: edge {record['id']} of type {edge_type} must have relation_realm EXPERIMENTAL_APPLICATION")

    source_id = record.get("source")
    target_id = record.get("target")
    if not source_id or not target_id:
        raise ValidationError(f"{path}: edge {record['id']} missing source/target")
    s = nodes.get(source_id)
    t = nodes.get(target_id)
    if not s or not t:
        raise ValidationError(f"{path}: edge {record['id']} references unknown node(s)")

    if edge_type in TRANSFORMATION_EDGE_TYPES:
        if s.get("type") != "EQUATION" or t.get("type") != "EQUATION":
            raise ValidationError(
                f"{path}: transformation edge {edge_type} on {record['id']} must connect EQUATION -> EQUATION (got {s.get('type')} -> {t.get('type')})"
            )

    # Enforce strict non-implication boundary between realms
    if relation_realm == "MATHEMATICAL":
        if s.get("type") in {"PERSON", "PUBLICATION", "ARCHIVAL_DOCUMENT", "CLAIM"}:
            raise ValidationError(
                f"{path}: MATHEMATICAL realm edge {record['id']} cannot originate from historical entity {s.get('type')}"
            )
        if t.get("type") in {"PERSON", "PUBLICATION", "ARCHIVAL_DOCUMENT"}:
            raise ValidationError(
                f"{path}: MATHEMATICAL realm edge {record['id']} cannot target historical entity {t.get('type')}"
            )
    elif relation_realm == "METHODOLOGICAL_PERSPECTIVE":
        if s.get("type") in {"PERSON", "PUBLICATION", "ARCHIVAL_DOCUMENT", "CLAIM"}:
            raise ValidationError(
                f"{path}: METHODOLOGICAL_PERSPECTIVE realm edge {record['id']} cannot originate from historical entity {s.get('type')}"
            )
        if t.get("type") in {"PERSON", "PUBLICATION", "ARCHIVAL_DOCUMENT"}:
            raise ValidationError(
                f"{path}: METHODOLOGICAL_PERSPECTIVE realm edge {record['id']} cannot target historical entity {t.get('type')}"
            )
    elif relation_realm == "EXPERIMENTAL_APPLICATION":
        if s.get("type") in {"PERSON", "PUBLICATION", "ARCHIVAL_DOCUMENT", "CLAIM", "METHOD_EPISODE"}:
            raise ValidationError(
                f"{path}: EXPERIMENTAL_APPLICATION realm edge {record['id']} cannot originate from {s.get('type')}"
            )
        if t.get("type") in {"PERSON", "PUBLICATION", "ARCHIVAL_DOCUMENT", "CLAIM", "METHOD_EPISODE"}:
            raise ValidationError(
                f"{path}: EXPERIMENTAL_APPLICATION realm edge {record['id']} cannot target {t.get('type')}"
            )

    namespaces = {s["namespace"], t["namespace"]}
    if "WEST" in namespaces and namespaces & SOURCE_NATIVE_NAMESPACES and edge_type not in COMPARISON_EDGES:
        raise ValidationError(f"{path}: WEST/SOV-RUS edge must be comparison-only: {record['id']}")

    if edge_type == "AVOIDS_COMPUTING":
        if s.get("type") != "METHOD_EPISODE" or t.get("type") != "NEGATIVE_INFORMATION":
            raise ValidationError(f"{path}: AVOIDS_COMPUTING must connect METHOD_EPISODE -> NEGATIVE_INFORMATION: {record['id']}")

    if edge_type == "DERIVED_FROM_METHOD_EPISODE":
        if s.get("type") != "METHOD_LENS" or t.get("type") != "METHOD_EPISODE":
            raise ValidationError(f"{path}: DERIVED_FROM_METHOD_EPISODE must connect METHOD_LENS -> METHOD_EPISODE: {record['id']}")

    if edge_type == "ENABLES_OMISSION_OF":
        if s.get("type") != "METHOD_LENS" or t.get("type") != "NEGATIVE_INFORMATION":
            raise ValidationError(f"{path}: ENABLES_OMISSION_OF must connect METHOD_LENS -> NEGATIVE_INFORMATION: {record['id']}")

    if edge_type == "APPLIES_TO_PROBLEM":
        if s.get("type") != "PERSPECTIVE_PROJECTION" or t.get("type") != "PROBLEM":
            raise ValidationError(f"{path}: APPLIES_TO_PROBLEM must connect PERSPECTIVE_PROJECTION -> PROBLEM: {record['id']}")

    if edge_type == "REVEALS":
        if s.get("type") != "PERSPECTIVE_PROJECTION" or t.get("type") != "INSIGHT":
            raise ValidationError(f"{path}: REVEALS must connect PERSPECTIVE_PROJECTION -> INSIGHT: {record['id']}")

    if edge_type == "COMPLEMENTS":
        if s.get("type") != "INSIGHT" or t.get("type") != "INSIGHT":
            raise ValidationError(f"{path}: COMPLEMENTS must connect INSIGHT -> INSIGHT: {record['id']}")

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

    if edge_type == "REPRODUCES":
        if s.get("type") not in {"PUBLICATION", "ARCHIVAL_DOCUMENT"} or t.get("type") not in {"PUBLICATION", "ARCHIVAL_DOCUMENT"}:
            raise ValidationError(f"{path}: REPRODUCES must connect source record -> source record: {record['id']}")

    if edge_type == "EDITION_OF":
        if s.get("type") not in {"PUBLICATION", "ARCHIVAL_DOCUMENT"} or t.get("type") not in {"PUBLICATION", "ARCHIVAL_DOCUMENT"}:
            raise ValidationError(f"{path}: EDITION_OF must connect source record -> source record: {record['id']}")

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
        validate_method_episode(path, record, nodes)
        validate_negative_information(path, record, nodes)
        validate_method_lens(path, record, nodes)
        validate_problem(path, record, nodes)
        validate_perspective_projection(path, record, nodes)
        validate_insight(path, record, nodes)
        validate_method_primitive(path, record, nodes)
        validate_primitive_composition(path, record, nodes)
        validate_lens_normal_form(path, record, nodes)
        validate_synthetic_lens(path, record, nodes)

    support_pairs: set[tuple[str, str]] = set()
    encoded_equation_pairs: set[tuple[str, str]] = set()
    for path, record in records:
        validate_edge(path, record, nodes)
        validate_temporal_edge(path, record, nodes)
        if record.get("type") == "EDGE" and record.get("edge_type") == "SUPPORTS":
            support_pairs.add((record["source"], record["target"]))
        if record.get("type") == "EDGE" and record.get("edge_type") == "ENCODES_EQUATION":
            encoded_equation_pairs.add((record["source"], record["target"]))

    for record in nodes.values():
        if record.get("type") != "CLAIM":
            continue
        for fragment_id in record.get("source_fragment_ids", []):
            if (fragment_id, record["id"]) not in support_pairs:
                raise ValidationError(
                    f"claim {record['id']} lists fragment {fragment_id} but lacks SUPPORTS edge"
                )

    for record in nodes.values():
        if record.get("type") != "EQUATION":
            continue
        for fragment_id in record.get("source_fragment_ids", []):
            if (fragment_id, record["id"]) not in encoded_equation_pairs:
                raise ValidationError(
                    f"equation {record['id']} lists fragment {fragment_id} but lacks ENCODES_EQUATION edge"
                )

    print(f"SOVCTX validation PASS: {len(records)} records, {len(nodes)} nodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
