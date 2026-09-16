from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.source_admission_v0_21 import admit_sources

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "formal" / "source_registry_v0_21.json"
EXPECTED_SOURCES = {
    "OPEN_LOGIC_PROJECT",
    "LEVIN_DISCRETE",
    "JUDSON_AATA",
    "LEBL_BASIC_ANALYSIS",
    "LEBL_DIFFYQS",
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
def test_real_pinned_sources_admit_nonzero_zero_prose_declarations(tmp_path: Path):
    result = admit_sources(REGISTRY, tmp_path / "sources")
    counts = result.counts_by_source()
    assert set(counts) == EXPECTED_SOURCES
    assert all(counts[source_id] > 0 for source_id in EXPECTED_SOURCES)
    assert sum(counts.values()) == len(result.metadata)

    for row in result.metadata:
        assert FORBIDDEN_KEYS.isdisjoint(row)
        assert row["canonical_status"] == "UNRESOLVED"
        assert row["formal_status"] == "UNFORMALIZED"
        assert row["executable_status"] == "UNTESTED"
        assert len(row["statement_sha256"]) == 64
        assert len(row["revision"]) == 40

    out = os.environ.get("V0_21_LIVE_REPORT")
    if out:
        output = Path(out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result.report(), sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
