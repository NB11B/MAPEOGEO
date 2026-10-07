"""Candidate Falsifier: Actively attacks proposed mathematical repairs against
the already-explained 96.1% corpus with a severe regression penalty lambda.

Utility:
U(C) = Delta H(B5 | C) - lambda * E_regression(C)
"""

from typing import Dict, Any

def falsify_candidate_repair(
    candidate_name: str,
    delta_h_b5: float,
    false_splits: int,
    false_merges: int,
    composition_violations: int,
    lambda_penalty: float = 100.0
) -> Dict[str, Any]:
    """
    Evaluates candidate repair against the explained corpus.
    """
    total_regressions = false_splits + false_merges + composition_violations
    regression_cost = lambda_penalty * total_regressions
    net_utility = delta_h_b5 - regression_cost

    survived = total_regressions == 0 and net_utility > 0

    return {
        "candidate": candidate_name,
        "delta_h_b5_gain": delta_h_b5,
        "total_regressions": total_regressions,
        "regression_breakdown": {
            "false_splits": false_splits,
            "false_merges": false_merges,
            "composition_violations": composition_violations
        },
        "lambda_penalty": lambda_penalty,
        "net_utility": net_utility,
        "survived_falsification": survived,
        "verdict": "FALSIFICATION_SURVIVED" if survived else "FALSIFIED_BY_REGRESSION"
    }
