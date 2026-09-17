from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, fields, is_dataclass, replace
from functools import lru_cache
from fractions import Fraction
from itertools import permutations
import ast
import hashlib
import inspect
import json
import math
from pathlib import Path
import re
from types import MappingProxyType, ModuleType
from typing import Any, Mapping, Sequence

import sympy as sp

from .campaign import MODE_CONFIGS
from .campaign_oracles import (
    build_independent_oracle,
    candidate_matches_independent_oracle,
)
from .canonical import canonical_sha256
from .compatibility import CompatibilityModel, authoritative_routing_decision
from .goal_verifiers import validate_historical_goal_contract, verify_historical_goal
from .historical_oracles import (
    HistoricalReference,
    build_historical_reference,
    historical_candidate_satisfies_reference,
)
from .lineage import track_roots
from .model import (
    Applicability,
    Artifact,
    ArtifactType,
    DerivedArtifactRecord,
    DerivationStep,
    DerivedObligation,
    GoalSpec,
    LineageReceipt,
    OperatorFailure,
    Refusal,
    RootOrigin,
    RoutingReceipt,
    SolveTrace,
    VerificationResult,
)
from .operators import OperatorSpec, callable_contract_digest
from .planner import (
    _PLANNER_COMPARISON_CONTRACTS,
    _registry_digest as _planner_registry_digest,
    solve,
)
from .repaired_main_binding import (
    build_repaired_main_binding,
    validate_repaired_main_binding_manifest,
    verify_repaired_main_checkout,
)
from .v0_20_goals import (
    ALL_V0_20_FAMILIES,
    CORE_SPLITS,
    CROSS_CLASS_FAMILIES,
    FROZEN_FEATURE_BASE_SHA,
    NEW_V0_20_FAMILIES,
    V0_20_EXPECTED_COUNTS,
    V0_20_TERMINAL_CONTROL_COUNT,
    TerminalCandidateControl,
    TerminalControlKind,
    _canonical,
    build_case_oracle,
    build_v0_20_corpus,
    build_v0_20_terminal_controls,
    case_signatures,
    prove_no_same_class_shortcut,
)
from .v0_20_macros import MacroProposalSpec, synthesize_macro_proposals
from .v0_20_operators import build_v0_20_operator_registry
from .v0_20_verifiers import validate_v0_20_goal_contract, verify_v0_20_goal


_STRICT_TERMINAL_CONTROL_AUTHORITY = verify_v0_20_goal


_FROZEN_CAMPAIGN_FAMILIES = (
    "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11", "G12",
    "F1", "F2", "F3", "C1", "C2", "X1", "X2",
)
_FROZEN_CROSS_CLASS_FAMILIES = ("X1", "X2")
_FROZEN_SPLIT_SPECS = (
    ("CALIBRATION_V0_20", "calibration_v0_20", 3),
    ("VALIDATION_V0_20", "validation_v0_20", 1),
    ("SEALED_V0_20", "sealed_v0_20", 2),
)
_FROZEN_SPLIT_NAMES = tuple(row[0] for row in _FROZEN_SPLIT_SPECS)
_FROZEN_EXPECTED_GOAL_ROWS = tuple(
    (split, f"{prefix}:{family.lower()}:{variant:02d}", family)
    for split, prefix, count in _FROZEN_SPLIT_SPECS
    for family in _FROZEN_CAMPAIGN_FAMILIES
    for variant in range(count)
)
_FROZEN_CORPUS_MANIFEST_SHA256 = (
    "093e4e5869dbde03e7bd98f135ded4cf344fda24bc439f4ef233e5142dbf7a1d"
)
_FROZEN_SEALED_CASE_MANIFEST_SHA256 = (
    "cafba9583f692f0653d2808bec71721efecac1fbac76c29f67178b1c415901d6"
)
_FROZEN_EXPECTED_SEALED_GOAL_ROWS = tuple(
    (goal_id, family)
    for split, goal_id, family in _FROZEN_EXPECTED_GOAL_ROWS
    if split == "SEALED_V0_20"
)
_FROZEN_MODE_CONFIGS = (
    ("EXPLICIT/PRIMITIVE", "EXPLICIT", False),
    ("EXPLICIT/SYNTHESIZED", "EXPLICIT", True),
    ("INFERRED/PRIMITIVE", "INFERRED", False),
    ("INFERRED/SYNTHESIZED", "INFERRED", True),
    ("HYBRID/PRIMITIVE", "HYBRID", False),
    ("HYBRID/SYNTHESIZED", "HYBRID", True),
)
_MODE_COUNT = 6
_SEALED_COUNT = 38
_CORE_COUNT = 114
_CROSS_CLASS_SEALED_COUNT = 4
_MACRO_PAIR_COUNT = 3


def _terminal_control_manifest_row(
    family: str,
    suffix: str,
    kind: TerminalControlKind,
    expected_pass: bool,
    distinct_alternative: bool,
) -> tuple[str, str, str, bool, bool]:
    return (
        f"terminal-control:{family.lower()}:{suffix}",
        family,
        kind.value,
        expected_pass,
        distinct_alternative,
    )


_FROZEN_TERMINAL_CONTROL_MANIFEST = (
    tuple(
        row
        for family in ("F1", "F2", "F3", "C1", "C2", "X1", "X2")
        for row in (
            _terminal_control_manifest_row(
                family,
                "domain",
                TerminalControlKind.DOMAIN_REFUSAL,
                False,
                False,
            ),
            _terminal_control_manifest_row(
                family,
                "invalid",
                TerminalControlKind.INVALID_TERMINAL_CERTIFICATE,
                False,
                False,
            ),
        )
    )
    + tuple(
        _terminal_control_manifest_row(
            family,
            "negative",
            TerminalControlKind.VALID_NEGATIVE_RESULT,
            True,
            False,
        )
        for family in ("F2", "F3", "C1", "C2", "X1")
    )
    + tuple(
        _terminal_control_manifest_row(
            family,
            "external",
            TerminalControlKind.EXTERNAL_VALID_CERTIFICATE,
            True,
            family in {"F2", "F3"},
        )
        for family in ("F2", "F3", "X1")
    )
)
if len(_FROZEN_TERMINAL_CONTROL_MANIFEST) != V0_20_TERMINAL_CONTROL_COUNT:
    raise AssertionError("frozen terminal control manifest count drifted")
_FROZEN_TERMINAL_CONTROLS_SHA256 = (
    "37efce3fa50565b124adc611965f66c747ff496ef0f1e86aed6bc8afe9889ad0"
)


ENGINE_GATE_KEYS = frozenset({
    "closed_challenge_domain_valid",
    "exact_content_partition_disjoint",
    "nuisance_partition_disjoint",
    "terminal_controls_conform",
    "target_contract_enforced",
    "zero_known_wrong_positives",
})
EVIDENCE_GATE_KEYS = frozenset({
    "independent_oracles_complete",
    "shortcut_proofs_complete",
    "runtime_lineage_receipts_complete",
    "implementation_manifest_bound",
    "dependency_lock_bound",
    "repaired_main_bound",
})
CAPABILITY_GATE_KEYS = frozenset({
    "explicit_family_coverage",
    "inferred_family_coverage",
    "hybrid_family_coverage",
    "zero_macro_rescues",
    "exact_macro_conservation",
})
EXPECTED_GATE_KEYS = ENGINE_GATE_KEYS | EVIDENCE_GATE_KEYS | CAPABILITY_GATE_KEYS


GATE_DENOMINATORS: dict[str, int] = {
    "closed_challenge_domain_valid": _CORE_COUNT,
    "exact_content_partition_disjoint": _CORE_COUNT,
    "nuisance_partition_disjoint": _CORE_COUNT,
    "terminal_controls_conform": V0_20_TERMINAL_CONTROL_COUNT,
    "target_contract_enforced": _MODE_COUNT * _SEALED_COUNT,
    "zero_known_wrong_positives": _MODE_COUNT * _SEALED_COUNT,
    "independent_oracles_complete": _SEALED_COUNT,
    "shortcut_proofs_complete": _CROSS_CLASS_SEALED_COUNT,
    "runtime_lineage_receipts_complete": _MODE_COUNT * _CROSS_CLASS_SEALED_COUNT,
    "implementation_manifest_bound": 1,
    "dependency_lock_bound": 1,
    "repaired_main_bound": 1,
    "explicit_family_coverage": len(_FROZEN_CAMPAIGN_FAMILIES),
    "inferred_family_coverage": len(_FROZEN_CAMPAIGN_FAMILIES),
    "hybrid_family_coverage": len(_FROZEN_CAMPAIGN_FAMILIES),
    "zero_macro_rescues": _MACRO_PAIR_COUNT * _SEALED_COUNT,
    "exact_macro_conservation": _MACRO_PAIR_COUNT * _SEALED_COUNT,
}
if set(GATE_DENOMINATORS) != set(EXPECTED_GATE_KEYS):
    raise AssertionError("scientific gate denominator manifest drifted")


FROZEN_EXPECTED_GATE_VECTOR: Mapping[str, bool] = MappingProxyType({
    "closed_challenge_domain_valid": True,
    "exact_content_partition_disjoint": True,
    "nuisance_partition_disjoint": True,
    "terminal_controls_conform": True,
    "target_contract_enforced": True,
    "zero_known_wrong_positives": True,
    "independent_oracles_complete": False,
    "shortcut_proofs_complete": True,
    "runtime_lineage_receipts_complete": False,
    "implementation_manifest_bound": True,
    "dependency_lock_bound": True,
    "repaired_main_bound": True,
    "explicit_family_coverage": False,
    "inferred_family_coverage": False,
    "hybrid_family_coverage": False,
    "zero_macro_rescues": True,
    "exact_macro_conservation": False,
})
FROZEN_EXPECTED_SCIENTIFIC_STATUS = "EVIDENCE_PARTIAL"
if set(FROZEN_EXPECTED_GATE_VECTOR) != set(EXPECTED_GATE_KEYS):
    raise AssertionError("frozen expected scientific gate vector drifted")


def matches_frozen_expected_gate_vector(gates: object) -> bool:
    """Accept only the reviewed, exact v0.20 gate outcome."""

    return bool(
        type(gates) is dict
        and set(gates) == set(FROZEN_EXPECTED_GATE_VECTOR)
        and all(type(gates[key]) is bool for key in FROZEN_EXPECTED_GATE_VECTOR)
        and all(
            gates[key] is FROZEN_EXPECTED_GATE_VECTOR[key]
            for key in FROZEN_EXPECTED_GATE_VECTOR
        )
    )


def classify_scientific_status(gates: Mapping[str, bool]) -> str:
    """Classify integrity, evidence completeness, and capability separately."""

    if set(gates) != set(EXPECTED_GATE_KEYS):
        return "ENGINE_INVALID"
    if any(type(gates[key]) is not bool for key in EXPECTED_GATE_KEYS):
        return "ENGINE_INVALID"
    if not all(gates[key] for key in ENGINE_GATE_KEYS):
        return "ENGINE_INVALID"
    if not all(gates[key] for key in EVIDENCE_GATE_KEYS):
        return "EVIDENCE_PARTIAL"
    if not all(gates[key] for key in CAPABILITY_GATE_KEYS):
        return "NOT_SUPPORTED"
    return "SUPPORTED"


def classify_scientific_axes(gates: Mapping[str, bool]) -> dict[str, str]:
    """Report engine, evidence, and capability conclusions independently."""

    well_formed = bool(
        type(gates) is dict
        and set(gates) == set(EXPECTED_GATE_KEYS)
        and all(type(gates[key]) is bool for key in EXPECTED_GATE_KEYS)
    )
    engine_valid = bool(well_formed and all(gates[key] for key in ENGINE_GATE_KEYS))
    if not engine_valid:
        return {
            "engine_validity": "INVALID",
            "evidence_completeness": "NOT_ASSESSABLE",
            "capability_support": "NOT_ASSESSABLE",
        }
    return {
        "engine_validity": "VALID",
        "evidence_completeness": (
            "COMPLETE" if all(gates[key] for key in EVIDENCE_GATE_KEYS) else "PARTIAL"
        ),
        "capability_support": (
            "SUPPORTED" if all(gates[key] for key in CAPABILITY_GATE_KEYS) else "NOT_SUPPORTED"
        ),
    }


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _sha256_bytes(payload)


