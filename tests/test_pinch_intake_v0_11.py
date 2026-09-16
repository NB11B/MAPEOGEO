from __future__ import annotations

import copy
import gzip
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from scripts.formal_bridge_v0_8 import proof_escape_hits
from scripts.pinch_contracts_v0_11 import run_contract
from tests.validate_pinch_intake_v0_11 import FORBIDDEN_PERSISTED_KEYS

ROOT = Path(__file__).resolve().parents[1]

FROZEN_TARGET_HASHES = {
    "srcdecl:proposition:3_14": "6e09e18756aefdaf8cdd2c03aca61548d1126fb3d30d70b49c58359f37c64b8e",
    "srcdecl:proposition:3_13": "0eef6ce3b699ddef7c209eb28b500b75aab07d9e540b7746b631f8db653addac",
    "srcdecl:theorem:27_10": "b99a4e9f7dcafc31774208c2d21485e59a23b3ae76f6fd3748babdefd41093e2",
    "srcdecl:proposition:4_4": "37e5dc6afdbd3d026c4f7ef71c3531fc74eaeb04bf21ed45c4a9add39fcb6ecf",
}


def make_mock_v09_graph() -> dict[str, Any]:
    """Build a complete, valid mock of the accepted v0.9 S5 graph."""
    nodes = [
        # Targets
        {
            "id": "srcdecl:proposition:3_14",
            "type": "DECLARATION",
            "attributes": {
                "independent_profile": {
                    "statement_sha256": FROZEN_TARGET_HASHES["srcdecl:proposition:3_14"],
                    "statement_chars": 150,
                    "eo_direct_families": ["basis", "coordinates"],
                    "geo_direct_families": [],
                    "direct_status": "EO_ONLY_DIRECT",
                }
            },
        },
        {
            "id": "srcdecl:proposition:3_13",
            "type": "DECLARATION",
            "attributes": {
                "independent_profile": {
                    "statement_sha256": FROZEN_TARGET_HASHES["srcdecl:proposition:3_13"],
                    "statement_chars": 200,
                    "eo_direct_families": ["linear_independence"],
                    "geo_direct_families": [],
                    "direct_status": "EO_ONLY_DIRECT",
                }
            },
        },
        {
            "id": "srcdecl:theorem:27_10",
            "type": "DECLARATION",
            "attributes": {
                "independent_profile": {
                    "statement_sha256": FROZEN_TARGET_HASHES["srcdecl:theorem:27_10"],
                    "statement_chars": 300,
                    "eo_direct_families": ["isometry", "translation"],
                    "geo_direct_families": ["spectral", "fixed_point"],
                    "direct_status": "DUAL_DIRECT",
                }
            },
        },
        {
            "id": "srcdecl:proposition:4_4",
            "type": "DECLARATION",
            "attributes": {
                "independent_profile": {
                    "statement_sha256": FROZEN_TARGET_HASHES["srcdecl:proposition:4_4"],
                    "statement_chars": 180,
                    "eo_direct_families": ["submodule", "direct_sum"],
                    "geo_direct_families": [],
                    "direct_status": "EO_ONLY_DIRECT",
                }
            },
        },
        # Cited dependencies
        {
            "id": "srcdecl:proposition:3_21",
            "type": "DECLARATION",
            "attributes": {"independent_profile": {"statement_sha256": "a" * 64, "direct_status": "EO_ONLY_DIRECT"}},
        },
        {
            "id": "srcdecl:proposition:2_2",
            "type": "DECLARATION",
            "attributes": {"independent_profile": {"statement_sha256": "b" * 64, "direct_status": "EO_ONLY_DIRECT"}},
        },
        {
            "id": "srcdecl:proposition:2_3",
            "type": "DECLARATION",
            "attributes": {"independent_profile": {"statement_sha256": "c" * 64, "direct_status": "EO_ONLY_DIRECT"}},
        },
        {
            "id": "srcdecl:theorem:6_16",
            "type": "DECLARATION",
            "attributes": {"independent_profile": {"statement_sha256": "d" * 64, "direct_status": "DUAL_DIRECT"}},
        },
        {
            "id": "srcdecl:proposition:4_3",
            "type": "DECLARATION",
            "attributes": {"independent_profile": {"statement_sha256": "e" * 64, "direct_status": "EO_ONLY_DIRECT"}},
        },
        {
            "id": "srcdecl:proposition:6_11",
            "type": "DECLARATION",
            "attributes": {"independent_profile": {"statement_sha256": "f" * 64, "direct_status": "EO_ONLY_DIRECT"}},
        },
        {
            "id": "srcdecl:proposition:3_15",
            "type": "DECLARATION",
            "attributes": {"independent_profile": {"statement_sha256": "0" * 64, "direct_status": "EO_ONLY_DIRECT"}},
        },
        {
            "id": "srcdecl:proposition:3_18",
            "type": "DECLARATION",
            "attributes": {"independent_profile": {"statement_sha256": "1" * 64, "direct_status": "EO_ONLY_DIRECT"}},
        },
        # v0.9 S5 Nodes & Wounds
        {
            "id": "formal:lean:v09:theorem_6_16",
            "type": "REPRESENTATION",
            "view": "FORMAL",
            "attributes": {"verifier": "Lean 4", "stage": "S5"},
        },
        {
            "id": "cert:v09:lean:theorem_6_16",
            "type": "CERTIFICATE",
            "attributes": {"status": "PASS", "certificate_class": "KERNEL_VERIFIED"},
        },
        {
            "id": "proofpath:v09:theorem:6_16",
            "type": "PROOF_PATH",
            "attributes": {"status": "KERNEL_ACCEPTED_WITH_REPAIRED_WOUND"},
        },
        {
            "id": "wound:v09:proposition:6_11:proposition:3_18",
            "type": "WOUND",
            "attributes": {"status": "REPAIRED_VISIBLE", "source": "srcdecl:proposition:6_11"},
        },
    ]

    edges = [
        # 3.14 -> 3.13, 4.4
        {"id": "e:dep:3_14:3_13", "source": "srcdecl:proposition:3_14", "target": "srcdecl:proposition:3_13", "type": "DEPENDS_ON"},
        {"id": "e:dep:3_14:4_4", "source": "srcdecl:proposition:3_14", "target": "srcdecl:proposition:4_4", "type": "DEPENDS_ON"},
        # 3.13 -> 3.21, 2.2, 2.3, 4.4
        {"id": "e:dep:3_13:3_21", "source": "srcdecl:proposition:3_13", "target": "srcdecl:proposition:3_21", "type": "DEPENDS_ON"},
        {"id": "e:dep:3_13:2_2", "source": "srcdecl:proposition:3_13", "target": "srcdecl:proposition:2_2", "type": "DEPENDS_ON"},
        {"id": "e:dep:3_13:2_3", "source": "srcdecl:proposition:3_13", "target": "srcdecl:proposition:2_3", "type": "DEPENDS_ON"},
        {"id": "e:dep:3_13:4_4", "source": "srcdecl:proposition:3_13", "target": "srcdecl:proposition:4_4", "type": "DEPENDS_ON"},
        # 27.10 -> 6.16
        {"id": "e:dep:27_10:6_16", "source": "srcdecl:theorem:27_10", "target": "srcdecl:theorem:6_16", "type": "DEPENDS_ON"},
        # 4.4 -> 4.3
        {"id": "e:dep:4_4:4_3", "source": "srcdecl:proposition:4_4", "target": "srcdecl:proposition:4_3", "type": "DEPENDS_ON"},
        # Repaired reference edges
        {
            "id": "e:v09:source-ref-correction:proposition:6_11:proposition:3_15",
            "source": "srcdecl:proposition:6_11",
            "target": "srcdecl:proposition:3_15",
            "type": "DEPENDS_ON",
            "attributes": {"v0_9_path_status": "CORRECTED_SOURCE_REFERENCE"},
        },
        {
            "id": "e:v09:source-ref-legacy:proposition:6_11:proposition:3_18",
            "source": "srcdecl:proposition:6_11",
            "target": "srcdecl:proposition:3_18",
            "type": "DEPENDS_ON",
            "attributes": {"v0_9_path_status": "REJECTED_REFERENCE_MISMATCH"},
        },
    ]

    return {"nodes": nodes, "edges": edges}


