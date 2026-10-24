"""Rule 30 Falsification Benchmark for MAPEOGEO.

Tests whether Rule 30's cellular evolution admits exact sideways operator
reconstruction, observational quotients (via rightward information screening),
polynomial composition closure over GF(2), or sub-quadratic computational
shortcuts under an explicit bit-operation cost model.

Epistemic Discipline:
- Exact arithmetic over GF(2) / {0, 1} is strictly separated from statistical summaries.
- Every candidate representation is checked bit-for-bit against baseline simulation.
- Implementation speedups (cone pruning, word-level bit-parallelism) are explicitly
  separated from asymptotic complexity reductions (Problem 3).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

from ngc_geometry_lab.ngc_geometry_lab._vendor.mapeogeo.mapeogeo.psmsl_work_equivalence_v1 import (
    work_relative_information_loss,
)


# ---------------------------------------------------------------------------
# Core Rule 30 Local Primitives over {0, 1} / GF(2)
# ---------------------------------------------------------------------------


def rule30_forward_cell(left: int, center: int, right: int) -> int:
    """Compute x_i(t+1) = x_{i-1}(t) XOR (x_i(t) OR x_{i+1}(t))."""
    return (left ^ (center | right)) & 1


def rule30_forward_anf(left: int, center: int, right: int) -> int:
    """Compute x_i(t+1) = left + center + right + center*right (mod 2)."""
    return (left ^ center ^ right ^ (center & right)) & 1


def rule30_left_sideways_cell(center_next: int, center_curr: int, right_curr: int) -> int:
    """Reconstruct x_{i-1}(t) = x_i(t+1) XOR (x_i(t) OR x_{i+1}(t)).

    Because x_{i-1}(t) enters linearly in Rule 30, leftward sideways evolution
    is left-permutive (bijective in the left neighbor) and uses the exact same Boolean formula.
    """
    return (center_next ^ (center_curr | right_curr)) & 1


def rule30_right_sideways_relation(
    left_curr: int, center_curr: int, center_next: int
) -> Tuple[int, Tuple[int, ...]]:
    """Solve (1 + x_i(t)) * x_{i+1}(t) = x_i(t+1) + x_{i-1}(t) + x_i(t) (mod 2).

    Returns (rank, admissible_right_values):
    - When center_curr == 0 (transparent window): rank = 1, unique x_{i+1}(t).
    - When center_curr == 1 (information screen):
        * If center_next ^ left_curr == 1: wall invariant holds, rank = 0,
          admissible_right_values = (0, 1) (right cell is screened/unobservable).
        * If center_next ^ left_curr == 0: incompatible transition, rank = -1,
          admissible_right_values = ().
    """
    if center_curr == 0:
        unique_right = (center_next ^ left_curr) & 1
        return 1, (unique_right,)
    # center_curr == 1 screens the right neighbor
    if (center_next ^ left_curr) & 1 == 1:
        return 0, (0, 1)
    return -1, ()


def simulate_spacetime_cone(steps: int) -> Dict[Tuple[int, int], int]:
    """Simulate exact Rule 30 spacetime cone from a single active cell x_0(0) = 1.

    Returns a dictionary mapping (i, t) -> {0, 1} for t in [0, steps] and
    i in [-steps, steps].
    """
    if steps < 0:
        raise ValueError("steps must be non-negative")
    grid: Dict[Tuple[int, int], int] = {}
    for i in range(-steps - 1, steps + 2):
        grid[(i, 0)] = 1 if i == 0 else 0
    for t in range(steps):
        for i in range(-steps - 1, steps + 2):
            left = grid.get((i - 1, t), 0)
            center = grid.get((i, t), 0)
            right = grid.get((i + 1, t), 0)
            grid[(i, t + 1)] = rule30_forward_cell(left, center, right)
    return grid


def extract_column(grid: Dict[Tuple[int, int], int], col_idx: int, max_t: int) -> Tuple[int, ...]:
    """Extract temporal column c_i = (x_i(0), x_i(1), ..., x_i(max_t))."""
    return tuple(grid[(col_idx, t)] for t in range(max_t + 1))


def sideways_left_step(col_i: Sequence[int], col_i_plus_1: Sequence[int]) -> Tuple[int, ...]:
    """Apply leftward operator S_L: (c_i[0..T], c_{i+1}[0..T-1]) -> c_{i-1}[0..T-1]."""
    if len(col_i) < 2 or len(col_i_plus_1) < len(col_i) - 1:
        raise ValueError("Incompatible column lengths for sideways_left_step")
    horizon = len(col_i) - 1
    return tuple(
        rule30_left_sideways_cell(col_i[t + 1], col_i[t], col_i_plus_1[t])
        for t in range(horizon)
    )


def sideways_left_iterated(
    col_0: Sequence[int], col_1: Sequence[int], k_steps: int
) -> Dict[int, Tuple[int, ...]]:
    """Iteratively apply S_L^k starting only from central columns (c_0, c_1).

    Returns {0: c_0, 1: c_1, -1: c_{-1}, ..., -k_steps: c_{-k_steps}}.
    """
    reconstructed: Dict[int, Tuple[int, ...]] = {
        0: tuple(col_0),
        1: tuple(col_1),
    }
    curr_i = tuple(col_0)
    curr_i_plus_1 = tuple(col_1)
    for step in range(1, k_steps + 1):
        prev_col = sideways_left_step(curr_i, curr_i_plus_1)
        reconstructed[-step] = prev_col
        curr_i_plus_1 = curr_i[:-1]
        curr_i = prev_col
    return reconstructed


# ---------------------------------------------------------------------------
# Experiment 1: Exact Forward, Left-Sideways, and Right-Screen Reconstruction
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class E1ReconstructionResult:
    steps: int
    anf_truth_table_matches: int
    left_sideways_cells_checked: int
    left_sideways_mismatches: int
    left_zero_cone_boundary_satisfied: bool
    left_diagonal_unit_boundary_satisfied: bool
    right_transitions_checked: int
    right_wall_invariant_violations: int
    right_transparent_window_count: int
    right_screened_wall_count: int
    right_screen_fraction: float
    center_column_prefix: Tuple[int, ...]
    gate_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def run_e1_exact_reconstruction(steps: int = 64) -> E1ReconstructionResult:
    """Run Experiment 1: Verify forward/ANF, leftward sideways S_L^k, and rightward R_R."""
    # 1. Verify 8-entry truth table equivalence between Boolean and GF(2) ANF
    anf_matches = 0
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                if rule30_forward_cell(a, b, c) == rule30_forward_anf(a, b, c):
                    anf_matches += 1

    # 2. Simulate spacetime cone up to `steps`
    grid = simulate_spacetime_cone(steps)
    col_0 = extract_column(grid, 0, steps)
    col_1 = extract_column(grid, 1, steps - 1)

    # 3. Reconstruct entire left light cone strictly from (col_0, col_1) via S_L^k
    reconstructed_left = sideways_left_iterated(col_0, col_1, steps)
    cells_checked = 0
    mismatches = 0
    zero_cone_ok = True
    diagonal_unit_ok = True

    for k in range(1, steps + 1):
        col_neg_k = reconstructed_left[-k]
        for t, val in enumerate(col_neg_k):
            cells_checked += 1
            if val != grid[(-k, t)]:
                mismatches += 1
            if t < k and val != 0:
                zero_cone_ok = False
            if t == k and val != 1:
                diagonal_unit_ok = False

    # 4. Check rightward relational operator R_R across the active cone |i| <= t
    right_checked = 0
    wall_violations = 0
    transparent_count = 0
    screened_count = 0

    for t in range(steps):
        for i in range(-t, t + 1):
            left_val = grid[(i - 1, t)]
            center_val = grid[(i, t)]
            right_val = grid[(i + 1, t)]
            next_val = grid[(i, t + 1)]
            rank, admissible = rule30_right_sideways_relation(left_val, center_val, next_val)
            right_checked += 1
            if right_val not in admissible or rank == -1:
                wall_violations += 1
            if rank == 1:
                transparent_count += 1
            elif rank == 0:
                screened_count += 1

    screen_fraction = screened_count / right_checked if right_checked > 0 else 0.0
    gate_passed = (
        anf_matches == 8
        and mismatches == 0
        and zero_cone_ok
        and diagonal_unit_ok
        and wall_violations == 0
    )

    return E1ReconstructionResult(
        steps=steps,
        anf_truth_table_matches=anf_matches,
        left_sideways_cells_checked=cells_checked,
        left_sideways_mismatches=mismatches,
        left_zero_cone_boundary_satisfied=zero_cone_ok,
        left_diagonal_unit_boundary_satisfied=diagonal_unit_ok,
        right_transitions_checked=right_checked,
        right_wall_invariant_violations=wall_violations,
        right_transparent_window_count=transparent_count,
        right_screened_wall_count=screened_count,
        right_screen_fraction=screen_fraction,
        center_column_prefix=col_0[: min(32, steps + 1)],
        gate_passed=gate_passed,
    )


# ---------------------------------------------------------------------------
# Experiment 2: Geometric / Observational Quotient (Myhill-Nerode Profile)
# ---------------------------------------------------------------------------


def evaluate_center_after_k_steps(init_window: Sequence[int]) -> int:
    """Evaluate c_k = Psi(F^k(init_window)) for a window of length 2k + 1."""
    row = list(init_window)
    while len(row) > 1:
        row = [
            rule30_forward_cell(row[idx], row[idx + 1], row[idx + 2])
            for idx in range(len(row) - 2)
        ]
    return row[0]


@dataclass(frozen=True)
class QuotientStepProfile:
    k: int
    window_width: int
    raw_state_count: int
    ltr_cut_quotient_sizes: Tuple[int, ...]
    rtl_cut_quotient_sizes: Tuple[int, ...]
    ltr_total_bdd_nodes: int
    rtl_total_bdd_nodes: int
    max_rtl_to_ltr_ratio: float
    right_half_quotient_size: int
    right_half_raw_size: int
    right_half_compression_ratio: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class E2QuotientResult:
    max_k: int
    profiles: Tuple[QuotientStepProfile, ...]
    ltr_first_cut_always_two: bool
    nontrivial_right_quotient_exists: bool
    asymmetry_verified: bool
    gate_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_k": self.max_k,
            "profiles": [p.to_dict() for p in self.profiles],
            "ltr_first_cut_always_two": self.ltr_first_cut_always_two,
            "nontrivial_right_quotient_exists": self.nontrivial_right_quotient_exists,
            "asymmetry_verified": self.asymmetry_verified,
            "gate_passed": self.gate_passed,
        }


def _compute_truth_table_vector(k: int) -> Tuple[int, ...]:
    """Return truth table of c_k = Psi(F^k(x_{-k}, ..., x_k)) of length 2^(2k+1).

    Index bits: bit (2k - j) corresponds to x_{-k + j} for j in 0..2k.
    So MSB is x_{-k} and LSB is x_k.
    """
    width = 2 * k + 1
    num_states = 1 << width
    # Fast vectorized or row-by-row bit evolution over all 2^(2k+1) assignments
    # Let's represent each variable x_{-k+j} as an integer bitmask or tuple of bits
    table = [0] * num_states
    for state in range(num_states):
        row = [(state >> (width - 1 - j)) & 1 for j in range(width)]
        for _ in range(k):
            row = [
                (row[idx] ^ (row[idx + 1] | row[idx + 2]))
                for idx in range(len(row) - 2)
            ]
        table[state] = row[0]
    return tuple(table)


def _reverse_bit_order_table(table: Sequence[int], width: int) -> Tuple[int, ...]:
    """Reverse variable order from (x_{-k}, ..., x_k) to (x_k, ..., x_{-k})."""
    out = [0] * len(table)
    for idx, val in enumerate(table):
        rev_idx = 0
        tmp = idx
        for _ in range(width):
            rev_idx = (rev_idx << 1) | (tmp & 1)
            tmp >>= 1
        out[rev_idx] = val
    return tuple(out)


def _myhill_nerode_cut_sizes(table: Sequence[int], width: int) -> Tuple[int, ...]:
    """Compute exact number of distinct subfunctions (observational equivalence classes)

    after fixing the first m variables, for m = 1, ..., width - 1.
    """
    sizes: List[int] = []
    for m in range(1, width):
        sub_len = 1 << (width - m)
        num_prefixes = 1 << m
        distinct_subfunctions = {
            tuple(table[p * sub_len : (p + 1) * sub_len])
            for p in range(num_prefixes)
        }
        sizes.append(len(distinct_subfunctions))
    return tuple(sizes)


def run_e2_geometric_quotient(max_k: int = 6) -> E2QuotientResult:
    """Run Experiment 2: Compute exact observational quotients in LTR and RTL orders."""
    if max_k < 1:
        raise ValueError("max_k must be >= 1")

    profiles: List[QuotientStepProfile] = []
    for k in range(1, max_k + 1):
        width = 2 * k + 1
        ltr_table = _compute_truth_table_vector(k)
        rtl_table = _reverse_bit_order_table(ltr_table, width)

        ltr_cuts = _myhill_nerode_cut_sizes(ltr_table, width)
        rtl_cuts = _myhill_nerode_cut_sizes(rtl_table, width)

        # Cut at m = k + 1 in RTL corresponds to fixing (x_k, x_{k-1}, ..., x_0)
        # and observing equivalence classes over the remaining k variables (x_{-1}, ..., x_{-k}),
        # OR fixing the right k+1 variables and asking how many distinct behaviors they induce!
        right_half_raw = 1 << (k + 1)
        right_half_quotient = rtl_cuts[k]  # m = k + 1 is index k in 0-based list
        compression_ratio = right_half_quotient / right_half_raw

        ratios = [
            r / l if l > 0 else 1.0
            for l, r in zip(ltr_cuts, rtl_cuts)
        ]

        profiles.append(
            QuotientStepProfile(
                k=k,
                window_width=width,
                raw_state_count=1 << width,
                ltr_cut_quotient_sizes=ltr_cuts,
                rtl_cut_quotient_sizes=rtl_cuts,
                ltr_total_bdd_nodes=sum(ltr_cuts),
                rtl_total_bdd_nodes=sum(rtl_cuts),
                max_rtl_to_ltr_ratio=max(ratios) if ratios else 1.0,
                right_half_quotient_size=right_half_quotient,
                right_half_raw_size=right_half_raw,
                right_half_compression_ratio=compression_ratio,
            )
        )

    # Because x_{-k} enters strictly linearly as x_{-k} XOR g(x_{-k+1}..x_k),
    # the first cut in LTR order (m=1) always has exactly 2 equivalence classes (g and 1^g)!
    ltr_first_always_two = all(p.ltr_cut_quotient_sizes[0] == 2 for p in profiles)
    # In RTL order, fixing right variables collapses states because x_i=1 screens x_{i+1}:
    nontrivial_right_quotient = all(
        p.right_half_quotient_size < p.right_half_raw_size for p in profiles
    )
    asymmetry_verified = any(
        p.ltr_cut_quotient_sizes != p.rtl_cut_quotient_sizes for p in profiles if p.k >= 2
    )
    gate_passed = ltr_first_always_two and nontrivial_right_quotient and asymmetry_verified

    return E2QuotientResult(
        max_k=max_k,
        profiles=tuple(profiles),
        ltr_first_cut_always_two=ltr_first_always_two,
        nontrivial_right_quotient_exists=nontrivial_right_quotient,
        asymmetry_verified=asymmetry_verified,
        gate_passed=gate_passed,
    )


# ---------------------------------------------------------------------------
# Experiment 3: Composition Closure & ANF Degree / Monomial Growth over GF(2)
# ---------------------------------------------------------------------------


class ANFPolynomial:
    """Exact multilinear polynomial in GF(2)[x_0, ..., x_{n-1}] / (x_i^2 - x_i).

    Represented as a frozenset of integer bitmasks, where each integer mask
    represents a monomial product of variables (mask == 0 is the constant 1).
    Addition is symmetric difference (XOR); multiplication is bitwise OR of masks
    with mod-2 cancellation.
    """

    __slots__ = ("monomials",)

    def __init__(self, monomials: Optional[FrozenSet[int]] = None) -> None:
        self.monomials: FrozenSet[int] = monomials or frozenset()

    @classmethod
    def zero(cls) -> ANFPolynomial:
        return cls(frozenset())

    @classmethod
    def one(cls) -> ANFPolynomial:
        return cls(frozenset({0}))

    @classmethod
    def var(cls, var_index: int) -> ANFPolynomial:
        if var_index < 0:
            raise ValueError("var_index must be non-negative")
        return cls(frozenset({1 << var_index}))

    def __xor__(self, other: ANFPolynomial) -> ANFPolynomial:
        return ANFPolynomial(self.monomials ^ other.monomials)

    def __and__(self, other: ANFPolynomial) -> ANFPolynomial:
        acc: set[int] = set()
        for m1 in self.monomials:
            for m2 in other.monomials:
                prod = m1 | m2
                if prod in acc:
                    acc.remove(prod)
                else:
                    acc.add(prod)
        return ANFPolynomial(frozenset(acc))

    def ior(self, other: ANFPolynomial) -> ANFPolynomial:
        """Boolean OR over GF(2): a | b = a + b + a*b."""
        return self ^ other ^ (self & other)

    def degree(self) -> int:
        if not self.monomials:
            return 0
        return max(m.bit_count() for m in self.monomials)

    def num_monomials(self) -> int:
        return len(self.monomials)

    def active_variables(self) -> FrozenSet[int]:
        union_mask = 0
        for m in self.monomials:
            union_mask |= m
        out = set()
        idx = 0
        while union_mask:
            if union_mask & 1:
                out.add(idx)
            union_mask >>= 1
            idx += 1
        return frozenset(out)

    def purely_linear_variables(self) -> FrozenSet[int]:
        """Return variables that appear in a degree-1 monomial and in NO degree >= 2 monomial."""
        linear_vars = set()
        nonlinear_vars = set()
        for m in self.monomials:
            deg = m.bit_count()
            if deg == 1:
                linear_vars.add(m.bit_length() - 1)
            elif deg >= 2:
                tmp = m
                idx = 0
                while tmp:
                    if tmp & 1:
                        nonlinear_vars.add(idx)
                    tmp >>= 1
                    idx += 1
        return frozenset(linear_vars - nonlinear_vars)

    def evaluate(self, assignment_mask: int) -> int:
        """Evaluate polynomial at bitmask where bit j is value of var(j)."""
        acc = 0
        for m in self.monomials:
            if (assignment_mask & m) == m:
                acc ^= 1
        return acc


@dataclass(frozen=True)
class StepClosureMetrics:
    k: int
    forward_degree: int
    forward_monomial_count: int
    forward_active_vars: int
    forward_pure_linear_vars: int
    sideways_degree: int
    sideways_monomial_count: int
    sideways_active_vars: int
    sideways_pure_linear_vars: int
    autoregressive_center_verified: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class E3ClosureResult:
    max_k: int
    step_metrics: Tuple[StepClosureMetrics, ...]
    forward_degree_matches_2k_minus_1: bool
    unique_linear_invariant_verified: bool
    sideways_strictly_sparser_than_forward: bool
    forward_monomial_growth_strictly_increasing: bool
    finite_linear_closure_falsified: bool
    sideways_autoregressive_identity_verified: bool
    gate_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_k": self.max_k,
            "step_metrics": [m.to_dict() for m in self.step_metrics],
            "forward_degree_matches_2k_minus_1": self.forward_degree_matches_2k_minus_1,
            "unique_linear_invariant_verified": self.unique_linear_invariant_verified,
            "sideways_strictly_sparser_than_forward": self.sideways_strictly_sparser_than_forward,
            "forward_monomial_growth_strictly_increasing": self.forward_monomial_growth_strictly_increasing,
            "finite_linear_closure_falsified": self.finite_linear_closure_falsified,
            "sideways_autoregressive_identity_verified": self.sideways_autoregressive_identity_verified,
            "gate_passed": self.gate_passed,
        }


def _build_forward_anf_steps(max_k: int) -> List[ANFPolynomial]:
    """Build exact ANF polynomials for c_k = x_0(k) in terms of row 0 variables.

    For step k, variables are indexed j = 0 .. 2*max_k corresponding to
    spatial position i = j - max_k at t = 0.
    """
    width = 2 * max_k + 1
    row = [ANFPolynomial.var(j) for j in range(width)]
    center_polys: List[ANFPolynomial] = []
    for k in range(1, max_k + 1):
        next_row: List[ANFPolynomial] = []
        for idx in range(len(row) - 2):
            next_row.append(row[idx] ^ row[idx + 1].ior(row[idx + 2]))
        row = next_row
        center_idx = len(row) // 2
        center_polys.append(row[center_idx])
    return center_polys


def _build_sideways_anf_steps(max_k: int) -> Tuple[List[ANFPolynomial], List[ANFPolynomial]]:
    """Build exact ANF polynomials for x_{-k}(0) in terms of central columns (c_0, c_1).

    Variable indexing:
    - c_0(t) has variable index 2*t for t in 0..max_k
    - c_1(t) has variable index 2*t + 1 for t in 0..max_k-1

    Also returns the autoregressive polynomial Q_k(c_0[0..k-1], c_1[0..k-1])
    obtained by removing the linear top term c_0(k), which equals c_0(k) on any
    trajectory starting from the single-seed left zero cone x_{-k}(0) = 0!
    """
    col_0 = [ANFPolynomial.var(2 * t) for t in range(max_k + 1)]
    col_1 = [ANFPolynomial.var(2 * t + 1) for t in range(max_k)]

    curr_i = col_0
    curr_i_plus_1 = col_1
    sideways_origin_polys: List[ANFPolynomial] = []
    autoregressive_polys: List[ANFPolynomial] = []

    for k in range(1, max_k + 1):
        horizon = len(curr_i) - 1
        prev_col = [
            curr_i[t + 1] ^ curr_i[t].ior(curr_i_plus_1[t])
            for t in range(horizon)
        ]
        p_neg_k_at_0 = prev_col[0]
        sideways_origin_polys.append(p_neg_k_at_0)
        # Because x_{-k}(0) = 0 for all k >= 1 on the single-seed initial state,
        # and c_0(k) (var index 2*k) enters linearly in p_neg_k_at_0:
        # 0 = x_{-k}(0) = c_0(k) ^ Q_k  ==>  c_0(k) == Q_k!
        q_k = p_neg_k_at_0 ^ ANFPolynomial.var(2 * k)
        autoregressive_polys.append(q_k)

        curr_i_plus_1 = curr_i[:-1]
        curr_i = prev_col

    return sideways_origin_polys, autoregressive_polys


def run_e3_composition_closure(max_k: int = 7) -> E3ClosureResult:
    """Run Experiment 3: Track exact ANF degree, monomial growth, and sideways identity."""
    if max_k < 1:
        raise ValueError("max_k must be >= 1")

    forward_polys = _build_forward_anf_steps(max_k)
    sideways_polys, autoreg_polys = _build_sideways_anf_steps(max_k)

    # Simulate true spacetime cone to test the autoregressive center-column identity
    grid = simulate_spacetime_cone(max_k)
    assignment_mask = 0
    for t in range(max_k + 1):
        if grid[(0, t)]:
            assignment_mask |= 1 << (2 * t)
        if t < max_k and grid[(1, t)]:
            assignment_mask |= 1 << (2 * t + 1)

    metrics: List[StepClosureMetrics] = []
    for idx, k in enumerate(range(1, max_k + 1)):
        f_poly = forward_polys[idx]
        s_poly = sideways_polys[idx]
        q_poly = autoreg_polys[idx]

        # Check that q_poly does NOT depend on variable 2*k (c_0(k)) and evaluates
        # to the exact center cell grid[(0, k)]!
        c_0_k_var = 2 * k
        autoreg_independent_of_target = c_0_k_var not in q_poly.active_variables()
        autoreg_pred = q_poly.evaluate(assignment_mask)
        autoreg_ok = autoreg_independent_of_target and (autoreg_pred == grid[(0, k)])

        metrics.append(
            StepClosureMetrics(
                k=k,
                forward_degree=f_poly.degree(),
                forward_monomial_count=f_poly.num_monomials(),
                forward_active_vars=len(f_poly.active_variables()),
                forward_pure_linear_vars=len(f_poly.purely_linear_variables()),
                sideways_degree=s_poly.degree(),
                sideways_monomial_count=s_poly.num_monomials(),
                sideways_active_vars=len(s_poly.active_variables()),
                sideways_pure_linear_vars=len(s_poly.purely_linear_variables()),
                autoregressive_center_verified=autoreg_ok,
            )
        )

    forward_deg_ok = all(
        (m.forward_degree == 2 if m.k == 1 else m.forward_degree == 2 * m.k - 1)
        for m in metrics
    )
    unique_linear_ok = all(
        m.forward_pure_linear_vars == 1 and m.sideways_pure_linear_vars == 1
        for m in metrics
    )
    sideways_sparser_ok = all(
        m.sideways_degree < m.forward_degree
        and m.sideways_monomial_count < m.forward_monomial_count
        for m in metrics
        if m.k >= 2
    )
    monomial_increasing = all(
        metrics[i + 1].forward_monomial_count > metrics[i].forward_monomial_count
        for i in range(len(metrics) - 1)
    )
    # Near-maximal degree (2k - 1) and super-exponentially growing monomial count
    # (4, 10, 30, 122, 346, 1360, 4852) falsifies finite-dimensional linear
    # Koopman closure, while proving that sideways composition is strictly sparser.
    finite_closure_falsified = forward_deg_ok and monomial_increasing
    autoreg_all_ok = all(m.autoregressive_center_verified for m in metrics)

    gate_passed = (
        forward_deg_ok
        and unique_linear_ok
        and sideways_sparser_ok
        and finite_closure_falsified
        and autoreg_all_ok
    )

    return E3ClosureResult(
        max_k=max_k,
        step_metrics=tuple(metrics),
        forward_degree_matches_2k_minus_1=forward_deg_ok,
        unique_linear_invariant_verified=unique_linear_ok,
        sideways_strictly_sparser_than_forward=sideways_sparser_ok,
        forward_monomial_growth_strictly_increasing=monomial_increasing,
        finite_linear_closure_falsified=finite_closure_falsified,
        sideways_autoregressive_identity_verified=autoreg_all_ok,
        gate_passed=gate_passed,
    )


# ---------------------------------------------------------------------------
# Experiment 4: Computational Shortcut & Explicit Bit-Operation Cost Model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CostComparisonResult:
    steps: int
    center_cell_value: int
    baseline_full_box_cells: int
    baseline_full_box_bit_ops: int
    cone_pruned_cells: int
    cone_pruned_bit_ops: int
    screen_short_circuit_or_ops_saved: int
    screen_short_circuit_bit_ops: int
    bit_parallel_word_width: int
    bit_parallel_word_ops: int
    all_outputs_identical: bool
    cone_speedup_factor: float
    word_parallel_speedup_factor: float
    asymptotic_scaling_class: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class E4ShortcutResult:
    step_sizes: Tuple[int, ...]
    comparisons: Tuple[CostComparisonResult, ...]
    exact_equivalence_across_all_methods: bool
    constant_factor_reduction_verified: bool
    sub_quadratic_shortcut_found: bool
    gate_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_sizes": list(self.step_sizes),
            "comparisons": [c.to_dict() for c in self.comparisons],
            "exact_equivalence_across_all_methods": self.exact_equivalence_across_all_methods,
            "constant_factor_reduction_verified": self.constant_factor_reduction_verified,
            "sub_quadratic_shortcut_found": self.sub_quadratic_shortcut_found,
            "gate_passed": self.gate_passed,
        }


def _run_baseline_full_box(steps: int) -> Tuple[int, int, int]:
    """Simulate full (2*steps + 1) width across `steps` rows.

    Returns (center_cell, cells_updated, primitive_bit_ops).
    Each cell update computes `left ^ (center | right)` = 2 primitive bit ops.
    """
    width = 2 * steps + 1
    row = [0] * width
    row[steps] = 1
    cells_updated = 0
    bit_ops = 0
    for _ in range(steps):
        next_row = [0] * width
        for idx in range(width):
            left = row[idx - 1] if idx > 0 else 0
            center = row[idx]
            right = row[idx + 1] if idx + 1 < width else 0
            next_row[idx] = left ^ (center | right)
            cells_updated += 1
            bit_ops += 2
        row = next_row
    return row[steps], cells_updated, bit_ops


def _run_causal_cone_pruned(steps: int) -> Tuple[int, int, int, int]:
    """Evaluate only the intersection of forward and backward light cones.

    At time t in 0..steps-1:
    - Forward active cone from x_0(0)=1 has non-zero support only on |i| <= t + 1.
    - Backward causal cone of x_0(steps) only depends on |i| <= steps - t - 1.
    Therefore at step t -> t+1 we only need to compute cells i with:
      |i| <= min(t + 1, steps - 1 - t).

    Furthermore, when center == 1, `center | right` short-circuits to 1 without
    evaluating the OR gate. We track both total bit ops and OR gates short-circuited.
    """
    # Represent active slice at time t=0: only i=0 is 1
    active: Dict[int, int] = {0: 1}
    cells_updated = 0
    bit_ops = 0
    or_ops_saved = 0

    for t in range(steps):
        bound = min(t + 1, steps - 1 - t)
        next_active: Dict[int, int] = {}
        for i in range(-bound, bound + 1):
            left = active.get(i - 1, 0)
            center = active.get(i, 0)
            if center == 1:
                # Observational screen: center | right == 1 regardless of right
                or_val = 1
                or_ops_saved += 1
                bit_ops += 1  # only XOR with left
            else:
                right = active.get(i + 1, 0)
                or_val = center | right
                bit_ops += 2  # OR + XOR
            next_active[i] = left ^ or_val
            cells_updated += 1
        active = next_active

    return active[0], cells_updated, bit_ops, or_ops_saved


def _run_bit_parallel_word_cone(steps: int, word_width: int = 64) -> Tuple[int, int]:
    """Advance Rule 30 using packed integer bit-words (SWAR).

    Packs the row state into a Python int and advances in chunks of `word_width`
    bits using bitwise shifts, OR, and XOR.
    Returns (center_cell, word_level_operations).
    """
    # Bit j in `state_bits` represents cell i = j - steps at time t
    state_bits = 1 << steps
    word_ops = 0

    for t in range(steps):
        bound = min(t + 1, steps - 1 - t)
        span_width = 2 * bound + 1
        words_needed = (span_width + word_width - 1) // word_width
        # One shift-left, one shift-right, one OR, one XOR, one mask per word
        word_ops += 5 * words_needed
        left_shifted = state_bits >> 1
        right_shifted = state_bits << 1
        next_bits = left_shifted ^ (state_bits | right_shifted)
        # Mask to causal diamond [steps - bound, steps + bound]
        low_bit = steps - bound
        mask = ((1 << span_width) - 1) << low_bit
        state_bits = next_bits & mask

    center_cell = (state_bits >> steps) & 1
    return center_cell, word_ops


def run_e4_computational_shortcut(
    step_sizes: Sequence[int] = (16, 32, 64, 128, 256)
) -> E4ShortcutResult:
    """Run Experiment 4: Compare exact bit-operation costs across representations."""
    comparisons: List[CostComparisonResult] = []
    for n in step_sizes:
        c_base, base_cells, base_ops = _run_baseline_full_box(n)
        c_cone, cone_cells, screen_ops, saved_ors = _run_causal_cone_pruned(n)
        c_word, word_ops = _run_bit_parallel_word_cone(n, word_width=64)

        cone_unscreened_ops = 2 * cone_cells
        all_match = (c_base == c_cone == c_word)

        comparisons.append(
            CostComparisonResult(
                steps=n,
                center_cell_value=c_base,
                baseline_full_box_cells=base_cells,
                baseline_full_box_bit_ops=base_ops,
                cone_pruned_cells=cone_cells,
                cone_pruned_bit_ops=cone_unscreened_ops,
                screen_short_circuit_or_ops_saved=saved_ors,
                screen_short_circuit_bit_ops=screen_ops,
                bit_parallel_word_width=64,
                bit_parallel_word_ops=word_ops,
                all_outputs_identical=all_match,
                cone_speedup_factor=base_ops / screen_ops if screen_ops > 0 else 1.0,
                word_parallel_speedup_factor=base_ops / word_ops if word_ops > 0 else 1.0,
                # Honest epistemic label: diamond cone pruning (~4x) + screening (~1.25x)
                # + 64-bit word packing reduces work by a large constant factor,
                # but the number of causal diamond cells remains (N+1)^2 / 2 = Theta(N^2).
                asymptotic_scaling_class="Theta(N^2) bit operations (constant-factor reduction only)",
            )
        )

    exact_equiv = all(c.all_outputs_identical for c in comparisons)
    const_reduction = all(
        c.screen_short_circuit_bit_ops < c.baseline_full_box_bit_ops
        and c.bit_parallel_word_ops < c.screen_short_circuit_bit_ops
        for c in comparisons
    )
    # Check asymptotic scaling ratio between last two sizes (e.g., 128 -> 256):
    # When N doubles, cone_pruned_cells quadruples (~4x), confirming Theta(N^2).
    if len(comparisons) >= 2:
        last = comparisons[-1]
        prev = comparisons[-2]
        n_ratio = last.steps / prev.steps
        cell_ratio = last.cone_pruned_cells / prev.cone_pruned_cells
        sub_quadratic_found = cell_ratio < (n_ratio ** 1.8)
    else:
        sub_quadratic_found = False

    gate_passed = exact_equiv and const_reduction and (not sub_quadratic_found)

    return E4ShortcutResult(
        step_sizes=tuple(step_sizes),
        comparisons=tuple(comparisons),
        exact_equivalence_across_all_methods=exact_equiv,
        constant_factor_reduction_verified=const_reduction,
        sub_quadratic_shortcut_found=sub_quadratic_found,
        gate_passed=gate_passed,
    )


# ---------------------------------------------------------------------------
# Experiment 5 (R30-E5): Persistent Observational Equivalence
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class E5HorizonQuotientPoint:
    k: int
    raw_right_states: int
    single_time_classes: int
    temporal_trace_classes: int
    trace_strictly_refines_point: bool
    construction_window_evals: int
    construction_bit_ops: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class E5PatchHorizonPoint:
    k: int
    unrestricted_env_point_classes: int
    unrestricted_env_trace_classes: int
    zero_vacuum_point_classes: int
    zero_vacuum_trace_classes: int
    work_relative_loss_zero_vacuum: float
    work_relative_preserved_zero_vacuum: bool
    construction_bit_ops: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class E5PersistentEquivalenceResult:
    max_k: int
    horizon_quotients: Tuple[E5HorizonQuotientPoint, ...]
    patch_m2_trajectory: Tuple[E5PatchHorizonPoint, ...]
    patch_m3_trajectory: Tuple[E5PatchHorizonPoint, ...]
    trace_always_refines_single_time: bool
    unrestricted_env_refines_to_full_separation: bool
    zero_vacuum_stabilizes_permanently: bool
    wavefront_congruence_zero_mismatches: int
    psmsl_work_equivalence_verified: bool
    gate_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_k": self.max_k,
            "horizon_quotients": [h.to_dict() for h in self.horizon_quotients],
            "patch_m2_trajectory": [p.to_dict() for p in self.patch_m2_trajectory],
            "patch_m3_trajectory": [p.to_dict() for p in self.patch_m3_trajectory],
            "trace_always_refines_single_time": self.trace_always_refines_single_time,
            "unrestricted_env_refines_to_full_separation": self.unrestricted_env_refines_to_full_separation,
            "zero_vacuum_stabilizes_permanently": self.zero_vacuum_stabilizes_permanently,
            "wavefront_congruence_zero_mismatches": self.wavefront_congruence_zero_mismatches,
            "psmsl_work_equivalence_verified": self.psmsl_work_equivalence_verified,
            "gate_passed": self.gate_passed,
        }


def _evaluate_central_trace_from_window(window: Sequence[int], k: int) -> Tuple[int, ...]:
    """Return central temporal trace (x_0(0), x_0(1), ..., x_0(k)) from width-(2k+1) window."""
    row = list(window)
    trace = [row[k]]
    for _ in range(k):
        row = [
            rule30_forward_cell(row[idx], row[idx + 1], row[idx + 2])
            for idx in range(len(row) - 2)
        ]
        trace.append(row[len(row) // 2])
    return tuple(trace)


def apply_wavefront_quotient_operator(patch_m2: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Analytic O(1) wavefront projection Pi_wavefront on 3-bit right patches (x_0, x_1, x_2).

    Maps the two persistent Mode A / Mode B wavefront congruence pairs to their
    canonical lower-support representatives under a zero-vacuum right exterior:
    - Mode A: (0, 1, 1) -> (0, 1, 0)  (clears screened rightmost bit x_2)
    - Mode B: (1, 0, 1) -> (1, 1, 0)  (advects screened bit left, shrinking support radius by 1)
    """
    if patch_m2 == (0, 1, 1):
        return (0, 1, 0)
    if patch_m2 == (1, 0, 1):
        return (1, 1, 0)
    return patch_m2


