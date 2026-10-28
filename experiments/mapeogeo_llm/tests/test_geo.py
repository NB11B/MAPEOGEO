from __future__ import annotations

import os
from pathlib import Path
import json
import shutil
import subprocess

import numpy as np
import pytest

from experiments.mapeogeo_llm.geo_adapter import GEO_ABI_VERSION, GeoAdapter


DLL = Path(os.environ.get("MAPEOGEO_GEO_LIBRARY", "experiments/mapeogeo_llm/artifacts/geo/geo_operator_kernel.dll"))
EXPECTED_DLL_DIGEST = "03eaa7778f53ccedaa1dc36a9e3872c4d95fea97d5967349094d4d40f58df963"


def _native() -> GeoAdapter:
    if not DLL.is_file():
        pytest.fail(f"native GEO library missing; run scripts/build_geo.ps1: {DLL}")
    return GeoAdapter(DLL, expected_digest=EXPECTED_DLL_DIGEST)


def _pauli_basis(signature: list[int]) -> list[np.ndarray]:
    i = 1j
    sigma = [
        np.array([[0, 1], [1, 0]], dtype=complex),
        np.array([[0, -i], [i, 0]], dtype=complex),
        np.array([[1, 0], [0, -1]], dtype=complex),
    ]
    return [matrix if sign == 1 else i * matrix for matrix, sign in zip(sigma, signature)]


def _blade_matrices(signature: list[int]) -> list[np.ndarray]:
    basis = _pauli_basis(signature)
    result: list[np.ndarray] = []
    for blade in range(1 << len(signature)):
        matrix = np.eye(2, dtype=complex)
        for index, generator in enumerate(basis):
            if blade & (1 << index):
                matrix = matrix @ generator
        result.append(matrix)
    return result


def _matrix_of(coefficients: list[float], signature: list[int]) -> np.ndarray:
    return sum((coefficient * blade for coefficient, blade in zip(coefficients, _blade_matrices(signature))), np.zeros((2, 2), dtype=complex))


def test_native_abi_and_backend_metadata_are_pinned() -> None:
    adapter = _native()
    metadata = adapter.metadata()
    assert metadata["backend"] == "native"
    assert metadata["abi_version"] == GEO_ABI_VERSION == 0x00050100
    assert metadata["max_dimension"] == 6
    assert metadata["native_qualified"] is True
    assert metadata["receipt_status"] == "verified"
    assert metadata["source_commit"] == "c590bd7a01f316971722053faf8626458958f820"
    assert metadata["source_inputs_sha256"] == {
        "include/geo/operator_kernel.h": "fc722c7457c79acf236d37098544fc16a0eb53d83caa0cd779a8e00ba007c256",
        "src/operator_kernel.c": "c2a63e94b1f0308aa7f1cc8b3347d00491c06fcb1b8a2a35efebca5b024d96df",
    }


@pytest.mark.parametrize("signature", [[1, 1, 1], [1, -1, 1]])
def test_geometric_product_matches_independent_pauli_representation(signature: list[int]) -> None:
    adapter = _native()
    blades = _blade_matrices(signature)
    for left in range(8):
        for right in range(8):
            a = [0.0] * 8
            b = [0.0] * 8
            a[left] = 1.0
            b[right] = 1.0
            actual = _matrix_of(adapter.gp(a, b, signature), signature)
            np.testing.assert_allclose(actual, blades[left] @ blades[right], rtol=0, atol=1e-12)


def test_mixed_metric_squares_and_anticommutation() -> None:
    adapter = _native()
    signature = [1, -1, 1]
    basis = [[0.0] * 8 for _ in range(3)]
    for index in range(3):
        basis[index][1 << index] = 1.0
    scalar = [1.0] + [0.0] * 7
    assert adapter.gp(basis[0], basis[0], signature) == scalar
    assert adapter.gp(basis[1], basis[1], signature) == [-1.0] + [0.0] * 7
    e12 = adapter.gp(basis[0], basis[1], signature)
    e21 = adapter.gp(basis[1], basis[0], signature)
    assert e12 == [-value for value in e21]


def test_associativity_and_bilinearity_against_matrix_reference() -> None:
    adapter = _native()
    signature = [1, -1, 1]
    rng = np.random.default_rng(20261028)
    for _ in range(20):
        a, b, c = (rng.integers(-3, 4, size=8).astype(float).tolist() for _ in range(3))
        lhs = adapter.gp(adapter.gp(a, b, signature), c, signature)
        rhs = adapter.gp(a, adapter.gp(b, c, signature), signature)
        np.testing.assert_allclose(lhs, rhs, rtol=0, atol=1e-12)
        np.testing.assert_allclose(_matrix_of(adapter.gp(a, b, signature), signature), _matrix_of(a, signature) @ _matrix_of(b, signature), rtol=0, atol=1e-11)
        summed = [x + y for x, y in zip(a, b)]
        expected = [x + y for x, y in zip(adapter.gp(a, c, signature), adapter.gp(b, c, signature))]
        np.testing.assert_allclose(adapter.gp(summed, c, signature), expected, rtol=0, atol=1e-12)