def test_v011_lean_file_has_no_escape_hatches():
    text = Path("MAPEOGEOFormal/PinchV011.lean").read_text(encoding="utf-8")
    assert proof_escape_hits(text) == []


def test_all_frozen_scopes_have_fixed_decl_names():
    cfg = json.loads(Path("formal/pinch_bindings_v0_11.json").read_text(encoding="utf-8"))
    text = Path("MAPEOGEOFormal/PinchV011.lean").read_text(encoding="utf-8")

    expected = [
        x["formal_decl"].split(".")[-1]
        for x in cfg["targets"]
        if x["scope_status"] == "FROZEN"
    ]

    assert len(expected) == 4
    assert all(name in text for name in expected)


def test_untested_is_not_pass():
    result = run_contract({
        "source_id": "srcdecl:proposition:3_14",
        "s3_test_state": "UNTESTED",
        "s3_contract_id": None,
        "s3_scope": None,
    })

    assert result.verdict == "UNTESTED"
    assert result.test_state == "UNTESTED"
    assert result.refused


def test_unknown_contract_is_invalid():
    result = run_contract({
        "source_id": "synthetic:test",
        "s3_test_state": "EXECUTABLE_CONTRACT",
        "s3_contract_id": "UNKNOWN_CONTRACT",
        "s3_scope": "SYNTHETIC",
    })

    assert result.verdict == "INVALID"
    assert result.refused


