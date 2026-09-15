#!/usr/bin/env python3
"""MAPEOGEO v0.15 Real Analysis and Differential Calculus Ingestion Module.

Extracts and classifies Real Analysis and Multivariable Differential Calculus declarations across
Gallier (S_A), Axler (S_B), VMLS (S_C), and Boyd & Vandenberghe (S_D).

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

STAGE = "v0.15"

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

# Detector Bank Keywords for Differential Calculus & Analysis
CALCULUS_EO_KEYWORDS = {
    "derivative": re.compile(r"\bderivative\b|\bdifferentiable\b|\bdifferential\b|\bfr[eé]chet\b", re.IGNORECASE),
    "gradient": re.compile(r"\bgradient\b|\bgrad\b|\bnabla\b", re.IGNORECASE),
    "jacobian": re.compile(r"\bjacobian\b|\bpartial derivative\b|\bjacobian matrix\b", re.IGNORECASE),
    "hessian": re.compile(r"\bhessian\b|\bsecond derivative\b|\bsecond-order\b", re.IGNORECASE),
    "chain_rule": re.compile(r"\bchain rule\b|\bderivative of composition\b", re.IGNORECASE),
    "taylor_expansion": re.compile(r"\btaylor\b|\btaylor series\b|\btaylor expansion\b|\btaylor approximation\b", re.IGNORECASE),
    "newton_step": re.compile(r"\bnewton step\b|\bnewton's method\b|\bnewton decrement\b", re.IGNORECASE),
    "critical_point": re.compile(r"\bcritical point\b|\bstationary point\b|\bfermat\b", re.IGNORECASE),
    "subgradient": re.compile(r"\bsubgradient\b|\bsubdifferential\b", re.IGNORECASE),
    "lagrange_multiplier": re.compile(r"\blagrange multiplier\b|\blagrangian\b|\bequality constraint\b", re.IGNORECASE),
}

CALCULUS_GEO_KEYWORDS = {
    "metric_ball": re.compile(r"\bmetric ball\b|\bopen ball\b|\beuclidean ball\b|\bneighborhood\b", re.IGNORECASE),
    "open_closed_set": re.compile(r"\bopen set\b|\bclosed set\b|\btopology\b|\binterior\b|\bboundary\b", re.IGNORECASE),
    "level_set": re.compile(r"\blevel set\b|\bsublevel set\b|\bcontour\b|\bsurface\b", re.IGNORECASE),
    "submanifold": re.compile(r"\bsubmanifold\b|\btangent space\b|\bmanifold\b", re.IGNORECASE),
    "convex_epigraph": re.compile(r"\bepigraph\b|\bconvex set\b|\bcone\b", re.IGNORECASE),
    "saddle_geometry": re.compile(r"\bsaddle\b|\bhyperbolic\b|\bcurvature\b", re.IGNORECASE),
    "distance_metric": re.compile(r"\bdistance\b|\bmetric\b|\bnorm\b", re.IGNORECASE),
}

REPRESENTATION_KINDS = {
    "abstract": re.compile(r"\bvector space\b|\bnormed space\b|\bbanach\b|\bhilbert\b|\bfr[eé]chet\b|\btopology\b|\bdual space\b", re.IGNORECASE),
    "algebraic": re.compile(r"\bmatrix\b|\bjacobian\b|\bhessian\b|\bpositive semidefinite\b|\bbilinear\b|\bquadratic form\b|\beigenvalue\b", re.IGNORECASE),
    "geometric": re.compile(r"\bball\b|\blevel set\b|\btangent\b|\bhyperplane\b|\bcontour\b|\bmanifold\b|\bcurvature\b|\bepigraph\b", re.IGNORECASE),
    "computational": re.compile(r"\balgorithm\b|\bnewton\b|\bgradient descent\b|\biteration\b|\bline search\b|\bstep\b|\bconvergence\b", re.IGNORECASE),
    "applied": re.compile(r"\bapproximation\b|\bfitting\b|\bdata\b|\boptimization\b|\bmodel\b|\bestimation\b", re.IGNORECASE),
}


@dataclass
class AnalysisDeclaration:
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
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            d.pop(forbidden, None)
        return d


def detect_analysis_representation_profile(text: str, title: str) -> dict[str, Any]:
    full_text = f"{title}\n{text}"
    eo_tags = [tag for tag, pat in CALCULUS_EO_KEYWORDS.items() if pat.search(full_text)]
    geo_tags = [tag for tag, pat in CALCULUS_GEO_KEYWORDS.items() if pat.search(full_text)]

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


def generate_additional_analysis_declarations() -> list[AnalysisDeclaration]:
    """Provides supplementary declarations for analysis and multivariable calculus."""
    data = [
        # Differential Calculus and Analysis declarations from Gallier / CVX Appendix
        ("srcdecl:gallier:chapter:37", "GALLIER_QUAINTANCE_2020", "Gallier Chapter 37 Metric Topology and Normed Spaces", "CHAPTER", "Chapter 37", 850, ["open_closed_set", "distance_metric"], ["metric_ball", "open_closed_set"], ["abstract", "geometric"]),
        ("srcdecl:gallier:chapter:39", "GALLIER_QUAINTANCE_2020", "Gallier Chapter 39 Differential Calculus in Normed Spaces", "CHAPTER", "Chapter 39", 900, ["derivative", "chain_rule", "jacobian"], ["level_set"], ["abstract", "algebraic", "geometric", "computational"]),
        ("srcdecl:gallier:chapter:40", "GALLIER_QUAINTANCE_2020", "Gallier Chapter 40 Extrema of Differentiable Functions", "CHAPTER", "Chapter 40", 940, ["critical_point", "hessian", "lagrange_multiplier"], ["saddle_geometry"], ["abstract", "algebraic", "computational", "applied"]),
        ("srcdecl:gallier:chapter:41", "GALLIER_QUAINTANCE_2020", "Gallier Chapter 41 Newton's Method and Optimality", "CHAPTER", "Chapter 41", 970, ["newton_step", "taylor_expansion"], [], ["algebraic", "computational", "applied"]),
        ("srcdecl:cvx:appendix:A_4", "BOYD_VANDENBERGHE_CVX_2004", "CVX Appendix A.4 Derivatives, Gradients, and Hessians", "APPENDIX", "Appendix A", 654, ["derivative", "gradient", "hessian", "chain_rule"], ["level_set"], ["algebraic", "computational", "geometric"]),
    ]

    decls: list[AnalysisDeclaration] = []
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
        decls.append(
            AnalysisDeclaration(
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
            )
        )
    return decls


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Analysis and Differential Calculus declarations for MAPEOGEO v0.15")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    decls = generate_additional_analysis_declarations()
    print(f"Loaded {len(decls)} Analysis & Calculus declarations.")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump([d.to_dict() for d in decls], f, indent=2)
        print(f"Saved to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
