"""Adapters to unchanged upstream code, with independent qualification evidence.

The finite closure below is a new fixture, not a recovered historical artifact.
Its multiplication uses MAPEOGEO; NumPy checks the products independently.
"""
from collections import Counter, deque
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
from numbers import Integral
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np

from ._vendor.mapeogeo.mapeogeo import (
    latent_generator_observability_v2 as _observability,
    latent_generator_v1 as _inverse,
    psmsl_operator_algebra_v1 as _algebra,
    psmsl_work_equivalence_v1 as _work,
)
from ._vendor.ngc_real.ngc_rq import real_phase as _real_phase
from ._vendor.ngc_real.ngc_rq.backends import dual_lane as _dual_lane


_VENDOR_ROOT = Path(__file__).resolve().parent / "_vendor"
_SOURCE_MANIFESTS = {
    "mapeogeo": Path("mapeogeo/SOURCE_PROVENANCE.json"),
    "mapeogeo_audit": Path("mapeogeo/AUDIT_SOURCE_PROVENANCE.json"),
    "ngc_real": Path("ngc_real/SOURCE_PROVENANCE.json"),
}
_IDENTITY = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
_ZERO = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
_GENERATORS = {
    "Rx90": ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
    "Rz90": ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
    "Pxy": ((1, 0, 0), (0, 1, 0), (0, 0, 0)),
}


def mapeogeo_modules() -> dict[str, ModuleType]:
    """Return real, package-relative upstream modules without changing sys.path."""
    return {"algebra": _algebra, "inverse": _inverse,
            "observability": _observability, "work": _work}


def dual_lane_apply(state, gate, targets, num_qubits) -> np.ndarray:
    """Validate a normalized state/unitary gate and execute the actual NGC backend.

    Qubit zero is the most significant tensor factor. Supplied target order is
    preserved. Validation never calls the independent complex reference.
    """
    if isinstance(num_qubits, (bool, np.bool_)) or not isinstance(num_qubits, Integral):
        raise ValueError("num_qubits must be a positive integer")
    if num_qubits <= 0:
        raise ValueError("num_qubits must be a positive integer")
    num_qubits = int(num_qubits)
    try:
        target_tuple = tuple(targets)
    except TypeError as exc:
        raise ValueError("targets must be a nonempty sequence of integers") from exc
    if not target_tuple or any(isinstance(t, (bool, np.bool_)) or not isinstance(t, Integral)
                               for t in target_tuple):
        raise ValueError("targets must be a nonempty sequence of integers")
    target_tuple = tuple(int(t) for t in target_tuple)
    if len(set(target_tuple)) != len(target_tuple):
        raise ValueError("targets must be unique")
    if any(t < 0 or t >= num_qubits for t in target_tuple):
        raise ValueError("targets must be within the qubit register")
    try:
        state_array = np.asarray(state, dtype=complex)
        gate_array = np.asarray(gate, dtype=complex)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("state and gate must be numeric arrays") from exc
    if state_array.ndim != 1 or state_array.size == 0:
        raise ValueError("state must be a nonempty one-dimensional vector")
    dimension = int(state_array.size)
    # Validate against the supplied vector before computing a potentially huge 2**n.
    if dimension & (dimension - 1) or dimension.bit_length() - 1 != num_qubits:
        raise ValueError("state length does not match num_qubits")
    if not np.all(np.isfinite(state_array)):
        raise ValueError("state must contain only finite values")
    with np.errstate(over="ignore", invalid="ignore"):
        state_norm = np.linalg.norm(state_array)
    if not np.isfinite(state_norm) or not np.isclose(state_norm, 1.0, atol=1e-10, rtol=0):
        raise ValueError("state must already be normalized")
    local_dimension = 1 << len(target_tuple)
    if gate_array.shape != (local_dimension, local_dimension):
        raise ValueError("gate shape does not match the number of targets")
    if not np.all(np.isfinite(gate_array)):
        raise ValueError("gate must contain only finite values")
    with np.errstate(over="ignore", invalid="ignore"):
        gram = gate_array.conj().T @ gate_array
    if not np.allclose(gram, np.eye(local_dimension), atol=1e-10, rtol=0):
        raise ValueError("gate must be unitary")
    state_real = _real_phase.realify_vector(state_array)
    gate_real = _real_phase.realify_operator(gate_array)
    result = _dual_lane.apply_local_gate_dual_lane(
        state_real, gate_real, target_tuple, num_qubits)
    result = np.asarray(result)
    if result.shape != (2 * dimension,):
        raise ValueError(f"dual-lane backend output has shape {result.shape}; expected {(2 * dimension,)}")
    if result.dtype.kind not in "fiu":
        raise ValueError("dual-lane backend output must be a real numeric vector")
    if not np.all(np.isfinite(result)):
        raise ValueError(f"dual-lane backend output contains nonfinite values: {result!r}")
    output = _real_phase.complexify_vector(result)
    if output.shape != state_array.shape or not np.all(np.isfinite(output)):
        raise ValueError("dual-lane backend output failed complex-state shape or finiteness postcondition")
    with np.errstate(over="ignore", invalid="ignore"):
        output_norm = np.linalg.norm(output)
    if not np.isfinite(output_norm) or not np.isclose(output_norm, 1.0, atol=1e-10, rtol=0):
        raise ValueError(f"dual-lane backend output is not normalized: norm={output_norm!r}")
    return output