def _frozen_corpus_manifest_receipt(
    corpus: object,
) -> dict[str, Any]:
    """Validate the exact preregistered v0.20 challenge population and content."""

    errors: list[str] = []
    observed_manifest_sha256: str | None = None
    observed_goal_count = 0
    try:
        if type(corpus) is not dict:
            raise ValueError("corpus must be an exact dict")
        if (
            type(MODE_CONFIGS) is not tuple
            or MODE_CONFIGS != _FROZEN_MODE_CONFIGS
            or len({row[0] for row in MODE_CONFIGS}) != _MODE_COUNT
        ):
            errors.append("MODE_CONFIG_MANIFEST_MISMATCH")
        if (
            type(CROSS_CLASS_FAMILIES) is not tuple
            or CROSS_CLASS_FAMILIES != _FROZEN_CROSS_CLASS_FAMILIES
        ):
            errors.append("CROSS_CLASS_FAMILY_MANIFEST_MISMATCH")
        expected_splits = tuple(row[0] for row in _FROZEN_SPLIT_SPECS)
        if tuple(corpus) != expected_splits or set(corpus) != set(expected_splits):
            errors.append("SPLIT_SET_OR_ORDER_MISMATCH")

        structural_rows: list[tuple[str, str, str]] = []
        content_rows: list[dict[str, Any]] = []
        goal_ids: list[str] = []
        per_split_family: dict[tuple[str, str], int] = {}
        sealed_cross_count = 0
        for split, _prefix, expected_per_family in _FROZEN_SPLIT_SPECS:
            goals = corpus.get(split, ())
            if type(goals) is not list:
                errors.append(f"{split}:NOT_EXACT_LIST")
                goals = ()
            expected_split_size = len(_FROZEN_CAMPAIGN_FAMILIES) * expected_per_family
            if len(goals) != expected_split_size:
                errors.append(f"{split}:SIZE_MISMATCH")
            for goal in goals:
                if type(goal) is not GoalSpec:
                    errors.append(f"{split}:NON_GOAL_SPEC")
                    continue
                observed_goal_count += 1
                structural_rows.append((split, goal.goal_id, goal.family))
                goal_ids.append(goal.goal_id)
                per_split_family[(split, goal.family)] = (
                    per_split_family.get((split, goal.family), 0) + 1
                )
                if (
                    split == "SEALED_V0_20"
                    and goal.family in _FROZEN_CROSS_CLASS_FAMILIES
                ):
                    sealed_cross_count += 1
                signatures = case_signatures(goal)
                content_rows.append({
                    "split": split,
                    "goal_id": goal.goal_id,
                    "family": goal.family,
                    "exact_content_sha256": signatures.exact_sha256,
                    "nuisance_content_sha256": signatures.nuisance_sha256,
                    "nuisance_relation": signatures.nuisance_relation,
                })

        if tuple(structural_rows) != _FROZEN_EXPECTED_GOAL_ROWS:
            errors.append("GOAL_ID_FAMILY_MANIFEST_MISMATCH")
        if len(goal_ids) != len(set(goal_ids)):
            errors.append("DUPLICATE_GOAL_ID")
        for split, _prefix, expected_per_family in _FROZEN_SPLIT_SPECS:
            for family in _FROZEN_CAMPAIGN_FAMILIES:
                if per_split_family.get((split, family), 0) != expected_per_family:
                    errors.append(f"{split}:{family}:CARDINALITY_MISMATCH")
        if sealed_cross_count != _CROSS_CLASS_SEALED_COUNT:
            errors.append("SEALED_CROSS_CLASS_COUNT_MISMATCH")
        observed_manifest_sha256 = _sha256_json(content_rows)
        if observed_manifest_sha256 != _FROZEN_CORPUS_MANIFEST_SHA256:
            errors.append("CORPUS_CONTENT_DIGEST_MISMATCH")
    except Exception as exc:
        errors.append(f"MANIFEST_VALIDATION_ERROR:{_safe_exception_label(exc)}")

    return {
        "valid": not errors,
        "expected_goal_count": _CORE_COUNT,
        "observed_goal_count": observed_goal_count,
        "expected_manifest_sha256": _FROZEN_CORPUS_MANIFEST_SHA256,
        "observed_manifest_sha256": observed_manifest_sha256,
        "errors": tuple(errors),
    }


def _scored_mode_manifest_receipt(mode: object) -> dict[str, Any]:
    """Bind one scored mode to the exact frozen sealed challenge population."""

    errors: list[str] = []
    observed_manifest_sha256: str | None = None
    rows: list[dict[str, Any]] = []
    try:
        if type(mode) is not dict:
            raise ValueError("scored mode must be an exact dict")
        cases = mode.get("cases")
        if type(mode.get("total")) is not int or mode["total"] != _SEALED_COUNT:
            errors.append("MODE_TOTAL_MISMATCH")
        if type(cases) is not list:
            errors.append("MODE_CASES_NOT_EXACT_LIST")
            cases = ()
        if len(cases) != _SEALED_COUNT:
            errors.append("MODE_CASE_COUNT_MISMATCH")

        structural_rows: list[tuple[str, str]] = []
        goal_ids: list[str] = []
        for case in cases:
            if type(case) is not dict:
                errors.append("NON_EXACT_CASE_ROW")
                continue
            row = {
                "goal_id": case.get("goal_id"),
                "family": case.get("family"),
                "exact_content_sha256": case.get("exact_content_sha256"),
                "nuisance_content_sha256": case.get("nuisance_content_sha256"),
                "nuisance_relation": case.get("nuisance_relation"),
            }
            if not all(type(row[key]) is str for key in row):
                errors.append("NONCANONICAL_CASE_MANIFEST_FIELD")
                continue
            rows.append(row)
            structural_rows.append((row["goal_id"], row["family"]))
            goal_ids.append(row["goal_id"])

        if tuple(structural_rows) != _FROZEN_EXPECTED_SEALED_GOAL_ROWS:
            errors.append("SEALED_GOAL_ID_FAMILY_MANIFEST_MISMATCH")
        if len(goal_ids) != len(set(goal_ids)):
            errors.append("DUPLICATE_SEALED_GOAL_ID")
        observed_manifest_sha256 = _sha256_json(rows)
        if observed_manifest_sha256 != _FROZEN_SEALED_CASE_MANIFEST_SHA256:
            errors.append("SEALED_CASE_CONTENT_DIGEST_MISMATCH")
    except Exception as exc:
        errors.append(f"SCORED_MODE_MANIFEST_ERROR:{_safe_exception_label(exc)}")

    return {
        "valid": not errors,
        "expected_case_count": _SEALED_COUNT,
        "observed_case_count": len(rows),
        "expected_manifest_sha256": _FROZEN_SEALED_CASE_MANIFEST_SHA256,
        "observed_manifest_sha256": observed_manifest_sha256,
        "errors": tuple(errors),
    }


_NONCANONICAL_EVIDENCE = {
    "type": "NONCANONICAL_EVIDENCE",
    "reason": "BOUNDED_CANONICALIZATION_REJECTED",
}
_MAX_EVIDENCE_NODES = 8192
_MAX_EVIDENCE_DEPTH = 64
_MAX_EVIDENCE_COLLECTION = 4096
_MAX_EVIDENCE_TEXT = 65536
_MAX_EVIDENCE_INTEGER_BITS = 65536
_MAX_EVIDENCE_CUMULATIVE_TEXT = 1_000_000
_MAX_EVIDENCE_CUMULATIVE_INTEGER_BITS = 1_000_000


def _bounded_evidence_shape(value: Any) -> None:
    """Reject cyclic or unreasonably large evidence before recursive encoding."""

    visited_nodes = 0
    active: set[int] = set()
    cumulative_text = 0
    cumulative_integer_bits = 0

    def visit(item: Any, depth: int) -> None:
        nonlocal visited_nodes, cumulative_text, cumulative_integer_bits
        visited_nodes += 1
        if visited_nodes > _MAX_EVIDENCE_NODES or depth > _MAX_EVIDENCE_DEPTH:
            raise ValueError("evidence exceeds canonicalization bounds")
        if type(item) is str:
            if len(item) > _MAX_EVIDENCE_TEXT:
                raise ValueError("evidence text exceeds canonicalization bounds")
            cumulative_text += len(item)
        elif type(item) is int:
            integer_bits = abs(item).bit_length()
            if integer_bits > _MAX_EVIDENCE_INTEGER_BITS:
                raise ValueError("evidence integer exceeds canonicalization bounds")
            cumulative_integer_bits += integer_bits
        elif type(item) is Fraction:
            numerator_bits = abs(item.numerator).bit_length()
            denominator_bits = item.denominator.bit_length()
            if max(numerator_bits, denominator_bits) > _MAX_EVIDENCE_INTEGER_BITS:
                raise ValueError("exact Fraction exceeds canonicalization bounds")
            cumulative_integer_bits += numerator_bits + denominator_bits
        elif isinstance(item, sp.Rational):
            numerator_bits = abs(int(item.p)).bit_length()
            denominator_bits = int(item.q).bit_length()
            if max(numerator_bits, denominator_bits) > _MAX_EVIDENCE_INTEGER_BITS:
                raise ValueError("symbolic rational exceeds canonicalization bounds")
            cumulative_integer_bits += numerator_bits + denominator_bits
        if isinstance(item, sp.Symbol):
            if len(item.name) > _MAX_EVIDENCE_TEXT:
                raise ValueError("symbolic name exceeds canonicalization bounds")
            cumulative_text += len(item.name)
        if cumulative_text > _MAX_EVIDENCE_CUMULATIVE_TEXT:
            raise ValueError("cumulative evidence text exceeds canonicalization bounds")
        if cumulative_integer_bits > _MAX_EVIDENCE_CUMULATIVE_INTEGER_BITS:
            raise ValueError("cumulative exact evidence exceeds canonicalization bounds")

        children: tuple[Any, ...] | None = None
        if isinstance(item, Mapping):
            if len(item) > _MAX_EVIDENCE_COLLECTION:
                raise ValueError("evidence mapping exceeds canonicalization bounds")
            children = tuple(item.keys()) + tuple(item.values())
        elif type(item) in (tuple, list, set, frozenset):
            if len(item) > _MAX_EVIDENCE_COLLECTION:
                raise ValueError("evidence collection exceeds canonicalization bounds")
            children = tuple(item)
        elif isinstance(item, sp.Basic):
            children = tuple(item.args)
        elif is_dataclass(item) and not isinstance(item, type):
            children = tuple(getattr(item, field.name) for field in fields(item))
        if children is None:
            return

        identity = id(item)
        if identity in active:
            raise ValueError("cyclic evidence is not canonical")
        active.add(identity)
        try:
            for child in children:
                visit(child, depth + 1)
        finally:
            active.remove(identity)

    visit(value, 0)


def _safe_canonical_evidence(value: Any) -> tuple[bool, Any]:
    try:
        _bounded_evidence_shape(value)
        canonical = _canonical(value)
        _bounded_evidence_shape(canonical)
        return True, canonical
    except Exception:
        return False, dict(_NONCANONICAL_EVIDENCE)


def _safe_text(value: Any, fallback: str) -> tuple[bool, str]:
    if type(value) is str and len(value) <= _MAX_EVIDENCE_TEXT:
        return True, value
    return False, fallback


def _safe_string_sequence(value: Any) -> tuple[bool, list[str]]:
    if type(value) is not tuple or len(value) > _MAX_EVIDENCE_COLLECTION:
        return False, ["NONCANONICAL_STRING_SEQUENCE"]
    items = value
    if any(
        type(item) is not str or len(item) > _MAX_EVIDENCE_TEXT
        for item in items
    ):
        return False, ["NONCANONICAL_STRING_SEQUENCE"]
    return True, list(items)


def _safe_nonnegative_count(value: Any) -> tuple[bool, int]:
    if type(value) is int and 0 <= value <= 10**12:
        return True, value
    return False, -1


def _safe_exception_label(exc: Exception) -> str:
    try:
        name = type(exc).__name__
        if type(name) is not str or not name:
            name = "Exception"
    except Exception:
        name = "Exception"
    try:
        detail = str(exc)
        if type(detail) is not str:
            detail = ""
    except Exception:
        detail = ""
    detail = detail[:512]
    return name if not detail else f"{name}: {detail}"


def _receipt(numerator: int, gate: str, reason: str) -> dict[str, Any]:
    """Create an exact receipt; impossible counts are evidence corruption."""

    denominator = GATE_DENOMINATORS[gate]
    in_range = type(numerator) is int and 0 <= numerator <= denominator
    return {
        "passed": bool(in_range and numerator == denominator),
        "numerator": numerator,
        "denominator": denominator,
        "reason": reason,
        "integrity_error": None if in_range else "COUNT_OUT_OF_RANGE",
    }


def _challenge_contract_valid(goal: object) -> bool:
    """Validate a frozen core challenge without treating refusal as evidence."""

    if type(goal) is not GoalSpec:
        return False
    try:
        if goal.family in NEW_V0_20_FAMILIES:
            result = validate_v0_20_goal_contract(goal)
        else:
            result = validate_historical_goal_contract(goal.solver_visible())
        return type(result) is VerificationResult and result.passed is True
    except Exception:
        return False


def _challenge_domain_receipt(
    corpus: Mapping[str, Sequence[GoalSpec]],
) -> dict[str, Any]:
    """Return the engine-level receipt for the complete frozen core domain."""

    manifest = _frozen_corpus_manifest_receipt(corpus)
    if manifest["valid"] is not True:
        return _receipt(
            0,
            "closed_challenge_domain_valid",
            "the exact preregistered corpus manifest and every closed challenge contract must validate",
        )
    try:
        goals = [goal for split in _FROZEN_SPLIT_NAMES for goal in corpus[split]]
    except Exception:
        goals = []
    valid_count = sum(_challenge_contract_valid(goal) for goal in goals)
    return _receipt(
        valid_count,
        "closed_challenge_domain_valid",
        "the exact preregistered corpus manifest and every closed challenge contract must validate",
    )


_HISTORICAL_ORACLE_MODULE = "experiments.pct_goal_solver.historical_oracles"
_HISTORICAL_ORACLE_IMPORT_ALLOWLIST = frozenset({
    (0, "__future__"),
    (0, "dataclasses"),
    (0, "fractions"),
    (0, "itertools"),
    (0, "math"),
    (0, "typing"),
    (0, "sympy"),
    (1, "model"),
})
_HISTORICAL_MODULE_GLOBALS = MappingProxyType({"math": math, "sp": sp})
_HISTORICAL_MODULE_API_SURFACE = MappingProxyType({
    "math": MappingProxyType({
        "hypot": math.hypot,
        "isfinite": math.isfinite,
        "pi": math.pi,
    }),
    "sp": MappingProxyType({
        "Basic": sp.Basic,
        "Matrix": sp.Matrix,
        "Rational": sp.Rational,
        "Symbol": sp.Symbol,
        "cancel": sp.cancel,
        "diff": sp.diff,
        "expand": sp.expand,
        "pi": sp.pi,
        "simplify": sp.simplify,
        "sympify": sp.sympify,
    }),
})
_MISSING_HISTORICAL_DEPENDENCY = object()
_HISTORICAL_EXTERNAL_CALLABLE_ALLOWLIST = (
    Fraction,
    HistoricalReference,
    Mapping,
    permutations,
)