def test_pct_contract_is_not_applicable():
    result = run_contract({
        "source_id": "synthetic:test",
        "s3_test_state": "PCT_CONTRACT",
        "s3_contract_id": "pct_mock",
        "s3_scope": "SYNTHETIC",
    })

    assert result.verdict == "NOT_APPLICABLE"
    assert result.applicability == "NOT_APPLICABLE"


def test_all_v011_target_contracts_execute_cleanly():
    cfg = json.loads(Path("formal/pinch_bindings_v0_11.json").read_text(encoding="utf-8"))

    for target in cfg["targets"]:
        res = run_contract(target)
        if target["s3_test_state"] == "UNTESTED":
            assert res.verdict == "UNTESTED"
        elif target["s3_test_state"] == "EXECUTABLE_CONTRACT":
            assert res.verdict == "PASS"
            assert res.measured.get("all_checks_passed") is True


def test_negative_escape_hatch_detection():
    assert proof_escape_hits("lemma foo : 1 = 1 := by sorry") == ["sorry"]
    assert proof_escape_hits("lemma bar : 1 = 1 := by admit") == ["admit"]
    assert proof_escape_hits("axiom bad_axiom : False") == ["axiom_declaration"]
    assert proof_escape_hits("unsafe def bad_fn : Nat := 0") == ["unsafe_declaration"]
    assert proof_escape_hits("theorem good : 1 = 1 := rfl") == []


def test_negative_forbidden_prose_keys_detected():
    test_node_attrs = {
        "statement_text": "Let V be a finite dimensional vector space...",
        "formal_scope": "Valid scope",
    }
    assert bool(FORBIDDEN_PERSISTED_KEYS.intersection(test_node_attrs)) is True


# ==============================================================================
# Fail-Closed Negative Mutation Tests for Intake Harness (Points 2, 3, 4, 6, 7, 11)
# ==============================================================================

def run_intake_test_helper(graph_dict: dict, tmp_path: Path, extra_args: list[str] = None) -> tuple[int, dict]:
    """Helper to run scripts/pinch_intake_v0_11.py against a graph in tmp_path."""
    graph_path = tmp_path / "test_graph.json"
    graph_path.write_text(json.dumps(graph_dict), encoding="utf-8")
    out_dir = tmp_path / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    mock_lean = tmp_path / "MockPinch.lean"
    mock_lean.write_text(
        "theorem proposition_3_14_v011 : 1 = 1 := rfl\n"
        "theorem proposition_3_13_v011 : 1 = 1 := rfl\n"
        "theorem theorem_27_10_v011 : 1 = 1 := rfl\n"
        "theorem proposition_4_4_v011 : 1 = 1 := rfl\n",
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "pinch_intake_v0_11.py"),
        "--base-graph", str(graph_path),
        "--out-dir", str(out_dir),
    ]
    if extra_args:
        if not any(arg == "--lean-file" for arg in extra_args):
            cmd.extend(["--lean-file", str(mock_lean)])
        cmd.extend(extra_args)
    else:
        cmd.extend([
            "--lean-file", str(mock_lean),
            "--independent-checker-status", "PASS",
            "--allow-unverified-checker-pass",
        ])

    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    results_file = out_dir / "pinch_v0_11_results.json"
    results = json.loads(results_file.read_text(encoding="utf-8")) if results_file.is_file() else {}
    return proc.returncode, results


def test_negative_missing_source_node_fails(tmp_path: Path):
    """Proves that a missing source node causes the gate to fail closed (never synthesized)."""
    graph = make_mock_v09_graph()
    # Remove proposition 3.14
    graph["nodes"] = [n for n in graph["nodes"] if n["id"] != "srcdecl:proposition:3_14"]

    rc, res = run_intake_test_helper(graph, tmp_path)
    assert rc != 0
    assert res.get("status") == "FAIL"
    assert res.get("gates", {}).get("target_nodes_present") is False


