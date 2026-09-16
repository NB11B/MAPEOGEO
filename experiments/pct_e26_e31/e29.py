from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
from itertools import combinations
import json
from pathlib import Path
from typing import Any, Iterable

from .cases import HeldoutCase, build_r1_cases, sanitize_case
from .constants import SEMANTIC_RELATION_TYPES
from .corpus import KnowledgeCorpus
from .e27 import build_r2_cluster_cases, build_r3_domain_cases
from .identity import compute_harness_sha
from .probes import B4_PROBE_KEYS, build_graph_index, pair_probe_values


@dataclass(frozen=True)
class TrainingRow:
    edge_id: str
    canonical_id: str
    relation: str
    probes: tuple[tuple[str, Any], ...]
    scope: tuple[tuple[str, Any], ...] = ()


@dataclass(frozen=True)
class CandidateRule:
    rule_id: str
    antecedents: tuple[tuple[str, Any], ...]
    consequent: str
    support_edge_count: int
    support_canonical_count: int
    support_edge_ids: tuple[str, ...]
    support_canonical_ids: tuple[str, ...]


@dataclass(frozen=True)
class RuleAudit:
    rule_id: str
    status: str
    theorem_status: bool
    counterexample_edge_ids: tuple[str, ...]
    matched_edge_count: int
    rescued_scopes: tuple[tuple[str, Any, int, int], ...] = ()


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, (list, set, frozenset)):
        return [_jsonable(v) for v in sorted(value, key=repr)]
    return value


def _digest(payload: Any) -> str:
    raw = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _matches(antecedents: tuple[tuple[str, Any], ...], row: TrainingRow) -> bool:
    probes = dict(row.probes)
    return all(key in probes and probes[key] == value for key, value in antecedents)


def enumerate_candidate_rules(
    training_cases: list[TrainingRow],
    max_width: int = 3,
    min_support_edges: int = 3,
    min_canonical_objects: int = 2,
    probe_keys: Iterable[str] | None = None,
) -> list[CandidateRule]:
    if max_width < 1:
        return []
    if min_support_edges < 1 or min_canonical_objects < 1:
        raise ValueError("Support thresholds must be positive")

    allowed = tuple(probe_keys) if probe_keys is not None else tuple(
        sorted({key for row in training_cases for key, _ in row.probes})
    )
    allowed_set = set(allowed)

    support_edges: dict[tuple[str, tuple[tuple[str, Any], ...]], set[str]] = defaultdict(set)
    support_canonicals: dict[tuple[str, tuple[tuple[str, Any], ...]], set[str]] = defaultdict(set)

    for row in training_cases:
        probe_map = dict(row.probes)
        keys = tuple(key for key in allowed if key in probe_map and key in allowed_set)
        width_limit = min(max_width, len(keys))
        for width in range(1, width_limit + 1):
            for key_subset in combinations(keys, width):
                antecedents = tuple((key, probe_map[key]) for key in key_subset)
                token = (row.relation, antecedents)
                support_edges[token].add(row.edge_id)
                support_canonicals[token].add(row.canonical_id)

    rules: list[CandidateRule] = []
    for (relation, antecedents), edge_ids in support_edges.items():
        canonical_ids = support_canonicals[(relation, antecedents)]
        if len(edge_ids) < min_support_edges or len(canonical_ids) < min_canonical_objects:
            continue
        rule_id = "rule:" + _digest(
            {
                "antecedents": antecedents,
                "consequent": relation,
                "max_width": max_width,
                "min_support_edges": min_support_edges,
                "min_canonical_objects": min_canonical_objects,
            }
        )
        rules.append(
            CandidateRule(
                rule_id=rule_id,
                antecedents=antecedents,
                consequent=relation,
                support_edge_count=len(edge_ids),
                support_canonical_count=len(canonical_ids),
                support_edge_ids=tuple(sorted(edge_ids)),
                support_canonical_ids=tuple(sorted(canonical_ids)),
            )
        )

    rules.sort(key=lambda rule: (len(rule.antecedents), rule.consequent, rule.rule_id))
    return rules


def _rescued_scopes(rule: CandidateRule, matched: list[TrainingRow]) -> tuple[tuple[str, Any, int, int], ...]:
    by_scope: dict[tuple[str, Any], list[TrainingRow]] = defaultdict(list)
    for row in matched:
        for key, value in row.scope:
            by_scope[(key, value)].append(row)

    rescued: list[tuple[str, Any, int, int]] = []
    for (key, value), rows in by_scope.items():
        if any(row.relation != rule.consequent for row in rows):
            continue
        edge_ids = {row.edge_id for row in rows}
        canonical_ids = {row.canonical_id for row in rows}
        if len(edge_ids) >= 3 and len(canonical_ids) >= 2:
            rescued.append((key, value, len(edge_ids), len(canonical_ids)))
    rescued.sort(key=lambda item: (item[0], repr(item[1]), item[2], item[3]))
    return tuple(rescued)


