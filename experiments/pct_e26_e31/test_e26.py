from __future__ import annotations

from pathlib import Path

from experiments.pct_e26_e31.constants import KNOWLEDGE_BASELINE_SHA, SOLVER_BASELINE_SHA
from experiments.pct_e26_e31.corpus import build_e26_manifest
from experiments.pct_e26_e31.identity import compute_harness_sha


ROOT = Path(__file__).resolve().parents[2]
FROZEN_MAIN = ROOT / ".crossbranch" / "frozen-main"
FROZEN_SOLVER = ROOT / ".crossbranch" / "frozen-solver"


def test_harness_sha_is_content_derived() -> None:
    digest = compute_harness_sha(ROOT)
    assert len(digest) == 64
    assert int(digest, 16) >= 0


def test_e26_manifest_binds_frozen_inputs() -> None:
    manifest = build_e26_manifest(FROZEN_MAIN, ROOT)
    assert manifest["solver_baseline_sha"] == SOLVER_BASELINE_SHA
    assert manifest["knowledge_baseline_sha"] == KNOWLEDGE_BASELINE_SHA
    assert manifest["campaign_harness_sha"] == compute_harness_sha(ROOT)


def test_e26_counts_come_from_graph() -> None:
    manifest = build_e26_manifest(FROZEN_MAIN, ROOT)
    counts = manifest["direct_graph_counts"]
    assert counts["source_declarations"] > 0
    assert counts["canonical_objects"] > 0
    assert counts["semantic_bridges"] > 0
    assert set(manifest["semantic_relation_types"]) >= {
        "SAME_SEMANTICS",
        "SCOPED_OVERLAP",
        "RELATED_TO",
    }


def test_e26_records_acceptance_manifest_discrepancies_without_substitution() -> None:
    manifest = build_e26_manifest(FROZEN_MAIN, ROOT)
    kinds = {row["kind"] for row in manifest["discrepancies"]}
    assert "ARTIFACT_DIGEST_MISMATCH" in kinds
    assert "REPORT_COUNT_MISMATCH" in kinds
    assert manifest["status"] == "PASS"
    assert manifest["validity_gates"]["sealed_confirmatory_artifact_loaded"] is True
    assert manifest["validity_gates"]["acceptance_manifest_graph_digest_match"] is False
    assert manifest["artifact_provenance"]["source"] == "SUCCESSFUL_CONFIRMATORY_ACTIONS_RUN"


def test_frozen_solver_checkout_is_present_and_separate() -> None:
    assert FROZEN_SOLVER.exists()
    assert FROZEN_MAIN.exists()
    assert FROZEN_SOLVER.resolve() != FROZEN_MAIN.resolve()
