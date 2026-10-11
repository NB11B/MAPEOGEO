from pathlib import Path
import importlib.util

VALIDATOR = Path(__file__).resolve().parents[1] / "tools" / "validate_graph.py"
spec = importlib.util.spec_from_file_location("sovctx_validator", VALIDATOR)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_seed_graph_validates() -> None:
    assert module.main() == 0


def test_forbidden_semantic_promotions_are_blocked() -> None:
    assert "SAME_OPERATOR" in module.FORBIDDEN_EDGE_TYPES
    assert "EQUIVALENT_TO" in module.FORBIDDEN_EDGE_TYPES


def test_comparison_isolation_is_defined() -> None:
    assert "PARALLEL_TO" in module.COMPARISON_EDGES
    assert "WEST" in module.ALLOWED_NAMESPACES


def test_verified_primary_claim_requires_fragment() -> None:
    nodes = {
        "PUB:X": {"id": "PUB:X", "type": "PUBLICATION", "namespace": "SOV", "label": "X"}
    }
    record = {
        "id": "CLAIM:X",
        "type": "CLAIM",
        "namespace": "SOV",
        "label": "X claim",
        "knowledge_status": "D",
        "verification_status": "verified_primary",
        "source_ids": ["PUB:X"],
    }
    try:
        module.validate_claim(Path("test"), record, nodes)
    except module.ValidationError:
        return
    raise AssertionError("verified_primary claim without fragment should fail")


def test_fragment_source_must_match_claim_source() -> None:
    nodes = {
        "PUB:X": {"id": "PUB:X", "type": "PUBLICATION", "namespace": "SOV", "label": "X"},
        "PUB:Y": {"id": "PUB:Y", "type": "PUBLICATION", "namespace": "SOV", "label": "Y"},
        "FRAG:Y": {
            "id": "FRAG:Y",
            "type": "SOURCE_FRAGMENT",
            "namespace": "SOV",
            "label": "Y fragment",
            "source_id": "PUB:Y",
            "verification_status": "verified_primary",
        },
    }
    record = {
        "id": "CLAIM:X",
        "type": "CLAIM",
        "namespace": "SOV",
        "label": "X claim",
        "knowledge_status": "D",
        "verification_status": "verified_primary",
        "source_ids": ["PUB:X"],
        "source_fragment_ids": ["FRAG:Y"],
    }
    try:
        module.validate_claim(Path("test"), record, nodes)
    except module.ValidationError:
        return
    raise AssertionError("claim should not accept a fragment from an uncited source")