def falsify_rule(rule: CandidateRule, visible_cases: list[TrainingRow]) -> RuleAudit:
    matched = [row for row in visible_cases if _matches(rule.antecedents, row)]
    counterexamples = tuple(
        sorted(row.edge_id for row in matched if row.relation != rule.consequent)
    )
    if counterexamples:
        return RuleAudit(
            rule_id=rule.rule_id,
            status="DEFEATED_BY_COUNTEREXAMPLE",
            theorem_status=False,
            counterexample_edge_ids=counterexamples,
            matched_edge_count=len(matched),
            rescued_scopes=_rescued_scopes(rule, matched),
        )
    return RuleAudit(
        rule_id=rule.rule_id,
        status="CANDIDATE_SURVIVED_VISIBLE_SEARCH",
        theorem_status=False,
        counterexample_edge_ids=(),
        matched_edge_count=len(matched),
        rescued_scopes=(),
    )


def _edge_map(corpus: KnowledgeCorpus) -> dict[str, dict[str, Any]]:
    return {
        str(edge["id"]): edge
        for edge in corpus.graph.get("edges", [])
        if "id" in edge
    }


def _canonical_id(edge: dict[str, Any], fallback: str = "UNKNOWN") -> str:
    attrs = edge.get("attributes", {})
    value = attrs.get("canonical_object") or attrs.get("canonical_id")
    return str(value) if value else fallback


def _source_pair(corpus: KnowledgeCorpus, source_id: str, target_id: str) -> tuple[str, str]:
    values: list[str] = []
    for node_id in (source_id, target_id):
        node = corpus.node_by_id.get(node_id, {})
        values.append(str(node.get("attributes", {}).get("source_id", "UNKNOWN")))
    return tuple(sorted(values))


def _domain(corpus: KnowledgeCorpus, canonical_id: str) -> str:
    return str(
        corpus.node_by_id.get(canonical_id, {})
        .get("attributes", {})
        .get("domain", "UNKNOWN")
    )


def _solver_visible_training_graph(corpus: KnowledgeCorpus) -> dict[str, Any]:
    # E27 established that cross_source_status on REPRESENTS edges is a redundant
    # answer label. Remove it globally before E29 derives any antecedent values.
    nodes = list(corpus.graph.get("nodes", []))
    edges: list[dict[str, Any]] = []
    for original in corpus.graph.get("edges", []):
        edge = dict(original)
        if edge.get("type") == "REPRESENTS":
            attrs = dict(edge.get("attributes", {}))
            attrs.pop("cross_source_status", None)
            edge["attributes"] = attrs
        edges.append(edge)
    graph = {key: value for key, value in corpus.graph.items() if key not in {"nodes", "edges"}}
    graph["nodes"] = nodes
    graph["edges"] = edges
    return graph


def _training_rows_from_graph(
    corpus: KnowledgeCorpus,
    graph: dict[str, Any],
    excluded_edge_ids: Iterable[str] = (),
) -> list[TrainingRow]:
    edge_map = _edge_map(corpus)
    excluded = frozenset(str(edge_id) for edge_id in excluded_edge_ids)
    index = build_graph_index(graph)
    rows: list[TrainingRow] = []
    for case in build_r1_cases(corpus):
        if case.edge_id in excluded:
            continue
        edge = edge_map[case.edge_id]
        canonical = _canonical_id(edge, dict(case.verifier_metadata).get("canonical_hint", "UNKNOWN"))
        probes = pair_probe_values(graph, case.source_id, case.target_id, index=index)
        rows.append(
            TrainingRow(
                edge_id=case.edge_id,
                canonical_id=canonical,
                relation=case.sealed_relation,
                probes=tuple((key, probes[key]) for key in B4_PROBE_KEYS if key in probes),
                scope=(
                    ("domain", _domain(corpus, canonical)),
                    ("source_pair", _source_pair(corpus, case.source_id, case.target_id)),
                ),
            )
        )
    rows.sort(key=lambda row: row.edge_id)
    return rows


def _training_rows(corpus: KnowledgeCorpus) -> list[TrainingRow]:
    return _training_rows_from_graph(corpus, _solver_visible_training_graph(corpus))


