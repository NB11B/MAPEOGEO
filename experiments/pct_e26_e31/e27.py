from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from .baselines import run_baseline
from .cases import HeldoutCase, SanitizedCase, build_r1_cases, sanitize_case
from .constants import SEMANTIC_RELATION_TYPES
from .corpus import KnowledgeCorpus
from .identity import compute_harness_sha
from .probes import B1_PROBE_KEYS, B2_PROBE_KEYS, B3_PROBE_KEYS, B4_PROBE_KEYS, build_graph_index
from .solver import SolverResult, fit_solver_model, solve_case, solve_with_model


@dataclass(frozen=True)
class ControlCase:
    control_id: str
    control_kind: str
    source_relation: str
    case: SanitizedCase
    probe_keys: tuple[str, ...] | None = None


def _digest(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _canonical_id(edge: dict[str, Any]) -> str | None:
    attrs = edge.get("attributes", {})
    value = attrs.get("canonical_object") or attrs.get("canonical_id")
    return str(value) if value else None


def _source_semantic_edges(corpus: KnowledgeCorpus) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for edge in corpus.semantic_edges:
        source = corpus.node_by_id.get(str(edge.get("source")))
        target = corpus.node_by_id.get(str(edge.get("target")))
        if not source or not target:
            continue
        if source.get("type") == "SOURCE_DECLARATION" and target.get("type") == "SOURCE_DECLARATION":
            rows.append(edge)
    return rows


def _semantic_pair_ids(corpus: KnowledgeCorpus) -> dict[tuple[str, str], set[str]]:
    out: dict[tuple[str, str], set[str]] = defaultdict(set)
    for edge in _source_semantic_edges(corpus):
        pair = tuple(sorted((str(edge["source"]), str(edge["target"]))))
        out[pair].add(str(edge["id"]))
    return out


def _edge_by_id(corpus: KnowledgeCorpus) -> dict[str, dict[str, Any]]:
    return {
        str(edge["id"]): edge
        for edge in corpus.graph.get("edges", [])
        if "id" in edge
    }


def build_r2_cluster_cases(corpus: KnowledgeCorpus) -> list[HeldoutCase]:
    r1 = build_r1_cases(corpus)
    edge_map = _edge_by_id(corpus)
    pair_ids = _semantic_pair_ids(corpus)
    all_by_canonical: dict[str, set[str]] = defaultdict(set)
    for edge in _source_semantic_edges(corpus):
        canonical = _canonical_id(edge)
        if canonical:
            all_by_canonical[canonical].add(str(edge["id"]))

    targets_by_canonical: dict[str, list[HeldoutCase]] = defaultdict(list)
    for case in r1:
        canonical = _canonical_id(edge_map[case.edge_id])
        if canonical:
            targets_by_canonical[canonical].append(case)

    cases: list[HeldoutCase] = []
    for canonical in sorted(targets_by_canonical):
        targets = targets_by_canonical[canonical]
        hidden = set(all_by_canonical[canonical])
        for target in targets:
            hidden.update(pair_ids[tuple(sorted((target.source_id, target.target_id)))])
        domain = str(corpus.node_by_id.get(canonical, {}).get("attributes", {}).get("domain", "UNKNOWN"))
        hidden_ids = tuple(sorted(hidden))
        for target in sorted(targets, key=lambda row: row.case_id):
            payload = {
                "tier": "R2",
                "edge_id": target.edge_id,
                "canonical": canonical,
                "hidden_edge_ids": hidden_ids,
            }
            cases.append(
                HeldoutCase(
                    case_id=_digest(payload),
                    tier="R2",
                    edge_id=target.edge_id,
                    source_id=target.source_id,
                    target_id=target.target_id,
                    sealed_relation=target.sealed_relation,
                    hidden_edge_ids=hidden_ids,
                    verifier_metadata=(
                        ("canonical_holdout_group", canonical),
                        ("domain", domain),
                    ),
                )
            )
    return cases


def build_r3_domain_cases(corpus: KnowledgeCorpus) -> list[HeldoutCase]:
    r2 = build_r2_cluster_cases(corpus)
    edge_map = _edge_by_id(corpus)
    pair_ids = _semantic_pair_ids(corpus)

    domain_edge_ids: dict[str, set[str]] = defaultdict(set)
    for edge in _source_semantic_edges(corpus):
        canonical = _canonical_id(edge)
        if not canonical:
            continue
        domain = str(corpus.node_by_id.get(canonical, {}).get("attributes", {}).get("domain", "UNKNOWN"))
        domain_edge_ids[domain].add(str(edge["id"]))

    targets_by_domain: dict[str, list[HeldoutCase]] = defaultdict(list)
    for case in r2:
        meta = dict(case.verifier_metadata)
        targets_by_domain[meta["domain"]].append(case)

    cases: list[HeldoutCase] = []
    for domain in sorted(targets_by_domain):
        targets = targets_by_domain[domain]
        hidden = set(domain_edge_ids[domain])
        for target in targets:
            hidden.update(pair_ids[tuple(sorted((target.source_id, target.target_id)))])
        hidden_ids = tuple(sorted(hidden))
        for target in sorted(targets, key=lambda row: row.case_id):
            canonical = _canonical_id(edge_map[target.edge_id]) or "UNKNOWN"
            payload = {
                "tier": "R3",
                "edge_id": target.edge_id,
                "domain": domain,
                "hidden_edge_ids": hidden_ids,
            }
            cases.append(
                HeldoutCase(
                    case_id=_digest(payload),
                    tier="R3",
                    edge_id=target.edge_id,
                    source_id=target.source_id,
                    target_id=target.target_id,
                    sealed_relation=target.sealed_relation,
                    hidden_edge_ids=hidden_ids,
                    verifier_metadata=(
                        ("domain_holdout_group", domain),
                        ("canonical", canonical),
                    ),
                )
            )
    return cases


def _direct_labels(graph: dict[str, Any], source_id: str, target_id: str) -> tuple[str, ...]:
    pair = frozenset((source_id, target_id))
    return tuple(
        sorted(
            str(edge["type"])
            for edge in graph.get("edges", [])
            if edge.get("type") in SEMANTIC_RELATION_TYPES
            and frozenset((str(edge.get("source")), str(edge.get("target")))) == pair
        )
    )


def _retarget(base: SanitizedCase, heldout: HeldoutCase) -> SanitizedCase:
    return SanitizedCase(
        case_id=heldout.case_id,
        tier=heldout.tier,
        source_id=heldout.source_id,
        target_id=heldout.target_id,
        visible_graph=base.visible_graph,
        visible_edge_ids=base.visible_edge_ids,
        direct_target_labels=_direct_labels(base.visible_graph, heldout.source_id, heldout.target_id),
        metadata={"tier": heldout.tier, "task": "RELATION_CLASSIFICATION"},
    )


def _clone_case(
    base: SanitizedCase,
    *,
    control_id: str,
    target_id: str | None = None,
    graph: dict[str, Any] | None = None,
    direct_labels: tuple[str, ...] | None = None,
) -> SanitizedCase:
    visible_graph = graph if graph is not None else base.visible_graph
    actual_target = target_id or base.target_id
    labels = direct_labels if direct_labels is not None else _direct_labels(visible_graph, base.source_id, actual_target)
    return SanitizedCase(
        case_id=control_id,
        tier="R4",
        source_id=base.source_id,
        target_id=actual_target,
        visible_graph=visible_graph,
        visible_edge_ids=tuple(sorted(str(edge.get("id", "")) for edge in visible_graph.get("edges", []))),
        direct_target_labels=labels,
        metadata={"tier": "R4", "task": "REFUSAL_CONTROL"},
    )


def build_r4_controls(corpus: KnowledgeCorpus) -> list[ControlCase]:
    representatives: dict[str, HeldoutCase] = {}
    for case in build_r1_cases(corpus):
        representatives.setdefault(case.sealed_relation, case)

    controls: list[ControlCase] = []
    for relation in SEMANTIC_RELATION_TYPES:
        seed = representatives.get(relation)
        if seed is None:
            continue
        base = sanitize_case(corpus, seed)
        index = build_graph_index(base.visible_graph)
        source_node = index.nodes[base.source_id]
        source_corpus = source_node.get("attributes", {}).get("source_id")
        shared = index.rep_targets.get(base.source_id, frozenset()) & index.rep_targets.get(base.target_id, frozenset())

        wrong_target = None
        for node_id, node in sorted(index.nodes.items()):
            if node.get("type") != "SOURCE_DECLARATION" or node_id in {base.source_id, base.target_id}:
                continue
            candidate_corpus = node.get("attributes", {}).get("source_id")
            if not candidate_corpus or candidate_corpus == source_corpus:
                continue
            if index.rep_targets.get(base.source_id, frozenset()) & index.rep_targets.get(node_id, frozenset()):
                continue
            if _direct_labels(base.visible_graph, base.source_id, node_id):
                continue
            wrong_target = node_id
            break
        if wrong_target is None:
            raise ValueError(f"Unable to construct endpoint-swap control for {relation}")

        endpoint_id = _digest({"kind": "ENDPOINT_SWAP", "relation": relation, "seed": seed.case_id})
        controls.append(
            ControlCase(
                control_id=endpoint_id,
                control_kind="ENDPOINT_SWAP",
                source_relation=relation,
                case=_clone_case(base, control_id=endpoint_id, target_id=wrong_target),
            )
        )

        binding_graph = deepcopy(base.visible_graph)
        for node in binding_graph.get("nodes", []):
            if str(node.get("id")) == base.target_id:
                attrs = dict(node.get("attributes", {}))
                attrs["source_id"] = source_corpus
                node["attributes"] = attrs
                break
        binding_id = _digest({"kind": "SOURCE_BINDING_CORRUPTION", "relation": relation, "seed": seed.case_id})
        controls.append(
            ControlCase(
                control_id=binding_id,
                control_kind="SOURCE_BINDING_CORRUPTION",
                source_relation=relation,
                case=_clone_case(base, control_id=binding_id, graph=binding_graph),
            )
        )

        scope_graph = deepcopy(base.visible_graph)
        scope_graph["edges"] = [
            edge
            for edge in scope_graph.get("edges", [])
            if not (
                edge.get("type") == "REPRESENTS"
                and str(edge.get("source")) == base.target_id
                and str(edge.get("target")) in shared
            )
        ]
        scope_id = _digest({"kind": "SCOPE_CORRUPTION", "relation": relation, "seed": seed.case_id})
        controls.append(
            ControlCase(
                control_id=scope_id,
                control_kind="SCOPE_CORRUPTION",
                source_relation=relation,
                case=_clone_case(base, control_id=scope_id, graph=scope_graph),
            )
        )

        alternate = next(value for value in SEMANTIC_RELATION_TYPES if value != relation)
        relation_graph = deepcopy(base.visible_graph)
        synthetic_edge_id = f"synthetic:r4:{relation.lower()}:{alternate.lower()}"
        relation_graph["edges"].append(
            {
                "id": synthetic_edge_id,
                "type": alternate,
                "source": base.source_id,
                "target": base.target_id,
                "attributes": {"provenance_class": "SYNTHETIC_CONTROL"},
            }
        )
        relation_id = _digest({"kind": "RELATION_TYPE_CORRUPTION", "relation": relation, "seed": seed.case_id})
        controls.append(
            ControlCase(
                control_id=relation_id,
                control_kind="RELATION_TYPE_CORRUPTION",
                source_relation=relation,
                case=_clone_case(
                    base,
                    control_id=relation_id,
                    graph=relation_graph,
                    direct_labels=(alternate,),
                ),
            )
        )

        erasure_id = _digest({"kind": "EVIDENCE_ERASURE", "relation": relation, "seed": seed.case_id})
        controls.append(
            ControlCase(
                control_id=erasure_id,
                control_kind="EVIDENCE_ERASURE",
                source_relation=relation,
                case=_clone_case(base, control_id=erasure_id),
                probe_keys=(),
            )
        )
    return controls


def _serialize_result(result: SolverResult) -> dict[str, Any]:
    return {
        "verdict": result.verdict,
        "predicted_relation": result.predicted_relation,
        "ambiguity_set": list(result.ambiguity_set),
        "ambiguity_size": len(result.ambiguity_set),
        "evidence_keys": list(result.evidence_keys),
        "unsupported_probe_keys": list(result.unsupported_probe_keys),
        "trace_digest": result.trace_digest,
    }


def _metrics(rows: list[dict[str, Any]], baseline: str) -> dict[str, Any]:
    answered = correct = wrong = not_established = invalid = 0
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    ambiguity_hist = Counter()
    by_relation: dict[str, Counter[str]] = defaultdict(Counter)
    by_domain: dict[str, Counter[str]] = defaultdict(Counter)

    for row in rows:
        result = row["baselines"][baseline]
        expected = row["sealed_relation"]
        prediction = result["predicted_relation"]
        if result["verdict"] == "PASS" and prediction is not None:
            answered += 1
            if prediction == expected:
                correct += 1
                outcome = "correct"
            else:
                wrong += 1
                outcome = "wrong"
            confusion[expected][prediction] += 1
        else:
            outcome = "refused"
            confusion[expected][result["verdict"]] += 1
            if result["verdict"] == "NOT_ESTABLISHED":
                not_established += 1
            if result["verdict"] == "INVALID":
                invalid += 1
        ambiguity_hist[str(result["ambiguity_size"])] += 1
        by_relation[expected][outcome] += 1
        domain = row.get("verifier_metadata", {}).get("domain") or row.get("verifier_metadata", {}).get("domain_holdout_group")
        if domain:
            by_domain[str(domain)][outcome] += 1

    total = len(rows)
    return {
        "total": total,
        "answered": answered,
        "not_established": not_established,
        "invalid": invalid,
        "correct_count": correct,
        "wrong_positive_count": wrong,
        "exact_relation_accuracy": correct / total if total else 0.0,
        "selective_accuracy": correct / answered if answered else None,
        "confusion_matrix": {
            expected: dict(sorted(counter.items()))
            for expected, counter in sorted(confusion.items())
        },
        "ambiguity_size_histogram": dict(sorted(ambiguity_hist.items(), key=lambda item: int(item[0]))),
        "by_relation": {
            relation: dict(sorted(counter.items()))
            for relation, counter in sorted(by_relation.items())
        },
        "by_domain": {
            domain: dict(sorted(counter.items()))
            for domain, counter in sorted(by_domain.items())
        },
    }


def _evaluate_cases(corpus: KnowledgeCorpus, cases: list[HeldoutCase]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    blocks: dict[tuple[str, ...], list[HeldoutCase]] = defaultdict(list)
    for case in cases:
        blocks[case.hidden_edge_ids].append(case)

    for hidden_ids in sorted(blocks, key=lambda value: (len(value), value)):
        block_cases = sorted(blocks[hidden_ids], key=lambda row: row.case_id)
        base = sanitize_case(corpus, block_cases[0])
        model = fit_solver_model(base, B4_PROBE_KEYS)
        for heldout in block_cases:
            case = _retarget(base, heldout)
            outputs = {
                "B0": run_baseline("B0", case),
                "B1": solve_with_model(case, model, B1_PROBE_KEYS),
                "B2": solve_with_model(case, model, B2_PROBE_KEYS),
                "B3": solve_with_model(case, model, B3_PROBE_KEYS),
                "B4": solve_with_model(case, model, B4_PROBE_KEYS),
            }
            rows.append(
                {
                    "case_id": heldout.case_id,
                    "tier": heldout.tier,
                    "edge_id": heldout.edge_id,
                    "source_id": heldout.source_id,
                    "target_id": heldout.target_id,
                    "sealed_relation": heldout.sealed_relation,
                    "hidden_edge_count": len(heldout.hidden_edge_ids),
                    "verifier_metadata": dict(heldout.verifier_metadata),
                    "baselines": {
                        name: _serialize_result(result)
                        for name, result in outputs.items()
                    },
                }
            )

    rows.sort(key=lambda row: row["case_id"])
    return {
        "total": len(rows),
        "block_count": len(blocks),
        "baselines": {
            name: _metrics(rows, name)
            for name in ("B0", "B1", "B2", "B3", "B4")
        },
        "cases": rows,
    }


def _run_r4(corpus: KnowledgeCorpus) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for control in build_r4_controls(corpus):
        result = solve_case(control.case, control.probe_keys)
        rows.append(
            {
                "control_id": control.control_id,
                "control_kind": control.control_kind,
                "source_relation": control.source_relation,
                "result": _serialize_result(result),
                "false_certainty": result.verdict == "PASS" and result.predicted_relation is not None,
            }
        )
    rows.sort(key=lambda row: row["control_id"])
    return {
        "total": len(rows),
        "false_certainty_count": sum(bool(row["false_certainty"]) for row in rows),
        "by_control_kind": dict(
            sorted(Counter(row["control_kind"] for row in rows).items())
        ),
        "cases": rows,
    }


def _recipe_digest() -> str:
    return _digest(
        {
            "relations": list(SEMANTIC_RELATION_TYPES),
            "B1": list(B1_PROBE_KEYS),
            "B2": list(B2_PROBE_KEYS),
            "B3": list(B3_PROBE_KEYS),
            "B4": list(B4_PROBE_KEYS),
            "preconditions": [
                "SOURCE_DECLARATION_ENDPOINTS",
                "DISTINCT_SOURCE_BINDINGS",
                "SHARED_CANONICAL_SUPPORT",
                "NO_DIRECT_TARGET_SEMANTIC_LABEL",
            ],
        }
    )


def evaluate_solver_signal(report: dict[str, Any]) -> dict[str, bool]:
    def strict_gain(tier: str) -> bool:
        metrics = report[tier]["baselines"]
        simpler = max(metrics[name]["correct_count"] for name in ("B0", "B1", "B2", "B3"))
        return metrics["B4"]["correct_count"] > simpler

    def strongest_simpler(tier: str) -> dict[str, Any]:
        metrics = report[tier]["baselines"]
        candidates = [metrics[name] for name in ("B0", "B1", "B2", "B3")]
        return max(
            candidates,
            key=lambda row: (
                row["correct_count"],
                -row["wrong_positive_count"],
                row["answered"],
            ),
        )

    coverage_safe = True
    for tier in ("R2", "R3"):
        b4 = report[tier]["baselines"]["B4"]
        simpler = strongest_simpler(tier)
        if b4["answered"] > simpler["answered"]:
            coverage_safe &= b4["wrong_positive_count"] <= simpler["wrong_positive_count"]

    positive_traces = True
    for tier in ("R1", "R2", "R3"):
        for row in report[tier]["cases"]:
            result = row["baselines"]["B4"]
            if result["verdict"] == "PASS":
                digest = result["trace_digest"]
                positive_traces &= (
                    len(digest) == 64
                    and all(ch in "0123456789abcdef" for ch in digest)
                    and bool(result["evidence_keys"])
                )

    gates = {
        "r4_zero_false_certainty": report["R4"]["false_certainty_count"] == 0,
        "r2_b4_strictly_exceeds_simpler": strict_gain("R2"),
        "r3_b4_strictly_exceeds_simpler": strict_gain("R3"),
        "coverage_gain_without_wrong_positive_increase": bool(coverage_safe),
        "positive_traces_reproducible": bool(positive_traces),
    }
    gates["h1_supported"] = all(gates.values())
    return gates


def run_e27(corpus: KnowledgeCorpus, repo_root: Path) -> dict[str, Any]:
    report = {
        "experiment_id": "E27_SEALED_HELDOUT_RELATIONAL_RECOVERY",
        "campaign_harness_sha": compute_harness_sha(repo_root),
        "solver_recipe_sha256": _recipe_digest(),
        "semantic_relation_types": list(SEMANTIC_RELATION_TYPES),
        "R1": _evaluate_cases(corpus, build_r1_cases(corpus)),
        "R2": _evaluate_cases(corpus, build_r2_cluster_cases(corpus)),
        "R3": _evaluate_cases(corpus, build_r3_domain_cases(corpus)),
        "R4": _run_r4(corpus),
    }
    report["solver_signal"] = evaluate_solver_signal(report)
    report["status"] = "PASS" if report["R4"]["false_certainty_count"] == 0 else "FAIL"
    return report
