"""Byte-reproducible, fail-closed writers for the active reconstruction chain."""

from __future__ import annotations

import gzip
import importlib
import json
from pathlib import Path

import pytest


ACTIVE_WRITER_MODULES = (
    "scripts.cross_source_intake_v0_12",
    "scripts.tri_source_intake_v0_13",
    "scripts.convex_intake_v0_14",
    "scripts.analysis_intake_v0_15",
    "scripts.analysis_intake_v0_15_1",
    "scripts.analysis_intake_v0_15_2",
    "scripts.topology_intake_v0_16",
    "scripts.measure_intake_v0_17",
    "scripts.diffgeom_intake_v0_18",
)


@pytest.mark.parametrize("module_name", ACTIVE_WRITER_MODULES)
def test_active_graph_writer_is_byte_deterministic(
    module_name: str,
    tmp_path: Path,
) -> None:
    """Changing wall time or output filename must not alter graph bytes."""

    module = importlib.import_module(module_name)
    graph = {
        "nodes": [{"id": "n", "type": "OBJECT", "attributes": {"z": 2, "a": 1}}],
        "edges": [],
    }
    first = tmp_path / "first.json.gz"
    second = tmp_path / "second.json.gz"
    module.save_graph_gz(graph, first)
    module.save_graph_gz(graph, second)

    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes()[3] == 0  # no original filename header
    with gzip.open(first, "rt", encoding="utf-8") as handle:
        assert json.load(handle) == graph


def test_atomic_writer_rejects_nonfinite_json_without_replacing_destination(
    tmp_path: Path,
) -> None:
    """A serialization failure must preserve the last complete artifact."""

    from scripts.io_utils import atomic_write_deterministic_json_gzip

    destination = tmp_path / "graph.json.gz"
    destination.write_bytes(b"last-good-artifact")
    with pytest.raises(ValueError, match="Out of range float values"):
        atomic_write_deterministic_json_gzip(destination, {"bad": float("nan")})
    assert destination.read_bytes() == b"last-good-artifact"
    assert not list(tmp_path.glob(".graph.json.gz.*"))