def verify_sources() -> dict[str, Any]:
    """Hash exactly the source files listed in the three provenance manifests.

    New namespace initializer files are not upstream files and are not included.
    Missing or changed files produce explicit mismatch records.
    """
    manifests = {}
    all_mismatches = []
    verified_total = 0
    for name, relative_manifest in _SOURCE_MANIFESTS.items():
        manifest_path = _VENDOR_ROOT / relative_manifest
        base = manifest_path.parent
        result = {"verified_files": 0, "mismatches": []}
        manifests[name] = result
        try:
            content = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries = content["files"]
            if not isinstance(entries, list) or not entries:
                raise ValueError("manifest files must be a nonempty list")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            mismatch = {"manifest": name, "path": str(relative_manifest),
                        "reason": "unreadable_manifest", "detail": str(exc)}
            result["mismatches"].append(mismatch)
            all_mismatches.append(mismatch)
            continue
        for entry in entries:
            try:
                relative = entry.get("destination", entry["path"])
                expected_sha256 = entry["sha256"]
                expected_blob = entry["git_blob_sha1"]
                if not isinstance(relative, str):
                    raise ValueError("source path must be a string")
                candidate = base / relative
                if not candidate.resolve().is_relative_to(base.resolve()):
                    raise ValueError("source path leaves its declared source directory")
            except (KeyError, TypeError, ValueError, AttributeError) as exc:
                mismatch = {"manifest": name, "path": str(entry),
                            "reason": "invalid_manifest_entry", "detail": str(exc)}
                result["mismatches"].append(mismatch)
                all_mismatches.append(mismatch)
                continue
            try:
                raw = candidate.read_bytes()
            except OSError as exc:
                mismatch = {"manifest": name, "path": relative,
                            "reason": "missing_source", "detail": str(exc)}
                result["mismatches"].append(mismatch)
                all_mismatches.append(mismatch)
                continue
            actual_sha256 = hashlib.sha256(raw).hexdigest()
            actual_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            if actual_sha256 == expected_sha256 and actual_blob == expected_blob:
                result["verified_files"] += 1
                verified_total += 1
            else:
                mismatch = {"manifest": name, "path": relative, "reason": "content_hash_mismatch",
                            "expected_sha256": expected_sha256, "actual_sha256": actual_sha256,
                            "expected_git_blob_sha1": expected_blob, "actual_git_blob_sha1": actual_blob}
                result["mismatches"].append(mismatch)
                all_mismatches.append(mismatch)
    return {"verified_files": verified_total, "mismatches": all_mismatches,
            "manifests": manifests}


def _matrix_lists(matrix):
    return [list(row) for row in matrix]


def _inverse_record(result):
    return {"recovered_state": list(result.generator),
            "null_basis": [list(vector) for vector in result.null_basis],
            "identifiable_rank": result.identifiable_rank,
            "residual": result.residual, "source_identified": result.source_identified}


