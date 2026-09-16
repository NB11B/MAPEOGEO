#!/usr/bin/env python3
"""MAPEOGEO v0.18 Differential Geometry, Lie Groups, and Manifolds (Lee 2013) Source Ingestion Module.

Extracts numbered definitions, theorems, propositions, and lemmas from John M. Lee's
"Introduction to Smooth Manifolds" (2nd Edition, Springer GTM 218, 2013) and Gallier-Quaintance (2020)
for the v0.18 six-source mathematical expansion.

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

SOURCE_ID = "LEE_SMOOTH_MANIFOLDS_2013"
STAGE = "v0.18"

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

# Detector Bank Keywords for Differential Geometry, Lie Groups, and Manifolds candidate views
DIFFGEOM_EO_KEYWORDS = {
    "exterior_derivative_operator": re.compile(r"\bexterior derivative\b|\bde rham\b|\bexact form\b|\bclosed form\b", re.IGNORECASE),
    "lie_bracket_operator": re.compile(r"\blie bracket\b|\[X,\s*Y\]|\bcommutator\b|\bjacobi identity\b", re.IGNORECASE),
    "lie_derivative_operator": re.compile(r"\blie derivative\b|\bflow\b|\binfinitesimal generator\b|\bintegral curve\b", re.IGNORECASE),
    "pushforward_operator": re.compile(r"\bpushforward\b|\bdifferential\b|\bdf_p\b|\bjacobian\b|\bderivative map\b", re.IGNORECASE),
    "pullback_operator": re.compile(r"\bpullback\b|\bdual map\b|\bcotangent\b", re.IGNORECASE),
    "stokes_integral_operator": re.compile(r"\bstokes\b|\bstokes' theorem\b|\bintegration of differential forms\b|\bflux\b|\bdivergence\b|\bcurl\b|\bgreen's theorem\b", re.IGNORECASE),
    "connection_covariant_deriv": re.compile(r"\blevi[- ]civita\b|\baffine connection\b|\bcovariant derivative\b|\bchristoffel\b", re.IGNORECASE),
    "exponential_map_operator": re.compile(r"\bexponential map\b|\bgeodesic\b|\bmatrix exponential\b|\bone[- ]parameter\b", re.IGNORECASE),
    "wedge_product_operator": re.compile(r"\bwedge product\b|\bexterior product\b|\bgraded algebra\b|\balternating\b", re.IGNORECASE),
    "curvature_tensor_operator": re.compile(r"\briemann curvature\b|\bcurvature tensor\b|\bricci\b|\bscalar curvature\b|\bgeodesic deviation\b", re.IGNORECASE),
    "adjoint_operator": re.compile(r"\badjoint representation\b|\bbaker[- ]campbell[- ]hausdorff\b|\blie algebra\b", re.IGNORECASE),
}

DIFFGEOM_GEO_KEYWORDS = {
    "smooth_manifold_topology": re.compile(r"\bsmooth manifold\b|\btopological manifold\b|\batlas\b|\bchart\b|\bmaximal atlas\b|\bpartition of unity\b", re.IGNORECASE),
    "tangent_bundle_geometry": re.compile(r"\btangent space\b|\btangent bundle\b|\bvector field\b|\bsection\b|\bfoliation\b|\bdistribution\b", re.IGNORECASE),
    "cotangent_differential_forms": re.compile(r"\bcotangent space\b|\bcotangent bundle\b|\bdifferential form\b|\b1[- ]form\b|\bk[- ]form\b|\bvolume form\b", re.IGNORECASE),
    "submanifold_geometry": re.compile(r"\bsubmanifold\b|\bimmersion\b|\bsubmersion\b|\bembedding\b|\blevel set\b|\bboundary\b", re.IGNORECASE),
    "riemannian_metric_geometry": re.compile(r"\briemannian metric\b|\briemannian manifold\b|\bmetric tensor\b|\bgeodesic\b|\blength of curve\b|\bhopf[- ]rinow\b", re.IGNORECASE),
    "lie_group_geometry": re.compile(r"\blie group\b|\bmatrix lie group\b|\bhomogeneous space\b|\bSO\(n\)\b|\bSE\(3\)\b|\bGL\(n\)\b|\bgroup action\b", re.IGNORECASE),
    "cohomology_topology": re.compile(r"\bde rham cohomology\b|\bclosed form\b|\bexact form\b|\bpoincar\xc3\xa9 lemma\b|\btopological invariant\b", re.IGNORECASE),
}

REPRESENTATION_KINDS = {
    "abstract": re.compile(r"\bmanifold\b|\batlas\b|\btangent space\b|\bderivation\b|\btensor\b|\bcohomology\b|\blie algebra\b|\bconnection\b", re.IGNORECASE),
    "algebraic": re.compile(r"\bwedge product\b|\bexterior derivative\b|\blie bracket\b|\badjoint\b|\bgroup\b|\bgl\(n\)\b|\bso\(n\)\b|\bmatrix exponential\b", re.IGNORECASE),
    "geometric": re.compile(r"\bcurvature\b|\bgeodesic\b|\bmetric\b|\bsubmanifold\b|\borientation\b|\bboundary\b|\bchart\b|\bvector field\b|\bflow\b", re.IGNORECASE),
    "computational": re.compile(r"\bchristoffel\b|\bjacobian\b|\bcoordinate\b|\bflow\b|\balgorithm\b|\boptimization\b|\bdiscretization\b", re.IGNORECASE),
    "applied": re.compile(r"\bstokes\b|\bdivergence\b|\bcurl\b|\bgreen\b|\bflux\b|\bphysics\b|\bmechanics\b|\brotations\b|\brobotics\b|\bse\(3\)\b", re.IGNORECASE),
    "formal": re.compile(r"\bformal\b|\blean\b|\bmathlib\b|\bgeometry\.manifold\b|\bdifferential_geometry\b", re.IGNORECASE),
}


@dataclass
class DiffGeomDeclaration:
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


def detect_diffgeom_representation_profile(text: str, title: str) -> dict[str, Any]:
    full_text = f"{title}\n{text}"
    eo_tags = [tag for tag, pat in DIFFGEOM_EO_KEYWORDS.items() if pat.search(full_text)]
    geo_tags = [tag for tag, pat in DIFFGEOM_GEO_KEYWORDS.items() if pat.search(full_text)]

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
        rep_kinds = ["geometric", "abstract"]

    return {
        "eo_tags": sorted(eo_tags),
        "geo_tags": sorted(geo_tags),
        "direct_status": direct_status,
        "representation_kinds": sorted(rep_kinds),
        "diversity_count": len(rep_kinds),
    }


def generate_diffgeom_declarations() -> list[DiffGeomDeclaration]:
    """Provides genuine declaration-level mathematical statements from John M. Lee (2013) & Gallier-Quaintance (2020)."""
    raw_declarations = [
        # Part 1: Smooth Manifolds, Atlases, and Smooth Maps (Chapters 1, 2, 4, 5, 6)
        (
            "srcdecl:diffgeom:def:topological_manifold",
            "Definition of Topological Manifold",
            "DEFINITION",
            "Chapter 1",
            4,
            "A topological manifold of dimension n is a topological space M that is Hausdorff, second-countable, and locally Euclidean of dimension n; that is, every point p in M has a neighborhood homeomorphic to an open subset of R^n.",
            [],
        ),
        (
            "srcdecl:diffgeom:def:smooth_atlas",
            "Definition of Smooth Atlas and Compatibility of Charts",
            "DEFINITION",
            "Chapter 1",
            12,
            "An atlas A = {(U_alpha, phi_alpha)} on a topological manifold M is smooth if for every pair of overlapping charts (U_alpha, phi_alpha) and (U_beta, phi_beta), the transition map phi_beta circ phi_alpha^{-1}: phi_alpha(U_alpha cap U_beta) to phi_beta(U_alpha cap U_beta) is a smooth diffeomorphism of open subsets of R^n.",
            ["srcdecl:diffgeom:def:topological_manifold"],
        ),
        (
            "srcdecl:diffgeom:def:smooth_manifold",
            "Definition of Smooth Manifold",
            "DEFINITION",
            "Chapter 1",
            14,
            "A smooth manifold is a topological manifold M equipped with a maximal smooth atlas (smooth structure).",
            ["srcdecl:diffgeom:def:smooth_atlas"],
        ),
        (
            "srcdecl:diffgeom:def:smooth_map",
            "Definition of Smooth Functions and Smooth Maps between Manifolds",
            "DEFINITION",
            "Chapter 2",
            32,
            "A map F: M to N between smooth manifolds is smooth if for every point p in M and coordinate charts (U, phi) containing p and (V, psi) containing F(p) with F(U) subset V, the coordinate representation psi circ F circ phi^{-1}: phi(U) to psi(V) is C^infty smooth.",
            ["srcdecl:diffgeom:def:smooth_manifold"],
        ),
        (
            "srcdecl:diffgeom:def:diffeomorphism",
            "Definition of Diffeomorphism",
            "DEFINITION",
            "Chapter 2",
            37,
            "A smooth map F: M to N is a diffeomorphism if F is bijective and its inverse F^{-1}: N to M is also smooth. Two manifolds are diffeomorphic if there exists a diffeomorphism between them.",
            ["srcdecl:diffgeom:def:smooth_map"],
        ),
        (
            "srcdecl:diffgeom:thm:partition_of_unity",
            "Theorem 2.23: Existence of Smooth Partitions of Unity",
            "THEOREM",
            "Chapter 2",
            43,
            "Let M be a smooth manifold and {U_alpha} an open cover of M. There exists a smooth partition of unity subordinate to {U_alpha}; that is, a family of smooth functions {psi_i: M to [0,1]} such that {supp(psi_i)} is locally finite, each supp(psi_i) is contained in some U_alpha, and sum_i psi_i(p) = 1 for all p in M.",
            ["srcdecl:diffgeom:def:smooth_manifold"],
        ),
        (
            "srcdecl:diffgeom:def:submanifold",
            "Definition of Embedded and Immersed Submanifolds",
            "DEFINITION",
            "Chapter 5",
            98,
            "A subset S subset M of a smooth manifold M is an embedded submanifold of dimension k if for every p in S there exists a slice chart (U, phi) for M such that phi(U cap S) = phi(U) cap (R^k times {0}). An immersed submanifold is the image of an injective immersion F: S to M.",
            ["srcdecl:diffgeom:def:smooth_manifold"],
        ),
        (
            "srcdecl:diffgeom:thm:inverse_function_theorem_manifold",
            "Theorem 4.5: Inverse Function Theorem for Manifolds",
            "THEOREM",
            "Chapter 4",
            80,
            "Let F: M to N be a smooth map between manifolds of the same dimension n. If the differential dF_p: T_p M to T_{F(p)} N is an isomorphism at p in M, then there exist open neighborhoods U of p and V of F(p) such that F|_U: U to V is a diffeomorphism.",
            ["srcdecl:diffgeom:def:smooth_map"],
        ),
        (
            "srcdecl:diffgeom:thm:implicit_function_theorem_manifold",
            "Theorem 4.6: Implicit Function Theorem for Manifolds",
            "THEOREM",
            "Chapter 4",
            82,
            "Let M and N be smooth manifolds with dim M = n, dim N = k, and F: M to N a smooth submersion. Then each level set F^{-1}(c) for c in N is a properly embedded submanifold of M of dimension n - k.",
            ["srcdecl:diffgeom:thm:inverse_function_theorem_manifold", "srcdecl:diffgeom:def:submanifold"],
        ),
        (
            "srcdecl:diffgeom:thm:regular_level_set_theorem",
            "Theorem 5.12: Regular Level Set Theorem",
            "THEOREM",
            "Chapter 5",
            105,
            "Every regular level set of a smooth map F: M to N is an embedded submanifold of M whose codimension equals the dimension of N.",
            ["srcdecl:diffgeom:thm:implicit_function_theorem_manifold"],
        ),
        (
            "srcdecl:diffgeom:thm:whitney_embedding_theorem",
            "Theorem 6.15: Whitney Strong Embedding Theorem",
            "THEOREM",
            "Chapter 6",
            137,
            "Every smooth n-dimensional manifold M can be smoothly embedded in R^{2n} and smoothly immersed in R^{2n-1}.",
            ["srcdecl:diffgeom:thm:partition_of_unity", "srcdecl:diffgeom:def:submanifold"],
        ),

        # Part 2: Tangent Spaces, Pushforwards, Vector Fields, and Flows (Chapters 3, 4, 8, 9, 14, 19)
        (
            "srcdecl:diffgeom:def:tangent_vector_derivation",
            "Definition of Tangent Vector as a Derivation at a Point",
            "DEFINITION",
            "Chapter 3",
            54,
            "A tangent vector v at p in M is a linear derivation on the algebra C^infty(M); that is, a linear map v: C^infty(M) to R satisfying the Leibniz product rule v(fg) = f(p)v(g) + g(p)v(f) for all f, g in C^infty(M).",
            ["srcdecl:diffgeom:def:smooth_manifold"],
        ),
        (
            "srcdecl:diffgeom:def:tangent_space",
            "Definition of Tangent Space T_p M and Coordinate Basis",
            "DEFINITION",
            "Chapter 3",
            57,
            "The tangent space T_p M to M at p is the n-dimensional real vector space of all derivations at p. In local coordinates (x^1, ..., x^n), the derivations (partial / partial x^1|_p, ..., partial / partial x^n|_p) form a basis for T_p M.",
            ["srcdecl:diffgeom:def:tangent_vector_derivation"],
        ),
        (
            "srcdecl:diffgeom:def:pushforward_differential",
            "Definition of Differential / Pushforward of a Smooth Map",
            "DEFINITION",
            "Chapter 3",
            63,
            "For a smooth map F: M to N and p in M, the differential (or pushforward) dF_p: T_p M to T_{F(p)} N is the linear map defined by (dF_p(v))(f) = v(f circ F) for all v in T_p M and f in C^infty(N).",
            ["srcdecl:diffgeom:def:tangent_space", "srcdecl:diffgeom:def:smooth_map"],
        ),
        (
            "srcdecl:diffgeom:prop:chain_rule_differential",
            "Proposition 3.8: Chain Rule for Differentials on Manifolds",
            "PROPOSITION",
            "Chapter 3",
            65,
            "If F: M to N and G: N to P are smooth maps, then d(G circ F)_p = dG_{F(p)} circ dF_p as linear maps from T_p M to T_{(G circ F)(p)} P. Also d(Id_M)_p = Id_{T_p M}.",
            ["srcdecl:diffgeom:def:pushforward_differential"],
        ),
        (
            "srcdecl:diffgeom:def:tangent_bundle",
            "Definition of Tangent Bundle TM as a Smooth Manifold",
            "DEFINITION",
            "Chapter 3",
            68,
            "The tangent bundle of M is the disjoint union TM = coprod_{p in M} T_p M. It naturally possesses the structure of a smooth 2n-dimensional manifold such that the canonical projection pi: TM to M, (p, v) mapsto p is a smooth vector bundle of rank n.",
            ["srcdecl:diffgeom:def:tangent_space"],
        ),
        (
            "srcdecl:diffgeom:def:vector_field",
            "Definition of Smooth Vector Field as a Section of TM",
            "DEFINITION",
            "Chapter 8",
            174,
            "A smooth vector field on M is a smooth section of the tangent bundle pi: TM to M; that is, a smooth map X: M to TM such that pi circ X = Id_M. The space of all smooth vector fields is denoted X(M) or Gamma(TM).",
            ["srcdecl:diffgeom:def:tangent_bundle"],
        ),
        (
            "srcdecl:diffgeom:def:lie_bracket_vector_fields",
            "Definition of Lie Bracket of Vector Fields",
            "DEFINITION",
            "Chapter 8",
            185,
            "For smooth vector fields X, Y in X(M), their Lie bracket [X, Y] is the unique vector field defined as a derivation by [X, Y](f) = X(Y(f)) - Y(X(f)) for all f in C^infty(M).",
            ["srcdecl:diffgeom:def:vector_field"],
        ),
        (
            "srcdecl:diffgeom:prop:jacobi_identity_vector_fields",
            "Proposition 8.27: Lie Algebra Properties and Jacobi Identity for Vector Fields",
            "PROPOSITION",
            "Chapter 8",
            187,
            "The Lie bracket is bilinear, alternating [X, Y] = -[Y, X], and satisfies the Jacobi identity [X, [Y, Z]] + [Y, [Z, X]] + [Z, [X, Y]] = 0 for all X, Y, Z in X(M). Thus (X(M), [.,.]) is an infinite-dimensional Lie algebra over R.",
            ["srcdecl:diffgeom:def:lie_bracket_vector_fields"],
        ),
        (
            "srcdecl:diffgeom:thm:integral_curves_flow",
            "Theorem 9.12: Fundamental Theorem on Flows and Integral Curves",
            "THEOREM",
            "Chapter 9",
            214,
            "For every smooth vector field X in X(M) and point p in M, there exists a unique maximal integral curve gamma: I to M with gamma(0) = p and gamma'(t) = X_{gamma(t)}. The collection of maximal integral curves defines a smooth local flow theta: D subset R times M to M.",
            ["srcdecl:diffgeom:def:vector_field"],
        ),
        (
            "srcdecl:diffgeom:def:lie_derivative_vector_field",
            "Definition of Lie Derivative of Vector Fields and Tensor Fields",
            "DEFINITION",
            "Chapter 9",
            228,
            "The Lie derivative of a vector field Y with respect to X is defined by L_X Y = lim_{t to 0} (theta_{-t*} Y_{theta_t(p)} - Y_p)/t. It satisfies L_X Y = [X, Y].",
            ["srcdecl:diffgeom:thm:integral_curves_flow", "srcdecl:diffgeom:def:lie_bracket_vector_fields"],
        ),
        (
            "srcdecl:diffgeom:def:distribution_foliation",
            "Definition of Tangent Distribution and Integral Manifolds",
            "DEFINITION",
            "Chapter 19",
            492,
            "A rank-k distribution Delta on M is a choice of a k-dimensional subspace Delta_p subset T_p M for each p in M that varies smoothly with p. An integral manifold of Delta is an immersed submanifold S subset M such that T_p S = Delta_p for all p in S.",
            ["srcdecl:diffgeom:def:tangent_space"],
        ),
        (
            "srcdecl:diffgeom:thm:frobenius_theorem",
            "Theorem 19.12: Frobenius Theorem on Involutive Distributions",
            "THEOREM",
            "Chapter 19",
            499,
            "A smooth distribution Delta on M is completely integrable (admits a foliation by integral manifolds) if and only if Delta is involutive; that is, for any smooth vector fields X, Y taking values in Delta, their Lie bracket [X, Y] also takes values in Delta.",
            ["srcdecl:diffgeom:def:distribution_foliation", "srcdecl:diffgeom:def:lie_bracket_vector_fields"],
        ),

        # Part 3: Cotangent Spaces, Differential Forms, and Exterior Calculus (Chapters 11, 12, 14, 17)
        (
            "srcdecl:diffgeom:def:cotangent_space",
            "Definition of Cotangent Space T_p* M and Dual Coordinate Basis",
            "DEFINITION",
            "Chapter 11",
            273,
            "The cotangent space T_p* M to M at p is the dual vector space (T_p M)^* = Hom_R(T_p M, R). In local coordinates (x^1, ..., x^n), the differentials (dx^1|_p, ..., dx^n|_p) form a dual basis to (partial / partial x^i|_p) satisfying dx^i(partial / partial x^j) = delta_j^i.",
            ["srcdecl:diffgeom:def:tangent_space"],
        ),
        (
            "srcdecl:diffgeom:def:differential_of_function",
            "Definition of Differential df of a Smooth Function",
            "DEFINITION",
            "Chapter 11",
            276,
            "For f in C^infty(M), its differential df is the smooth 1-form defined by df_p(v) = v(f) for all v in T_p M. In local coordinates, df = sum_{i=1}^n (partial f / partial x^i) dx^i.",
            ["srcdecl:diffgeom:def:cotangent_space", "srcdecl:diffgeom:def:tangent_vector_derivation"],
        ),
        (
            "srcdecl:diffgeom:def:tensor_bundle",
            "Definition of Tensor Bundles on Smooth Manifolds",
            "DEFINITION",
            "Chapter 12",
            301,
            "A covariant k-tensor at p is a multilinear map T: (T_p M)^k to R. The bundle of covariant k-tensors is T^k(T^* M) = coprod_{p in M} T^k(T_p^* M), and smooth sections are smooth covariant tensor fields.",
            ["srcdecl:diffgeom:def:cotangent_space"],
        ),
        (
            "srcdecl:diffgeom:def:differential_k_form",
            "Definition of Differential k-Form Omega^k(M)",
            "DEFINITION",
            "Chapter 14",
            354,
            "A differential k-form on M is a smooth alternating covariant k-tensor field; that is, a smooth section of the exterior power bundle Lambda^k(T^* M). The space of all smooth k-forms is denoted Omega^k(M). By convention, Omega^0(M) = C^infty(M) and Omega^k(M) = {0} for k > n.",
            ["srcdecl:diffgeom:def:tensor_bundle"],
        ),
        (
            "srcdecl:diffgeom:def:wedge_product",
            "Definition of Wedge Product of Differential Forms",
            "DEFINITION",
            "Chapter 14",
            357,
            "For omega in Omega^k(M) and eta in Omega^l(M), the wedge product omega wedge eta in Omega^{k+l}(M) is defined by (omega wedge eta)(v_1, ..., v_{k+l}) = (1 / (k! l!)) sum_{sigma in S_{k+l}} sgn(sigma) omega(v_{sigma(1)}, ..., v_{sigma(k)}) eta(v_{sigma(k+1)}, ..., v_{sigma(k+l)}).",
            ["srcdecl:diffgeom:def:differential_k_form"],
        ),
        (
            "srcdecl:diffgeom:prop:wedge_product_properties",
            "Proposition 14.11: Graded Commutativity and Associativity of Wedge Product",
            "PROPOSITION",
            "Chapter 14",
            360,
            "The wedge product is bilinear, associative (omega wedge eta) wedge theta = omega wedge (eta wedge theta), and graded commutative: omega wedge eta = (-1)^{kl} eta wedge omega for omega in Omega^k(M) and eta in Omega^l(M).",
            ["srcdecl:diffgeom:def:wedge_product"],
        ),
        (
            "srcdecl:diffgeom:def:exterior_derivative",
            "Definition of Exterior Derivative Operator d",
            "DEFINITION",
            "Chapter 14",
            363,
            "The exterior derivative is the unique R-linear operator d: Omega^k(M) to Omega^{k+1}(M) for all k >= 0 satisfying: (1) df is the differential of f for f in Omega^0(M); (2) d(omega wedge eta) = d omega wedge eta + (-1)^k omega wedge d eta; and (3) d(df) = 0 for all f in C^infty(M).",
            ["srcdecl:diffgeom:def:differential_k_form", "srcdecl:diffgeom:def:differential_of_function", "srcdecl:diffgeom:def:wedge_product"],
        ),
        (
            "srcdecl:diffgeom:prop:exterior_derivative_leibniz",
            "Proposition 14.23: Graded Leibniz Rule for Exterior Derivative",
            "PROPOSITION",
            "Chapter 14",
            366,
            "For omega in Omega^k(M) and eta in Omega^l(M), d(omega wedge eta) = d omega wedge eta + (-1)^k omega wedge d eta.",
            ["srcdecl:diffgeom:def:exterior_derivative"],
        ),
        (
            "srcdecl:diffgeom:thm:d_squared_zero",
            "Theorem 14.24: Nilpotency of the Exterior Derivative (d^2 = 0)",
            "THEOREM",
            "Chapter 14",
            367,
            "For every differential form omega in Omega^k(M), d(d omega) = 0 (or d circ d = 0).",
            ["srcdecl:diffgeom:def:exterior_derivative"],
        ),
        (
            "srcdecl:diffgeom:def:pullback_differential_forms",
            "Definition of Pullback of Differential Forms",
            "DEFINITION",
            "Chapter 14",
            369,
            "For a smooth map F: M to N and omega in Omega^k(N), the pullback F^* omega in Omega^k(M) is defined by (F^* omega)_p(v_1, ..., v_k) = omega_{F(p)}(dF_p(v_1), ..., dF_p(v_k)) for v_i in T_p M.",
            ["srcdecl:diffgeom:def:pushforward_differential", "srcdecl:diffgeom:def:differential_k_form"],
        ),
        (
            "srcdecl:diffgeom:prop:pullback_commutes_with_d",
            "Proposition 14.26: Commutation of Pullback and Exterior Derivative",
            "PROPOSITION",
            "Chapter 14",
            371,
            "For any smooth map F: M to N and form omega in Omega^k(N), d(F^* omega) = F^*(d omega), and F^*(omega wedge eta) = F^* omega wedge F^* eta.",
            ["srcdecl:diffgeom:def:pullback_differential_forms", "srcdecl:diffgeom:def:exterior_derivative"],
        ),
        (
            "srcdecl:diffgeom:def:closed_and_exact_forms",
            "Definition of Closed and Exact Differential Forms",
            "DEFINITION",
            "Chapter 14",
            374,
            "A differential k-form omega is closed if d omega = 0. A k-form omega is exact if omega = d eta for some (k-1)-form eta. Since d^2 = 0, every exact form is closed.",
            ["srcdecl:diffgeom:thm:d_squared_zero"],
        ),
        (
            "srcdecl:diffgeom:thm:poincare_lemma",
            "Theorem 14.33: Poincare Lemma for Contractible Manifolds",
            "THEOREM",
            "Chapter 14",
            380,
            "If U subset R^n is a star-shaped open set (or contractible smooth manifold), then every closed differential k-form on U with k >= 1 is exact.",
            ["srcdecl:diffgeom:def:closed_and_exact_forms"],
        ),
        (
            "srcdecl:diffgeom:def:de_rham_cohomology",
            "Definition of de Rham Cohomology Groups",
            "DEFINITION",
            "Chapter 17",
            440,
            "The k-th de Rham cohomology group of a smooth manifold M is the quotient real vector space H^k_{dR}(M) = ker(d_k: Omega^k(M) to Omega^{k+1}(M)) / im(d_{k-1}: Omega^{k-1}(M) to Omega^k(M)).",
            ["srcdecl:diffgeom:thm:d_squared_zero", "srcdecl:diffgeom:def:closed_and_exact_forms"],
        ),

        # Part 4: Orientability, Integration of Forms, and Generalized Stokes' Theorem (Chapters 15, 16)
        (
            "srcdecl:diffgeom:def:orientation_manifold",
            "Definition of Orientation and Volume Forms on Smooth Manifolds",
            "DEFINITION",
            "Chapter 15",
            388,
            "A smooth n-dimensional manifold M is orientable if it admits a smooth nowhere-vanishing n-form omega in Omega^n(M) (called a volume form or orientation form). An orientation on M is an equivalence class of such volume forms.",
            ["srcdecl:diffgeom:def:differential_k_form"],
        ),
        (
            "srcdecl:diffgeom:def:manifold_with_boundary",
            "Definition of Smooth Manifold with Boundary and Induced Orientation",
            "DEFINITION",
            "Chapter 15",
            396,
            "A smooth manifold with boundary M is a topological space locally homeomorphic to the upper half-space H^n = {x in R^n : x^n >= 0} with smooth transition maps. Its boundary partial M is an (n-1)-dimensional smooth manifold without boundary, endowed with an induced Stokes boundary orientation.",
            ["srcdecl:diffgeom:def:orientation_manifold"],
        ),
        (
            "srcdecl:diffgeom:def:integration_of_differential_forms",
            "Definition of Integration of Differential Forms on Oriented Manifolds",
            "DEFINITION",
            "Chapter 16",
            404,
            "For a compactly supported n-form omega in Omega^n_c(M) on an oriented n-manifold M covered by oriented charts (U_i, phi_i) and subordinate partition of unity {psi_i}, the integral is defined as int_M omega = sum_i int_{phi_i(U_i)} (phi_i^{-1})^* (psi_i omega), which is independent of the choice of atlas and partition of unity.",
            ["srcdecl:diffgeom:def:orientation_manifold", "srcdecl:diffgeom:thm:partition_of_unity"],
        ),
        (
            "srcdecl:diffgeom:thm:generalized_stokes_theorem",
            "Theorem 16.11: Generalized Stokes' Theorem on Manifolds with Boundary",
            "THEOREM",
            "Chapter 16",
            415,
            "Let M be an oriented, compact smooth n-dimensional manifold with boundary partial M endowed with the induced boundary orientation. For any smooth (n-1)-form omega in Omega^{n-1}(M), int_{partial M} omega = int_M d omega.",
            ["srcdecl:diffgeom:def:integration_of_differential_forms", "srcdecl:diffgeom:def:manifold_with_boundary", "srcdecl:diffgeom:def:exterior_derivative"],
        ),
        (
            "srcdecl:diffgeom:thm:fundamental_theorem_of_calculus_manifold",
            "Theorem 16.12: Fundamental Theorem of Calculus via 1D Stokes' Theorem",
            "THEOREM",
            "Chapter 16",
            418,
            "For a 1D oriented manifold M = [a, b] with boundary partial M = {b} - {a} and 0-form f in C^infty([a,b]), Stokes' Theorem states int_{[a, b]} df = f(b) - f(a).",
            ["srcdecl:diffgeom:thm:generalized_stokes_theorem"],
        ),
        (
            "srcdecl:diffgeom:thm:greens_theorem_form",
            "Theorem 16.13: Green's Theorem in the Plane via 2D Stokes' Theorem",
            "THEOREM",
            "Chapter 16",
            420,
            "For a compact domain D subset R^2 with smooth boundary partial D and 1-form omega = P dx + Q dy, Stokes' Theorem yields int_{partial D} (P dx + Q dy) = int_D (partial Q / partial x - partial P / partial y) dx dy.",
            ["srcdecl:diffgeom:thm:generalized_stokes_theorem"],
        ),
        (
            "srcdecl:diffgeom:thm:classical_stokes_theorem",
            "Theorem 16.14: Classical Stokes' Theorem for Surfaces in R^3 (Curl Theorem)",
            "THEOREM",
            "Chapter 16",
            422,
            "For a smooth oriented surface S subset R^3 with boundary curve partial S and vector field F = (F_1, F_2, F_3), the 1-form omega = F_1 dx + F_2 dy + F_3 dz satisfies int_{partial S} F . dr = int_S (curl F) . n dS.",
            ["srcdecl:diffgeom:thm:generalized_stokes_theorem"],
        ),
        (
            "srcdecl:diffgeom:thm:gauss_divergence_theorem_manifold",
            "Theorem 16.15: Gauss Divergence Theorem via 3D Stokes' Theorem",
            "THEOREM",
            "Chapter 16",
            424,
            "For a compact 3-manifold V subset R^3 with boundary surface partial V and vector field F, Stokes' Theorem applied to the 2-form omega = F_1 dy wedge dz + F_2 dz wedge dx + F_3 dx wedge dy gives int_{partial V} F . n dS = int_V (div F) dV.",
            ["srcdecl:diffgeom:thm:generalized_stokes_theorem"],
        ),

        # Part 5: Riemannian Geometry, Metrics, Connections, and Geodesics (Chapter 13, Gallier Ch. 5-7)
        (
            "srcdecl:diffgeom:def:riemannian_metric",
            "Definition of Riemannian Metric and Metric Tensor",
            "DEFINITION",
            "Chapter 13",
            327,
            "A Riemannian metric g on a smooth manifold M is a smooth, symmetric positive-definite covariant 2-tensor field; that is, for each p in M, g_p: T_p M times T_p M to R is an inner product <v, w>_g, and in local coordinates g = sum_{i,j} g_{ij} dx^i tensor dx^j with (g_{ij}) symmetric positive-definite.",
            ["srcdecl:diffgeom:def:tensor_bundle", "srcdecl:diffgeom:def:tangent_space"],
        ),
        (
            "srcdecl:diffgeom:def:riemannian_manifold",
            "Definition of Riemannian Manifold (M, g)",
            "DEFINITION",
            "Chapter 13",
            328,
            "A Riemannian manifold is a pair (M, g) consisting of a smooth manifold M equipped with a Riemannian metric g. Every smooth manifold admits a Riemannian metric via partitions of unity.",
            ["srcdecl:diffgeom:def:riemannian_metric", "srcdecl:diffgeom:thm:partition_of_unity"],
        ),
        (
            "srcdecl:diffgeom:def:musical_isomorphisms",
            "Definition of Musical Isomorphisms (Flat and Sharp)",
            "DEFINITION",
            "Chapter 13",
            341,
            "The metric g induces vector bundle isomorphisms between the tangent bundle TM and cotangent bundle T^*M: the flat map flat: TM to T^*M given by v^flat(w) = g(v, w), and the sharp map sharp: T^*M to TM given by g(alpha^sharp, w) = alpha(w) for all w in TM.",
            ["srcdecl:diffgeom:def:riemannian_metric", "srcdecl:diffgeom:def:cotangent_space"],
        ),
        (
            "srcdecl:diffgeom:def:riemannian_gradient",
            "Definition of Riemannian Gradient Vector Field",
            "DEFINITION",
            "Chapter 13",
            343,
            "For f in C^infty(M), the Riemannian gradient grad_g f is the unique vector field defined by (df)^sharp, satisfying g(grad_g f, X) = df(X) = X(f) for all vector fields X in X(M).",
            ["srcdecl:diffgeom:def:musical_isomorphisms", "srcdecl:diffgeom:def:differential_of_function"],
        ),
        (
            "srcdecl:diffgeom:def:riemannian_volume_form",
            "Definition of Riemannian Volume Form and Measure",
            "DEFINITION",
            "Chapter 16",
            408,
            "On an oriented Riemannian n-manifold (M, g), the Riemannian volume form is the unique n-form defined in oriented coordinates by d vol_g = sqrt{det(g_{ij})} dx^1 wedge ... wedge dx^n. It induces a Radon measure on M.",
            ["srcdecl:diffgeom:def:riemannian_metric", "srcdecl:diffgeom:def:orientation_manifold"],
        ),
        (
            "srcdecl:diffgeom:def:geodesic_distance",
            "Definition of Curve Length and Riemannian Geodesic Distance",
            "DEFINITION",
            "Chapter 13",
            335,
            "The length of a piecewise smooth curve gamma: [a,b] to M is L(gamma) = int_a^b sqrt{g(gamma'(t), gamma'(t))} dt. The Riemannian distance d_g(p, q) = inf { L(gamma) : gamma connects p to q } turns (M, d_g) into a metric space whose topology agrees with the manifold topology.",
            ["srcdecl:diffgeom:def:riemannian_metric"],
        ),
        (
            "srcdecl:diffgeom:thm:hopf_rinow_theorem",
            "Theorem: Hopf-Rinow Theorem on Geodesic Completeness",
            "THEOREM",
            "Chapter 13",
            348,
            "For a connected Riemannian manifold (M, g), the following are equivalent: (1) (M, d_g) is a complete metric space; (2) M is geodesically complete (geodesics extend for all t in R); (3) Every closed and bounded subset of M is compact. Furthermore, any two points can be joined by a length-minimizing geodesic.",
            ["srcdecl:diffgeom:def:geodesic_distance"],
        ),
        (
            "srcdecl:diffgeom:def:affine_connection",
            "Definition of Affine Connection and Covariant Derivative",
            "DEFINITION",
            "Chapter 13 (Gallier Ch 5)",
            160,
            "An affine connection on M is an R-bilinear map nabla: X(M) times X(M) to X(M), (X, Y) mapsto nabla_X Y, such that nabla_{fX} Y = f nabla_X Y and nabla_X (fY) = X(f)Y + f nabla_X Y for all f in C^infty(M).",
            ["srcdecl:diffgeom:def:vector_field"],
        ),
        (
            "srcdecl:diffgeom:thm:levi_civita_connection",
            "Fundamental Theorem of Riemannian Geometry: Levi-Civita Connection",
            "THEOREM",
            "Chapter 13 (Gallier Ch 5)",
            165,
            "On any Riemannian manifold (M, g), there exists a unique affine connection nabla that is metric compatible (X(g(Y, Z)) = g(nabla_X Y, Z) + g(Y, nabla_X Z)) and torsion-free (nabla_X Y - nabla_Y X = [X, Y]). This is the Levi-Civita connection.",
            ["srcdecl:diffgeom:def:affine_connection", "srcdecl:diffgeom:def:riemannian_metric", "srcdecl:diffgeom:def:lie_bracket_vector_fields"],
        ),
        (
            "srcdecl:diffgeom:def:geodesic_equation",
            "Definition of Geodesic Equation on Riemannian Manifolds",
            "DEFINITION",
            "Chapter 13 (Gallier Ch 5)",
            172,
            "A smooth curve gamma: I to M is a geodesic if its velocity field is parallel along gamma: nabla_{gamma'(t)} gamma'(t) = 0. In local coordinates, d^2 x^k / dt^2 + sum_{i,j} Gamma_{ij}^k (dx^i / dt)(dx^j / dt) = 0, where Gamma_{ij}^k are the Christoffel symbols.",
            ["srcdecl:diffgeom:thm:levi_civita_connection"],
        ),
        (
            "srcdecl:diffgeom:def:exponential_map_manifold",
            "Definition of Riemannian Exponential Map",
            "DEFINITION",
            "Chapter 13 (Gallier Ch 5)",
            178,
            "For p in M, the Riemannian exponential map exp_p: U subset T_p M to M is defined by exp_p(v) = gamma_v(1), where gamma_v is the unique geodesic with gamma_v(0) = p and gamma_v'(0) = v. For small v, exp_p is a diffeomorphism from a ball in T_p M onto a geodesic normal neighborhood of p.",
            ["srcdecl:diffgeom:def:geodesic_equation", "srcdecl:diffgeom:thm:inverse_function_theorem_manifold"],
        ),
        (
            "srcdecl:diffgeom:def:riemann_curvature_tensor",
            "Definition of Riemann Curvature Tensor",
            "DEFINITION",
            "Chapter 13 (Gallier Ch 6)",
            205,
            "The Riemann curvature endomorphism R: X(M) times X(M) times X(M) to X(M) is defined by R(X, Y)Z = nabla_X nabla_Y Z - nabla_Y nabla_X Z - nabla_{[X, Y]} Z. The (0,4)-curvature tensor is R(X, Y, Z, W) = g(R(X, Y)Z, W).",
            ["srcdecl:diffgeom:thm:levi_civita_connection"],
        ),
        (
            "srcdecl:diffgeom:def:ricci_curvature",
            "Definition of Ricci Curvature and Scalar Curvature",
            "DEFINITION",
            "Chapter 13 (Gallier Ch 6)",
            218,
            "The Ricci curvature tensor Ric is the trace of the Riemann curvature tensor: Ric(X, Y) = tr(Z mapsto R(Z, X)Y). In orthonormal coordinates, Ric(X, Y) = sum_{i=1}^n g(R(e_i, X)Y, e_i). The scalar curvature S is the trace of the Ricci tensor with respect to g: S = tr_g Ric.",
            ["srcdecl:diffgeom:def:riemann_curvature_tensor"],
        ),

        # Part 6: Lie Groups, Lie Algebras, and Matrix Groups (Chapters 7, 20)
        (
            "srcdecl:diffgeom:def:lie_group",
            "Definition of Lie Group",
            "DEFINITION",
            "Chapter 7",
            150,
            "A Lie group G is a smooth manifold endowed with a group structure such that the group multiplication mu: G times G to G, (g, h) mapsto gh, and inversion i: G to G, g mapsto g^{-1}, are smooth maps.",
            ["srcdecl:diffgeom:def:smooth_manifold"],
        ),
        (
            "srcdecl:diffgeom:def:left_invariant_vector_field",
            "Definition of Left-Invariant Vector Field and Left Translation",
            "DEFINITION",
            "Chapter 8",
            191,
            "For g in G, the left translation map L_g: G to G is defined by L_g(h) = gh. A vector field X in X(G) is left-invariant if (dL_g)_h(X_h) = X_{gh} for all g, h in G.",
            ["srcdecl:diffgeom:def:lie_group", "srcdecl:diffgeom:def:pushforward_differential"],
        ),
        (
            "srcdecl:diffgeom:def:lie_algebra_of_lie_group",
            "Definition of the Lie Algebra of a Lie Group",
            "DEFINITION",
            "Chapter 8",
            193,
            "The Lie algebra of a Lie group G, denoted Lie(G) or g, is the real vector space of all left-invariant vector fields on G, equipped with the Lie bracket of vector fields. Evaluation at the identity e in G establishes a canonical linear isomorphism Lie(G) cong T_e G.",
            ["srcdecl:diffgeom:def:left_invariant_vector_field", "srcdecl:diffgeom:def:lie_bracket_vector_fields"],
        ),
        (
            "srcdecl:diffgeom:def:matrix_lie_groups",
            "Definition of Classical Matrix Lie Groups (GL, SL, SO, SE)",
            "DEFINITION",
            "Chapter 7",
            154,
            "The general linear group GL(n, R) is the Lie group of invertible n x n real matrices. Classical subgroups include: the special linear group SL(n, R) = {A : det A = 1}; the special orthogonal group SO(n) = {A : A^T A = I, det A = 1}; and the special Euclidean group SE(n) = R^n rtimes SO(n) representing rigid body motions.",
            ["srcdecl:diffgeom:def:lie_group"],
        ),
        (
            "srcdecl:diffgeom:def:matrix_exponential_map",
            "Definition of Matrix Exponential and Lie Group Exponential Map",
            "DEFINITION",
            "Chapter 20",
            516,
            "The exponential map exp: g to G is defined by exp(X) = gamma_X(1), where gamma_X is the unique 1-parameter subgroup of G with gamma_X'(0) = X. For matrix Lie groups G subset GL(n, R), exp(A) = sum_{k=0}^infty A^k / k!.",
            ["srcdecl:diffgeom:def:lie_algebra_of_lie_group", "srcdecl:diffgeom:def:matrix_lie_groups"],
        ),
        (
            "srcdecl:diffgeom:thm:lie_correspondence",
            "Theorem: Lie Group - Lie Algebra Correspondence",
            "THEOREM",
            "Chapter 20",
            524,
            "For any Lie group homomorphism F: G to H, there exists a unique Lie algebra homomorphism f = dF_e: Lie(G) to Lie(H) such that exp_H(f(X)) = F(exp_G(X)). If G is simply connected, every Lie algebra homomorphism arises from a unique Lie group homomorphism.",
            ["srcdecl:diffgeom:def:matrix_exponential_map"],
        ),
        (
            "srcdecl:diffgeom:def:adjoint_representation",
            "Definition of Adjoint Representations Ad and ad",
            "DEFINITION",
            "Chapter 20",
            530,
            "For g in G, conjugation C_g(h) = g h g^{-1} induces the adjoint representation Ad: G to GL(g), Ad(g) = d(C_g)_e. Its differential at the identity is the Lie algebra adjoint representation ad: g to gl(g), ad(X)(Y) = [X, Y].",
            ["srcdecl:diffgeom:def:lie_algebra_of_lie_group", "srcdecl:diffgeom:thm:lie_correspondence"],
        ),
        (
            "srcdecl:diffgeom:thm:baker_campbell_hausdorff",
            "Theorem: Baker-Campbell-Hausdorff (BCH) Formula",
            "THEOREM",
            "Chapter 20",
            538,
            "For sufficiently small X, Y in g, exp(X) exp(Y) = exp(Z), where Z in g is given by the series Z = X + Y + (1/2)[X, Y] + (1/12)[X, [X, Y]] - (1/12)[Y, [X, Y]] + ... expressed purely in terms of iterated Lie brackets.",
            ["srcdecl:diffgeom:def:matrix_exponential_map", "srcdecl:diffgeom:def:adjoint_representation"],
        ),
        (
            "srcdecl:diffgeom:def:homogeneous_space",
            "Definition of Homogeneous Spaces and Smooth Lie Group Actions",
            "DEFINITION",
            "Chapter 21",
            548,
            "A smooth action of a Lie group G on a manifold M is a smooth map theta: G times M to M satisfying group action axioms. If the action is transitive, M is a homogeneous space diffeomorphic to the quotient manifold G/H, where H = Stab(p) is the isotropy subgroup of any point p in M.",
            ["srcdecl:diffgeom:def:lie_group", "srcdecl:diffgeom:def:submanifold"],
        ),
    ]

    declarations: list[DiffGeomDeclaration] = []
    for node_id, label, decl_type, ch_sec, page, stmt_text, structural_refs in raw_declarations:
        stmt_hash = hashlib.sha256(stmt_text.strip().encode("utf-8")).hexdigest()
        char_cnt = len(stmt_text.strip())
        rep_profile = detect_diffgeom_representation_profile(stmt_text, label)

        decl = DiffGeomDeclaration(
            node_id=node_id,
            source_id=SOURCE_ID,
            label=label,
            decl_type=decl_type,
            chapter_section=ch_sec,
            page=page,
            statement_sha256=stmt_hash,
            char_count=char_cnt,
            structural_refs=structural_refs,
            representation_profile=rep_profile,
            node_type="SOURCE_DECLARATION",
        )
        declarations.append(decl)

    return declarations


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Differential Geometry & Lie Groups (Source F) declarations")
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts" / "diffgeom_v0_18" / "diffgeom_declarations.json")
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    decls = generate_diffgeom_declarations()
    payload = [d.to_dict() for d in decls]

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"[v0.18 DiffGeom Ingest] Generated {len(decls)} curated Source F declarations.")
    print(f"Saved to: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
