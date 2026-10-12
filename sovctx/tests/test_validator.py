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


def test_support_edge_requires_fragment_to_claim() -> None:
    nodes = {
        "PUB:X": {"id": "PUB:X", "type": "PUBLICATION", "namespace": "SOV", "label": "X"},
        "CLAIM:X": {"id": "CLAIM:X", "type": "CLAIM", "namespace": "SOV", "label": "C", "source_fragment_ids": []},
    }
    edge = {
        "id": "EDGE:X",
        "type": "EDGE",
        "namespace": "SOV",
        "label": "invalid support",
        "edge_type": "SUPPORTS",
        "relation_realm": "HISTORICAL",
        "source": "PUB:X",
        "target": "CLAIM:X",
    }
    try:
        module.validate_edge(Path("test"), edge, nodes)
    except module.ValidationError:
        return
    raise AssertionError("SUPPORTS should require SOURCE_FRAGMENT -> CLAIM")


def test_extracted_from_must_match_fragment_source() -> None:
    nodes = {
        "PUB:X": {"id": "PUB:X", "type": "PUBLICATION", "namespace": "SOV", "label": "X"},
        "PUB:Y": {"id": "PUB:Y", "type": "PUBLICATION", "namespace": "SOV", "label": "Y"},
        "FRAG:X": {
            "id": "FRAG:X", "type": "SOURCE_FRAGMENT", "namespace": "SOV",
            "label": "fragment", "source_id": "PUB:X"
        },
    }
    edge = {
        "id": "EDGE:X",
        "type": "EDGE",
        "namespace": "SOV",
        "label": "invalid extraction",
        "edge_type": "EXTRACTED_FROM",
        "relation_realm": "HISTORICAL",
        "source": "FRAG:X",
        "target": "PUB:Y",
    }
    try:
        module.validate_edge(Path("test"), edge, nodes)
    except module.ValidationError:
        return
    raise AssertionError("EXTRACTED_FROM target must match fragment source_id")


def test_edge_requires_declared_relation_realm() -> None:
    nodes = {
        "EQ:A": {"id": "EQ:A", "type": "EQUATION", "namespace": "SOV", "label": "A"},
        "EQ:B": {"id": "EQ:B", "type": "EQUATION", "namespace": "SOV", "label": "B"},
    }
    edge = {
        "id": "EDGE:NO_REALM",
        "type": "EDGE",
        "namespace": "SOV",
        "label": "missing realm",
        "edge_type": "REDUCES_TO",
        "source": "EQ:A",
        "target": "EQ:B",
    }
    try:
        module.validate_edge(Path("test"), edge, nodes)
    except module.ValidationError as exc:
        assert "missing required relation_realm" in str(exc)
        return
    raise AssertionError("Edge without relation_realm must fail validation")


def test_edge_relation_realm_must_match_edge_type() -> None:
    nodes = {
        "EQ:A": {"id": "EQ:A", "type": "EQUATION", "namespace": "SOV", "label": "A"},
        "EQ:B": {"id": "EQ:B", "type": "EQUATION", "namespace": "SOV", "label": "B"},
        "PUB:P": {"id": "PUB:P", "type": "PUBLICATION", "namespace": "SOV", "label": "P"},
        "PERSON:X": {"id": "PERSON:X", "type": "PERSON", "namespace": "SOV", "label": "X"},
    }
    # Mathematical edge falsely marked HISTORICAL
    edge_bad_hist = {
        "id": "EDGE:BAD_HIST",
        "type": "EDGE",
        "namespace": "SOV",
        "label": "mismatched realm",
        "edge_type": "REDUCES_TO",
        "relation_realm": "HISTORICAL",
        "source": "EQ:A",
        "target": "EQ:B",
    }
    try:
        module.validate_edge(Path("test"), edge_bad_hist, nodes)
    except module.ValidationError as exc:
        assert "must have relation_realm MATHEMATICAL" in str(exc)
    else:
        raise AssertionError("Mathematical edge with HISTORICAL realm must fail")

    # Historical edge falsely marked MATHEMATICAL
    edge_bad_math = {
        "id": "EDGE:BAD_MATH",
        "type": "EDGE",
        "namespace": "SOV",
        "label": "mismatched realm",
        "edge_type": "AUTHORED",
        "relation_realm": "MATHEMATICAL",
        "source": "PERSON:X",
        "target": "PUB:P",
    }
    try:
        module.validate_edge(Path("test"), edge_bad_math, nodes)
    except module.ValidationError as exc:
        assert "must have relation_realm HISTORICAL" in str(exc)
    else:
        raise AssertionError("Historical edge with MATHEMATICAL realm must fail")


def test_mathematical_edge_cannot_connect_historical_entities() -> None:
    nodes = {
        "PERSON:A": {"id": "PERSON:A", "type": "PERSON", "namespace": "SOV", "label": "A"},
        "PERSON:B": {"id": "PERSON:B", "type": "PERSON", "namespace": "SOV", "label": "B"},
    }
    edge = {
        "id": "EDGE:CONFLATION",
        "type": "EDGE",
        "namespace": "SOV",
        "label": "conflated edge",
        "edge_type": "REDUCES_TO",
        "relation_realm": "MATHEMATICAL",
        "source": "PERSON:A",
        "target": "PERSON:B",
    }
    try:
        module.validate_edge(Path("test"), edge, nodes)
    except module.ValidationError as exc:
        assert "transformation edge REDUCES_TO on EDGE:CONFLATION must connect EQUATION -> EQUATION" in str(exc)
        return
    raise AssertionError("Mathematical transformation connecting persons must fail")
