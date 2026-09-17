"""Strict, deterministic identities for solver evidence.

The encoding is deliberately small and tagged.  It never falls back to ``repr``
or ``str`` for an unknown object: adding a new evidence type requires an explicit
encoding rule and therefore an explicit compatibility decision.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from decimal import Decimal
from fractions import Fraction
import base64
import hashlib
import importlib
import json
import math
import unicodedata
from typing import Any

import numpy as np
import sympy as sp


class CanonicalizationError(TypeError):
    """Raised when a value cannot be represented without ambiguity."""


def _text(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _float_node(value: float) -> dict[str, Any]:
    if not math.isfinite(value):
        raise CanonicalizationError("non-finite floating-point value")
    normalized = 0.0 if value == 0.0 else value
    return {"t": "float", "v": normalized.hex()}


def _decimal_node(value: Decimal) -> dict[str, Any]:
    if not value.is_finite():
        raise CanonicalizationError("non-finite Decimal value")
    if value == 0:
        sign, digits, exponent = 0, (0,), 0
    else:
        sign, raw_digits, exponent = value.as_tuple()
        digits_list = list(raw_digits)
        while len(digits_list) > 1 and digits_list[-1] == 0:
            digits_list.pop()
            exponent += 1
        digits = tuple(digits_list)
    return {
        "t": "decimal",
        "v": {"sign": sign, "digits": "".join(str(digit) for digit in digits), "exponent": exponent},
    }


def _encoded_node_bytes(node: Any) -> bytes:
    return json.dumps(node, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _approved_dataclass_types() -> tuple[type[Any], ...]:
    # Evidence identities may contain only the closed solver model.  Keeping this
    # list here (rather than accepting every object decorated with @dataclass)
    # prevents caller-defined classes from acquiring trusted evidence identities.
    from . import elliptic_periods, model, rigorous_math, v0_20_contracts

    return (
        model.ArtifactType,
        model.InputPort,
        model.Artifact,
        model.TargetSpec,
        model.CandidateLineageObligation,
        model.SolverVisibleGoal,
        model.GoalSpec,
        model.Applicability,
        model.VerificationResult,
        model.Refusal,
        model.RootOrigin,
        model.DerivationStep,
        model.DerivedArtifactRecord,
        model.DerivedObligation,
        model.RoutingReceipt,
        model.LineageReceipt,
        model.RuntimeMacroBinding,
        model.OperatorFailure,
        model.SolveTrace,
        rigorous_math.Sqrt2CutCertificate,
        rigorous_math.QuadraticMeanValueCertificate,
        rigorous_math.BezoutCertificate,
        rigorous_math.CauchyRiemannCertificate,
        rigorous_math.ResidueCertificate,
        rigorous_math.GridEvaluationCertificate,
        elliptic_periods.RationalInterval,
        elliptic_periods.InvariantDiagnostic,
        elliptic_periods.PeriodCertificate,
        v0_20_contracts.SymbolicPolynomial,
        v0_20_contracts.NumericalPolynomialEvaluation,
        v0_20_contracts.WeierstrassCurve,
    )


def _is_registered_library_type(value_type: type[Any], root_module: str) -> bool:
    module_name = value_type.__module__
    if module_name != root_module and not module_name.startswith(f"{root_module}."):
        return False
    try:
        resolved: Any = importlib.import_module(module_name)
        for component in value_type.__qualname__.split("."):
            if component == "<locals>":
                return False
            resolved = getattr(resolved, component)
    except (AttributeError, ImportError):
        return False
    return resolved is value_type


def canonical_node(value: Any) -> Any:
    """Return a tagged JSON-compatible representation of ``value``."""

    value_type = type(value)
    if value is None:
        return {"t": "none"}
    if value_type is bool:
        return {"t": "bool", "v": value}
    if value_type is int:
        return {"t": "int", "v": str(value)}
    if value_type is float:
        return _float_node(value)
    if value_type is str:
        return {"t": "str", "v": _text(value)}
    if value_type is bytes:
        return {"t": "bytes", "v": base64.b64encode(value).decode("ascii")}
    if value_type is Fraction:
        return {"t": "fraction", "n": str(value.numerator), "d": str(value.denominator)}
    if value_type is Decimal:
        return _decimal_node(value)
    if value_type is complex:
        return {"t": "complex", "real": _float_node(value.real), "imag": _float_node(value.imag)}
    if isinstance(value, np.generic):
        if value.dtype.type is not value_type or not _is_registered_library_type(value_type, "numpy"):
            raise CanonicalizationError(
                f"unsupported evidence type: {value_type.__module__}.{value_type.__qualname__}"
            )
        return {
            "t": "numpy_scalar",
            "dtype": value.dtype.str,
            "v": canonical_node(value.item()),
        }
    if value_type is np.ndarray:
        if value.dtype.hasobject:
            raise CanonicalizationError("object-dtype arrays are not canonical evidence")
        return {
            "t": "numpy_array",
            "dtype": value.dtype.str,
            "shape": [str(part) for part in value.shape],
            "v": [canonical_node(item.item() if isinstance(item, np.generic) else item) for item in value.flat],
        }
    if isinstance(value, sp.Basic):
        if not _is_registered_library_type(value_type, "sympy"):
            raise CanonicalizationError(
                f"unsupported evidence type: {value_type.__module__}.{value_type.__qualname__}"
            )
        if bool(value.has(sp.nan, sp.oo, -sp.oo, sp.zoo)):
            raise CanonicalizationError("non-finite SymPy value")
        return {"t": "sympy", "v": _text(sp.srepr(value))}
    if value_type is list:
        return {"t": "list", "v": [canonical_node(item) for item in value]}
    if value_type is tuple:
        return {"t": "tuple", "v": [canonical_node(item) for item in value]}
    if value_type in {set, frozenset}:
        nodes = [canonical_node(item) for item in value]
        encoded = [_encoded_node_bytes(node) for node in nodes]
        if len(encoded) != len(set(encoded)):
            raise CanonicalizationError("canonical set element collision")
        nodes = [node for _, node in sorted(zip(encoded, nodes), key=lambda pair: pair[0])]
        return {"t": "frozenset" if value_type is frozenset else "set", "v": nodes}
    if value_type is dict:
        pairs = [(canonical_node(key), canonical_node(item)) for key, item in value.items()]
        encoded_keys = [_encoded_node_bytes(pair[0]) for pair in pairs]
        if len(encoded_keys) != len(set(encoded_keys)):
            raise CanonicalizationError("canonical mapping key collision")
        pairs = [pair for _, pair in sorted(zip(encoded_keys, pairs), key=lambda row: row[0])]
        return {"t": "map", "v": [[key, item] for key, item in pairs]}
    if is_dataclass(value) and not isinstance(value, type):
        if value_type not in _approved_dataclass_types():
            raise CanonicalizationError(
                f"unapproved dataclass evidence type: {value_type.__module__}.{value_type.__qualname__}"
            )
        type_name = f"{value_type.__module__}.{value_type.__qualname__}"
        return {
            "t": "dataclass",
            "class": _text(type_name),
            "v": [[field.name, canonical_node(getattr(value, field.name))] for field in fields(value)],
        }
    if callable(value):
        raise CanonicalizationError("callables are not canonical evidence")
    raise CanonicalizationError(f"unsupported evidence type: {type(value).__module__}.{type(value).__qualname__}")


def canonical_bytes(value: Any) -> bytes:
    return _encoded_node_bytes(canonical_node(value))


def canonical_sha256(value: Any, *, domain: str) -> str:
    if not isinstance(domain, str) or not domain:
        raise ValueError("canonical digest domain must be a nonempty string")
    domain_bytes = _text(domain).encode("utf-8")
    return hashlib.sha256(domain_bytes + b"\0" + canonical_bytes(value)).hexdigest()
