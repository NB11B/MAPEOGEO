from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from experiments.pct_e25ij.lifecycle import GLOBAL_COMPONENT, apply_event_state
from experiments.pct_e25ij.receipts import canonical_sha256, make_event, make_receipt

from .cases import HeldoutCase, build_r1_cases
from .constants import KNOWLEDGE_BASELINE_SHA, KNOWLEDGE_GRAPH_BASENAME, SOLVER_BASELINE_SHA
from .corpus import KnowledgeCorpus
from .e27 import build_r2_cluster_cases, build_r3_domain_cases, build_r4_controls
from .identity import compute_harness_sha


GLOBAL_POLICY_ROLE = "E31_GLOBAL_STRICT_C5_POLICY"


def _sha(value: Any) -> str:
    return canonical_sha256(value)


def _case_maps(corpus: KnowledgeCorpus) -> dict[str, HeldoutCase]:
    rows = build_r1_cases(corpus) + build_r2_cluster_cases(corpus) + build_r3_domain_cases(corpus)
    return {case.case_id: case for case in rows}


def _binding_hashes(
    *,
    campaign_harness_sha: str,
    solver_recipe_sha256: str,
    input_payload: Any,
    output_payload: Any,
    answer_payload: Any,
    artifact_sha256: str,
) -> dict[str, str]:
    return {
        "solver_baseline_sha": SOLVER_BASELINE_SHA,
        "knowledge_baseline_sha": KNOWLEDGE_BASELINE_SHA,
        "campaign_harness_sha": campaign_harness_sha,
        "solver_recipe_sha256": solver_recipe_sha256,
        "input_sha256": _sha(input_payload),
        "output_sha256": _sha(output_payload),
        "answer_sha256": _sha(answer_payload),
        "artifact_sha256": artifact_sha256,
    }


