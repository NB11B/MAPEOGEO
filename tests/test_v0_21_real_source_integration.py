from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.freeze_v0_21_admission import freeze_admission_report
from scripts.source_admission_v0_21 import admit_sources

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "formal" / "source_registry_v0_21.json"
FROZEN_DECLARATIONS = ROOT / "formal" / "source_declarations_v0_21.json.gz"
FROZEN_EVIDENCE = ROOT / "evidence" / "v0_21_source_admission_manifest.json"
EXPECTED_SOURCES = {
    "OPEN_LOGIC_PROJECT",
    "LEVIN_DISCRETE",
    "JUDSON_AATA",
    "LEBL_BASIC_ANALYSIS",
    "LEBL_DIFFYQS",
}
EXPECTED_COUNTS = {
    "OPEN_LOGIC_PROJECT": 1244,
    "LEVIN_DISCRETE": 68,
    "JUDSON_AATA": 275,
    "LEBL_BASIC_ANALYSIS": 440,
    "LEBL_DIFFYQS": 48,
}
FORBIDDEN_KEYS = {
    "statement_text",
    "proof_text",
    "source_prose",
    "page_image",
    "statement",
    "body",
}


@pytest.mark.skipif(
    os.environ.get("MAPEOGEO_RUN_NETWORK_SOURCE_TESTS") != "1",
    reason="explicit network source verification is disabled",
)
def test_real_pinned_sources_replay_exact_frozen_zero_prose_identities(tmp_path: Path):
    result = admit_sources(REGISTRY, tmp_path / "sources")
    counts = result.counts_by_source()
    assert set(counts) == EXPECTED_SOURCES
    assert counts == EXPECTED_COUNTS
    assert sum(counts.values()) == 2075 == len(result.metadata)

    for row in result.metadata:
        assert FORBIDDEN_KEYS.isdisjoint(row)
        assert row["canonical_status"] == "UNRESOLVED"
        assert row["formal_status"] == "UNFORMALIZED"
        assert row["executable_status"] == "UNTESTED"
        assert len(row["statement_sha256"]) == 64
        assert len(row["revision"]) == 40

    live_report = tmp_path / "live.json"
    live_report.write_text(
        json.dumps(result.report(), sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    live_declarations = tmp_path / "source_declarations_v0_21.json.gz"
    live_evidence = tmp_path / "v0_21_source_admission_manifest.json"
    manifest = freeze_admission_report(live_report, live_declarations, live_evidence)

    assert manifest["admitted_source_occurrences"] == 2075
    assert manifest["unique_statement_bodies"] == 2010
    assert manifest["duplicate_statement_hash_groups"] == 41
    assert manifest["duplicate_statement_occurrences"] == 65
    assert live_declarations.read_bytes() == FROZEN_DECLARATIONS.read_bytes()
    assert live_evidence.read_bytes() == FROZEN_EVIDENCE.read_bytes()

    out = os.environ.get("V0_21_LIVE_REPORT")
    if out:
        output = Path(out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(live_report.read_bytes())
