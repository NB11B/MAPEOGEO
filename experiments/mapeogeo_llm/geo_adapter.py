"""Validated binding to the GeometricElementaryOperators dense f64 ABI."""

from __future__ import annotations

import ctypes
import hashlib
import json
import math
from pathlib import Path
from typing import Sequence


GEO_ABI_VERSION = 0x00050100
GEO_MAX_DIMENSION = 6
GEO_MAX_BLADES = 64
GEO_SOURCE_COMMIT = "c590bd7a01f316971722053faf8626458958f820"
GEO_SOURCE_INPUTS_SHA256 = {
    "include/geo/operator_kernel.h": "fc722c7457c79acf236d37098544fc16a0eb53d83caa0cd779a8e00ba007c256",
    "src/operator_kernel.c": "c2a63e94b1f0308aa7f1cc8b3347d00491c06fcb1b8a2a35efebca5b024d96df",
}


class _Multivector(ctypes.Structure):
    _fields_ = [
        ("dimension", ctypes.c_uint8),
        ("signature", ctypes.c_int8 * GEO_MAX_DIMENSION),
        ("coefficients", ctypes.c_double * GEO_MAX_BLADES),
    ]


def _validated_inputs(
    a: Sequence[float], b: Sequence[float] | None, signature: Sequence[int]
) -> tuple[list[float], list[float] | None, list[int]]:
    if isinstance(signature, (str, bytes)):
        raise TypeError("signature must be a sequence of integers")
    metric = list(signature)
    if not 1 <= len(metric) <= GEO_MAX_DIMENSION:
        raise ValueError("signature dimension must be in [1, 6]")
    if any(type(value) is not int or value not in (-1, 1) for value in metric):
        raise ValueError("signature entries must be integer +1 or -1")
    blade_count = 1 << len(metric)

    def coefficients(value: Sequence[float], label: str) -> list[float]:
        if isinstance(value, (str, bytes)):
            raise TypeError(f"{label} must be a coefficient sequence")
        converted = list(value)
        if len(converted) != blade_count:
            raise ValueError(f"{label} must contain exactly {blade_count} coefficients")
        if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in converted):
            raise TypeError(f"{label} coefficients must be real numbers")
        result = [float(item) for item in converted]
        if any(not math.isfinite(item) for item in result):
            raise ValueError(f"{label} coefficients must be finite")
        return result

    return coefficients(a, "a"), coefficients(b, "b") if b is not None else None, metric


def _reference_gp(a: list[float], b: list[float], signature: list[int]) -> list[float]:
    result = [0.0] * len(a)
    for left_blade, left_value in enumerate(a):
        if left_value == 0.0:
            continue
        for right_blade, right_value in enumerate(b):
            if right_value == 0.0:
                continue
            sign = 1
            for index, metric_value in enumerate(signature):
                bit = 1 << index
                if left_blade & bit:
                    if (right_blade & (bit - 1)).bit_count() & 1:
                        sign = -sign
                    if right_blade & bit:
                        sign *= metric_value
            result[left_blade ^ right_blade] += left_value * right_value * sign
    return result