def _direction_a_specs(
    corpus: KnowledgeCorpus,
    e27_report: dict[str, Any],
    campaign_harness_sha: str,
    artifact_sha256: str,
) -> list[dict[str, Any]]:
    case_map = _case_maps(corpus)
    specs: list[dict[str, Any]] = []
    recipe = str(e27_report["solver_recipe_sha256"])

    for tier in ("R1", "R2", "R3"):
        for row in e27_report[tier]["cases"]:
            case = case_map[row["case_id"]]
            output = row["baselines"]["B4"]
            answer = {
                "sealed_relation": row["sealed_relation"],
                "edge_id": row["edge_id"],
            }
            input_descriptor = {
                "binding_kind": "DERIVED_SANITIZED_INPUT_DESCRIPTOR",
                "base_artifact_sha256": artifact_sha256,
                "case_id": case.case_id,
                "tier": case.tier,
                "source_id": case.source_id,
                "target_id": case.target_id,
                "hidden_edge_ids": list(case.hidden_edge_ids),
                "sanitization_recipe": [
                    "REMOVE_HELDOUT_SEMANTIC_EDGES",
                    "REMOVE_PARALLEL_TARGET_SEMANTIC_LABELS",
                    "REMOVE_TARGET_REPRESENTS_CROSS_SOURCE_STATUS",
                    "HIDE_VERIFIER_ONLY_GROUP_METADATA",
                ],
            }
            if output["verdict"] == "PASS" and output["predicted_relation"] is not None:
                agreement = "PASS" if output["predicted_relation"] == row["sealed_relation"] else "FAIL"
            else:
                agreement = "NOT_ESTABLISHED"
            bindings = _binding_hashes(
                campaign_harness_sha=campaign_harness_sha,
                solver_recipe_sha256=recipe,
                input_payload=input_descriptor,
                output_payload=output,
                answer_payload=answer,
                artifact_sha256=artifact_sha256,
            )
            specs.append(
                {
                    "component_id": f"E31:A:{tier}:{case.case_id}",
                    "direction": "A",
                    "contract": f"E27_{tier}_B4_RELATIONAL_RECOVERY",
                    "case_id": case.case_id,
                    "source_ref": f"frozen-main-semantic-edge:{row['edge_id']}",
                    "input_payload": input_descriptor,
                    "output_payload": output,
                    "answer_payload": answer,
                    "bindings": bindings,
                    "c5a_verdict": agreement,
                    "c3_applicable": False,
                    "c4_applicable": False,
                }
            )

    controls = {control.control_id: control for control in build_r4_controls(corpus)}
    for row in e27_report["R4"]["cases"]:
        control = controls[row["control_id"]]
        output = row["result"]
        answer = {
            "required_behavior": "REFUSE_UNSUPPORTED_POSITIVE_INFERENCE",
            "source_relation": row["source_relation"],
            "control_kind": row["control_kind"],
        }
        input_descriptor = {
            "binding_kind": "R4_CONTROL_INPUT_DESCRIPTOR",
            "base_artifact_sha256": artifact_sha256,
            "control_id": row["control_id"],
            "control_kind": row["control_kind"],
            "source_id": control.case.source_id,
            "target_id": control.case.target_id,
            "visible_edge_ids_sha256": _sha(list(control.case.visible_edge_ids)),
        }
        agreement = "FAIL" if row["false_certainty"] else "PASS"
        bindings = _binding_hashes(
            campaign_harness_sha=campaign_harness_sha,
            solver_recipe_sha256=recipe,
            input_payload=input_descriptor,
            output_payload=output,
            answer_payload=answer,
            artifact_sha256=artifact_sha256,
        )
        specs.append(
            {
                "component_id": f"E31:A:R4:{row['control_id']}",
                "direction": "A",
                "contract": "E27_R4_REFUSAL_CONTROL",
                "case_id": row["control_id"],
                "source_ref": f"synthetic-control:{row['control_kind']}:{row['source_relation']}",
                "input_payload": input_descriptor,
                "output_payload": output,
                "answer_payload": answer,
                "bindings": bindings,
                "c5a_verdict": agreement,
                "c3_applicable": False,
                "c4_applicable": False,
            }
        )

    specs.sort(key=lambda row: row["component_id"])
    return specs


def _direction_b_specs(
    e30_report: dict[str, Any],
    campaign_harness_sha: str,
) -> list[dict[str, Any]]:
    replay_recipe = _sha(
        {
            "capability_matrix": e30_report["capability_matrix"],
            "scored_requests": [
                {"replay_id": row["replay_id"], "request": row["request"]}
                for row in e30_report["replays"]
                if row["scored"]
            ],
        }
    )
    code_artifact = _sha({"frozen_main_pct_checkout_sha": KNOWLEDGE_BASELINE_SHA})
    specs: list[dict[str, Any]] = []
    for row in e30_report["replays"]:
        if not row["scored"]:
            continue
        answer = {"expected": row["expected"], "required_replay_verdict": "PASS"}
        bindings = _binding_hashes(
            campaign_harness_sha=campaign_harness_sha,
            solver_recipe_sha256=replay_recipe,
            input_payload=row["request"],
            output_payload=row["result"],
            answer_payload=answer,
            artifact_sha256=code_artifact,
        )
        specs.append(
            {
                "component_id": f"E31:B:{row['replay_id']}",
                "direction": "B",
                "contract": row["replay_id"],
                "case_id": row["replay_id"],
                "source_ref": f"frozen-main-pct:{row['replay_id']}",
                "input_payload": row["request"],
                "output_payload": row["result"],
                "answer_payload": answer,
                "bindings": bindings,
                "c5a_verdict": row["verdict"],
                "c3_applicable": row["replay_id"] == "E5_DIRECT_CHAIN_MAP_CORRUPTION",
                "c4_applicable": False,
            }
        )
    specs.sort(key=lambda row: row["component_id"])
    return specs


