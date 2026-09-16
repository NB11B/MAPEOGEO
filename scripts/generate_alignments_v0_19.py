#!/usr/bin/env python3
"""Generate curated cross-source alignments for MAPEOGEO v0.19 Complex Analysis, SCV & Riemann Surfaces Expansion."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SOURCE_ID = "AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979"

# New canonical objects for Complex Analysis, SCV & Riemann Surfaces (Domain 8)
COMPLEX_CANONICAL_OBJECTS = [
    {
        "id": "canonical:complex:holomorphic_functions_cauchy_riemann",
        "name": "Holomorphic Functions and Cauchy-Riemann Equations",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Complex differentiability, Cauchy-Riemann system partial_x u = partial_y v, partial_y u = -partial_x v, and dbar f = 0",
        "representation_kinds": ["abstract", "algebraic", "computational"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:2.1", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:2.2", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:38_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:conformal_mapping_and_mobius",
        "name": "Conformal Mappings and Mobius Transformations",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Angle-preserving holomorphic maps with non-zero derivative, fractional linear transformations PSL(2,C), and circle preservation",
        "representation_kinds": ["geometric", "algebraic"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:1.4", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:1.5", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:2.3", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:DEFINITION:7.5", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:smooth_map", "corpus": "LEE", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:riemann_sphere_stereographic",
        "name": "Riemann Sphere and Extended Complex Plane",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "One-point compactification C_hat = C union {infinity} isomorphic to S^2 via stereographic projection",
        "representation_kinds": ["geometric", "abstract"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:1.3", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:topological_manifold", "corpus": "LEE", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:definition:37_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:power_series_analyticity",
        "name": "Power Series Representation and Analyticity",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Cauchy-Hadamard radius of convergence, infinite differentiability, and equivalence of holomorphy and analyticity",
        "representation_kinds": ["abstract", "computational", "algebraic"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:3.1", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:3.2", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.7", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:2_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:contour_integration",
        "name": "Complex Contour Integration and Line Integrals",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Integration of continuous complex functions along piecewise C^1 curves, ML inequality, and primitive integration",
        "representation_kinds": ["computational", "geometric"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:4.1", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:4.2", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:differential_k_form", "corpus": "LEE", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:cauchy_integral_theorem",
        "name": "Cauchy's Integral Theorem (Goursat, Convex, Homology)",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Vanishing of closed contour integrals oint_gamma f(z) dz = 0 for holomorphic functions on simply connected domains and homologous cycles",
        "representation_kinds": ["abstract", "geometric", "computational"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:4.3", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:4.4", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:4.6", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:generalized_stokes_theorem", "corpus": "LEE", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:cauchy_integral_formula",
        "name": "Cauchy's Integral Formula and Higher Derivatives",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Integral representation of holomorphic functions and all derivatives via Cauchy kernel (z - z0)^{-(n+1)}",
        "representation_kinds": ["computational", "abstract"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.1", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.2", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.3", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:liouville_and_fundamental_theorem_algebra",
        "name": "Liouville's Theorem and Fundamental Theorem of Algebra",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Constancy of bounded entire functions and algebraic completeness of C via Cauchy estimates",
        "representation_kinds": ["abstract", "algebraic"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.4", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.5", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:5_8", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:12_6", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:morera_theorem",
        "name": "Morera's Theorem",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Integral converse to Cauchy's Theorem: continuous functions with vanishing triangle integrals are holomorphic",
        "representation_kinds": ["abstract", "computational"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.6", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:maximum_modulus_and_schwarz_lemma",
        "name": "Maximum Modulus Principle and Schwarz Lemma",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Absence of interior local maxima for |f(z)|, Schwarz lemma on unit disk |f(z)| <= |z|, and Schwarz-Pick hyperbolic geometry",
        "representation_kinds": ["geometric", "abstract"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.9", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:LEMMA:5.10", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.14", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:identity_and_open_mapping_theorems",
        "name": "Identity Theorem and Open Mapping Theorem",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Uniqueness of analytic continuation from accumulation points and openness of holomorphic images",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.8", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.11", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:montel_and_normal_families",
        "name": "Montel's Theorem and Normal Families",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Compactness of locally uniformly bounded families of holomorphic functions under compact-open topology",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.12", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:runge_rational_approximation",
        "name": "Runge's Rational Approximation Theorem",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Uniform approximation of holomorphic functions on compact sets by rational functions with prescribed poles",
        "representation_kinds": ["abstract", "computational"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:5.13", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:isolated_singularities_classification",
        "name": "Classification of Isolated Singularities and Removable Singularities",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Removable singularities, poles, and essential singularities characterized by limit behavior and Riemann's theorem",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:6.1", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:6.2", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:laurent_series_annulus",
        "name": "Laurent Series Expansion",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Two-sided power series expansion in annular domains decomposing into regular and principal parts",
        "representation_kinds": ["computational", "algebraic"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:6.5", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:residue_theorem_and_calculus",
        "name": "Cauchy's Residue Theorem and Residue Calculus",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Evaluation of contour integrals via residues sum Res(f, zk) Ind_gamma(zk) for meromorphic functions",
        "representation_kinds": ["computational", "applied"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:6.6", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:6.7", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:argument_principle_and_rouche",
        "name": "Argument Principle and Rouche's Theorem",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Counting zeros minus poles (1/(2 pi i)) oint (f'/f) dz = N - P and perturbation stability of roots",
        "representation_kinds": ["computational", "geometric"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:6.8", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:6.9", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:picard_theorems",
        "name": "Picard's Little and Great Theorems",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Density of essential singularity images (Casorati-Weierstrass) and omission of at most one complex value (Picard)",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:6.3", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:6.4", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:6.10", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:harmonic_functions_poisson_integral",
        "name": "Harmonic Functions, Mean Value Property, and Dirichlet Problem",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Laplace equation Delta u = 0, mean value property, Poisson kernel representation on disk, and Harnack's inequality",
        "representation_kinds": ["computational", "geometric", "applied"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:2.4", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:7.1", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:7.2", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:7.3", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:7.4", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:riemann_mapping_theorem",
        "name": "Riemann Mapping Theorem",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Biholomorphic equivalence of every non-empty simply connected proper domain in C to the open unit disk",
        "representation_kinds": ["geometric", "abstract"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:7.6", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:smooth_map", "corpus": "LEE", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:uniformization_and_monodromy",
        "name": "Uniformization Theorem and Monodromy",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Classification of simply connected Riemann surfaces (sphere, plane, disk) and monodromy theorem for analytic continuation",
        "representation_kinds": ["geometric", "abstract"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:7.7", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:7.8", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:weierstrass_factorization_mittag_leffler",
        "name": "Weierstrass Factorization and Mittag-Leffler Theorems",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Construction of entire functions with prescribed zeros via infinite products and meromorphic functions with prescribed poles",
        "representation_kinds": ["abstract", "algebraic", "computational"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:8.1", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:8.2", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:8.3", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:gamma_zeta_special_functions",
        "name": "Gamma and Riemann Zeta Functions",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Euler Gamma function reflection formula Gamma(z)Gamma(1-z) = pi/sin(pi z) and Riemann zeta function functional equation",
        "representation_kinds": ["computational", "applied", "algebraic"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:8.4", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:DEFINITION:8.5", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:scv_hartogs_extension",
        "name": "Several Complex Variables and Hartogs' Extension Phenomenon",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Separate holomorphy implies joint holomorphy and Kugelsatz: absence of isolated singularities in C^n (n >= 2)",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:9.1", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:9.2", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:9.3", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:dolbeault_dbar_complex",
        "name": "Dolbeault (p,q)-Decomposition and d-bar Poincare Lemma",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Graded decomposition of complex differential forms Omega^k = bigoplus Omega^{p,q}, d = partial + dbar, and exactness on polydisks",
        "representation_kinds": ["abstract", "algebraic"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:9.4", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:9.5", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:differential_k_form", "corpus": "LEE", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:diffgeom:thm:poincare_lemma", "corpus": "LEE", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:domains_holomorphy_pseudoconvexity",
        "name": "Domains of Holomorphy, Pseudoconvexity, and Levi Form",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Characterization of natural domains of definition for holomorphic functions via boundary pseudoconvexity and semi-definite Levi form",
        "representation_kinds": ["geometric", "abstract"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:9.6", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:DEFINITION:9.7", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:riemann_surface_complex_manifold",
        "name": "Riemann Surfaces and 1-Dimensional Complex Manifolds",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Connected 2-manifolds with holomorphic coordinate transition charts, holomorphic 1-forms, and genus g",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:10.1", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:DEFINITION:10.2", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:smooth_manifold", "corpus": "LEE", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:diffgeom:def:differential_k_form", "corpus": "LEE", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:complex:divisors_and_linear_systems",
        "name": "Divisors, Principal Divisors, and Linear Systems L(D)",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Formal sums of points D = sum np p, principal divisors (f), and finite-dimensional meromorphic function spaces L(D)",
        "representation_kinds": ["algebraic", "abstract"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:10.3", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:DEFINITION:10.4", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:DEFINITION:10.5", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:riemann_roch_and_serre_duality",
        "name": "The Riemann-Roch Theorem and Serre Duality",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Index theorem on compact Riemann surfaces ell(D) - ell(K - D) = deg(D) + 1 - g and cohomology duality H^1(X, O(D)) =~= H^0(X, Omega^1( -D ))^*",
        "representation_kinds": ["abstract", "algebraic"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:THEOREM:10.6", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:10.7", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
            {"source": f"decl:{SOURCE_ID}:THEOREM:10.8", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:complex:elliptic_functions_complex_torus",
        "name": "Complex Tori and Weierstrass Elliptic Functions",
        "domain": "Complex Analysis & Riemann Surfaces",
        "description": "Genus 1 Riemann surfaces C/Lambda parameterized by doubly-periodic Weierstrass function wp(z) with cubic differential equation (wp')^2 = 4 wp^3 - g2 wp - g3",
        "representation_kinds": ["algebraic", "geometric", "computational"],
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:10.9", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    }
]

# Enrich existing canonical objects with Source G connections
EXISTING_CANONICAL_ENRICHMENTS = [
    {
        "id": "canonical:metric_space",
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:PROPOSITION:1.2", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:inner_product_space",
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:1.1", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:linear_map",
        "alignments": [
            {"source": f"decl:{SOURCE_ID}:DEFINITION:2.1", "corpus": "AHLFORS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    }
]


def load_v0_18_canonical_objects() -> list[dict]:
    v0_18_file = ROOT / "formal" / "cross_source_alignments_v0_18.json"
    data = json.loads(v0_18_file.read_text(encoding="utf-8"))
    return data.get("canonical_objects", [])


def merge_and_generate_v0_19_alignments() -> dict:
    prev_objects = load_v0_18_canonical_objects()
    by_id = {co["id"]: co for co in prev_objects}

    # Enrich existing canonical objects
    for enrich in EXISTING_CANONICAL_ENRICHMENTS:
        cid = enrich["id"]
        if cid in by_id:
            existing_sources = {al["source"] for al in by_id[cid]["alignments"]}
            for al in enrich["alignments"]:
                if al["source"] not in existing_sources:
                    by_id[cid]["alignments"].append(al)

    # Add new complex analysis canonical objects
    for c_co in COMPLEX_CANONICAL_OBJECTS:
        if c_co["id"] in by_id:
            existing = by_id[c_co["id"]]
            existing_sources = {al["source"] for al in existing["alignments"]}
            for al in c_co["alignments"]:
                if al["source"] not in existing_sources:
                    existing["alignments"].append(al)
        else:
            by_id[c_co["id"]] = c_co

    all_canonical = list(by_id.values())
    return {
        "schema_version": "v0.19",
        "description": "Curated Cross-Source Alignments spanning Gallier (S_A), Axler (S_B), VMLS (S_C), CVX (S_D), Billingsley (S_E), Lee (S_F), and Ahlfors/Krantz (S_G)",
        "total_canonical_objects": len(all_canonical),
        "canonical_objects": all_canonical,
    }


def main() -> int:
    out_path = ROOT / "formal" / "cross_source_alignments_v0_19.json"
    result = merge_and_generate_v0_19_alignments()
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Generated {len(result['canonical_objects'])} canonical alignments for v0.19 at {out_path}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
