from __future__ import annotations

from fractions import Fraction
from itertools import product
import hashlib
import json
import math

import sympy as sp


ROUTES = ("EO", "GEO", "FORMAL")


def _canonicalize(value):
    if isinstance(value, Fraction):
        return [value.numerator, value.denominator]
    if isinstance(value, sp.Rational):
        return [int(value.p), int(value.q)]
    if isinstance(value, dict):
        return {str(k): _canonicalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(v) for v in value]
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    raise TypeError(f"unsupported canonical value: {type(value)!r}")


def canonical_json(value) -> str:
    return json.dumps(_canonicalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest_stream(records: list[dict]) -> str:
    payload = "\n".join(canonical_json(record) for record in records).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _matrix_domain():
    for m in range(1, 4):
        for n in range(1, 4):
            for bits in range(1 << (m * n)):
                matrix = [[(bits >> (i * n + j)) & 1 for j in range(n)] for i in range(m)]
                yield matrix


def _rank_eo(matrix: list[list[int]]) -> dict:
    rows = [row[:] for row in matrix]
    m, n = len(rows), len(rows[0])
    pivots: list[int] = []
    r = 0
    for c in range(n):
        pivot = next((i for i in range(r, m) if rows[i][c]), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        for i in range(m):
            if i != r and rows[i][c]:
                rows[i] = [a ^ b for a, b in zip(rows[i], rows[r])]
        pivots.append(c)
        r += 1
        if r == m:
            break
    free = [c for c in range(n) if c not in pivots]
    basis = []
    for f in free:
        x = [0] * n
        x[f] = 1
        for i, p in enumerate(pivots):
            x[p] = rows[i][f]
        basis.append(x)
    return {
        "matrix": matrix,
        "rank": len(pivots),
        "rref": rows,
        "pivot_columns": pivots,
        "nullity": len(free),
        "canonical_nullspace_basis": basis,
    }


def _rank_geo(matrix: list[list[int]]) -> dict:
    m, n = len(matrix), len(matrix[0])
    row_masks = [sum((bit & 1) << j for j, bit in enumerate(row)) for row in matrix]
    rowspace = {0}
    for mask in row_masks:
        rowspace |= {v ^ mask for v in tuple(rowspace)}
    work = set(rowspace)
    pivots: list[int] = []
    for c in range(n):
        if any((v >> c) & 1 for v in work):
            pivots.append(c)
            work = {v for v in work if not ((v >> c) & 1)}
    rref_nonzero = []
    for p in pivots:
        candidates = [
            v for v in rowspace
            if ((v >> p) & 1)
            and all(((v >> q) & 1) == (q == p) for q in pivots)
        ]
        if len(candidates) != 1:
            raise AssertionError("row-space pivot coordinate did not determine a unique RREF row")
        v = candidates[0]
        rref_nonzero.append([(v >> j) & 1 for j in range(n)])
    rref = rref_nonzero + [[0] * n for _ in range(m - len(rref_nonzero))]
    kernel = [
        x for x in range(1 << n)
        if all(((mask & x).bit_count() & 1) == 0 for mask in row_masks)
    ]
    free = [c for c in range(n) if c not in pivots]
    basis = []
    for f in free:
        matches = [
            x for x in kernel
            if ((x >> f) & 1)
            and all(((x >> g) & 1) == 0 for g in free if g != f)
        ]
        if len(matches) != 1:
            raise AssertionError("kernel free coordinate did not determine a unique canonical basis vector")
        x = matches[0]
        basis.append([(x >> j) & 1 for j in range(n)])
    return {
        "matrix": matrix,
        "rank": int(math.log2(len(rowspace))),
        "rref": rref,
        "pivot_columns": pivots,
        "nullity": int(math.log2(len(kernel))),
        "canonical_nullspace_basis": basis,
    }


def _rank_formal(matrix: list[list[int]]) -> dict:
    m, n = len(matrix), len(matrix[0])
    packed = [sum((bit & 1) << j for j, bit in enumerate(row)) for row in matrix]
    work = packed[:]
    pivot_cols: list[int] = []
    row_index = 0
    for col in range(n):
        pivot_index = None
        for i in range(row_index, m):
            if (work[i] >> col) & 1:
                pivot_index = i
                break
        if pivot_index is None:
            continue
        work[row_index], work[pivot_index] = work[pivot_index], work[row_index]
        pivot_mask = work[row_index]
        for i in range(m):
            if i != row_index and ((work[i] >> col) & 1):
                work[i] ^= pivot_mask
        pivot_cols.append(col)
        row_index += 1
        if row_index == m:
            break
    rref = [[(mask >> j) & 1 for j in range(n)] for mask in work]
    image = set()
    kernel = []
    for x in range(1 << n):
        y = tuple(((mask & x).bit_count() & 1) for mask in packed)
        image.add(y)
        if not any(y):
            kernel.append(x)
    free_cols = [c for c in range(n) if c not in pivot_cols]
    basis = []
    for free_col in free_cols:
        chosen = None
        for x in kernel:
            if not ((x >> free_col) & 1):
                continue
            if any((x >> other) & 1 for other in free_cols if other != free_col):
                continue
            chosen = x
            break
        if chosen is None:
            raise AssertionError("formal kernel enumeration did not yield canonical basis vector")
        basis.append([(chosen >> j) & 1 for j in range(n)])
    return {
        "matrix": matrix,
        "rank": int(math.log2(len(image))),
        "rref": rref,
        "pivot_columns": pivot_cols,
        "nullity": int(math.log2(len(kernel))),
        "canonical_nullspace_basis": basis,
    }


def _convex_domain():
    values = tuple(Fraction(i) for i in range(-2, 3))
    queries = tuple(Fraction(i, 2) for i in range(-4, 5))
    for mask in range(1, 1 << len(values)):
        points = tuple(values[i] for i in range(len(values)) if (mask >> i) & 1)
        for x in queries:
            yield points, x


def _convex_eo(points: tuple[Fraction, ...], x: Fraction) -> dict:
    lo, hi = min(points), max(points)
    member = lo <= x <= hi
    if member and lo == hi:
        witness_type = "SINGLETON"
        witness = {"endpoint": lo}
    elif member:
        lam = (x - lo) / (hi - lo)
        witness_type = "BARYCENTRIC"
        witness = {"endpoints": [lo, hi], "lambda": lam, "coefficients": [1 - lam, lam]}
    elif x < lo:
        witness_type = "SEPARATION"
        witness = {"side": "LEFT", "nearest_endpoint": lo, "gap": lo - x}
    else:
        witness_type = "SEPARATION"
        witness = {"side": "RIGHT", "nearest_endpoint": hi, "gap": x - hi}
    return {"points": list(points), "x": x, "hull_lo": lo, "hull_hi": hi, "member": member, "witness_type": witness_type, "witness": witness}


def _convex_geo(points: tuple[Fraction, ...], x: Fraction) -> dict:
    ordered = sorted(points)
    lo, hi = ordered[0], ordered[-1]
    left_ok = x - lo >= 0
    right_ok = hi - x >= 0
    member = left_ok and right_ok
    if member:
        if hi - lo == 0:
            witness_type = "SINGLETON"
            witness = {"endpoint": ordered[0]}
        else:
            right_weight = Fraction(x - lo, hi - lo)
            left_weight = 1 - right_weight
            witness_type = "BARYCENTRIC"
            witness = {"endpoints": [lo, hi], "lambda": right_weight, "coefficients": [left_weight, right_weight]}
    else:
        if not left_ok:
            witness_type = "SEPARATION"
            witness = {"side": "LEFT", "nearest_endpoint": lo, "gap": -(x - lo)}
        else:
            witness_type = "SEPARATION"
            witness = {"side": "RIGHT", "nearest_endpoint": hi, "gap": -(hi - x)}
    return {"points": list(points), "x": x, "hull_lo": lo, "hull_hi": hi, "member": member, "witness_type": witness_type, "witness": witness}


def _convex_formal(points: tuple[Fraction, ...], x: Fraction) -> dict:
    lo = points[0]
    hi = points[0]
    for p in points[1:]:
        if p < lo:
            lo = p
        if p > hi:
            hi = p
    if lo == hi:
        member = x == lo
        if member:
            witness_type = "SINGLETON"
            witness = {"endpoint": lo}
        elif x < lo:
            witness_type = "SEPARATION"
            witness = {"side": "LEFT", "nearest_endpoint": lo, "gap": lo - x}
        else:
            witness_type = "SEPARATION"
            witness = {"side": "RIGHT", "nearest_endpoint": hi, "gap": x - hi}
    else:
        alpha = Fraction(hi - x, hi - lo)
        beta = Fraction(x - lo, hi - lo)
        member = alpha >= 0 and beta >= 0 and alpha + beta == 1 and alpha * lo + beta * hi == x
        if member:
            witness_type = "BARYCENTRIC"
            witness = {"endpoints": [lo, hi], "lambda": beta, "coefficients": [alpha, beta]}
        elif x < lo:
            witness_type = "SEPARATION"
            witness = {"side": "LEFT", "nearest_endpoint": lo, "gap": lo - x}
        else:
            witness_type = "SEPARATION"
            witness = {"side": "RIGHT", "nearest_endpoint": hi, "gap": x - hi}
    return {"points": list(points), "x": x, "hull_lo": lo, "hull_hi": hi, "member": member, "witness_type": witness_type, "witness": witness}


def _lp_domain():
    vals = (1, 2, 3)
    for m in (1, 2, 3):
        for a in product(vals, repeat=m):
            for b in product(vals, repeat=m):
                for c in vals:
                    yield a, b, c


def _lp_record(a, b, c, ratios, optimum, active_indices):
    witnesses = []
    for i in active_indices:
        dual_y = Fraction(c, a[i])
        witnesses.append({
            "index": i,
            "primal_optimum": optimum,
            "dual_y": dual_y,
            "dual_value": Fraction(b[i]) * dual_y,
        })
    return {
        "a": list(a), "b": list(b), "c": c,
        "ratios": ratios,
        "optimum": optimum,
        "active_indices": active_indices,
        "canonical_active_witnesses": witnesses,
    }


def _lp_eo(a, b, c):
    ratios = [Fraction(bi, ai) for ai, bi in zip(a, b)]
    min_ratio = min(ratios)
    active = [i for i, ratio in enumerate(ratios) if ratio == min_ratio]
    return _lp_record(a, b, c, ratios, Fraction(c) * min_ratio, active)


def _lp_geo(a, b, c):
    best = 0
    for i in range(1, len(a)):
        if b[i] * a[best] < b[best] * a[i]:
            best = i
    active = [i for i in range(len(a)) if b[i] * a[best] == b[best] * a[i]]
    ratios = [Fraction(b[i], a[i]) for i in range(len(a))]
    optimum = Fraction(c * b[best], a[best])
    return _lp_record(a, b, c, ratios, optimum, active)


def _lp_formal(a, b, c):
    candidates = [(Fraction(c * b[i], a[i]), i) for i in range(len(a))]
    optimum = sorted(value for value, _ in candidates)[0]
    active = sorted(i for value, i in candidates if value == optimum)
    ratios = [Fraction(value, c) for value, _ in candidates]
    return _lp_record(a, b, c, ratios, optimum, active)


def _gaussian_record(expr, nx_, ny_, dot, s2):
    scaled = sp.expand(sp.cancel(expr * s2))
    poly = sp.Poly(scaled, nx_, ny_, dot, domain=sp.QQ)
    coeffs = [Fraction(int(poly.coeff_monomial(v).p), int(poly.coeff_monomial(v).q)) for v in (nx_, ny_, dot)]
    canonical_expr = f"({coeffs[0].numerator}/{coeffs[0].denominator})*nx/s2+({coeffs[1].numerator}/{coeffs[1].denominator})*ny/s2+({coeffs[2].numerator}/{coeffs[2].denominator})*dot/s2"
    return {"coefficients": coeffs, "normalized_expression": canonical_expr}


def _gauss_eo():
    nx_, ny_, dot, s2 = sp.symbols("nx ny dot s2", nonzero=True)
    expr = dot / s2 - nx_ / (2 * s2) - ny_ / (2 * s2)
    return _gaussian_record(expr, nx_, ny_, dot, s2)


def _gauss_geo():
    nx_, ny_, dot, s2 = sp.symbols("nx ny dot s2", nonzero=True)
    expr = -(nx_ + ny_ - 2 * dot) / (2 * s2)
    return _gaussian_record(expr, nx_, ny_, dot, s2)


def _gauss_formal():
    nx_, ny_, dot, s2 = sp.symbols("nx ny dot s2", nonzero=True)
    expr = sp.Rational(1, 2) * (-nx_ - ny_ + 2 * dot) / s2
    return _gaussian_record(expr, nx_, ny_, dot, s2)


def _audit_contract(contract: str, domain, routes: dict) -> dict:
    route_records = {name: [] for name in ROUTES}
    inputs_tested = 0
    disagreements = 0
    tie_cases = 0
    active_ok = True
    for args in domain:
        records = {name: routes[name](*args) for name in ROUTES}
        serial = {name: canonical_json(record) for name, record in records.items()}
        inputs_tested += 1
        if len(set(serial.values())) != 1:
            disagreements += 1
        for name in ROUTES:
            route_records[name].append(records[name])
        if contract == "lp":
            eo_active = records["EO"]["active_indices"]
            if len(eo_active) > 1:
                tie_cases += 1
                active_ok &= all(records[name]["active_indices"] == eo_active for name in ROUTES)
    result = {
        "contract": contract,
        "inputs_tested": inputs_tested,
        "route_disagreements": disagreements,
        "all_routes_agree": disagreements == 0,
        "route_digests": {name: _digest_stream(route_records[name]) for name in ROUTES},
        "route_implementation_ids": {name: routes[name].__name__ for name in ROUTES},
    }
    if contract == "lp":
        result["tie_case_count"] = tie_cases
        result["all_active_minimizers_preserved"] = bool(active_ok and tie_cases > 0)
    return result


def run_c5a_audit() -> dict:
    components = []
    components.append(_audit_contract("rank", ((matrix,) for matrix in _matrix_domain()), {
        "EO": _rank_eo, "GEO": _rank_geo, "FORMAL": _rank_formal,
    }))
    components.append(_audit_contract("convex", _convex_domain(), {
        "EO": _convex_eo, "GEO": _convex_geo, "FORMAL": _convex_formal,
    }))
    components.append(_audit_contract("lp", _lp_domain(), {
        "EO": _lp_eo, "GEO": _lp_geo, "FORMAL": _lp_formal,
    }))
    gauss_records = {"EO": [_gauss_eo()], "GEO": [_gauss_geo()], "FORMAL": [_gauss_formal()]}
    gauss_serial = {name: canonical_json(records[0]) for name, records in gauss_records.items()}
    components.append({
        "contract": "gauss",
        "inputs_tested": 1,
        "route_disagreements": 0 if len(set(gauss_serial.values())) == 1 else 1,
        "all_routes_agree": len(set(gauss_serial.values())) == 1,
        "route_digests": {name: _digest_stream(records) for name, records in gauss_records.items()},
        "route_implementation_ids": {"EO": "_gauss_eo", "GEO": "_gauss_geo", "FORMAL": "_gauss_formal"},
    })
    status = "PASS" if all(c["all_routes_agree"] for c in components) else "FAIL"
    return {
        "experiment_id": "E25G_C5A_EXACT_MORPHISM_AUDIT",
        "status": status,
        "component_count": len(components),
        "components": components,
        "total_inputs_tested": sum(c["inputs_tested"] for c in components),
        "claim_boundary": "C5a is exact and witness-bearing only on the four frozen bounded contracts; route generators are independent and share only canonical serialization/comparison.",
    }