def test_negative_missing_source_hash_fails(tmp_path: Path):
    """Proves that a source node missing statement_sha256 fails closed."""
    graph = make_mock_v09_graph()
    for n in graph["nodes"]:
        if n["id"] == "srcdecl:proposition:3_14":
            del n["attributes"]["independent_profile"]["statement_sha256"]

    rc, res = run_intake_test_helper(graph, tmp_path)
    assert rc != 0
    assert res.get("status") == "FAIL"
    assert res.get("gates", {}).get("statement_hashes_matched") is False


def test_negative_statement_hash_mismatch_fails(tmp_path: Path):
    """Proves that a statement hash mismatch fails closed."""
    graph = make_mock_v09_graph()
    for n in graph["nodes"]:
        if n["id"] == "srcdecl:proposition:3_14":
            n["attributes"]["independent_profile"]["statement_sha256"] = "0" * 64

    rc, res = run_intake_test_helper(graph, tmp_path)
    assert rc != 0
    assert res.get("status") == "FAIL"
    assert res.get("gates", {}).get("statement_hashes_matched") is False


def test_negative_direct_status_drift_fails(tmp_path: Path):
    """Proves that historical direct-status drift (e.g. EO_ONLY inflated to DUAL_DIRECT) fails closed."""
    graph = make_mock_v09_graph()
    for n in graph["nodes"]:
        if n["id"] == "srcdecl:proposition:3_14":
            n["attributes"]["independent_profile"]["direct_status"] = "DUAL_DIRECT"  # Drifts from EO_ONLY_DIRECT

    rc, res = run_intake_test_helper(graph, tmp_path)
    assert rc != 0
    assert res.get("status") == "FAIL"
    assert res.get("gates", {}).get("historical_direct_views_matched") is False


def test_negative_absent_expected_dependency_fails(tmp_path: Path):
    """Proves that an absent explicit dependency edge fails closed (never manufactured)."""
    graph = make_mock_v09_graph()
    # Remove edge: proposition:3_14 -> proposition:3_13
    graph["edges"] = [
        e for e in graph["edges"]
        if not (e.get("source") == "srcdecl:proposition:3_14" and e.get("target") == "srcdecl:proposition:3_13")
    ]

    rc, res = run_intake_test_helper(graph, tmp_path)
    assert rc != 0
    assert res.get("status") == "FAIL"
    assert res.get("gates", {}).get("explicit_dependencies_present") is False


def test_negative_refused_scope_cannot_receive_kernel_verified(tmp_path: Path):
    """Proves that a REFUSED_SCOPE_MISMATCH target cannot receive KERNEL_VERIFIED or formal nodes."""
    graph = make_mock_v09_graph()
    bindings = json.loads((ROOT / "formal" / "pinch_bindings_v0_11.json").read_text(encoding="utf-8"))
    # Set proposition 3.14 to REFUSED_SCOPE_MISMATCH
    for t in bindings["targets"]:
        if t["source_id"] == "srcdecl:proposition:3_14":
            t["scope_status"] = "REFUSED_SCOPE_MISMATCH"

    bindings_file = tmp_path / "test_bindings.json"
    bindings_file.write_text(json.dumps(bindings), encoding="utf-8")

    graph_path = tmp_path / "test_graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    out_dir = tmp_path / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    mock_lean = tmp_path / "MockPinch.lean"
    mock_lean.write_text(
        "theorem proposition_3_14_v011 : 1 = 1 := rfl\n"
        "theorem proposition_3_13_v011 : 1 = 1 := rfl\n"
        "theorem theorem_27_10_v011 : 1 = 1 := rfl\n"
        "theorem proposition_4_4_v011 : 1 = 1 := rfl\n",
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "pinch_intake_v0_11.py"),
        "--base-graph", str(graph_path),
        "--bindings", str(bindings_file),
        "--lean-file", str(mock_lean),
        "--out-dir", str(out_dir),
        "--independent-checker-status", "PASS",
        "--allow-unverified-checker-pass",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    assert proc.returncode == 0

    certs = json.loads((out_dir / "pinch_v0_11_certificates.json").read_text(encoding="utf-8"))
    cert_ids = {c["source_id"] for c in certs}
    assert "srcdecl:proposition:3_14" not in cert_ids
    assert len(certs) == 3

    with gzip.open(out_dir / "mapeogeo_v0_11_graph.json.gz", "rt", encoding="utf-8") as f:
        out_graph = json.load(f)
    out_node_ids = {n["id"] for n in out_graph["nodes"]}
    assert "formal:lean:v011:proposition_3_14" not in out_node_ids
    assert "cert:v011:lean:proposition_3_14" not in out_node_ids