def connected_operator_demo() -> dict[str, Any]:
    """Measure actual connected source operations against independent NumPy math."""
    a = ((2, 0), (0, 1))
    b = ((0, -1), (1, 0))
    fused = _algebra.fuse(a, b)
    expected_fused = np.asarray(b, dtype=np.int64) @ np.asarray(a, dtype=np.int64)
    projection = ((1, 0, 0), (0, 1, 0))
    information = _algebra.information_semantics(projection)
    information_rank = int(np.linalg.matrix_rank(np.asarray(projection)))

    # These are the original upstream test's matrices, with its incorrect
    # expected result retained separately from the measured mathematical result.
    work_a = ((1, 0), (0, 2))
    work_b = ((1, 1), (0, 1))
    work_p = ((0, 1),)
    work_result = _work.work_relative_commutation(work_a, work_b, work_p, 0.0)
    wa, wb, wp = (np.asarray(matrix, dtype=np.int64) for matrix in (work_a, work_b, work_p))
    ab, ba = wa @ wb, wb @ wa
    pab, pba = wp @ ab, wp @ ba
    observed_equal = bool(np.array_equal(pab, pba))

    transition = ((0, 1, 0), (0, 0, 1), (1, 0, 0))
    observation = ((1, 0, 0),)
    initial_state = np.array([1, 2, 3], dtype=np.int64)
    expected_observability = np.vstack([
        np.asarray(observation, dtype=np.int64) @ np.linalg.matrix_power(
            np.asarray(transition, dtype=np.int64), step)
        for step in range(3)
    ])
    samples = tuple((int(value),) for value in expected_observability @ initial_state)
    observed_matrix = _observability.observability_matrix(transition, observation, 3)
    reconstructed = _observability.dynamic_initial_state_inverse(transition, observation, samples)
    duplicate_matrix = ((1, 0, 0), (1, 0, 0), (-1, 0, 0))
    duplicate_samples = tuple(int(value) for value in np.asarray(duplicate_matrix) @ initial_state)
    duplicate = _inverse.linear_inverse(duplicate_matrix, duplicate_samples)
    duplicate_rank = int(np.linalg.matrix_rank(duplicate_matrix))

    checks = {
        "fusion_order": bool(np.array_equal(fused, expected_fused)),
        "information_rank_and_nullity": bool(information.rank == information_rank
                                              and information.nullity == 3 - information_rank),
        "observable_equivalence": bool(work_result.equivalent_for_work == observed_equal
                                       and work_result.exact_equal == np.array_equal(ab, ba)
                                       and work_result.observed_difference == np.linalg.norm(pab - pba)),
        "observability_matrix": bool(np.array_equal(observed_matrix, expected_observability)),
        "initial_state_reconstruction": bool(np.allclose(reconstructed.generator, initial_state,
                                                         atol=1e-12, rtol=0)
                                             and reconstructed.identifiable_rank == 3
                                             and not reconstructed.null_basis
                                             and reconstructed.residual <= 1e-12),
        "duplicate_direction_rank": bool(duplicate.identifiable_rank == duplicate_rank == 1
                                         and len(duplicate.null_basis) == 2
                                         and np.array_equal(np.asarray(duplicate_matrix) @ duplicate.generator,
                                                            duplicate_samples)),
        "source_identity_not_inferred": bool(not reconstructed.source_identified
                                             and not duplicate.source_identified),
    }
    return {
        "qualified": all(checks.values()), "checks": checks,
        "provenance": "new qualification inputs executed by unchanged pinned MAPEOGEO modules",
        "composition": {"A": _matrix_lists(a), "B": _matrix_lists(b),
                        "execution_order": ["A", "B"], "fused": _matrix_lists(fused),
                        "numpy_product": expected_fused.tolist(),
                        "max_abs_error": float(np.max(np.abs(np.asarray(fused) - expected_fused)))},
        "information": {"matrix": _matrix_lists(projection), **asdict(information)},
        "work_equivalence": {"A": _matrix_lists(work_a), "B": _matrix_lists(work_b),
                             "observation": _matrix_lists(work_p),
                             "AB": ab.tolist(), "BA": ba.tolist(),
                             "PAB": pab.tolist(), "PBA": pba.tolist(),
                             "upstream_result": asdict(work_result),
                             "upstream_test_expected_equivalent": False,
                             "corrected_expected_equivalent": observed_equal,
                             "upstream_test_status": "incorrect expectation for its supplied matrices"},
        "observability": {"transition": _matrix_lists(transition),
                          "observation": _matrix_lists(observation),
                          "matrix": _matrix_lists(observed_matrix),
                          "numpy_matrix": expected_observability.tolist(),
                          "initial_state": initial_state.tolist(),
                          "samples": _matrix_lists(samples), **_inverse_record(reconstructed)},
        "duplicate_observations": {"matrix": _matrix_lists(duplicate_matrix),
                                   "samples": list(duplicate_samples), "numpy_rank": duplicate_rank,
                                   **_inverse_record(duplicate)},
        "source_identified": False,
    }


