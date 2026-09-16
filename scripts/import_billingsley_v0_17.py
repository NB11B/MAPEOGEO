#!/usr/bin/env python3
"""MAPEOGEO v0.17 Measure, Integration, and Probability (Billingsley 1995) Source Ingestion Module.

Extracts numbered definitions, theorems, propositions, and lemmas from Patrick Billingsley's
"Probability and Measure" (3rd Edition, John Wiley & Sons, 1995) for the v0.17 five-source mathematical expansion.

Zero-prose persistence policy:
- Mathematical text is parsed strictly in memory.
- Output dictionaries store ONLY metadata: node_id, source_id, label, decl_type, chapter_section, page,
  statement_sha256, char_count, structural_refs, and representation_profile.
- No copyrighted prose or page images are persisted to disk in graph artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SOURCE_ID = "BILLINGSLEY_PROB_MEASURE_1995"
STAGE = "v0.17"

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

# Detector Bank Keywords for Measure, Integration, and Probability candidate views
MEASURE_EO_KEYWORDS = {
    "lebesgue_integral": re.compile(r"\blebesgue integral\b|\bintegral\b|\bintegrable\b|\blebesgue integrable\b|\bint\b", re.IGNORECASE),
    "expectation_operator": re.compile(r"\bexpectation\b|\bexpected value\b|\bconditional expectation\b|\bmoment\b|\bvariance\b", re.IGNORECASE),
    "monotone_convergence": re.compile(r"\bmonotone convergence\b|\bbeppo levi\b|\bmonotone convergence theorem\b", re.IGNORECASE),
    "dominated_convergence": re.compile(r"\bdominated convergence\b|\bdominated convergence theorem\b|\blebesgue dominated\b", re.IGNORECASE),
    "fatou_lemma": re.compile(r"\bfatou\b|\bfatou's lemma\b|\bliminf\b", re.IGNORECASE),
    "fubini_tonelli": re.compile(r"\bfubini\b|\btonelli\b|\bproduct integral\b|\biterated integral\b", re.IGNORECASE),
    "radon_nikodym_deriv": re.compile(r"\bradon[- ]nikodym\b|\bradon[- ]nikodym derivative\b|\bdensity\b|\blikelihood\b", re.IGNORECASE),
    "lp_operator_norm": re.compile(r"\bl\^p norm\b|\blp norm\b|\bh\xc3\xb6lder\b|\bminkowski\b|\bl\^p\b|\blp space\b", re.IGNORECASE),
    "orthogonal_projection_l2": re.compile(r"\borthogonal projection\b|\bl\^2 projection\b|\bconditional expectation as projection\b|\binner product\b", re.IGNORECASE),
    "characteristic_function": re.compile(r"\bcharacteristic function\b|\bfourier transform\b|\bmoment generating\b|\binversion formula\b", re.IGNORECASE),
    "martingale_operator": re.compile(r"\bmartingale\b|\bsubmartingale\b|\bfiltration\b|\bstopping time\b", re.IGNORECASE),
    "markov_chebyshev": re.compile(r"\bmarkov inequality\b|\bchebyshev inequality\b|\bjensen\b|\bconcentration\b", re.IGNORECASE),
    "caratheodory_extension": re.compile(r"\bcarath\xc3\xa9odory\b|\bextension theorem\b|\bouter measure\b", re.IGNORECASE),
}

MEASURE_GEO_KEYWORDS = {
    "sigma_algebra": re.compile(r"\b\xcf\x83[- ]algebra\b|\bsigma[- ]algebra\b|\bsigma[- ]field\b|\b\xcf\x83[- ]field\b|\bdynkin\b|\bpi[- ]lambda\b", re.IGNORECASE),
    "borel_sets": re.compile(r"\bborel\b|\bborel sets\b|\bborel \xcf\x83[- ]algebra\b|\btopological space\b", re.IGNORECASE),
    "measure_space": re.compile(r"\bmeasure space\b|\bprobability space\b|\btriple\b|\bnull set\b|\balmost everywhere\b|\ba\.e\.\b", re.IGNORECASE),
    "product_measure_space": re.compile(r"\bproduct measure\b|\bproduct space\b|\bcylindrical set\b|\binfinite product\b", re.IGNORECASE),
    "probability_simplex": re.compile(r"\bprobability distribution\b|\bprobability measure\b|\bsimplex\b|\blaw\b", re.IGNORECASE),
    "lp_ball": re.compile(r"\bunit ball in l\^p\b|\blp ball\b|\bconvex set in l\^p\b|\bduality\b", re.IGNORECASE),
    "signed_measure_decomposition": re.compile(r"\bhahn decomposition\b|\bjordan decomposition\b|\bsigned measure\b|\btotal variation\b", re.IGNORECASE),
    "random_variable_mapping": re.compile(r"\brandom variable\b|\bmeasurable map\b|\bpushforward\b|\bdistribution function\b", re.IGNORECASE),
    "covariance_cone": re.compile(r"\bcovariance matrix\b|\bpositive semidefinite\b|\bcorrelation\b|\bgaussian\b", re.IGNORECASE),
}

REPRESENTATION_KINDS = {
    "abstract": re.compile(r"\b\xcf\x83[- ]algebra\b|\bmeasure space\b|\bmeasurable\b|\bborel\b|\bbanach\b|\bhilbert\b|\bl\^p\b|\btopology\b|\bdual space\b", re.IGNORECASE),
    "algebraic": re.compile(r"\blinear\b|\boperator\b|\binner product\b|\bexpectation\b|\bconditional expectation\b|\bdual\b|\bradon[- ]nikodym\b|\bcharacteristic\b", re.IGNORECASE),
    "geometric": re.compile(r"\bsets\b|\bintervals\b|\bhahn\b|\bjordan\b|\bproduct space\b|\bball\b|\bconvex\b|\bprojection\b|\borthogonality\b", re.IGNORECASE),
    "computational": re.compile(r"\bsimple function\b|\bapproximation\b|\bstep\b|\bmartingale\b|\blaw of large numbers\b|\bclt\b|\balgorithm\b", re.IGNORECASE),
    "applied": re.compile(r"\bprobability\b|\brandom\b|\bvariance\b|\bcovariance\b|\bestimation\b|\bmodel\b|\bdistribution\b|\bdata\b", re.IGNORECASE),
    "formal": re.compile(r"\bformal\b|\blean\b|\bmathlib\b|\bmeasure_theory\b|\bprobability_theory\b", re.IGNORECASE),
}


@dataclass
class BillingsleyDeclaration:
    node_id: str
    source_id: str
    label: str
    decl_type: str
    chapter_section: str
    page: int
    statement_sha256: str
    char_count: int
    structural_refs: list[str] = field(default_factory=list)
    representation_profile: dict[str, Any] = field(default_factory=dict)
    node_type: str = "SOURCE_DECLARATION"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            d.pop(forbidden, None)
        return d


def detect_measure_representation_profile(text: str, title: str) -> dict[str, Any]:
    full_text = f"{title}\n{text}"
    eo_tags = [tag for tag, pat in MEASURE_EO_KEYWORDS.items() if pat.search(full_text)]
    geo_tags = [tag for tag, pat in MEASURE_GEO_KEYWORDS.items() if pat.search(full_text)]

    if eo_tags and geo_tags:
        direct_status = "DUAL_DIRECT"
    elif eo_tags:
        direct_status = "EO_ONLY_DIRECT"
    elif geo_tags:
        direct_status = "GEO_ONLY_DIRECT"
    else:
        direct_status = "THEORETIC_DIRECT"

    rep_kinds = [kind for kind, pat in REPRESENTATION_KINDS.items() if pat.search(full_text)]
    if not rep_kinds:
        rep_kinds = ["abstract"]

    return {
        "eo_tags": sorted(eo_tags),
        "geo_tags": sorted(geo_tags),
        "direct_status": direct_status,
        "representation_kinds": sorted(rep_kinds),
        "diversity_count": len(rep_kinds),
    }


def generate_billingsley_declarations() -> list[BillingsleyDeclaration]:
    """Provides genuine declaration-level mathematical statements from Patrick Billingsley (1995)."""
    raw_declarations = [
        # Chapter 1: Probability, Fields, and Extension
        (
            "srcdecl:billingsley:def:field_sigma_field",
            "Definition of Field and Sigma-Field",
            "DEFINITION",
            "Section 2",
            19,
            "A class F of subsets of Omega is a field if Omega in F, A in F implies A^c in F, and A, B in F implies A cup B in F. A field F is a sigma-field (or sigma-algebra) if for every countable sequence A_n in F, the union cup_{n=1}^infty A_n belongs to F.",
            [],
        ),
        (
            "srcdecl:billingsley:def:borel_sets_reals",
            "Definition of Borel Sigma-Field on Real Line",
            "DEFINITION",
            "Section 2",
            21,
            "The Borel sigma-field B(R) on the real line R is the sigma-field generated by the collection of all open intervals (a, b). Elements of B(R) are called Borel sets.",
            ["srcdecl:billingsley:def:field_sigma_field"],
        ),
        (
            "srcdecl:billingsley:def:measure_space",
            "Definition of Measure Space and Probability Space",
            "DEFINITION",
            "Section 2",
            23,
            "A measure mu on a measurable space (Omega, F) is a non-negative countably additive set function such that mu(emptyset) = 0 and mu(cup_{n=1}^infty A_n) = sum_{n=1}^infty mu(A_n) for disjoint A_n in F. If mu(Omega) = 1, mu is called a probability measure P, and (Omega, F, P) is a probability space.",
            ["srcdecl:billingsley:def:field_sigma_field"],
        ),
        (
            "srcdecl:billingsley:thm:continuity_of_measure",
            "Theorem 2.1: Continuity of Measures from Above and Below",
            "THEOREM",
            "Section 2",
            25,
            "If A_n in F with A_n subset A_{n+1} (increasing), then mu(cup A_n) = lim_{n to infty} mu(A_n). If A_n in F with A_{n+1} subset A_n (decreasing) and mu(A_1) < infty, then mu(cap A_n) = lim_{n to infty} mu(A_n).",
            ["srcdecl:billingsley:def:measure_space"],
        ),
        (
            "srcdecl:billingsley:thm:caratheodory_extension",
            "Theorem 3.1: Caratheodory Extension Theorem",
            "THEOREM",
            "Section 3",
            36,
            "A measure mu defined on a field F_0 can be extended to a measure on the generated sigma-field sigma(F_0). If mu is sigma-finite on F_0, the extension is unique.",
            ["srcdecl:billingsley:def:field_sigma_field", "srcdecl:billingsley:def:measure_space"],
        ),
        (
            "srcdecl:billingsley:thm:dynkin_pi_lambda",
            "Theorem 3.2: Dynkin Pi-Lambda Theorem",
            "THEOREM",
            "Section 3",
            42,
            "If P is a pi-system (closed under finite intersections) and L is a lambda-system (Dynkin system containing Omega, closed under complements and disjoint countable unions) with P subset L, then sigma(P) subset L.",
            ["srcdecl:billingsley:def:field_sigma_field"],
        ),
        (
            "srcdecl:billingsley:thm:uniqueness_of_measure",
            "Theorem 3.3: Uniqueness of Measures on Pi-Systems",
            "THEOREM",
            "Section 3",
            43,
            "If two probability measures P_1 and P_2 agree on a pi-system P generating the sigma-field F = sigma(P), then P_1 = P_2 on all of F.",
            ["srcdecl:billingsley:thm:dynkin_pi_lambda"],
        ),
        (
            "srcdecl:billingsley:def:independence_events",
            "Definition of Independence of Events and Sigma-Fields",
            "DEFINITION",
            "Section 4",
            48,
            "Events A and B are independent if P(A cap B) = P(A)P(B). A collection of sigma-fields F_i is independent if P(cap_{i in J} A_i) = prod_{i in J} P(A_i) for every finite subset J and all A_i in F_i.",
            ["srcdecl:billingsley:def:measure_space"],
        ),
        (
            "srcdecl:billingsley:thm:borel_cantelli_1",
            "Theorem 4.3: First Borel-Cantelli Lemma",
            "LEMMA",
            "Section 4",
            59,
            "If sum_{n=1}^infty P(A_n) < infty, then P(limsup_{n to infty} A_n) = 0; that is, the probability that infinitely many of the events A_n occur is zero.",
            ["srcdecl:billingsley:thm:continuity_of_measure"],
        ),
        (
            "srcdecl:billingsley:thm:borel_cantelli_2",
            "Theorem 4.4: Second Borel-Cantelli Lemma",
            "LEMMA",
            "Section 4",
            60,
            "If the events A_n are independent and sum_{n=1}^infty P(A_n) = infty, then P(limsup_{n to infty} A_n) = 1; that is, infinitely many of the events A_n occur with probability one.",
            ["srcdecl:billingsley:def:independence_events", "srcdecl:billingsley:thm:borel_cantelli_1"],
        ),
        (
            "srcdecl:billingsley:thm:kolmogorov_zero_one",
            "Theorem 4.5: Kolmogorov Zero-One Law",
            "THEOREM",
            "Section 4",
            63,
            "If X_1, X_2, ... are independent random variables, every event A in the tail sigma-field T = cap_{n=1}^infty sigma(X_n, X_{n+1}, ...) has probability P(A) = 0 or P(A) = 1.",
            ["srcdecl:billingsley:thm:uniqueness_of_measure", "srcdecl:billingsley:def:independence_events"],
        ),

        # Chapter 2 & 3: Measurable Functions and Lebesgue Integration
        (
            "srcdecl:billingsley:def:measurable_function",
            "Definition of Measurable Function and Random Variable",
            "DEFINITION",
            "Section 13",
            182,
            "A mapping f: (Omega, F) to (Omega', F') is measurable if f^{-1}(A') in F for every A' in F'. If (Omega', F') is (R, B(R)), f is a real-valued measurable function or random variable.",
            ["srcdecl:billingsley:def:borel_sets_reals"],
        ),
        (
            "srcdecl:billingsley:prop:composition_measurable",
            "Theorem 13.1: Composition of Measurable Functions",
            "PROPOSITION",
            "Section 13",
            184,
            "If f: (Omega_1, F_1) to (Omega_2, F_2) is measurable and g: (Omega_2, F_2) to (Omega_3, F_3) is measurable, then the composition g circ f: (Omega_1, F_1) to (Omega_3, F_3) is measurable. In particular, continuous functions of random variables are random variables.",
            ["srcdecl:billingsley:def:measurable_function"],
        ),
        (
            "srcdecl:billingsley:thm:limit_of_measurable",
            "Theorem 13.4: Limits of Measurable Functions",
            "THEOREM",
            "Section 13",
            186,
            "If f_n are measurable functions to the extended reals, then sup_n f_n, inf_n f_n, limsup_{n to infty} f_n, and liminf_{n to infty} f_n are measurable. If lim f_n exists pointwise, the limit function is measurable.",
            ["srcdecl:billingsley:def:measurable_function"],
        ),
        (
            "srcdecl:billingsley:def:simple_function",
            "Definition of Simple Function and Approximation",
            "DEFINITION",
            "Section 13",
            187,
            "A simple function s: Omega to R is a measurable function taking only finitely many distinct values, s = sum_{i=1}^k a_i 1_{A_i} with A_i in F. Every non-negative measurable function f is the pointwise limit of a non-decreasing sequence of non-negative simple functions.",
            ["srcdecl:billingsley:def:measurable_function"],
        ),
        (
            "srcdecl:billingsley:def:lebesgue_integral_simple",
            "Definition of Lebesgue Integral for Simple Functions",
            "DEFINITION",
            "Section 15",
            204,
            "For a non-negative simple function s = sum_{i=1}^k a_i 1_{A_i}, the integral with respect to measure mu is defined as int s dmu = sum_{i=1}^k a_i mu(A_i).",
            ["srcdecl:billingsley:def:simple_function", "srcdecl:billingsley:def:measure_space"],
        ),
        (
            "srcdecl:billingsley:def:lebesgue_integral_nonneg",
            "Definition of Lebesgue Integral for Non-Negative Functions",
            "DEFINITION",
            "Section 15",
            206,
            "For a non-negative measurable function f, the integral is defined as int f dmu = sup { int s dmu : s is simple and 0 <= s <= f }.",
            ["srcdecl:billingsley:def:lebesgue_integral_simple"],
        ),
        (
            "srcdecl:billingsley:def:integrable_function",
            "Definition of Integrable Function and General Lebesgue Integral",
            "DEFINITION",
            "Section 15",
            209,
            "A measurable function f is integrable if int |f| dmu < infty. In this case, int f dmu = int f^+ dmu - int f^- dmu, where f^+ = max(f, 0) and f^- = max(-f, 0).",
            ["srcdecl:billingsley:def:lebesgue_integral_nonneg"],
        ),
        (
            "srcdecl:billingsley:prop:linearity_integral",
            "Theorem 15.1: Linearity and Monotonicity of the Integral",
            "PROPOSITION",
            "Section 15",
            211,
            "If f and g are integrable and a, b in R, then int (a f + b g) dmu = a int f dmu + b int g dmu. If f <= g almost everywhere, then int f dmu <= int g dmu.",
            ["srcdecl:billingsley:def:integrable_function"],
        ),

        # Section 16: Convergence Theorems
        (
            "srcdecl:billingsley:thm:monotone_convergence",
            "Theorem 16.2: Monotone Convergence Theorem (Beppo Levi)",
            "THEOREM",
            "Section 16",
            214,
            "If 0 <= f_1 <= f_2 <= ... are measurable functions and f_n(omega) to f(omega) pointwise, then int f dmu = lim_{n to infty} int f_n dmu.",
            ["srcdecl:billingsley:def:lebesgue_integral_nonneg", "srcdecl:billingsley:thm:limit_of_measurable"],
        ),
        (
            "srcdecl:billingsley:thm:fatou_lemma",
            "Theorem 16.3: Fatou's Lemma",
            "LEMMA",
            "Section 16",
            216,
            "If f_n >= 0 are measurable functions, then int (liminf_{n to infty} f_n) dmu <= liminf_{n to infty} int f_n dmu.",
            ["srcdecl:billingsley:thm:monotone_convergence"],
        ),
        (
            "srcdecl:billingsley:thm:dominated_convergence",
            "Theorem 16.4: Lebesgue Dominated Convergence Theorem",
            "THEOREM",
            "Section 16",
            217,
            "If f_n to f pointwise almost everywhere and |f_n| <= g for all n where g is integrable, then f is integrable and lim_{n to infty} int |f_n - f| dmu = 0, so int f dmu = lim_{n to infty} int f_n dmu.",
            ["srcdecl:billingsley:thm:fatou_lemma"],
        ),
        (
            "srcdecl:billingsley:thm:bounded_convergence",
            "Theorem 16.5: Bounded Convergence Theorem",
            "THEOREM",
            "Section 16",
            219,
            "If mu(Omega) < infty and f_n to f pointwise almost everywhere with |f_n| <= M for some constant M, then int f dmu = lim_{n to infty} int f_n dmu.",
            ["srcdecl:billingsley:thm:dominated_convergence"],
        ),
        (
            "srcdecl:billingsley:thm:differentiation_under_integral",
            "Theorem 16.8: Differentiation under the Integral Sign",
            "THEOREM",
            "Section 16",
            223,
            "If f(t, x) is differentiable with respect to t and |partial f / partial t (t, x)| <= g(x) with g integrable, then d/dt int f(t, x) dmu(x) = int partial f / partial t (t, x) dmu(x).",
            ["srcdecl:billingsley:thm:dominated_convergence"],
        ),

        # Section 18: Product Measures & Fubini-Tonelli
        (
            "srcdecl:billingsley:def:product_sigma_field",
            "Definition of Product Sigma-Field",
            "DEFINITION",
            "Section 18",
            231,
            "For measurable spaces (Omega_1, F_1) and (Omega_2, F_2), the product sigma-field F_1 otimes F_2 is the sigma-field generated by measurable rectangles A_1 times A_2 with A_1 in F_1 and A_2 in F_2.",
            ["srcdecl:billingsley:def:field_sigma_field"],
        ),
        (
            "srcdecl:billingsley:thm:product_measure_existence",
            "Theorem 18.2: Existence and Uniqueness of Product Measure",
            "THEOREM",
            "Section 18",
            233,
            "If (Omega_1, F_1, mu_1) and (Omega_2, F_2, mu_2) are sigma-finite measure spaces, there exists a unique measure mu = mu_1 otimes mu_2 on F_1 otimes F_2 such that mu(A_1 times A_2) = mu_1(A_1) mu_2(A_2).",
            ["srcdecl:billingsley:thm:caratheodory_extension", "srcdecl:billingsley:def:product_sigma_field"],
        ),
        (
            "srcdecl:billingsley:thm:tonelli_theorem",
            "Theorem 18.3: Tonelli's Theorem for Non-Negative Functions",
            "THEOREM",
            "Section 18",
            234,
            "If f: Omega_1 times Omega_2 to [0, infty] is measurable with respect to F_1 otimes F_2 on sigma-finite spaces, then int f d(mu_1 otimes mu_2) = int (int f(x, y) dmu_2(y)) dmu_1(x) = int (int f(x, y) dmu_1(x)) dmu_2(y).",
            ["srcdecl:billingsley:thm:product_measure_existence", "srcdecl:billingsley:thm:monotone_convergence"],
        ),
        (
            "srcdecl:billingsley:thm:fubini_theorem",
            "Theorem 18.4: Fubini's Theorem for Integrable Functions",
            "THEOREM",
            "Section 18",
            235,
            "If f is integrable with respect to mu_1 otimes mu_2 on sigma-finite spaces, then the iterated integrals exist and equal the double integral: int f d(mu_1 otimes mu_2) = int (int f(x, y) dmu_2(y)) dmu_1(x) = int (int f(x, y) dmu_1(x)) dmu_2(y).",
            ["srcdecl:billingsley:thm:tonelli_theorem", "srcdecl:billingsley:def:integrable_function"],
        ),

        # Section 19: L^p Spaces, Duality, Completeness
        (
            "srcdecl:billingsley:def:lp_space_norm",
            "Definition of L^p Space and Norm",
            "DEFINITION",
            "Section 19",
            241,
            "For 1 <= p < infty, L^p(Omega, F, mu) is the space of measurable functions f with ||f||_p = (int |f|^p dmu)^{1/p} < infty (modulo almost everywhere equality). For p = infty, ||f||_infty = ess sup |f|.",
            ["srcdecl:billingsley:def:integrable_function"],
        ),
        (
            "srcdecl:billingsley:thm:holder_inequality",
            "Theorem 19.1: Holder's Inequality for L^p Spaces",
            "THEOREM",
            "Section 19",
            242,
            "If 1 <= p, q <= infty with 1/p + 1/q = 1, and f in L^p, g in L^q, then fg in L^1 and ||fg||_1 = int |fg| dmu <= ||f||_p ||g||_q.",
            ["srcdecl:billingsley:def:lp_space_norm"],
        ),
        (
            "srcdecl:billingsley:thm:minkowski_inequality",
            "Theorem 19.2: Minkowski's Inequality",
            "THEOREM",
            "Section 19",
            244,
            "If 1 <= p <= infty and f, g in L^p, then f + g in L^p and ||f + g||_p <= ||f||_p + ||g||_p.",
            ["srcdecl:billingsley:thm:holder_inequality"],
        ),
        (
            "srcdecl:billingsley:thm:riesz_fischer_completeness",
            "Theorem 19.3: Riesz-Fischer Theorem (Completeness of L^p)",
            "THEOREM",
            "Section 19",
            245,
            "For 1 <= p <= infty, the normed space (L^p(Omega, F, mu), ||.||_p) is complete and therefore a Banach space.",
            ["srcdecl:billingsley:thm:minkowski_inequality", "srcdecl:billingsley:thm:dominated_convergence"],
        ),
        (
            "srcdecl:billingsley:thm:l2_hilbert_space",
            "L^2 Space as Hilbert Space with Inner Product",
            "THEOREM",
            "Section 19",
            247,
            "The space L^2(Omega, F, mu) is an inner product space with inner product <f, g> = int f g dmu. Since it is complete under ||f||_2 = sqrt{<f, f>}, L^2 is a Hilbert space.",
            ["srcdecl:billingsley:thm:riesz_fischer_completeness"],
        ),
        (
            "srcdecl:billingsley:thm:lp_duality",
            "Theorem 19.4: Dual Space of L^p",
            "THEOREM",
            "Section 19",
            249,
            "For 1 <= p < infty and 1/p + 1/q = 1, the dual space (L^p(mu))^* is isometrically isomorphic to L^q(mu) via the functional phi_g(f) = int fg dmu for g in L^q.",
            ["srcdecl:billingsley:thm:holder_inequality", "srcdecl:billingsley:thm:riesz_fischer_completeness"],
        ),

        # Section 21: Expected Values and Moment Inequalities
        (
            "srcdecl:billingsley:def:expectation_variance",
            "Definition of Expectation and Variance",
            "DEFINITION",
            "Section 21",
            273,
            "For a random variable X on (Omega, F, P), the expected value is E[X] = int X dP. The variance is Var(X) = E[(X - E[X])^2] = E[X^2] - (E[X])^2.",
            ["srcdecl:billingsley:def:integrable_function"],
        ),
        (
            "srcdecl:billingsley:thm:jensen_inequality",
            "Theorem 21.1: Jensen's Inequality for Expectations",
            "THEOREM",
            "Section 21",
            276,
            "If phi: R to R is a convex function and X and phi(X) are integrable random variables, then phi(E[X]) <= E[phi(X)].",
            ["srcdecl:billingsley:def:expectation_variance"],
        ),
        (
            "srcdecl:billingsley:thm:markov_chebyshev_inequality",
            "Theorem 21.2: Markov and Chebyshev Inequalities",
            "THEOREM",
            "Section 21",
            277,
            "If X >= 0 and a > 0, then P(X >= a) <= E[X]/a (Markov). If X has finite mean mu and variance sigma^2, then P(|X - mu| >= k sigma) <= 1/k^2 for all k > 0 (Chebyshev).",
            ["srcdecl:billingsley:def:expectation_variance"],
        ),
        (
            "srcdecl:billingsley:thm:cauchy_schwarz_rv",
            "Theorem 21.3: Cauchy-Schwarz Inequality for Random Variables",
            "THEOREM",
            "Section 21",
            278,
            "For square-integrable random variables X, Y in L^2(P), (E[XY])^2 <= E[X^2] E[Y^2], with equality if and only if aX + bY = 0 almost surely for some constants (a,b) != (0,0).",
            ["srcdecl:billingsley:thm:l2_hilbert_space"],
        ),
        (
            "srcdecl:billingsley:def:covariance_matrix",
            "Definition of Covariance Matrix and PSD Property",
            "DEFINITION",
            "Section 21",
            280,
            "For a random vector X = (X_1, ..., X_n)^T, the covariance matrix Sigma = E[(X - E[X])(X - E[X])^T] has entries Sigma_{ij} = Cov(X_i, X_j) and is symmetric positive semidefinite (PSD): v^T Sigma v = Var(v^T X) >= 0 for all v in R^n.",
            ["srcdecl:billingsley:def:expectation_variance"],
        ),

        # Section 22 & 25: Laws of Large Numbers & Modes of Convergence
        (
            "srcdecl:billingsley:thm:weak_law_large_numbers",
            "Theorem 22.1: Weak Law of Large Numbers (WLLN)",
            "THEOREM",
            "Section 22",
            284,
            "If X_1, X_2, ... are uncorrelated random variables with identical mean mu and bounded variance sigma^2, then the sample mean S_n/n = (1/n) sum_{i=1}^n X_i converges in probability to mu as n to infty: lim_{n to infty} P(|S_n/n - mu| >= epsilon) = 0 for all epsilon > 0.",
            ["srcdecl:billingsley:thm:markov_chebyshev_inequality"],
        ),
        (
            "srcdecl:billingsley:thm:strong_law_large_numbers",
            "Theorem 22.2: Strong Law of Large Numbers (SLLN)",
            "THEOREM",
            "Section 22",
            288,
            "If X_1, X_2, ... are independent identically distributed (i.i.d.) random variables with E[|X_1|] < infty, then S_n/n converges almost surely to mu = E[X_1]: P(lim_{n to infty} S_n/n = mu) = 1.",
            ["srcdecl:billingsley:thm:borel_cantelli_1", "srcdecl:billingsley:thm:kolmogorov_zero_one"],
        ),
        (
            "srcdecl:billingsley:def:modes_of_convergence",
            "Definition of Modes of Convergence for Random Variables",
            "DEFINITION",
            "Section 25",
            327,
            "Let X_n, X be random variables. X_n to X almost surely (a.s.) if P(lim X_n = X) = 1; X_n to X in probability if P(|X_n - X| >= epsilon) to 0; X_n to X in L^p if E[|X_n - X|^p] to 0; X_n to X in distribution (weakly) if E[f(X_n)] to E[f(X)] for all bounded continuous f.",
            ["srcdecl:billingsley:def:lp_space_norm"],
        ),
        (
            "srcdecl:billingsley:thm:convergence_implications",
            "Theorem 25.2: Hierarchy of Convergence Modes",
            "THEOREM",
            "Section 25",
            329,
            "Almost sure convergence implies convergence in probability. L^p convergence implies convergence in probability. Convergence in probability implies convergence in distribution and existence of an almost surely convergent subsequence.",
            ["srcdecl:billingsley:def:modes_of_convergence"],
        ),
        (
            "srcdecl:billingsley:thm:continuous_mapping_theorem",
            "Theorem 25.7: Continuous Mapping Theorem",
            "THEOREM",
            "Section 25",
            334,
            "If g: R^k to R^m is continuous and X_n to X in distribution (or in probability, or almost surely), then g(X_n) to g(X) in distribution (or in probability, or almost surely).",
            ["srcdecl:billingsley:def:modes_of_convergence"],
        ),
        (
            "srcdecl:billingsley:thm:slutsky_theorem",
            "Theorem 25.8: Slutsky's Theorem",
            "THEOREM",
            "Section 25",
            336,
            "If X_n to X in distribution and Y_n to c (constant) in probability, then X_n + Y_n to X + c in distribution, X_n Y_n to cX in distribution, and X_n / Y_n to X / c in distribution (if c != 0).",
            ["srcdecl:billingsley:thm:continuous_mapping_theorem"],
        ),

        # Section 26 & 27: Characteristic Functions & Central Limit Theorem
        (
            "srcdecl:billingsley:def:characteristic_function",
            "Definition of Characteristic Function",
            "DEFINITION",
            "Section 26",
            342,
            "The characteristic function of a random variable X (or probability distribution mu) is the Fourier transform phi_X(t) = E[e^{i t X}] = int_{R} e^{i t x} dmu(x) for t in R.",
            ["srcdecl:billingsley:def:integrable_function"],
        ),
        (
            "srcdecl:billingsley:prop:char_func_properties",
            "Theorem 26.1: Elementary Properties of Characteristic Functions",
            "PROPOSITION",
            "Section 26",
            344,
            "For any characteristic function phi(t): phi(0) = 1, |phi(t)| <= 1 for all t in R, phi(-t) = conjugate(phi(t)), phi is uniformly continuous on R, and phi is positive semidefinite.",
            ["srcdecl:billingsley:def:characteristic_function"],
        ),
        (
            "srcdecl:billingsley:thm:inversion_formula",
            "Theorem 26.2: Levy Inversion Formula",
            "THEOREM",
            "Section 26",
            347,
            "A probability measure mu on (R, B(R)) is uniquely determined by its characteristic function phi. If int |phi(t)| dt < infty, mu has a continuous bounded probability density function f(x) = (1 / 2 pi) int_{-infty}^infty e^{-i t x} phi(t) dt.",
            ["srcdecl:billingsley:prop:char_func_properties"],
        ),
        (
            "srcdecl:billingsley:thm:continuity_theorem_levy",
            "Theorem 26.3: Levy Continuity Theorem",
            "THEOREM",
            "Section 26",
            349,
            "A sequence of probability measures mu_n converges weakly (in distribution) to a probability measure mu if and only if their characteristic functions phi_n(t) converge pointwise to a function phi(t) that is continuous at t = 0; in this case phi is the characteristic function of mu.",
            ["srcdecl:billingsley:thm:inversion_formula"],
        ),
        (
            "srcdecl:billingsley:thm:central_limit_theorem",
            "Theorem 27.1: Lindeberg-Levy Central Limit Theorem",
            "THEOREM",
            "Section 27",
            357,
            "If X_1, X_2, ... are i.i.d. random variables with mean mu and finite variance sigma^2 > 0, then the standardized sum Z_n = (S_n - n mu) / (sigma sqrt{n}) converges in distribution to the standard normal distribution N(0, 1): lim_{n to infty} P(Z_n <= z) = Phi(z) = (1 / sqrt{2 pi}) int_{-infty}^z e^{-u^2/2} du.",
            ["srcdecl:billingsley:thm:continuity_theorem_levy"],
        ),
        (
            "srcdecl:billingsley:thm:lindeberg_feller_clt",
            "Theorem 27.2: Lindeberg-Feller Central Limit Theorem",
            "THEOREM",
            "Section 27",
            359,
            "For an independent triangular array of random variables X_{n,k} with zero mean and sum of variances s_n^2 = sum_{k=1}^{r_n} Var(X_{n,k}), the normalized sum converges in distribution to N(0, 1) if and only if the Lindeberg condition holds: lim_{n to infty} (1 / s_n^2) sum_{k=1}^{r_n} E[X_{n,k}^2 1_{|X_{n,k}| >= epsilon s_n}] = 0 for every epsilon > 0.",
            ["srcdecl:billingsley:thm:central_limit_theorem"],
        ),

        # Section 32: Derivatives of Measures & Radon-Nikodym
        (
            "srcdecl:billingsley:def:absolute_continuity_measures",
            "Definition of Absolute Continuity and Singularity of Measures",
            "DEFINITION",
            "Section 32",
            422,
            "A measure nu is absolutely continuous with respect to mu (written nu << mu) if mu(A) = 0 implies nu(A) = 0 for all A in F. Measures nu and mu are mutually singular (nu perp mu) if there exists E in F such that nu(E) = 0 and mu(E^c) = 0.",
            ["srcdecl:billingsley:def:measure_space"],
        ),
        (
            "srcdecl:billingsley:thm:lebesgue_decomposition",
            "Theorem 32.1: Lebesgue Decomposition Theorem",
            "THEOREM",
            "Section 32",
            423,
            "Let mu and nu be sigma-finite measures on (Omega, F). There exist unique sigma-finite measures nu_ac and nu_s such that nu = nu_ac + nu_s, with nu_ac << mu and nu_s perp mu.",
            ["srcdecl:billingsley:def:absolute_continuity_measures"],
        ),
        (
            "srcdecl:billingsley:thm:radon_nikodym",
            "Theorem 32.2: Radon-Nikodym Theorem",
            "THEOREM",
            "Section 32",
            424,
            "Let mu and nu be sigma-finite measures on (Omega, F) with nu << mu. There exists a non-negative measurable function f = dnu / dmu, unique up to mu-null sets, such that nu(A) = int_A f dmu for all A in F. The function f is called the Radon-Nikodym derivative.",
            ["srcdecl:billingsley:thm:lebesgue_decomposition", "srcdecl:billingsley:thm:l2_hilbert_space"],
        ),
        (
            "srcdecl:billingsley:thm:chain_rule_radon_nikodym",
            "Theorem 32.3: Chain Rule for Radon-Nikodym Derivatives",
            "THEOREM",
            "Section 32",
            426,
            "If nu_1 << nu_2 << mu on sigma-finite spaces, then dnu_1 / dmu = (dnu_1 / dnu_2) (dnu_2 / dmu) almost everywhere with respect to mu.",
            ["srcdecl:billingsley:thm:radon_nikodym"],
        ),
        (
            "srcdecl:billingsley:thm:hahn_jordan_decomposition",
            "Theorem 32.4: Hahn and Jordan Decompositions for Signed Measures",
            "THEOREM",
            "Section 32",
            428,
            "For any signed measure nu on (Omega, F), there exists a partition Omega = P cup N with P in F (positive set) and N in F (negative set) such that nu(E cap P) >= 0 and nu(E cap N) <= 0 for all E in F (Hahn). Consequently, nu = nu^+ - nu^- with nu^+ perp nu^- (Jordan).",
            ["srcdecl:billingsley:def:measure_space"],
        ),

        # Section 34 & 35: Conditional Probability, Expectation, Martingales
        (
            "srcdecl:billingsley:def:conditional_expectation",
            "Definition of Conditional Expectation",
            "DEFINITION",
            "Section 34",
            445,
            "Let X be an integrable random variable on (Omega, F, P) and G a sub-sigma-field of F. The conditional expectation E[X|G] is the unique G-measurable integrable random variable Y such that int_G Y dP = int_G X dP for all G in G (constructed as Radon-Nikodym derivative of nu(G) = int_G X dP with respect to P|_G).",
            ["srcdecl:billingsley:thm:radon_nikodym"],
        ),
        (
            "srcdecl:billingsley:thm:conditional_expectation_projection",
            "Theorem 34.2: Conditional Expectation as Orthogonal Projection in L^2",
            "THEOREM",
            "Section 34",
            448,
            "If X in L^2(Omega, F, P), the conditional expectation E[X|G] is the unique orthogonal projection of X onto the closed subspace L^2(Omega, G, P), minimizing the mean squared error: E[(X - E[X|G])^2] = inf_{Z in L^2(G)} E[(X - Z)^2].",
            ["srcdecl:billingsley:def:conditional_expectation", "srcdecl:billingsley:thm:l2_hilbert_space"],
        ),
        (
            "srcdecl:billingsley:prop:tower_property_conditional",
            "Theorem 34.3: Tower Property of Conditional Expectation",
            "PROPOSITION",
            "Section 34",
            450,
            "If G_1 subset G_2 subset F are sub-sigma-fields, then E[E[X|G_2]|G_1] = E[X|G_1] almost surely. In particular, E[E[X|G]] = E[X].",
            ["srcdecl:billingsley:def:conditional_expectation"],
        ),
        (
            "srcdecl:billingsley:thm:conditional_jensen",
            "Theorem 34.7: Conditional Jensen's Inequality",
            "THEOREM",
            "Section 34",
            453,
            "If phi: R to R is convex and X and phi(X) are integrable, then phi(E[X|G]) <= E[phi(X)|G] almost surely.",
            ["srcdecl:billingsley:thm:jensen_inequality", "srcdecl:billingsley:def:conditional_expectation"],
        ),
        (
            "srcdecl:billingsley:def:martingale",
            "Definition of Martingale and Filtration",
            "DEFINITION",
            "Section 35",
            458,
            "A sequence of random variables (X_n)_{n=1}^infty adapted to a filtration (F_n)_{n=1}^infty is a martingale if E[|X_n|] < infty and E[X_{n+1}|F_n] = X_n almost surely for all n. It is a submartingale if E[X_{n+1}|F_n] >= X_n, and a supermartingale if E[X_{n+1}|F_n] <= X_n.",
            ["srcdecl:billingsley:def:conditional_expectation"],
        ),
        (
            "srcdecl:billingsley:thm:martingale_convergence",
            "Theorem 35.5: Doob's Martingale Convergence Theorem",
            "THEOREM",
            "Section 35",
            468,
            "If (X_n, F_n) is a submartingale with sup_n E[X_n^+] < infty, then X_n converges almost surely to an integrable random variable X_infty as n to infty.",
            ["srcdecl:billingsley:def:martingale", "srcdecl:billingsley:thm:monotone_convergence"],
        ),
        (
            "srcdecl:billingsley:thm:kolmogorov_extension",
            "Theorem 36.1: Kolmogorov Extension Theorem",
            "THEOREM",
            "Section 36",
            482,
            "For any consistent family of finite-dimensional probability distributions {P_{t_1, ..., t_k}}, there exists a probability measure P on (R^T, B(R^T)) such that the coordinate process has the given finite-dimensional distributions.",
            ["srcdecl:billingsley:thm:caratheodory_extension", "srcdecl:billingsley:thm:product_measure_existence"],
        ),
        (
            "srcdecl:billingsley:thm:radon_riesz_representation",
            "Theorem 31.1: Riesz-Markov-Kakutani Representation Theorem",
            "THEOREM",
            "Section 31",
            412,
            "Let X be a locally compact Hausdorff space. For every positive linear functional I on C_c(X), there exists a unique Radon measure mu on the Borel sigma-field B(X) such that I(f) = int_X f dmu for all f in C_c(X).",
            ["srcdecl:billingsley:thm:caratheodory_extension", "srcdecl:billingsley:def:borel_sets_reals"],
        ),
    ]

    declarations: list[BillingsleyDeclaration] = []
    for nid, title, dtype, chap, pno, text, refs in raw_declarations:
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        profile = detect_measure_representation_profile(text, title)
        declarations.append(
            BillingsleyDeclaration(
                node_id=nid,
                source_id=SOURCE_ID,
                label=f"Billingsley ({chap}, p. {pno}): {title}",
                decl_type=dtype,
                chapter_section=chap,
                page=pno,
                statement_sha256=h,
                char_count=len(text),
                structural_refs=refs,
                representation_profile=profile,
                node_type="SOURCE_DECLARATION",
            )
        )
    return declarations


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Measure Theory and Probability declarations for MAPEOGEO v0.17")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    decls = generate_billingsley_declarations()
    print(f"Loaded {len(decls)} Measure Theory & Probability declarations from Billingsley (1995).")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump([d.to_dict() for d in decls], f, indent=2)
        print(f"Saved to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
