import json
from pathlib import Path

from scripts.audit_pinch_source_v0_11 import audit_targets


FROZEN = {
    "srcdecl:proposition:3_14":
        "6e09e18756aefdaf8cdd2c03aca61548d1126fb3d30d70b49c58359f37c64b8e",
    "srcdecl:proposition:3_13":
        "0eef6ce3b699ddef7c209eb28b500b75aab07d9e540b7746b631f8db653addac",
    "srcdecl:theorem:27_10":
        "d205d7c5313b841e6afafc9d619fa059dfe50a2f6c11a48ca2cff466cc84d4fa",
    "srcdecl:proposition:4_4":
        "37e5dc6afdbd3d026c4f7ef71c3531fc74eaeb04bf21ed45c4a9add39fcb6ecf",
}


def make_mock_graph():
    nodes = [
        {
            "id": "srcdecl:proposition:3_14",
            "attributes": {
                "independent_profile": {
                    "statement_sha256": FROZEN["srcdecl:proposition:3_14"],
                    "direct_status": "EO_ONLY_DIRECT",
                }
            },
        },
        {
            "id": "srcdecl:proposition:3_13",
            "attributes": {
                "independent_profile": {
                    "statement_sha256": FROZEN["srcdecl:proposition:3_13"],
                    "direct_status": "EO_ONLY_DIRECT",
                }
            },
        },
        {
            "id": "srcdecl:theorem:27_10",
            "attributes": {
                "independent_profile": {
                    "statement_sha256": FROZEN["srcdecl:theorem:27_10"],
                    "direct_status": "DUAL_DIRECT",
                }
            },
        },
        {
            "id": "srcdecl:proposition:4_4",
            "attributes": {
                "independent_profile": {
                    "statement_sha256": FROZEN["srcdecl:proposition:4_4"],
                    "direct_status": "EO_ONLY_DIRECT",
                }
            },
        },
    ]
    edges = [
        # 3.14 -> 3.13, 4.4
        {"source": "srcdecl:proposition:3_14", "target": "srcdecl:proposition:3_13", "type": "DEPENDS_ON"},
        {"source": "srcdecl:proposition:3_14", "target": "srcdecl:proposition:4_4", "type": "DEPENDS_ON"},
        # 3.13 -> 3.21, 2.2, 2.3, 4.4
        {"source": "srcdecl:proposition:3_13", "target": "srcdecl:proposition:3_21", "type": "DEPENDS_ON"},
        {"source": "srcdecl:proposition:3_13", "target": "srcdecl:proposition:2_2", "type": "DEPENDS_ON"},
        {"source": "srcdecl:proposition:3_13", "target": "srcdecl:proposition:2_3", "type": "DEPENDS_ON"},
        {"source": "srcdecl:proposition:3_13", "target": "srcdecl:proposition:4_4", "type": "DEPENDS_ON"},
        # 27.10 -> 6.16
        {"source": "srcdecl:theorem:27_10", "target": "srcdecl:theorem:6_16", "type": "DEPENDS_ON"},
        # 4.4 -> 4.3
        {"source": "srcdecl:proposition:4_4", "target": "srcdecl:proposition:4_3", "type": "DEPENDS_ON"},
    ]
    return {"nodes": nodes, "edges": edges}


def test_v011_bindings_freeze_exact_quartet():
    cfg = json.loads(
        Path("formal/pinch_bindings_v0_11.json")
        .read_text(encoding="utf-8")
    )

    got = {
        x["source_id"]: x["statement_sha256"]
        for x in cfg["targets"]
    }

    assert got == FROZEN
    assert len(cfg["targets"]) == 4

    for item in cfg["targets"]:
        assert item["s3_test_state"] in {
            "EXECUTABLE_CONTRACT",
            "PCT_CONTRACT",
            "UNTESTED",
        }
        assert item["scope_status"] in {
            "FROZEN",
            "REFUSED_SCOPE_MISMATCH",
        }


def test_audit_targets_pass():
    cfg = json.loads(Path("formal/pinch_bindings_v0_11.json").read_text(encoding="utf-8"))
    graph = make_mock_graph()
    res = audit_targets(graph, cfg)
    assert res["audit_passed"] is True
    assert res["all_hashes_match"] is True
    assert res["all_direct_states_match"] is True
    assert res["all_explicit_dependencies_present"] is True


def test_audit_targets_fails_mutated_hash():
    cfg = json.loads(Path("formal/pinch_bindings_v0_11.json").read_text(encoding="utf-8"))
    graph = make_mock_graph()
    # mutate one hash
    graph["nodes"][0]["attributes"]["independent_profile"]["statement_sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    res = audit_targets(graph, cfg)
    assert res["audit_passed"] is False
    assert res["all_hashes_match"] is False


def test_audit_targets_fails_changed_direct_state():
    cfg = json.loads(Path("formal/pinch_bindings_v0_11.json").read_text(encoding="utf-8"))
    graph = make_mock_graph()
    # mutate direct state
    graph["nodes"][0]["attributes"]["independent_profile"]["direct_status"] = "DUAL_DIRECT"
    res = audit_targets(graph, cfg)
    assert res["audit_passed"] is False
    assert res["all_direct_states_match"] is False


def test_audit_targets_fails_missing_dependency():
    cfg = json.loads(Path("formal/pinch_bindings_v0_11.json").read_text(encoding="utf-8"))
    graph = make_mock_graph()
    # remove one edge
    graph["edges"] = [e for e in graph["edges"] if not (e["source"] == "srcdecl:proposition:3_14" and e["target"] == "srcdecl:proposition:4_4")]
    res = audit_targets(graph, cfg)
    assert res["audit_passed"] is False
    assert res["all_explicit_dependencies_present"] is False
