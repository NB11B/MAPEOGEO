"""Unit tests for deterministic artifact serialization, sealing, and graph emission."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from mapeogeo.pct.artifacts import (
    FORBIDDEN_GRAPH_KEYS,
    build_graph_fragment,
    canonical_json,
    write_run_artifacts,
)
from mapeogeo.pct.experiment import run_pct_experiment


REQUIRED_FILES = [
    "manifest.json",
    "hashes.json",
    "objects/fixtures.json",
    "probes/responses.json",
    "complexes/chain_data.json",
    "maps/chain_maps.json",
    "homology/betti.json",
    "persistence/pairs.json",
    "geometry/metrics.json",
    "event_ledger/events.json",
    "reconstruction/results.json",
    "negative_controls/results.json",
    "residuals/results.json",
    "validity.json",
    "scientific_result.json",
    "pct_graph_fragment.json",
    "summary.md",
]


def test_canonical_json_is_key_order_independent():
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_artifacts_generation_and_reproducibility(tmp_path: Path):
    manifest_path = Path("evidence/v0_10_pct_preregistration.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    result1 = run_pct_experiment(manifest, repository_commit="TEST_COMMIT")
    dir1 = tmp_path / "run1"
    hashes1 = write_run_artifacts(result1, dir1, manifest)

    # Check that all required files exist
    for f_rel in REQUIRED_FILES:
        p = dir1 / f_rel
        assert p.is_file(), f"Missing required artifact: {f_rel}"

    # Rerun in a second directory and verify exact byte/hash matching
    result2 = run_pct_experiment(manifest, repository_commit="TEST_COMMIT")
    dir2 = tmp_path / "run2"
    hashes2 = write_run_artifacts(result2, dir2, manifest)

    assert hashes1 == hashes2
    for f_rel in REQUIRED_FILES:
        bytes1 = (dir1 / f_rel).read_bytes()
        bytes2 = (dir2 / f_rel).read_bytes()
        assert bytes1 == bytes2, f"Artifact {f_rel} differs across reruns!"


def test_graph_fragment_integrity():
    manifest_path = Path("evidence/v0_10_pct_preregistration.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result = run_pct_experiment(manifest, repository_commit="TEST_COMMIT")
    fragment = build_graph_fragment(result)

    node_ids = {n["id"] for n in fragment["nodes"]}
    assert len(node_ids) == len(fragment["nodes"]), "Duplicate node IDs in graph fragment"

    edge_ids = {e["id"] for e in fragment["edges"]}
    assert len(edge_ids) == len(fragment["edges"]), "Duplicate edge IDs in graph fragment"

    # All edge endpoints exist
    for e in fragment["edges"]:
        assert e["source"] in node_ids, f"Edge source {e['source']} not found"
        assert e["target"] in node_ids, f"Edge target {e['target']} not found"

    # Verify no forbidden keys
    for n in fragment["nodes"]:
        for k in FORBIDDEN_GRAPH_KEYS:
            assert k not in n
            assert k not in n.get("attributes", {})

    # Certificate class must be EXECUTABLE_EVIDENCE_PCT and never KERNEL_VERIFIED
    cert_nodes = [n for n in fragment["nodes"] if n["type"] == "CERTIFICATE"]
    assert len(cert_nodes) == 1
    cert = cert_nodes[0]
    assert cert["certificate_class"] == "EXECUTABLE_EVIDENCE_PCT"
    assert "KERNEL_VERIFIED" not in str(cert)