class GeoAdapter:
    """Dense multivector adapter; blade index is the basis-bit mask."""

    def __init__(
        self,
        library_path: str | Path | None = None,
        *,
        allow_reference: bool = False,
        expected_digest: str | None = None,
    ):
        default = Path(__file__).with_name("artifacts") / "geo" / "geo_operator_kernel.dll"
        self._path = Path(library_path) if library_path is not None else default
        self._library: ctypes.CDLL | None = None
        self._library_digest: str | None = None
        self._receipt_status = "not_applicable"
        self._receipt: dict[str, object] | None = None
        self._expected_digest = expected_digest.lower() if expected_digest is not None else None
        if self._expected_digest is not None and (
            len(self._expected_digest) != 64
            or any(character not in "0123456789abcdef" for character in self._expected_digest)
        ):
            raise ValueError("expected_digest must be a 64-character SHA-256 hex digest")
        try:
            self._library = ctypes.CDLL(str(self._path.resolve()))
        except OSError:
            if not allow_reference:
                raise
        if self._library is not None:
            self._configure_library()
            actual_abi = int(self._library.geo_operator_abi_version())
            if actual_abi != GEO_ABI_VERSION:
                raise RuntimeError(
                    f"GEO ABI mismatch: expected 0x{GEO_ABI_VERSION:08x}, got 0x{actual_abi:08x}"
                )
            self._library_digest = hashlib.sha256(self._path.read_bytes()).hexdigest()
            self._load_receipt()

    def _load_receipt(self) -> None:
        receipt_path = self._path.with_name(f"{self._path.stem}.receipt.json")
        if not receipt_path.is_file():
            self._receipt_status = "missing"
            return
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            self._receipt_status = "malformed"
            return
        if not isinstance(receipt, dict) or receipt.get("schema") != "mapeogeo.geo.native-build.v1":
            self._receipt_status = "schema_mismatch"
            return
        if receipt.get("library_sha256") != self._library_digest:
            self._receipt_status = "library_digest_mismatch"
            return
        if receipt.get("abi_version") != "0x00050100":
            self._receipt_status = "abi_mismatch"
            return
        if (
            receipt.get("source_commit") != GEO_SOURCE_COMMIT
            or receipt.get("source_inputs_sha256") != GEO_SOURCE_INPUTS_SHA256
        ):
            self._receipt_status = "source_manifest_mismatch"
            return
        self._receipt = receipt
        self._receipt_status = "verified"

    def _configure_library(self) -> None:
        assert self._library is not None
        self._library.geo_operator_abi_version.argtypes = []
        self._library.geo_operator_abi_version.restype = ctypes.c_uint32
        self._library.geo_operator_gp_f64.argtypes = [
            ctypes.POINTER(_Multivector),
            ctypes.POINTER(_Multivector),
            ctypes.POINTER(_Multivector),
        ]
        self._library.geo_operator_gp_f64.restype = ctypes.c_int

    @staticmethod
    def _native_mv(coefficients: list[float], signature: list[int]) -> _Multivector:
        value = _Multivector()
        value.dimension = len(signature)
        for index, metric_value in enumerate(signature):
            value.signature[index] = metric_value
        for index, coefficient in enumerate(coefficients):
            value.coefficients[index] = coefficient
        return value

    def gp(self, a: list[float], b: list[float], signature: list[int]) -> list[float]:
        left, right, metric = _validated_inputs(a, b, signature)
        assert right is not None
        if self._library is None:
            return _reference_gp(left, right, metric)
        left_mv = self._native_mv(left, metric)
        right_mv = self._native_mv(right, metric)
        output = _Multivector()
        status = self._library.geo_operator_gp_f64(left_mv, right_mv, output)
        if status != 0:
            raise RuntimeError(f"geo_operator_gp_f64 failed with status {status}")
        return [float(output.coefficients[index]) for index in range(1 << len(metric))]

    def grade(self, a: list[float], grade: int, signature: list[int]) -> list[float]:
        coefficients, _, metric = _validated_inputs(a, None, signature)
        if type(grade) is not int or not 0 <= grade <= len(metric):
            raise ValueError(f"grade must be an integer in [0, {len(metric)}]")
        return [
            value if blade.bit_count() == grade else 0.0
            for blade, value in enumerate(coefficients)
        ]

    def metadata(self) -> dict[str, object]:
        native = self._library is not None
        qualified = (
            native
            and self._expected_digest is not None
            and self._expected_digest == self._library_digest
            and self._receipt_status == "verified"
        )
        if not native:
            qualification_reason = "reference_backend"
        elif self._expected_digest is None:
            qualification_reason = "expected_digest_not_supplied"
        elif self._expected_digest != self._library_digest:
            qualification_reason = "expected_digest_mismatch"
        elif self._receipt_status != "verified":
            qualification_reason = f"receipt_{self._receipt_status}"
        else:
            qualification_reason = "caller_expected_digest_and_receipt_match"
        return {
            "backend": "native" if native else "python_reference",
            "abi_version": GEO_ABI_VERSION,
            "max_dimension": GEO_MAX_DIMENSION,
            "source_commit": GEO_SOURCE_COMMIT if qualified else None,
            "declared_source_commit": (
                self._receipt.get("source_commit") if self._receipt is not None else None
            ),
            "source_inputs_sha256": (
                dict(GEO_SOURCE_INPUTS_SHA256) if qualified else None
            ),
            "library_path": str(self._path.resolve()) if native else None,
            "library_sha256": self._library_digest,
            "expected_library_sha256": self._expected_digest,
            "receipt_status": self._receipt_status,
            "native_qualified": qualified,
            "qualification_reason": qualification_reason,
            "evidence_kind": "native_numerical" if native else "development_reference",
        }
