from __future__ import annotations

from pathlib import Path

import pytest

from experiments.pct_e26_e31.cases import sanitize_case
from experiments.pct_e26_e31.corpus import load_knowledge_corpus
from experiments.pct_e26_e31.e27 import build_r2_cluster_cases, build_r3_domain_cases, run_e27
from experiments.pct_e26_e31.e28 import certify_minimum_evidence, run_e28
from experiments.pct_e26_e31.solver import SolverResult


ROOT = Path(__file__).resolve().parents[2]
FROZEN_MAIN = ROOT / ".crossbranch" / "frozen-main"


@pytest.fixture(scope="module")
def campaign():
    corpus = load_knowledge_corpus(FROZEN_MAIN, ROOT)
    report = run_e27(corpus, ROOT)
    cases = {
        case.case_id: case
        for case in build_r2_cluster_cases(corpus) + build_r3_domain_cases(corpus)
    }
    for tier in ("R2", "R3"):
        for row in report[tier]["cases"]:
            b4 = row["baselines"]["B4"]
            if (
                b4["verdict"] == "PASS"
                and b4["predicted_relation"] == row["sealed_relation"]
                and b4["evidence_keys"]
            ):
                result = SolverResult(
                    verdict=b4["verdict"],
                    predicted_relation=b4["predicted_relation"],
                    ambiguity_set=tuple(b4["ambiguity_set"]),
                    evidence_keys=tuple(b4["evidence_keys"]),
                    unsupported_probe_keys=tuple(b4["unsupported_probe_keys"]),
                    trace_digest=b4["trace_digest"],
                )
                return corpus, report, sanitize_case(corpus, cases[row["case_id"]]), result
    pytest.fail("E27 produced no correctly recovered B4 case with binding evidence")


def test_exact_minimum_excludes_every_smaller_cardinality(campaign) -> None:
    _, _, case, result = campaign
    bank = tuple(result.evidence_keys)
    audit = certify_minimum_evidence(case, result, bank, max_exact_bank=16)
    assert audit.status == "EXACT_MINIMUM_CERTIFIED"
    assert audit.minimum_size is not None
    assert all(audit.infeasible_by_size[size] for size in range(audit.minimum_size))
    assert audit.witness_probe_keys


def test_resource_bound_returns_inconclusive_not_exact(campaign) -> None:
    _, _, case, result = campaign
    bank = tuple(result.evidence_keys)
    audit = certify_minimum_evidence(case, result, bank, max_exact_bank=0)
    assert audit.status == "INCONCLUSIVE_MINIMUM"
    assert audit.minimum_size is None
    assert audit.upper_bound_size <= len(bank)


def test_e28_never_labels_unexhausted_search_exact(campaign) -> None:
    corpus, report, _, _ = campaign
    audit = run_e28(report, corpus, ROOT, max_exact_bank=8)
    assert audit["eligible_correct_recoveries"] > 0
    for row in audit["cases"]:
        if row["status"] == "EXACT_MINIMUM_CERTIFIED":
            minimum = row["minimum_size"]
            assert all(row["infeasible_by_size"][str(size)] for size in range(minimum))
        elif row["status"] == "INCONCLUSIVE_MINIMUM":
            assert row["minimum_size"] is None
        else:
            raise AssertionError(f"Unexpected E28 status: {row['status']}")
