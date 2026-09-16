#!/usr/bin/env python3
"""Generate curated cross-source alignments for MAPEOGEO v0.18 Differential Geometry & Lie Groups Expansion."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# New canonical objects for Differential Geometry, Lie Groups & Smooth Manifolds (Domain 7)
DIFFGEOM_CANONICAL_OBJECTS = [
    {
        "id": "canonical:diffgeom:smooth_manifold",
        "name": "Smooth Manifold and Smooth Atlas",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Topological manifold equipped with a maximal smooth atlas of smoothly compatible charts",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:topological_manifold", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:smooth_atlas", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:smooth_manifold", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:37_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:smooth_map_and_diffeomorphism",
        "name": "Smooth Map and Diffeomorphism",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Smooth mappings between manifolds and smooth invertible maps with smooth inverses",
        "representation_kinds": ["abstract", "geometric", "algebraic"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:smooth_map", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:diffeomorphism", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:38_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:partition_of_unity",
        "name": "Smooth Partition of Unity",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Locally finite collection of smooth bump functions summing to 1 subordinate to an open cover",
        "representation_kinds": ["abstract", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:diffgeom:thm:partition_of_unity", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:37_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:submanifold_and_embedding",
        "name": "Submanifolds, Immersions, and Whitney Embedding",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Embedded/immersed submanifolds, regular level sets, and Whitney strong embedding in Euclidean space",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:submanifold", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:regular_level_set_theorem", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:whitney_embedding_theorem", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:tangent_space_derivation",
        "name": "Tangent Space and Derivations",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Tangent vectors as directional derivations on smooth functions forming vector space T_p M",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:tangent_vector_derivation", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:tangent_space", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:2_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:1_20", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:1_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:pushforward_differential",
        "name": "Pushforward / Differential Map",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Linear map df_p: T_p M -> T_f(p) N induced by smooth map between manifolds and functorial chain rule",
        "representation_kinds": ["abstract", "algebraic", "computational"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:pushforward_differential", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:prop:chain_rule_differential", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:inverse_function_theorem_manifold", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:implicit_function_theorem_manifold", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:5_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:3_1", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:diffgeom:tangent_bundle",
        "name": "Tangent Bundle",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Disjoint union TM = coprod T_p M endowed with natural 2n-dimensional smooth manifold structure",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:tangent_bundle", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:2_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:vector_field_and_flow",
        "name": "Vector Fields, Integral Curves, and Flows",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Smooth sections of the tangent bundle and their associated 1-parameter groups of local diffeomorphisms",
        "representation_kinds": ["abstract", "geometric", "computational", "applied"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:vector_field", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:integral_curves_flow", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:5_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:lie_bracket_vector_fields",
        "name": "Lie Bracket of Vector Fields",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Bilinear alternating commutator bracket on vector fields satisfying the Jacobi identity",
        "representation_kinds": ["abstract", "algebraic"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:lie_bracket_vector_fields", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:prop:jacobi_identity_vector_fields", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:lie_derivative_vector_field", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:diffgeom:frobenius_theorem",
        "name": "Frobenius Theorem on Involutive Distributions",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Equivalence of involutivity of tangent distributions under Lie bracket and complete integrability/foliations",
        "representation_kinds": ["abstract", "geometric", "algebraic"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:distribution_foliation", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:frobenius_theorem", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:diffgeom:cotangent_space_and_bundle",
        "name": "Cotangent Space and Dual 1-Forms",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Dual vector space T_p* M of linear functionals on tangent vectors, and differentials df of smooth functions",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:cotangent_space", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:differential_of_function", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:tensor_bundle", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:3_7", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:diffgeom:differential_forms",
        "name": "Differential k-Forms",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Smooth alternating covariant tensor fields forming exterior algebra bundle Lambda^k(T* M)",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:differential_k_form", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:wedge_product", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:prop:wedge_product_properties", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:diffgeom:exterior_derivative",
        "name": "Exterior Derivative Operator",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Graded differential operator d: Omega^k -> Omega^{k+1} satisfying graded Leibniz rule and d^2 = 0",
        "representation_kinds": ["abstract", "algebraic", "computational"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:exterior_derivative", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcgeom:prop:exterior_derivative_leibniz", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"} if False else {"source": "srcdecl:diffgeom:prop:exterior_derivative_leibniz", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:d_squared_zero", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:closed_and_exact_forms", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:diffgeom:pullback_forms",
        "name": "Pullback of Differential Forms",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Contravariant functorial pullback f* omega commuting with exterior derivative d(f* omega) = f*(d omega)",
        "representation_kinds": ["abstract", "algebraic"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:pullback_differential_forms", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:prop:pullback_commutes_with_d", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:diffgeom:poincare_lemma_cohomology",
        "name": "Poincare Lemma and de Rham Cohomology",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Exactness of closed forms on contractible manifolds and topological de Rham cohomology quotient ker d / im d",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:diffgeom:thm:poincare_lemma", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:de_rham_cohomology", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:diffgeom:integration_and_stokes",
        "name": "Integration of Forms and Generalized Stokes' Theorem",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Integration on oriented manifolds with boundary and master duality theorem int_{partial M} omega = int_M d omega",
        "representation_kinds": ["abstract", "geometric", "applied", "computational"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:orientation_manifold", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:manifold_with_boundary", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:integration_of_differential_forms", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:generalized_stokes_theorem", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:fundamental_theorem_of_calculus_manifold", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:greens_theorem_form", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:classical_stokes_theorem", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:gauss_divergence_theorem_manifold", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:def:lebesgue_integral_nonneg", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:riemannian_metric_and_manifold",
        "name": "Riemannian Metric and Riemannian Manifold",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Smooth positive-definite inner product field on tangent spaces turning manifold into metric space (M, d_g)",
        "representation_kinds": ["abstract", "geometric", "algebraic", "computational"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:riemannian_metric", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:riemannian_manifold", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:geodesic_distance", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:hopf_rinow_theorem", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:14_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:6_1", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:thm:l2_hilbert_space", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:diffgeom:musical_isomorphisms_gradient",
        "name": "Musical Isomorphisms and Riemannian Gradient",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Metric duality isomorphisms (flat/sharp) between TM and T*M and coordinate-free gradient grad_g f = (df)^sharp",
        "representation_kinds": ["abstract", "algebraic", "computational"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:musical_isomorphisms", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:riemannian_gradient", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_42", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:section:3_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:riemannian_volume_measure",
        "name": "Riemannian Volume Form and Measure",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Canonical volume form d vol_g = sqrt(det g) dx^1 ... dx^n and induced Radon measure on Riemannian manifolds",
        "representation_kinds": ["abstract", "geometric", "applied"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:riemannian_volume_form", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:billingsley:def:measure_space", "corpus": "BILLINGSLEY", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:levi_civita_connection",
        "name": "Levi-Civita Connection and Affine Connections",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Unique torsion-free, metric-compatible covariant derivative on Riemannian manifolds",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:affine_connection", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:levi_civita_connection", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:diffgeom:geodesic_and_exponential_map",
        "name": "Geodesics and Riemannian Exponential Map",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Auto-parallel curves minimizing Riemannian distance and exponential diffeomorphism exp_p: T_p M -> M",
        "representation_kinds": ["abstract", "geometric", "computational", "applied"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:geodesic_equation", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:exponential_map_manifold", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:8_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:riemann_and_ricci_curvature",
        "name": "Riemann Curvature, Ricci Tensor, and Scalar Curvature",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Intrinsic curvature tensor R(X,Y)Z measuring non-commutativity of covariant derivatives, and trace contractions",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:riemann_curvature_tensor", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:ricci_curvature", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:diffgeom:lie_group_and_algebra",
        "name": "Lie Group and Lie Algebra",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Smooth group manifold G with smooth multiplication and inversion, and its Lie algebra g = Lie(G) = T_e G",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:lie_group", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:left_invariant_vector_field", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:lie_algebra_of_lie_group", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:lie_correspondence", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:2_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:axler:definition:1_20", "corpus": "AXLER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:matrix_lie_groups",
        "name": "Matrix Lie Groups (GL, SL, SO, SE)",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Classical matrix subgroups of GL(n) governing rotations, volume preservation, and rigid body kinematics",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational", "applied"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:matrix_lie_groups", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:11_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:7_1", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_3", "corpus": "VMLS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:2_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:lie_group_exponential_bch",
        "name": "Lie Group Exponential Map and Baker-Campbell-Hausdorff Formula",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Exponential mapping from Lie algebra to Lie group exp: g -> G and non-abelian product expansion via Lie brackets",
        "representation_kinds": ["abstract", "algebraic", "computational"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:matrix_exponential_map", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:thm:baker_campbell_hausdorff", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:diffgeom:def:adjoint_representation", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:14_3", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:diffgeom:homogeneous_spaces_actions",
        "name": "Homogeneous Spaces and Lie Group Actions",
        "domain": "Differential Geometry & Lie Groups",
        "description": "Smooth group actions on manifolds and transitive quotient homogeneous manifolds G/H",
        "representation_kinds": ["abstract", "geometric", "algebraic"],
        "alignments": [
            {"source": "srcdecl:diffgeom:def:homogeneous_space", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:37_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:axler:definition:3_99", "corpus": "AXLER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    }
]


# Existing canonical objects getting Source F alignments (expanding universal convergence to 6 sources!)
EXISTING_CANONICAL_ENRICHMENTS = [
    {
        "id": "canonical:topology:cauchy_schwarz_inequality",
        "alignments": [
            {"source": "srcdecl:diffgeom:def:riemannian_metric", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:topology:triangle_inequality",
        "alignments": [
            {"source": "srcdecl:diffgeom:def:geodesic_distance", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:topology:metric_space",
        "alignments": [
            {"source": "srcdecl:diffgeom:def:geodesic_distance", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:topology:normed_vector_space",
        "alignments": [
            {"source": "srcdecl:diffgeom:def:riemannian_metric", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:topology:compact_set",
        "alignments": [
            {"source": "srcdecl:diffgeom:thm:hopf_rinow_theorem", "corpus": "LEE", "status": "CROSS_SOURCE_SAME"}
        ]
    }
]


def load_v0_17_canonical_objects() -> list[dict]:
    v0_17_file = ROOT / "formal" / "cross_source_alignments_v0_17.json"
    data = json.loads(v0_17_file.read_text(encoding="utf-8"))
    return data.get("canonical_objects", [])


def merge_and_generate_v0_18_alignments() -> dict:
    prev_objects = load_v0_17_canonical_objects()
    by_id = {co["id"]: co for co in prev_objects}

    # Enrich existing canonical objects
    for enrich in EXISTING_CANONICAL_ENRICHMENTS:
        cid = enrich["id"]
        if cid in by_id:
            existing_sources = {al["source"] for al in by_id[cid]["alignments"]}
            for al in enrich["alignments"]:
                if al["source"] not in existing_sources:
                    by_id[cid]["alignments"].append(al)

    # Add new differential geometry canonical objects
    for dg_co in DIFFGEOM_CANONICAL_OBJECTS:
        if dg_co["id"] in by_id:
            existing = by_id[dg_co["id"]]
            existing_sources = {al["source"] for al in existing["alignments"]}
            for al in dg_co["alignments"]:
                if al["source"] not in existing_sources:
                    existing["alignments"].append(al)
        else:
            by_id[dg_co["id"]] = dg_co

    all_canonical = list(by_id.values())
    return {
        "schema_version": "v0.18",
        "description": "Curated Cross-Source Alignments spanning Gallier (S_A), Axler (S_B), VMLS (S_C), CVX (S_D), Billingsley (S_E), and Lee (S_F)",
        "total_canonical_objects": len(all_canonical),
        "canonical_objects": all_canonical,
    }


def main() -> int:
    out_path = ROOT / "formal" / "cross_source_alignments_v0_18.json"
    result = merge_and_generate_v0_18_alignments()
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Generated {len(result['canonical_objects'])} canonical alignments for v0.18 at {out_path}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