def test_negative_lean_success_alone_creates_no_equivalent_to(tmp_path: Path):
    """Proves that Lean kernel verification alone creates NO automatic EQUIVALENT_TO edges."""
    graph = make_mock_v09_graph()
    rc, res = run_intake_test_helper(graph, tmp_path)
    assert rc == 0
    assert res.get("status") == "PASS"

    with gzip.open(tmp_path / "artifacts" / "mapeogeo_v0_11_graph.json.gz", "rt", encoding="utf-8") as f:
        out_graph = json.load(f)

    formal_equivs = [
        e for e in out_graph["edges"]
        if e.get("type") == "EQUIVALENT_TO" and "formal:lean:v011" in e.get("source", "")
    ]
    assert len(formal_equivs) == 0


def test_negative_caller_claiming_checker_pass_without_evidence_fails(tmp_path: Path):
    """Proves that claiming independent checker PASS without an evidence file fails closed."""
    graph = make_mock_v09_graph()
    graph_path = tmp_path / "test_graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    out_dir = tmp_path / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    mock_lean = tmp_path / "MockPinch.lean"
    mock_lean.write_text(
        "theorem proposition_3_14_v011 : 1 = 1 := rfl\n"
        "theorem proposition_3_13_v011 : 1 = 1 := rfl\n"
        "theorem theorem_27_10_v011 : 1 = 1 := rfl\n"
        "theorem proposition_4_4_v011 : 1 = 1 := rfl\n",
        encoding="utf-8",
    )

    # Calling with --independent-checker-status PASS without --checker-evidence-file
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "pinch_intake_v0_11.py"),
        "--base-graph", str(graph_path),
        "--lean-file", str(mock_lean),
        "--out-dir", str(out_dir),
        "--independent-checker-status", "PASS",
        # NOTE: omitted --allow-unverified-checker-pass and --checker-evidence-file
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    assert proc.returncode != 0
    results_file = out_dir / "pinch_v0_11_results.json"
    res = json.loads(results_file.read_text(encoding="utf-8")) if results_file.is_file() else {}
    assert res.get("gates", {}).get("independent_checker_pass") is False


def test_negative_pre_v09_base_graph_fails(tmp_path: Path):
    """Proves that running against a pre-v0.9 base graph (e.g. v0.3 graph) fails closed."""
    # gallier_quaintance_graph_v0_3.json.gz is a pre-v0.9 graph without S5 proof path/wounds
    v03_graph = ROOT / "data" / "gallier_quaintance_graph_v0_3.json.gz"
    out_dir = tmp_path / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "pinch_intake_v0_11.py"),
        "--base-graph", str(v03_graph),
        "--out-dir", str(out_dir),
        "--independent-checker-status", "PASS",
        "--allow-unverified-checker-pass",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    assert proc.returncode != 0
    results_file = out_dir / "pinch_v0_11_results.json"
    res = json.loads(results_file.read_text(encoding="utf-8")) if results_file.is_file() else {}
    assert res.get("gates", {}).get("base_graph_is_v09_accepted") is False


def test_v09_wounds_survive_regression(tmp_path: Path):
    """Regression test: proves all v0.9 WOUND nodes and rejected/corrected reference edges survive in v0.11."""
    graph = make_mock_v09_graph()
    rc, res = run_intake_test_helper(graph, tmp_path)
    assert rc == 0
    assert res.get("status") == "PASS"

    with gzip.open(tmp_path / "artifacts" / "mapeogeo_v0_11_graph.json.gz", "rt", encoding="utf-8") as f:
        out_graph = json.load(f)

    out_node_ids = {n["id"] for n in out_graph["nodes"]}
    out_edges = out_graph["edges"]

    # Check wound node preserved
    assert "wound:v09:proposition:6_11:proposition:3_18" in out_node_ids
    assert "proofpath:v09:theorem:6_16" in out_node_ids

    # Check rejected/corrected wound edges preserved
    rejected_edges = [
        e for e in out_edges
        if e.get("attributes", {}).get("v0_9_path_status") == "REJECTED_REFERENCE_MISMATCH"
    ]
    corrected_edges = [
        e for e in out_edges
        if e.get("attributes", {}).get("v0_9_path_status") == "CORRECTED_SOURCE_REFERENCE"
    ]
    assert len(rejected_edges) >= 1
    assert len(corrected_edges) >= 1

    # Check pinch_v0_11_wounds.json
    wounds_file = tmp_path / "artifacts" / "pinch_v0_11_wounds.json"
    assert wounds_file.is_file()
    wounds_data = json.loads(wounds_file.read_text(encoding="utf-8"))
    assert len(wounds_data) >= 2
