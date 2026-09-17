from __future__ import annotations

"""JSON stdin/stdout protocol executed with cwd and PYTHONPATH pinned to frozen main.

This file intentionally imports only stdlib until the experimental checkout has
been removed from sys.path.  Operations may translate adversarial inputs, but
all PCT capabilities under test are imported from the frozen main checkout.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
EXPERIMENTAL_ROOT = SCRIPT_PATH.parents[2]
MAIN_ROOT = Path.cwd().resolve()


def _resolved(entry: str) -> Path | None:
    try:
        return Path(entry or os.curdir).resolve()
    except OSError:
        return None


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _scrub_experimental_paths() -> None:
    cleaned: list[str] = []
    for entry in sys.path:
        resolved = _resolved(entry)
        if resolved is None:
            cleaned.append(entry)
            continue
        if _within(resolved, EXPERIMENTAL_ROOT) and not _within(resolved, MAIN_ROOT):
            continue
        cleaned.append(entry)
    sys.path[:] = cleaned
    main_text = str(MAIN_ROOT)
    if main_text in sys.path:
        sys.path.remove(main_text)
    sys.path.insert(0, main_text)


_scrub_experimental_paths()


def _checkout_sha() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=MAIN_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout.strip()


def _experimental_branch_on_sys_path() -> bool:
    for entry in sys.path:
        resolved = _resolved(entry)
        if resolved is None:
            continue
        if _within(resolved, EXPERIMENTAL_ROOT) and not _within(resolved, MAIN_ROOT):
            return True
    return False


def _runtime_identity() -> dict[str, Any]:
    import mapeogeo.pct as pct

    return {
        "checkout_sha": _checkout_sha(),
        "pct_module_path": str(Path(pct.__file__).resolve()),
        "experimental_branch_on_sys_path": _experimental_branch_on_sys_path(),
        "cwd": str(MAIN_ROOT),
    }


def _chain_map_corruption() -> dict[str, Any]:
    from mapeogeo.pct.fixtures import (
        triangle_loop_complex,
        triangle_loop_subdivided_complex,
    )
    from mapeogeo.pct.maps import check_chain_map, triangle_subdivision_map

    coarse = triangle_loop_complex()
    fine = triangle_loop_subdivided_complex()
    valid = check_chain_map(coarse, fine, triangle_subdivision_map(corrupt=False))
    corrupt = check_chain_map(coarse, fine, triangle_subdivision_map(corrupt=True))
    return {
        "valid_map_pass": bool(valid["pass"]),
        "corrupt_map_pass": bool(corrupt["pass"]),
        "corrupt_residual_nonzero_entries": {
            str(k): int(v) for k, v in corrupt["residual_nonzero_entries"].items()
        },
        "operation_source": "mapeogeo.pct.maps.check_chain_map",
    }


def _applicability_refusal() -> dict[str, Any]:
    from mapeogeo.pct.fixtures import build_control_corpus
    from mapeogeo.pct.geometry import check_convex_steiner

    corpus = build_control_corpus()
    reentrant = corpus["reentrant_control"]
    square = corpus["equal_area_square"]
    rejected = check_convex_steiner(
        reentrant.geometry, [0.1, 0.2], 1e-9, is_convex=reentrant.is_convex
    )
    accepted = check_convex_steiner(
        square.geometry, [0.1, 0.2], 1e-3, is_convex=square.is_convex
    )
    return {
        "reentrant_verdict": rejected.verdict.value,
        "reentrant_applicability": rejected.applicability.value,
        "square_verdict": accepted.verdict.value,
        "square_applicability": accepted.applicability.value,
        "operation_source": "mapeogeo.pct.geometry.check_convex_steiner",
    }


def _persistence_information_loss() -> dict[str, Any]:
    from mapeogeo.pct.models import Simplex
    from mapeogeo.pct.persistence import (
        PersistencePair,
        betti_at,
        euler_at,
        pairing_ledger,
    )

    # A: beta=(1,0), chi=1.  B: beta=(2,1), chi=1.
    # Both are valid persistence summaries at t=0 but carry different homology.
    a = [
        PersistencePair(0, 0.0, Simplex((0,)), None, None, True),
    ]
    b = [
        PersistencePair(0, 0.0, Simplex((0,)), None, None, True),
        PersistencePair(0, 0.0, Simplex((1,)), None, None, True),
        PersistencePair(1, 0.0, Simplex((0, 1)), None, None, True),
    ]
    beta_a = betti_at(a, 0.0, max_dim=1)
    beta_b = betti_at(b, 0.0, max_dim=1)
    chi_a = euler_at(a, 0.0, max_dim=1)
    chi_b = euler_at(b, 0.0, max_dim=1)
    ledger_a = pairing_ledger(a)
    ledger_b = pairing_ledger(b)
    return {
        "betti_a": {str(k): int(v) for k, v in beta_a.items()},
        "betti_b": {str(k): int(v) for k, v in beta_b.items()},
        "euler_a": int(chi_a),
        "euler_b": int(chi_b),
        "same_euler": chi_a == chi_b,
        "different_betti": beta_a != beta_b,
        "different_persistence": ledger_a != ledger_b,
        "operation_source": "mapeogeo.pct.persistence.betti_at/euler_at",
    }


def _exact_rank_float_control(request: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import sympy as sp

    from mapeogeo.pct.chain import rank_over_field
    from mapeogeo.pct.models import CoefficientField

    n = int(request.get("n", 11))
    exact_matrix = sp.Matrix(
        [[sp.Rational(1, i + j + 1) for j in range(n)] for i in range(n)]
    )
    exact_rank = int(rank_over_field(exact_matrix, CoefficientField.Q))

    # The floating calculation is an adversarial comparator, not a replacement
    # implementation of the main exact-rank operation.
    float_matrix = np.array(
        [[1.0 / float(i + j + 1) for j in range(n)] for i in range(n)],
        dtype=np.float64,
    )
    float_rank = int(np.linalg.matrix_rank(float_matrix))
    return {
        "n": n,
        "exact_rank": exact_rank,
        "float_rank": float_rank,
        "rank_loss_detected": exact_rank > float_rank,
        "exact_operation_source": "mapeogeo.pct.chain.rank_over_field",
        "float_control_source": "numpy.linalg.matrix_rank",
    }


def _dispatch(request: dict[str, Any]) -> dict[str, Any]:
    op = request.get("op")
    if op == "runtime_identity":
        result = _runtime_identity()
    elif op == "chain_map_corruption":
        result = _chain_map_corruption()
    elif op == "applicability_refusal":
        result = _applicability_refusal()
    elif op == "persistence_information_loss":
        result = _persistence_information_loss()
    elif op == "exact_rank_float_control":
        result = _exact_rank_float_control(request)
    else:
        raise ValueError(f"Unknown frozen-main protocol operation: {op!r}")

    result.setdefault("checkout_sha", _checkout_sha())
    result.setdefault("experimental_branch_on_sys_path", _experimental_branch_on_sys_path())
    return result


def main() -> int:
    try:
        request = json.loads(sys.stdin.read())
        if not isinstance(request, dict):
            raise TypeError("Protocol request must be a JSON object")
        output = _dispatch(request)
        sys.stdout.write(json.dumps(output, sort_keys=True, separators=(",", ":")))
        return 0
    except Exception as exc:  # fail-closed protocol envelope
        error = {
            "error": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        sys.stdout.write(json.dumps(error, sort_keys=True, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