def build_visible_training_rows(
    corpus: KnowledgeCorpus,
    heldout: HeldoutCase,
) -> list[TrainingRow]:
    """Build E29 training rows from exactly the graph visible for one sealed holdout."""
    sanitized = sanitize_case(corpus, heldout)
    rows = _training_rows_from_graph(
        corpus,
        sanitized.visible_graph,
        excluded_edge_ids=heldout.hidden_edge_ids,
    )
    hidden = set(heldout.hidden_edge_ids)
    if any(row.edge_id in hidden for row in rows):
        raise ValueError("E29 visible training contains a sealed hidden edge")
    return rows


def _serialize_rule(rule: CandidateRule) -> dict[str, Any]:
    return {
        "rule_id": rule.rule_id,
        "antecedents": [[key, _jsonable(value)] for key, value in rule.antecedents],
        "consequent": rule.consequent,
        "support_edge_count": rule.support_edge_count,
        "support_canonical_count": rule.support_canonical_count,
        "support_edge_ids": list(rule.support_edge_ids),
        "support_canonical_ids": list(rule.support_canonical_ids),
        "theorem_status": False,
    }


def _serialize_audit(audit: RuleAudit) -> dict[str, Any]:
    return {
        "rule_id": audit.rule_id,
        "status": audit.status,
        "theorem_status": audit.theorem_status,
        "counterexample_edge_ids": list(audit.counterexample_edge_ids),
        "matched_edge_count": audit.matched_edge_count,
        "rescued_scopes": [
            {
                "scope_key": key,
                "scope_value": _jsonable(value),
                "support_edge_count": edge_count,
                "support_canonical_count": canonical_count,
            }
            for key, value, edge_count, canonical_count in audit.rescued_scopes
        ],
    }


def _heldout_case_map(cases: Iterable[HeldoutCase]) -> dict[str, HeldoutCase]:
    return {case.case_id: case for case in cases}


def _rule_matches_probes(rule: CandidateRule, probes: dict[str, Any]) -> bool:
    return all(key in probes and probes[key] == value for key, value in rule.antecedents)


def _discover_visible_survivors(
    training: list[TrainingRow],
) -> tuple[list[CandidateRule], list[RuleAudit], list[CandidateRule]]:
    rules = enumerate_candidate_rules(
        training,
        max_width=3,
        min_support_edges=3,
        min_canonical_objects=2,
        probe_keys=B4_PROBE_KEYS,
    )
    audits = [falsify_rule(rule, training) for rule in rules]
    audit_by_id = {audit.rule_id: audit for audit in audits}
    survivors = [
        rule
        for rule in rules
        if audit_by_id[rule.rule_id].status == "CANDIDATE_SURVIVED_VISIBLE_SEARCH"
    ]
    return rules, audits, survivors


