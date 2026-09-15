#!/usr/bin/env python3
"""MAPEOGEO v0.13 VMLS (Boyd & Vandenberghe) Source Ingestion Module.

Extracts numbered sections, definitions, and algorithms from Stephen Boyd and Lieven Vandenberghe's
"Introduction to Applied Linear Algebra – Vectors, Matrices, and Least Squares" (VMLS, 2018)
for the v0.13 tri-source mathematical expansion.

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

SOURCE_ID = "BOYD_VANDENBERGHE_VMLS_2018"
VMLS_URL = "https://web.stanford.edu/~boyd/vmls/vmls.pdf"
DEFAULT_CACHE_PATH = ROOT / "data" / "sources" / "vmls.pdf"

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

# Detector Bank Keywords for Executable Operator (EO) and Geometric Object (GEO) candidate views
EO_KEYWORDS = {
    "linear_combination": re.compile(r"\blinear combination\b|\blinear combinations\b|\blinear function\b", re.IGNORECASE),
    "span": re.compile(r"\bspan\b|\bset of linear combinations\b", re.IGNORECASE),
    "linear_independence": re.compile(r"\blinearly independent\b|\blinear independence\b|\blinear dependence\b", re.IGNORECASE),
    "basis": re.compile(r"\bbasis\b|\bbases\b", re.IGNORECASE),
    "matrix": re.compile(r"\bmatrix\b|\bmatrices\b", re.IGNORECASE),
    "matrix_multiplication": re.compile(r"\bmatrix multiplication\b|\bmatrix product\b|\bmatrix-vector\b", re.IGNORECASE),
    "matrix_inverse": re.compile(r"\bmatrix inverse\b|\binvertible\b|\bleft inverse\b|\bright inverse\b", re.IGNORECASE),
    "linear_equations": re.compile(r"\blinear equations\b|\bsystem of linear equations\b", re.IGNORECASE),
    "gram_schmidt": re.compile(r"\bgram\s*[-]?\s*schmidt\b", re.IGNORECASE),
    "qr_factorization": re.compile(r"\bqr factorization\b|\bqr decomposition\b", re.IGNORECASE),
    "least_squares": re.compile(r"\bleast squares\b|\bleast-squares\b", re.IGNORECASE),
    "normal_equations": re.compile(r"\bnormal equations\b", re.IGNORECASE),
    "pseudoinverse": re.compile(r"\bpseudo[-]?inverse\b|\bmoore[-]?penrose\b", re.IGNORECASE),
    "regularization": re.compile(r"\bregulariz(?:ation|ed)\b|\btikhonov\b|\bmulti-objective\b", re.IGNORECASE),
    "data_fitting": re.compile(r"\bdata fitting\b|\bregression\b", re.IGNORECASE),
    "clustering": re.compile(r"\bclustering\b|\bk-means\b", re.IGNORECASE),
    "algorithm": re.compile(r"\balgorithm\b", re.IGNORECASE),
    "vector": re.compile(r"\bvector\b|\bvectors\b", re.IGNORECASE),
}

GEO_KEYWORDS = {
    "orthogonal": re.compile(r"\borthogonal\b|\borthogonality\b", re.IGNORECASE),
    "orthonormal": re.compile(r"\borthonormal\b|\borthonormal vectors\b", re.IGNORECASE),
    "norm": re.compile(r"\bnorm\b|\beuclidean norm\b|\blength\b", re.IGNORECASE),
    "distance": re.compile(r"\bdistance\b|\beuclidean distance\b", re.IGNORECASE),
    "inner_product": re.compile(r"\binner product\b|\bdot product\b", re.IGNORECASE),
    "angle": re.compile(r"\bangle\b|\bvector angle\b|\bcosine\b", re.IGNORECASE),
    "cauchy_schwarz": re.compile(r"\bcauchy[-]?schwarz\b", re.IGNORECASE),
    "projection": re.compile(r"\bprojection\b|\borthogonal projection\b", re.IGNORECASE),
    "hyperplane": re.compile(r"\bhyperplane\b|\baffine\b", re.IGNORECASE),
}


@dataclass
class VmlsDeclaration:
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


def detect_vmls_representation_profile(text: str, title: str) -> dict[str, Any]:
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

    return {
        "eo_tags": sorted(eo_tags),
        "geo_tags": sorted(geo_tags),
        "direct_status": direct_status,
    }


def download_vmls_pdf(target_path: Path = DEFAULT_CACHE_PATH) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists() and target_path.stat().st_size > 5000000:
        return target_path
    req = urllib.request.Request(
        VMLS_URL,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MAPEOGEO-Intake/0.13"},
    )
    with urllib.request.urlopen(req, timeout=45) as resp, open(target_path, "wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
    return target_path


def parse_vmls_declarations_from_pdf(
    pdf_path: Path,
) -> list[VmlsDeclaration]:
    try:
        import fitz  # PyMuPDF
    except ImportError as err:
        raise RuntimeError("PyMuPDF (fitz) is required to parse VMLS PDF") from err

    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    ref_re = re.compile(r"\b(\d{1,2}\.\d{1,2})\b")

    chap_num = 0
    sec_num = 0
    sections_meta = []

    for lvl, title, page in toc:
        if lvl == 2:
            chap_num += 1
            sec_num = 0
        elif lvl == 3 and not title.lower().startswith("exercises"):
            sec_num += 1
            sec_code = f"{chap_num}.{sec_num}"
            title_clean = title.encode("ascii", "replace").decode("ascii")
            sections_meta.append((sec_code, title_clean, f"Chapter {chap_num}", page))

    declarations: list[VmlsDeclaration] = []

    for i, (sec_code, sec_title, chap, pno) in enumerate(sections_meta):
        # Extract page text
        start_pno = max(0, pno - 1)
        end_pno = min(len(doc), sections_meta[i + 1][3] - 1 if i + 1 < len(sections_meta) else start_pno + 4)
        
        pages_text = []
        for p in range(start_pno, max(start_pno + 1, end_pno)):
            pages_text.append(doc[p].get_text("text"))

        stmt_text = f"{sec_title} " + " ".join(pages_text)
        stmt_clean = re.sub(r"\s+", " ", stmt_text)[:4000].strip()

        stmt_hash = hashlib.sha256(stmt_clean.encode("utf-8")).hexdigest()
        char_count = len(stmt_clean)

        refs = sorted(set(ref_re.findall(stmt_clean)) - {sec_code})
        profile = detect_vmls_representation_profile(stmt_clean, sec_title)

        sec_id = sec_code.replace(".", "_")
        node_id = f"srcdecl:vmls:section:{sec_id}"
        label = f"VMLS {sec_code} {sec_title}"

        decl = VmlsDeclaration(
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


def generate_mock_vmls_declarations() -> list[VmlsDeclaration]:
    """Deterministic fallback mock declarations for testing environments without PDF access."""
    mock_data = [
        ("1.1", "Vectors", "Chapter 1", 13, ["vector"], ["norm"]),
        ("1.2", "Vector addition", "Chapter 1", 21, ["vector", "linear_combination"], []),
        ("1.3", "Scalar-vector multiplication", "Chapter 1", 25, ["vector", "linear_combination"], []),
        ("1.4", "Inner product", "Chapter 1", 29, ["inner_product", "vector"], ["inner_product", "orthogonal"]),
        ("2.1", "Linear functions", "Chapter 2", 39, ["linear_combination", "vector"], []),
        ("2.2", "Taylor approximation", "Chapter 2", 45, ["linear_combination"], []),
        ("3.1", "Norm", "Chapter 3", 55, ["vector"], ["norm", "distance", "inner_product"]),
        ("3.2", "Distance", "Chapter 3", 58, ["vector"], ["distance", "norm", "cauchy_schwarz"]),
        ("3.3", "Standard deviation", "Chapter 3", 62, ["vector"], ["distance"]),
        ("3.4", "Angle", "Chapter 3", 66, ["inner_product"], ["angle", "orthogonal", "inner_product"]),
        ("4.1", "Clustering", "Chapter 4", 79, ["clustering"], ["distance"]),
        ("4.2", "A clustering objective", "Chapter 4", 82, ["clustering", "least_squares"], ["distance"]),
        ("4.3", "The k-means algorithm", "Chapter 4", 84, ["clustering", "algorithm"], ["distance"]),
        ("5.1", "Linear dependence", "Chapter 5", 99, ["linear_independence", "linear_combination"], []),
        ("5.2", "Basis", "Chapter 5", 101, ["basis", "linear_independence", "span"], []),
        ("5.3", "Orthonormal vectors", "Chapter 5", 105, ["basis"], ["orthonormal", "orthogonal", "norm"]),
        ("5.4", "Gram-Schmidt algorithm", "Chapter 5", 107, ["gram_schmidt", "qr_factorization", "algorithm"], ["orthonormal", "orthogonal"]),
        ("6.1", "Matrices", "Chapter 6", 117, ["matrix"], []),
        ("6.2", "Zero and identity matrices", "Chapter 6", 123, ["matrix"], []),
        ("6.3", "Transpose, addition, and norm", "Chapter 6", 125, ["matrix"], ["norm"]),
        ("6.4", "Matrix-vector multiplication", "Chapter 6", 128, ["matrix", "linear_combination"], []),
        ("7.1", "Geometric transformations", "Chapter 7", 139, ["matrix"], ["projection", "orthogonal", "hyperplane"]),
        ("8.1", "Linear and affine functions", "Chapter 8", 157, ["linear_equations", "matrix"], []),
        ("8.3", "Systems of linear equations", "Chapter 8", 162, ["linear_equations", "matrix_inverse"], []),
        ("9.1", "Linear dynamical systems", "Chapter 9", 173, ["matrix", "algorithm"], []),
        ("10.1", "Matrix-matrix multiplication", "Chapter 10", 187, ["matrix_multiplication", "matrix"], []),
        ("11.1", "Left and right inverses", "Chapter 11", 215, ["matrix_inverse", "pseudoinverse", "matrix"], []),
        ("11.2", "Inverse", "Chapter 11", 220, ["matrix_inverse", "matrix"], []),
        ("11.3", "Solving linear equations", "Chapter 11", 225, ["linear_equations", "matrix_inverse"], []),
        ("11.4", "QR factorization", "Chapter 11", 230, ["qr_factorization", "linear_equations", "algorithm"], ["orthonormal"]),
        ("12.1", "Least squares problem", "Chapter 12", 243, ["least_squares", "matrix"], ["norm", "distance"]),
        ("12.2", "Solution", "Chapter 12", 247, ["least_squares", "normal_equations", "pseudoinverse"], ["projection", "orthogonal"]),
        ("13.1", "Least squares data fitting", "Chapter 13", 265, ["data_fitting", "least_squares"], ["norm"]),
        ("13.2", "Validation", "Chapter 13", 272, ["data_fitting", "least_squares"], []),
        ("14.1", "Classification", "Chapter 14", 287, ["data_fitting", "least_squares"], ["hyperplane"]),
        ("15.1", "Multi-objective least squares", "Chapter 15", 305, ["regularization", "least_squares"], ["norm"]),
        ("15.2", "Control", "Chapter 15", 310, ["regularization", "least_squares", "normal_equations"], ["norm"]),
        ("16.1", "Constrained least squares problem", "Chapter 16", 325, ["least_squares", "linear_equations"], ["norm", "projection"]),
    ]

    decls: list[VmlsDeclaration] = []
    for sec, title, chap, pno, eo_t, geo_t in mock_data:
        sec_id = sec.replace(".", "_")
        node_id = f"srcdecl:vmls:section:{sec_id}"
        label = f"VMLS {sec} {title}"
        raw_mock = f"{sec} {title} in {chap}"
        h = hashlib.sha256(raw_mock.encode("utf-8")).hexdigest()

        status = "DUAL_DIRECT" if (eo_t and geo_t) else ("EO_ONLY_DIRECT" if eo_t else ("GEO_ONLY_DIRECT" if geo_t else "THEORETIC_DIRECT"))
        profile = {
            "eo_tags": sorted(eo_t),
            "geo_tags": sorted(geo_t),
            "direct_status": status,
        }
        decls.append(
            VmlsDeclaration(
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


def get_vmls_declarations(
    pdf_path: Path | None = None,
    use_mock: bool = False,
    auto_download: bool = True,
) -> list[VmlsDeclaration]:
    if use_mock:
        return generate_mock_vmls_declarations()

    path = pdf_path or DEFAULT_CACHE_PATH
    if not path.exists() or path.stat().st_size < 5000000:
        if auto_download:
            try:
                download_vmls_pdf(path)
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to download VMLS PDF ({e}). Falling back to deterministic mock.\n")
                return generate_mock_vmls_declarations()
        else:
            return generate_mock_vmls_declarations()

    try:
        return parse_vmls_declarations_from_pdf(path)
    except Exception as e:
        sys.stderr.write(f"Warning: VMLS PDF parsing failed ({e}). Falling back to deterministic mock.\n")
        return generate_mock_vmls_declarations()


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract VMLS declarations for MAPEOGEO v0.13")
    parser.add_argument("--pdf-path", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    decls = get_vmls_declarations(
        pdf_path=args.pdf_path,
        use_mock=args.mock,
        auto_download=True,
    )

    print(f"Extracted {len(decls)} VMLS declarations.")
    dual = sum(1 for d in decls if d.representation_profile.get("direct_status") == "DUAL_DIRECT")
    eo = sum(1 for d in decls if d.representation_profile.get("direct_status") == "EO_ONLY_DIRECT")
    geo = sum(1 for d in decls if d.representation_profile.get("direct_status") == "GEO_ONLY_DIRECT")
    print(f"Profiles: {dual} DUAL_DIRECT, {eo} EO_ONLY_DIRECT, {geo} GEO_ONLY_DIRECT")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        out_dicts = [d.to_dict() for d in decls]
        for item in out_dicts:
            for forbidden in FORBIDDEN_PERSISTED_KEYS:
                assert forbidden not in item, f"Zero-prose violation: found '{forbidden}'"
        args.out.write_text(json.dumps(out_dicts, indent=2), encoding="utf-8")
        print(f"Saved VMLS declarations metadata to {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