def _enumerate_matrices(generators, max_elements=10000):
    """Deterministic BFS with explicit refusal to truncate a growing closure."""
    matrices = [_IDENTITY]
    words = [()]
    indices = {_IDENTITY: 0}
    queue = deque([0])
    while queue:
        current = queue.popleft()
        for name, generator in generators.items():
            candidate = _algebra.matmul(matrices[current], generator)
            if any(type(value) is not int for row in candidate for value in row):
                raise RuntimeError("exact closure multiplication produced a non-integer")
            if candidate not in indices:
                if len(matrices) >= max_elements:
                    raise RuntimeError(f"closure enumeration guard of {max_elements} elements exceeded")
                indices[candidate] = len(matrices)
                matrices.append(candidate)
                words.append(words[current] + (name,))
                queue.append(len(matrices) - 1)
    return matrices, words, indices


def _rational_rank(matrix):
    """Compute exact rank without tolerance or conversion to floating point."""
    rows = [[Fraction(value) for value in row] for row in matrix]
    rank = 0
    for column in range(len(rows[0])):
        pivot = next((index for index in range(rank, len(rows)) if rows[index][column]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        denominator = rows[rank][column]
        rows[rank] = [value / denominator for value in rows[rank]]
        for index in range(rank + 1, len(rows)):
            factor = rows[index][column]
            rows[index] = [value - factor * pivot_value
                           for value, pivot_value in zip(rows[index], rows[rank])]
        rank += 1
        if rank == len(rows):
            break
    return rank


def exact_closure() -> dict[str, Any]:
    """Enumerate and verify the new Rx90/Rz90/Pxy fixture without assuming size.

    Words name matrices multiplied left-to-right from the identity. Acting on a
    column vector applies the rightmost named matrix first. Nilpotence is checked
    by A**3 == 0, which is sufficient and necessary for nilpotent 3x3 matrices.
    """
    matrices, words, indices = _enumerate_matrices(_GENERATORS, max_elements=10000)
    size = len(matrices)
    identity_index = indices[_IDENTITY]
    zero_index = indices.get(_ZERO)
    numpy_matrices = np.asarray(matrices, dtype=np.int64)
    multiplication_table = []
    product_mismatches = 0
    for left, matrix in enumerate(matrices):
        row = []
        for right, other in enumerate(matrices):
            computed = _algebra.matmul(matrix, other)
            if computed not in indices:
                raise RuntimeError("enumerated set is not closed under an upstream matrix product")
            row.append(indices[computed])
            independent = numpy_matrices[left] @ numpy_matrices[right]
            product_mismatches += int(not np.array_equal(computed, independent))
        multiplication_table.append(row)
    table = np.asarray(multiplication_table, dtype=np.int64)
    associativity_mismatches = 0
    for left in range(size):
        left_grouping = table[table[left, :], :]
        right_grouping = table[left, table]
        associativity_mismatches += int(np.count_nonzero(left_grouping != right_grouping))

    rank_histogram = Counter(str(_rational_rank(matrix)) for matrix in matrices)
    units = [index for index in range(size)
             if any(multiplication_table[index][other] == identity_index
                    and multiplication_table[other][index] == identity_index
                    for other in range(size))]
    idempotents = [index for index in range(size) if multiplication_table[index][index] == index]
    nilpotents = [index for index in range(size)
                  if multiplication_table[multiplication_table[index][index]][index] == zero_index]
    commuting = table == table.T
    return {
        "provenance": "new qualification fixture; not recovered sealed artifact",
        "arithmetic": "exact Python integer products via unchanged MAPEOGEO algebra.matmul",
        "generator_order": list(_GENERATORS),
        "generators": {name: _matrix_lists(matrix) for name, matrix in _GENERATORS.items()},
        "word_convention": "left-to-right matrix product; rightmost operator acts first on column vectors",
        "size": size, "matrices": [_matrix_lists(matrix) for matrix in matrices],
        "shortest_words": [list(word) for word in words],
        "multiplication_table": multiplication_table,
        "identity_index": identity_index, "zero_index": zero_index,
        "rank_histogram": dict(sorted(rank_histogram.items())),
        "units": units, "idempotents": idempotents, "nilpotents": nilpotents,
        "center": np.flatnonzero(commuting.all(axis=1)).tolist(),
        "commuting_ordered_pairs": int(commuting.sum()),
        "validation": {"product_comparisons": size**2,
                       "product_mismatches": product_mismatches,
                       "associativity_triples": size**3,
                       "associativity_mismatches": associativity_mismatches},
    }