def _transfer_tier(
    corpus: KnowledgeCorpus,
    tier_report: dict[str, Any],
    cases: dict[str, HeldoutCase],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    correct = wrong = ambiguous = refused = 0
    block_cache: dict[
        tuple[str, ...],
        tuple[list[TrainingRow], list[CandidateRule], list[RuleAudit], list[CandidateRule], str],
    ] = {}

    for sealed in sorted(tier_report.get("cases", []), key=lambda row: row["case_id"]):
        heldout = cases[sealed["case_id"]]
        block_key = tuple(heldout.hidden_edge_ids)
        if block_key not in block_cache:
            training = build_visible_training_rows(corpus, heldout)
            rules, audits, survivors = _discover_visible_survivors(training)
            candidate_sha = _digest([_serialize_rule(rule) for rule in rules])
            block_cache[block_key] = (training, rules, audits, survivors, candidate_sha)
        training, rules, _audits, survivors, candidate_sha = block_cache[block_key]

        training_ids = {row.edge_id for row in training}
        hidden_overlap_count = len(training_ids.intersection(heldout.hidden_edge_ids))
        if hidden_overlap_count:
            raise ValueError("E29 sealed transfer training overlaps hidden answer edges")

        sanitized = sanitize_case(corpus, heldout)
        probes = pair_probe_values(sanitized.visible_graph, heldout.source_id, heldout.target_id)
        matched = [rule for rule in survivors if _rule_matches_probes(rule, probes)]
        predictions = tuple(sorted({rule.consequent for rule in matched}))
        if len(predictions) == 1:
            verdict = "PASS"
            prediction = predictions[0]
            if prediction == heldout.sealed_relation:
                outcome = "correct"
                correct += 1
            else:
                outcome = "wrong"
                wrong += 1
        elif len(predictions) > 1:
            verdict = "NOT_ESTABLISHED"
            prediction = None
            outcome = "ambiguous"
            ambiguous += 1
        else:
            verdict = "NOT_ESTABLISHED"
            prediction = None
            outcome = "refused"
            refused += 1
        rows.append(
            {
                "case_id": heldout.case_id,
                "sealed_relation": heldout.sealed_relation,
                "verdict": verdict,
                "prediction": prediction,
                "outcome": outcome,
                "matched_rule_ids": [rule.rule_id for rule in matched],
                "candidate_relations": list(predictions),
                "training_edge_count": len(training),
                "training_hidden_overlap_count": hidden_overlap_count,
                "candidate_rules_generated": len(rules),
                "rules_survived_visible_search": len(survivors),
                "frozen_candidate_set_sha256": candidate_sha,
            }
        )
    return {
        "total": len(rows),
        "block_count": len(block_cache),
        "correct": correct,
        "wrong": wrong,
        "ambiguous": ambiguous,
        "refused": refused,
        "selective_accuracy": correct / (correct + wrong) if (correct + wrong) else None,
        "cases": rows,
    }


def run_e29(corpus: KnowledgeCorpus, e27_report: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    training = _training_rows(corpus)
    rules, audits, survivors = _discover_visible_survivors(training)

    # Freeze the visible-corpus discovery output. Sealed transfer below independently
    # freezes a candidate set from each holdout block's visible complement.
    frozen_rule_payload = [_serialize_rule(rule) for rule in rules]
    frozen_rule_sha256 = _digest(frozen_rule_payload)

    r2_cases = _heldout_case_map(build_r2_cluster_cases(corpus))
    r3_cases = _heldout_case_map(build_r3_domain_cases(corpus))
    transfer = {
        "R2": _transfer_tier(corpus, e27_report["R2"], r2_cases),
        "R3": _transfer_tier(corpus, e27_report["R3"], r3_cases),
    }

    relation_support: dict[str, dict[str, int | str]] = {}
    for relation in SEMANTIC_RELATION_TYPES:
        relation_rows = [row for row in training if row.relation == relation]
        canonicals = {row.canonical_id for row in relation_rows}
        relation_support[relation] = {
            "edge_count": len(relation_rows),
            "canonical_count": len(canonicals),
            "discovery_applicability": (
                "APPLICABLE"
                if len(relation_rows) >= 3 and len(canonicals) >= 2
                else "NOT_APPLICABLE"
            ),
        }

    surviving_serialized = []
    for rule in survivors:
        row = _serialize_rule(rule)
        row["visible_search_status"] = "CANDIDATE_SURVIVED_VISIBLE_SEARCH"
        row["theorem_status"] = False
        surviving_serialized.append(row)

    defeated = [audit for audit in audits if audit.status == "DEFEATED_BY_COUNTEREXAMPLE"]
    transfer_overlap_count = sum(
        row["training_hidden_overlap_count"]
        for tier in ("R2", "R3")
        for row in transfer[tier]["cases"]
    )
    report = {
        "experiment_id": "E29_STRUCTURAL_RULE_DISCOVERY_FALSIFICATION",
        "status": "PASS" if transfer_overlap_count == 0 else "FAIL",
        "campaign_harness_sha": compute_harness_sha(repo_root),
        "e27_solver_recipe_sha256": e27_report.get("solver_recipe_sha256"),
        "rule_language": {
            "max_conjunction_width": 3,
            "min_support_edges": 3,
            "min_support_canonical_objects": 2,
            "probe_keys": list(B4_PROBE_KEYS),
        },
        "training_edge_count": len(training),
        "relation_support": relation_support,
        "candidate_rules_generated": len(rules),
        "frozen_candidate_set_sha256": frozen_rule_sha256,
        "rules_defeated_by_counterexample": len(defeated),
        "counterexamples_found": sum(len(audit.counterexample_edge_ids) for audit in defeated),
        "rules_with_scope_rescues": sum(bool(audit.rescued_scopes) for audit in defeated),
        "rules_survived_visible_search": len(survivors),
        "surviving_rules": surviving_serialized,
        "rule_audits": [_serialize_audit(audit) for audit in audits],
        "sealed_transfer_protocol": "PER_HOLDOUT_VISIBLE_TRAINING_ONLY",
        "sealed_transfer_hidden_overlap_count": transfer_overlap_count,
        "sealed_transfer": transfer,
        "claim_boundary": "SURVIVING_RULES_ARE_BOUNDED_CANDIDATES_NOT_THEOREMS; SEALED_TRANSFER_TRAINS_ONLY_ON_EACH_HOLDOUT_VISIBLE_COMPLEMENT",
    }
    return report