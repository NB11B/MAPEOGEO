from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

from .cases import SanitizedCase, sanitize_case
from .corpus import KnowledgeCorpus
from .e27 import build_r2_cluster_cases, build_r3_domain_cases
from .identity import compute_harness_sha
from .solver import SolverResult, fit_solver_model, solve_with_model


@dataclass(frozen=True)
class MinimumEvidenceResult:
    status: str
    minimum_size: int | None
    witness_probe_keys: tuple[str, ...]
    infeasible_by_size: dict[int, bool]
    upper_bound_size: int
    original_bank_size: int
    erasure_tolerance: int | None
    critical_removals: tuple[dict[str, Any], ...]


def _same_positive(result: SolverResult, reference: SolverResult) -> bool:
    return (
        result.verdict == "PASS"
        and result.predicted_relation is not None
        and result.predicted_relation == reference.predicted_relation
    )


def certify_minimum_evidence(
    case: SanitizedCase,
    result: SolverResult,
    probe_bank: tuple[str, ...],
    max_exact_bank: int,
) -> MinimumEvidenceResult:
    bank = tuple(dict.fromkeys(probe_bank))
    if result.verdict != "PASS" or result.predicted_relation is None:
        raise ValueError("E28 minimum evidence requires a positive reference result")
    if not bank:
        raise ValueError("E28 minimum evidence requires a non-empty binding probe bank")

    model = fit_solver_model(case, bank)
    full = solve_with_model(case, model, bank)
    if not _same_positive(full, result):
        raise ValueError("Binding probe bank does not reproduce the reference result")

    if len(bank) > max_exact_bank:
        return MinimumEvidenceResult(
            status="INCONCLUSIVE_MINIMUM",
            minimum_size=None,
            witness_probe_keys=bank,
            infeasible_by_size={},
            upper_bound_size=len(bank),
            original_bank_size=len(bank),
            erasure_tolerance=None,
            critical_removals=(),
        )

    infeasible: dict[int, bool] = {}
    witness: tuple[str, ...] | None = None
    for size in range(len(bank) + 1):
        successful: tuple[str, ...] | None = None
        for subset in combinations(bank, size):
            candidate = solve_with_model(case, model, subset)
            if _same_positive(candidate, result):
                successful = tuple(subset)
                break
        if successful is None:
            infeasible[size] = True
            continue
        witness = successful
        break

    if witness is None:
        raise AssertionError("Full binding probe bank was sufficient but no witness was found")

    # Redundancy certificate on the original binding bank: largest t such that
    # every deletion of up to t probes still preserves the same unique answer.
    erasure_tolerance = 0
    for removed_count in range(1, len(bank) + 1):
        every_survives = True
        for removed in combinations(bank, removed_count):
            remaining = tuple(key for key in bank if key not in set(removed))
            candidate = solve_with_model(case, model, remaining)
            if not _same_positive(candidate, result):
                every_survives = False
                break
        if every_survives:
            erasure_tolerance = removed_count
        else:
            break

    critical: list[dict[str, Any]] = []
    for key in witness:
        remaining = tuple(candidate for candidate in witness if candidate != key)
        after = solve_with_model(case, model, remaining)
        critical.append(
            {
                "removed_probe": key,
                "remaining_probe_keys": list(remaining),
                "verdict": after.verdict,
                "predicted_relation": after.predicted_relation,
                "ambiguity_set": list(after.ambiguity_set),
                "ambiguity_size": len(after.ambiguity_set),
                "same_positive_answer": _same_positive(after, result),
                "trace_digest": after.trace_digest,
            }
        )

    return MinimumEvidenceResult(
        status="EXACT_MINIMUM_CERTIFIED",
        minimum_size=len(witness),
        witness_probe_keys=witness,
        infeasible_by_size=infeasible,
        upper_bound_size=len(witness),
        original_bank_size=len(bank),
        erasure_tolerance=erasure_tolerance,
        critical_removals=tuple(critical),
    )


def _solver_result_from_row(row: dict[str, Any]) -> SolverResult:
    return SolverResult(
        verdict=str(row["verdict"]),
        predicted_relation=row.get("predicted_relation"),
        ambiguity_set=tuple(row.get("ambiguity_set", [])),
        evidence_keys=tuple(row.get("evidence_keys", [])),
        unsupported_probe_keys=tuple(row.get("unsupported_probe_keys", [])),
        trace_digest=str(row["trace_digest"]),
    )


def _serialize(audit: MinimumEvidenceResult) -> dict[str, Any]:
    return {
        "status": audit.status,
        "minimum_size": audit.minimum_size,
        "witness_probe_keys": list(audit.witness_probe_keys),
        "infeasible_by_size": {
            str(size): value for size, value in sorted(audit.infeasible_by_size.items())
        },
        "upper_bound_size": audit.upper_bound_size,
        "original_bank_size": audit.original_bank_size,
        "erasure_tolerance": audit.erasure_tolerance,
        "critical_removals": list(audit.critical_removals),
    }


def run_e28(
    e27_report: dict[str, Any],
    corpus: KnowledgeCorpus,
    repo_root: Path,
    *,
    max_exact_bank: int = 8,
) -> dict[str, Any]:
    case_index = {
        case.case_id: case
        for case in build_r2_cluster_cases(corpus) + build_r3_domain_cases(corpus)
    }

    rows: list[dict[str, Any]] = []
    for tier in ("R2", "R3"):
        for row in e27_report[tier]["cases"]:
            b4 = row["baselines"]["B4"]
            if not (
                b4["verdict"] == "PASS"
                and b4["predicted_relation"] == row["sealed_relation"]
                and b4["evidence_keys"]
            ):
                continue
            heldout = case_index[row["case_id"]]
            case = sanitize_case(corpus, heldout)
            reference = _solver_result_from_row(b4)
            bank = tuple(reference.evidence_keys)
            audit = certify_minimum_evidence(
                case,
                reference,
                bank,
                max_exact_bank=max_exact_bank,
            )
            serialized = _serialize(audit)
            serialized.update(
                {
                    "case_id": row["case_id"],
                    "tier": tier,
                    "sealed_relation": row["sealed_relation"],
                    "reference_trace_digest": reference.trace_digest,
                }
            )
            rows.append(serialized)

    rows.sort(key=lambda item: (item["tier"], item["case_id"]))
    exact_count = sum(row["status"] == "EXACT_MINIMUM_CERTIFIED" for row in rows)
    inconclusive_count = sum(row["status"] == "INCONCLUSIVE_MINIMUM" for row in rows)
    return {
        "experiment_id": "E28_MINIMAL_EVIDENCE_ERASURE_NULLSPACE",
        "status": "PASS",
        "campaign_harness_sha": compute_harness_sha(repo_root),
        "max_exact_bank": max_exact_bank,
        "eligible_correct_recoveries": len(rows),
        "exact_minimum_certified": exact_count,
        "inconclusive_minimum": inconclusive_count,
        "cases": rows,
        "claim_boundary": (
            "Exact minima are certified only within each case's finite binding-probe bank; "
            "resource-bounded larger banks remain INCONCLUSIVE_MINIMUM."
        ),
    }
