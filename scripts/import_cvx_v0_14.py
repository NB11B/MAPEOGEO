#!/usr/bin/env python3
"""MAPEOGEO v0.14 Convex Optimization (Boyd & Vandenberghe) Source Ingestion Module.

Extracts numbered sections, definitions, and algorithms from Stephen Boyd and Lieven Vandenberghe's
"Convex Optimization" (Cambridge University Press, 2004) for the v0.14 quad-source mathematical expansion.

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
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SOURCE_ID = "BOYD_VANDENBERGHE_CVX_2004"
CVX_URL = "https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf"
DEFAULT_CACHE_PATH = ROOT / "data" / "sources" / "bv_cvxbook.pdf"

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

# Detector Bank Keywords for Executable Operator (EO) and Geometric Object (GEO) candidate views
EO_KEYWORDS = {
    "affine_combination": re.compile(r"\baffine combination\b|\baffine set\b|\baffine function\b", re.IGNORECASE),
    "convex_combination": re.compile(r"\bconvex combination\b|\bconvex combination of\b", re.IGNORECASE),
    "convex_function": re.compile(r"\bconvex function\b|\bquasiconvex\b|\bconvexity\b|\bepigraph\b", re.IGNORECASE),
    "linear_program": re.compile(r"\blinear program\b|\blinear programming\b|\bLP\b", re.IGNORECASE),
    "quadratic_program": re.compile(r"\bquadratic program\b|\bquadratic programming\b|\bQP\b|\bQCQP\b", re.IGNORECASE),
    "semidefinite_program": re.compile(r"\bsemidefinite program\b|\bsemidefinite programming\b|\bSDP\b|\bLMI\b", re.IGNORECASE),
    "lagrangian": re.compile(r"\blagrangian\b|\blagrange multiplier\b|\blagrange dual\b", re.IGNORECASE),
    "dual_problem": re.compile(r"\bdual problem\b|\bduality\b|\bweak duality\b|\bstrong duality\b|\bslater\b", re.IGNORECASE),
    "kkt_conditions": re.compile(r"\bkkt\b|\bkarush[-]?kuhn[-]?tucker\b|\boptimality conditions\b", re.IGNORECASE),
    "interior_point": re.compile(r"\binterior[-]?point\b|\bbarrier method\b|\bcentral path\b", re.IGNORECASE),
    "newton_method": re.compile(r"\bnewton's method\b|\bnewton step\b|\bgradient descent\b", re.IGNORECASE),
    "subgradient": re.compile(r"\bsubgradient\b|\bsubdifferential\b", re.IGNORECASE),
    "least_squares_cvx": re.compile(r"\bleast[-]?squares\b|\bregularized least squares\b", re.IGNORECASE),
    "ellipsoid_method": re.compile(r"\bellipsoid method\b|\bcutting plane\b", re.IGNORECASE),
    "matrix_inequality": re.compile(r"\bmatrix inequality\b|\bpositive semidefinite\b|\bPSD\b|\bcone of positive\b", re.IGNORECASE),
    "fenchel_conjugate": re.compile(r"\bconjugate function\b|\bfenchel conjugate\b|\blegendre\b", re.IGNORECASE),
}

GEO_KEYWORDS = {
    "hyperplane": re.compile(r"\bhyperplane\b|\baffine subspace\b", re.IGNORECASE),
    "halfspace": re.compile(r"\bhalfspace\b|\bhalfspaces\b", re.IGNORECASE),
    "polyhedron": re.compile(r"\bpolyhedron\b|\bpolyhedra\b|\bpolytope\b|\bsimplex\b", re.IGNORECASE),
    "convex_set": re.compile(r"\bconvex set\b|\bconvex sets\b|\bconvex hull\b", re.IGNORECASE),
    "cone": re.compile(r"\bcone\b|\bconvex cone\b|\bproper cone\b|\bgeneralized inequalities\b", re.IGNORECASE),
    "dual_cone": re.compile(r"\bdual cone\b|\bpolar cone\b", re.IGNORECASE),
    "separating_hyperplane": re.compile(r"\bseparating hyperplane\b|\bseparation theorem\b", re.IGNORECASE),
    "supporting_hyperplane": re.compile(r"\bsupporting hyperplane\b|\bsupport function\b", re.IGNORECASE),
    "ellipsoid": re.compile(r"\bellipsoid\b|\bellipsoids\b|\bloewner[-]?john\b", re.IGNORECASE),
    "projection_convex_set": re.compile(r"\bprojection onto\b|\bprojection on a convex\b|\bclosest point\b", re.IGNORECASE),
    "distance_to_set": re.compile(r"\bdistance to a set\b|\beuclidean distance\b|\bmetric\b", re.IGNORECASE),
    "norm_ball": re.compile(r"\bnorm ball\b|\bunit ball\b|\bellipsoidal\b", re.IGNORECASE),
    "analytic_center": re.compile(r"\banalytic center\b|\banalytic centering\b", re.IGNORECASE),
    "voronoi": re.compile(r"\bvoronoi\b|\bpolyhedral\b", re.IGNORECASE),
}

REPRESENTATION_KINDS = {
    "abstract": re.compile(r"\bvector space\b|\bdual space\b|\bproper cone\b|\bgeneralized inequality\b|\btopology\b|\binterior\b|\brelative interior\b", re.IGNORECASE),
    "algebraic": re.compile(r"\bmatrix\b|\bpositive semidefinite\b|\beigenvalue\b|\bschur complement\b|\bquadratic form\b|\btrace\b|\bdeterminant\b", re.IGNORECASE),
    "geometric": re.compile(r"\bhyperplane\b|\bhalfspace\b|\bpolyhedron\b|\bcone\b|\bellipsoid\b|\bconvex hull\b|\bseparating\b|\bsupporting\b|\bdimension\b", re.IGNORECASE),
    "computational": re.compile(r"\balgorithm\b|\bcomplexity\b|\binterior[-]?point\b|\bnewton\b|\bstep\b|\biteration\b|\bbarrier\b|\bconvergence\b|\bsolver\b", re.IGNORECASE),
    "applied": re.compile(r"\bapproximation\b|\bfitting\b|\bestimation\b|\bmodel\b|\brobust\b|\bportfolio\b|\bdesign\b|\bplacement\b|\blocation\b", re.IGNORECASE),
}


@dataclass
class CvxDeclaration:
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


def detect_cvx_representation_profile(text: str, title: str) -> dict[str, Any]:
    full_text = f"{title}\n{text}"
    eo_tags = [tag for tag, pat in EO_KEYWORDS.items() if pat.search(full_text)]
    geo_tags = [tag for tag, pat in GEO_KEYWORDS.items() if pat.search(full_text)]

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


def download_cvx_pdf(target_path: Path = DEFAULT_CACHE_PATH) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists() and target_path.stat().st_size > 5000000:
        return target_path
    req = urllib.request.Request(
        CVX_URL,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MAPEOGEO-Intake/0.14"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp, open(target_path, "wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
    return target_path


def parse_cvx_declarations_from_pdf(
    pdf_path: Path,
) -> list[CvxDeclaration]:
    try:
        import fitz  # PyMuPDF
    except ImportError as err:
        raise RuntimeError("PyMuPDF (fitz) is required to parse Convex Optimization PDF") from err

    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    ref_re = re.compile(r"\b(\d{1,2}\.\d{1,2})\b")

    chap_map = {
        "Introduction": 1,
        "Convex sets": 2,
        "Convex functions": 3,
        "Convex optimization problems": 4,
        "Duality": 5,
        "Approximation and fitting": 6,
        "Statistical estimation": 7,
        "Geometric problems": 8,
        "Unconstrained minimization": 9,
        "Equality constrained minimization": 10,
        "Interior-point methods": 11,
    }
    target_chaps = set(range(1, 12))

    sections_meta: list[tuple[str, str, str, int, int]] = []
    current_chap = 0
    current_sec = 0

    for lvl, title, page in toc:
        t = title.strip()
        if lvl == 1 and t == "Introduction":
            current_chap = 1
            current_sec = 0
        elif lvl == 2 and t in chap_map:
            current_chap = chap_map[t]
            current_sec = 0
        elif lvl == 2 and current_chap == 1 and t.lower() not in ("bibliography", "exercises", "outline", "notation"):
            current_sec += 1
            sec_code = f"1.{current_sec}"
            title_clean = t.encode("ascii", "replace").decode("ascii")
            sections_meta.append((sec_code, title_clean, "Chapter 1", page, 1))
        elif lvl == 3 and current_chap >= 2 and t.lower() not in ("bibliography", "exercises"):
            current_sec += 1
            sec_code = f"{current_chap}.{current_sec}"
            title_clean = t.encode("ascii", "replace").decode("ascii")
            sections_meta.append((sec_code, title_clean, f"Chapter {current_chap}", page, current_chap))

    declarations: list[CvxDeclaration] = []

    for i, (sec_code, sec_title, chap, pno, c_num) in enumerate(sections_meta):
        # Extract page text in memory
        start_pno = max(0, pno - 1)
        end_pno = min(len(doc), sections_meta[i + 1][3] - 1 if i + 1 < len(sections_meta) else start_pno + 5)

        pages_text = []
        for p in range(start_pno, max(start_pno + 1, end_pno)):
            pages_text.append(doc[p].get_text("text"))

        stmt_text = f"{sec_title} " + " ".join(pages_text)
        stmt_clean = re.sub(r"\s+", " ", stmt_text)[:5000].strip()

        stmt_hash = hashlib.sha256(stmt_clean.encode("utf-8")).hexdigest()
        char_count = len(stmt_clean)

        refs = sorted(set(ref_re.findall(stmt_clean)) - {sec_code})
        profile = detect_cvx_representation_profile(stmt_clean, sec_title)

        sec_id = sec_code.replace(".", "_")
        node_id = f"srcdecl:cvx:section:{sec_id}"
        label = f"Convex Optimization {sec_code} {sec_title}"

        decl = CvxDeclaration(
            node_id=node_id,
            source_id=SOURCE_ID,
            label=label,
            decl_type="SECTION",
            chapter_section=chap,
            page=pno,
            statement_sha256=stmt_hash,
            char_count=char_count,
            structural_refs=refs,
            representation_profile=profile,
        )
        declarations.append(decl)

    return declarations


def generate_mock_cvx_declarations() -> list[CvxDeclaration]:
    """Deterministic fallback mock declarations for testing environments without PDF access."""
    mock_data = [
        # Chapter 2: Convex sets
        ("2.1", "Affine and convex sets", "Chapter 2", 21, ["affine_combination", "convex_combination"], ["hyperplane", "halfspace", "convex_set"], ["abstract", "geometric"]),
        ("2.2", "Some important examples", "Chapter 2", 27, ["convex_combination", "matrix_inequality"], ["hyperplane", "halfspace", "polyhedron", "cone", "norm_ball", "ellipsoid"], ["geometric", "algebraic"]),
        ("2.3", "Operations that preserve convexity", "Chapter 2", 35, ["convex_combination"], ["convex_set", "projection_convex_set"], ["abstract", "geometric"]),
        ("2.4", "Generalized inequalities", "Chapter 2", 43, ["matrix_inequality"], ["cone", "dual_cone"], ["abstract", "algebraic"]),
        ("2.5", "Separating and supporting hyperplanes", "Chapter 2", 46, ["affine_combination"], ["separating_hyperplane", "supporting_hyperplane", "hyperplane"], ["geometric", "abstract"]),
        ("2.6", "Dual cones and generalized inequalities", "Chapter 2", 51, ["matrix_inequality"], ["cone", "dual_cone", "hyperplane"], ["abstract", "geometric", "algebraic"]),

        # Chapter 3: Convex functions
        ("3.1", "Basic properties and examples", "Chapter 3", 67, ["convex_function", "affine_combination"], ["epigraph", "hyperplane"], ["abstract", "algebraic"]),
        ("3.2", "Operations that preserve convexity", "Chapter 3", 79, ["convex_function", "convex_combination"], [], ["abstract", "algebraic", "computational"]),
        ("3.3", "The conjugate function", "Chapter 3", 90, ["fenchel_conjugate", "convex_function"], ["supporting_hyperplane", "hyperplane"], ["abstract", "geometric", "algebraic"]),
        ("3.4", "Quasiconvex functions", "Chapter 3", 95, ["convex_function"], ["convex_set"], ["abstract", "geometric"]),
        ("3.5", "Log-concave and log-convex functions", "Chapter 3", 104, ["convex_function"], [], ["abstract", "algebraic"]),

        # Chapter 4: Convex optimization problems
        ("4.1", "Optimization problems", "Chapter 4", 127, ["linear_program", "lagrangian"], ["convex_set"], ["abstract", "computational"]),
        ("4.2", "Convex optimization", "Chapter 4", 136, ["convex_function", "convex_combination"], ["convex_set"], ["abstract", "computational", "geometric"]),
        ("4.3", "Linear optimization problems", "Chapter 4", 146, ["linear_program"], ["polyhedron", "halfspace"], ["algebraic", "geometric", "computational"]),
        ("4.4", "Quadratic optimization problems", "Chapter 4", 152, ["quadratic_program", "least_squares_cvx"], ["ellipsoid"], ["algebraic", "computational", "applied"]),
        ("4.5", "Geometric programming", "Chapter 4", 160, ["convex_function"], [], ["algebraic", "applied"]),
        ("4.6", "Generalized inequality constraints", "Chapter 4", 167, ["semidefinite_program", "matrix_inequality"], ["cone"], ["abstract", "algebraic", "computational"]),
        ("4.7", "Semidefinite programming", "Chapter 4", 168, ["semidefinite_program", "matrix_inequality"], ["cone"], ["algebraic", "computational", "applied"]),

        # Chapter 5: Duality
        ("5.1", "The Lagrange dual function", "Chapter 5", 215, ["lagrangian", "dual_problem"], ["hyperplane"], ["abstract", "algebraic"]),
        ("5.2", "The Lagrange dual problem", "Chapter 5", 223, ["lagrangian", "dual_problem"], ["supporting_hyperplane"], ["abstract", "computational", "geometric"]),
        ("5.3", "Geometric interpretation", "Chapter 5", 232, ["dual_problem", "lagrangian"], ["separating_hyperplane", "supporting_hyperplane", "hyperplane"], ["geometric", "abstract"]),
        ("5.4", "Saddle-point interpretation", "Chapter 5", 237, ["lagrangian", "dual_problem"], [], ["abstract", "algebraic"]),
        ("5.5", "Optimality conditions", "Chapter 5", 241, ["kkt_conditions", "lagrangian"], ["projection_convex_set"], ["algebraic", "computational", "applied"]),
        ("5.6", "Perturbation and sensitivity analysis", "Chapter 5", 249, ["lagrangian", "dual_problem"], [], ["applied", "algebraic"]),
        ("5.7", "Reformulation of dual problems", "Chapter 5", 253, ["dual_problem", "linear_program"], [], ["algebraic", "computational"]),
        ("5.8", "Theorems of alternatives", "Chapter 5", 258, ["linear_program", "matrix_inequality"], ["separating_hyperplane", "cone"], ["geometric", "abstract", "algebraic"]),
        ("5.9", "Generalized inequalities duality", "Chapter 5", 264, ["semidefinite_program", "dual_problem"], ["cone", "dual_cone"], ["abstract", "algebraic"]),

        # Chapter 6: Approximation and fitting
        ("6.1", "Norm approximation", "Chapter 6", 291, ["least_squares_cvx", "quadratic_program"], ["norm_ball", "distance_to_set"], ["applied", "computational", "geometric"]),
        ("6.2", "Least-norm problems", "Chapter 6", 302, ["least_squares_cvx", "quadratic_program"], ["projection_convex_set", "hyperplane"], ["algebraic", "applied", "geometric"]),
        ("6.3", "Regularized approximation", "Chapter 6", 305, ["least_squares_cvx", "quadratic_program"], ["norm_ball"], ["applied", "computational", "algebraic"]),
        ("6.4", "Robust approximation", "Chapter 6", 318, ["quadratic_program", "semidefinite_program"], ["ellipsoid"], ["applied", "algebraic", "geometric"]),
        ("6.5", "Function fitting and interpolation", "Chapter 6", 324, ["least_squares_cvx", "convex_function"], [], ["applied", "computational"]),

        # Chapter 8: Geometric problems
        ("8.1", "Projection on a set", "Chapter 8", 397, ["least_squares_cvx"], ["projection_convex_set", "distance_to_set", "convex_set"], ["geometric", "computational", "algebraic"]),
        ("8.2", "Distance between sets", "Chapter 8", 402, ["quadratic_program"], ["distance_to_set", "separating_hyperplane", "polyhedron"], ["geometric", "computational"]),
        ("8.3", "Euclidean distance and angle problems", "Chapter 8", 405, ["matrix_inequality"], ["distance_to_set", "norm_ball", "polyhedron"], ["geometric", "algebraic"]),
        ("8.4", "Extremal volume ellipsoids", "Chapter 8", 410, ["semidefinite_program"], ["ellipsoid", "norm_ball", "polyhedron"], ["geometric", "computational", "applied"]),
        ("8.5", "Centering", "Chapter 8", 416, ["interior_point"], ["analytic_center", "polyhedron", "ellipsoid"], ["computational", "geometric", "applied"]),
        ("8.6", "Classification", "Chapter 8", 422, ["linear_program", "quadratic_program"], ["separating_hyperplane", "hyperplane", "polyhedron"], ["applied", "geometric", "computational"]),
        ("8.7", "Placement and location", "Chapter 8", 432, ["quadratic_program"], ["distance_to_set", "norm_ball"], ["applied", "computational", "geometric"]),
        ("8.8", "Floor planning", "Chapter 8", 438, ["linear_program", "geometric_programming"], ["polyhedron"], ["applied", "geometric"]),
    ]

    decls: list[CvxDeclaration] = []
    for sec, title, chap, pno, eo_t, geo_t, kinds in mock_data:
        sec_id = sec.replace(".", "_")
        node_id = f"srcdecl:cvx:section:{sec_id}"
        label = f"Convex Optimization {sec} {title}"
        raw_mock = f"{sec} {title} in {chap}"
        h = hashlib.sha256(raw_mock.encode("utf-8")).hexdigest()

        status = "DUAL_DIRECT" if (eo_t and geo_t) else ("EO_ONLY_DIRECT" if eo_t else ("GEO_ONLY_DIRECT" if geo_t else "THEORETIC_DIRECT"))
        profile = {
            "eo_tags": sorted(eo_t),
            "geo_tags": sorted(geo_t),
            "direct_status": status,
            "representation_kinds": sorted(kinds),
            "diversity_count": len(kinds),
        }
        decls.append(
            CvxDeclaration(
                node_id=node_id,
                source_id=SOURCE_ID,
                label=label,
                decl_type="SECTION",
                chapter_section=chap,
                page=pno,
                statement_sha256=h,
                char_count=len(raw_mock),
                structural_refs=[],
                representation_profile=profile,
            )
        )
    return decls


def get_cvx_declarations(
    pdf_path: Path | None = None,
    use_mock: bool = False,
    auto_download: bool = True,
) -> list[CvxDeclaration]:
    if use_mock:
        return generate_mock_cvx_declarations()

    path = pdf_path or DEFAULT_CACHE_PATH
    if not path.exists() or path.stat().st_size < 5000000:
        if auto_download:
            try:
                download_cvx_pdf(path)
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to download Convex Optimization PDF ({e}). Falling back to deterministic mock.\n")
                return generate_mock_cvx_declarations()
        else:
            return generate_mock_cvx_declarations()

    try:
        return parse_cvx_declarations_from_pdf(path)
    except Exception as e:
        sys.stderr.write(f"Warning: Convex Optimization PDF parsing failed ({e}). Falling back to deterministic mock.\n")
        return generate_mock_cvx_declarations()


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Convex Optimization declarations for MAPEOGEO v0.14")
    parser.add_argument("--pdf-path", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    decls = get_cvx_declarations(args.pdf_path, use_mock=args.mock)
    print(f"Extracted {len(decls)} Convex Optimization declarations.")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        data = [d.to_dict() for d in decls]
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved declarations to {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