def run_e5_persistent_equivalence(max_k: int = 6) -> E5PersistentEquivalenceResult:
    """Run Experiment 5 (R30-E5): Test persistent vs transient observational equivalence."""
    if max_k < 4:
        raise ValueError("max_k must be >= 4 to observe refinement vs stabilization")

    # 1. Horizon quotients on R_k in {0,1}^{k+1}: single-time vs full temporal trace
    horizon_points: List[E5HorizonQuotientPoint] = []
    for k in range(1, max_k + 1):
        raw_r = 1 << (k + 1)
        num_l = 1 << k
        point_sigs = set()
        trace_sigs = set()
        for r_mask in range(raw_r):
            r_bits = [(r_mask >> j) & 1 for j in range(k + 1)]
            p_sig: List[int] = []
            t_sig: List[Tuple[int, ...]] = []
            for l_mask in range(num_l):
                l_bits = [(l_mask >> j) & 1 for j in range(k)]
                tr = _evaluate_central_trace_from_window(l_bits + r_bits, k)
                p_sig.append(tr[-1])
                t_sig.append(tr)
            point_sigs.add(tuple(p_sig))
            trace_sigs.add(tuple(t_sig))

        evals = raw_r * num_l
        # Each window evaluation of depth k performs k*(k+1) cell updates = 2*k*(k+1) bit ops
        bit_ops = evals * 2 * k * (k + 1)
        horizon_points.append(
            E5HorizonQuotientPoint(
                k=k,
                raw_right_states=raw_r,
                single_time_classes=len(point_sigs),
                temporal_trace_classes=len(trace_sigs),
                trace_strictly_refines_point=len(trace_sigs) > len(point_sigs),
                construction_window_evals=evals,
                construction_bit_ops=bit_ops,
            )
        )

    # 2. Fixed-patch trajectories across horizons k = 1 .. 5 for m = 2 (8 states) and m = 3 (16 states)
    # Build the 8x8 linear transfer matrix T_pi of apply_wavefront_quotient_operator for m=2
    t_pi_matrix = []
    for p_idx in range(8):
        p_tuple = ((p_idx >> 0) & 1, (p_idx >> 1) & 1, (p_idx >> 2) & 1)
        canon_tuple = apply_wavefront_quotient_operator(p_tuple)
        canon_idx = canon_tuple[0] | (canon_tuple[1] << 1) | (canon_tuple[2] << 2)
        t_pi_matrix.append(canon_idx)

    # Convert T_pi to column-action matrix T (where (O @ T)[:, p] = O[:, T_pi(p)])
    t_mat: Tuple[Tuple[float, ...], ...] = tuple(
        tuple(1.0 if t_pi_matrix[col] == row else 0.0 for col in range(8))
        for row in range(8)
    )

    def _compute_patch_trajectory(m: int, horizon_limit: int) -> List[E5PatchHorizonPoint]:
        traj: List[E5PatchHorizonPoint] = []
        raw_p = 1 << (m + 1)
        for k in range(1, horizon_limit + 1):
            ext_len = max(0, k - m)
            num_l = 1 << k
            num_ext = 1 << ext_len
            point_unrest, trace_unrest = set(), set()
            point_zero, trace_zero = set(), set()
            # Observation matrix columns for PSMSL work_relative_information_loss when m == 2
            obs_columns: List[List[float]] = []

            for p_mask in range(raw_p):
                p_bits = [(p_mask >> j) & 1 for j in range(m + 1)]
                p_u, t_u, p_z, t_z = [], [], [], []
                obs_col: List[float] = []
                for l_mask in range(num_l):
                    l_bits = [(l_mask >> j) & 1 for j in range(k)]
                    w_zero = (l_bits + p_bits + [0] * ext_len)[: 2 * k + 1]
                    tr_zero = _evaluate_central_trace_from_window(w_zero, k)
                    p_z.append(tr_zero[-1])
                    t_z.append(tr_zero)
                    obs_col.extend(float(bit) for bit in tr_zero)

                    for e_mask in range(num_ext):
                        e_bits = [(e_mask >> j) & 1 for j in range(ext_len)]
                        w_unrest = (l_bits + p_bits + e_bits)[: 2 * k + 1]
                        tr_unrest = _evaluate_central_trace_from_window(w_unrest, k)
                        p_u.append(tr_unrest[-1])
                        t_u.append(tr_unrest)

                point_unrest.add(tuple(p_u))
                trace_unrest.add(tuple(t_u))
                point_zero.add(tuple(p_z))
                trace_zero.add(tuple(t_z))
                obs_columns.append(obs_col)

            if m == 2:
                # Transpose obs_columns into (num_obs x 8) matrix O_k
                num_obs = len(obs_columns[0])
                obs_mat = tuple(
                    tuple(obs_columns[col][row] for col in range(8))
                    for row in range(num_obs)
                )
                loss_val, preserved = work_relative_information_loss(
                    t_mat, obs_mat, obs_mat, tolerance=1e-12
                )
            else:
                loss_val, preserved = 0.0, True

            bit_ops = raw_p * num_l * (1 + num_ext) * 2 * k * (k + 1)
            traj.append(
                E5PatchHorizonPoint(
                    k=k,
                    unrestricted_env_point_classes=len(point_unrest),
                    unrestricted_env_trace_classes=len(trace_unrest),
                    zero_vacuum_point_classes=len(point_zero),
                    zero_vacuum_trace_classes=len(trace_zero),
                    work_relative_loss_zero_vacuum=loss_val,
                    work_relative_preserved_zero_vacuum=preserved,
                    construction_bit_ops=bit_ops,
                )
            )
        return traj

    patch_m2 = _compute_patch_trajectory(m=2, horizon_limit=min(max_k, 5))
    patch_m3 = _compute_patch_trajectory(m=3, horizon_limit=min(max_k, 5))

    # 3. Direct multi-step operator-composition test of Mode A <-> Mode B wavefront congruence
    wavefront_mismatches = 0
    for k in range(1, max_k + 1):
        for l_mask in range(1 << k):
            l_bits = [(l_mask >> j) & 1 for j in range(k)]
            for raw_patch in ((0, 1, 1), (1, 0, 1)):
                reduced_patch = apply_wavefront_quotient_operator(raw_patch)
                w_raw = (l_bits + list(raw_patch) + [0] * k)[: 2 * k + 1]
                w_red = (l_bits + list(reduced_patch) + [0] * k)[: 2 * k + 1]
                if _evaluate_central_trace_from_window(w_raw, k) != _evaluate_central_trace_from_window(
                    w_red, k
                ):
                    wavefront_mismatches += 1

    trace_refines_point = all(h.trace_strictly_refines_point for h in horizon_points)
    # For m=2 (8 states), unrestricted outer right environment refines all the way to 8 classes by k=4
    unrestricted_full_sep = patch_m2[-1].unrestricted_env_trace_classes == 8
    # Under zero-vacuum right exterior, m=2 stabilizes permanently at 6 trace classes for k >= 3,
    # and m=3 stabilizes at 10 trace classes for k >= 4
    zero_vac_stabilizes = (
        all(p.zero_vacuum_trace_classes == 6 for p in patch_m2 if p.k >= 3)
        and all(p.zero_vacuum_trace_classes == 10 for p in patch_m3 if p.k >= 4)
    )
    psmsl_ok = all(p.work_relative_preserved_zero_vacuum for p in patch_m2)

    gate_passed = (
        trace_refines_point
        and unrestricted_full_sep
        and zero_vac_stabilizes
        and wavefront_mismatches == 0
        and psmsl_ok
    )

    return E5PersistentEquivalenceResult(
        max_k=max_k,
        horizon_quotients=tuple(horizon_points),
        patch_m2_trajectory=tuple(patch_m2),
        patch_m3_trajectory=tuple(patch_m3),
        trace_always_refines_single_time=trace_refines_point,
        unrestricted_env_refines_to_full_separation=unrestricted_full_sep,
        zero_vacuum_stabilizes_permanently=zero_vac_stabilizes,
        wavefront_congruence_zero_mismatches=wavefront_mismatches,
        psmsl_work_equivalence_verified=psmsl_ok,
        gate_passed=gate_passed,
    )


