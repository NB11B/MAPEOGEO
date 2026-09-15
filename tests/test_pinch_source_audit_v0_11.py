import json
from pathlib import Path

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
