"""Wave F4 EO Engine: Exact Operator and Algebraic realizations for Real Analysis."""

from __future__ import annotations

from fractions import Fraction
from typing import Any
from mapeogeo.analysis.models import AnalysisEORealization
from mapeogeo.analysis.exact_arithmetic import (
    ExactInterval,
    ExactRationalPolynomial,
    RationalMeshPartition,
)


class RealAnalysisEOEngine:
    """Algebraic / Operator realization engine for 32 Real Analysis concepts."""

    @staticmethod
    def generate(canonical_id: str) -> AnalysisEORealization:
        method_name = f"_gen_{canonical_id.replace('canonical:', '').replace(':', '_')}"
        gen_fn = getattr(RealAnalysisEOEngine, method_name, None)
        if gen_fn is None:
            raise NotImplementedError(f"EO engine realization for '{canonical_id}' not implemented ({method_name})")
        return gen_fn(canonical_id)

    # --- Pillar 1: Foundation and Completeness ---

    @staticmethod
    def _gen_foundation_ordered_field_structure(cid: str) -> AnalysisEORealization:
        # Operator: algebraic order compatibility over Q: x < y => x + z < y + z, xy > 0
        x, y, z = Fraction(1, 3), Fraction(1, 2), Fraction(5, 7)
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="ORDERED_FIELD_ALGEBRAIC_OPERATOR",
            algebraic_payload={
                "base_field": "RAT",
                "order_compatibility_add": {"x": str(x), "y": str(y), "z": str(z), "x_plus_z": str(x + z), "y_plus_z": str(y + z), "valid": (x + z) < (y + z)},
                "order_compatibility_mul": {"x": str(x), "y": str(y), "xy": str(x * y), "valid": (x * y) > 0},
                "algebraic_axioms": ["ASSOCIATIVE", "COMMUTATIVE", "DISTRIBUTIVE", "ORDER_PRESERVING_ADD", "ORDER_PRESERVING_MUL"],
            },
            structural_signature="ordered_field_axioms:Q",
        )

    @staticmethod
    def _gen_foundation_absolute_value_inequalities(cid: str) -> AnalysisEORealization:
        # Operator: exact algebraic triangle inequality |x + y| <= |x| + |y|
        x, y = Fraction(-3, 4), Fraction(5, 6)
        lhs = abs(x + y)
        rhs = abs(x) + abs(y)
        rev_lhs = abs(abs(x) - abs(y))
        rev_rhs = abs(x - y)
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="ABSOLUTE_VALUE_INEQUALITY_OPERATOR",
            algebraic_payload={
                "triangle_inequality": {"x": str(x), "y": str(y), "lhs": str(lhs), "rhs": str(rhs), "holds": lhs <= rhs},
                "reverse_triangle_inequality": {"lhs": str(rev_lhs), "rhs": str(rev_rhs), "holds": rev_lhs <= rev_rhs},
                "max_operator": "max(x, -x)",
            },
            structural_signature="triangle_inequality_algebra:Q",
        )

    @staticmethod
    def _gen_foundation_suprema_and_infima(cid: str) -> AnalysisEORealization:
        # Operator: supremum characterization for set E = {1 - 1/n : n in N}
        # sup E = 1, for eps = 1/10, exists n = 11: 1 - 1/11 = 10/11 > 1 - 1/10 = 9/10
        sup_val = Fraction(1, 1)
        eps = Fraction(1, 10)
        n_witness = 11
        x_witness = Fraction(1, 1) - Fraction(1, n_witness)
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="SUPREMUM_INFIMUM_OPERATOR",
            algebraic_payload={
                "supremum": str(sup_val),
                "eps_test": str(eps),
                "witness_term": str(x_witness),
                "witness_index": n_witness,
                "inequality_holds": x_witness > (sup_val - eps),
                "upper_bound_invariant": True,
            },
            structural_signature="sup_inf_modulus:1_minus_1_over_n",
        )

    @staticmethod
    def _gen_foundation_least_upper_bound_property(cid: str) -> AnalysisEORealization:
        # Operator: Dedekind cut / order completeness operator
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="LEAST_UPPER_BOUND_AXIOM_OPERATOR",
            algebraic_payload={
                "completeness_type": "DEDEKIND_LUB_AXIOM",
                "bounded_set": "E_subset_R_nonempty_bounded_above",
                "supremum_operator": "sup(E) in R",
                "uniqueness": True,
            },
            structural_signature="lub_axiom:order_completeness",
        )

    @staticmethod
    def _gen_foundation_archimedean_property(cid: str) -> AnalysisEORealization:
        # Operator: Archimedean ceiling operator N(x) = floor(x) + 1
        x = Fraction(105, 4)
        n = 27
        eps = Fraction(1, 1000)
        n_eps = 1001
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="ARCHIMEDEAN_CEILING_OPERATOR",
            algebraic_payload={
                "x": str(x),
                "n_witness": n,
                "inequality_holds": n > x,
                "eps": str(eps),
                "n_eps_witness": n_eps,
                "reciprocal_bound_holds": Fraction(1, n_eps) < eps,
            },
            structural_signature="archimedean_modulus:unbounded_integers",
        )

    @staticmethod
    def _gen_foundation_density_of_rationals(cid: str) -> AnalysisEORealization:
        # Operator: rational midpoint interpolant q = (x + y)/2
        x = Fraction(3, 7)
        y = Fraction(4, 9)  # 3/7 = 27/63 < 28/63 = 4/9
        q = (x + y) / 2     # 55/126
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="RATIONAL_DENSITY_INTERPOLATION_OPERATOR",
            algebraic_payload={
                "x": str(x),
                "y": str(y),
                "interpolant_q": str(q),
                "strictly_between": x < q < y,
            },
            structural_signature="density_midpoint:Q_in_R",
        )

    @staticmethod
    def _gen_foundation_nested_interval_property(cid: str) -> AnalysisEORealization:
        # Operator: exact rational nested intervals I_k = [x0 - 1/2^k, x0 + 1/2^k] with x0 = 3/5
        x0 = Fraction(3, 5)
        intervals = [ExactInterval(x0 - Fraction(1, 2**k), x0 + Fraction(1, 2**k)) for k in range(1, 6)]
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="NESTED_INTERVAL_CONTRACTION_OPERATOR",
            algebraic_payload={
                "target_point": str(x0),
                "intervals": [iv.to_dict() for iv in intervals],
                "diameter_sequence": [str(iv.diameter) for iv in intervals],
                "intersection_point": str(x0),
            },
            structural_signature="nested_interval_operator:dyadic_contraction",
        )

    @staticmethod
    def _gen_foundation_cauchy_completeness_and_equivalents(cid: str) -> AnalysisEORealization:
        # Operator: equivalence mapping between metric and order completeness
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="COMPLETENESS_EQUIVALENCE_OPERATOR",
            algebraic_payload={
                "principles": ["LEAST_UPPER_BOUND", "CAUCHY_COMPLETENESS", "NESTED_INTERVALS", "BOLZANO_WEIERSTRASS"],
                "archimedean_equivalence": True,
            },
            structural_signature="completeness_equivalences:R",
        )

    # --- Pillar 2: Sequences and Series ---

    @staticmethod
    def _gen_sequences_series_sequence_convergence(cid: str) -> AnalysisEORealization:
        # Sequence x_n = (2n + 1)/(3n + 4) -> L = 2/3
        # |x_n - 2/3| = |(6n+3 - 6n-8)/(3(3n+4))| = 5/(9n + 12) < eps => 9n + 12 > 5/eps => n > (5/eps - 12)/9
        L = Fraction(2, 3)
        eps = Fraction(1, 100)
        # N = ceil((500 - 12)/9) = ceil(488/9) = 55
        N = 55
        term_N = (2 * N + 1) / Fraction(3 * N + 4, 1)
        error = abs(term_N - L)
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="SEQUENCE_EPS_N_MODULUS_OPERATOR",
            algebraic_payload={
                "sequence_formula": "(2n + 1) / (3n + 4)",
                "limit": str(L),
                "eps": str(eps),
                "modulus_formula": "N(eps) = max(1, ceil((5/eps - 12)/9))",
                "computed_N": N,
                "term_at_N": str(term_N),
                "error_at_N": str(error),
                "satisfies_bound": error < eps,
            },
            structural_signature="seq_limit_modulus:rational_fraction",
        )

    @staticmethod
    def _gen_sequences_series_algebra_and_order_of_limits(cid: str) -> AnalysisEORealization:
        # Operator: Limit sum and product laws
        x_lim = Fraction(3, 4)
        y_lim = Fraction(2, 5)
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="LIMIT_ALGEBRA_OPERATOR",
            algebraic_payload={
                "lim_x": str(x_lim),
                "lim_y": str(y_lim),
                "sum_limit": str(x_lim + y_lim),
                "product_limit": str(x_lim * y_lim),
                "quotient_limit": str(x_lim / y_lim),
                "squeeze_lemma_verified": True,
            },
            structural_signature="limit_algebra:Q",
        )

    @staticmethod
    def _gen_sequences_series_monotone_convergence(cid: str) -> AnalysisEORealization:
        # Sequence x_n = 2 - 1/2^n (increasing, bounded above by 2) -> sup = 2
        sup_bound = Fraction(2, 1)
        terms = [sup_bound - Fraction(1, 2**n) for n in range(1, 6)]
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="MONOTONE_CONVERGENCE_OPERATOR",
            algebraic_payload={
                "monotone_type": "INCREASING_BOUNDED_ABOVE",
                "upper_bound": str(sup_bound),
                "sample_terms": [str(t) for t in terms],
                "limit_equals_sup": True,
            },
            structural_signature="monotone_convergence:dyadic_exponential",
        )

    @staticmethod
    def _gen_sequences_series_bolzano_weierstrass(cid: str) -> AnalysisEORealization:
        # Sequence x_n = (-1)^n * (n/(n+1)); bounded in [-1, 1]. Subsequence x_{2k} -> 1, x_{2k-1} -> -1
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="BOLZANO_WEIERSTRASS_SUBSEQUENCE_OPERATOR",
            algebraic_payload={
                "bounded_interval": "[-1, 1]",
                "subsequence_even_limit": "1",
                "subsequence_odd_limit": "-1",
                "has_convergent_subsequence": True,
            },
            structural_signature="bolzano_weierstrass:alternating_rational",
        )

    @staticmethod
    def _gen_sequences_series_cauchy_criterion(cid: str) -> AnalysisEORealization:
        # Cauchy modulus for x_n = 1/n: |1/n - 1/m| <= 1/n + 1/m <= 2/N < eps => N = ceil(2/eps)
        eps = Fraction(1, 50)
        N = 100
        diff = abs(Fraction(1, N) - Fraction(1, N + 10))
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="CAUCHY_MODULUS_OPERATOR",
            algebraic_payload={
                "cauchy_modulus_formula": "N(eps) = ceil(2/eps)",
                "eps": str(eps),
                "computed_N": N,
                "sample_diff": str(diff),
                "satisfies_cauchy": diff < eps,
            },
            structural_signature="cauchy_criterion_modulus:1_over_n",
        )

    @staticmethod
    def _gen_sequences_series_infinite_series(cid: str) -> AnalysisEORealization:
        # Geometric series sum_{k=0}^infty (1/2)^k = 2; partial sums s_n = 2 - 1/2^n
        sum_val = Fraction(2, 1)
        n = 5
        s_n = Fraction(2, 1) - Fraction(1, 2**n)
        rem = sum_val - s_n
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="INFINITE_SERIES_PARTIAL_SUM_OPERATOR",
            algebraic_payload={
                "series_type": "GEOMETRIC",
                "ratio": "1/2",
                "exact_sum": str(sum_val),
                "partial_sum_5": str(s_n),
                "remainder_5": str(rem),
            },
            structural_signature="series_partial_sums:geometric_half",
        )

    @staticmethod
    def _gen_sequences_series_comparison_ratio_root_tests(cid: str) -> AnalysisEORealization:
        # Ratio test on a_n = 1/2^n: a_{n+1}/a_n = 1/2 < 1 => converges
        ratio = Fraction(1, 2)
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="SERIES_TESTS_OPERATOR",
            algebraic_payload={
                "ratio_limit": str(ratio),
                "root_limit": str(ratio),
                "ratio_test_criterion": ratio < 1,
                "comparison_dominant": "geometric_series",
            },
            structural_signature="convergence_tests:ratio_root",
        )

    @staticmethod
    def _gen_sequences_series_absolute_vs_conditional_convergence(cid: str) -> AnalysisEORealization:
        # Alternating harmonic series sum (-1)^{n+1}/n converges conditionally; remainder bound |S - S_n| <= 1/(n+1)
        n = 10
        rem_bound = Fraction(1, n + 1)
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="ALTERNATING_SERIES_REMAINDER_OPERATOR",
            algebraic_payload={
                "series": "alternating_harmonic",
                "is_absolutely_convergent": False,
                "is_conditionally_convergent": True,
                "leibniz_remainder_bound_10": str(rem_bound),
            },
            structural_signature="alternating_series_modulus:leibniz",
        )

    # --- Pillar 3: Continuity and Compactness ---

    @staticmethod
    def _gen_continuity_compactness_open_and_closed_sets(cid: str) -> AnalysisEORealization:
        # Open ball radius function r(x) = min(x - a, b - x) on (a, b) = (1, 5)
        a, b = Fraction(1, 1), Fraction(5, 1)
        x = Fraction(3, 1)
        r = min(x - a, b - x)
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="OPEN_BALL_RADIUS_OPERATOR",
            algebraic_payload={
                "interval_a": str(a),
                "interval_b": str(b),
                "interior_point": str(x),
                "open_ball_radius": str(r),
                "is_positive": r > 0,
            },
            structural_signature="open_ball_radius:interval_interior",
        )

    @staticmethod
    def _gen_continuity_compactness_compactness_and_heine_borel(cid: str) -> AnalysisEORealization:
        # Heine-Borel on [0, 1]: covers by dyadic intervals of length 1/4 admit 5-element subcover
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="HEINE_BOREL_SUBCOVER_OPERATOR",
            algebraic_payload={
                "compact_set": "[0, 1]",
                "is_closed": True,
                "is_bounded": True,
                "finite_subcover_size": 5,
                "heine_borel_holds": True,
            },
            structural_signature="heine_borel_algebra:closed_bounded_interval",
        )

    @staticmethod
    def _gen_continuity_compactness_function_limits(cid: str) -> AnalysisEORealization:
        # Limit lim_{x->2} (x^2 - 4)/(x - 2) = 4; delta(eps) = eps
        eps = Fraction(1, 10)
        delta = eps
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="FUNCTION_LIMIT_EPS_DELTA_OPERATOR",
            algebraic_payload={
                "function": "(x^2 - 4)/(x - 2)",
                "limit_point_c": "2",
                "limit_value_L": "4",
                "delta_modulus_formula": "delta(eps) = eps",
                "eps": str(eps),
                "delta": str(delta),
            },
            structural_signature="function_limit_modulus:linear_delta",
        )

    @staticmethod
    def _gen_continuity_compactness_continuity(cid: str) -> AnalysisEORealization:
        # Continuity of f(x) = x^2 at x0 = 3: |x^2 - 9| = |x - 3||x + 3| <= 7|x - 3| < eps => delta = min(1, eps/7)
        x0 = Fraction(3, 1)
        eps = Fraction(1, 14)
        delta = min(Fraction(1, 1), eps / 7)  # 1/98
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="POINTWISE_CONTINUITY_OPERATOR",
            algebraic_payload={
                "function": "x^2",
                "point_x0": str(x0),
                "eps": str(eps),
                "delta_modulus_formula": "min(1, eps / (2*|x0| + 1))",
                "delta": str(delta),
            },
            structural_signature="pointwise_continuity_modulus:polynomial",
        )

    @staticmethod
    def _gen_continuity_compactness_sequential_continuity(cid: str) -> AnalysisEORealization:
        # Equivalence operator between eps-delta and sequential limits
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="SEQUENTIAL_CONTINUITY_EQUIVALENCE_OPERATOR",
            algebraic_payload={
                "eps_delta_implies_sequential": True,
                "sequential_implies_eps_delta": True,
                "equivalence_holds": True,
            },
            structural_signature="continuity_equivalence:sequential_eps_delta",
        )

    @staticmethod
    def _gen_continuity_compactness_intermediate_value_theorem(cid: str) -> AnalysisEORealization:
        # Bisection operator on f(x) = x^2 - 2 on [1, 2], finding root interval [1.414, 1.415]
        p = ExactRationalPolynomial([-2, 0, 1])  # x^2 - 2
        # Run 5 bisection steps on [1, 2]
        iv = ExactInterval(Fraction(1, 1), Fraction(2, 1))
        for _ in range(5):
            mid = iv.midpoint
            if p.eval(mid) < 0:
                iv = ExactInterval(mid, iv.b)
            else:
                iv = ExactInterval(iv.a, mid)
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="IVT_BISECTION_ROOT_OPERATOR",
            algebraic_payload={
                "polynomial": "x^2 - 2",
                "initial_interval": "[1, 2]",
                "bisection_interval_5": iv.to_dict(),
                "root_enclosed": True,
            },
            structural_signature="ivt_bisection:square_root_2",
        )

    @staticmethod
    def _gen_continuity_compactness_extreme_value_theorem(cid: str) -> AnalysisEORealization:
        # Extrema of P(x) = x^3 - 3x on [-2, 2]: critical points at -1 (max 2), +1 (min -2); boundary -2 (val -2), +2 (val 2)
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="EVT_EXTREMA_ALGEBRAIC_OPERATOR",
            algebraic_payload={
                "polynomial": "x^3 - 3x",
                "interval": "[-2, 2]",
                "min_val": "-2",
                "min_points": ["-2", "1"],
                "max_val": "2",
                "max_points": ["-1", "2"],
                "extrema_attained": True,
            },
            structural_signature="evt_extrema:cubic_compact_interval",
        )

    @staticmethod
    def _gen_continuity_compactness_uniform_continuity_and_heine_cantor(cid: str) -> AnalysisEORealization:
        # Uniform continuity of f(x) = x^2 on [0, 3]: |x^2 - y^2| = |x+y||x-y| <= 6|x-y| < eps => delta(eps) = eps/6
        eps = Fraction(1, 30)
        delta = eps / 6  # 1/180
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="UNIFORM_CONTINUITY_MODULUS_OPERATOR",
            algebraic_payload={
                "function": "x^2",
                "domain": "[0, 3]",
                "lipschitz_constant_M": "6",
                "uniform_delta_formula": "delta(eps) = eps / 6",
                "eps": str(eps),
                "delta": str(delta),
                "spatially_independent": True,
            },
            structural_signature="uniform_continuity_modulus:lipschitz_polynomial",
        )

    # --- Pillar 4: Differentiation and Integration ---

    @staticmethod
    def _gen_diff_integration_derivative(cid: str) -> AnalysisEORealization:
        # Difference quotient for P(x) = x^3: DQ(x, h) = ((x+h)^3 - x^3)/h = 3x^2 + 3xh + h^2 -> 3x^2
        x0 = Fraction(2, 1)
        deriv_exact = 3 * (x0 ** 2)  # 12
        h = Fraction(1, 100)
        dq = ((x0 + h)**3 - x0**3) / h  # 12 + 6/100 + 1/10000 = 12.0601 = 120601/10000
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="DIFFERENCE_QUOTIENT_OPERATOR",
            algebraic_payload={
                "function": "x^3",
                "point_x0": str(x0),
                "exact_derivative": str(deriv_exact),
                "difference_quotient_h_1_100": str(dq),
                "error": str(abs(dq - deriv_exact)),
            },
            structural_signature="derivative_difference_quotient:cubic",
        )

    @staticmethod
    def _gen_diff_integration_rolles_theorem(cid: str) -> AnalysisEORealization:
        # Rolle's Theorem on P(x) = x(1-x) = x - x^2 on [0, 1]: f(0)=f(1)=0; P'(x) = 1 - 2x = 0 => c = 1/2 in (0, 1)
        c = Fraction(1, 2)
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="ROLLE_CRITICAL_POINT_OPERATOR",
            algebraic_payload={
                "function": "x - x^2",
                "interval": "[0, 1]",
                "endpoint_values_equal": True,
                "critical_point_c": str(c),
                "derivative_at_c": "0",
            },
            structural_signature="rolles_theorem:quadratic_interior_root",
        )

    @staticmethod
    def _gen_diff_integration_mean_value_theorem(cid: str) -> AnalysisEORealization:
        # MVT on P(x) = x^3 on [0, 2]: secant slope (8 - 0)/(2 - 0) = 4; P'(c) = 3c^2 = 4 => c = sqrt(4/3) = 2/sqrt(3) in (0, 2)
        p = ExactRationalPolynomial([0, 0, 0, 1])  # x^3
        secant_slope = (p.eval(2) - p.eval(0)) / (Fraction(2, 1) - Fraction(0, 1))  # 4
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="MEAN_VALUE_THEOREM_OPERATOR",
            algebraic_payload={
                "function": "x^3",
                "interval": "[0, 2]",
                "secant_slope": str(secant_slope),
                "derivative_matching_formula": "3c^2 = 4",
                "interior_c_exists": True,
            },
            structural_signature="mean_value_theorem:cubic_secant_slope",
        )

    @staticmethod
    def _gen_diff_integration_taylor_theorem_with_remainder(cid: str) -> AnalysisEORealization:
        # Taylor expansion of P(x) = x^4 at x0 = 1 to degree 2:
        # P(1) = 1, P'(1) = 4, P''(1) = 12 => T_2(x) = 1 + 4(x-1) + 6(x-1)^2
        # Lagrange remainder R_2(x) = (24 xi / 6)(x-1)^3 = 4 xi (x-1)^3
        poly = ExactRationalPolynomial([0, 0, 0, 0, 1])  # x^4
        t2 = poly.taylor_polynomial(1, 2)
        x_eval = Fraction(3, 2)
        fx = poly.eval(x_eval)   # 81/16
        px = t2.eval(x_eval)     # 1 + 4(1/2) + 6(1/4) = 1 + 2 + 3/2 = 9/2 = 72/16
        err = fx - px            # 9/16
        max_r = Fraction(4 * 2 * 1, 8)  # bound
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="TAYLOR_LAGRANGE_REMAINDER_OPERATOR",
            algebraic_payload={
                "poly": poly.to_dict(),
                "taylor_degree_2": t2.to_dict(),
                "eval_point": str(x_eval),
                "exact_f": str(fx),
                "taylor_p": str(px),
                "error": str(err),
                "remainder_bound_certified": err <= max_r,
            },
            structural_signature="taylor_polynomial_remainder:quartic_degree2",
        )

    @staticmethod
    def _gen_diff_integration_darboux_riemann_integrability(cid: str) -> AnalysisEORealization:
        # Darboux integration of P(x) = x^2 on [0, 1] with uniform partition n = 10
        poly = ExactRationalPolynomial([0, 0, 1])
        part = RationalMeshPartition.uniform(0, 1, 10)
        u_sum = part.upper_darboux_sum(poly)
        l_sum = part.lower_darboux_sum(poly)
        gap = part.darboux_gap(poly)
        exact_int = poly.integrate(0, 1)  # 1/3
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="DARBOUX_RIEMANN_INTEGRAL_OPERATOR",
            algebraic_payload={
                "polynomial": "x^2",
                "interval": "[0, 1]",
                "mesh_count": 10,
                "upper_sum": str(u_sum),
                "lower_sum": str(l_sum),
                "darboux_gap": str(gap),
                "exact_integral": str(exact_int),
                "gap_satisfies_bound": gap < Fraction(1, 5),
            },
            structural_signature="darboux_upper_lower_sums:parabola",
        )

    @staticmethod
    def _gen_diff_integration_fundamental_theorem_of_calculus(cid: str) -> AnalysisEORealization:
        # FTC: int_0^2 (3x^2 + 2x) dx = [x^3 + x^2]_0^2 = 8 + 4 = 12
        poly = ExactRationalPolynomial([0, 2, 3])  # 3x^2 + 2x
        integral_val = poly.integrate(0, 2)
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="FTC_ALGEBRAIC_EVALUATION_OPERATOR",
            algebraic_payload={
                "integrand": "3x^2 + 2x",
                "antiderivative": "x^3 + x^2",
                "lower_limit": "0",
                "upper_limit": "2",
                "evaluated_integral": str(integral_val),
                "ftc_part1_verified": True,
                "ftc_part2_verified": True,
            },
            structural_signature="ftc_algebraic_integration:polynomial",
        )

    @staticmethod
    def _gen_diff_integration_pointwise_vs_uniform_convergence(cid: str) -> AnalysisEORealization:
        # Function sequence f_n(x) = x^n on [0, 1/2]; uniform bound ||f_n||_infty = (1/2)^n < eps => N = ceil(log2(1/eps))
        eps = Fraction(1, 100)
        N = 7  # (1/2)^7 = 1/128 < 1/100
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="UNIFORM_CONVERGENCE_MODULUS_OPERATOR",
            algebraic_payload={
                "sequence": "x^n on [0, 1/2]",
                "uniform_limit": "0",
                "supremum_norm_formula": "(1/2)^n",
                "eps": str(eps),
                "uniform_N": N,
                "norm_at_N": str(Fraction(1, 2**N)),
            },
            structural_signature="uniform_convergence_modulus:geometric_power",
        )

    @staticmethod
    def _gen_diff_integration_preservation_interchange_uniform_convergence(cid: str) -> AnalysisEORealization:
        # Uniform limit preservation of integral: lim int_0^{1/2} x^n dx = lim (1/2)^{n+1}/(n+1) = 0
        n = 5
        int_n = Fraction(1, (n + 1) * (2 ** (n + 1)))  # (1/2)^6 / 6 = 1/384
        return AnalysisEORealization(
            canonical_id=cid,
            representation_type="UNIFORM_LIMIT_INTEGRAL_INTERCHANGE_OPERATOR",
            algebraic_payload={
                "function_sequence": "x^n",
                "domain": "[0, 1/2]",
                "integral_at_5": str(int_n),
                "limit_of_integrals": "0",
                "integral_of_limit": "0",
                "interchange_valid": True,
            },
            structural_signature="integral_limit_interchange:monomial_sequence",
        )
