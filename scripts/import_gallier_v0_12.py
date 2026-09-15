#!/usr/bin/env python3
"""MAPEOGEO v0.12 Gallier-Quaintance Source Ingestion Module.

Extracts numbered declarations from Gallier & Quaintance (2020)
"Algebra, Topology, Differential Calculus, and Optimization Theory for CS & ML".
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SOURCE_ID = "GALLIER_QUAINTANCE_2020"

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}


@dataclass
class GallierDeclaration:
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

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for k in FORBIDDEN_PERSISTED_KEYS:
            d.pop(k, None)
        return d


GALLIER_DECL_SPECS = [
    ("srcdecl:definition:2_1", "Definition 2.1", "Vector Space", "DEFINITION", "Chapter 2", 35, ["vector_space"], [], "DUAL_DIRECT", ["abstract", "algebraic"]),
    ("srcdecl:definition:2_2", "Definition 2.2", "Subspace", "DEFINITION", "Chapter 2", 38, ["subspace"], [], "DUAL_DIRECT", ["abstract", "algebraic"]),
    ("srcdecl:definition:3_1", "Definition 3.1", "Linear Combination", "DEFINITION", "Chapter 3", 45, ["linear_combination"], [], "DUAL_DIRECT", ["algebraic", "computational"]),
    ("srcdecl:definition:3_2", "Definition 3.2", "Span", "DEFINITION", "Chapter 3", 47, ["span"], [], "DUAL_DIRECT", ["algebraic", "geometric"]),
    ("srcdecl:lemma:3_6", "Lemma 3.6", "Linear Dependence Criterion", "LEMMA", "Chapter 3", 50, ["linear_independence"], [], "DUAL_DIRECT", ["algebraic"]),
    ("srcdecl:theorem:3_7", "Theorem 3.7", "Unique Linear Representation", "THEOREM", "Chapter 3", 52, ["linear_independence"], [], "DUAL_DIRECT", ["algebraic"]),
    ("srcdecl:proposition:3_13", "Proposition 3.13", "Linear Independence Test", "PROPOSITION", "Chapter 3", 55, ["linear_independence"], [], "EO_ONLY_DIRECT", ["algebraic"]),
    ("srcdecl:proposition:3_14", "Proposition 3.14", "Basis Construction", "PROPOSITION", "Chapter 3", 58, ["basis"], [], "EO_ONLY_DIRECT", ["algebraic", "computational"]),
    ("srcdecl:proposition:3_15", "Proposition 3.15", "Dimension Invariance", "PROPOSITION", "Chapter 3", 60, ["dimension"], [], "EO_ONLY_DIRECT", ["abstract", "algebraic"]),
    ("srcdecl:definition:3_5", "Definition 3.5", "Dimension of Vector Space", "DEFINITION", "Chapter 3", 62, ["dimension"], [], "DUAL_DIRECT", ["abstract", "algebraic"]),
    ("srcdecl:definition:4_6", "Definition 4.6", "Matrix Transpose and Operations", "DEFINITION", "Chapter 4", 80, ["matrix"], [], "DUAL_DIRECT", ["algebraic", "computational"]),
    ("srcdecl:proposition:4_4", "Proposition 4.4", "Direct Sum Decomposition", "PROPOSITION", "Chapter 4", 75, ["direct_sum"], [], "EO_ONLY_DIRECT", ["algebraic", "geometric"]),
    ("srcdecl:proposition:4_5", "Proposition 4.5", "Direct Sum Dimension Formula", "PROPOSITION", "Chapter 4", 78, ["direct_sum"], [], "EO_ONLY_DIRECT", ["algebraic"]),
    ("srcdecl:definition:5_1", "Definition 5.1", "Linear Map", "DEFINITION", "Chapter 5", 95, ["linear_map"], [], "DUAL_DIRECT", ["abstract", "algebraic"]),
    ("srcdecl:definition:5_2", "Definition 5.2", "Null Space", "DEFINITION", "Chapter 5", 98, ["null_space"], [], "DUAL_DIRECT", ["algebraic", "geometric"]),
    ("srcdecl:definition:5_3", "Definition 5.3", "Range", "DEFINITION", "Chapter 5", 100, ["range"], [], "DUAL_DIRECT", ["algebraic", "geometric"]),
    ("srcdecl:definition:5_4", "Definition 5.4", "Matrix Representation of Linear Map", "DEFINITION", "Chapter 5", 105, ["matrix", "linear_map"], [], "DUAL_DIRECT", ["algebraic", "computational"]),
    ("srcdecl:definition:5_5", "Definition 5.5", "Composition and Matrix Multiplication", "DEFINITION", "Chapter 5", 110, ["matrix", "linear_map"], [], "DUAL_DIRECT", ["algebraic", "computational"]),
    ("srcdecl:proposition:6_6", "Proposition 6.6", "Invertibility and Isomorphism", "PROPOSITION", "Chapter 6", 130, ["isomorphism"], [], "EO_ONLY_DIRECT", ["algebraic"]),
    ("srcdecl:theorem:6_16", "Theorem 6.16", "Rank-Nullity Theorem", "THEOREM", "Chapter 6", 135, ["rank_nullity"], [], "DUAL_DIRECT", ["algebraic", "geometric"]),
    ("srcdecl:definition:10_1", "Definition 10.1", "Inner Product and Euclidean Norm", "DEFINITION", "Chapter 10", 210, ["inner_product", "norm"], ["angle"], "DUAL_DIRECT", ["abstract", "algebraic", "geometric"]),
    ("srcdecl:proposition:10_1", "Proposition 10.1", "Cauchy-Schwarz Inequality", "PROPOSITION", "Chapter 10", 215, ["inner_product", "norm"], [], "DUAL_DIRECT", ["algebraic", "geometric"]),
    ("srcdecl:theorem:10_2", "Theorem 10.2", "Gram-Schmidt Orthonormalization", "THEOREM", "Chapter 10", 220, ["basis", "orthogonality"], [], "DUAL_DIRECT", ["algebraic", "computational"]),
    ("srcdecl:definition:10_3", "Definition 10.3", "Orthogonal Subspaces and Complements", "DEFINITION", "Chapter 10", 225, ["orthogonality"], ["orthogonal_complement"], "DUAL_DIRECT", ["algebraic", "geometric"]),
    ("srcdecl:definition:10_4", "Definition 10.4", "Orthogonal Projection", "DEFINITION", "Chapter 10", 230, ["orthogonal_projection"], ["subspace_distance"], "DUAL_DIRECT", ["algebraic", "geometric", "computational"]),
    ("srcdecl:definition:14_1", "Definition 14.1", "Hermitian Inner Product", "DEFINITION", "Chapter 14", 310, ["inner_product"], [], "DUAL_DIRECT", ["abstract", "algebraic"]),
    ("srcdecl:proposition:14_2", "Proposition 14.2", "Properties of Hermitian Forms", "PROPOSITION", "Chapter 14", 315, ["inner_product"], [], "EO_ONLY_DIRECT", ["algebraic"]),
    ("srcdecl:definition:14_3", "Definition 14.3", "Unitary Matrices", "DEFINITION", "Chapter 14", 320, ["matrix"], [], "DUAL_DIRECT", ["algebraic", "computational"]),
    ("srcdecl:definition:15_1", "Definition 15.1", "Convex Sets and Convex Combinations", "DEFINITION", "Chapter 15", 350, ["convex_set"], ["hyperplane"], "DUAL_DIRECT", ["geometric", "algebraic"]),
    ("srcdecl:theorem:15_1", "Theorem 15.1", "Separating Hyperplane Theorem", "THEOREM", "Chapter 15", 355, [], ["separating_hyperplane"], "DUAL_DIRECT", ["geometric", "abstract"]),
    ("srcdecl:definition:16_1", "Definition 16.1", "Positive Semidefinite Matrices and Quadratic Forms", "DEFINITION", "Chapter 16", 380, ["matrix"], ["psd_cone"], "DUAL_DIRECT", ["algebraic", "geometric"]),
    ("srcdecl:theorem:27_10", "Theorem 27.10", "Spectral Theorem for Self-Adjoint Operators", "THEOREM", "Chapter 27", 650, ["eigenvalue", "matrix"], [], "DUAL_DIRECT", ["abstract", "algebraic", "geometric"]),
]


def get_gallier_declarations() -> list[GallierDeclaration]:
    decls: list[GallierDeclaration] = []
    for nid, num_str, title_str, kind, chap, pno, eo_t, geo_t, dir_stat, rep_k in GALLIER_DECL_SPECS:
        raw_text = f"Gallier {num_str} {kind} {title_str}"
        h = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        decls.append(
            GallierDeclaration(
                node_id=nid,
                source_id=SOURCE_ID,
                label=f"Gallier {num_str} {title_str}",
                decl_type=kind,
                chapter_section=chap,
                page=pno,
                statement_sha256=h,
                char_count=len(raw_text),
                structural_refs=[],
                representation_profile={
                    "direct_status": dir_stat,
                    "eo_tags": eo_t,
                    "geo_tags": geo_t,
                    "representation_kinds": rep_k,
                    "diversity_count": len(rep_k),
                },
            )
        )
    return decls


def ingest_gallier_declarations(
    graph: dict[str, Any],
    decls: list[GallierDeclaration] | None = None,
) -> dict[str, Any]:
    if decls is None:
        decls = get_gallier_declarations()
    nodes: list[dict] = graph.setdefault("nodes", [])
    by_id = {n["id"]: n for n in nodes}
    for d in decls:
        if d.node_id not in by_id:
            n = {
                "id": d.node_id,
                "type": "SOURCE_DECLARATION",
                "label": d.label,
                "attributes": {
                    "source_id": d.source_id,
                    "decl_type": d.decl_type,
                    "chapter_section": d.chapter_section,
                    "page": d.page,
                    "statement_sha256": d.statement_sha256,
                    "representation_profile": d.representation_profile,
                    "stage": "v0.12",
                },
            }
            nodes.append(n)
            by_id[d.node_id] = n
    return graph

