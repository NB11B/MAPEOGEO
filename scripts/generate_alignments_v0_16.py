#!/usr/bin/env python3
"""Generate curated cross-source alignments for MAPEOGEO v0.16 Topology Expansion."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TOPOLOGY_CANONICAL_OBJECTS = [
    {
        "id": "canonical:topology:metric_space",
        "name": "Metric Space",
        "domain": "Topology & Metric Spaces",
        "description": "Set endowed with a distance function satisfying non-negativity, identity of indiscernibles, symmetry, and the triangle inequality",
        "representation_kinds": ["abstract", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:definition:37_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:6_7", "corpus": "AXLER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:vmls:section:3_2", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:normed_vector_space",
        "name": "Normed Vector Space",
        "domain": "Topology & Metric Spaces",
        "description": "Vector space equipped with a subadditive, absolutely homogeneous, positive-definite norm inducing a metric",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:definition:9_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:37_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:6_7", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_9", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:inner_product_space",
        "name": "Inner Product Space / Pre-Hilbert Space",
        "domain": "Topology & Metric Spaces",
        "description": "Vector space with a positive-definite conjugate-symmetric sesquilinear form inducing a Euclidean/Hermitian norm",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:definition:14_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:48_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:6_4", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_6", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_4", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:banach_space",
        "name": "Banach Space",
        "domain": "Topology & Metric Spaces",
        "description": "Complete normed vector space in which every Cauchy sequence converges to a limit in the space",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_16", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:37_62", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:37_63", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:hilbert_space",
        "name": "Hilbert Space",
        "domain": "Topology & Metric Spaces",
        "description": "Complete inner product space exhibiting full geometric orthogonality and projection properties",
        "representation_kinds": ["abstract", "algebraic", "geometric", "formal"],
        "formal_decl": "MAPEOGEOFormal.proposition_4_4_v011",
        "alignments": [
            {"source": "srcdecl:definition:48_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:48_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:gallier:chapter:48", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:axler:definition:6_4", "corpus": "AXLER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:topological_space",
        "name": "Topological Space",
        "domain": "Topology & Metric Spaces",
        "description": "Pair of a set and a collection of open sets closed under arbitrary unions and finite intersections",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_3", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:open_ball",
        "name": "Open Metric Ball",
        "domain": "Topology & Metric Spaces",
        "description": "Set of points strictly within distance r from center x_0, forming a canonical basis for metric topology",
        "representation_kinds": ["abstract", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:definition:37_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:vmls:section:3_2", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:closed_ball",
        "name": "Closed Metric Ball / Norm Ball",
        "domain": "Topology & Metric Spaces",
        "description": "Set of points within distance r or norm bounded by r, forming a closed convex set in normed spaces",
        "representation_kinds": ["abstract", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:definition:37_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:6_7", "corpus": "AXLER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:neighborhood",
        "name": "Neighborhood of a Point",
        "domain": "Topology & Metric Spaces",
        "description": "Subset containing an open set containing the point x, defining local topological behavior",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_4", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:interior",
        "name": "Interior of a Set",
        "domain": "Topology & Metric Spaces",
        "description": "Union of all open subsets of S, constituting the largest open set contained within S",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_3", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_5", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:closure",
        "name": "Closure of a Set",
        "domain": "Topology & Metric Spaces",
        "description": "Intersection of all closed supersets of S, constituting the smallest closed set containing S",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_3", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_6", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:boundary",
        "name": "Boundary of a Set",
        "domain": "Topology & Metric Spaces",
        "description": "Set difference between closure and interior of S, containing all frontier points",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_3", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_6", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:relative_interior",
        "name": "Relative Interior",
        "domain": "Topology & Metric Spaces",
        "description": "Interior of a convex set relative to its affine hull, avoiding empty interiors in lower-dimensional embeddings",
        "representation_kinds": ["abstract", "geometric", "applied"],
        "alignments": [
            {"source": "srcdecl:definition:44_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:2_1", "corpus": "CVX", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:cauchy_sequence",
        "name": "Cauchy Sequence",
        "domain": "Topology & Metric Spaces",
        "description": "Sequence whose elements become arbitrarily close to each other as index grows without bound",
        "representation_kinds": ["abstract", "computational"],
        "alignments": [
            {"source": "srcdecl:definition:37_10", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_48", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:completeness",
        "name": "Metric Completeness",
        "domain": "Topology & Metric Spaces",
        "description": "Property that every Cauchy sequence in the space has a limit that belongs to the space",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_10", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:37_49", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:48_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:compact_set",
        "name": "Compact Set / Space",
        "domain": "Topology & Metric Spaces",
        "description": "Topological space/set where every open cover admits a finite subcover",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_7", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_24", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_28", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:sequential_compactness",
        "name": "Sequential Compactness",
        "domain": "Topology & Metric Spaces",
        "description": "Property that every sequence contains a convergent subsequence, equivalent to compactness in metric spaces",
        "representation_kinds": ["abstract", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:proposition:37_42", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_43", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:37_47", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:heine_borel_theorem",
        "name": "Heine-Borel Theorem",
        "domain": "Topology & Metric Spaces",
        "description": "A subset of Euclidean space R^n is compact if and only if it is closed and bounded",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:proposition:37_25", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_26", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:weierstrass_extreme_value_theorem",
        "name": "Weierstrass Extreme Value Theorem",
        "domain": "Topology & Metric Spaces",
        "description": "Continuous real-valued function defined on a compact topological space attains its global minimum and maximum",
        "representation_kinds": ["abstract", "geometric", "computational", "applied"],
        "alignments": [
            {"source": "srcdecl:proposition:37_32", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:section:11_9", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:connected_space",
        "name": "Connected Topological Space",
        "domain": "Topology & Metric Spaces",
        "description": "Topological space that cannot be represented as the disjoint union of two non-empty open sets",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_6", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_16", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_18", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:topology:path_connected_space",
        "name": "Path-Connected Space",
        "domain": "Topology & Metric Spaces",
        "description": "Topological space where every pair of points can be joined by a continuous path",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_8", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:37_23", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:topology:continuous_function",
        "name": "Continuous Map / Function",
        "domain": "Topology & Metric Spaces",
        "description": "Map between topological spaces where preimage of every open set is open, with epsilon-delta equivalence in metric spaces",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_4", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_9", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_10", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:uniform_continuity",
        "name": "Uniform Continuity",
        "domain": "Topology & Metric Spaces",
        "description": "Continuity condition where delta depends only on epsilon and holds uniformly over the entire domain",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_9", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:37_45", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:homeomorphism",
        "name": "Homeomorphism",
        "domain": "Topology & Metric Spaces",
        "description": "Continuous bijection with continuous inverse, establishing topological isomorphism",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_4", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_33", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:topology:bounded_linear_operator",
        "name": "Bounded Linear Operator",
        "domain": "Topology & Metric Spaces",
        "description": "Linear operator between normed spaces with bounded operator norm, equivalent to continuity",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_13", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_56", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:37_58", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:7_1", "corpus": "AXLER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:operator_norm",
        "name": "Operator Norm / Induced Matrix Norm",
        "domain": "Topology & Metric Spaces",
        "description": "Supremum norm of operator action on the unit sphere, satisfying submultiplicativity",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:definition:9_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:9_6", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:9_8", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_56", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:7_20", "corpus": "AXLER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:vmls:section:6_3", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:dual_norm",
        "name": "Dual Norm",
        "domain": "Topology & Metric Spaces",
        "description": "Norm defined on linear functionals as supremum over the primal unit ball",
        "representation_kinds": ["abstract", "algebraic", "geometric", "applied"],
        "alignments": [
            {"source": "srcdecl:definition:11_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:9_8", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:section:6_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:banach_fixed_point_theorem",
        "name": "Banach Fixed Point Theorem",
        "domain": "Topology & Metric Spaces",
        "description": "Contraction mapping on a complete metric space possesses a unique fixed point computable via Picard iteration",
        "representation_kinds": ["abstract", "computational", "applied"],
        "alignments": [
            {"source": "srcdecl:definition:37_12", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_54", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:37_55", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_3", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:orthogonal_projection_theorem",
        "name": "Orthogonal Projection Theorem on Closed Convex Sets",
        "domain": "Topology & Metric Spaces",
        "description": "Existence and uniqueness of distance-minimizing projection onto nonempty closed convex subsets and subspaces of Hilbert spaces",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:proposition:48_5", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:48_6", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:48_7", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:6_55", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_57", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:12_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:section:8_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:riesz_representation_theorem",
        "name": "Riesz Representation Theorem",
        "domain": "Topology & Metric Spaces",
        "description": "Every continuous linear functional on a Hilbert space is uniquely represented as an inner product with a fixed vector",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:corollary:48_8", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:48_9", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_42", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_58", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_5", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:cauchy_schwarz_inequality",
        "name": "Cauchy-Schwarz Inequality",
        "domain": "Topology & Metric Spaces",
        "description": "Fundamental inner product bound |<u, v>| <= ||u|| ||v|| governing metric geometry and angles",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:proposition:14_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_14", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_4", "corpus": "VMLS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:triangle_inequality",
        "name": "Triangle Inequality",
        "domain": "Topology & Metric Spaces",
        "description": "Metric and norm subadditivity condition ||u + v|| <= ||u|| + ||v|| and d(x, z) <= d(x, y) + d(y, z)",
        "representation_kinds": ["abstract", "algebraic", "geometric", "computational"],
        "alignments": [
            {"source": "srcdecl:definition:37_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:definition:9_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_17", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:3_1", "corpus": "VMLS", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:parallelogram_identity",
        "name": "Parallelogram Identity",
        "domain": "Topology & Metric Spaces",
        "description": "Geometric identity ||u + v||^2 + ||u - v||^2 = 2||u||^2 + 2||v||^2 characterizing inner product induced norms",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:theorem:48_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:48_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_17", "corpus": "AXLER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:finite_dimensional_norm_equivalence",
        "name": "Equivalence of Norms in Finite Dimensions",
        "domain": "Topology & Metric Spaces",
        "description": "All norms on a finite-dimensional real or complex vector space induce identical topologies",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:corollary:9_4", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:9_5", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:theorem:37_58", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_1", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:subspace_topology",
        "name": "Subspace / Relative Topology",
        "domain": "Topology & Metric Spaces",
        "description": "Topology induced on a subset S consisting of intersections of open sets with S",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_8", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:product_topology",
        "name": "Product Topology",
        "domain": "Topology & Metric Spaces",
        "description": "Coarsest topology on Cartesian product making canonical projection maps continuous",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_7", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_2", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:hausdorff_space",
        "name": "Hausdorff / T_2 Separation Space",
        "domain": "Topology & Metric Spaces",
        "description": "Topological space where distinct points admit disjoint open neighborhoods, ensuring uniqueness of limits",
        "representation_kinds": ["abstract", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:37_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_3", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_26", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:37_27", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:topology:sublevel_set_compactness",
        "name": "Sublevel Set Compactness",
        "domain": "Topology & Metric Spaces",
        "description": "Compactness of lower sublevel sets for coercive continuous and convex functions, guaranteeing existence of minimizers",
        "representation_kinds": ["abstract", "geometric", "applied"],
        "alignments": [
            {"source": "srcdecl:proposition:40_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:appendix:A_3", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:section:11_9", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:dual_cone",
        "name": "Dual Cone Closedness and Properties",
        "domain": "Topology & Metric Spaces",
        "description": "Set of non-negative dual pairing vectors forming a closed convex cone regardless of primal cone topology",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:44_1", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:section:2_6", "corpus": "CVX", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:appendix:A_5", "corpus": "CVX", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    },
    {
        "id": "canonical:topology:separating_hyperplane_theorem",
        "name": "Separating Hyperplane Theorem",
        "domain": "Topology & Metric Spaces",
        "description": "Topological separation of disjoint nonempty convex sets by an affine hyperplane",
        "representation_kinds": ["abstract", "geometric", "algebraic"],
        "alignments": [
            {"source": "srcdecl:theorem:48_12", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:cvx:section:2_5", "corpus": "CVX", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:topology:supporting_hyperplane_theorem",
        "name": "Supporting Hyperplane Theorem",
        "domain": "Topology & Metric Spaces",
        "description": "Existence of a supporting hyperplane containing any boundary point of a closed convex set",
        "representation_kinds": ["abstract", "geometric", "algebraic"],
        "alignments": [
            {"source": "srcdecl:theorem:48_12", "corpus": "GALLIER", "status": "CROSS_SOURCE_SCOPED_OVERLAP"},
            {"source": "srcdecl:cvx:section:2_5", "corpus": "CVX", "status": "CROSS_SOURCE_SAME"}
        ]
    },
    {
        "id": "canonical:topology:orthogonal_complement",
        "name": "Orthogonal Complement",
        "domain": "Topology & Metric Spaces",
        "description": "Closed subspace of vectors orthogonal to a given subset in an inner product or Hilbert space",
        "representation_kinds": ["abstract", "algebraic", "geometric"],
        "alignments": [
            {"source": "srcdecl:definition:14_2", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:proposition:48_7", "corpus": "GALLIER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:definition:6_46", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_48", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:axler:theorem:6_49", "corpus": "AXLER", "status": "CROSS_SOURCE_SAME"},
            {"source": "srcdecl:vmls:section:5_3", "corpus": "VMLS", "status": "CROSS_SOURCE_SCOPED_OVERLAP"}
        ]
    }
]


def generate_alignments_v0_16():
    base_alignments_path = ROOT / "formal" / "analysis_alignments_v0_15.json"
    base_data = json.loads(base_alignments_path.read_text(encoding="utf-8"))

    existing_objects = base_data.get("canonical_objects", [])
    existing_ids = {co["id"] for co in existing_objects}

    combined_objects = list(existing_objects)
    for to in TOPOLOGY_CANONICAL_OBJECTS:
        if to["id"] not in existing_ids:
            combined_objects.append(to)
            existing_ids.add(to["id"])

    out_data = {
        "schema_version": "0.16",
        "stage": "v0.16",
        "description": "Canonical mathematical objects and cross-source alignments for Topology, Metric Spaces, and Functional Structure expansion",
        "canonical_objects": combined_objects,
    }

    out_path = ROOT / "formal" / "cross_source_alignments_v0_16.json"
    out_path.write_text(json.dumps(out_data, indent=2), encoding="utf-8")
    print(f"Generated {len(combined_objects)} canonical objects in {out_path}")
    print(f"  - Prior objects: {len(existing_objects)}")
    print(f"  - New topology objects: {len(TOPOLOGY_CANONICAL_OBJECTS)}")


if __name__ == "__main__":
    generate_alignments_v0_16()
