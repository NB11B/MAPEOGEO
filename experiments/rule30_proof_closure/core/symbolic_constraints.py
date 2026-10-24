"""Exact Algebraic Normal Form (ANF over F_2) symbolic constraint engine for bilateral cone variables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple


Monomial = FrozenSet[str]


@dataclass(frozen=True)
class ANFPolynomial:
    """Boolean polynomial over F_2 represented as a set of square-free monomials."""

    monomials: FrozenSet[Monomial]

    @staticmethod
    def zero() -> "ANFPolynomial":
        return ANFPolynomial(frozenset())

    @staticmethod
    def one() -> "ANFPolynomial":
        return ANFPolynomial(frozenset([frozenset()]))

    @staticmethod
    def const(val: int) -> "ANFPolynomial":
        return ANFPolynomial.one() if (val & 1) else ANFPolynomial.zero()

    @staticmethod
    def var(name: str) -> "ANFPolynomial":
        return ANFPolynomial(frozenset([frozenset([name])]))

    def __xor__(self, other: "ANFPolynomial") -> "ANFPolynomial":
        return ANFPolynomial(self.monomials ^ other.monomials)

    def __and__(self, other: "ANFPolynomial") -> "ANFPolynomial":
        acc: Set[Monomial] = set()
        for m1 in self.monomials:
            for m2 in other.monomials:
                prod = m1 | m2
                if prod in acc:
                    acc.remove(prod)
                else:
                    acc.add(prod)
        return ANFPolynomial(frozenset(acc))

    def __or__(self, other: "ANFPolynomial") -> "ANFPolynomial":
        return self ^ other ^ (self & other)

    def __invert__(self) -> "ANFPolynomial":
        return self ^ ANFPolynomial.one()

    @property
    def degree(self) -> int:
        if not self.monomials:
            return 0
        return max(len(m) for m in self.monomials)

    @property
    def num_monomials(self) -> int:
        return len(self.monomials)

    @property
    def variables(self) -> Set[str]:
        out: Set[str] = set()
        for m in self.monomials:
            out.update(m)
        return out

    def evaluate(self, assignment: Dict[str, int]) -> int:
        val = 0
        for m in self.monomials:
            if all(assignment.get(v, 0) == 1 for v in m):
                val ^= 1
        return val


def rule30_anf(left: ANFPolynomial, center: ANFPolynomial, right: ANFPolynomial) -> ANFPolynomial:
    """Symbolic Rule 30 update over F_2: left XOR (center OR right)."""
    return left ^ (center | right)


@dataclass(frozen=True)
class SymbolicConeSystem:
    """Symbolic ANF constraint system for bilateral cone compatibility at transient T and word w."""

    transient_t: int
    word: Tuple[int, ...]
    horizon: int
    left_vars: Tuple[str, ...]
    right_vars: Tuple[str, ...]
    obs_left_polys: Tuple[ANFPolynomial, ...]
    obs_right_polys: Tuple[ANFPolynomial, ...]
    discrepancy_polys: Tuple[ANFPolynomial, ...]
    max_degree: int
    total_monomials: int
    satisfying_assignments: Tuple[Dict[str, int], ...]
    first_unsat_horizon: Optional[int]


def build_bilateral_cone_anf_system(
    transient_t: int,
    word: Sequence[int],
    horizon: int,
) -> SymbolicConeSystem:
    """Construct exact ANF polynomials for obs_left(s) and obs_right(s) over cone variables at time T."""
    w = tuple(int(c) for c in word)
    p_len = len(w)
    left_vars = tuple(f"l_{i}" for i in range(1, max(1, transient_t)))
    right_vars = tuple(f"r_{i}" for i in range(1, max(1, transient_t)))

    # Initialize left and right half-lines at time T
    cur_left: Dict[int, ANFPolynomial] = {}
    cur_right: Dict[int, ANFPolynomial] = {}
    if transient_t >= 1:
        for i in range(1, transient_t):
            cur_left[-i] = ANFPolynomial.var(f"l_{i}")
            cur_right[i] = ANFPolynomial.var(f"r_{i}")
        cur_left[-transient_t] = ANFPolynomial.one()
        cur_right[transient_t] = ANFPolynomial.one()

    obs_left_list: List[ANFPolynomial] = []
    obs_right_list: List[ANFPolynomial] = []
    disc_list: List[ANFPolynomial] = []

    for s in range(horizon):
        c_s = ANFPolynomial.const(w[s % p_len])
        c_next = ANFPolynomial.const(w[(s + 1) % p_len])

        l_m1 = cur_left.get(-1, ANFPolynomial.zero())
        r_p1 = cur_right.get(1, ANFPolynomial.zero())

        obs_l = c_next ^ l_m1
        obs_r = c_s | r_p1
        obs_left_list.append(obs_l)
        obs_right_list.append(obs_r)
        disc_list.append(obs_l ^ obs_r)

        nxt_left: Dict[int, ANFPolynomial] = {}
        for pos in range(-(transient_t + s + 1), 0):
            lp = cur_left.get(pos - 1, ANFPolynomial.zero())
            cp = cur_left.get(pos, ANFPolynomial.zero())
            rp = cur_left.get(pos + 1, ANFPolynomial.zero()) if pos + 1 <= -1 else c_s
            nxt_left[pos] = rule30_anf(lp, cp, rp)

        nxt_right: Dict[int, ANFPolynomial] = {}
        for pos in range(1, transient_t + s + 2):
            lp = cur_right.get(pos - 1, ANFPolynomial.zero()) if pos - 1 >= 1 else c_s
            cp = cur_right.get(pos, ANFPolynomial.zero())
            rp = cur_right.get(pos + 1, ANFPolynomial.zero())
            nxt_right[pos] = rule30_anf(lp, cp, rp)

        cur_left = nxt_left
        cur_right = nxt_right

    all_vars = left_vars + right_vars
    num_vars = len(all_vars)
    active_assignments: List[Dict[str, int]] = []
    for mask in range(1 << num_vars):
        active_assignments.append(
            {all_vars[idx]: (mask >> idx) & 1 for idx in range(num_vars)}
        )

    first_unsat: Optional[int] = None
    surviving = list(active_assignments)
    for s, d_poly in enumerate(disc_list):
        surviving = [asg for asg in surviving if d_poly.evaluate(asg) == 0]
        if not surviving and first_unsat is None:
            first_unsat = s + 1

    max_deg = max((p.degree for p in disc_list), default=0)
    tot_mon = sum(p.num_monomials for p in disc_list)

    return SymbolicConeSystem(
        transient_t=transient_t,
        word=w,
        horizon=horizon,
        left_vars=left_vars,
        right_vars=right_vars,
        obs_left_polys=tuple(obs_left_list),
        obs_right_polys=tuple(obs_right_list),
        discrepancy_polys=tuple(disc_list),
        max_degree=max_deg,
        total_monomials=tot_mon,
        satisfying_assignments=tuple(surviving),
        first_unsat_horizon=first_unsat,
    )