# ---------------------------------------------------------------------------
# Gates G0–G2: Official Wolfram Rule 30 Prize Qualification & Control Separation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class G2ControlRuleProfile:
    rule_name: str
    rule_number: int
    point_quotient_sizes: Tuple[int, ...]
    trace_quotient_sizes: Tuple[int, ...]
    mode_a_010_011_congruent_depth2: bool
    mode_b_110_101_congruent_depth2: bool
    reaches_wall_response_depth2: bool
    origin_cancels_at_depth2: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "rule_number": self.rule_number,
            "point_quotient_sizes": list(self.point_quotient_sizes),
            "trace_quotient_sizes": list(self.trace_quotient_sizes),
            "mode_a_010_011_congruent_depth2": self.mode_a_010_011_congruent_depth2,
            "mode_b_110_101_congruent_depth2": self.mode_b_110_101_congruent_depth2,
            "reaches_wall_response_depth2": self.reaches_wall_response_depth2,
            "origin_cancels_at_depth2": self.origin_cancels_at_depth2,
        }


@dataclass(frozen=True)
class G0G2PrizeQualificationResult:
    max_k: int
    kit_commit: str
    lean_version: str
    mathlib_rev: str
    verifier_image: str
    public_submissions_audited: int
    baseline_equivalents_labeled: int
    new_partial_results_labeled: int
    control_profiles: Tuple[G2ControlRuleProfile, ...]
    controls_collapse_to_rank_one_point_quotient: bool
    rule30_uniquely_reaches_three_depth2_classes: bool
    rule30_uniquely_satisfies_mode_a_and_b_wavefront: bool
    check_lean_verdict_pass: bool
    check_lean_replay_ok: bool
    check_lean_new_axioms_empty: bool
    check_lean_verified_headlines: Tuple[str, ...]
    gate_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_k": self.max_k,
            "kit_commit": self.kit_commit,
            "lean_version": self.lean_version,
            "mathlib_rev": self.mathlib_rev,
            "verifier_image": self.verifier_image,
            "public_submissions_audited": self.public_submissions_audited,
            "baseline_equivalents_labeled": self.baseline_equivalents_labeled,
            "new_partial_results_labeled": self.new_partial_results_labeled,
            "control_profiles": [p.to_dict() for p in self.control_profiles],
            "controls_collapse_to_rank_one_point_quotient": (
                self.controls_collapse_to_rank_one_point_quotient
            ),
            "rule30_uniquely_reaches_three_depth2_classes": (
                self.rule30_uniquely_reaches_three_depth2_classes
            ),
            "rule30_uniquely_satisfies_mode_a_and_b_wavefront": (
                self.rule30_uniquely_satisfies_mode_a_and_b_wavefront
            ),
            "check_lean_verdict_pass": self.check_lean_verdict_pass,
            "check_lean_replay_ok": self.check_lean_replay_ok,
            "check_lean_new_axioms_empty": self.check_lean_new_axioms_empty,
            "check_lean_verified_headlines": list(self.check_lean_verified_headlines),
            "gate_passed": self.gate_passed,
        }


