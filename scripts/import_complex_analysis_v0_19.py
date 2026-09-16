#!/usr/bin/env python3
"""MAPEOGEO v0.19 Complex Analysis, Several Complex Variables & Riemann Surfaces (Ahlfors, Krantz, Conway) Source Ingestion Module.

Extracts numbered definitions, theorems, propositions, and lemmas from Lars Ahlfors'
"Complex Analysis" (3rd Edition, McGraw-Hill, 1979), Steven G. Krantz's "Function Theory
of Several Complex Variables" (AMS, 2001), and John B. Conway's "Functions of One Complex
Variable I & II" (Springer GTM) for the v0.19 mathematical expansion.

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

SOURCE_ID = "AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979"
STAGE = "v0.19"

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

# Detector Bank Keywords for Complex Analysis, SCV, and Riemann Surfaces candidate views
COMPLEX_EO_KEYWORDS = {
    "cauchy_riemann_operator": re.compile(r"\bcauchy[- ]riemann\b|\bdbar\b|\bdel[- ]bar\b|\bpartial_zbar\b|\bpartial f / partial z\b", re.IGNORECASE),
    "cauchy_integral_operator": re.compile(r"\bcauchy('s)? integral formula\b|\bcontour integral\b|\bcauchy('s)? integral theorem\b|\bline integral\b", re.IGNORECASE),
    "residue_calculus_operator": re.compile(r"\bresidue theorem\b|\bresidue\b|\bargument principle\b|\brouche('s)? theorem\b|\bmeromorphic\b", re.IGNORECASE),
    "power_series_laurent": re.compile(r"\bpower series\b|\blaurent series\b|\btaylor series\b|\bradius of convergence\b|\bprincipal part\b", re.IGNORECASE),
    "laplacian_harmonic_operator": re.compile(r"\bharmonic function\b|\blaplacian\b|\bharmonic conjugate\b|\bmean value property\b|\bdirichlet problem\b|\bpoisson integral\b", re.IGNORECASE),
    "weierstrass_mittag_leffler_prod": re.compile(r"\bweierstrass (factorization|product)\b|\bmittag[- ]leffler\b|\binfinite product\b|\bentire function\b", re.IGNORECASE),
    "dolbeault_dbar_operator": re.compile(r"\bdolbeault\b|\bd-bar complex\b|\bdbar\b|\bpoincare lemma\b|\b(p,q)-form\b", re.IGNORECASE),
    "riemann_roch_index": re.compile(r"\briemann[- ]roch\b|\bdivisor\b|\bcanonical divisor\b|\bindex of specialty\b|\bserre duality\b", re.IGNORECASE),
    "conformal_metric_operator": re.compile(r"\bconformal factor\b|\bpoincare metric\b|\bhyperbolic metric\b|\bschwarz[- ]pick\b", re.IGNORECASE),
}

COMPLEX_GEO_KEYWORDS = {
    "complex_plane_geometry": re.compile(r"\bcomplex plane\b|\b\u2102\b|\bextended complex plane\b|\briemann sphere\b|\bstereographic projection\b", re.IGNORECASE),
    "conformal_mapping_geometry": re.compile(r"\bconformal mapping\b|\briemann mapping theorem\b|\bm\u00f6bius transformation\b|\bautomorphism\b|\bunit disk\b|\bupper half plane\b|\buniformization\b", re.IGNORECASE),
    "homology_homotopy_topology": re.compile(r"\bhomotopy\b|\bhomology\b|\bwinding number\b|\bindex of a curve\b|\bsimply connected\b|\bcycle\b|\bclosed path\b", re.IGNORECASE),
    "singularities_branch_geometry": re.compile(r"\bisolated singularity\b|\bpole\b|\bessential singularity\b|\bbranch point\b|\bbranch cut\b|\bcasorati[- ]weierstrass\b|\bpicard\b", re.IGNORECASE),
    "several_complex_geometry": re.compile(r"\bpolydisk\b|\bdomain of holomorphy\b|\bpseudoconvexity\b|\blevi form\b|\bhartogs(')? (extension|phenomenon)\b|\b\u2102\^n\b", re.IGNORECASE),
    "riemann_surface_geometry": re.compile(r"\briemann surface\b|\bcomplex manifold\b|\bholomorphic line bundle\b|\babelian differential\b|\bmeromorphic 1-form\b|\bgenus\b|\buniversal covering\b", re.IGNORECASE),
}

REPRESENTATION_KINDS = {
    "abstract": re.compile(r"\bholomorphic\b|\banalytic\b|\bcomplex manifold\b|\briemann surface\b|\bdivisor\b|\bcohomology\b|\bsheaf\b", re.IGNORECASE),
    "algebraic": re.compile(r"\bm\u00f6bius\b|\bfield\b|\bring of holomorphic\b|\blaurent\b|\bgroup of automorphisms\b|\bdivisor group\b", re.IGNORECASE),
    "geometric": re.compile(r"\bconformal\b|\briemann sphere\b|\bhyperbolic\b|\bcontour\b|\bdomain\b|\bdisk\b|\bannulus\b|\bgenus\b", re.IGNORECASE),
    "computational": re.compile(r"\bresidue\b|\bcontour integral\b|\bpower series\b|\bradius of convergence\b|\bpoisson formula\b|\bpartial fractions\b", re.IGNORECASE),
    "applied": re.compile(r"\bpotential flow\b|\belectrostatics\b|\bfluid dynamics\b|\bconformal map application\b|\bharmonic potential\b", re.IGNORECASE),
    "formal": re.compile(r"\bformal\b|\blean\b|\bmathlib\b|\bcomplex_analysis\b|\banalysis\.complex\b", re.IGNORECASE),
}


@dataclass
class ComplexAnalysisDeclaration:
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


def detect_complex_representation_profile(text: str, title: str) -> dict[str, Any]:
    full_text = f"{title}\n{text}"
    eo_tags = [tag for tag, pat in COMPLEX_EO_KEYWORDS.items() if pat.search(full_text)]
    geo_tags = [tag for tag, pat in COMPLEX_GEO_KEYWORDS.items() if pat.search(full_text)]

    if eo_tags and geo_tags:
        direct_status = "DUAL_DIRECT"
    elif eo_tags:
        direct_status = "EO_ONLY_DIRECT"
    elif geo_tags:
        direct_status = "GEO_ONLY_DIRECT"
    else:
        direct_status = "UNCLASSIFIED"

    rep_kinds = [k for k, pat in REPRESENTATION_KINDS.items() if pat.search(full_text)]
    if not rep_kinds:
        rep_kinds = ["abstract"]

    return {
        "direct_status": direct_status,
        "eo_tags": sorted(eo_tags),
        "geo_tags": sorted(geo_tags),
        "representation_kinds": sorted(rep_kinds),
        "detector_stage": STAGE,
    }


def compute_statement_hash(statement_text: str) -> str:
    cleaned = " ".join(statement_text.strip().split())
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def authoritative_complex_declaration_registry() -> dict[str, dict[str, Any]]:
    """Rebuild exact declaration identities from the curated source statements."""
    registry: dict[str, dict[str, Any]] = {}
    for item in get_raw_declarations():
        node_id = f"decl:{SOURCE_ID}:{item['decl_type']}:{item['number']}"
        if node_id in registry:
            raise ValueError(f"duplicate authoritative declaration identity: {node_id}")
        registry[node_id] = {
            "source_id": SOURCE_ID,
            "decl_type": item["decl_type"],
            "chapter_section": item["chapter_section"],
            "page": item["page"],
            "statement_sha256": compute_statement_hash(item["text"]),
            "char_count": len(item["text"]),
            "structural_refs": [
                f"decl:{SOURCE_ID}:{target}" for target in item.get("refs", [])
            ],
            "node_type": "SOURCE_DECLARATION",
        }
    return registry


def validate_complex_declarations(declarations: list[ComplexAnalysisDeclaration]) -> None:
    """Validate declaration identities and structural references before graph mutation.

    A structural reference is proof metadata, so accepting a dangling target would make
    the resulting graph claim a dependency which cannot be inspected.  This validator
    deliberately fails closed instead.
    """

    authoritative = authoritative_complex_declaration_registry()
    by_id: dict[str, ComplexAnalysisDeclaration] = {}
    for declaration in declarations:
        if declaration.node_id in by_id:
            raise ValueError(f"duplicate complex declaration identity: {declaration.node_id}")
        expected_prefix = f"decl:{declaration.source_id}:{declaration.decl_type}:"
        if declaration.source_id != SOURCE_ID or not declaration.node_id.startswith(expected_prefix):
            raise ValueError(f"invalid source-bound declaration identity: {declaration.node_id}")
        if declaration.node_type != "SOURCE_DECLARATION":
            raise ValueError(f"invalid declaration node type for {declaration.node_id}")
        if not _SHA256_RE.fullmatch(declaration.statement_sha256):
            raise ValueError(f"invalid statement_sha256 for {declaration.node_id}")
        if declaration.char_count <= 0:
            raise ValueError(f"invalid statement character count for {declaration.node_id}")
        expected = authoritative.get(declaration.node_id)
        if expected is None:
            raise ValueError(
                f"declaration identity is absent from authoritative registry: {declaration.node_id}"
            )
        for field_name, expected_value in expected.items():
            if field_name == "structural_refs":
                continue
            actual_value = getattr(declaration, field_name)
            if actual_value != expected_value:
                raise ValueError(
                    f"authoritative {field_name} mismatch for {declaration.node_id}"
                )
        by_id[declaration.node_id] = declaration

    if set(by_id) != set(authoritative):
        missing = sorted(set(authoritative) - set(by_id))
        raise ValueError(f"authoritative declaration registry is incomplete: {missing}")

    for declaration in declarations:
        for target_id in declaration.structural_refs:
            if target_id not in by_id:
                raise ValueError(
                    "dangling structural reference: "
                    f"{declaration.node_id} -> {target_id}"
                )
        expected_refs = authoritative[declaration.node_id]["structural_refs"]
        if declaration.structural_refs != expected_refs:
            raise ValueError(
                f"authoritative structural_refs mismatch for {declaration.node_id}"
            )


def get_raw_declarations() -> list[dict[str, Any]]:
    """Curated raw mathematical statements across Ahlfors, Krantz, and Conway."""
    return [
        # 1. Complex Numbers, Conformal Geometry & Riemann Sphere (Ahlfors Ch. 1)
        {
            "decl_type": "DEFINITION",
            "number": "1.1",
            "title": "Complex Number Field and Modulus",
            "chapter_section": "Ahlfors Chapter 1.1",
            "page": 1,
            "text": "The field of complex numbers C is R^2 with addition (x1, y1) + (x2, y2) = (x1+x2, y1+y2) and multiplication (x1, y1)(x2, y2) = (x1 x2 - y1 y2, x1 y2 + x2 y1), equipped with modulus |z| = sqrt(x^2 + y^2) and complex conjugation z_bar = x - i y.",
            "refs": [],
        },
        {
            "decl_type": "PROPOSITION",
            "number": "1.2",
            "title": "Triangle Inequality and Complex Modulus Properties",
            "chapter_section": "Ahlfors Chapter 1.1",
            "page": 7,
            "text": "For any z1, z2 in C, |z1 + z2| <= |z1| + |z2|, with equality if and only if z1 and z2 lie on the same ray from the origin, and |z1 z2| = |z1| |z2|.",
            "refs": ["DEFINITION:1.1"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "1.3",
            "title": "Extended Complex Plane and Riemann Sphere",
            "chapter_section": "Ahlfors Chapter 1.2",
            "page": 18,
            "text": "The extended complex plane C_hat = C union {infinity} is homeomorphic to the unit sphere S^2 in R^3 via stereographic projection from the north pole (0,0,1).",
            "refs": ["DEFINITION:1.1"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "1.4",
            "title": "Mobius Transformations",
            "chapter_section": "Ahlfors Chapter 1.3",
            "page": 24,
            "text": "A Mobius transformation (fractional linear transformation) is a mapping T(z) = (a z + b)/(c z + d) with a,b,c,d in C and a d - b c != 0, forming the automorphism group Aut(C_hat) isomorphic to PSL(2, C).",
            "refs": ["DEFINITION:1.3"],
        },
        {
            "decl_type": "THEOREM",
            "number": "1.5",
            "title": "Circle Preservation and Cross Ratio Invariance",
            "chapter_section": "Ahlfors Chapter 1.3",
            "page": 27,
            "text": "Mobius transformations map generalized circles (circles and straight lines) to generalized circles in C_hat and preserve the cross ratio (z1, z2, z3, z4) = ((z1-z3)(z2-z4))/((z1-z4)(z2-z3)).",
            "refs": ["DEFINITION:1.4"],
        },

        # 2. Complex Differentiability & Cauchy-Riemann (Ahlfors Ch. 2)
        {
            "decl_type": "DEFINITION",
            "number": "2.1",
            "title": "Complex Derivative and Holomorphic Functions",
            "chapter_section": "Ahlfors Chapter 2.1",
            "page": 30,
            "text": "A complex-valued function f: Omega -> C on an open set Omega subset C is complex differentiable at z0 in Omega if f'(z0) = lim_{h -> 0} (f(z0+h) - f(z0))/h exists. The function f is holomorphic on Omega if it is complex differentiable at every point of the open set Omega.",
            "refs": ["DEFINITION:1.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "2.2",
            "title": "Cauchy-Riemann Equations and Complex Differentiability",
            "chapter_section": "Ahlfors Chapter 2.1",
            "page": 32,
            "text": "Let f = u + i v be defined on Omega. Then f is complex differentiable at z0 = x0 + i y0 if and only if u, v are differentiable in the real sense and satisfy the Cauchy-Riemann equations: partial u/partial x = partial v/partial y and partial u/partial y = -partial v/partial x, equivalently partial f/partial z_bar = 0.",
            "refs": ["DEFINITION:2.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "2.3",
            "title": "Conformality and Jacobian Determinant of Holomorphic Maps",
            "chapter_section": "Ahlfors Chapter 2.1",
            "page": 35,
            "text": "If f is holomorphic on Omega and f'(z0) != 0, then the mapping f is conformal at z0 (preserves angles and orientation) and the real Jacobian determinant is det J_f(z0) = |f'(z0)|^2 > 0.",
            "refs": ["THEOREM:2.2"],
        },
        {
            "decl_type": "THEOREM",
            "number": "2.4",
            "title": "Harmonic Functions and Harmonic Conjugates",
            "chapter_section": "Ahlfors Chapter 2.1",
            "page": 38,
            "text": "If f = u + i v is holomorphic on Omega, then u and v are harmonic functions satisfying Delta u = partial^2 u/partial x^2 + partial^2 u/partial y^2 = 0. On any simply connected domain, every real harmonic function u has a harmonic conjugate v such that u + i v is holomorphic.",
            "refs": ["THEOREM:2.2"],
        },

        # 3. Power Series & Analytic Functions (Ahlfors Ch. 2, Conway Ch. 3)
        {
            "decl_type": "DEFINITION",
            "number": "3.1",
            "title": "Power Series and Radius of Convergence",
            "chapter_section": "Ahlfors Chapter 2.2",
            "page": 42,
            "text": "A power series centered at z0 is sum_{n=0}^infinity a_n (z - z0)^n. By the Cauchy-Hadamard formula, its radius of convergence is R = 1 / limsup_{n -> infinity} |a_n|^{1/n}.",
            "refs": ["DEFINITION:1.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "3.2",
            "title": "Analyticity of Power Series Sums",
            "chapter_section": "Ahlfors Chapter 2.2",
            "page": 44,
            "text": "Within its disk of convergence B(z0, R), the sum f(z) = sum_{n=0}^infinity a_n (z-z0)^n is holomorphic and termwise infinitely differentiable, with f'(z) = sum_{n=1}^infinity n a_n (z-z0)^{n-1} possessing the same radius of convergence R.",
            "refs": ["DEFINITION:3.1", "DEFINITION:2.1"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "3.3",
            "title": "Complex Exponential and Trigonometric Functions",
            "chapter_section": "Ahlfors Chapter 2.3",
            "page": 48,
            "text": "The complex exponential function is exp(z) = sum_{n=0}^infinity z^n / n!, satisfying exp(z1 + z2) = exp(z1) exp(z2), exp(i z) = cos(z) + i sin(z), with period 2 pi i.",
            "refs": ["DEFINITION:3.1"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "3.4",
            "title": "Complex Logarithm and Branch Cuts",
            "chapter_section": "Ahlfors Chapter 2.3",
            "page": 52,
            "text": "For z in C \\ {0}, the multi-valued logarithm is log(z) = ln|z| + i Arg(z) + 2 k pi i (k in Z). The principal branch Log(z) is holomorphic on the slit plane C \\ (-infinity, 0] and satisfies -pi < Im(Log z) < pi.",
            "refs": ["DEFINITION:3.3"],
        },

        # 4. Complex Integration & Cauchy's Integral Theorem (Ahlfors Ch. 4)
        {
            "decl_type": "DEFINITION",
            "number": "4.1",
            "title": "Complex Contour Integral",
            "chapter_section": "Ahlfors Chapter 4.1",
            "page": 101,
            "text": "For a piecewise C^1 curve gamma: [a,b] -> C and continuous f: gamma([a,b]) -> C, the contour integral is int_gamma f(z) dz = int_a^b f(gamma(t)) gamma'(t) dt, satisfying |int_gamma f(z) dz| <= sup_{z in gamma} |f(z)| * Length(gamma).",
            "refs": ["DEFINITION:1.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "4.2",
            "title": "Fundamental Theorem of Contour Integration",
            "chapter_section": "Ahlfors Chapter 4.1",
            "page": 106,
            "text": "If f: Omega -> C possesses a primitive F (such that F' = f on Omega), then for any curve gamma from z1 to z2 in Omega, int_gamma f(z) dz = F(z2) - F(z1). In particular, int_gamma f(z) dz = 0 for all closed curves gamma.",
            "refs": ["DEFINITION:4.1", "DEFINITION:2.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "4.3",
            "title": "Cauchy's Theorem for a Triangle (Goursat)",
            "chapter_section": "Ahlfors Chapter 4.1",
            "page": 109,
            "text": "If f is holomorphic in an open set containing a closed solid triangle Delta, then the contour integral over the boundary vanishes: oint_{partial Delta} f(z) dz = 0.",
            "refs": ["THEOREM:4.2"],
        },
        {
            "decl_type": "THEOREM",
            "number": "4.4",
            "title": "Cauchy's Integral Theorem in Convex and Simply Connected Domains",
            "chapter_section": "Ahlfors Chapter 4.1",
            "page": 112,
            "text": "If f is holomorphic in a simply connected domain Omega, then for every closed rectifiable curve gamma in Omega, oint_gamma f(z) dz = 0.",
            "refs": ["THEOREM:4.3"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "4.5",
            "title": "Winding Number (Index of a Curve)",
            "chapter_section": "Ahlfors Chapter 4.2",
            "page": 115,
            "text": "For a closed curve gamma and z0 not in gamma, the winding number (index) is Ind_gamma(z0) = (1 / (2 pi i)) oint_gamma (1 / (z - z0)) dz, which is always an integer.",
            "refs": ["DEFINITION:4.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "4.6",
            "title": "General Homology Version of Cauchy's Theorem",
            "chapter_section": "Ahlfors Chapter 4.2",
            "page": 141,
            "text": "Let f be holomorphic on open Omega. If a cycle gamma is homologous to zero in Omega (i.e. Ind_gamma(w) = 0 for all w not in Omega), then oint_gamma f(z) dz = 0.",
            "refs": ["DEFINITION:4.5", "THEOREM:4.4"],
        },

        # 5. Cauchy Integral Formula & Local Properties (Ahlfors Ch. 4)
        {
            "decl_type": "THEOREM",
            "number": "5.1",
            "title": "Cauchy's Integral Formula",
            "chapter_section": "Ahlfors Chapter 4.2",
            "page": 118,
            "text": "Let f be holomorphic on Omega and gamma a cycle homologous to zero in Omega. Then for any z0 in Omega not on gamma, n(gamma, z0) f(z0) = (1 / (2 pi i)) oint_gamma (f(z) / (z - z0)) dz.",
            "refs": ["DEFINITION:4.5", "THEOREM:4.6"],
        },
        {
            "decl_type": "THEOREM",
            "number": "5.2",
            "title": "Higher Derivatives of Holomorphic Functions",
            "chapter_section": "Ahlfors Chapter 4.2",
            "page": 120,
            "text": "Let f be holomorphic on an open set Omega, let z0 belong to Omega, and let gamma be the positively oriented circle |z - z0| = r whose closed disk is contained in Omega. Then, for every integer n >= 0, f^{(n)}(z0) = (n! / (2 pi i)) oint_gamma (f(z) / (z - z0)^{n+1}) dz.",
            "refs": ["THEOREM:5.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "5.3",
            "title": "Cauchy's Estimates",
            "chapter_section": "Ahlfors Chapter 4.2",
            "page": 122,
            "text": "If f is holomorphic on an open neighborhood of the closed disk B_bar(z0, R) and |f(z)| <= M on the boundary circle |z - z0| = R, then |f^{(n)}(z0)| <= (n! M) / R^n for all n >= 0.",
            "refs": ["THEOREM:5.2"],
        },
        {
            "decl_type": "THEOREM",
            "number": "5.4",
            "title": "Liouville's Theorem",
            "chapter_section": "Ahlfors Chapter 4.2",
            "page": 122,
            "text": "Every bounded entire function (holomorphic on the entire complex plane C) is constant.",
            "refs": ["THEOREM:5.3"],
        },
        {
            "decl_type": "THEOREM",
            "number": "5.5",
            "title": "Fundamental Theorem of Algebra via Complex Analysis",
            "chapter_section": "Ahlfors Chapter 4.2",
            "page": 123,
            "text": "Every non-constant polynomial P(z) = a_n z^n + ... + a_0 with coefficients in C has at least one root in C.",
            "refs": ["THEOREM:5.4"],
        },
        {
            "decl_type": "THEOREM",
            "number": "5.6",
            "title": "Morera's Theorem (Converse of Cauchy's Theorem)",
            "chapter_section": "Ahlfors Chapter 4.2",
            "page": 123,
            "text": "If f: Omega -> C is continuous and oint_{partial T} f(z) dz = 0 for every closed triangle T subset Omega, then f is holomorphic on Omega.",
            "refs": ["THEOREM:4.3", "THEOREM:5.2"],
        },
        {
            "decl_type": "THEOREM",
            "number": "5.7",
            "title": "Taylor Series Representation of Holomorphic Functions",
            "chapter_section": "Ahlfors Chapter 4.2",
            "page": 125,
            "text": "If f is holomorphic on B(z0, R), then f(z) = sum_{n=0}^infinity a_n (z-z0)^n converges for all |z-z0| < R with a_n = f^{(n)}(z0)/n!.",
            "refs": ["THEOREM:5.2", "THEOREM:3.2"],
        },
        {
            "decl_type": "THEOREM",
            "number": "5.8",
            "title": "Identity Theorem and Isolated Zeros",
            "chapter_section": "Ahlfors Chapter 4.3",
            "page": 127,
            "text": "If f is holomorphic on a connected domain Omega and the zero set {z in Omega : f(z) = 0} has an accumulation point in Omega, then f is identically zero on Omega.",
            "refs": ["THEOREM:5.7"],
        },
        {
            "decl_type": "THEOREM",
            "number": "5.9",
            "title": "Maximum Modulus Principle",
            "chapter_section": "Ahlfors Chapter 4.3",
            "page": 134,
            "text": "If f is holomorphic on a connected domain Omega and |f(z)| attains a local maximum at some point in Omega, then f is constant on Omega.",
            "refs": ["THEOREM:5.1", "THEOREM:5.8"],
        },
        {
            "decl_type": "LEMMA",
            "number": "5.10",
            "title": "Schwarz Lemma",
            "chapter_section": "Ahlfors Chapter 4.3",
            "page": 135,
            "text": "If f: D -> D is holomorphic on the unit disk D = {z in C : |z| < 1} and f(0) = 0, then |f(z)| <= |z| for every z in D and |f'(0)| <= 1. If |f(z0)| = |z0| for some nonzero z0 in D, or if |f'(0)| = 1, then f(z) = e^{i theta} z for some real theta; conversely, every such rotation attains equality.",
            "refs": ["THEOREM:5.9"],
        },
        {
            "decl_type": "THEOREM",
            "number": "5.11",
            "title": "Open Mapping Theorem for Holomorphic Functions",
            "chapter_section": "Ahlfors Chapter 4.3",
            "page": 133,
            "text": "If f is a non-constant holomorphic function on a connected domain Omega, then f(Omega) is open in C.",
            "refs": ["THEOREM:5.8"],
        },
        {
            "decl_type": "THEOREM",
            "number": "5.12",
            "title": "Montel's Theorem on Normal Families",
            "chapter_section": "Ahlfors Chapter 5.5",
            "page": 225,
            "text": "A family F of holomorphic functions on an open set Omega is locally uniformly bounded if and only if every sequence in F has a subsequence converging uniformly on compact subsets of Omega to a finite-valued holomorphic limit.",
            "refs": ["THEOREM:5.3"],
        },
        {
            "decl_type": "THEOREM",
            "number": "5.13",
            "title": "Runge's Rational Approximation Theorem",
            "chapter_section": "Ahlfors Chapter 5.2",
            "page": 176,
            "text": "Let K subset C be a compact set and E a subset of C_hat \\ K meeting every connected component of C_hat \\ K. Every holomorphic function f in a neighborhood of K can be approximated uniformly on K by rational functions with poles in E.",
            "refs": ["THEOREM:5.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "5.14",
            "title": "Phragmen-Lindelof Principle",
            "chapter_section": "Ahlfors Chapter 4.3",
            "page": 136,
            "text": "Let f be holomorphic on an unbounded sector S of angle pi/alpha and continuous on its boundary. If |f(z)| <= M on partial S and |f(z)| <= C exp(eps |z|^beta) with beta < alpha, then |f(z)| <= M throughout S.",
            "refs": ["THEOREM:5.9"],
        },

        # 6. Singularities, Laurent Series & Residue Calculus (Ahlfors Ch. 4, 5, Conway Ch. 5)
        {
            "decl_type": "DEFINITION",
            "number": "6.1",
            "title": "Classification of Isolated Singularities",
            "chapter_section": "Ahlfors Chapter 4.3",
            "page": 128,
            "text": "An isolated singularity z0 of f is: (1) Removable if lim_{z -> z0} (z-z0) f(z) = 0; (2) A Pole of order m >= 1 if lim_{z -> z0} (z-z0)^m f(z) = c != 0; (3) An Essential Singularity otherwise.",
            "refs": ["DEFINITION:2.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "6.2",
            "title": "Riemann's Theorem on Removable Singularities",
            "chapter_section": "Ahlfors Chapter 4.3",
            "page": 128,
            "text": "If f is holomorphic on Omega \\ {z0} and bounded in a punctured neighborhood of z0, then f extends uniquely to a holomorphic function on Omega.",
            "refs": ["DEFINITION:6.1", "THEOREM:5.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "6.3",
            "title": "Casorati-Weierstrass Theorem",
            "chapter_section": "Ahlfors Chapter 4.3",
            "page": 129,
            "text": "If z0 is an essential singularity of f, then for any punctured neighborhood U of z0, the image f(U \\ {z0}) is dense in the complex plane C.",
            "refs": ["DEFINITION:6.1", "THEOREM:6.2"],
        },
        {
            "decl_type": "THEOREM",
            "number": "6.4",
            "title": "Great Picard Theorem",
            "chapter_section": "Conway Chapter 12",
            "page": 300,
            "text": "In any punctured neighborhood of an essential singularity z0, f(z) assumes every complex value infinitely many times, with at most one exception.",
            "refs": ["THEOREM:6.3"],
        },
        {
            "decl_type": "THEOREM",
            "number": "6.5",
            "title": "Laurent Series Expansion in an Annulus",
            "chapter_section": "Ahlfors Chapter 5.1",
            "page": 184,
            "text": "If f is holomorphic in an annulus A = {z : r1 < |z - z0| < r2}, then f(z) = sum_{n=-infinity}^infinity a_n (z-z0)^n with a_n = (1 / (2 pi i)) oint_gamma (f(w) / (w - z0)^{n+1}) dw for any concentric circle gamma.",
            "refs": ["THEOREM:5.1", "DEFINITION:6.1"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "6.6",
            "title": "Residue of a Meromorphic Function",
            "chapter_section": "Ahlfors Chapter 4.5",
            "page": 148,
            "text": "The residue of f at an isolated singularity z0 is the coefficient a_{-1} of (z-z0)^{-1} in its Laurent expansion: Res(f, z0) = (1 / (2 pi i)) oint_gamma f(z) dz.",
            "refs": ["THEOREM:6.5"],
        },
        {
            "decl_type": "THEOREM",
            "number": "6.7",
            "title": "Cauchy's Residue Theorem",
            "chapter_section": "Ahlfors Chapter 4.5",
            "page": 149,
            "text": "Let f be holomorphic on Omega except for isolated singularities {zk}. If gamma is a cycle homologous to zero in Omega not passing through any zk, then (1 / (2 pi i)) oint_gamma f(z) dz = sum_k Ind_gamma(zk) Res(f, zk).",
            "refs": ["DEFINITION:6.6", "THEOREM:4.6"],
        },
        {
            "decl_type": "THEOREM",
            "number": "6.8",
            "title": "The Argument Principle",
            "chapter_section": "Ahlfors Chapter 4.5",
            "page": 152,
            "text": "If f is meromorphic on Omega and gamma is a cycle homologous to zero in Omega that avoids every zero and pole of f, then (1 / (2 pi i)) oint_gamma (f'(z) / f(z)) dz = sum_j m_j Ind_gamma(z_j) - sum_k n_k Ind_gamma(p_k), the index-weighted number of zeros minus poles, where each zero or pole a is weighted by Ind_gamma(a) and its multiplicity. This equals the plain count N - P only when gamma is a positively oriented simple closed contour and each enclosed zero and pole has index one.",
            "refs": ["THEOREM:6.7"],
        },
        {
            "decl_type": "THEOREM",
            "number": "6.9",
            "title": "Rouche's Theorem",
            "chapter_section": "Ahlfors Chapter 4.5",
            "page": 153,
            "text": "If f and g are holomorphic on and inside a simple closed contour gamma, and |g(z)| < |f(z)| for all z on gamma, then f and f + g have the same number of zeros inside gamma counted with multiplicity.",
            "refs": ["THEOREM:6.8"],
        },
        {
            "decl_type": "THEOREM",
            "number": "6.10",
            "title": "Picard's Little Theorem",
            "chapter_section": "Ahlfors Chapter 7.4",
            "page": 307,
            "text": "Every non-constant entire function f: C -> C takes every complex value with at most one exception.",
            "refs": ["THEOREM:6.4", "THEOREM:5.4"],
        },

        # 7. Harmonic Functions, Dirichlet Problem & Conformal Mappings (Ahlfors Ch. 6, Conway Ch. 8)
        {
            "decl_type": "THEOREM",
            "number": "7.1",
            "title": "Mean Value Property of Harmonic Functions",
            "chapter_section": "Ahlfors Chapter 6.1",
            "page": 242,
            "text": "If u is harmonic on the disk B(z0, R), then u(z0) = (1 / (2 pi)) int_0^{2 pi} u(z0 + r e^{i theta}) d theta for any 0 < r < R.",
            "refs": ["THEOREM:2.4"],
        },
        {
            "decl_type": "THEOREM",
            "number": "7.2",
            "title": "Poisson Integral Formula for the Unit Disk",
            "chapter_section": "Ahlfors Chapter 6.1",
            "page": 244,
            "text": "If u is continuous on the closed disk D_bar and harmonic in D, then for z = r e^{i theta} in D, u(r e^{i theta}) = (1 / (2 pi)) int_0^{2 pi} ((1 - r^2) / (1 - 2 r cos(theta - phi) + r^2)) u(e^{i phi}) d phi.",
            "refs": ["THEOREM:7.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "7.3",
            "title": "Solvability of Dirichlet Problem on the Disk",
            "chapter_section": "Ahlfors Chapter 6.1",
            "page": 246,
            "text": "For any continuous boundary function f: partial D -> R, the Poisson integral P[f] defines a unique harmonic function u on D such that lim_{z -> zeta, z in D} u(z) = f(zeta) for all zeta in partial D.",
            "refs": ["THEOREM:7.2"],
        },
        {
            "decl_type": "THEOREM",
            "number": "7.4",
            "title": "Harnack's Inequality and Harnack's Principle",
            "chapter_section": "Ahlfors Chapter 6.1",
            "page": 247,
            "text": "If u >= 0 is harmonic on B(z0, R), then ((R - r) / (R + r)) u(z0) <= u(z) <= ((R + r) / (R - r)) u(z0) whenever |z - z0| = r < R. If (u_n) is an increasing sequence of positive harmonic functions on a connected domain Omega, then either it converges locally uniformly on Omega to a harmonic function, or it diverges locally uniformly to +infinity.",
            "refs": ["THEOREM:7.2"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "7.5",
            "title": "Conformal Equivalence of Domains",
            "chapter_section": "Ahlfors Chapter 6.2",
            "page": 251,
            "text": "Two domains Omega1, Omega2 subset C are conformally equivalent if there exists a bijective holomorphic map f: Omega1 -> Omega2 (with holomorphic inverse).",
            "refs": ["THEOREM:2.3"],
        },
        {
            "decl_type": "THEOREM",
            "number": "7.6",
            "title": "Riemann Mapping Theorem",
            "chapter_section": "Ahlfors Chapter 6.2",
            "page": 253,
            "text": "Every non-empty simply connected open subset Omega subset C with Omega != C is conformally equivalent to the open unit disk D = {z in C : |z| < 1}. Given z0 in Omega, the biholomorphism f: Omega -> D is uniquely determined by f(z0) = 0 and f'(z0) > 0.",
            "refs": ["DEFINITION:7.5", "LEMMA:5.10"],
        },
        {
            "decl_type": "THEOREM",
            "number": "7.7",
            "title": "Uniformization Theorem for Simply Connected Riemann Surfaces",
            "chapter_section": "Ahlfors Chapter 8",
            "page": 310,
            "text": "Every simply connected Riemann surface is conformally equivalent to exactly one of: (1) The Riemann sphere C_hat (elliptic); (2) The complex plane C (parabolic); (3) The open unit disk D (hyperbolic).",
            "refs": ["THEOREM:7.6", "DEFINITION:1.3"],
        },
        {
            "decl_type": "THEOREM",
            "number": "7.8",
            "title": "Monodromy Theorem for Analytic Continuation",
            "chapter_section": "Ahlfors Chapter 8.1",
            "page": 295,
            "text": "If a function element (f, D0) can be analytically continued along all paths in a simply connected domain Omega, then the analytic continuation defines a single-valued holomorphic function on Omega.",
            "refs": ["THEOREM:7.6", "THEOREM:5.8"],
        },

        # 8. Entire & Meromorphic Functions (Weierstrass & Mittag-Leffler) (Ahlfors Ch. 5, Conway Ch. 7)
        {
            "decl_type": "DEFINITION",
            "number": "8.1",
            "title": "Weierstrass Elementary Factors",
            "chapter_section": "Ahlfors Chapter 5.2",
            "page": 194,
            "text": "The Weierstrass elementary factors are E_0(z) = 1 - z and E_p(z) = (1 - z) exp(sum_{k=1}^p z^k / k) for p >= 1.",
            "refs": ["DEFINITION:3.3"],
        },
        {
            "decl_type": "THEOREM",
            "number": "8.2",
            "title": "Weierstrass Factorization Theorem",
            "chapter_section": "Ahlfors Chapter 5.2",
            "page": 195,
            "text": "Let (a_n) be a sequence of nonzero complex numbers, repeated according to prescribed multiplicity, with no finite accumulation point, and let m >= 0 be an integer. There exist nonnegative integers p_n such that f(z) = z^m prod_{n=1}^infinity E_{p_n}(z / a_n) defines an entire function whose zeros are exactly 0 with multiplicity m and the points a_n with their prescribed multiplicities, with no other zeros.",
            "refs": ["DEFINITION:8.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "8.3",
            "title": "Mittag-Leffler Theorem on Meromorphic Functions",
            "chapter_section": "Ahlfors Chapter 5.2",
            "page": 197,
            "text": "Let {bn} be a sequence of distinct points in Omega with no accumulation point in Omega, and Pn(1 / (z - bn)) prescribed polynomials in 1 / (z - bn) with no constant term. Then there exists a meromorphic function f on Omega whose polar parts are precisely Pn at bn.",
            "refs": ["DEFINITION:6.1", "THEOREM:6.5"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "8.4",
            "title": "Gamma Function and Euler's Reflection Formula",
            "chapter_section": "Ahlfors Chapter 5.2",
            "page": 198,
            "text": "The Euler Gamma function Gamma(z) = int_0^infinity t^{z-1} e^{-t} dt (for Re(z) > 0) extends to a meromorphic function on C with simple poles at non-positive integers, satisfying Gamma(z+1) = z Gamma(z) and Gamma(z) Gamma(1-z) = pi / sin(pi z).",
            "refs": ["THEOREM:8.2", "THEOREM:8.3"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "8.5",
            "title": "Riemann Zeta Function and Functional Equation",
            "chapter_section": "Ahlfors Chapter 5.2",
            "page": 213,
            "text": "The Riemann zeta function zeta(s) = sum_{n=1}^infinity n^{-s} (for Re(s) > 1) has a meromorphic continuation to C with a unique simple pole at s = 1, satisfying the functional equation xi(s) = xi(1-s) where xi(s) = (1/2) s (s-1) pi^{-s/2} Gamma(s/2) zeta(s).",
            "refs": ["DEFINITION:8.4"],
        },

        # 9. Several Complex Variables (SCV) & Dolbeault Operators (Krantz Ch. 1-4)
        {
            "decl_type": "DEFINITION",
            "number": "9.1",
            "title": "Holomorphic Functions in Several Variables",
            "chapter_section": "Krantz Chapter 1.1",
            "page": 1,
            "text": "A function f: Omega -> C on open Omega subset C^n is holomorphic if it is continuous and holomorphic in each complex coordinate variable z_j separately (Osgood's Lemma / Hartogs' Theorem).",
            "refs": ["DEFINITION:2.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "9.2",
            "title": "Hartogs' Separate Holomorphy Theorem",
            "chapter_section": "Krantz Chapter 1.2",
            "page": 8,
            "text": "If f: Omega -> C is separately holomorphic in each coordinate variable z1, ..., zn on open Omega subset C^n, then f is jointly continuous and holomorphic on Omega.",
            "refs": ["DEFINITION:9.1"],
        },
        {
            "decl_type": "THEOREM",
            "number": "9.3",
            "title": "Hartogs' Extension Phenomenon (Kugelsatz)",
            "chapter_section": "Krantz Chapter 1.3",
            "page": 14,
            "text": "Let n >= 2 and K subset Omega be a compact subset such that Omega \\ K is connected. Then every holomorphic function f on Omega \\ K extends uniquely to a holomorphic function on the entire domain Omega. Consequently, holomorphic functions in C^n (n >= 2) have no isolated singularities.",
            "refs": ["DEFINITION:9.1", "THEOREM:6.2"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "9.4",
            "title": "Dolbeault Operators and (p,q)-Forms",
            "chapter_section": "Krantz Chapter 2.1",
            "page": 35,
            "text": "The space of complex differential forms on C^n decomposes into types Omega^k = bigoplus_{p+q=k} Omega^{p,q}, with the exterior derivative splitting as d = partial + partial_bar, where partial: Omega^{p,q} -> Omega^{p+1,q} and partial_bar: Omega^{p,q} -> Omega^{p,q+1} satisfy partial^2 = 0, partial_bar^2 = 0, and partial partial_bar + partial_bar partial = 0.",
            "refs": ["THEOREM:2.2"],
        },
        {
            "decl_type": "THEOREM",
            "number": "9.5",
            "title": "The d-bar Poincare Lemma (Dolbeault-Grothendieck)",
            "chapter_section": "Krantz Chapter 2.2",
            "page": 42,
            "text": "On any polydisk P subset C^n, the Dolbeault complex is exact in positive degrees: for any partial_bar-closed (p,q)-form alpha with q >= 1 (so partial_bar alpha = 0), there exists a (p,q-1)-form u such that partial_bar u = alpha.",
            "refs": ["DEFINITION:9.4"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "9.6",
            "title": "Domain of Holomorphy and Pseudoconvexity",
            "chapter_section": "Krantz Chapter 3.1",
            "page": 75,
            "text": "A domain Omega subset C^n is a domain of holomorphy if there exists a holomorphic function on Omega that does not extend holomorphically to any strictly larger domain. The solution of the Levi problem states that Omega is a domain of holomorphy if and only if Omega is pseudoconvex.",
            "refs": ["THEOREM:9.3"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "9.7",
            "title": "Levi Form and Strict Pseudoconvexity",
            "chapter_section": "Krantz Chapter 3.3",
            "page": 88,
            "text": "Let Omega have C^2 boundary and a C^2 defining function rho on a neighborhood of the boundary, with the fixed sign convention Omega = {rho < 0}, boundary Omega = {rho = 0}, and d rho nonzero on the boundary. The Levi form L_rho(p, w) = sum_{j,k=1}^n (partial^2 rho / partial z_j partial z_bar_k)(p) w_j w_bar_k is semipositive on complex tangent vectors w at every boundary point precisely when the boundary is Levi pseudoconvex; under these C^2 hypotheses this characterizes pseudoconvexity of Omega. Strict positivity on every nonzero complex tangent vector defines strict pseudoconvexity.",
            "refs": ["DEFINITION:9.6"],
        },

        # 10. Riemann Surfaces, Complex Manifolds & Riemann-Roch (Ahlfors Ch. 8, Conway II, Forster)
        {
            "decl_type": "DEFINITION",
            "number": "10.1",
            "title": "Riemann Surface (1-Dimensional Complex Manifold)",
            "chapter_section": "Ahlfors Chapter 8.1",
            "page": 302,
            "text": "A Riemann surface X is a connected 2-dimensional topological manifold equipped with a holomorphic atlas {(U_alpha, phi_alpha)} where coordinate transition maps phi_beta circ phi_alpha^{-1} are biholomorphic.",
            "refs": ["DEFINITION:2.1", "DEFINITION:7.5"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "10.2",
            "title": "Holomorphic and Meromorphic 1-Forms",
            "chapter_section": "Ahlfors Chapter 8.2",
            "page": 306,
            "text": "A holomorphic (resp. meromorphic) 1-form omega on a Riemann surface X is locally given in coordinates by f(z) dz where f is holomorphic (resp. meromorphic), transforming under coordinate changes z = psi(w) as (f circ psi)(w) psi'(w) dw.",
            "refs": ["DEFINITION:10.1", "DEFINITION:4.1"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "10.3",
            "title": "Divisors and Divisor Class Group",
            "chapter_section": "Conway II Chapter 17",
            "page": 85,
            "text": "A divisor D on a compact Riemann surface X is a formal sum D = sum_{p in X} n_p p (n_p in Z, finitely many non-zero) with degree deg(D) = sum n_p. The principal divisor of a meromorphic function f is (f) = sum_p ord_p(f) p, with deg((f)) = 0.",
            "refs": ["DEFINITION:10.1", "DEFINITION:6.1"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "10.4",
            "title": "Linear System L(D) Associated to a Divisor",
            "chapter_section": "Conway II Chapter 17",
            "page": 88,
            "text": "For a divisor D on X, the vector space L(D) is {f in M(X)* : (f) + D >= 0} union {0}, consisting of meromorphic functions whose poles are bounded by D, with dimension ell(D) = dim_C L(D).",
            "refs": ["DEFINITION:10.3"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "10.5",
            "title": "Canonical Divisor and Genus of a Riemann Surface",
            "chapter_section": "Conway II Chapter 17",
            "page": 92,
            "text": "The canonical divisor K on a compact Riemann surface X of genus g is the divisor of any non-zero meromorphic 1-form omega: K = (omega), satisfying deg(K) = 2 g - 2 and ell(K) = g.",
            "refs": ["DEFINITION:10.2", "DEFINITION:10.4"],
        },
        {
            "decl_type": "THEOREM",
            "number": "10.6",
            "title": "The Riemann-Roch Theorem",
            "chapter_section": "Conway II Chapter 17",
            "page": 95,
            "text": "For any divisor D on a compact Riemann surface X of genus g with canonical divisor K: ell(D) - ell(K - D) = deg(D) + 1 - g.",
            "refs": ["DEFINITION:10.4", "DEFINITION:10.5"],
        },
        {
            "decl_type": "THEOREM",
            "number": "10.7",
            "title": "Serre Duality for Compact Riemann Surfaces",
            "chapter_section": "Conway II Chapter 18",
            "page": 115,
            "text": "For any holomorphic vector bundle E (or invertible sheaf O(D)) on a compact Riemann surface X, the cohomology spaces satisfy H^1(X, O(D)) =~= H^0(X, Omega^1 tensor O(-D))^*, so dim H^1(X, O(D)) = ell(K - D).",
            "refs": ["THEOREM:10.6", "DEFINITION:10.5"],
        },
        {
            "decl_type": "THEOREM",
            "number": "10.8",
            "title": "Abel's Theorem and Jacobi Inversion",
            "chapter_section": "Conway II Chapter 19",
            "page": 140,
            "text": "A degree zero divisor D = sum p_i - sum q_i on a compact Riemann surface X is principal if and only if its Abel-Jacobi map image sum int_{q_i}^{p_i} (omega_1, ..., omega_g)^T is zero in the Jacobian variety Jac(X) = C^g / Lambda.",
            "refs": ["DEFINITION:10.3", "DEFINITION:10.5"],
        },
        {
            "decl_type": "DEFINITION",
            "number": "10.9",
            "title": "Complex Torus and Weierstrass Elliptic Functions",
            "chapter_section": "Ahlfors Chapter 7.2",
            "page": 272,
            "text": "A 1-dimensional complex torus is X = C / Lambda for a lattice Lambda = Z omega1 + Z omega2 (Im(omega2/omega1) > 0), parameterized by the doubly-periodic Weierstrass elliptic function wp(z) = 1/z^2 + sum_{w in Lambda \\ {0}} (1/(z-w)^2 - 1/w^2) satisfying the differential equation (wp')^2 = 4 wp^3 - g2 wp - g3.",
            "refs": ["DEFINITION:10.1", "DEFINITION:6.1"],
        },
    ]


def build_complex_declarations() -> list[ComplexAnalysisDeclaration]:
    raw_decls = get_raw_declarations()
    declarations: list[ComplexAnalysisDeclaration] = []

    for item in raw_decls:
        decl_type = item["decl_type"]
        number = item["number"]
        node_id = f"decl:{SOURCE_ID}:{decl_type}:{number}"
        label = f"Complex Analysis ({decl_type} {number}): {item['title']}"
        stmt_hash = compute_statement_hash(item["text"])
        char_count = len(item["text"])
        rep_profile = detect_complex_representation_profile(item["text"], item["title"])

        structural_refs = [
            f"decl:{SOURCE_ID}:{ref_target}"
            for ref_target in item.get("refs", [])
        ]

        decl = ComplexAnalysisDeclaration(
            node_id=node_id,
            source_id=SOURCE_ID,
            label=label,
            decl_type=decl_type,
            chapter_section=item["chapter_section"],
            page=item["page"],
            statement_sha256=stmt_hash,
            char_count=char_count,
            structural_refs=structural_refs,
            representation_profile=rep_profile,
        )
        declarations.append(decl)

    validate_complex_declarations(declarations)
    return declarations


def export_declarations_json(output_path: Path) -> None:
    decls = build_complex_declarations()
    out_dicts = [d.to_dict() for d in decls]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out_dicts, f, indent=2)
    print(f"[Import v0.19] Exported {len(out_dicts)} Source G declarations to {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="MAPEOGEO v0.19 Complex Analysis Source Declarations Ingestion")
    parser.add_argument("--out-file", type=Path, default=ROOT / "artifacts" / "complex_analysis_v0_19" / "declarations_v0_19.json")
    args = parser.parse_args()

    decls = build_complex_declarations()
    print(f"Loaded {len(decls)} Complex Analysis / SCV / Riemann Surfaces declarations (Source ID: {SOURCE_ID}).")

    eo_direct = sum(1 for d in decls if d.representation_profile.get("direct_status") == "EO_ONLY_DIRECT")
    geo_direct = sum(1 for d in decls if d.representation_profile.get("direct_status") == "GEO_ONLY_DIRECT")
    dual_direct = sum(1 for d in decls if d.representation_profile.get("direct_status") == "DUAL_DIRECT")
    print(f"  Representation profiles: EO={eo_direct}, GEO={geo_direct}, DUAL={dual_direct}")

    export_declarations_json(args.out_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