def _historical_live_dependency_key() -> tuple[tuple[str, str, int, int], ...]:
    """Cheaply fingerprint the complete live Python-function dependency graph."""

    pending = [
        build_historical_reference,
        historical_candidate_satisfies_reference,
    ]
    visited: set[int] = set()
    rows: list[tuple[str, str, int, int]] = []
    root_globals = getattr(build_historical_reference, "__globals__", {})
    for module_name, reviewed_surface in _HISTORICAL_MODULE_API_SURFACE.items():
        live_module = root_globals.get(
            module_name,
            _MISSING_HISTORICAL_DEPENDENCY,
        )
        for attribute_name in reviewed_surface:
            live_attribute = getattr(
                live_module,
                attribute_name,
                _MISSING_HISTORICAL_DEPENDENCY,
            )
            rows.append((
                "@module-api",
                f"{module_name}.{attribute_name}",
                id(live_attribute),
                id(type(live_attribute)),
            ))
    while pending:
        function = pending.pop()
        if id(function) in visited:
            continue
        visited.add(id(function))
        module_name = getattr(function, "__module__", "")
        qualname = getattr(function, "__qualname__", "")
        code = getattr(function, "__code__", None)
        rows.append((module_name, qualname, id(function), id(code)))
        globals_map = getattr(function, "__globals__", {})
        for name in getattr(code, "co_names", ()):
            dependency = globals_map.get(name)
            if inspect.isfunction(dependency):
                pending.append(dependency)
            elif (
                name in _HISTORICAL_MODULE_GLOBALS
                or isinstance(dependency, ModuleType)
                or callable(dependency)
            ):
                rows.append((
                    "@global",
                    f"{module_name}.{qualname}:{name}",
                    id(dependency),
                    id(type(dependency)),
                ))
    return tuple(sorted(rows))


