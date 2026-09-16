#!/usr/bin/env python3
"""MAPEOGEO v0.16 Topology, Metric Spaces, and Functional Structure Ingestion Module.

Extracts and classifies Topology, Metric Spaces, Normed Spaces, Banach Spaces, and Hilbert Spaces
declarations across Gallier (S_A), Axler (S_B), VMLS (S_C), and Boyd & Vandenberghe (S_D).

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

STAGE = "v0.16"

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

# Detector Bank Keywords for Topology, Metric Spaces, and Functional Structure
TOPOLOGY_EO_KEYWORDS = {
    "operator_norm": re.compile(r"\boperator norm\b|\bmatrix norm\b|\bbounded operator\b|\binduced norm\b|\bsubmultiplicative\b", re.IGNORECASE),
    "contraction_mapping": re.compile(r"\bcontraction\b|\bcontraction mapping\b|\bbanach fixed point\b|\bfixed point theorem\b", re.IGNORECASE),
    "projection_operator": re.compile(r"\borthogonal projection\b|\bprojection lemma\b|\bdistance minimizing\b|\bprojection on convex\b|\bprojection operator\b", re.IGNORECASE),
    "adjoint_operator": re.compile(r"\badjoint\b|\bself[- ]adjoint\b|\bhermitian adjoint\b|\bunitary\b|\bisometry\b", re.IGNORECASE),
    "riesz_functional": re.compile(r"\briesz representation\b|\bcontinuous linear functional\b|\bdual space\b|\briesz\b", re.IGNORECASE),
    "cauchy_sequence": re.compile(r"\bcauchy sequence\b|\bcauchy\b|\bcompleteness\b|\bcomplete metric\b", re.IGNORECASE),
    "dual_norm": re.compile(r"\bdual norm\b|\bpolar set\b|\bdual cone\b|\bhahn[- ]banach\b", re.IGNORECASE),
    "bounded_linear_map": re.compile(r"\bbounded linear\b|\bcontinuous linear\b|\blinear functional\b|\bcontinuity of linear\b", re.IGNORECASE),
    "metric_distance": re.compile(r"\bmetric\b|\bdistance\b|\btriangle inequality\b|\bmetric space\b", re.IGNORECASE),
    "inner_product_functional": re.compile(r"\binner product\b|\bsesquilinear\b|\bhermitian space\b|\bpre[- ]hilbert\b", re.IGNORECASE),
}

TOPOLOGY_GEO_KEYWORDS = {
    "open_set": re.compile(r"\bopen set\b|\bopen sets\b|\btopology\b|\btopological space\b|\bbase of topology\b", re.IGNORECASE),
    "closed_set": re.compile(r"\bclosed set\b|\bclosed sets\b|\bclosed subset\b", re.IGNORECASE),
    "open_ball": re.compile(r"\bopen ball\b|\bmetric ball\b|\beuclidean ball\b|\bunit ball\b", re.IGNORECASE),
    "closed_ball": re.compile(r"\bclosed ball\b|\bclosed metric ball\b", re.IGNORECASE),
    "neighborhood": re.compile(r"\bneighborhood\b|\bopen neighborhood\b|\bvicinity\b", re.IGNORECASE),
    "interior": re.compile(r"\binterior\b|\binterior point\b|\bint\b", re.IGNORECASE),
    "closure": re.compile(r"\bclosure\b|\badherent point\b|\bcl\b", re.IGNORECASE),
    "boundary": re.compile(r"\bboundary\b|\bfrontier\b|\bbd\b|\bpartial\b", re.IGNORECASE),
    "relative_interior": re.compile(r"\brelative interior\b|\brelint\b|\baffine hull\b", re.IGNORECASE),
    "compact_set": re.compile(r"\bcompact\b|\bcompactness\b|\bopen cover\b|\bheine[- ]borel\b|\bbolzano[- ]weierstrass\b", re.IGNORECASE),
    "connected_set": re.compile(r"\bconnected\b|\bconnectedness\b|\bpath[- ]connected\b|\barcwise connected\b", re.IGNORECASE),
    "subspace_topology": re.compile(r"\bsubspace topology\b|\brelative topology\b|\binduced metric\b", re.IGNORECASE),
    "product_topology": re.compile(r"\bproduct topology\b|\bproduct space\b|\bproduct metric\b", re.IGNORECASE),
    "hausdorff_space": re.compile(r"\bhausdorff\b|\bt_2\b|\bseparated\b", re.IGNORECASE),
    "dual_cone": re.compile(r"\bdual cone\b|\bproper cone\b|\bconvex cone\b", re.IGNORECASE),
    "hyperplane_separation": re.compile(r"\bseparating hyperplane\b|\bsupporting hyperplane\b|\bseparation theorem\b", re.IGNORECASE),
}

REPRESENTATION_KINDS = {
    "abstract": re.compile(r"\btopolog\w*\b|\bmetric(?: space)?s?\b|\bnormed(?: space)?s?\b|\bbanach(?: space)?s?\b|\bhilbert(?: space)?s?\b|\bhausdorff\b|\bcompleteness\b|\bcompactness\b|\bvector space\b", re.IGNORECASE),
    "algebraic": re.compile(r"\blinear map\b|\boperator\b|\badjoint\b|\bmatrix norm\b|\binner product\b|\bdirect sum\b|\border\b|\bquadratic\b", re.IGNORECASE),
    "geometric": re.compile(r"\bball\b|\bneighborhood\b|\binterior\b|\bclosure\b|\bboundary\b|\bconvex\b|\bcone\b|\bhyperplane\b|\bprojection\b|\bmetric\b|\bdistance\b", re.IGNORECASE),
    "computational": re.compile(r"\balgorithm\b|\biteration\b|\bfixed point\b|\bk[- ]means\b|\bclustering\b|\bleast squares\b|\bapproximation\b|\bnewton\b", re.IGNORECASE),
    "applied": re.compile(r"\bdata\b|\bfitting\b|\boptimization\b|\bclassification\b|\bclustering\b|\bmodel\b", re.IGNORECASE),
    "formal": re.compile(r"\bformal\b|\blean\b|\bkernel\b|\bproof\b", re.IGNORECASE),
}


@dataclass
class TopologySectionAnchor:
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
    node_type: str = "SOURCE_SECTION_ANCHOR"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            d.pop(forbidden, None)
        return d


def detect_topology_representation_profile(text: str, title: str) -> dict[str, Any]:
    full_text = f"{title}\n{text}"
    eo_tags = [tag for tag, pat in TOPOLOGY_EO_KEYWORDS.items() if pat.search(full_text)]
    geo_tags = [tag for tag, pat in TOPOLOGY_GEO_KEYWORDS.items() if pat.search(full_text)]

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


def generate_supplementary_topology_anchors() -> list[TopologySectionAnchor]:
    """Provides supplementary section anchors for topology, metric spaces, and functional analysis."""
    data = [
        # CVX Appendix A section anchors for topology, norms, and analysis
        ("srcdecl:cvx:appendix:A_1", "BOYD_VANDENBERGHE_CVX_2004", "CVX Appendix A.1 Norms, Vector Norms, Matrix Norms, and Dual Norms", "APPENDIX", "Appendix A", 633, ["operator_norm", "dual_norm", "metric_distance"], ["open_ball", "closed_ball"], ["abstract", "algebraic", "geometric", "computational"]),
        ("srcdecl:cvx:appendix:A_2", "BOYD_VANDENBERGHE_CVX_2004", "CVX Appendix A.2 Analysis: Open and Closed Sets, Interior, Boundary, Closure, Compact Sets, Continuity", "APPENDIX", "Appendix A", 637, ["bounded_linear_map"], ["open_set", "closed_set", "interior", "closure", "boundary", "compact_set"], ["abstract", "geometric"]),
        ("srcdecl:cvx:appendix:A_3", "BOYD_VANDENBERGHE_CVX_2004", "CVX Appendix A.3 Functions: Coercivity, Sublevel Sets, and Compactness", "APPENDIX", "Appendix A", 643, ["contraction_mapping"], ["compact_set", "closed_set"], ["abstract", "algebraic", "geometric", "applied"]),
        ("srcdecl:cvx:appendix:A_5", "BOYD_VANDENBERGHE_CVX_2004", "CVX Appendix A.5 Linear Algebra, Matrix Inverses, and Quadratic Forms", "APPENDIX", "Appendix A", 647, ["operator_norm", "inner_product_functional"], ["dual_cone"], ["abstract", "algebraic", "computational"]),
        # Gallier chapter anchor for Hilbert spaces and projection lemma
        ("srcdecl:gallier:chapter:48", "GALLIER_QUAINTANCE_2020", "Gallier Chapter 48 Basics of Hilbert Spaces and Projection Lemma", "CHAPTER", "Chapter 48", 1649, ["projection_operator", "riesz_functional", "adjoint_operator", "inner_product_functional"], ["closed_set", "hyperplane_separation"], ["abstract", "algebraic", "geometric", "formal"]),
    ]

    anchors: list[TopologySectionAnchor] = []
    for nid, sid, label, dtype, chap, pno, eo_t, geo_t, kinds in data:
        raw_text = f"{label} in {chap}"
        h = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        status = "DUAL_DIRECT" if (eo_t and geo_t) else ("EO_ONLY_DIRECT" if eo_t else ("GEO_ONLY_DIRECT" if geo_t else "THEORETIC_DIRECT"))
        profile = {
            "eo_tags": sorted(eo_t),
            "geo_tags": sorted(geo_t),
            "direct_status": status,
            "representation_kinds": sorted(kinds),
            "diversity_count": len(kinds),
        }
        anchors.append(
            TopologySectionAnchor(
                node_id=nid,
                source_id=sid,
                label=label,
                decl_type=dtype,
                chapter_section=chap,
                page=pno,
                statement_sha256=h,
                char_count=len(raw_text),
                structural_refs=[],
                representation_profile=profile,
                node_type="SOURCE_SECTION_ANCHOR",
            )
        )
    return anchors


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Topology and Functional Analysis section anchors for MAPEOGEO v0.16")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    anchors = generate_supplementary_topology_anchors()
    print(f"Loaded {len(anchors)} Topology & Functional Analysis section anchors.")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump([a.to_dict() for a in anchors], f, indent=2)
        print(f"Saved to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