def _build_ledger(specs: list[dict[str, Any]]) -> dict[str, Any]:
    receipts: list[dict[str, Any]] = []
    components: list[dict[str, Any]] = []
    revision = 1

    policy = make_receipt(
        component_id=GLOBAL_COMPONENT,
        component_epoch=0,
        layer="C5",
        role=GLOBAL_POLICY_ROLE,
        mathematical_verdict="PASS",
        content={"policy": "STRICT_AND", "requires": ["C5A_EXACT_RESULT", "C5B_PROVENANCE_BINDING"]},
        dependency_receipt_ids=[],
        source_statement_sha256=_sha("E31_STRICT_AND_POLICY"),
        evidence_refs=["docs/superpowers/specs/2026-09-15-e26-e31-cross-branch-general-solver-validation-design.md"],
        predecessor_receipt_id=None,
        issuance_revision=revision,
    )
    receipts.append(policy)
    revision += 1

    for spec in specs:
        component_id = spec["component_id"]
        bindings = spec["bindings"]
        source_hash = bindings["answer_sha256"]
        epoch = 0

        c0 = make_receipt(
            component_id=component_id,
            component_epoch=epoch,
            layer="C0",
            role="C0_IDENTITY",
            mathematical_verdict="PASS",
            content={
                "solver_baseline_sha": bindings["solver_baseline_sha"],
                "knowledge_baseline_sha": bindings["knowledge_baseline_sha"],
                "campaign_harness_sha": bindings["campaign_harness_sha"],
                "artifact_sha256": bindings["artifact_sha256"],
                "direction": spec["direction"],
                "case_id": spec["case_id"],
            },
            dependency_receipt_ids=[],
            source_statement_sha256=source_hash,
            evidence_refs=[spec["source_ref"]],
            predecessor_receipt_id=None,
            issuance_revision=revision,
        )
        revision += 1
        c1 = make_receipt(
            component_id=component_id,
            component_epoch=epoch,
            layer="C1",
            role="C1_ANSWER_BINDING",
            mathematical_verdict="PASS",
            content={
                "answer_sha256": bindings["answer_sha256"],
                "answer_binding": spec["answer_payload"],
                "source_ref": spec["source_ref"],
            },
            dependency_receipt_ids=[c0["receipt_id"]],
            source_statement_sha256=source_hash,
            evidence_refs=[spec["source_ref"]],
            predecessor_receipt_id=None,
            issuance_revision=revision,
        )
        revision += 1
        c2_verdict = (
            "NOT_ESTABLISHED"
            if spec["output_payload"].get("verdict") in {"ERROR", "INVALID"}
            else "PASS"
        )
        c2 = make_receipt(
            component_id=component_id,
            component_epoch=epoch,
            layer="C2",
            role="C2_EXECUTABLE_RESULT",
            mathematical_verdict=c2_verdict,
            content={
                "input_sha256": bindings["input_sha256"],
                "output_sha256": bindings["output_sha256"],
                "solver_recipe_sha256": bindings["solver_recipe_sha256"],
            },
            dependency_receipt_ids=[c1["receipt_id"]],
            source_statement_sha256=source_hash,
            evidence_refs=["E27" if spec["direction"] == "A" else "E30"],
            predecessor_receipt_id=None,
            issuance_revision=revision,
        )
        revision += 1

        c3 = None
        if spec["c3_applicable"]:
            c3 = make_receipt(
                component_id=component_id,
                component_epoch=epoch,
                layer="C3",
                role="C3_CHAIN_MAP_COMMUTATION",
                mathematical_verdict=spec["c5a_verdict"],
                content={"contract": spec["contract"], "output_sha256": bindings["output_sha256"]},
                dependency_receipt_ids=[c2["receipt_id"]],
                source_statement_sha256=source_hash,
                evidence_refs=["E30:E5_DIRECT_CHAIN_MAP_CORRUPTION"],
                predecessor_receipt_id=None,
                issuance_revision=revision,
            )
            revision += 1

        c5a_deps = [c2["receipt_id"]] + ([c3["receipt_id"]] if c3 else [])
        c5a = make_receipt(
            component_id=component_id,
            component_epoch=epoch,
            layer="C5",
            role="C5A_EXACT_RESULT",
            mathematical_verdict=spec["c5a_verdict"],
            content={
                "output_sha256": bindings["output_sha256"],
                "answer_sha256": bindings["answer_sha256"],
                "agreement_verdict": spec["c5a_verdict"],
            },
            dependency_receipt_ids=c5a_deps,
            source_statement_sha256=source_hash,
            evidence_refs=[spec["source_ref"]],
            predecessor_receipt_id=None,
            issuance_revision=revision,
        )
        revision += 1
        c5b = make_receipt(
            component_id=component_id,
            component_epoch=epoch,
            layer="C5",
            role="C5B_PROVENANCE_BINDING",
            mathematical_verdict="PASS",
            content={"bindings": bindings, "source_ref": spec["source_ref"]},
            dependency_receipt_ids=[c2["receipt_id"]],
            source_statement_sha256=source_hash,
            evidence_refs=[spec["source_ref"]],
            predecessor_receipt_id=None,
            issuance_revision=revision,
        )
        revision += 1

        c5_pass = (
            c2_verdict == "PASS"
            and spec["c5a_verdict"] == "PASS"
            and (c3 is None or c3["mathematical_verdict"] == "PASS")
        )
        c5_deps = [
            c0["receipt_id"],
            c1["receipt_id"],
            c2["receipt_id"],
            c5a["receipt_id"],
            c5b["receipt_id"],
            policy["receipt_id"],
        ] + ([c3["receipt_id"]] if c3 else [])
        c5 = make_receipt(
            component_id=component_id,
            component_epoch=epoch,
            layer="C5",
            role="C5_ELIGIBILITY",
            mathematical_verdict="PASS" if c5_pass else "NOT_ESTABLISHED",
            content={
                "policy": "STRICT_AND",
                "c5a_state": spec["c5a_verdict"],
                "c5b_state": "PASS",
                "c3_state": c3["mathematical_verdict"] if c3 else "NOT_APPLICABLE",
                "c4_state": "NOT_APPLICABLE",
            },
            dependency_receipt_ids=c5_deps,
            source_statement_sha256=source_hash,
            evidence_refs=["E31_STRICT_AND"],
            predecessor_receipt_id=None,
            issuance_revision=revision,
        )
        revision += 1

        receipts.extend([c0, c1, c2])
        if c3:
            receipts.append(c3)
        receipts.extend([c5a, c5b, c5])
        components.append(
            {
                "component_id": component_id,
                "component_epoch": epoch,
                "contract": spec["contract"],
                "direction": spec["direction"],
                "case_id": spec["case_id"],
                "bindings": bindings,
                "applicability_mask": {
                    "C3": bool(spec["c3_applicable"]),
                    "C4": bool(spec["c4_applicable"]),
                },
                "applicability_reasons": {
                    "C3": None if spec["c3_applicable"] else "NO_CHAIN_MAP_CONTRACT",
                    "C4": None if spec["c4_applicable"] else "NO_INDUCED_HOMOLOGY_MAP_CONTRACT",
                },
            }
        )

    return {
        "experiment_id": "E31_BIDIRECTIONAL_RECEIPT_LEDGER",
        "components": components,
        "receipts": receipts,
        "events": [],
        "policy_receipt_id": policy["receipt_id"],
    }