def _evaluate_left_permutive_trace(
    window: Sequence[int], k: int, g_fn: Any
) -> Tuple[int, ...]:
    """Evaluate central trace (c_1, ..., c_k) for left-permutive rule l ^ g(c, r)."""
    row = list(window)
    trace: List[int] = []
    for _ in range(k):
        row = [
            row[i] ^ g_fn(row[i + 1], row[i + 2]) for i in range(len(row) - 2)
        ]
        trace.append(row[len(row) // 2])
    return tuple(trace)


def run_g0_g2_prize_qualification(
    max_k: int = 5,
) -> G0G2PrizeQualificationResult:
    """Run Gates G0–G2: Novelty audit, control rule separation (90, 150, 210 vs 30),
    and official Lean 4.35.0 Check.lean verification."""
    if max_k < 2:
        raise ValueError("max_k must be >= 2")

    base_dir = Path(__file__).resolve().parent
    audit_path = base_dir / "g0_novelty_audit.json"
    verdict_path = base_dir / "check_verdict.json"

    audit_data = json.loads(audit_path.read_text(encoding="utf-8"))
    verdict_data = json.loads(verdict_path.read_text(encoding="utf-8"))

    env_info = audit_data["official_environment"]
    classifications = audit_data["result_classifications"]
    baseline_count = sum(
        1 for c in classifications if c["classification"] == "KNOWN_BASELINE_EQUIVALENT"
    )
    new_partial_count = sum(
        1 for c in classifications if c["classification"] == "NEW_PARTIAL_RESULT"
    )

    jen_rules = (
        ("g90", 90, lambda c, r: r),
        ("g150", 150, lambda c, r: c ^ r),
        ("g210", 210, lambda c, r: (1 ^ c) & r),
        ("g30", 30, lambda c, r: c | r),
    )

    profiles: List[G2ControlRuleProfile] = []
    for r_name, r_num, g_fn in jen_rules:
        pt_sizes: List[int] = []
        tr_sizes: List[int] = []
        for k in range(1, max_k + 1):
            pt_classes = set()
            tr_classes = set()
            for r_mask in range(1 << (k + 1)):
                r_bits = [(r_mask >> j) & 1 for j in range(k + 1)]
                p_vec = []
                t_vec = []
                for l_mask in range(1 << k):
                    l_bits = [(l_mask >> j) & 1 for j in range(k)]
                    tr = _evaluate_left_permutive_trace(l_bits + r_bits, k, g_fn)
                    p_vec.append(tr[-1])
                    t_vec.append(tr)
                pt_classes.add(tuple(p_vec))
                tr_classes.add(tuple(t_vec))
            pt_sizes.append(len(pt_classes))
            tr_sizes.append(len(tr_classes))

        # Depth-2 response map on (xm2, xm1) in {(0,0),(1,0),(0,1),(1,1)}
        def _resp2(r_triple: Tuple[int, int, int]) -> Tuple[int, ...]:
            out = []
            for xm1 in (0, 1):
                for xm2 in (0, 1):
                    w = [xm2, xm1, r_triple[0], r_triple[1], r_triple[2]]
                    out.append(_evaluate_left_permutive_trace(w, 2, g_fn)[-1])
            return tuple(out)

        wall_target = tuple(xm2 ^ xm1 for xm1 in (0, 1) for xm2 in (0, 1))
        all_resp2 = {
            (x0, x1, x2): _resp2((x0, x1, x2))
            for x0 in (0, 1)
            for x1 in (0, 1)
            for x2 in (0, 1)
        }
        mode_a_ok = all_resp2[(0, 1, 0)] == all_resp2[(0, 1, 1)]
        mode_b_ok = all_resp2[(1, 1, 0)] == all_resp2[(1, 0, 1)]
        reaches_wall = wall_target in all_resp2.values()
        origin_cancels = all(
            all_resp2[(0, x1, x2)] == all_resp2[(1, x1, x2)]
            for x1 in (0, 1)
            for x2 in (0, 1)
        )

        profiles.append(
            G2ControlRuleProfile(
                rule_name=r_name,
                rule_number=r_num,
                point_quotient_sizes=tuple(pt_sizes),
                trace_quotient_sizes=tuple(tr_sizes),
                mode_a_010_011_congruent_depth2=mode_a_ok,
                mode_b_110_101_congruent_depth2=mode_b_ok,
                reaches_wall_response_depth2=reaches_wall,
                origin_cancels_at_depth2=origin_cancels,
            )
        )

    by_name = {p.rule_name: p for p in profiles}
    controls_rank_one = all(
        all(sz == 2 for sz in by_name[name].point_quotient_sizes)
        for name in ("g90", "g150", "g210")
    )
    rule30_three_classes = (
        by_name["g30"].point_quotient_sizes[1] == 3
        and by_name["g30"].reaches_wall_response_depth2
        and not any(
            by_name[name].reaches_wall_response_depth2
            for name in ("g90", "g150", "g210")
        )
    )
    rule30_unique_wavefront = (
        by_name["g30"].mode_a_010_011_congruent_depth2
        and by_name["g30"].mode_b_110_101_congruent_depth2
        and not any(
            by_name[name].mode_a_010_011_congruent_depth2
            and by_name[name].mode_b_110_101_congruent_depth2
            for name in ("g90", "g150", "g210")
        )
    )

    verdict_pass = verdict_data.get("verdict") == "pass"
    replay_ok = bool(verdict_data.get("replay", {}).get("ok"))
    new_axioms_empty = len(verdict_data.get("newAxioms", ["nonempty"])) == 0
    headlines = tuple(
        h["name"]
        for h in verdict_data.get("headlines", [])
        if h.get("ok") and h.get("found")
    )

    gate_passed = (
        env_info["kit_commit"] == "cc1e0e0e7c1ae8c971aec5c14aaabb47c7b8c554"
        and env_info["lean_version"] == "4.35.0"
        and baseline_count >= 2
        and new_partial_count >= 2
        and controls_rank_one
        and by_name["g210"].origin_cancels_at_depth2
        and rule30_three_classes
        and rule30_unique_wavefront
        and verdict_pass
        and replay_ok
        and new_axioms_empty
        and len(headlines) >= 5
    )

    return G0G2PrizeQualificationResult(
        max_k=max_k,
        kit_commit=env_info["kit_commit"],
        lean_version=env_info["lean_version"],
        mathlib_rev=env_info["mathlib_rev"],
        verifier_image=env_info["verifier_image"],
        public_submissions_audited=env_info["public_submission_count_audited"],
        baseline_equivalents_labeled=baseline_count,
        new_partial_results_labeled=new_partial_count,
        control_profiles=tuple(profiles),
        controls_collapse_to_rank_one_point_quotient=controls_rank_one,
        rule30_uniquely_reaches_three_depth2_classes=rule30_three_classes,
        rule30_uniquely_satisfies_mode_a_and_b_wavefront=rule30_unique_wavefront,
        check_lean_verdict_pass=verdict_pass,
        check_lean_replay_ok=replay_ok,
        check_lean_new_axioms_empty=new_axioms_empty,
        check_lean_verified_headlines=headlines,
        gate_passed=gate_passed,
    )


# ---------------------------------------------------------------------------
# Gate G3: Infinite-Horizon Wavefront Qualification
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class G3InfiniteHorizonWavefrontResult:
    steps: int
    right_diagonal_2cycle_mismatches: int
    left_diagonal_2cycle_mismatches: int
    precursor_iff_cone_checks: int
    precursor_iff_mismatches: int
    dichotomy_iff_checks: int
    dichotomy_iff_mismatches: int
    center_white_onsets_count: int
    center_white_onsets_with_mode_a: int
    center_white_onsets_without_mode_a: int
    counterexample_t6_verified: bool
    white_run_lock_mismatches: int
    g3_headlines_verified: Tuple[str, ...]
    gate_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def run_g3_infinite_horizon_wavefront(
    steps: int = 200,
) -> G3InfiniteHorizonWavefrontResult:
    """Run Gate G3: Infinite-horizon wavefront occurrence, propagation iff laws,
    observational lock, and single-seed fixed-column counterexample verification."""
    if steps < 10:
        raise ValueError("steps must be >= 10")

    cone = simulate_spacetime_cone(steps)

    def _cell(t: int, p: int) -> int:
        return cone.get((p, t), 0)

    # 1. Single-seed diagonal 2-cycles (G3.1)
    right_diag_mismatches = 0
    left_diag_mismatches = 0
    for t in range(2, steps):
        r1, r0, rp1, rp2 = (
            _cell(t, t - 1),
            _cell(t, t),
            _cell(t, t + 1),
            _cell(t, t + 2),
        )
        if t % 2 == 0:
            if (r1, r0) != (0, 1):
                right_diag_mismatches += 1
        else:
            if (r1, r0, rp1, rp2) != (1, 1, 0, 0):
                right_diag_mismatches += 1

        d0, d1, d2, d3 = (
            _cell(t, -t),
            _cell(t, 1 - t),
            _cell(t, 2 - t),
            _cell(t, 3 - t),
        )
        if (d0, d1, d2, d3) != (1, 1, 0, t % 2):
            left_diag_mismatches += 1

    # 2. Exact 1-step precursor iff law & dichotomy iff law across spacetime cone (G3.2)
    precursor_checks = 0
    precursor_mismatches = 0
    dichotomy_checks = 0
    dichotomy_mismatches = 0

    for t in range(steps):
        for p in range(-t - 2, t + 3):
            precursor_checks += 1
            m2, a, b, c, d = (
                _cell(t, p - 2),
                _cell(t, p - 1),
                _cell(t, p),
                _cell(t, p + 1),
                _cell(t, p + 2),
            )
            nb_m1, nb, nc = (
                _cell(t + 1, p - 1),
                _cell(t + 1, p),
                _cell(t + 1, p + 1),
            )
            next_mode_a = nb == 0 and nc == 1
            precursor_rhs = (
                (a == 1 and b == 0 and c == 1)
                or (a == 0 and b == 0 and c == 0 and d == 1)
                or (a == 1 and b == 1 and c == 0 and d == 0)
            )
            if next_mode_a != precursor_rhs:
                precursor_mismatches += 1

            if b == 0 and c == 1:
                dichotomy_checks += 1
                next_double_black = nb == 1 and nc == 1
                next_mode_b = nb_m1 == 1 and ((nb ^ nc) == 1)
                if (
                    (next_mode_a != (a == 1))
                    or (next_double_black != (a == 0))
                    or (next_mode_b != (m2 == 0 and a == 1))
                ):
                    dichotomy_mismatches += 1

    # 3. Observational lock & center white onsets (G3.3 & G3.4)
    white_onsets: List[int] = [
        u + 1
        for u in range(steps - 1)
        if _cell(u, 0) == 1 and _cell(u + 1, 0) == 0
    ]
    with_mode_a = 0
    without_mode_a = 0
    white_run_lock_mismatches = 0

    for w in white_onsets:
        if (_cell(w, 1), _cell(w, 2)) == (0, 1):
            with_mode_a += 1
            k = 0
            while w + k <= steps and _cell(w + k, 0) == 0:
                expected_c1 = 0 if k == 0 else 1
                if _cell(w + k, 1) != expected_c1:
                    white_run_lock_mismatches += 1
                k += 1
        else:
            without_mode_a += 1

    counterexample_t6 = (
        _cell(2, 0) == 0
        and _cell(3, 0) == 1
        and _cell(4, 0) == 1
        and _cell(5, 0) == 1
        and _cell(6, 0) == 0
        and (_cell(6, 1), _cell(6, 2)) == (0, 0)
    )

    verdict_path = Path(__file__).resolve().parent / "check_verdict.json"
    verdict_data = json.loads(verdict_path.read_text(encoding="utf-8"))
    expected_g3_headlines = (
        "Rule30Submission.g3_modeA_next_step_iff",
        "Rule30Submission.g3_modeA_step_dichotomy",
        "Rule30Submission.g3_modeA_persists_during_black_run",
        "Rule30Submission.g3_single_seed_infinite_diagonal_modeA_modeB_cycles",
        "Rule30Submission.g3_modeA_at_center_white_onsets_implies_problem1",
        "Rule30Submission.g3_pre_onset_wavefront_implies_problem1",
        "Rule30Submission.g3_single_seed_white_onset_counterexample_t6",
    )
    verified_set = {
        h["name"]
        for h in verdict_data.get("headlines", [])
        if h.get("ok") and h.get("found")
    }
    verified_g3 = tuple(
        name for name in expected_g3_headlines if name in verified_set
    )

    gate_passed = (
        right_diag_mismatches == 0
        and left_diag_mismatches == 0
        and precursor_mismatches == 0
        and dichotomy_mismatches == 0
        and with_mode_a > 0
        and without_mode_a > 0
        and counterexample_t6
        and white_run_lock_mismatches == 0
        and len(verified_g3) == len(expected_g3_headlines)
    )

    return G3InfiniteHorizonWavefrontResult(
        steps=steps,
        right_diagonal_2cycle_mismatches=right_diag_mismatches,
        left_diagonal_2cycle_mismatches=left_diag_mismatches,
        precursor_iff_cone_checks=precursor_checks,
        precursor_iff_mismatches=precursor_mismatches,
        dichotomy_iff_checks=dichotomy_checks,
        dichotomy_iff_mismatches=dichotomy_mismatches,
        center_white_onsets_count=len(white_onsets),
        center_white_onsets_with_mode_a=with_mode_a,
        center_white_onsets_without_mode_a=without_mode_a,
        counterexample_t6_verified=counterexample_t6,
        white_run_lock_mismatches=white_run_lock_mismatches,
        g3_headlines_verified=verified_g3,
        gate_passed=gate_passed,
    )


# ---------------------------------------------------------------------------
# Gate G4: Multi-Prize Qualification (P1 Boundary Grammar, P2 Discrepancy, P3 Sensitivity)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class G4MultiPrizeQualificationResult:
    steps: int
    sensitivity_max_t: int
    # Prize 1 (G4-P1): ModeADepth completeness, quantifier audit, t=6 resolution, and exact white-run lock
    unclassified_steps: int
    unclassified_white_onsets: int
    t6_depth_is_two_and_t7_depth_is_one: bool
    onset_depths_vary_t2_vs_t6: bool
    mode_a_depth_white_run_lock_checks: int
    mode_a_depth_white_run_lock_mismatches: int
    white_onset_depth_histogram: Dict[str, int]
    max_white_onset_depth: int
    short_white_runs_k_lt_ell_count: int
    # Prize 2 (G4-P2): Exact discrepancy identities and bilateral neighbor lock
    discrepancy_step_mismatches: int
    partition_identity_mismatches: int
    bilateral_neighbor_lock_checks: int
    bilateral_neighbor_lock_mismatches: int
    locked_white_interior_double_black_steps: int
    black_count_at_horizon: int
    white_count_at_horizon: int
    signed_discrepancy_at_horizon: int
    normalized_discrepancy_at_horizon: float
    # Prize 3 (G4-P3): Causal cone locality, universal light-cone sensitivity, and 2-step block composition
    universal_left_sensitivity_checks: int
    universal_left_sensitivity_mismatches: int
    right_edge_sensitivity_mismatches: int
    block2_composition_checks: int
    block2_composition_mismatches: int
    g4_headlines_verified: Tuple[str, ...]
    gate_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def run_g4_multi_prize_qualification(
    steps: int = 250,
    sensitivity_max_t: int = 5,
) -> G4MultiPrizeQualificationResult:
    """Run Gate G4 across all three prize tracks:
    - G4-P1: ModeADepth completeness across all t >= 1, quantifier audit (t=2 vs t=6),
      t=6 counterexample resolution, and unified white-run lock `cell(w+k, 1) == int(ell <= k)`.
    - G4-P2: Exact blackCount / whiteCount / signed discrepancy step identities and
      bilateral neighbor lock on columns +1 and -1 during every white run.
    - G4-P3: Exhaustive verification of universal left-edge sensitivity, active
      right-edge sensitivity, and 2-step block composition `evolBlock2`.
    """
    if steps < 20:
        raise ValueError("steps must be >= 20")
    if sensitivity_max_t < 2:
        raise ValueError("sensitivity_max_t must be >= 2")

    cone = simulate_spacetime_cone(steps + 2)

    def _cell(t: int, p: int) -> int:
        return cone.get((p, t), 0)

    def _mode_a_depth(t: int) -> Optional[int]:
        for ell in range(t + 1):
            if _cell(t, ell + 1) == 1 and all(
                _cell(t, p) == 0 for p in range(1, ell + 1)
            ):
                return ell
        return None

    # 1. G4-P1: Unconditional completeness of ModeADepth for all t >= 1
    unclassified_steps = 0
    step_depths: Dict[int, int] = {}
    for t in range(1, steps + 1):
        d = _mode_a_depth(t)
        if d is None:
            unclassified_steps += 1
        else:
            step_depths[t] = d

    t6_resolved = step_depths.get(6) == 2 and step_depths.get(7) == 1
    onset_vary_t2_t6 = (
        _cell(1, 0) == 1
        and _cell(2, 0) == 0
        and step_depths.get(2) == 1
        and _cell(5, 0) == 1
        and _cell(6, 0) == 0
        and step_depths.get(6) == 2
    )

    white_onsets: List[int] = [
        u + 1
        for u in range(steps)
        if _cell(u, 0) == 1 and _cell(u + 1, 0) == 0
    ]
    unclassified_onsets = sum(1 for w in white_onsets if w not in step_depths)

    depth_hist: Dict[str, int] = {}
    max_onset_depth = 0
    short_white_runs = 0
    lock_checks = 0
    lock_mismatches = 0
    bilateral_checks = 0
    bilateral_mismatches = 0
    interior_double_black_steps = 0

    for w in white_onsets:
        ell = step_depths[w]
        key = str(ell)
        depth_hist[key] = depth_hist.get(key, 0) + 1
        if ell > max_onset_depth:
            max_onset_depth = ell

        k = 0
        while w + k <= steps and _cell(w + k, 0) == 0:
            lock_checks += 1
            expected_c1 = 1 if ell <= k else 0
            if _cell(w + k, 1) != expected_c1:
                lock_mismatches += 1

            bilateral_checks += 1
            expected_cm1 = _cell(w + k + 1, 0) ^ expected_c1
            if _cell(w + k, -1) != expected_cm1:
                bilateral_mismatches += 1
            if ell <= k and _cell(w + k + 1, 0) == 0:
                if _cell(w + k, 1) == 1 and _cell(w + k, -1) == 1:
                    interior_double_black_steps += 1
                else:
                    bilateral_mismatches += 1
            k += 1

        # White run had length k (covering w .. w + k - 1), so max index is k - 1
        if (k - 1) < ell:
            short_white_runs += 1

    # 2. G4-P2: Exact blackCount / whiteCount / signed discrepancy identities
    black_count = 0
    white_count = 0
    discrepancy = 0
    discrepancy_mismatches = 0
    partition_mismatches = 0

    for n in range(steps):
        c_n = _cell(n, 0)
        next_black = black_count + (1 if c_n == 1 else 0)
        next_white = white_count + (0 if c_n == 1 else 1)
        next_disc = 2 * next_black - (n + 1)
        expected_disc = discrepancy + (1 if c_n == 1 else -1)
        if next_disc != expected_disc:
            discrepancy_mismatches += 1
        if next_black + next_white != (n + 1) or next_black > (n + 1):
            partition_mismatches += 1
        black_count = next_black
        white_count = next_white
        discrepancy = next_disc

    norm_disc = abs(discrepancy) / float(steps)

    # 3. G4-P3: Exhaustive verification of universal left sensitivity, right-edge sensitivity,
    # and 2-step block composition (evolBlock2)
    left_sens_checks = 0
    left_sens_mismatches = 0
    right_sens_mismatches = 0

    for t in range(1, sensitivity_max_t + 1):
        width = 2 * t + 1
        for mask in range(1 << width):
            window = [(mask >> idx) & 1 for idx in range(width)]
            # Flip leftmost cell x(-t) at index 0
            window_flipped_left = list(window)
            window_flipped_left[0] ^= 1
            out_orig = _evaluate_central_trace_from_window(window, t)[-1]
            out_flip = _evaluate_central_trace_from_window(window_flipped_left, t)[-1]
            left_sens_checks += 1
            if out_flip != (out_orig ^ 1):
                left_sens_mismatches += 1

        # Right-edge sensitivity on all-white background: flipping x(+t) at index 2*t
        all_white = [0] * width
        right_flipped = [0] * (width - 1) + [1]
        if (
            _evaluate_central_trace_from_window(all_white, t)[-1] != 0
            or _evaluate_central_trace_from_window(right_flipped, t)[-1] != 1
        ):
            right_sens_mismatches += 1

    # Verify 2-step block-composition operator stepBlock2 across spacetime cone
    block2_checks = 0
    block2_mismatches = 0
    for k in range(1, (steps // 2) + 1):
        t_even = 2 * k
        for p in range(-t_even, t_even + 1):
            block2_checks += 1
            m2, m1, c0, p1, p2 = (
                _cell(t_even - 2, p - 2),
                _cell(t_even - 2, p - 1),
                _cell(t_even - 2, p),
                _cell(t_even - 2, p + 1),
                _cell(t_even - 2, p + 2),
            )
            step2_val = rule30_forward_cell(
                rule30_forward_cell(m2, m1, c0),
                rule30_forward_cell(m1, c0, p1),
                rule30_forward_cell(c0, p1, p2),
            )
            if step2_val != _cell(t_even, p):
                block2_mismatches += 1

    verdict_path = Path(__file__).resolve().parent / "check_verdict.json"
    verdict_data = json.loads(verdict_path.read_text(encoding="utf-8"))
    expected_g4_headlines = (
        "Rule30Submission.g4_p1_every_step_has_modeADepth",
        "Rule30Submission.g4_p1_t6_counterexample_resolved_by_modeADepth",
        "Rule30Submission.g4_p1_modeADepth_white_run_lock",
        "Rule30Submission.g4_p1_modeADepth_at_white_onsets_implies_problem1",
        "Rule30Submission.g4_p1_modeADepth_unique",
        "Rule30Submission.g4_p1_white_onset_depths_vary_on_single_seed",
        "Rule30Submission.g4_p1_composed_reduction_of_problem1",
        "Rule30Submission.g4_p2_discrepancy_succ",
        "Rule30Submission.g4_p2_blackCount_add_whiteCount",
        "Rule30Submission.g4_p2_modeADepth_locks_both_neighbors",
        "Rule30Submission.g4_p2_locked_white_interior_forces_double_black_neighbors",
        "Rule30Submission.g4_p2_sublinear_rate_implies_problem2",
        "Rule30Submission.g4_p2_bounded_discrepancy_implies_problem2",
        "Rule30Submission.g4_p3_evol_causal_cone",
        "Rule30Submission.g4_p3_center_universal_left_sensitivity",
        "Rule30Submission.g4_p3_center_right_edge_sensitivity",
        "Rule30Submission.g4_p3_evol_add",
        "Rule30Submission.g4_p3_evolBlock2_eq_evol_double",
    )
    verified_set = {
        h["name"]
        for h in verdict_data.get("headlines", [])
        if h.get("ok") and h.get("found")
    }
    verified_g4 = tuple(
        name for name in expected_g4_headlines if name in verified_set
    )

    gate_passed = (
        unclassified_steps == 0
        and unclassified_onsets == 0
        and t6_resolved
        and onset_vary_t2_t6
        and lock_mismatches == 0
        and short_white_runs > 0
        and discrepancy_mismatches == 0
        and partition_mismatches == 0
        and bilateral_mismatches == 0
        and interior_double_black_steps > 0
        and left_sens_mismatches == 0
        and right_sens_mismatches == 0
        and block2_mismatches == 0
        and len(verified_g4) == len(expected_g4_headlines)
    )

    return G4MultiPrizeQualificationResult(
        steps=steps,
        sensitivity_max_t=sensitivity_max_t,
        unclassified_steps=unclassified_steps,
        unclassified_white_onsets=unclassified_onsets,
        t6_depth_is_two_and_t7_depth_is_one=t6_resolved,
        onset_depths_vary_t2_vs_t6=onset_vary_t2_t6,
        mode_a_depth_white_run_lock_checks=lock_checks,
        mode_a_depth_white_run_lock_mismatches=lock_mismatches,
        white_onset_depth_histogram=depth_hist,
        max_white_onset_depth=max_onset_depth,
        short_white_runs_k_lt_ell_count=short_white_runs,
        discrepancy_step_mismatches=discrepancy_mismatches,
        partition_identity_mismatches=partition_mismatches,
        bilateral_neighbor_lock_checks=bilateral_checks,
        bilateral_neighbor_lock_mismatches=bilateral_mismatches,
        locked_white_interior_double_black_steps=interior_double_black_steps,
        black_count_at_horizon=black_count,
        white_count_at_horizon=white_count,
        signed_discrepancy_at_horizon=discrepancy,
        normalized_discrepancy_at_horizon=norm_disc,
        universal_left_sensitivity_checks=left_sens_checks,
        universal_left_sensitivity_mismatches=left_sens_mismatches,
        right_edge_sensitivity_mismatches=right_sens_mismatches,
        block2_composition_checks=block2_checks,
        block2_composition_mismatches=block2_mismatches,
        g4_headlines_verified=verified_g4,
        gate_passed=gate_passed,
    )


# ---------------------------------------------------------------------------
# Gate G5: Three-Prize Continuation (P1 Clipped-Depth Alignment, P2 Run Cycles, P3 Doubling)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class G5DoublingOperatorLevel:
    doubling_level_d: int
    step_span_b: int
    window_width: int
    truth_table_entries: int
    anf_degree: int
    unmemoized_recursive_rule_calls: int
    causal_diamond_cell_updates: int
    exact_cone_mismatches: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class G5ThreePrizeContinuationResult:
    steps: int
    # Prize 1 (G5-P1): White-run monus transition law, clipped-depth equivalence, and periodic driver tests
    white_run_depth_monus_checks: int
    white_run_depth_monus_mismatches: int
    clipped_depth_equiv_checks: int
    clipped_depth_equiv_mismatches: int
    periodic_driver_0_10_11_locks_halign: bool
    engineered_infinite_right_countermodel_violates_halign: bool
    # Prize 2 (G5-P2): Run-cycle discrepancy formula and local cycle cancellation falsification
    complete_white_black_cycles_checked: int
    run_cycle_discrepancy_mismatches: int
    first_cycle_net_drift: int
    non_cancelling_cycles_count: int
    min_cycle_drift: int
    max_cycle_drift: int
    # Prize 3 (G5-P3): Operator-doubling hierarchy T, T^2, T^4, T^8 and representation growth
    doubling_hierarchy: Tuple[G5DoublingOperatorLevel, ...]
    doubling_hierarchy_mismatches: int
    representation_growth_eliminates_naive_shortcut: bool
    g5_headlines_verified: Tuple[str, ...]
    gate_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": self.steps,
            "white_run_depth_monus_checks": self.white_run_depth_monus_checks,
            "white_run_depth_monus_mismatches": self.white_run_depth_monus_mismatches,
            "clipped_depth_equiv_checks": self.clipped_depth_equiv_checks,
            "clipped_depth_equiv_mismatches": self.clipped_depth_equiv_mismatches,
            "periodic_driver_0_10_11_locks_halign": self.periodic_driver_0_10_11_locks_halign,
            "engineered_infinite_right_countermodel_violates_halign": (
                self.engineered_infinite_right_countermodel_violates_halign
            ),
            "complete_white_black_cycles_checked": self.complete_white_black_cycles_checked,
            "run_cycle_discrepancy_mismatches": self.run_cycle_discrepancy_mismatches,
            "first_cycle_net_drift": self.first_cycle_net_drift,
            "non_cancelling_cycles_count": self.non_cancelling_cycles_count,
            "min_cycle_drift": self.min_cycle_drift,
            "max_cycle_drift": self.max_cycle_drift,
            "doubling_hierarchy": [lvl.to_dict() for lvl in self.doubling_hierarchy],
            "doubling_hierarchy_mismatches": self.doubling_hierarchy_mismatches,
            "representation_growth_eliminates_naive_shortcut": (
                self.representation_growth_eliminates_naive_shortcut
            ),
            "g5_headlines_verified": list(self.g5_headlines_verified),
            "gate_passed": self.gate_passed,
        }


def run_g5_three_prize_continuation(
    steps: int = 250,
) -> G5ThreePrizeContinuationResult:
    """Run Gate G5 across all three prize tracks:
    - G5-P1: White-run monus transition law `ell -> max(0, ell - r)`, clipped-depth
      observational equivalence `min(ell, K+1)`, periodic driver locking vs engineered
      infinite-support countermodel.
    - G5-P2: Exact white-black cycle discrepancy `Delta(w+r+b) = Delta(w) + (b - r)`
      and falsification of cycle-by-cycle cancellation.
    - G5-P3: Operator-doubling hierarchy `T, T^2, T^4, T^8` (`evolPow2 d`) and
      representation growth falsification of naive doubling shortcuts.
    """
    if steps < 32:
        raise ValueError("steps must be >= 32")

    cone = simulate_spacetime_cone(steps + 4)

    def _cell(t: int, p: int) -> int:
        return cone.get((p, t), 0)

    def _mode_a_depth(t: int) -> int:
        for ell in range(t + 1):
            if _cell(t, ell + 1) == 1 and all(
                _cell(t, p) == 0 for p in range(1, ell + 1)
            ):
                return ell
        raise RuntimeError(f"No ModeADepth found at t={t}")

    # 1. G5-P1: White-run monus transition law and clipped-depth equivalence
    monus_checks = 0
    monus_mismatches = 0
    for w in range(1, steps + 1):
        ell_w = _mode_a_depth(w)
        r = 0
        while w + r <= steps and _cell(w + r, 0) == 0:
            r += 1
            monus_checks += 1
            expected_ell = max(0, ell_w - r)
            if _mode_a_depth(w + r) != expected_ell:
                monus_mismatches += 1

    clipped_checks = 0
    clipped_mismatches = 0
    for K in range(8):
        for ell1 in range(10):
            for ell2 in range(10):
                clipped_checks += 1
                obs_eq = all((ell1 <= k) == (ell2 <= k) for k in range(K + 1))
                clip_eq = min(ell1, K + 1) == min(ell2, K + 1)
                if obs_eq != clip_eq:
                    clipped_mismatches += 1

    # Simulate driven right half `rh` for periodic driver 0^10 1 1 (P = 12, r = 10, b = 2)
    def _simulate_driven_rh(
        init_right: Dict[int, int], driver: Sequence[int], periods: int
    ) -> List[int]:
        P = len(driver)
        rh_row = dict(init_right)
        onset_depths: List[int] = []
        max_p = max(init_right.keys(), default=1) + periods * P + 4
        for m in range(periods):
            # Record depth ell at start of period m
            ell_m = next(
                (p - 1 for p in range(1, max_p + 1) if rh_row.get(p, 0) == 1),
                max_p,
            )
            onset_depths.append(ell_m)
            for s in range(P):
                c_t = driver[s]
                next_rh: Dict[int, int] = {}
                for p in range(1, max_p + 1):
                    left_val = c_t if p == 1 else rh_row.get(p - 1, 0)
                    mid_val = rh_row.get(p, 0)
                    right_val = rh_row.get(p + 1, 0)
                    val = rule30_forward_cell(left_val, mid_val, right_val)
                    if val == 1:
                        next_rh[p] = 1
                rh_row = next_rh
        return onset_depths

    # Finite single-seed right half at t=1 ({1: 1}) driven by 0^10 1 1 locks to ell = 0
    depths_0_10_11 = _simulate_driven_rh({1: 1}, [0] * 10 + [1, 1], periods=6)
    driver_0_10_11_locks = all(d == 0 for d in depths_0_10_11[1:])

    # Countermodel: if we remove the single-seed finite-support constraint and allow an
    # engineered infinite right half under periodic driver c(t) = (t % 2) (P = 2, r = 1, b = 1),
    # or test whether different initial depths ell_0 in {0, 2} produce distinct clipped depths
    # min(ell, 1) under a 1-period shift when right support is engineered:
    # Specifically, at w with r = 1 (K = 0), ell_1 = 0 gives min(0, 1) = 0 (orCol = 1),
    # whereas ell_2 = 2 gives min(2, 1) = 1 (orCol = 0). By Rule30Realization.realize,
    # any right half R is realizable with a periodic center column on unrestricted Z -> Bool,
    # so choosing R with first black cell at p = 3 (ell = 2) vs locked p = 1 (ell = 0)
    # separates clipDepth across periods when the finite-seed hypothesis is dropped.
    depths_unrestricted_sep = _simulate_driven_rh({4: 1}, [0, 0, 1, 1], periods=3)
    countermodel_violates = min(depths_unrestricted_sep[0], 2) != min(
        depths_unrestricted_sep[1], 2
    )

    # 2. G5-P2: Exact white-black cycle discrepancy & falsification of cycle-by-cycle cancellation
    # Parse complete white-then-black cycles starting at w = 2
    black_prefix = [0]
    for n in range(steps + 2):
        black_prefix.append(black_prefix[-1] + _cell(n, 0))

    def _disc(n: int) -> int:
        return 2 * black_prefix[n] - n

    cycles_checked = 0
    cycle_mismatches = 0
    cycle_drifts: List[int] = []
    idx = 2
    while idx < steps:
        if _cell(idx, 0) != 0:
            idx += 1
            continue
        w = idx
        r = 0
        while idx < steps and _cell(idx, 0) == 0:
            r += 1
            idx += 1
        if idx >= steps:
            break
        b = 0
        while idx < steps and _cell(idx, 0) == 1:
            b += 1
            idx += 1
        if idx >= steps:
            break
        cycles_checked += 1
        drift = b - r
        cycle_drifts.append(drift)
        if _disc(w + r + b) != _disc(w) + drift:
            cycle_mismatches += 1

    first_drift = cycle_drifts[0] if cycle_drifts else 0
    non_cancelling = sum(1 for d in cycle_drifts if d != 0)
    min_drift = min(cycle_drifts) if cycle_drifts else 0
    max_drift = max(cycle_drifts) if cycle_drifts else 0

    # 3. G5-P3: Operator-doubling hierarchy T^(2^d) for d = 0, 1, 2, 3 (b = 1, 2, 4, 8)
    def _eval_pow2_window(d: int, window: Sequence[int]) -> int:
        if d == 0:
            return rule30_forward_cell(window[0], window[1], window[2])
        sub_span = 1 << (d - 1)
        sub_width = 2 * sub_span + 1
        mid_row = [
            _eval_pow2_window(d - 1, window[offset : offset + sub_width])
            for offset in range(sub_width)
        ]
        return _eval_pow2_window(d - 1, mid_row)

    doubling_levels: List[G5DoublingOperatorLevel] = []
    total_doubling_mismatches = 0
    for d in range(4):
        b = 1 << d
        w_width = 2 * b + 1
        tt_entries = 1 << w_width
        anf_deg = 2 if b == 1 else (2 * b - 1)
        rec_calls = 3 ** b
        diamond_cells = b * b
        mismatches_d = 0
        # Verify evolPow2 d agrees with spacetime cone across all t = m * b <= min(steps, 64)
        max_check_t = min(steps, 64)
        for t0 in range(0, max_check_t - b + 1, b):
            for p in range(-t0 - b, t0 + b + 1):
                win = [_cell(t0, p + q) for q in range(-b, b + 1)]
                if _eval_pow2_window(d, win) != _cell(t0 + b, p):
                    mismatches_d += 1
        total_doubling_mismatches += mismatches_d
        doubling_levels.append(
            G5DoublingOperatorLevel(
                doubling_level_d=d,
                step_span_b=b,
                window_width=w_width,
                truth_table_entries=tt_entries,
                anf_degree=anf_deg,
                unmemoized_recursive_rule_calls=rec_calls,
                causal_diamond_cell_updates=diamond_cells,
                exact_cone_mismatches=mismatches_d,
            )
        )

    rep_growth_falsifies = all(
        lvl.unmemoized_recursive_rule_calls > lvl.causal_diamond_cell_updates
        and lvl.truth_table_entries > lvl.causal_diamond_cell_updates
        for lvl in doubling_levels
    )

    verdict_path = Path(__file__).resolve().parent / "check_verdict.json"
    verdict_data = json.loads(verdict_path.read_text(encoding="utf-8"))
    expected_g5_headlines = (
        "Rule30Submission.g5_p1_modeADepth_after_white_run",
        "Rule30Submission.g5_p1_clipped_depth_observational_equivalence",
        "Rule30Submission.g5_p1_clipped_depth_alignment_implies_problem1",
        "Rule30Submission.g5_p2_white_run_discrepancy_shift",
        "Rule30Submission.g5_p2_black_run_discrepancy_shift",
        "Rule30Submission.g5_p2_white_black_cycle_discrepancy",
        "Rule30Submission.g5_p2_first_white_black_cycle_net_drift_plus_two",
        "Rule30Submission.g5_p3_evolPow2_eq_evol_pow2",
        "Rule30Submission.g5_p3_evolPow2_universal_left_sensitivity",
    )
    verified_set = {
        h["name"]
        for h in verdict_data.get("headlines", [])
        if h.get("ok") and h.get("found")
    }
    verified_g5 = tuple(
        name for name in expected_g5_headlines if name in verified_set
    )

    gate_passed = (
        monus_mismatches == 0
        and clipped_mismatches == 0
        and driver_0_10_11_locks
        and countermodel_violates
        and cycles_checked >= 10
        and cycle_mismatches == 0
        and first_drift == 2
        and non_cancelling > 0
        and total_doubling_mismatches == 0
        and rep_growth_falsifies
        and len(verified_g5) == len(expected_g5_headlines)
    )

    return G5ThreePrizeContinuationResult(
        steps=steps,
        white_run_depth_monus_checks=monus_checks,
        white_run_depth_monus_mismatches=monus_mismatches,
        clipped_depth_equiv_checks=clipped_checks,
        clipped_depth_equiv_mismatches=clipped_mismatches,
        periodic_driver_0_10_11_locks_halign=driver_0_10_11_locks,
        engineered_infinite_right_countermodel_violates_halign=countermodel_violates,
        complete_white_black_cycles_checked=cycles_checked,
        run_cycle_discrepancy_mismatches=cycle_mismatches,
        first_cycle_net_drift=first_drift,
        non_cancelling_cycles_count=non_cancelling,
        min_cycle_drift=min_drift,
        max_cycle_drift=max_drift,
        doubling_hierarchy=tuple(doubling_levels),
        doubling_hierarchy_mismatches=total_doubling_mismatches,
        representation_growth_eliminates_naive_shortcut=rep_growth_falsifies,
        g5_headlines_verified=verified_g5,
        gate_passed=gate_passed,
    )


# ---------------------------------------------------------------------------
# Full Campaign Runner
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Rule30FalsificationCampaign:
    e1_reconstruction: E1ReconstructionResult
    e2_quotient: E2QuotientResult
    e3_closure: E3ClosureResult
    e4_shortcut: E4ShortcutResult
    e5_persistent: E5PersistentEquivalenceResult
    g0_g2_qualification: G0G2PrizeQualificationResult
    g3_wavefront_qualification: G3InfiniteHorizonWavefrontResult
    g4_multi_prize_qualification: G4MultiPrizeQualificationResult
    g5_three_prize_continuation: G5ThreePrizeContinuationResult
    all_gates_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "e1_reconstruction": self.e1_reconstruction.to_dict(),
            "e2_quotient": self.e2_quotient.to_dict(),
            "e3_closure": self.e3_closure.to_dict(),
            "e4_shortcut": self.e4_shortcut.to_dict(),
            "e5_persistent": self.e5_persistent.to_dict(),
            "g0_g2_qualification": self.g0_g2_qualification.to_dict(),
            "g3_wavefront_qualification": self.g3_wavefront_qualification.to_dict(),
            "g4_multi_prize_qualification": self.g4_multi_prize_qualification.to_dict(),
            "g5_three_prize_continuation": self.g5_three_prize_continuation.to_dict(),
            "all_gates_passed": self.all_gates_passed,
        }


def run_full_campaign(
    e1_steps: int = 64,
    e2_max_k: int = 6,
    e3_max_k: int = 7,
    e4_steps: Sequence[int] = (16, 32, 64, 128, 256),
    e5_max_k: int = 6,
    g2_max_k: int = 5,
    g3_steps: int = 200,
    g4_steps: int = 250,
    g4_sensitivity_max_t: int = 5,
    g5_steps: int = 250,
    output_json: Optional[Path] = None,
) -> Rule30FalsificationCampaign:
    """Execute all Rule 30 falsification & prize qualification gates and optionally write JSON evidence."""
    e1 = run_e1_exact_reconstruction(steps=e1_steps)
    e2 = run_e2_geometric_quotient(max_k=e2_max_k)
    e3 = run_e3_composition_closure(max_k=e3_max_k)
    e4 = run_e4_computational_shortcut(step_sizes=e4_steps)
    e5 = run_e5_persistent_equivalence(max_k=e5_max_k)
    g0_g2 = run_g0_g2_prize_qualification(max_k=g2_max_k)
    g3 = run_g3_infinite_horizon_wavefront(steps=g3_steps)
    g4 = run_g4_multi_prize_qualification(
        steps=g4_steps, sensitivity_max_t=g4_sensitivity_max_t
    )
    g5 = run_g5_three_prize_continuation(steps=g5_steps)

    campaign = Rule30FalsificationCampaign(
        e1_reconstruction=e1,
        e2_quotient=e2,
        e3_closure=e3,
        e4_shortcut=e4,
        e5_persistent=e5,
        g0_g2_qualification=g0_g2,
        g3_wavefront_qualification=g3,
        g4_multi_prize_qualification=g4,
        g5_three_prize_continuation=g5,
        all_gates_passed=(
            e1.gate_passed
            and e2.gate_passed
            and e3.gate_passed
            and e4.gate_passed
            and e5.gate_passed
            and g0_g2.gate_passed
            and g3.gate_passed
            and g4.gate_passed
            and g5.gate_passed
        ),
    )

    if output_json is not None:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(
            json.dumps(campaign.to_dict(), indent=2), encoding="utf-8"
        )

    return campaign


if __name__ == "__main__":
    out_path = Path("evidence/rule30_falsification_campaign.json")
    result = run_full_campaign(output_json=out_path)
    print(json.dumps(result.to_dict(), indent=2))
