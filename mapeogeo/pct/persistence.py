"""GF(2) persistence, column reduction, and event pairing ledgers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mapeogeo.pct.chain import canonical_simplex
from mapeogeo.pct.models import Simplex


@dataclass(frozen=True)
class FilteredSimplex:
    simplex: Simplex
    filtration: float


@dataclass(frozen=True)
class PersistencePair:
    dimension: int
    birth: float
    birth_simplex: Simplex
    death: float | None
    death_simplex: Simplex | None
    essential: bool


def validate_filtration_order(items: list[FilteredSimplex]) -> bool:
    """Verify that all proper faces precede the simplex and have filtration <= simplex.filtration."""
    seen: dict[tuple[int, ...], float] = {}
    for item in items:
        canon_s, _ = canonical_simplex(item.simplex)
        v = canon_s.vertices
        if canon_s.dimension > 0:
            for i in range(len(v)):
                face_v = v[:i] + v[i + 1:]
                if face_v not in seen:
                    return False
                if seen[face_v] > item.filtration + 1e-12:
                    return False
        seen[v] = item.filtration
    return True


def persistent_pairs_gf2(items: list[FilteredSimplex]) -> list[PersistencePair]:
    """Compute persistence pairs over GF(2) via standard column reduction."""
    # Canonicalize simplices and ensure consistent sort
    # Sort order: filtration ascending, then dimension ascending, then vertices
    sorted_items = sorted(
        items,
        key=lambda x: (x.filtration, x.simplex.dimension, tuple(sorted(x.simplex.vertices))),
    )

    simplex_to_idx = {
        canonical_simplex(item.simplex)[0].vertices: idx
        for idx, item in enumerate(sorted_items)
    }

    # Initialize boundary matrix columns as sets of face row indices
    cols: list[set[int]] = []
    for item in sorted_items:
        canon_s, _ = canonical_simplex(item.simplex)
        v = canon_s.vertices
        col_set: set[int] = set()
        if canon_s.dimension > 0:
            for i in range(len(v)):
                face_v = v[:i] + v[i + 1:]
                face_canon = tuple(sorted(face_v))
                if face_canon in simplex_to_idx:
                    col_set.add(simplex_to_idx[face_canon])
        cols.append(col_set)

    pivot_to_col: dict[int, int] = {}
    destroyer_cols: set[int] = set()

    def get_low(s: set[int]) -> int | None:
        return max(s) if s else None

    # Perform reduction
    for j in range(len(sorted_items)):
        low_j = get_low(cols[j])
        while low_j is not None and low_j in pivot_to_col:
            k = pivot_to_col[low_j]
            cols[j] = cols[j].symmetric_difference(cols[k])
            low_j = get_low(cols[j])

        if low_j is not None:
            pivot_to_col[low_j] = j
            destroyer_cols.add(j)

    pairs: list[PersistencePair] = []

    for i, item in enumerate(sorted_items):
        if i in destroyer_cols:
            continue

        canon_s, _ = canonical_simplex(item.simplex)
        dim = canon_s.dimension

        if i in pivot_to_col:
            j = pivot_to_col[i]
            death_item = sorted_items[j]
            death_s, _ = canonical_simplex(death_item.simplex)
            pairs.append(
                PersistencePair(
                    dimension=dim,
                    birth=float(item.filtration),
                    birth_simplex=canon_s,
                    death=float(death_item.filtration),
                    death_simplex=death_s,
                    essential=False,
                )
            )
        else:
            pairs.append(
                PersistencePair(
                    dimension=dim,
                    birth=float(item.filtration),
                    birth_simplex=canon_s,
                    death=None,
                    death_simplex=None,
                    essential=True,
                )
            )

    # Sort pairs stably by dimension, birth, death
    return sorted(
        pairs,
        key=lambda p: (p.dimension, p.birth, 0 if p.essential else 1, p.death if p.death is not None else -1.0),
    )


def betti_at(pairs: list[PersistencePair], t: float, max_dim: int = 2) -> dict[int, int]:
    """Compute Betti numbers beta_d at filtration value t."""
    betti: dict[int, int] = {d: 0 for d in range(max_dim + 1)}
    for p in pairs:
        if p.dimension > max_dim:
            continue
        if p.birth <= t:
            if p.essential or (p.death is not None and p.death > t):
                betti[p.dimension] += 1
    return betti


def euler_at(pairs: list[PersistencePair], t: float, max_dim: int = 2) -> int:
    """Compute Euler characteristic at filtration value t from Betti numbers."""
    b = betti_at(pairs, t, max_dim)
    return sum(((-1) ** d) * count for d, count in b.items())


def pairing_ledger(pairs: list[PersistencePair]) -> list[dict[str, Any]]:
    """Format persistence pairs into serializable ledger dictionaries."""
    ledger: list[dict[str, Any]] = []
    for p in pairs:
        ledger.append({
            "dimension": p.dimension,
            "birth": p.birth,
            "birth_simplex": list(p.birth_simplex.vertices),
            "death": p.death,
            "death_simplex": list(p.death_simplex.vertices) if p.death_simplex is not None else None,
            "essential": p.essential,
        })
    return ledger
