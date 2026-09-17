from __future__ import annotations

from fractions import Fraction
from itertools import combinations, product
import math

import sympy as sp

from .multipath import load_trust_projection, _index, _source_hash

_CYCLES = (
    {
        "contract": "rank",
        "anchor": "srcdecl:theorem:6_16",
        "eo": "repr:eo:theorem:6_16",
        "geo": "repr:geo:theorem:6_16",
        "formal": "formal:lean:theorem_6_16",
    },
    {
        "contract": "convex",
        "anchor": "srcdecl:definition:44_6",
        "eo": "repr:eo:definition:44_6",
        "geo": "repr:geo:definition:44_6",
        "formal": "formal:lean:definition_44_6",
    },
    {
        "contract": "lp",
        "anchor": "srcdecl:theorem:47_9",
        "eo": "repr:eo:theorem:47_9",
        "geo": "repr:geo:theorem:47_9",
        "formal": "formal:lean:theorem_47_9",
    },
    {
        "contract": "gauss",
        "anchor": "srcdecl:definition:53_4",
        "eo": "repr:eo:definition:53_4",
        "geo": "repr:geo:definition:53_4",
        "formal": "formal:lean:definition_53_4",
    },
)


def _gf2_rank(rows: list[int], n: int) -> int:
    rows = list(rows)
    rank = 0
    col = 0
    while col < n and rank < len(rows):
        pivot = next((i for i in range(rank, len(rows)) if (rows[i] >> col) & 1), None)
        if pivot is None:
            col += 1
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(len(rows)):
            if i != rank and ((rows[i] >> col) & 1):
                rows[i] ^= rows[rank]
        rank += 1
        col += 1
    return rank


def _rank_contract(mutate_view: str | None = None) -> tuple[int, int, bool]:
    checks = equalities = 0
    all_ok = True
    mutated = False
    for m in range(1, 4):
        for n in range(1, 4):
            for bits in range(1 << (m * n)):
                rows = [sum(((bits >> (i*n+j)) & 1) << j for j in range(n)) for i in range(m)]
                rank = _gf2_rank(rows, n)
                kernel = [x for x in range(1 << n) if all((row & x).bit_count() % 2 == 0 for row in rows)]
                eo = rank + int(math.log2(len(kernel)))

                image = set()
                kernel_count = 0
                for x in range(1 << n):
                    y = tuple((row & x).bit_count() % 2 for row in rows)
                    image.add(y)
                    kernel_count += all(v == 0 for v in y)
                geo = int(math.log2(len(image))) + int(math.log2(kernel_count))
                formal = n
                if mutate_view == "GEO" and not mutated:
                    geo += 1
                    mutated = True
                values = (eo, geo, formal)
                checks += 1
                for a, b in combinations(values, 2):
                    equalities += 1
                    all_ok &= a == b
    return checks, equalities, all_ok


def _convex_contract(mutate_view: str | None = None) -> tuple[int, int, bool]:
    vals = [Fraction(i) for i in range(-2, 3)]
    queries = [Fraction(i, 2) for i in range(-4, 5)]
    checks = equalities = 0
    all_ok = True
    mutated = False
    for mask in range(1, 1 << 5):
        pts = [vals[i] for i in range(5) if (mask >> i) & 1]
        lo, hi = min(pts), max(pts)
        for x in queries:
            if lo == hi:
                eo = x == lo
                formal = x == lo
            else:
                lam = (x - lo) / (hi - lo)
                eo = 0 <= lam <= 1 and (1 - lam) * lo + lam * hi == x
                formal = (x - lo) >= 0 and (hi - x) >= 0
            geo = lo <= x <= hi
            if mutate_view == "GEO" and not mutated:
                geo = not geo
                mutated = True
            values = (eo, geo, formal)
            checks += 1
            for a, b in combinations(values, 2):
                equalities += 1
                all_ok &= a == b
    return checks, equalities, all_ok


def _tuples(values: tuple[int, ...], length: int):
    yield from product(values, repeat=length)


