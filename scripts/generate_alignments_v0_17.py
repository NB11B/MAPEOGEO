#!/usr/bin/env python3
"""Generate curated cross-source alignments for MAPEOGEO v0.17 Measure, Integration & Probability Expansion."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# New canonical objects for Measure Theory & Probability (Domain 6)
MEASURE_CANONICAL_OBJECTS = [
    {
        "id": "canonical:measure:sigma_algebra",
        "name": "Sigma-Algebra / Sigma-Field",
        "domain": "Measure Theory & Probability",
        "description": "Collection of subsets of a set closed under complementation and countable unions",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:field_sigma_field", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:37_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:borel_sigma_algebra",
        "name": "Borel Sigma-Algebra",
        "domain": "Measure Theory & Probability",
        "description": "Smallest sigma-algebra containing all open sets of a topological space",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:borel_sets_reals", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:37_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:measure_space",
        "name": "Measure Space & Probability Space",
        "domain": "Measure Theory & Probability",
        "description": "Triple (Omega, F, mu) of a set, sigma-algebra, and non-negative countably additive measure",
        "representation_kinds": ["abstract", "geometric", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:measure_space", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:continuity_of_measure", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:37_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:caratheodory_extension",
        "name": "Caratheodory Extension Theorem",
        "domain": "Measure Theory & Probability",
        "description": "Extension of a pre-measure on an algebra to a unique complete measure on the generated sigma-algebra",
        "representation_kinds": ["abstract", "geometric", "formal"],
        "alignments": [
            {"source": "srcdecl:billingsley:thm:caratheodory_extension", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:dynkin_pi_lambda", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:uniqueness_of_measure", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:measure:measurable_function",
        "name": "Measurable Function / Random Variable",
        "domain": "Measure Theory & Probability",
        "description": "Mapping between measurable spaces whose preimages of measurable sets are measurable",
        "representation_kinds": ["abstract", "algebraic", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:measurable_function", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:prop:composition_measurable", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:limit_of_measurable", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:38_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:simple_function_approximation",
        "name": "Simple Function Approximation",
        "domain": "Measure Theory & Probability",
        "description": "Pointwise monotone approximation of non-negative measurable functions by finite linear combinations of indicator functions",
        "representation_kinds": ["abstract", "algebraic", "computational"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:simple_function", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:2_2", "corpus": "AXLER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:axler:definition:2_4", "corpus": "AXLER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:vmls:section:1_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:lebesgue_integral",
        "name": "Lebesgue Integral",
        "domain": "Measure Theory & Probability",
        "description": "Integral of a measurable function constructed via suprema of simple functions and positive/negative decomposition",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:lebesgue_integral_simple", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:def:lebesgue_integral_nonneg", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:def:integrable_function", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:prop:linearity_integral", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:38_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:monotone_convergence_theorem",
        "name": "Monotone Convergence Theorem (Beppo Levi)",
        "domain": "Measure Theory & Probability",
        "description": "Interchange of integral and limit for non-decreasing sequences of non-negative measurable functions",
        "representation_kinds": ["abstract", "computational"],
        "alignments": [
            {"source": "srcdecl:billingsley:thm:monotone_convergence", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:37_62", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:fatou_lemma",
        "name": "Fatou's Lemma",
        "domain": "Measure Theory & Probability",
        "description": "Inequality relating integral of liminf to liminf of integrals for non-negative functions",
        "representation_kinds": ["abstract", "algebraic"],
        "alignments": [
            {"source": "srcdecl:billingsley:thm:fatou_lemma", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:monotone_convergence", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:measure:dominated_convergence_theorem",
        "name": "Lebesgue Dominated Convergence Theorem",
        "domain": "Measure Theory & Probability",
        "description": "Interchange of limit and integral under pointwise almost everywhere convergence bounded by an integrable dominant",
        "representation_kinds": ["abstract", "algebraic", "computational"],
        "alignments": [
            {"source": "srcdecl:billingsley:thm:dominated_convergence", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:bounded_convergence", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:differentiation_under_integral", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:37_63", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:product_measure_fubini_tonelli",
        "name": "Product Measure and Fubini-Tonelli Theorems",
        "domain": "Measure Theory & Probability",
        "description": "Product sigma-algebra, existence of product measure, and reduction of multiple integrals to iterated integrals",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:product_sigma_field", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:product_measure_existence", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:tonelli_theorem", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:fubini_theorem", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:37_17", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:lp_banach_space",
        "name": "L^p Space (Lebesgue Space)",
        "domain": "Measure Theory & Probability",
        "description": "Complete normed function space of p-integrable functions with ||f||_p = (int |f|^p dmu)^{1/p}",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:lp_space_norm", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:riesz_fischer_completeness", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:37_16", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:6_7", "corpus": "AXLER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:vmls:section:3_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:holder_minkowski_inequalities",
        "name": "Holder's and Minkowski's Inequalities",
        "domain": "Measure Theory & Probability",
        "description": "Fundamental norm inequalities ||fg||_1 <= ||f||_p ||g||_q and ||f+g||_p <= ||f||_p + ||g||_p on L^p",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:billingsley:thm:holder_inequality", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:minkowski_inequality", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:9_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_14", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:l2_hilbert_space",
        "name": "L^2 Space as Hilbert Space",
        "domain": "Measure Theory & Probability",
        "description": "Square-integrable function space with inner product <f, g> = int f g dmu and complete geometric structure",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:billingsley:thm:l2_hilbert_space", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:cauchy_schwarz_rv", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:48_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:48_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:6_4", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_48", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_4", "corpus": "VMLS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:12_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:lp_duality_riesz",
        "name": "L^p Duality and Riesz Representation",
        "domain": "Measure Theory & Probability",
        "description": "Isometric isomorphism (L^p)^* = L^q and representation of continuous linear functionals by integral pairing",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:billingsley:thm:lp_duality", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:radon_riesz_representation", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:48_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_42", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:radon_nikodym_theorem",
        "name": "Radon-Nikodym Theorem & Lebesgue Decomposition",
        "domain": "Measure Theory & Probability",
        "description": "Decomposition of measures into absolutely continuous and singular parts, and existence of density derivative dnu/dmu",
        "representation_kinds": ["abstract", "algebraic", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:absolute_continuity_measures", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:lebesgue_decomposition", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:radon_nikodym", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:chain_rule_radon_nikodym", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:hahn_jordan_decomposition", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:measure:probability_space_and_random_variables",
        "name": "Probability Space and Random Variables",
        "domain": "Measure Theory & Probability",
        "description": "Probability triple (Omega, F, P), random variables as measurable functions, and pushforward distributions",
        "representation_kinds": ["abstract", "geometric", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:measure_space", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:def:measurable_function", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:borel_cantelli_1", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:borel_cantelli_2", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:kolmogorov_zero_one", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:1_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:expectation_variance_moments",
        "name": "Expected Value, Variance, and Moments",
        "domain": "Measure Theory & Probability",
        "description": "Linear expectation operator E[X] = int X dP, variance Var(X) = E[(X-mu)^2], and higher moments",
        "representation_kinds": ["abstract", "algebraic", "computational", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:expectation_variance", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_3", "corpus": "VMLS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:3_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:jensen_inequality",
        "name": "Jensen's Inequality",
        "domain": "Measure Theory & Probability",
        "description": "Fundamental convexity inequality phi(E[X]) <= E[phi(X)] for convex functions phi",
        "representation_kinds": ["abstract", "algebraic", "geometric", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:thm:jensen_inequality", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:3_1", "corpus": "CVX", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:markov_chebyshev_concentration",
        "name": "Markov and Chebyshev Concentration Inequalities",
        "domain": "Measure Theory & Probability",
        "description": "Tail probability bounds P(X >= a) <= E[X]/a and P(|X-mu| >= k sigma) <= 1/k^2",
        "representation_kinds": ["abstract", "algebraic", "computational", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:thm:markov_chebyshev_inequality", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_3", "corpus": "VMLS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:7_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:covariance_matrix_psd",
        "name": "Covariance Matrix and Positive Semidefinite Geometry",
        "domain": "Measure Theory & Probability",
        "description": "Covariance matrix Sigma = E[(X-mu)(X-mu)^T] and its symmetric positive semidefinite property",
        "representation_kinds": ["algebraic", "geometric", "computational", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:covariance_matrix", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:15_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:7_1", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:8_3", "corpus": "VMLS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:2_2", "corpus": "CVX", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:measure:laws_of_large_numbers",
        "name": "Laws of Large Numbers (Weak and Strong)",
        "domain": "Measure Theory & Probability",
        "description": "Convergence in probability (WLLN) and almost sure convergence (SLLN) of sample means to expected value",
        "representation_kinds": ["abstract", "computational", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:thm:weak_law_large_numbers", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:strong_law_large_numbers", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_3", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:modes_of_stochastic_convergence",
        "name": "Modes of Stochastic Convergence",
        "domain": "Measure Theory & Probability",
        "description": "Hierarchy and relations among almost sure, in probability, in L^p, and weak (in distribution) convergence",
        "representation_kinds": ["abstract", "computational"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:modes_of_convergence", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:convergence_implications", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:continuous_mapping_theorem", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:slutsky_theorem", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:37_13", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:characteristic_functions_fourier",
        "name": "Characteristic Functions and Fourier Transforms",
        "domain": "Measure Theory & Probability",
        "description": "Fourier transform phi_X(t) = E[e^{itX}], inversion theorem, and Levy's continuity theorem",
        "representation_kinds": ["abstract", "algebraic", "computational"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:characteristic_function", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:prop:char_func_properties", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:inversion_formula", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:continuity_theorem_levy", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:measure:central_limit_theorem",
        "name": "Central Limit Theorem (Lindeberg-Levy & Lindeberg-Feller)",
        "domain": "Measure Theory & Probability",
        "description": "Universal weak convergence of standardized sums of independent random variables to standard Gaussian distribution",
        "representation_kinds": ["abstract", "algebraic", "computational", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:thm:central_limit_theorem", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:lindeberg_feller_clt", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_3", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:conditional_expectation_projection",
        "name": "Conditional Expectation & Minimum Mean Squared Error Projection",
        "domain": "Measure Theory & Probability",
        "description": "Conditional expectation E[X|G] as Radon-Nikodym derivative and orthogonal projection in L^2",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:conditional_expectation", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:conditional_expectation_projection", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:prop:tower_property_conditional", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:conditional_jensen", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:48_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_48", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:12_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:8_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:measure:martingales_and_convergence",
        "name": "Martingales and Doob's Convergence Theorem",
        "domain": "Measure Theory & Probability",
        "description": "Adapted stochastic processes with constant conditional expectation, and almost sure convergence under boundedness",
        "representation_kinds": ["abstract", "algebraic", "computational", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:def:martingale", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:martingale_convergence", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:measure:stochastic_process_kolmogorov",
        "name": "Stochastic Processes and Kolmogorov Extension Theorem",
        "domain": "Measure Theory & Probability",
        "description": "Construction of probability measures on infinite-dimensional product spaces from consistent finite-dimensional distributions",
        "representation_kinds": ["abstract", "geometric", "applied"],
        "alignments": [
            {"source": "srcdecl:billingsley:thm:kolmogorov_extension", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:product_measure_existence", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"}
        ]
    },
]


def load_v0_16_canonical_objects() -> list[dict]:
    v0_16_file = ROOT / "formal" / "cross_source_alignments_v0_16.json"
    data = json.loads(v0_16_file.read_text(encoding="utf-8"))
    return data.get("canonical_objects", [])


def merge_and_generate_v0_17_alignments() -> dict:
    prev_objects = load_v0_16_canonical_objects()
    by_id = {co["id"]: co for co in prev_objects}

    # Add new measure canonical objects
    for mco in MEASURE_CANONICAL_OBJECTS:
        if mco["id"] in by_id:
            # merge alignments
            existing = by_id[mco["id"]]
            existing_sources = {al["source"] for al in existing["alignments"]}
            for al in mco["alignments"]:
                if al["source"] not in existing_sources:
                    existing["alignments"].append(al)
        else:
            by_id[mco["id"]] = mco

    all_canonical = list(by_id.values())
    return {
        "schema_version": "v0.17",
        "description": "Curated Cross-Source Alignments spanning Gallier (S_A), Axler (S_B), VMLS (S_C), CVX (S_D), and Billingsley (S_E)",
        "total_canonical_objects": len(all_canonical),
        "canonical_objects": all_canonical,
    }


def main() -> int:
    out_path = ROOT / "formal" / "cross_source_alignments_v0_17.json"
    result = merge_and_generate_v0_17_alignments()
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Generated {len(result['canonical_objects'])} canonical alignments for v0.17 at {out_path}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
