from __future__ import annotations

import shutil

import pytest

from experiments.mapeogeo_llm.lean_adapter import LeanAdapter


LEAN = shutil.which("lean")


@pytest.fixture(scope="module")
def adapter() -> LeanAdapter:
    if LEAN is None:
        pytest.fail("Lean is required for Task 2 integration tests")
    return LeanAdapter(LEAN)


@pytest.mark.parametrize(("proposition", "proof"), [("2 + 2 = 4", "by decide"), ("7 * 6 = 42", "by rfl"), ("3 < 5", "by decide")])
def test_real_lean_verifies_closed_arithmetic_without_axioms(adapter: LeanAdapter, proposition: str, proof: str) -> None:
    result = adapter.verify(proposition, proof)
    assert result["status"] == "VERIFIED"
    assert result["evidence"]["kernel_checked"] is True
    assert result["evidence"]["axioms"] == []
    assert result["evidence"]["theorem"] == "mapeogeo_checked"
    assert "4.33.1" in result["evidence"]["lean_version"]


def test_false_theorem_is_not_verified(adapter: LeanAdapter) -> None:
    result = adapter.verify("2 + 2 = 5", "by decide")
    assert result["status"] == "UNSOLVED"
    assert result["evidence"]["kernel_checked"] is False
    assert result["evidence"]["negation_checked"] is False


@pytest.mark.parametrize(
    ("proposition", "proof"),
    [
        ("2 + = 4", "by decide"),
        ("True", "by decide"),
        ("2 = 2\naxiom stolen : False", "by decide"),
        ("2 = 2", "by sorry"),
        ("2 = 2", "by admit"),
        ("2 = 2", "by exact (Classical.choice (show Nonempty (2 = 2) from inferInstance))"),
        ("False -> 2 = 2", "by intro h; rfl"),
    ],
)
def test_malformed_source_injection_sorry_axiom_and_hypothesis_smuggling_are_rejected(adapter: LeanAdapter, proposition: str, proof: str) -> None:
    result = adapter.verify(proposition, proof)
    assert result["status"] == "INVALID_INPUT"
    assert result["evidence"]["kernel_checked"] is False


def test_real_process_timeout_is_non_verifying(adapter: LeanAdapter) -> None:
    result = adapter.verify("2 + 2 = 4", "by decide", timeout_seconds=1e-9)
    assert result["status"] == "TIMEOUT"
    assert result["evidence"]["kernel_checked"] is False


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_invalid_timeout_is_rejected(adapter: LeanAdapter, timeout: float) -> None:
    result = adapter.verify("2 = 2", "by rfl", timeout_seconds=timeout)
    assert result["status"] == "INVALID_INPUT"