def _active_role(
    receipts: list[dict[str, Any]],
    states: dict[str, str],
    component_id: str,
    role: str,
) -> dict[str, Any] | None:
    candidates = [
        receipt
        for receipt in receipts
        if receipt["component_id"] == component_id
        and receipt["role"] == role
        and states.get(receipt["receipt_id"]) == "ACTIVE"
    ]
    return max(candidates, key=lambda r: (r["issuance_revision"], r["receipt_id"])) if candidates else None


def derive_e31_closure(
    ledger: dict[str, Any], events: Iterable[dict[str, Any]] | None = None
) -> dict[str, Any]:
    receipts = ledger["receipts"]
    all_events = list(ledger.get("events", [])) + list(events or [])
    epochs = {component["component_id"]: component["component_epoch"] for component in ledger["components"]}
    authority = apply_event_state(receipts, all_events, epochs)
    states = authority["receipt_states"]

    components_out: list[dict[str, Any]] = []
    for metadata in sorted(ledger["components"], key=lambda row: row["component_id"]):
        component_id = metadata["component_id"]
        closure: dict[str, dict[str, Any]] = {}
        for layer, role in (
            ("C0", "C0_IDENTITY"),
            ("C1", "C1_ANSWER_BINDING"),
            ("C2", "C2_EXECUTABLE_RESULT"),
        ):
            receipt = _active_role(receipts, states, component_id, role)
            closure[layer] = {
                "state": "PASS" if receipt and receipt["mathematical_verdict"] == "PASS" else "NOT_ESTABLISHED",
                "receipt_id": receipt["receipt_id"] if receipt else None,
            }

        for layer, role in (
            ("C3", "C3_CHAIN_MAP_COMMUTATION"),
            ("C4", "C4_HOMOLOGY_MAP_AGREEMENT"),
        ):
            if not metadata["applicability_mask"][layer]:
                closure[layer] = {
                    "state": "NOT_APPLICABLE",
                    "receipt_id": None,
                    "reason": metadata["applicability_reasons"][layer],
                }
            else:
                receipt = _active_role(receipts, states, component_id, role)
                closure[layer] = {
                    "state": "PASS" if receipt and receipt["mathematical_verdict"] == "PASS" else "NOT_ESTABLISHED",
                    "receipt_id": receipt["receipt_id"] if receipt else None,
                }

        c5 = _active_role(receipts, states, component_id, "C5_ELIGIBILITY")
        c5a = _active_role(receipts, states, component_id, "C5A_EXACT_RESULT")
        c5b = _active_role(receipts, states, component_id, "C5B_PROVENANCE_BINDING")
        closure["C5"] = {
            "state": "PASS" if c5 and c5["mathematical_verdict"] == "PASS" else "NOT_ESTABLISHED",
            "receipt_id": c5["receipt_id"] if c5 else None,
            "c5a_state": c5a["mathematical_verdict"] if c5a else "NOT_ESTABLISHED",
            "c5b_state": c5b["mathematical_verdict"] if c5b else "NOT_ESTABLISHED",
        }

        frontier = None
        for layer in ("C5", "C4", "C3", "C2", "C1", "C0"):
            if closure[layer]["state"] == "PASS":
                frontier = layer
                break

        component_receipts = [r for r in receipts if r["component_id"] == component_id]
        components_out.append(
            {
                "component_id": component_id,
                "direction": metadata["direction"],
                "contract": metadata["contract"],
                "closure": closure,
                "effective_frontier": frontier,
                "active_receipt_ids": sorted(
                    r["receipt_id"] for r in component_receipts if states[r["receipt_id"]] == "ACTIVE"
                ),
                "stale_receipt_ids": sorted(
                    r["receipt_id"] for r in component_receipts if states[r["receipt_id"]] == "STALE"
                ),
                "revoked_receipt_ids": sorted(
                    r["receipt_id"] for r in component_receipts if states[r["receipt_id"]] == "REVOKED"
                ),
            }
        )

    histogram = Counter(component["effective_frontier"] or "NONE" for component in components_out)
    return {
        "components": components_out,
        "frontier_histogram": dict(sorted(histogram.items())),
        "receipt_state_histogram": dict(sorted(Counter(states.values()).items())),
    }


