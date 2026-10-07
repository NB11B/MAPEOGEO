"""Unit tests for deterministic JSON and SHA-256 manifest utilities."""

from __future__ import annotations

import json
from pathlib import Path

from tools.deterministic_json import read_json, serialize_deterministic, write_deterministic_json
from tools.manifest_utils import compute_directory_tree_sha256, compute_file_sha256


def test_deterministic_json_serialization() -> None:
    data1 = {"b": 2, "a": 1, "nested": {"z": 26, "y": 25}}
    data2 = {"nested": {"y": 25, "z": 26}, "a": 1, "b": 2}

    s1 = serialize_deterministic(data1)
    s2 = serialize_deterministic(data2)

    assert s1 == s2
    assert s1.endswith("\n")
    loaded = json.loads(s1)
    assert loaded == data1


def test_deterministic_json_roundtrip(tmp_path: Path) -> None:
    target = tmp_path / "test.json"
    obj = {"gamma": [3, 2, 1], "alpha": "test"}
    write_deterministic_json(target, obj)
    assert target.is_file()

    read_back = read_json(target)
    assert read_back == obj


def test_compute_file_sha256(tmp_path: Path) -> None:
    f = tmp_path / "hello.txt"
    f.write_text("Hello World\n", encoding="utf-8")
    digest = compute_file_sha256(f)
    assert len(digest) == 64
    assert isinstance(digest, str)


def test_compute_directory_tree_sha256(tmp_path: Path) -> None:
    dir1 = tmp_path / "d1"
    dir1.mkdir()
    (dir1 / "b.py").write_text("print(2)\n", encoding="utf-8")
    (dir1 / "a.py").write_text("print(1)\n", encoding="utf-8")

    h1 = compute_directory_tree_sha256(dir1)

    dir2 = tmp_path / "d2"
    dir2.mkdir()
    (dir2 / "a.py").write_text("print(1)\n", encoding="utf-8")
    (dir2 / "b.py").write_text("print(2)\n", encoding="utf-8")

    h2 = compute_directory_tree_sha256(dir2)

    assert h1 == h2