def _lp_contract(mutate_view: str | None = None) -> tuple[int, int, bool]:
    vals = (1, 2, 3)
    checks = equalities = 0
    all_ok = True
    mutated = False
    for m in (1, 2, 3):
        for a in _tuples(vals, m):
            for b in _tuples(vals, m):
                for c in vals:
                    ratios = [Fraction(bi, ai) for ai, bi in zip(a, b)]
                    eo = Fraction(c) * min(ratios)
                    active = min(range(m), key=ratios.__getitem__)
                    geo = Fraction(b[active]) * Fraction(c, a[active])
                    formal = sorted(Fraction(c) * r for r in ratios)[0]
                    if mutate_view == "GEO" and not mutated:
                        geo += 1
                        mutated = True
                    values = (eo, geo, formal)
                    checks += 1
                    for x, y in combinations(values, 2):
                        equalities += 1
                        all_ok &= x == y
    return checks, equalities, all_ok


def _gauss_contract(mutate_view: str | None = None) -> tuple[int, int, bool]:
    nx_, ny_, dot, s2 = sp.symbols("nx ny dot s2", nonzero=True)
    eo = sp.expand(dot/s2 - nx_/(2*s2) - ny_/(2*s2))
    geo = sp.expand(-(nx_ + ny_ - 2*dot)/(2*s2))
    formal = sp.expand((-nx_ - ny_ + 2*dot)/(2*s2))
    if mutate_view == "GEO":
        geo = sp.expand(geo + 1/s2)
    values = (eo, geo, formal)
    equalities = 0
    all_ok = True
    for x, y in combinations(values, 2):
        equalities += 1
        all_ok &= sp.simplify(x - y) == 0
    return 1, equalities, all_ok


_EXECUTORS = {
    "rank": _rank_contract,
    "convex": _convex_contract,
    "lp": _lp_contract,
    "gauss": _gauss_contract,
}


def run_e25c(mutate_contract: str | None = None, mutate_view: str | None = None) -> dict:
    projection = load_trust_projection()
    nodes, _ = _index(projection)
    cycles = []
    total_inputs = 0
    total_equalities = 0
    for config in _CYCLES:
        for key in ("anchor", "eo", "geo", "formal"):
            if config[key] not in nodes:
                raise KeyError(f"missing E25C node: {config[key]}")
        eo_contract = nodes[config["eo"]].get("attributes", {}).get("contract")
        geo_contract = nodes[config["geo"]].get("attributes", {}).get("contract")
        if eo_contract != config["contract"] or geo_contract != config["contract"]:
            raise ValueError(f"contract mismatch for {config['contract']}")
        formal_scope = nodes[config["formal"]].get("attributes", {}).get("formal_scope")
        source_hashes = {
            _source_hash(nodes[nid])
            for nid in (config["anchor"], config["eo"], config["geo"], config["formal"])
            if _source_hash(nodes[nid])
        }
        if len(source_hashes) != 1:
            raise ValueError(f"source-hash inconsistency in executable cycle {config['contract']}")

        mutation = mutate_view if mutate_contract == config["contract"] else None
        exact_inputs, pairwise_equalities, all_paths_agree = _EXECUTORS[config["contract"]](mutation)
        total_inputs += exact_inputs
        total_equalities += pairwise_equalities
        cycles.append({
            **config,
            "formal_scope": formal_scope,
            "source_statement_sha256": next(iter(source_hashes)),
            "exact_inputs": exact_inputs,
            "pairwise_path_equalities": pairwise_equalities,
            "all_paths_agree": bool(all_paths_agree),
        })

    status = "PASS" if all(c["all_paths_agree"] for c in cycles) else "FAIL"
    return {
        "experiment_id": "E25C_EXECUTABLE_CYCLE_CONSISTENCY",
        "status": status,
        "cycle_count": len(cycles),
        "total_exact_inputs": total_inputs,
        "total_pairwise_path_equalities": total_equalities,
        "cycles": cycles,
        "maximum_executed_closure_level": "C2_EXECUTABLE_CONTRACT",
        "C3_chain_map": "NOT_APPLICABLE_TO_THESE_FOUR_CONTRACTS",
        "C4_induced_homology": "NOT_APPLICABLE_TO_THESE_FOUR_CONTRACTS",
        "C5_exact_morphism_provenance": "NOT_ESTABLISHED",
        "claim_boundary": (
            "E25C attaches executable contract adapters to the four existing source-bound EO/GEO/FORMAL cycles. "
            "The adapters instantiate the persisted v0.7 contracts and v0.8 formal scopes; they do not assert that "
            "all repository edges already contained executable morphisms or promote C3-C5 evidence."
        ),
    }