def _lifecycle_change_check(ledger: dict[str, Any], change: str, role: str) -> dict[str, Any]:
    targets = [
        receipt
        for receipt in ledger["receipts"]
        if receipt["component_id"] != GLOBAL_COMPONENT and receipt["role"] == role
    ]
    events: list[dict[str, Any]] = []
    revision = max(receipt["issuance_revision"] for receipt in ledger["receipts"]) + 1
    for receipt in targets:
        events.append(
            make_event(
                revision=revision,
                event_type="REVOKE",
                target_receipt_id=receipt["receipt_id"],
                component_id=receipt["component_id"],
                reason_code=change.upper(),
            )
        )
        revision += 1

    epochs = {component["component_id"]: component["component_epoch"] for component in ledger["components"]}
    authority = apply_event_state(ledger["receipts"], events, epochs)
    states = authority["receipt_states"]
    c5_receipts = [
        receipt
        for receipt in ledger["receipts"]
        if receipt["component_id"] != GLOBAL_COMPONENT and receipt["role"] == "C5_ELIGIBILITY"
    ]
    affected_components = {receipt["component_id"] for receipt in targets}
    relevant_c5 = [receipt for receipt in c5_receipts if receipt["component_id"] in affected_components]
    return {
        "affected_component_count": len(affected_components),
        "target_receipt_count": len(targets),
        "descendants_staled": bool(relevant_c5)
        and all(states[receipt["receipt_id"]] == "STALE" for receipt in relevant_c5),
        "old_c5_reactivated": any(states[receipt["receipt_id"]] == "ACTIVE" for receipt in relevant_c5),
        "event_count": len(events),
    }


