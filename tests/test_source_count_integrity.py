"""Active source counts must be derived from the sealed graph, not headlines."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from scripts.complex_analysis_intake_v0_19 import authoritative_source_registry
from scripts.import_analysis_v0_15 import generate_additional_analysis_declarations


ROOT = Path(__file__).resolve().parents[1]
SEALED = ROOT / "data" / "mapeogeo_v0_11_graph.json.gz"
AMENDMENTS = ROOT / "formal" / "mathematical_integrity_amendments_v0_20.json"


def test_sealed_v011_has_1356_statement_declarations_and_bound_count_amendment() -> None:
    sealed_digest = hashlib.sha256(SEALED.read_bytes()).hexdigest()
    assert sealed_digest == "409a648d8563bc4a027dc3dc29fc53722d11bc489462a0f3d1f71bd4f272544d"
    with gzip.open(SEALED, "rt", encoding="utf-8") as handle:
        graph = json.load(handle)
    assert sum(node.get("type") == "STATEMENT" for node in graph["nodes"]) == 1356

    data = json.loads(AMENDMENTS.read_text(encoding="utf-8"))
    amendment = next(
        item
        for item in data["amendments"]
        if item["amendment_id"] == "amendment:v0.20:source-count:gallier-v0.11"
    )
    assert amendment["historical_count"] == 1360
    assert amendment["corrected_count"] == 1356
    assert amendment["sealed_graph_sha256"] == sealed_digest


def test_active_downstream_source_totals_use_sealed_count() -> None:
    assert 1356 + 235 + 81 + 84 == 1756
    assert 1756 + 64 == 1820
    assert 1820 + 67 == 1887
    assert 1887 + 72 == 1959
    assert 1959 + 176 == 2135


def test_only_the_four_synthetic_gallier_chapter_records_are_count_excluded() -> None:
    registry = authoritative_source_registry()
    supplementary = generate_additional_analysis_declarations()
    excluded = {
        declaration.node_id
        for declaration in supplementary
        if registry[declaration.node_id]["count_status"]
        == "EXCLUDED_HISTORICAL_COUNT_ARTIFACT"
    }
    assert excluded == {
        "srcdecl:gallier:chapter:37",
        "srcdecl:gallier:chapter:39",
        "srcdecl:gallier:chapter:40",
        "srcdecl:gallier:chapter:41",
    }
    cvx_appendix = next(
        declaration for declaration in supplementary if declaration.node_id.endswith("A_4")
    )
    assert registry[cvx_appendix.node_id]["count_status"] == "ADMISSIBLE_SOURCE_DECLARATION"