@lru_cache(maxsize=8)
def _historical_reference_independence_receipt_cached(
    _dependency_key: tuple[tuple[str, str, int, int], ...],
) -> dict[str, Any]:
    """Establish structural independence instead of trusting result flags.

    Historical references may use only standard mathematical dependencies and
    the public goal model.  In particular, importing the planner, registry,
    operators, or terminal verifiers would make the purported oracle circular.
    """

    try:
        if (
            build_historical_reference.__module__ != _HISTORICAL_ORACLE_MODULE
            or historical_candidate_satisfies_reference.__module__
            != _HISTORICAL_ORACLE_MODULE
        ):
            raise ValueError("historical reference callable module mismatch")
        module = inspect.getmodule(build_historical_reference)
        if module is None or module.__name__ != _HISTORICAL_ORACLE_MODULE:
            raise ValueError("historical reference module is unavailable")
        module_file = Path(inspect.getsourcefile(module) or "").resolve()
        if not module_file.is_file():
            raise ValueError("historical reference source file is unavailable")
        source = inspect.getsource(module)
        tree = ast.parse(source)
        imports: set[tuple[int, str]] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update((0, alias.name) for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add((node.level, node.module or ""))
        if not imports <= _HISTORICAL_ORACLE_IMPORT_ALLOWLIST:
            raise ValueError("historical reference imports unreviewed dependencies")
        pending = [
            build_historical_reference,
            historical_candidate_satisfies_reference,
        ]
        visited: set[int] = set()
        dependency_names: list[str] = []
        while pending:
            function = pending.pop()
            if id(function) in visited:
                continue
            visited.add(id(function))
            if (
                not inspect.isfunction(function)
                or function.__module__ != _HISTORICAL_ORACLE_MODULE
                or Path(inspect.getsourcefile(function) or "").resolve()
                != module_file
            ):
                raise ValueError("historical reference has an external live callable")
            dependency_names.append(function.__qualname__)
            for name in function.__code__.co_names:
                dependency = function.__globals__.get(name)
                if name in _HISTORICAL_MODULE_GLOBALS:
                    if dependency is not _HISTORICAL_MODULE_GLOBALS[name]:
                        raise ValueError(
                            "historical reference module global identity mismatch"
                        )
                elif inspect.isfunction(dependency):
                    if dependency.__module__ != _HISTORICAL_ORACLE_MODULE:
                        raise ValueError(
                            "historical reference invokes an external Python callable"
                        )
                    pending.append(dependency)
                elif isinstance(dependency, ModuleType):
                    raise ValueError(
                        "historical reference uses an unreviewed module object"
                    )
                elif callable(dependency) and not any(
                    dependency is reviewed
                    for reviewed in _HISTORICAL_EXTERNAL_CALLABLE_ALLOWLIST
                ):
                    raise ValueError(
                        "historical reference uses an unreviewed external callable"
                    )
        root_globals = build_historical_reference.__globals__
        for module_name, reviewed_surface in _HISTORICAL_MODULE_API_SURFACE.items():
            live_module = root_globals.get(module_name)
            if live_module is not _HISTORICAL_MODULE_GLOBALS[module_name]:
                raise ValueError("historical reference module identity drifted")
            for attribute_name, reviewed_attribute in reviewed_surface.items():
                if getattr(
                    live_module,
                    attribute_name,
                    _MISSING_HISTORICAL_DEPENDENCY,
                ) is not reviewed_attribute:
                    raise ValueError(
                        "historical reference reviewed module API drifted"
                    )
        source_sha256 = _sha256_bytes(source.encode("utf-8"))
        return {
            "established": True,
            "method_id": "bounded-reference-v1",
            "module": _HISTORICAL_ORACLE_MODULE,
            "source_sha256": source_sha256,
            "build_callable_sha256": callable_contract_digest(
                build_historical_reference,
                implementation_id="pct.historical-oracle.build.v1",
            ),
            "matching_callable_sha256": callable_contract_digest(
                historical_candidate_satisfies_reference,
                implementation_id="pct.historical-oracle.match.v1",
            ),
            "live_dependency_functions": tuple(sorted(dependency_names)),
            "reviewed_imports": tuple(
                f"{'.' * level}{module_name}"
                for level, module_name in sorted(imports)
            ),
        }
    except Exception as exc:
        return {
            "established": False,
            "method_id": "bounded-reference-v1",
            "module": _HISTORICAL_ORACLE_MODULE,
            "source_sha256": None,
            "build_callable_sha256": None,
            "matching_callable_sha256": None,
            "live_dependency_functions": (),
            "reviewed_imports": (),
            "reason": _safe_exception_label(exc),
        }


def _historical_reference_independence_receipt() -> dict[str, Any]:
    return deepcopy(
        _historical_reference_independence_receipt_cached(
            _historical_live_dependency_key()
        )
    )


def _build_campaign_oracle(goal: GoalSpec) -> dict[str, Any]:
    """Build an implementation-independent assessment for one core goal."""

    if goal.family in NEW_V0_20_FAMILIES:
        return build_case_oracle(goal)
    if not _challenge_contract_valid(goal):
        try:
            signatures = case_signatures(goal)
            exact_fingerprint = signatures.exact_sha256
            nuisance_fingerprint = signatures.nuisance_sha256
            nuisance_relation = signatures.nuisance_relation
        except Exception:
            exact_fingerprint = None
            nuisance_fingerprint = None
            nuisance_relation = "UNAVAILABLE_INVALID_GOAL"
        return {
            "goal_id": goal.goal_id if type(goal.goal_id) is str else "INVALID_GOAL_ID",
            "family": goal.family if type(goal.family) is str else "INVALID_FAMILY",
            "content_fingerprint": exact_fingerprint,
            "nuisance_fingerprint": nuisance_fingerprint,
            "nuisance_relation": nuisance_relation,
            "control_kind": None,
            "authoritative": False,
            "authority_kind": "INVALID_CHALLENGE_CONTRACT",
            "oracle_availability": "INVALID_CHALLENGE",
            "oracle_method": "CLOSED_HISTORICAL_GOAL_CONTRACT",
            "expected_verdict": "INVALID",
            "reason": "HISTORICAL_GOAL_CONTRACT_INVALID",
            "certificate": _canonical({"contract_valid": False}),
        }
    reference = build_historical_reference(goal.solver_visible())
    independence = _historical_reference_independence_receipt()
    signatures = case_signatures(goal)
    reference_schema_valid = bool(
        type(reference) is HistoricalReference
        and type(reference.authoritative) is bool
        and reference.authoritative is True
        and type(reference.implementation_independent) is bool
        and reference.implementation_independent is True
        and reference.method_id == independence["method_id"]
        and reference.expected_verdict in {"PASS", "NOT_APPLICABLE", "INVALID"}
        and (
            (reference.expected_verdict == "PASS" and reference.candidate_value is not None)
            or (reference.expected_verdict != "PASS" and reference.candidate_value is None)
        )
    )
    authoritative = bool(
        independence["established"] is True
        and reference_schema_valid
    )
    return {
        "goal_id": goal.goal_id,
        "family": goal.family,
        "content_fingerprint": signatures.exact_sha256,
        "nuisance_fingerprint": signatures.nuisance_sha256,
        "nuisance_relation": signatures.nuisance_relation,
        "control_kind": None,
        "authoritative": authoritative,
        "authority_kind": "INDEPENDENT_MATHEMATICAL_ORACLE",
        "oracle_availability": "AVAILABLE" if authoritative else "UNAVAILABLE",
        "oracle_method": reference.method_id,
        "expected_verdict": reference.expected_verdict,
        "reason": "" if authoritative else "HISTORICAL_REFERENCE_NOT_INDEPENDENT",
        "certificate": _canonical({
            "candidate_value": reference.candidate_value,
            "implementation_independent": reference.implementation_independent,
            "independence_receipt": independence,
        }),
    }


def _blind_input_semantic_types(goal_visible):
    return replace(
        goal_visible,
        inputs={
            key: replace(artifact, semantic_type="BLINDED_INPUT_TYPE")
            for key, artifact in goal_visible.inputs.items()
        },
    )


def _error_trace(goal: GoalSpec, mode_name: str, exc: Exception) -> SolveTrace:
    error_label = _safe_exception_label(exc)
    return SolveTrace(
        goal_id=goal.goal_id,
        mode=mode_name,
        operator_path=(),
        expanded_state_count=0,
        primitive_execution_count=0,
        macro_ids=(),
        candidate_artifact=None,
        verifier_chain=(),
        falsification_events=(("CONTAINED_EXCEPTION", error_label.split(":", 1)[0]),),
        final_verdict="ERROR",
        failure_reason=error_label,
    )


def _safe_solve(
    goal: GoalSpec,
    registry: Mapping[str, OperatorSpec],
    *,
    mode_name: str,
    typing_mode: str,
    compatibility_model: CompatibilityModel | None = None,
    macros: Sequence[Any] = (),
) -> SolveTrace:
    visible = goal.solver_visible()
    if typing_mode != "EXPLICIT":
        visible = _blind_input_semantic_types(visible)
    try:
        return solve(
            visible,
            registry,
            typing_mode=typing_mode,
            compatibility_model=compatibility_model if typing_mode != "EXPLICIT" else None,
            macros=macros,
        )
    except Exception as exc:
        return _error_trace(goal, mode_name, exc)


def _stable_verifier_evidence(evidence: Sequence[tuple[str, Any]]) -> tuple[tuple[str, Any], ...]:
    stable: list[tuple[str, Any]] = []
    for key, value in evidence:
        if key == "artifact_id" and isinstance(value, str) and value.startswith("derived:"):
            parts = value.split(":", 2)
            stable.append((key, {
                "status": "LEGACY_NONCONTENT_ID_OMITTED",
                "producer_operator": parts[1] if len(parts) > 1 else "UNKNOWN",
            }))
        else:
            stable.append((key, value))
    return tuple(stable)


def _verifier_rows_checked(trace: SolveTrace) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    complete = True
    chain = trace.verifier_chain
    if type(chain) is not tuple or len(chain) > _MAX_EVIDENCE_COLLECTION:
        return ([{"evidence": dict(_NONCANONICAL_EVIDENCE)}], False)
    for result in chain:
        try:
            passed = type(result.passed) is bool and result.passed
            verifier_ok, verifier_class = _safe_text(
                result.verifier_class,
                "NONCANONICAL_VERIFIER_CLASS",
            )
            reason_ok, reason = _safe_text(result.reason, "NONCANONICAL_VERIFIER_REASON")
            stage_ok, stage = _safe_text(
                getattr(result, "stage", "UNSPECIFIED"),
                "NONCANONICAL_VERIFIER_STAGE",
            )
            subject_ok, subject_id = _safe_text(
                getattr(result, "subject_id", ""),
                "NONCANONICAL_VERIFIER_SUBJECT",
            )
            residual = result.residual
            residual_ok = residual is None or (
                type(residual) in (int, float) and math.isfinite(residual)
            )
            evidence_ok, evidence = _safe_canonical_evidence(
                _stable_verifier_evidence(result.evidence)
            )
            row_ok = bool(
                type(result.passed) is bool
                and verifier_ok
                and reason_ok
                and stage_ok
                and subject_ok
                and residual_ok
                and evidence_ok
            )
            rows.append({
                "passed": bool(passed),
                "verifier_class": verifier_class,
                "reason": reason,
                "residual": residual if residual_ok else None,
                "evidence": evidence,
                "stage": stage,
                "subject_id": subject_id,
            })
            complete = complete and row_ok
        except Exception:
            rows.append({"evidence": dict(_NONCANONICAL_EVIDENCE)})
            complete = False
    return rows, complete


def _verifier_rows(trace: SolveTrace) -> list[dict[str, Any]]:
    return _verifier_rows_checked(trace)[0]


def _candidate_contract_matches(goal: GoalSpec, candidate: Artifact | None) -> bool:
    try:
        return bool(
            type(candidate) is Artifact
            and type(candidate.semantic_type) is str
            and type(candidate.representation_class) is str
            and type(candidate.exactness_class) is str
            and candidate.semantic_type == goal.target.semantic_type
            and candidate.representation_class == goal.target.representation_class
            and (
                goal.target.exactness_class is None
                or candidate.exactness_class == goal.target.exactness_class
            )
        )
    except Exception:
        return False


def _terminal_authority(goal: GoalSpec, trace: SolveTrace) -> VerificationResult:
    candidate = trace.candidate_artifact
    if candidate is None:
        return VerificationResult(False, goal.required_verifier_class, "terminal candidate is absent")
    if goal.family in NEW_V0_20_FAMILIES:
        return verify_v0_20_goal(goal, candidate)
    return verify_historical_goal(goal.solver_visible(), candidate)


def _oracle_integrity_valid(goal: GoalSpec, oracle: Mapping[str, Any]) -> bool:
    """Require the supplied report oracle to equal a fresh independent build."""

    try:
        return type(oracle) is dict and oracle == _build_campaign_oracle(goal)
    except Exception:
        return False


def _candidate_matches_oracle(goal: GoalSpec, candidate: Artifact | None) -> bool:
    if candidate is None:
        return False
    if goal.family not in NEW_V0_20_FAMILIES:
        return historical_candidate_satisfies_reference(
            goal.solver_visible(),
            candidate.value,
        )
    try:
        independent = build_independent_oracle(
            family=goal.family,
            inputs={key: artifact.value for key, artifact in goal.inputs.items()},
            constraints=dict(goal.constraints),
            tolerance=goal.allowed_numeric_tolerance,
        )
        if not independent.authoritative or independent.expected_verdict != "PASS":
            return False
        projection = asdict(candidate.value)
        return candidate_matches_independent_oracle(
            family=goal.family,
            candidate=projection,
            oracle_certificate=independent.certificate,
        )
    except (TypeError, ValueError):
        return False


def _bounded_refusal_schema(refusal: object) -> bool:
    """Accept only the exact, bounded public refusal record."""

    return bool(
        type(refusal) is Refusal
        and type(refusal.code) is str
        and 0 < len(refusal.code) <= _MAX_EVIDENCE_TEXT
        and type(refusal.reason) is str
        and 0 < len(refusal.reason) <= _MAX_EVIDENCE_TEXT
        and (
            refusal.operator_id is None
            or (
                type(refusal.operator_id) is str
                and 0 < len(refusal.operator_id) <= _MAX_EVIDENCE_TEXT
            )
        )
    )


def _semantic_certificate(
    trace: SolveTrace,
    *,
    terminal_verified: bool,
) -> dict[str, Any]:
    candidate = trace.candidate_artifact
    lineage = getattr(trace, "candidate_lineage", None)
    refusal = getattr(trace, "refusal", None)
    raw_obligations = getattr(trace, "derived_obligations", ())
    obligations_container_ok = type(raw_obligations) is tuple
    obligations = raw_obligations if obligations_container_ok else ()
    raw_macro_bindings = getattr(trace, "macro_bindings", ())
    macro_container_ok = type(raw_macro_bindings) is tuple
    macro_bindings = raw_macro_bindings if macro_container_ok else ()
    if candidate is None:
        candidate_ok, normalized_candidate = True, None
    elif not terminal_verified:
        candidate_ok, normalized_candidate = False, dict(_NONCANONICAL_EVIDENCE)
    else:
        candidate_ok, normalized_candidate = _safe_canonical_evidence(
            candidate.value
        )
    if refusal is None:
        refusal_ok, normalized_refusal = True, None
    elif _bounded_refusal_schema(refusal):
        refusal_ok, normalized_refusal = _safe_canonical_evidence(refusal)
    else:
        refusal_ok, normalized_refusal = False, dict(_NONCANONICAL_EVIDENCE)
    lineage_ok, normalized_lineage = (
        (True, None) if lineage is None else _safe_canonical_evidence(lineage)
    )
    obligations_ok, normalized_obligations = _safe_canonical_evidence(obligations)
    macro_ok, normalized_macro_bindings = _safe_canonical_evidence(macro_bindings)
    verifier_rows, verifier_ok = _verifier_rows_checked(trace)
    failure_ok, safe_failure_reason = _safe_text(
        trace.failure_reason,
        "NONCANONICAL_FAILURE_REASON",
    )
    verdict_ok, safe_verdict = _safe_text(
        trace.final_verdict,
        "NONCANONICAL_VERDICT",
    )
    projections_ok = bool(
        candidate_ok
        and refusal_ok
        and lineage_ok
        and obligations_ok
        and obligations_container_ok
        and macro_ok
        and macro_container_ok
        and verifier_ok
        and failure_ok
        and verdict_ok
    )
    complete = bool(
        projections_ok
        and (
            (safe_verdict == "PASS" and lineage is not None and bool(verifier_rows))
            or (safe_verdict != "PASS" and refusal is not None)
        )
    )
    return {
        "complete": complete,
        "verdict": safe_verdict,
        "normalized_candidate": normalized_candidate,
        "structured_refusal": normalized_refusal if refusal is not None else (
            safe_failure_reason if safe_verdict != "PASS" else None
        ),
        "verifier_chain": verifier_rows,
        "candidate_lineage": normalized_lineage if lineage is not None else None,
        "derived_obligations": normalized_obligations,
        "macro_bindings": normalized_macro_bindings,
    }


def _nonpass_refusal_matches(
    goal: GoalSpec,
    trace: SolveTrace,
    expected_verdict: object,
    *,
    compatibility_model: CompatibilityModel | None = None,
    expected_typing_mode: str | None = None,
) -> bool:
    """Bind a non-PASS outcome to a fresh authoritative planner execution."""

    try:
        refusal = trace.refusal
        if (
            expected_verdict != "NOT_APPLICABLE"
            or trace.final_verdict != expected_verdict
            or trace.candidate_artifact is not None
            or not _bounded_refusal_schema(refusal)
            or refusal.code != "GOAL_NOT_APPLICABLE"
            or type(trace.failure_reason) is not str
            or trace.failure_reason != refusal.reason
            or type(trace.operator_path) is not tuple
            or not trace.operator_path
            or refusal.operator_id != trace.operator_path[-1]
        ):
            return False
        registry = _authoritative_registry()
        specification = registry.get(refusal.operator_id)
        if (
            type(specification) is not OperatorSpec
            or specification.output != goal.target.artifact_type
        ):
            return False
        typing_mode = _validated_trace_typing_mode(
            goal,
            trace,
            registry,
            compatibility_model,
        )
        if typing_mode is None or (
            expected_typing_mode is not None
            and typing_mode != expected_typing_mode
        ):
            return False
        replay = _safe_solve(
            goal,
            registry,
            mode_name=f"{typing_mode}/PRIMITIVE",
            typing_mode=typing_mode,
            compatibility_model=compatibility_model,
        )
        return type(replay) is SolveTrace and replay == trace
    except Exception:
        return False


def _is_sha256(value: object) -> bool:
    return bool(
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _prefixed_sha256(value: object, prefix: str) -> bool:
    return bool(type(value) is str and value.startswith(prefix) and _is_sha256(value[len(prefix):]))


_SHORTCUT_PROOF_KEYS = frozenset({
    "status",
    "proven_no_shortcut",
    "proof_validated",
    "proof_digest",
    "registry_digest",
    "goal_contract_digest",
    "obligation_digest",
    "explored_state_count",
    "witness",
    "counterexample",
    "reason",
})


def _shortcut_proof_complete(
    proof: object,
    goal: GoalSpec,
    registry: Mapping[str, OperatorSpec],
) -> bool:
    """Require a complete, live-bound, replay-validated no-shortcut proof."""

    try:
        if (
            type(proof) is not dict
            or set(proof) != set(_SHORTCUT_PROOF_KEYS)
            or proof["status"] != "PROVED"
            or proof["proven_no_shortcut"] is not True
            or proof["proof_validated"] is not True
            or any(
                not _is_sha256(proof[key])
                for key in (
                    "proof_digest",
                    "registry_digest",
                    "goal_contract_digest",
                    "obligation_digest",
                )
            )
            or type(proof["explored_state_count"]) is not int
            or proof["explored_state_count"] <= 0
            or type(proof["witness"]) is not dict
            or proof["counterexample"] is not None
            or type(proof["reason"]) is not str
            or not proof["reason"]
            or len(proof["reason"]) > _MAX_EVIDENCE_TEXT
            or not _challenge_contract_valid(goal)
        ):
            return False
        expected = prove_no_same_class_shortcut(goal, registry)
        return type(expected) is dict and expected == proof
    except Exception:
        return False


@lru_cache(maxsize=1)
def _authoritative_registry() -> Mapping[str, OperatorSpec]:
    return MappingProxyType(dict(build_v0_20_operator_registry()))


def _validated_trace_typing_mode(
    goal: GoalSpec,
    trace: SolveTrace,
    registry: Mapping[str, OperatorSpec],
    compatibility_model: CompatibilityModel | None,
) -> str | None:
    if type(trace.mode) is not str:
        return None
    parts = trace.mode.split("/")
    if len(parts) != 2 or parts[1] != "PRIMITIVE":
        return None
    typing_mode = parts[0]
    routing = trace.routing_receipt
    if typing_mode == "EXPLICIT":
        return typing_mode if routing is None else None
    if typing_mode not in {"INFERRED", "HYBRID"} or type(routing) is not RoutingReceipt:
        return None
    if routing.typing_mode != typing_mode:
        return None

    rows = routing.inferred_root_types
    if (
        type(rows) is not tuple
        or rows != tuple(sorted(rows, key=lambda row: row[0] if type(row) is tuple and row else ""))
        or any(
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not str
            or not row[0]
            or type(row[1]) is not ArtifactType
            for row in rows
        )
    ):
        return None
    inferred = dict(rows)
    if len(inferred) != len(rows) or set(inferred) != set(goal.inputs):
        return None
    if any(
        artifact_type.representation_class != goal.inputs[key].representation_class
        or artifact_type.exactness_class != goal.inputs[key].exactness_class
        for key, artifact_type in inferred.items()
    ):
        return None

    order = routing.ordered_operator_ids
    if (
        type(order) is not tuple
        or any(type(operator_id) is not str or not operator_id for operator_id in order)
        or len(order) != len(set(order))
        or set(order) != set(registry)
        or len(order) != len(registry)
    ):
        return None
    ambiguous = routing.ambiguous_input_keys
    if (
        type(ambiguous) is not tuple
        or any(type(key) is not str or not key for key in ambiguous)
        or len(ambiguous) != len(set(ambiguous))
        or not set(ambiguous) <= set(goal.inputs)
        or ambiguous
    ):
        return None
    if not _is_sha256(routing.compatibility_model_digest):
        return None
    expected_decision_digest = canonical_sha256(
        {
            "inferred_root_types": rows,
            "ordered_operator_ids": order,
            "ambiguous_input_keys": ambiguous,
            "compatibility_model_digest": routing.compatibility_model_digest,
        },
        domain="pct-routing-decision-v1",
    )
    if routing.decision_digest != expected_decision_digest:
        return None
    if type(compatibility_model) is not CompatibilityModel:
        return None
    blinded_inputs = {
        key: replace(artifact, semantic_type="BLINDED_INPUT_TYPE")
        for key, artifact in goal.inputs.items()
    }
    try:
        authoritative = authoritative_routing_decision(
            compatibility_model,
            blinded_inputs,
            registry,
        )
    except Exception:
        return None
    if (
        rows != authoritative.inferred_root_types
        or order != authoritative.ordered_operator_ids
        or ambiguous != authoritative.ambiguous_input_keys
        or routing.compatibility_model_digest != authoritative.compatibility_model_digest
        or routing.decision_digest != authoritative.decision_digest
    ):
        return None
    return typing_mode


def _execution_receipt_complete(
    goal: GoalSpec,
    trace: SolveTrace,
    compatibility_model: CompatibilityModel | None = None,
    *,
    expected_typing_mode: str | None = None,
    require_ordered_stages: bool = False,
) -> bool:
    """Replay every planner-owned fact required to credit a PASS.

    Candidate correctness alone cannot establish that the planner executed the
    claimed route.  This validator binds the exact goal and typing mode, root
    identities, routing decision, operator DAG, materialized artifacts,
    verifier chain, obligation witnesses, candidate lineage, and registry to a
    fresh execution of every recorded primitive.
    """

    try:
        if type(goal) is not GoalSpec or type(trace) is not SolveTrace:
            return False
        if trace.goal_id != goal.goal_id:
            return False
        obligation = goal.lineage_obligation
        required_types = () if obligation is None else obligation.ordered_stage_types
        if (
            trace.final_verdict != "PASS"
            or trace.refusal is not None
            or trace.failure_reason != ""
            or trace.macro_ids != ()
            or trace.macro_bindings != ()
        ):
            return False
        if require_ordered_stages and not required_types:
            return False
        candidate = trace.candidate_artifact
        receipt = trace.candidate_lineage
        if type(candidate) is not Artifact or type(receipt) is not LineageReceipt:
            return False
        if candidate.artifact_type != goal.target.artifact_type:
            return False
        if (
            not trace.verifier_chain
            or type(trace.verifier_chain[-1]) is not VerificationResult
            or trace.verifier_chain[-1].passed is not True
            or trace.verifier_chain[-1].verifier_class != goal.required_verifier_class
        ):
            return False
        registry = _authoritative_registry()
        typing_mode = _validated_trace_typing_mode(
            goal,
            trace,
            registry,
            compatibility_model,
        )
        if typing_mode is None:
            return False
        if (
            expected_typing_mode is not None
            and typing_mode != expected_typing_mode
        ):
            return False
        # Derivation replay proves that recorded outputs follow from recorded
        # parents, but it cannot reconstruct planner search accounting or
        # falsification events.  Bind *every* SolveTrace field—including all
        # counters and events—by rerunning the deterministic authoritative
        # primitive solve and requiring exact dataclass equality.
        authoritative_replay = _safe_solve(
            goal,
            registry,
            mode_name=f"{typing_mode}/PRIMITIVE",
            typing_mode=typing_mode,
            compatibility_model=compatibility_model,
        )
        if type(authoritative_replay) is not SolveTrace or authoritative_replay != trace:
            return False
        producer = trace.derivations[-1] if trace.derivations else None
        if type(producer) is not DerivationStep:
            return False
        producer_specification = registry.get(producer.operator_id)
        if producer_specification is not None:
            if (
                goal.target.objective not in producer_specification.objectives
                or producer_specification.output != goal.target.artifact_type
            ):
                return False
        else:
            comparison = _PLANNER_COMPARISON_CONTRACTS.get(goal.family)
            if (
                comparison is None
                or comparison.operator_id != producer.operator_id
                or comparison.objective != goal.target.objective
                or comparison.output != goal.target.artifact_type
            ):
                return False
        if receipt.registry_digest != _planner_registry_digest(registry):
            return False
        # G4/G5 terminal candidates are constructed by closed planner-owned
        # comparison contracts rather than ordinary registry operators.  Their
        # supplemental derivation steps therefore cannot be replayed through
        # ``OperatorSpec`` below.  Replay the complete solve instead, requiring
        # exact equality of every root, step, materialization, verifier,
        # lineage receipt, obligation, routing receipt, and work counter.
        if any(step.operator_id not in registry for step in trace.derivations):
            return True
        expected_obligation_digest = canonical_sha256(
            {"goal_id": goal.goal_id, "lineage_obligation": obligation},
            domain="pct-goal-obligation-v1",
        )
        if receipt.obligation_digest != expected_obligation_digest:
            return False

        # Root origins are rebuilt from exactly the view supplied by this
        # campaign.  In inferred/hybrid runs every semantic label was blinded
        # before solve(), so those labels must also be blinded for identity
        # replay here.
        root_inputs = goal.inputs
        routing = trace.routing_receipt
        if typing_mode != "EXPLICIT":
            root_inputs = {
                key: replace(artifact, semantic_type="BLINDED_INPUT_TYPE")
                for key, artifact in goal.inputs.items()
            }
        tracked_roots = dict(track_roots(root_inputs))
        expected_roots = {
            key: tracked.origin
            for key, tracked in tracked_roots.items()
        }
        if (
            type(trace.root_origins) is not tuple
            or len(trace.root_origins) != len(expected_roots)
            or any(type(origin) is not RootOrigin for origin in trace.root_origins)
        ):
            return False
        roots_by_key = {origin.input_key: origin for origin in trace.root_origins}
        if len(roots_by_key) != len(trace.root_origins) or roots_by_key != expected_roots:
            return False
        root_keys_by_instance = {
            origin.instance_id: frozenset((origin.input_key,))
            for origin in trace.root_origins
        }
        if len(root_keys_by_instance) != len(trace.root_origins):
            return False

        effective_root_types = {
            key: artifact.artifact_type for key, artifact in goal.inputs.items()
        }
        if typing_mode != "EXPLICIT":
            if type(routing) is not RoutingReceipt:
                return False
            inferred_rows = routing.inferred_root_types
            if type(inferred_rows) is not tuple:
                return False
            inferred = dict(inferred_rows)
            if len(inferred) != len(inferred_rows) or set(inferred) != set(goal.inputs):
                return False
            effective_root_types = inferred
        type_by_instance = {
            origin.instance_id: effective_root_types[origin.input_key]
            for origin in trace.root_origins
        }
        artifact_by_instance = {
            tracked.instance_id: tracked.artifact
            for tracked in tracked_roots.values()
        }

        if type(trace.derivations) is not tuple or not trace.derivations:
            return False
        materialized = trace.derived_artifacts
        if (
            type(materialized) is not tuple
            or len(materialized) != len(trace.derivations)
            or any(type(record) is not DerivedArtifactRecord for record in materialized)
        ):
            return False
        record_by_step = {record.derivation_step_id: record for record in materialized}
        if len(record_by_step) != len(materialized):
            return False
        step_by_id: dict[str, DerivationStep] = {}
        step_by_output: dict[str, DerivationStep] = {}
        roots_by_instance = dict(root_keys_by_instance)
        parents_by_output: dict[str, tuple[str, ...]] = {}
        for step in trace.derivations:
            if type(step) is not DerivationStep:
                return False
            specification = registry.get(step.operator_id)
            record = record_by_step.get(step.step_id)
            if (
                not step.step_id
                or not step.output_instance_id
                or not step.operator_id
                or specification is None
                or record is None
                or record.instance_id != step.output_instance_id
                or record.artifact.artifact_id != step.output_artifact_id
                or record.artifact.artifact_type != step.output_type
                or specification.output != step.output_type
                or not _prefixed_sha256(step.step_id, "step:")
                or not _prefixed_sha256(step.output_instance_id, "derived:")
                or step.step_id in step_by_id
                or step.output_instance_id in roots_by_instance
                or type(step.input_bindings) is not tuple
                or not step.input_bindings
                or step.input_bindings != tuple(sorted(step.input_bindings))
                or type(step.verifier) is not VerificationResult
                or step.verifier.passed is not True
                or step.verifier.stage != "OPERATOR"
                or step.verifier.subject_id != step.operator_id
            ):
                return False
            required_ports = {
                port.port_id: port.artifact_type for port in specification.input_ports
            }
            if len(step.input_bindings) != len(required_ports):
                return False
            ports: set[str] = set()
            parent_instances: list[str] = []
            computed_roots: set[str] = set()
            for binding in step.input_bindings:
                if type(binding) is not tuple or len(binding) != 2:
                    return False
                port, parent_instance = binding
                if (
                    type(port) is not str
                    or not port
                    or port in ports
                    or port not in required_ports
                    or type(parent_instance) is not str
                    or parent_instance not in roots_by_instance
                    or type_by_instance.get(parent_instance) != required_ports[port]
                ):
                    return False
                ports.add(port)
                parent_instances.append(parent_instance)
                computed_roots.update(roots_by_instance[parent_instance])
            if step.root_input_keys != frozenset(computed_roots):
                return False

            binding_by_port = dict(step.input_bindings)
            execution_inputs: dict[str, Artifact] = {}
            for port in specification.input_ports:
                parent = artifact_by_instance[binding_by_port[port.port_id]]
                if parent.artifact_type == port.artifact_type:
                    execution_inputs[port.port_id] = parent
                else:
                    execution_inputs[port.port_id] = Artifact(
                        artifact_id=parent.artifact_id,
                        semantic_type=port.artifact_type.semantic_type,
                        representation_class=port.artifact_type.representation_class,
                        exactness_class=port.artifact_type.exactness_class,
                        value=parent.value,
                        metadata=parent.metadata,
                        provenance=parent.provenance,
                    )
            replay_applicability = specification.applicability(
                deepcopy(execution_inputs),
                deepcopy(tuple(goal.constraints)),
            )
            if (
                type(replay_applicability) is not Applicability
                or not replay_applicability.applicable
            ):
                return False
            replay_output = specification.execute(
                deepcopy(execution_inputs),
                deepcopy(tuple(goal.constraints)),
            )
            if (
                type(replay_output) is not Artifact
                or isinstance(replay_output, OperatorFailure)
                or replay_output != record.artifact
            ):
                return False
            replay_verifier = specification.verify(
                deepcopy(tuple(execution_inputs.values())),
                deepcopy(replay_output),
            )
            if type(replay_verifier) is not VerificationResult:
                return False
            replay_verifier = replace(
                replay_verifier,
                stage="OPERATOR",
                subject_id=step.operator_id,
            )
            if replay_verifier != step.verifier:
                return False

            expected_output_instance = "derived:" + canonical_sha256(
                {
                    "operator_id": step.operator_id,
                    "parents": step.input_bindings,
                    "artifact": {
                        "artifact_id": record.artifact.artifact_id,
                        "artifact_type": record.artifact.artifact_type,
                        "value": record.artifact.value,
                        "metadata": record.artifact.metadata,
                    },
                },
                domain="pct-derived-instance-v1",
            )
            if step.output_instance_id != expected_output_instance:
                return False
            expected_step_id = "step:" + canonical_sha256(
                {
                    "operator_id": step.operator_id,
                    "parents": step.input_bindings,
                    "output_instance_id": step.output_instance_id,
                    "verifier": step.verifier,
                },
                domain="pct-derivation-step-v1",
            )
            if step.step_id != expected_step_id:
                return False
            step_by_id[step.step_id] = step
            step_by_output[step.output_instance_id] = step
            roots_by_instance[step.output_instance_id] = step.root_input_keys
            type_by_instance[step.output_instance_id] = step.output_type
            artifact_by_instance[step.output_instance_id] = record.artifact
            parents_by_output[step.output_instance_id] = tuple(parent_instances)

        terminal_independent = _terminal_authority(goal, trace)
        implementation_id = (
            "pct.v0_20_verifiers.verify_v0_20_goal.v1"
            if goal.family in NEW_V0_20_FAMILIES
            else f"pct.goal-verifier.{goal.family.lower()}.v1"
        )
        expected_terminal = replace(
            terminal_independent,
            verifier_class=goal.required_verifier_class,
            stage="TERMINAL",
            subject_id=goal.goal_id,
            evidence=terminal_independent.evidence
            + (
                ("independent_check_id", terminal_independent.verifier_class),
                (
                    "registered_implementation_id",
                    implementation_id,
                ),
            ),
        )
        expected_verifier_chain = tuple(
            step.verifier for step in trace.derivations
        ) + (expected_terminal,)
        if trace.verifier_chain != expected_verifier_chain:
            return False

        candidate_step = step_by_output.get(receipt.candidate_instance_id)
        required_input_keys = (
            frozenset() if obligation is None else obligation.required_input_keys
        )
        if (
            candidate_step is None
            or record_by_step[candidate_step.step_id].artifact != candidate
            or candidate_step.output_artifact_id != candidate.artifact_id
            or candidate_step.output_type != candidate.artifact_type
            or receipt.root_input_keys != candidate_step.root_input_keys
            or not required_input_keys <= receipt.root_input_keys
        ):
            return False
        expected_candidate_instance = "derived:" + canonical_sha256(
            {
                "operator_id": candidate_step.operator_id,
                "parents": candidate_step.input_bindings,
                "artifact": {
                    "artifact_id": candidate.artifact_id,
                    "artifact_type": candidate.artifact_type,
                    "value": candidate.value,
                    "metadata": candidate.metadata,
                },
            },
            domain="pct-derived-instance-v1",
        )
        if receipt.candidate_instance_id != expected_candidate_instance:
            return False

        derived = trace.derived_obligations
        stage_roots = (
            () if obligation is None else obligation.stage_required_input_keys
        ) or tuple(frozenset() for _ in required_types)
        if (
            type(derived) is not tuple
            or len(derived) != len(required_types)
            or len(stage_roots) != len(required_types)
        ):
            return False
        selected_instances: list[str] = []
        for order_index, (witness, required_type, required_roots) in enumerate(
            zip(derived, required_types, stage_roots)
        ):
            if type(witness) is not DerivedObligation or witness.order_index != order_index:
                return False
            step = step_by_id.get(witness.derivation_step_id)
            if (
                step is None
                or witness.semantic_type != required_type.semantic_type
                or witness.artifact_instance_id != step.output_instance_id
                or step.output_type != required_type
                or not required_roots <= step.root_input_keys
            ):
                return False
            selected_instances.append(step.output_instance_id)
        if receipt.stage_instance_ids != tuple(selected_instances):
            return False

        def is_ancestor(ancestor: str, descendant: str) -> bool:
            pending = [descendant]
            visited: set[str] = set()
            while pending:
                current = pending.pop()
                if current in visited:
                    continue
                visited.add(current)
                for parent in parents_by_output.get(current, ()):
                    if parent == ancestor:
                        return True
                    pending.append(parent)
            return False

        lineage_chain = tuple(selected_instances) + (receipt.candidate_instance_id,)
        if any(
            not is_ancestor(ancestor, descendant)
            for ancestor, descendant in zip(lineage_chain, lineage_chain[1:])
        ):
            return False

        derivation_operator_path = tuple(step.operator_id for step in trace.derivations)
        if trace.operator_path != derivation_operator_path + ("VERIFY_CANDIDATE",):
            return False
        return True
    except Exception:
        return False


def _lineage_complete(
    goal: GoalSpec,
    trace: SolveTrace,
    compatibility_model: CompatibilityModel | None = None,
) -> bool:
    """Require the full execution replay plus ordered cross-class stages."""

    return _execution_receipt_complete(
        goal,
        trace,
        compatibility_model,
        require_ordered_stages=True,
    )


def evaluate_case(
    goal: GoalSpec,
    trace: SolveTrace,
    oracle: Mapping[str, Any],
    *,
    compatibility_model: CompatibilityModel | None = None,
    expected_typing_mode: str | None = None,
) -> dict[str, Any]:
    candidate = trace.candidate_artifact
    verdict_ok, observed_verdict = _safe_text(
        trace.final_verdict,
        "NONCANONICAL_VERDICT",
    )
    contract_matches = _candidate_contract_matches(goal, candidate)
    authority = _terminal_authority(goal, trace)
    terminal_verified = bool(
        verdict_ok
        and observed_verdict == "PASS"
        and contract_matches
        and authority.passed
        and authority.verifier_class == goal.required_verifier_class
    )
    authoritative = oracle.get("authoritative") is True
    expected_verdict = oracle.get("expected_verdict")
    oracle_integrity = _oracle_integrity_valid(goal, oracle)
    challenge_contract_valid = _challenge_contract_valid(goal)
    mathematical_authority = bool(
        challenge_contract_valid
        and authoritative
        and oracle.get("authority_kind") == "INDEPENDENT_MATHEMATICAL_ORACLE"
    )
    semantic_certificate = _semantic_certificate(
        trace,
        terminal_verified=terminal_verified,
    )
    execution_receipt_complete = bool(
        observed_verdict == "PASS"
        and _execution_receipt_complete(
            goal,
            trace,
            compatibility_model,
            expected_typing_mode=expected_typing_mode,
        )
    )
    runtime_lineage_complete = bool(
        execution_receipt_complete
        and goal.lineage_obligation is not None
        and goal.lineage_obligation.ordered_stage_types
    )
    refusal_execution_replayed = bool(
        mathematical_authority
        and expected_verdict != "PASS"
        and _nonpass_refusal_matches(
            goal,
            trace,
            expected_verdict,
            compatibility_model=compatibility_model,
            expected_typing_mode=expected_typing_mode,
        )
    )
    candidate_matches_oracle = bool(
        mathematical_authority
        and expected_verdict == "PASS"
        and terminal_verified
        and _candidate_matches_oracle(goal, candidate)
    )
    if mathematical_authority and expected_verdict == "PASS":
        correct: bool | None = bool(
            oracle_integrity
            and observed_verdict == "PASS"
            and terminal_verified
            and candidate_matches_oracle
            and semantic_certificate["complete"] is True
            and execution_receipt_complete
        )
    elif mathematical_authority:
        correct = bool(
            verdict_ok
            and oracle_integrity
            and observed_verdict == expected_verdict
            and candidate is None
            and refusal_execution_replayed
            and semantic_certificate["complete"] is True
        )
    else:
        correct = None
    wrong_positive = bool(
        observed_verdict == "PASS"
        and (
            not terminal_verified
            or not oracle_integrity
            or not execution_receipt_complete
            or (mathematical_authority and correct is not True)
        )
    )
    _operator_path_ok, safe_operator_path = _safe_string_sequence(trace.operator_path)
    _macro_ids_ok, safe_macro_ids = _safe_string_sequence(trace.macro_ids)
    _expanded_ok, safe_expanded_count = _safe_nonnegative_count(trace.expanded_state_count)
    _executions_ok, safe_execution_count = _safe_nonnegative_count(
        trace.primitive_execution_count
    )
    _failure_ok, safe_failure_reason = _safe_text(
        trace.failure_reason,
        "NONCANONICAL_FAILURE_REASON",
    )
    safe_verdict = observed_verdict
    if candidate is None:
        candidate_type = None
    elif type(candidate) is not Artifact:
        candidate_type = {
            "semantic_type": "NONCANONICAL_SEMANTIC_TYPE",
            "representation_class": "NONCANONICAL_REPRESENTATION_CLASS",
            "exactness_class": "NONCANONICAL_EXACTNESS_CLASS",
        }
    else:
        _, semantic_type = _safe_text(
            candidate.semantic_type,
            "NONCANONICAL_SEMANTIC_TYPE",
        )
        _, representation_class = _safe_text(
            candidate.representation_class,
            "NONCANONICAL_REPRESENTATION_CLASS",
        )
        _, exactness_class = _safe_text(
            candidate.exactness_class,
            "NONCANONICAL_EXACTNESS_CLASS",
        )
        candidate_type = {
            "semantic_type": semantic_type,
            "representation_class": representation_class,
            "exactness_class": exactness_class,
        }
    observation = {
        "verdict": safe_verdict,
        "candidate": semantic_certificate["normalized_candidate"],
        "candidate_type": candidate_type,
        "operator_path": safe_operator_path,
        "macro_ids": safe_macro_ids,
        "expanded_state_count": safe_expanded_count,
        "primitive_execution_count": safe_execution_count,
        "failure_reason": safe_failure_reason,
        "verifier_chain": _verifier_rows(trace),
        "terminal_authority": {
            "passed": authority.passed,
            "verifier_class": authority.verifier_class,
            "reason": authority.reason,
        },
        "semantic_certificate": semantic_certificate,
    }
    signatures = case_signatures(goal)
    return {
        "goal_id": goal.goal_id,
        "family": goal.family,
        "exact_content_sha256": signatures.exact_sha256,
        "nuisance_content_sha256": signatures.nuisance_sha256,
        "nuisance_relation": signatures.nuisance_relation,
        "observation": observation,
        "oracle": dict(oracle),
        "assessment": {
            "oracle_available": mathematical_authority,
            "challenge_contract_valid": challenge_contract_valid,
            "correct": correct,
            "wrong_positive": wrong_positive,
            "oracle_integrity_valid": oracle_integrity,
            "candidate_matches_independent_oracle": (
                candidate_matches_oracle
                if mathematical_authority and expected_verdict == "PASS" and observed_verdict == "PASS"
                else None
            ),
            "candidate_contract_matches": contract_matches if observed_verdict == "PASS" else None,
            "terminal_verified": terminal_verified if observed_verdict == "PASS" else None,
            "execution_receipt_complete": execution_receipt_complete,
            "refusal_execution_replayed": (
                refusal_execution_replayed if observed_verdict != "PASS" else None
            ),
            "credit_eligible_execution": (
                execution_receipt_complete
                if observed_verdict == "PASS"
                else refusal_execution_replayed
            ),
            "runtime_lineage_complete": runtime_lineage_complete,
        },
    }


def _summarize_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total": len(cases),
        "pass_count": sum(case["observation"]["verdict"] == "PASS" for case in cases),
        "authoritatively_assessed_count": sum(case["assessment"]["oracle_available"] for case in cases),
        "correct_count": sum(case["assessment"]["correct"] is True for case in cases),
        "wrong_positive_count": sum(case["assessment"]["wrong_positive"] is True for case in cases),
        "oracle_unavailable_count": sum(not case["assessment"]["oracle_available"] for case in cases),
        "cases": cases,
    }


def _run_split(
    goals: Sequence[GoalSpec],
    registry: Mapping[str, OperatorSpec],
    compatibility_model: CompatibilityModel,
    macro_proposals: Sequence[MacroProposalSpec],
    oracles: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for mode_name, typing_mode, synthesized in _FROZEN_MODE_CONFIGS:
        cases: list[dict[str, Any]] = []
        for goal in goals:
            trace = _safe_solve(
                goal,
                registry,
                mode_name=mode_name,
                typing_mode=typing_mode,
                compatibility_model=compatibility_model,
                macros=macro_proposals if synthesized else (),
            )
            case = evaluate_case(
                goal,
                trace,
                oracles[goal.goal_id],
                compatibility_model=compatibility_model,
                expected_typing_mode=typing_mode,
            )
            case["observation"]["input_semantic_types_blinded"] = typing_mode != "EXPLICIT"
            cases.append(case)
        result[mode_name] = _summarize_cases(cases)
    return result


def evaluate_terminal_control(control: TerminalCandidateControl) -> dict[str, Any]:
    kind_suffix = {
        TerminalControlKind.DOMAIN_REFUSAL: "domain",
        TerminalControlKind.INVALID_TERMINAL_CERTIFICATE: "invalid",
        TerminalControlKind.VALID_NEGATIVE_RESULT: "negative",
        TerminalControlKind.EXTERNAL_VALID_CERTIFICATE: "external",
    }
    schema_valid = bool(
        type(control) is TerminalCandidateControl
        and type(control.control_id) is str
        and type(control.family) is str
        and type(control.kind) is TerminalControlKind
        and type(control.goal) is GoalSpec
        and type(control.candidate) is Artifact
        and type(control.expected_verification_pass) is bool
        and type(control.is_distinct_alternative) is bool
        and type(control.rationale) is str
        and 0 < len(control.rationale) <= _MAX_EVIDENCE_TEXT
        and control.family == control.goal.family
        and control.family in NEW_V0_20_FAMILIES
        and control.control_id
        == f"terminal-control:{control.family.lower()}:{kind_suffix.get(control.kind, '')}"
        and control.expected_verification_pass
        is (
            control.kind
            in {
                TerminalControlKind.VALID_NEGATIVE_RESULT,
                TerminalControlKind.EXTERNAL_VALID_CERTIFICATE,
            }
        )
        and (
            not control.is_distinct_alternative
            or control.kind is TerminalControlKind.EXTERNAL_VALID_CERTIFICATE
        )
    )
    result = verify_v0_20_goal(control.goal, control.candidate)
    authoritative_result = _STRICT_TERMINAL_CONTROL_AUTHORITY(
        control.goal,
        control.candidate,
    )
    absent_from_roots = bool(
        schema_valid
        and all(
            root is not control.candidate
            and root.artifact_id != control.candidate.artifact_id
            for root in control.goal.inputs.values()
        )
    )
    challenge_valid = _challenge_contract_valid(control.goal)
    challenge_semantics_valid = bool(
        challenge_valid
        is (control.kind is not TerminalControlKind.DOMAIN_REFUSAL)
    )
    candidate_contract_valid = _candidate_contract_matches(
        control.goal,
        control.candidate,
    )
    certifier_semantics_valid = bool(
        type(result) is VerificationResult
        and type(authoritative_result) is VerificationResult
        and result == authoritative_result
        and type(result.passed) is bool
        and result.verifier_class == control.goal.required_verifier_class
        and type(result.reason) is str
        and 0 < len(result.reason) <= _MAX_EVIDENCE_TEXT
    )
    correct = bool(
        schema_valid
        and absent_from_roots
        and challenge_semantics_valid
        and candidate_contract_valid
        and certifier_semantics_valid
        and result.passed is control.expected_verification_pass
    )
    return {
        "control_id": control.control_id,
        "family": control.family,
        "kind": control.kind.value,
        "is_distinct_alternative": control.is_distinct_alternative,
        "rationale": control.rationale,
        "candidate_was_planner_root": not absent_from_roots,
        "control_schema_valid": schema_valid,
        "challenge_semantics_valid": challenge_semantics_valid,
        "candidate_contract_valid": candidate_contract_valid,
        "certifier_semantics_valid": certifier_semantics_valid,
        "expected_verification_pass": control.expected_verification_pass,
        "observed_verification_pass": result.passed,
        "verifier_class": result.verifier_class,
        "reason": result.reason,
        "correct": correct,
    }


def _terminal_control_manifest_conforms(
    controls: Sequence[TerminalCandidateControl],
    evaluated_rows: Sequence[Mapping[str, Any]],
) -> bool:
    """Require the exact frozen controls and one conforming receipt per control."""

    try:
        if type(controls) is not tuple or type(evaluated_rows) is not list:
            return False
        if (
            len(controls) != V0_20_TERMINAL_CONTROL_COUNT
            or len(evaluated_rows) != V0_20_TERMINAL_CONTROL_COUNT
        ):
            return False
        actual_manifest = tuple(
            (
                control.control_id,
                control.family,
                control.kind.value,
                control.expected_verification_pass,
                control.is_distinct_alternative,
            )
            for control in controls
            if type(control) is TerminalCandidateControl
            and type(control.kind) is TerminalControlKind
            and type(control.expected_verification_pass) is bool
            and type(control.is_distinct_alternative) is bool
        )
        if (
            actual_manifest != _FROZEN_TERMINAL_CONTROL_MANIFEST
            or len({row[0] for row in actual_manifest})
            != V0_20_TERMINAL_CONTROL_COUNT
            or _controls_digest(controls) != _FROZEN_TERMINAL_CONTROLS_SHA256
        ):
            return False
        for expected, row in zip(_FROZEN_TERMINAL_CONTROL_MANIFEST, evaluated_rows):
            control_id, family, kind, expected_pass, distinct = expected
            if (
                type(row) is not dict
                or row.get("control_id") != control_id
                or row.get("family") != family
                or row.get("kind") != kind
                or row.get("expected_verification_pass") is not expected_pass
                or row.get("is_distinct_alternative") is not distinct
                or row.get("candidate_was_planner_root") is not False
                or row.get("control_schema_valid") is not True
                or row.get("challenge_semantics_valid") is not True
                or row.get("candidate_contract_valid") is not True
                or row.get("certifier_semantics_valid") is not True
                or row.get("correct") is not True
            ):
                return False
        return len({row["control_id"] for row in evaluated_rows}) == len(
            evaluated_rows
        )
    except Exception:
        return False


def _case_map(mode: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {case["goal_id"]: case for case in mode.get("cases", ())}


def _observation_claims_macro_authority(observation: Mapping[str, Any]) -> bool:
    try:
        if bool(observation.get("macro_ids")):
            return True
        operator_path = observation.get("operator_path", ())
        if type(operator_path) not in (tuple, list) or any(
            type(operator_id) is not str for operator_id in operator_path
        ):
            return True
        if any(
            operator_id.startswith(("MACRO:", "CERT_MACRO:"))
            for operator_id in operator_path
        ):
            return True
        certificate = observation.get("semantic_certificate", {})
        bindings = certificate.get("macro_bindings") if isinstance(certificate, Mapping) else None
        if isinstance(bindings, Mapping) and bindings.get("type") == "tuple":
            return bool(bindings.get("items"))
        return bool(bindings)
    except Exception:
        return True


def _macro_analysis(*split_modes: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    pairs = (
        ("EXPLICIT/PRIMITIVE", "EXPLICIT/SYNTHESIZED"),
        ("INFERRED/PRIMITIVE", "INFERRED/SYNTHESIZED"),
        ("HYBRID/PRIMITIVE", "HYBRID/SYNTHESIZED"),
    )
    evaluations: list[dict[str, Any]] = []
    for modes in split_modes:
        for primitive_name, macro_name in pairs:
            primitive = _case_map(modes.get(primitive_name, {}))
            synthesized = _case_map(modes.get(macro_name, {}))
            for goal_id in sorted(set(primitive) | set(synthesized)):
                before, after = primitive.get(goal_id), synthesized.get(goal_id)
                if before is None or after is None:
                    evaluations.append({
                        "goal_id": goal_id,
                        "mode_pair": [primitive_name, macro_name],
                        "macro_used": False,
                        "primitive_macro_claim": False,
                        "synthesized_macro_claim": False,
                        "unauthorized_macro_claim": False,
                        "macro_rescue": True,
                        "exact_conservation": False,
                        "work_reduced": False,
                        "efficiency_credit": False,
                        "reason": "MISSING_COMPARISON_CASE",
                    })
                    continue
                before_observation = before["observation"]
                after_observation = after["observation"]
                primitive_macro_claim = _observation_claims_macro_authority(
                    before_observation
                )
                synthesized_macro_claim = _observation_claims_macro_authority(
                    after_observation
                )
                macro_used = bool(primitive_macro_claim or synthesized_macro_claim)
                unauthorized_macro_claim = macro_used
                verdict_rescue = bool(
                    before_observation["verdict"] != "PASS"
                    and after_observation["verdict"] == "PASS"
                )
                rescue = bool(unauthorized_macro_claim or verdict_rescue)
                evaluations.append({
                    "goal_id": goal_id,
                    "family": before["family"],
                    "mode_pair": [primitive_name, macro_name],
                    "macro_used": macro_used,
                    "primitive_macro_claim": primitive_macro_claim,
                    "synthesized_macro_claim": synthesized_macro_claim,
                    "unauthorized_macro_claim": unauthorized_macro_claim,
                    "macro_rescue": rescue,
                    "exact_conservation": False,
                    "work_reduced": False,
                    "efficiency_credit": False,
                    "reason": (
                        "UNAUTHORIZED_MACRO_EXECUTION_CLAIM"
                        if unauthorized_macro_claim
                        else "MACRO_EXECUTION_AUTHORITY_DISABLED"
                    ),
                })
    return {
        "total_comparisons": len(evaluations),
        "macro_use_count": sum(row["macro_used"] for row in evaluations),
        "unauthorized_macro_claim_count": sum(
            row.get("unauthorized_macro_claim", False) for row in evaluations
        ),
        "macro_rescue_count": sum(row["macro_rescue"] for row in evaluations),
        "exact_conservation_count": sum(row["exact_conservation"] for row in evaluations),
        "efficiency_credit_count": sum(row["efficiency_credit"] for row in evaluations),
        "evaluations": evaluations,
    }


def _macro_gate_credit_counts(analysis: object) -> tuple[int, int]:
    """Return gate numerators only for the exact frozen comparison population."""

    denominator = GATE_DENOMINATORS["zero_macro_rescues"]
    try:
        if type(analysis) is not dict:
            return 0, 0
        evaluations = analysis["evaluations"]
        if (
            type(evaluations) is not list
            or type(analysis["total_comparisons"]) is not int
            or analysis["total_comparisons"] != denominator
            or len(evaluations) != denominator
        ):
            return 0, 0
        comparison_keys = [
            (
                row.get("goal_id"),
                row.get("family"),
                tuple(row.get("mode_pair", ())),
            )
            for row in evaluations
            if type(row) is dict
        ]
        expected_pairs = (
            ("EXPLICIT/PRIMITIVE", "EXPLICIT/SYNTHESIZED"),
            ("INFERRED/PRIMITIVE", "INFERRED/SYNTHESIZED"),
            ("HYBRID/PRIMITIVE", "HYBRID/SYNTHESIZED"),
        )
        expected_keys = {
            (goal_id, family, pair)
            for goal_id, family in _FROZEN_EXPECTED_SEALED_GOAL_ROWS
            for pair in expected_pairs
        }
        if (
            len(comparison_keys) != denominator
            or len(set(comparison_keys)) != denominator
            or set(comparison_keys) != expected_keys
        ):
            return 0, 0
        zero_rescue = (
            denominator
            if analysis.get("macro_rescue_count") == 0
            and all(row.get("macro_rescue") is False for row in evaluations)
            else 0
        )
        conservation = (
            denominator
            if analysis.get("exact_conservation_count") == denominator
            and analysis.get("macro_use_count") == denominator
            and analysis.get("macro_rescue_count") == 0
            and analysis.get("unauthorized_macro_claim_count") == 0
            and all(
                row.get("macro_used") is True
                and row.get("exact_conservation") is True
                and row.get("macro_rescue") is False
                and row.get("unauthorized_macro_claim") is False
                for row in evaluations
            )
            else 0
        )
        return zero_rescue, conservation
    except Exception:
        return 0, 0


def _family_coverage(mode: Mapping[str, Any]) -> int:
    if _scored_mode_manifest_receipt(mode)["valid"] is not True:
        return 0
    by_family: dict[str, list[Mapping[str, Any]]] = {}
    for case in mode.get("cases", ()):
        by_family.setdefault(case["family"], []).append(case)
    return sum(
        len(cases) == 2
        and all(
            case["assessment"].get("challenge_contract_valid") is True
            and case["assessment"].get("oracle_available") is True
            and case["assessment"].get("correct") is True
            and case["assessment"].get("credit_eligible_execution") is True
            and case.get("oracle", {}).get("authority_kind")
            == "INDEPENDENT_MATHEMATICAL_ORACLE"
            for case in cases
        )
        for family, cases in by_family.items()
        if family in _FROZEN_CAMPAIGN_FAMILIES
    )


def _all_cases(modes: Mapping[str, Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [case for mode in modes.values() for case in mode.get("cases", ())]


def _observed_channel(modes: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {
        mode_name: {
            "total": mode["total"],
            "pass_count": mode["pass_count"],
            "cases": [{
                "goal_id": case["goal_id"],
                "family": case["family"],
                "exact_content_sha256": case["exact_content_sha256"],
                "nuisance_content_sha256": case["nuisance_content_sha256"],
                "nuisance_relation": case["nuisance_relation"],
                "observation": case["observation"],
            } for case in mode["cases"]],
        }
        for mode_name, mode in modes.items()
    }


def _assessment_channel(modes: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {
        mode_name: {
            "total": mode["total"],
            "authoritatively_assessed_count": mode["authoritatively_assessed_count"],
            "correct_count": mode["correct_count"],
            "wrong_positive_count": mode["wrong_positive_count"],
            "oracle_unavailable_count": mode["oracle_unavailable_count"],
            "cases": [{
                "goal_id": case["goal_id"],
                "family": case["family"],
                "assessment": case["assessment"],
            } for case in mode["cases"]],
        }
        for mode_name, mode in modes.items()
    }


_IMPLEMENTATION_PATHS = (
    "experiments/__init__.py",
    "experiments/pct_goal_solver/__init__.py",
    "experiments/pct_goal_solver/model.py",
    "experiments/pct_goal_solver/canonical.py",
    "experiments/pct_goal_solver/lineage.py",
    "experiments/pct_goal_solver/planner.py",
    "experiments/pct_goal_solver/operators.py",
    "experiments/pct_goal_solver/verifiers.py",
    "experiments/pct_goal_solver/compatibility.py",
    "experiments/pct_goal_solver/macros.py",
    "experiments/pct_goal_solver/campaign.py",
    "experiments/pct_goal_solver/goals.py",
    "experiments/pct_goal_solver/goal_verifiers.py",
    "experiments/pct_goal_solver/historical_oracles.py",
    "experiments/pct_goal_solver/bridge_operators.py",
    "experiments/pct_goal_solver/v0_20_goals.py",
    "experiments/pct_goal_solver/v0_20_contracts.py",
    "experiments/pct_goal_solver/v0_20_operators.py",
    "experiments/pct_goal_solver/v0_20_macros.py",
    "experiments/pct_goal_solver/v0_20_verifiers.py",
    "experiments/pct_goal_solver/v0_20_terminal_verification.py",
    "experiments/pct_goal_solver/rigorous_math.py",
    "experiments/pct_goal_solver/elliptic_periods.py",
    "experiments/pct_goal_solver/shortcut_proof.py",
    "experiments/pct_goal_solver/campaign_oracles.py",
    "experiments/pct_goal_solver/repaired_main_binding.py",
    "experiments/pct_goal_solver/v0_20_campaign.py",
    "experiments/pct_goal_solver/generate_v0_20_report.py",
)


def build_implementation_manifest() -> dict[str, Any]:
    repository = Path(__file__).resolve().parents[2]
    files: list[dict[str, str]] = []
    missing_required: list[str] = []
    for relative in _IMPLEMENTATION_PATHS:
        path = repository / relative
        if not path.is_file():
            missing_required.append(relative)
            continue
        files.append({"path": relative, "sha256": _sha256_bytes(path.read_bytes())})
    files.sort(key=lambda row: row["path"])
    body = {"schema": "PCT_V0_20_IMPLEMENTATION_MANIFEST_V1", "files": files}
    return {
        **body,
        "manifest_sha256": _sha256_json(body),
        "complete": not missing_required and len(files) >= len(_IMPLEMENTATION_PATHS),
        "missing_required_files": missing_required,
    }


def _is_hash_locked_requirements(payload: str) -> bool:
    if type(payload) is not str:
        return False
    records: list[str] = []
    pending: list[str] = []
    for raw_line in payload.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        continued = stripped.endswith("\\")
        fragment = stripped[:-1].strip() if continued else stripped
        if not fragment:
            return False
        pending.append(fragment)
        if not continued:
            records.append(" ".join(pending))
            pending = []
    if pending or not records:
        return False

    exact_pin = re.compile(
        r"[A-Za-z0-9][A-Za-z0-9._-]*(?:\[[A-Za-z0-9._,-]+\])?"
        r"==[A-Za-z0-9][A-Za-z0-9._+!-]*"
    )
    exact_hash = re.compile(r"--hash=sha256:[0-9a-f]{64}")
    for record in records:
        tokens = record.split()
        if not tokens or exact_pin.fullmatch(tokens[0]) is None:
            return False
        hashes = tokens[1:]
        if not hashes or any(exact_hash.fullmatch(token) is None for token in hashes):
            return False
    return True


def build_dependency_lock_binding() -> dict[str, Any]:
    repository = Path(__file__).resolve().parents[2]
    candidates = ("requirements-v0.20-lock.txt",)
    files: list[dict[str, str]] = []
    bound = True
    for relative in candidates:
        path = repository / relative
        if not path.is_file():
            bound = False
            continue
        payload = path.read_text(encoding="utf-8")
        files.append({"path": relative, "sha256": _sha256_bytes(payload.encode("utf-8"))})
        bound = bound and _is_hash_locked_requirements(payload)
    manifest_digest = _sha256_json(files) if bound and files else None
    return {
        "status": "BOUND" if bound and files else "UNBOUND",
        "lock_manifest_sha256": manifest_digest,
        "files": files,
        "reason": "" if bound and files else "HASH_LOCKED_V0_20_DEPENDENCIES_NOT_BOUND",
    }


def _registry_contract_digest(registry: Mapping[str, OperatorSpec]) -> str:
    """Bind complete live operators plus terminal/comparison dispatch contracts."""

    return _planner_registry_digest(registry)


def _corpus_digest(corpus: Mapping[str, Sequence[GoalSpec]], oracles: Mapping[str, Mapping[str, Any]]) -> str:
    rows = [{
        "split": split,
        "goal_id": goal.goal_id,
        "signatures": asdict(case_signatures(goal)),
        "oracle": oracles[goal.goal_id],
    } for split in _FROZEN_SPLIT_NAMES for goal in corpus[split]]
    return _sha256_json(rows)


def _controls_digest(controls: Sequence[TerminalCandidateControl]) -> str:
    rows = [{
        "control_id": control.control_id,
        "family": control.family,
        "kind": control.kind.value,
        "goal_exact_sha256": case_signatures(control.goal).exact_sha256,
        "candidate": _canonical(control.candidate),
        "expected_verification_pass": control.expected_verification_pass,
        "is_distinct_alternative": control.is_distinct_alternative,
    } for control in controls]
    return _sha256_json(rows)


def _invalid_corpus_campaign_result(
    manifest_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a bounded fail-closed report without solving an invalid corpus."""

    reason = "the preregistered corpus manifest is invalid; no capability evidence was executed"
    receipts = {
        gate: _receipt(0, gate, reason)
        for gate in EXPECTED_GATE_KEYS
    }
    gates = {gate: False for gate in EXPECTED_GATE_KEYS}
    return {
        "campaign_id": "PCT_GOAL_SOLVER_CROSS_CLASS_V0_20",
        "scientific_status": classify_scientific_status(gates),
        "scientific_axes": classify_scientific_axes(gates),
        "gates": gates,
        "gate_receipts": receipts,
        "gates_passed": 0,
        "gates_total": len(EXPECTED_GATE_KEYS),
        "total_wrong_positives": 0,
        "provenance": {
            "frozen_feature_base_sha": FROZEN_FEATURE_BASE_SHA,
            "corpus_manifest_validation": dict(manifest_receipt),
            "expected_corpus_manifest_sha256": _FROZEN_CORPUS_MANIFEST_SHA256,
            "expected_sealed_case_manifest_sha256": _FROZEN_SEALED_CASE_MANIFEST_SHA256,
            "expected_terminal_controls_sha256": _FROZEN_TERMINAL_CONTROLS_SHA256,
        },
        "channels": {},
        "macro_proposals": [],
        "splits": {},
    }


@lru_cache(maxsize=1)
def _execute_v0_20_campaign_cached() -> dict[str, Any]:
    corpus = build_v0_20_corpus()
    corpus_manifest = _frozen_corpus_manifest_receipt(corpus)
    if corpus_manifest["valid"] is not True:
        return _invalid_corpus_campaign_result(corpus_manifest)
    controls = build_v0_20_terminal_controls()
    registry = build_v0_20_operator_registry()
    all_core_goals = [
        goal for split in _FROZEN_SPLIT_NAMES for goal in corpus[split]
    ]
    oracle_by_goal_id: dict[str, Mapping[str, Any]] = {}
    for goal in all_core_goals:
        if goal.goal_id in oracle_by_goal_id:
            return _invalid_corpus_campaign_result({
                **corpus_manifest,
                "valid": False,
                "errors": tuple(corpus_manifest["errors"]) + ("DUPLICATE_GOAL_ID",),
            })
        oracle_by_goal_id[goal.goal_id] = _build_campaign_oracle(goal)
    if len(oracle_by_goal_id) != len(all_core_goals):
        return _invalid_corpus_campaign_result({
            **corpus_manifest,
            "valid": False,
            "errors": tuple(corpus_manifest["errors"]) + ("ORACLE_MAP_CARDINALITY_MISMATCH",),
        })

    calibration_goals = corpus["CALIBRATION_V0_20"]
    calibration_traces = tuple(
        _safe_solve(goal, registry, mode_name="EXPLICIT/PRIMITIVE", typing_mode="EXPLICIT")
        for goal in calibration_goals
    )
    compatibility_model = CompatibilityModel.fit(calibration_goals, calibration_traces, registry)
    macro_proposals = synthesize_macro_proposals(
        calibration_goals,
        calibration_traces,
        registry,
    )

    validation_modes = _run_split(
        corpus["VALIDATION_V0_20"], registry, compatibility_model, macro_proposals, oracle_by_goal_id
    )
    sealed_modes = _run_split(
        corpus["SEALED_V0_20"], registry, compatibility_model, macro_proposals, oracle_by_goal_id
    )
    terminal_controls = [evaluate_terminal_control(control) for control in controls]
    terminal_controls_digest = _controls_digest(controls)

    sealed_cross_class = [
        goal
        for goal in corpus["SEALED_V0_20"]
        if goal.family in _FROZEN_CROSS_CLASS_FAMILIES
    ]
    shortcut_proofs = [prove_no_same_class_shortcut(goal, registry) for goal in sealed_cross_class]
    shortcut_proof_count = (
        sum(
            _shortcut_proof_complete(proof, goal, registry)
            for proof, goal in zip(shortcut_proofs, sealed_cross_class)
        )
        if len(sealed_cross_class) == _CROSS_CLASS_SEALED_COUNT
        and len(shortcut_proofs) == _CROSS_CLASS_SEALED_COUNT
        else 0
    )
    macro_analysis = _macro_analysis(sealed_modes)
    scored_cases = _all_cases(sealed_modes)
    scored_case_cardinality_valid = bool(
        type(sealed_modes) is dict
        and set(sealed_modes) == {row[0] for row in _FROZEN_MODE_CONFIGS}
        and len(sealed_modes) == _MODE_COUNT
        and len(scored_cases) == GATE_DENOMINATORS["target_contract_enforced"]
        and all(
            _scored_mode_manifest_receipt(sealed_modes[mode_name])["valid"] is True
            for mode_name, _typing_mode, _synthesized in _FROZEN_MODE_CONFIGS
        )
    )
    zero_macro_rescue_count, exact_macro_conservation_count = (
        _macro_gate_credit_counts(macro_analysis)
    )

    exact_counts: dict[str, int] = {}
    nuisance_counts: dict[str, int] = {}
    for goal in all_core_goals:
        signatures = case_signatures(goal)
        exact_counts[signatures.exact_sha256] = exact_counts.get(signatures.exact_sha256, 0) + 1
        nuisance_counts[signatures.nuisance_sha256] = nuisance_counts.get(signatures.nuisance_sha256, 0) + 1
    core_counts_exact = corpus_manifest["valid"] is True
    exact_disjoint = sum(count == 1 for count in exact_counts.values()) if core_counts_exact else 0
    nuisance_disjoint = sum(count == 1 for count in nuisance_counts.values()) if core_counts_exact else 0

    oracle_complete = sum(
        _challenge_contract_valid(goal)
        and oracle_by_goal_id[goal.goal_id].get("authoritative") is True
        and oracle_by_goal_id[goal.goal_id].get("authority_kind")
        == "INDEPENDENT_MATHEMATICAL_ORACLE"
        for goal in corpus["SEALED_V0_20"]
    )
    terminal_control_manifest_valid = _terminal_control_manifest_conforms(
        controls,
        terminal_controls,
    )
    terminal_control_count = (
        V0_20_TERMINAL_CONTROL_COUNT if terminal_control_manifest_valid else 0
    )
    target_contract_count = (
        sum(
            case["observation"]["verdict"] != "PASS"
            or (
                case["assessment"]["candidate_contract_matches"] is True
                and case["assessment"]["terminal_verified"] is True
            )
            for case in scored_cases
        )
        if scored_case_cardinality_valid
        else 0
    )
    no_wrong_positive_count = (
        sum(
            case["assessment"]["wrong_positive"] is False
            for case in scored_cases
        )
        if scored_case_cardinality_valid
        else 0
    )
    lineage_cases = [
        case
        for case in scored_cases
        if case["family"] in _FROZEN_CROSS_CLASS_FAMILIES
    ]
    lineage_count = (
        sum(
            case["assessment"]["runtime_lineage_complete"] is True
            for case in lineage_cases
        )
        if scored_case_cardinality_valid
        and len(lineage_cases) == GATE_DENOMINATORS["runtime_lineage_receipts_complete"]
        else 0
    )

    implementation_manifest = build_implementation_manifest()
    dependency_lock = build_dependency_lock_binding()
    repaired_main = build_repaired_main_binding()
    provenance = {
        "frozen_feature_base_sha": FROZEN_FEATURE_BASE_SHA,
        "implementation_manifest": implementation_manifest,
        "dependency_lock_binding": dependency_lock,
        "repaired_main_binding": repaired_main,
        "corpus_manifest_validation": corpus_manifest,
        "expected_corpus_manifest_sha256": _FROZEN_CORPUS_MANIFEST_SHA256,
        "expected_sealed_case_manifest_sha256": _FROZEN_SEALED_CASE_MANIFEST_SHA256,
        "corpus_sha256": _corpus_digest(corpus, oracle_by_goal_id),
        "terminal_controls_sha256": terminal_controls_digest,
        "expected_terminal_controls_sha256": _FROZEN_TERMINAL_CONTROLS_SHA256,
        "terminal_control_manifest_sha256": _sha256_json(
            _FROZEN_TERMINAL_CONTROL_MANIFEST
        ),
        "registry_contract_sha256": _registry_contract_digest(registry),
    }

    receipts = {
        "closed_challenge_domain_valid": _challenge_domain_receipt(corpus),
        "exact_content_partition_disjoint": _receipt(exact_disjoint, "exact_content_partition_disjoint", "every raw mathematical problem must be unique across core partitions"),
        "nuisance_partition_disjoint": _receipt(nuisance_disjoint, "nuisance_partition_disjoint", "known nuisance-equivalent problems must not leak across partitions"),
        "terminal_controls_conform": {
            **_receipt(terminal_control_count, "terminal_controls_conform", "the exact frozen external-control manifest must match typed expectations without planner-root leakage"),
            "expected_controls_sha256": _FROZEN_TERMINAL_CONTROLS_SHA256,
            "observed_controls_sha256": terminal_controls_digest,
        },
        "target_contract_enforced": _receipt(target_contract_count, "target_contract_enforced", "every PASS must satisfy target type and public terminal authority"),
        "zero_known_wrong_positives": _receipt(no_wrong_positive_count, "zero_known_wrong_positives", "no observed PASS may contradict available terminal or oracle evidence"),
        "independent_oracles_complete": _receipt(oracle_complete, "independent_oracles_complete", "every sealed goal needs an import-independent authoritative oracle"),
        "shortcut_proofs_complete": _receipt(
            shortcut_proof_count,
            "shortcut_proofs_complete",
            "each sealed cross-class goal requires a complete live-bound no-shortcut proof",
        ),
        "runtime_lineage_receipts_complete": _receipt(lineage_count, "runtime_lineage_receipts_complete", "every cross-class execution must expose complete ordered lineage"),
        "implementation_manifest_bound": _receipt(int(implementation_manifest["complete"]), "implementation_manifest_bound", "the full implementation file manifest must be SHA-256 bound"),
        "dependency_lock_bound": _receipt(int(dependency_lock["status"] == "BOUND"), "dependency_lock_bound", "hash-locked dependencies must be bound"),
        "repaired_main_bound": _receipt(int(repaired_main["status"] == "BOUND"), "repaired_main_bound", "the separate repaired-main commit and file manifest must be bound"),
        "explicit_family_coverage": _receipt(_family_coverage(sealed_modes["EXPLICIT/PRIMITIVE"]), "explicit_family_coverage", "both sealed cases in every family must be independently correct"),
        "inferred_family_coverage": _receipt(_family_coverage(sealed_modes["INFERRED/PRIMITIVE"]), "inferred_family_coverage", "blinded primitive routing must solve both sealed cases per family"),
        "hybrid_family_coverage": _receipt(_family_coverage(sealed_modes["HYBRID/PRIMITIVE"]), "hybrid_family_coverage", "hybrid primitive routing must solve both sealed cases per family"),
        "zero_macro_rescues": _receipt(zero_macro_rescue_count, "zero_macro_rescues", "exactly 114 primitive/synthesized comparisons must exist and none may be a macro rescue"),
        "exact_macro_conservation": _receipt(exact_macro_conservation_count, "exact_macro_conservation", "exactly 114 comparisons must each use a macro and preserve an identical complete semantic certificate"),
    }
    gates = {key: receipt["passed"] for key, receipt in receipts.items()}
    if set(receipts) != set(EXPECTED_GATE_KEYS):
        gates = {key: False for key in EXPECTED_GATE_KEYS}

    return {
        "campaign_id": "PCT_GOAL_SOLVER_CROSS_CLASS_V0_20",
        "scientific_status": classify_scientific_status(gates),
        "scientific_axes": classify_scientific_axes(gates),
        "gates": gates,
        "gate_receipts": receipts,
        "gates_passed": sum(gates.values()),
        "gates_total": len(EXPECTED_GATE_KEYS),
        "total_wrong_positives": sum(case["assessment"]["wrong_positive"] is True for case in scored_cases),
        "provenance": provenance,
        "channels": {
            "observed_solver_outcomes": {
                "validation": _observed_channel(validation_modes),
                "sealed": _observed_channel(sealed_modes),
            },
            "mathematical_oracle_certificates": {
                "sealed_goal_count": len(corpus["SEALED_V0_20"]),
                "authoritative_count": oracle_complete,
                "unavailable_count": len(corpus["SEALED_V0_20"]) - oracle_complete,
                "cases": [oracle_by_goal_id[goal.goal_id] for goal in corpus["SEALED_V0_20"]],
            },
            "independent_assessments": {
                "sealed": _assessment_channel(sealed_modes),
            },
            "terminal_candidate_controls": {
                "total": len(terminal_controls),
                "correct_count": terminal_control_count,
                "cases": terminal_controls,
            },
            "shortcut_proofs": shortcut_proofs,
            "macro_conservation": macro_analysis,
        },
        "macro_proposals": [{
            "macro_id": macro.macro_id,
            "primitive_ids": list(macro.primitive_ids),
            "witness_goal_ids": sorted(macro.witness_goal_ids),
            "witness_trace_digests": list(macro.witness_trace_digests),
            "execution_authority": False,
            "efficiency_credit_eligible": False,
        } for macro in macro_proposals],
        "splits": {
            "VALIDATION_V0_20": validation_modes,
            "SEALED_V0_20": sealed_modes,
            "TERMINAL_CONTROLS_V0_20": terminal_controls,
        },
    }


def execute_v0_20_campaign() -> dict[str, Any]:
    """Return an isolated snapshot so callers cannot poison cached evidence."""

    return deepcopy(_execute_v0_20_campaign_cached())