def run_e31(
    corpus: KnowledgeCorpus,
    e27_report: dict[str, Any],
    e30_report: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    harness = compute_harness_sha(repo_root)
    graph_artifact_sha = corpus.artifact_digests[KNOWLEDGE_GRAPH_BASENAME]
    specs_a = _direction_a_specs(corpus, e27_report, harness, graph_artifact_sha)
    specs_b = _direction_b_specs(e30_report, harness)
    ledger = _build_ledger(specs_a + specs_b)
    derived = derive_e31_closure(ledger)

    lifecycle_checks = {
        "solver_baseline_change": _lifecycle_change_check(ledger, "SOLVER_BASELINE_CHANGE", "C0_IDENTITY"),
        "knowledge_baseline_change": _lifecycle_change_check(ledger, "KNOWLEDGE_BASELINE_CHANGE", "C0_IDENTITY"),
        "harness_change": _lifecycle_change_check(ledger, "HARNESS_CHANGE", "C0_IDENTITY"),
        "recipe_change": _lifecycle_change_check(ledger, "RECIPE_CHANGE", "C2_EXECUTABLE_RESULT"),
        "artifact_change": _lifecycle_change_check(ledger, "ARTIFACT_CHANGE", "C0_IDENTITY"),
    }
    lifecycle_pass = all(
        row["affected_component_count"] > 0
        and row["descendants_staled"]
        and not row["old_c5_reactivated"]
        for row in lifecycle_checks.values()
    )
    return {
        "experiment_id": "E31_BIDIRECTIONAL_SOLVER_VERIFIER_CLOSURE",
        "status": "PASS" if lifecycle_pass else "FAIL",
        "solver_baseline_sha": SOLVER_BASELINE_SHA,
        "knowledge_baseline_sha": KNOWLEDGE_BASELINE_SHA,
        "campaign_harness_sha": harness,
        "direction_a_component_count": len(specs_a),
        "direction_b_component_count": len(specs_b),
        "semantic_graph_mutations": 0,
        "ledger": ledger,
        "derived_closure": derived,
        "lifecycle_checks": lifecycle_checks,
        "claim_boundary": "E31_DERIVES_AUDITABLE_REVOCABLE_CLOSURE_WITHOUT_MUTATING_MAIN_OR_PROMOTING_SEMANTICS",
    }