def test_grade_selects_only_requested_blades() -> None:
    adapter = _native()
    mv = list(map(float, range(8)))
    assert adapter.grade(mv, 0, [1, 1, 1]) == [0.0] * 8
    assert adapter.grade(mv, 1, [1, 1, 1]) == [0.0, 1.0, 2.0, 0.0, 4.0, 0.0, 0.0, 0.0]
    assert adapter.grade(mv, 2, [1, 1, 1]) == [0.0, 0.0, 0.0, 3.0, 0.0, 5.0, 6.0, 0.0]
    assert adapter.grade(mv, 3, [1, 1, 1]) == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7.0]


@pytest.mark.parametrize(
    ("a", "b", "signature"),
    [
        ([], [], []),
        ([1.0], [1.0], [1]),
        ([1.0, 0.0], [1.0], [1]),
        ([1.0, 0.0], [1.0, 0.0], [0]),
        ([1.0] * 128, [1.0] * 128, [1] * 7),
        ([float("nan"), 0.0], [1.0, 0.0], [1]),
    ],
)
def test_invalid_dimensions_signatures_shapes_and_values_fail_closed(a: list[float], b: list[float], signature: list[int]) -> None:
    with pytest.raises((TypeError, ValueError)):
        _native().gp(a, b, signature)


def test_reference_backend_requires_explicit_opt_in_and_is_not_native_qualified() -> None:
    missing = Path("definitely-not-a-geo-library.dll")
    with pytest.raises(OSError):
        GeoAdapter(missing)
    adapter = GeoAdapter(missing, allow_reference=True)
    assert adapter.metadata()["backend"] == "python_reference"
    assert adapter.metadata()["native_qualified"] is False
    assert adapter.gp([0.0, 1.0], [0.0, 1.0], [-1]) == [-1.0, 0.0]


def test_native_build_is_byte_reproducible(tmp_path: Path) -> None:
    repo_root = Path(__file__).parents[3]
    outputs = [tmp_path / "first", tmp_path / "second"]
    for output in outputs:
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(repo_root / "scripts" / "build_geo.ps1"),
                "-OutputDirectory",
                str(output),
            ],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )
    assert (outputs[0] / "geo_operator_kernel.dll").read_bytes() == (
        outputs[1] / "geo_operator_kernel.dll"
    ).read_bytes()
    receipt = json.loads((outputs[0] / "geo_operator_kernel.receipt.json").read_text(encoding="utf-8"))
    assert receipt["schema"] == "mapeogeo.geo.native-build.v1"
    assert receipt["library_sha256"] == EXPECTED_DLL_DIGEST


def test_arbitrary_same_abi_library_is_usable_but_unqualified(tmp_path: Path) -> None:
    copied = tmp_path / "alternate.dll"
    shutil.copy2(DLL, copied)
    adapter = GeoAdapter(copied)
    metadata = adapter.metadata()
    assert metadata["backend"] == "native"
    assert metadata["native_qualified"] is False
    assert metadata["source_commit"] is None
    assert metadata["receipt_status"] == "missing"
    assert adapter.gp([0.0, 1.0], [0.0, 1.0], [1]) == [1.0, 0.0]


def test_tampered_receipt_cannot_qualify_native_library(tmp_path: Path) -> None:
    copied = tmp_path / "geo_operator_kernel.dll"
    receipt_path = tmp_path / "geo_operator_kernel.receipt.json"
    shutil.copy2(DLL, copied)
    receipt = json.loads(DLL.with_name("geo_operator_kernel.receipt.json").read_text(encoding="utf-8"))
    receipt["library_sha256"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    metadata = GeoAdapter(copied, expected_digest=EXPECTED_DLL_DIGEST).metadata()
    assert metadata["native_qualified"] is False
    assert metadata["source_commit"] is None
    assert metadata["receipt_status"] == "library_digest_mismatch"


def test_build_rejects_dirty_compiled_source_inputs(tmp_path: Path) -> None:
    repo_root = Path(__file__).parents[3]
    source_checkout = tmp_path / "geo-source"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", r"C:\Users\nateb\Documents\GeometricElementaryOperators", str(source_checkout)],
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    source = source_checkout / "src" / "operator_kernel.c"
    source.write_text(source.read_text(encoding="utf-8") + "\n/* dirty test input */\n", encoding="utf-8")
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repo_root / "scripts" / "build_geo.ps1"),
            "-SourceRoot",
            str(source_checkout),
            "-OutputDirectory",
            str(tmp_path / "dirty-output"),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        shell=False,
    )
    assert completed.returncode != 0
    assert "compiled source inputs differ from pinned commit" in completed.stderr
