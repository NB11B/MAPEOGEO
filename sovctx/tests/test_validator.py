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
