from __future__ import annotations

from .adversaries import build_adversarial_matrix
from .morphisms import run_c5a_audit
from .provenance import run_c5b_audit


POLICIES = {
    "STRICT_AND": lambda a, b: a and b,
    "MAP_ONLY": lambda a, b: a,
    "PROVENANCE_ONLY": lambda a, b: b,
    "ANY_AXIS": lambda a, b: a or b,
}


def _passed(state: str) -> bool:
    return state == "PASS"


def _empty_metrics() -> dict:
    return {
        "valid_accepts": 0,
        "valid_rejects": 0,
        "false_accepts": 0,
        "false_rejects": 0,
        "correct_rejects": 0,
        "adversarial_cases": 0,
    }


def _finalize_metrics(metrics: dict) -> dict:
    adversarial = metrics["adversarial_cases"]
    valid_total = metrics["valid_accepts"] + metrics["valid_rejects"]
    return {
        **metrics,
        "false_accept_rate": metrics["false_accepts"] / adversarial if adversarial else 0.0,
        "false_reject_rate": metrics["valid_rejects"] / valid_total if valid_total else 0.0,
    }


def run_e25h_policy_comparison() -> dict:
    c5a = run_c5a_audit()
    c5b = run_c5b_audit()
    c5a_by_contract = {c["contract"]: c for c in c5a["components"]}
    c5b_by_contract = {c["contract"]: c for c in c5b["components"]}
    matrix = build_adversarial_matrix()

    aggregate = {name: _empty_metrics() for name in POLICIES}
    contracts = []
    for contract_case in matrix:
        contract = contract_case["contract"]
        valid_a = bool(c5a_by_contract[contract]["all_routes_agree"])
        valid_b = c5b_by_contract[contract]["provenance_state"] == "PASS"
        policy_metrics = {name: _empty_metrics() for name in POLICIES}

        for name, policy in POLICIES.items():
            accepted = policy(valid_a, valid_b)
            if accepted:
                policy_metrics[name]["valid_accepts"] += 1
                aggregate[name]["valid_accepts"] += 1
            else:
                policy_metrics[name]["valid_rejects"] += 1
                policy_metrics[name]["false_rejects"] += 1
                aggregate[name]["valid_rejects"] += 1
                aggregate[name]["false_rejects"] += 1

        enriched_cases = []
        for case in contract_case["adversarial_cases"]:
            a = _passed(case["c5a_state"])
            b = _passed(case["c5b_state"])
            decisions = {}
            for name, policy in POLICIES.items():
                accepted = policy(a, b)
                decisions[name] = "ACCEPT" if accepted else "REJECT"
                policy_metrics[name]["adversarial_cases"] += 1
                aggregate[name]["adversarial_cases"] += 1
                if accepted:
                    policy_metrics[name]["false_accepts"] += 1
                    aggregate[name]["false_accepts"] += 1
                else:
                    policy_metrics[name]["correct_rejects"] += 1
                    aggregate[name]["correct_rejects"] += 1
            enriched_cases.append({**case, "policy_decisions": decisions})

        finalized = {name: _finalize_metrics(metrics) for name, metrics in policy_metrics.items()}
        strict_ok = finalized["STRICT_AND"]["false_accepts"] == 0 and finalized["STRICT_AND"]["valid_rejects"] == 0
        contracts.append({
            "contract": contract,
            "c5a_valid_state": "PASS" if valid_a else "FAIL",
            "c5b_valid_state": "PASS" if valid_b else "FAIL",
            "valid_case": {"c5a_state": "PASS" if valid_a else "FAIL", "c5b_state": "PASS" if valid_b else "FAIL"},
            "adversarial_cases": enriched_cases,
            "policy_metrics": finalized,
            "strict_c5_eligible": bool(valid_a and valid_b and strict_ok),
        })

    policies = {name: _finalize_metrics(metrics) for name, metrics in aggregate.items()}
    strict_policy_acceptable = (
        policies["STRICT_AND"]["false_accepts"] == 0
        and policies["STRICT_AND"]["valid_rejects"] == 0
        and all(c["policy_metrics"]["STRICT_AND"]["false_accepts"] == 0 for c in contracts)
    )
    single_axis_survivors = [
        name for name in ("MAP_ONLY", "PROVENANCE_ONLY")
        if policies[name]["false_accepts"] == 0 and policies[name]["valid_rejects"] == 0
    ]
    status = "PASS" if strict_policy_acceptable else "FAIL"
    return {
        "experiment_id": "E25H_C5_POLICY_COMPARISON",
        "status": status,
        "strict_policy_acceptable": strict_policy_acceptable,
        "single_axis_policies_surviving_all_controls": single_axis_survivors,
        "policies": policies,
        "contracts": contracts,
        "component_count": len(contracts),
        "adversarial_case_count": sum(len(c["adversarial_cases"]) for c in contracts),
        "claim_boundary": "Policy comparison applies only to the four frozen source-bound contracts and preregistered synthetic C5 adversaries; it does not promote repository semantics automatically.",
    }
