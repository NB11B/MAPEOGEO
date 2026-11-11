"""Shared clock utilities must not require the optional intelligence runtime."""

from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_without_intel_uow(source: str) -> subprocess.CompletedProcess[str]:
    # A fresh interpreter avoids order-dependent imports from other test modules.
    # Block only the external runtime, even when it is installed on a developer's machine.
    setup = """
import importlib.abc
import sys

class MissingIntelligenceRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "intel_uow" or fullname.startswith("intel_uow."):
            raise ModuleNotFoundError("No module named 'intel_uow'", name="intel_uow")

sys.meta_path.insert(0, MissingIntelligenceRuntime())
"""
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(setup) + textwrap.dedent(source)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_clock_and_contract_import_without_optional_runtime() -> None:
    result = run_without_intel_uow('''
        before = list(sys.path)
        from experiments.intelligence_integration.v0_1 import (
            AdapterContract, ClockDomain, GraphLayer, ProjectionStatus,
            CLOCK_IDENTITY_PREFIX, encode_clock_identity, decode_clock_identity,
        )
        from experiments.intelligence_integration.v0_1.clock_identity import encode_clock_identity as encode
        encoded = encode("domain:a", "actor:b")
        assert encoded == 'uow-clock:v1:["domain:a","actor:b"]'
        assert decode_clock_identity(encoded) == ("domain:a", "actor:b")
        assert encode_clock_identity is encode
        assert "experiments.intelligence_integration.v0_1.adapter" not in sys.modules
        assert sys.path == before
    ''')
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("name", [
    "AttributedAnalysisResult", "MAPEOGEOAnalysisAdapter", "ProjectedAnalysisCase",
])
def test_explicit_adapter_export_preserves_missing_runtime_error(name: str) -> None:
    result = run_without_intel_uow(f'''
        import experiments.intelligence_integration.v0_1 as integration
        try:
            from experiments.intelligence_integration.v0_1 import {name}
        except ModuleNotFoundError as error:
            assert error.name == "intel_uow", error
        else:
            raise AssertionError("Explicit adapter use must require the real runtime")
    ''')
    assert result.returncode == 0, result.stderr


def test_unknown_package_attribute_raises_attribute_error() -> None:
    result = run_without_intel_uow('''
        import experiments.intelligence_integration.v0_1 as integration
        try:
            integration.not_an_export
        except AttributeError:
            pass
        else:
            raise AssertionError("Unknown attributes must not resolve")
        assert "experiments.intelligence_integration.v0_1.adapter" not in sys.modules
    ''')
    assert result.returncode == 0, result.stderr
