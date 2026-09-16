"""Current-facing reports must not repeat superseded mathematical claims."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_uses_corrected_active_counts_and_evidence_scopes() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "**2,135**" in text
    assert "**1,356**" in text
    assert "v0.16: **1,756**" in text
    assert "v0.17: **1,820**" in text
    assert "v0.18: **1,887**" in text
    assert "v0.19: **1,959**" in text
    assert "Executable declaration evidence | **1 / 176**" in text
    assert "Kernel-verified foundation declarations | **0 / 176**" in text
    assert "Proof-eligible grounding | **0 / 235**" in text
    assert "100% Pass (8/8 Domains)" not in text
    assert "unbroken mathematical dependency chain" not in text


def test_additive_current_integrity_report_states_wounds_and_nonpromotion() -> None:
    report = (ROOT / "docs" / "V0_20_MATHEMATICAL_INTEGRITY_REPORT.md").read_text(encoding="utf-8")
    for phrase in (
        "1 / 176",
        "0 / 176",
        "0 / 235",
        "33 relation conflicts",
        "RELATED_TO < SCOPED_OVERLAP < SAME_SEMANTICS",
        "sealed v0.19",
        "raw topology reachability",
        "proof-eligible grounding",
        "foundation amendment registry",
        "producer source tree",
        "does not claim its own Git commit",
    ):
        assert phrase in report


def test_historical_reports_are_explicitly_superseded_not_silently_rewritten() -> None:
    for relative in (
        "docs/V0_15_2_CONFIRMATORY_REPORT.md",
        "docs/V0_17_MEASURE_REPORT.md",
        "docs/V0_18_DIFFGEOM_REPORT.md",
        "docs/V0_19_COMPLEX_ANALYSIS_REPORT.md",
        "docs/FOUNDATION_BACKFILL_REPORT.md",
        "docs/FOUNDATION_BACKFILL_SPEC.md",
    ):
        prefix = (ROOT / relative).read_text(encoding="utf-8")[:700]
        assert "Historical report" in prefix
        assert "V0_20_MATHEMATICAL_INTEGRITY_REPORT.md" in prefix


def test_machine_readable_integrity_report_is_additive_and_fail_closed() -> None:
    data = json.loads(
        (ROOT / "evidence" / "v0_20_mathematical_integrity_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert data["schema_version"] == "v0.20-mathematical-integrity-report"
    assert data["sealed_inputs"]["v0_19_alignments_sha256"] == "ae2169f7edc3012d92c96c90c5d2707f5f08c62c89002287e90ce44a0e23f2c8"
    assert data["source_counts"]["with_foundation"] == 2135
    assert data["source_counts"]["with_foundation_raw_records"] == 2144
    assert data["source_counts"]["excluded_historical_count_artifacts"] == 4
    assert data["source_counts"]["section_anchors"] == 5
    assert data["foundation_evidence"] == {
        "curated_declarations": 176,
        "executable_verified_declarations": 1,
        "kernel_verified_declarations": 0,
        "proof_eligible_advanced_reachable": 0,
        "advanced_canonical_objects": 235,
    }
    assert data["alignment_projection"]["integrity_wounds"] == 35
    assert data["alignment_projection"]["relation_conflicts_downgraded"] == 33
    provenance = data["provenance"]
    assert provenance["identity_policy"]["git_commit_claimed"] is False
    assert provenance["foundation_amendment_manifest"]["raw_sha256"] == (
        "ffa3cbbc4b6a2b1f580df71d61ad24522d5aafcc1e5062de6cb559e28b16adae"
    )
    assert provenance["foundation_declaration_registry"]["entry_count"] == 176
    assert provenance["foundation_contract_registry"]["entry_count"] == 1
