#!/usr/bin/env python3
"""MAPEOGEO v0.12 Axler LADR4e Source Ingestion Module.

Extracts numbered declarations from Sheldon Axler's "Linear Algebra Done Right" (4th Edition, 2026-08-16)
for the v0.12 mathematical expansion slice (1A-1C, 2A-2C, 3A-3E, 5A/5D, 6B-6C, 7A-7B).

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

SOURCE_ID = "AXLER_LADR4E_2026_08_16"
AXLER_URL = "https://linear.axler.net/LADR4e.pdf"
DEFAULT_CACHE_PATH = ROOT / "data" / "sources" / "LADR4e.pdf"

DEFAULT_TARGET_SLICES = [
    "1A", "1B", "1C",
    "2A", "2B", "2C",
    "3A", "3B", "3C", "3D", "3E",
    "5A", "5D",
    "6A", "6B", "6C",
    "7A", "7B",
]

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

# Detector Bank Keywords for Executable Operator (EO) and Geometric Object (GEO) views
EO_KEYWORDS = {
    "linear_map": re.compile(r"\blinear map\b|\blinear transformation\b", re.IGNORECASE),
    "matrix": re.compile(r"\bmatrix\b|\bmatrices\b", re.IGNORECASE),
    "null_space": re.compile(r"\bnull space\b|\bkernel\b|\bnull\s+[T]\b", re.IGNORECASE),
    "range": re.compile(r"\brange\b|\bimage\b|\brange\s+[T]\b", re.IGNORECASE),
    "rank_nullity": re.compile(r"\bfundamental theorem of linear maps\b|\brank-nullity\b|\bdim null\b", re.IGNORECASE),
    "dimension": re.compile(r"\bdimension\b|\bdim\s+[VUW]\b", re.IGNORECASE),
    "isomorphism": re.compile(r"\bisomorph(?:ic|ism)?\b|\binvertib(?:le|ility)\b", re.IGNORECASE),
    "quotient_space": re.compile(r"\bquotient space\b|\b[V]/[U]\b", re.IGNORECASE),
    "basis": re.compile(r"\bbasis\b|\bbases\b", re.IGNORECASE),
    "span": re.compile(r"\bspan\b|\bspans\b|\bspanning\b", re.IGNORECASE),
    "linear_combination": re.compile(r"\blinear combination\b", re.IGNORECASE),
    "linear_independence": re.compile(r"\blinearly independent\b|\blinear independence\b", re.IGNORECASE),
    "direct_sum": re.compile(r"\bdirect sum\b", re.IGNORECASE),
    "subspace": re.compile(r"\bsubspace\b|\bsubspaces\b", re.IGNORECASE),
    "eigenvalue": re.compile(r"\beigenvalue\b|\beigenvector\b|\beigenspace\b", re.IGNORECASE),
    "diagonalizable": re.compile(r"\bdiagonaliz(?:able|ation)\b|\bdiagonal matrix\b", re.IGNORECASE),
    "pseudoinverse": re.compile(r"\bpseudoinverse\b", re.IGNORECASE),
    "operator": re.compile(r"\boperator\b", re.IGNORECASE),
}

GEO_KEYWORDS = {
    "orthogonal": re.compile(r"\borthogonal\b|\borthogonality\b", re.IGNORECASE),
    "orthonormal": re.compile(r"\borthonormal\b|\borthonormal basis\b", re.IGNORECASE),
    "norm": re.compile(r"\bnorm\b|\bnormed\b|\blength\b", re.IGNORECASE),
    "inner_product": re.compile(r"\binner product\b|\bdot product\b", re.IGNORECASE),
    "isometry": re.compile(r"\bisometr(?:y|ies)\b", re.IGNORECASE),
    "projection": re.compile(r"\borthogonal projection\b|\bprojection\b", re.IGNORECASE),
    "complement": re.compile(r"\borthogonal complement\b|\bU\^\s*\\perp\b", re.IGNORECASE),
    "spectral": re.compile(r"\bspectral theorem\b|\bspectral\b", re.IGNORECASE),
    "gram_schmidt": re.compile(r"\bgram\s*[-]?\s*schmidt\b", re.IGNORECASE),
    "angle": re.compile(r"\bangle\b|\bdistance\b", re.IGNORECASE),
    "self_adjoint": re.compile(r"\bself-adjoint\b|\bhermitian\b|\bsymmetric operator\b", re.IGNORECASE),
}


@dataclass
class AxlerDeclaration:
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


def detect_representation_profile(text: str, title: str) -> dict[str, Any]:
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


def download_axler_pdf(target_path: Path = DEFAULT_CACHE_PATH) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists() and target_path.stat().st_size > 100000:
        return target_path
    req = urllib.request.Request(
        AXLER_URL,
        headers={"User-Agent": "MAPEOGEO-Intake/0.12 (Educational Research; Open Access CC BY-NC 4.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp, open(target_path, "wb") as f:
        f.write(resp.read())
    return target_path


def parse_declarations_from_pdf(
    pdf_path: Path,
    slices: list[str] | None = None,
) -> list[AxlerDeclaration]:
    try:
        import fitz  # PyMuPDF
    except ImportError as err:
        raise RuntimeError("PyMuPDF (fitz) is required to parse PDF sources") from err

    target_slice_set = set(s.upper() for s in (slices or DEFAULT_TARGET_SLICES))

    doc = fitz.open(pdf_path)
    decl_num_re = re.compile(r"^(\d+\.\d{1,2})$")
    type_re = re.compile(r"^(definition|notation|example|theorem|lemma|proposition|corollary):\s*(.*)", re.IGNORECASE)
    section_re = re.compile(r"^(\d[A-F])\s+(.*)", re.IGNORECASE)
    ref_re = re.compile(r"\b(\d+\.\d{1,2})\b")

    # Pass 1: Build full text and page offsets
    pages_text: list[tuple[int, str]] = []
    current_sec = "1A"

    for pno in range(len(doc)):
        page_t = doc[pno].get_text("text")
        pages_text.append((pno + 1, page_t))

    # Pass 2: Extract structured declarations
    declarations: list[AxlerDeclaration] = []
    full_doc_lines: list[tuple[int, str, str]] = []  # (page_no, line, section)

    for pno, text in pages_text:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines:
            sm = section_re.match(line)
            if sm:
                current_sec = sm.group(1).upper()
            full_doc_lines.append((pno, line, current_sec))

    i = 0
    total_lines = len(full_doc_lines)
    while i < total_lines:
        pno, line, sec = full_doc_lines[i]
        dm = decl_num_re.match(line)
        if dm:
            num_str = dm.group(1)
            # Peek ahead for title & kind
            next_lines = [full_doc_lines[j][1] for j in range(i + 1, min(i + 6, total_lines))]
            raw_title = next_lines[0] if next_lines else ""
            
            kind = "THEOREM"
            tm = type_re.match(raw_title)
            if tm:
                k_raw = tm.group(1).upper()
                raw_title = tm.group(2).strip()
                if k_raw in ("DEFINITION", "THEOREM", "LEMMA", "PROPOSITION", "COROLLARY"):
                    kind = k_raw
                else:
                    # NOTATION, EXAMPLE, etc.
                    i += 1
                    continue
            else:
                # Standard un-prefixed theorem/lemma name in Axler (e.g. "Linear Dependence Lemma")
                if "lemma" in raw_title.lower():
                    kind = "LEMMA"
                elif "proposition" in raw_title.lower():
                    kind = "PROPOSITION"
                elif "corollary" in raw_title.lower():
                    kind = "COROLLARY"
                else:
                    kind = "THEOREM"

            # Check if this declaration belongs to target slices
            if sec in target_slice_set:
                # Extract in-memory statement block up to next declaration / Proof / boundary
                stmt_lines: list[str] = [raw_title]
                j = i + 2
                while j < total_lines:
                    _, next_l, _ = full_doc_lines[j]
                    if decl_num_re.match(next_l) or next_l.startswith("Proof") or section_re.match(next_l):
                        break
                    stmt_lines.append(next_l)
                    j += 1
                    if j - i > 50:  # Bound statement search window
                        break

                stmt_text = " ".join(stmt_lines).strip()
                stmt_clean = re.sub(r"\s+", " ", stmt_text)

                # Compute cryptographic hash and character count strictly in memory
                stmt_hash = hashlib.sha256(stmt_clean.encode("utf-8")).hexdigest()
                char_count = len(stmt_clean)

                # Find structural cross-references
                refs = sorted(set(ref_re.findall(stmt_clean)) - {num_str})

                # Compute representation profile
                rep_profile = detect_representation_profile(stmt_clean, raw_title)

                # Construct clean node ID
                num_id = num_str.replace(".", "_")
                kind_id = kind.lower()
                node_id = f"srcdecl:axler:{kind_id}:{num_id}"
                label = f"Axler {num_str} {kind.capitalize()} {raw_title}".strip()

                decl = AxlerDeclaration(
                    node_id=node_id,
                    source_id=SOURCE_ID,
                    label=label,
                    decl_type=kind,
                    chapter_section=sec,
                    page=pno,
                    statement_sha256=stmt_hash,
                    char_count=char_count,
                    structural_refs=refs,
                    representation_profile=rep_profile,
                )
                declarations.append(decl)
        i += 1

    return declarations


MANIFEST_PATH = ROOT / "formal" / "axler_declarations_manifest.json"


def generate_mock_axler_declarations() -> list[AxlerDeclaration]:
    """Deterministic fallback mock declarations for testing environments without PDF access."""
    if MANIFEST_PATH.exists():
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return [
            AxlerDeclaration(
                node_id=item["node_id"],
                source_id=item["source_id"],
                label=item["label"],
                decl_type=item["decl_type"],
                chapter_section=item["chapter_section"],
                page=item["page"],
                statement_sha256=item["statement_sha256"],
                char_count=item["char_count"],
                structural_refs=item.get("structural_refs", []),
                representation_profile=item.get("representation_profile", {}),
            )
            for item in data
        ]
    mock_data = [
        ("1.20", "DEFINITION", "vector space", "1B", 26, ["1.19"], ["linear_map", "operator", "subspace"], []),
        ("1.33", "DEFINITION", "subspace", "1C", 32, ["1.20"], ["subspace"], []),
        ("1.34", "THEOREM", "conditions for a subspace", "1C", 32, ["1.33"], ["subspace"], []),
        ("1.41", "DEFINITION", "direct sum", "1C", 35, ["1.33"], ["direct_sum", "subspace"], []),
        ("1.45", "THEOREM", "condition for a direct sum", "1C", 37, ["1.41"], ["direct_sum", "subspace"], []),
        ("2.2", "DEFINITION", "linear combination", "2A", 42, ["1.20"], ["linear_combination"], []),
        ("2.4", "DEFINITION", "span", "2A", 43, ["2.2"], ["span", "subspace"], []),
        ("2.6", "THEOREM", "span is the smallest containing subspace", "2A", 43, ["2.4"], ["span", "subspace"], []),
        ("2.7", "DEFINITION", "spans", "2A", 43, ["2.4"], ["span"], []),
        ("2.15", "DEFINITION", "linearly independent", "2A", 46, ["2.2"], ["linear_independence"], []),
        ("2.19", "LEMMA", "linear dependence lemma", "2A", 47, ["2.15"], ["linear_independence", "span"], []),
        ("2.26", "DEFINITION", "basis", "2B", 53, ["2.15", "2.7"], ["basis", "linear_independence", "span"], []),
        ("2.28", "THEOREM", "criterion for basis", "2B", 53, ["2.26"], ["basis"], []),
        ("2.32", "THEOREM", "every linearly independent list extends to a basis", "2B", 55, ["2.26"], ["basis", "linear_independence"], []),
        ("2.35", "DEFINITION", "dimension", "2C", 58, ["2.26"], ["dimension", "basis"], []),
        ("2.37", "THEOREM", "dimension of a subspace", "2C", 59, ["2.35"], ["dimension", "subspace"], []),
        ("2.38", "THEOREM", "linearly independent list of the right length is a basis", "2C", 59, ["2.35"], ["dimension", "basis"], []),
        ("2.43", "THEOREM", "dimension of a sum", "2C", 61, ["2.35", "1.41"], ["dimension", "direct_sum", "subspace"], []),
        ("3.1", "DEFINITION", "linear map", "3A", 66, ["1.20"], ["linear_map", "operator"], []),
        ("3.5", "DEFINITION", "addition and scalar multiplication on L(V, W)", "3A", 69, ["3.1"], ["linear_map"], []),
        ("3.11", "DEFINITION", "null space", "3B", 73, ["3.1"], ["null_space", "linear_map"], []),
        ("3.13", "THEOREM", "the null space is a subspace", "3B", 73, ["3.11"], ["null_space", "subspace"], []),
        ("3.15", "THEOREM", "injectivity equivalent to null space equals {0}", "3B", 74, ["3.11"], ["null_space", "isomorphism"], []),
        ("3.16", "DEFINITION", "range", "3B", 75, ["3.1"], ["range", "linear_map"], []),
        ("3.18", "THEOREM", "the range is a subspace", "3B", 75, ["3.16"], ["range", "subspace"], []),
        ("3.21", "THEOREM", "fundamental theorem of linear maps", "3B", 76, ["3.11", "3.16", "2.35"], ["rank_nullity", "dimension", "null_space", "range"], []),
        ("3.31", "DEFINITION", "matrix of a linear map", "3C", 83, ["3.1", "2.26"], ["matrix", "linear_map", "basis"], []),
        ("3.41", "DEFINITION", "matrix multiplication", "3C", 87, ["3.31"], ["matrix"], []),
        ("3.43", "THEOREM", "matrix of product of linear maps", "3C", 88, ["3.41"], ["matrix", "linear_map"], []),
        ("3.59", "DEFINITION", "invertible", "3D", 96, ["3.1"], ["isomorphism", "linear_map"], []),
        ("3.69", "DEFINITION", "isomorphism", "3D", 100, ["3.59"], ["isomorphism", "linear_map"], []),
        ("3.70", "THEOREM", "dimension shows whether vector spaces are isomorphic", "3D", 100, ["3.69", "2.35"], ["dimension", "isomorphism"], []),
        ("3.99", "DEFINITION", "quotient space", "3E", 113, ["1.33"], ["quotient_space", "subspace"], []),
        ("5.5", "DEFINITION", "eigenvalue", "5A", 148, ["3.1"], ["eigenvalue", "operator"], []),
        ("5.8", "DEFINITION", "eigenvector", "5A", 149, ["5.5"], ["eigenvalue", "operator"], []),
        ("5.10", "THEOREM", "linearly independent eigenvectors", "5A", 149, ["5.8"], ["eigenvalue", "linear_independence"], []),
        ("5.50", "DEFINITION", "diagonalizable", "5A", 177, ["5.5", "2.26"], ["diagonalizable", "eigenvalue", "basis"], []),
        ("5.55", "THEOREM", "conditions equivalent to diagonalizability", "5A", 179, ["5.50"], ["diagonalizable", "eigenvalue"], []),
        ("6.1", "DEFINITION", "inner product", "6A", 202, ["1.20"], ["inner_product"], ["inner_product"]),
        ("6.7", "DEFINITION", "norm", "6A", 204, ["6.1"], ["norm"], ["norm", "inner_product"]),
        ("6.10", "DEFINITION", "orthogonal", "6A", 205, ["6.1"], [], ["orthogonal", "inner_product"]),
        ("6.12", "THEOREM", "Pythagorean Theorem", "6A", 206, ["6.7", "6.10"], [], ["orthogonal", "norm"]),
        ("6.14", "THEOREM", "Cauchy-Schwarz Inequality", "6A", 206, ["6.1", "6.7"], ["norm"], ["inner_product", "norm"]),
        ("6.27", "DEFINITION", "orthonormal basis", "6B", 213, ["2.26"], ["basis"], ["orthonormal", "orthogonal", "inner_product"]),
        ("6.32", "THEOREM", "Gram-Schmidt procedure", "6B", 215, ["6.27"], ["basis", "span"], ["gram_schmidt", "orthonormal", "orthogonal"]),
        ("6.46", "DEFINITION", "orthogonal complement", "6C", 225, ["1.33"], ["subspace"], ["orthogonal", "complement", "inner_product"]),
        ("6.48", "THEOREM", "properties of orthogonal complement", "6C", 225, ["6.46"], ["subspace", "direct_sum"], ["orthogonal", "complement"]),
        ("6.55", "DEFINITION", "orthogonal projection", "6C", 228, ["6.46", "3.1"], ["linear_map", "operator"], ["projection", "orthogonal"]),
        ("6.57", "THEOREM", "properties of orthogonal projection", "6C", 229, ["6.55"], ["linear_map", "operator", "range", "null_space"], ["projection", "orthogonal"]),
        ("6.68", "DEFINITION", "pseudoinverse", "6C", 235, ["3.1"], ["pseudoinverse", "linear_map", "operator"], ["orthogonal", "projection"]),
        ("6.69", "THEOREM", "algebraic properties of the pseudoinverse", "6C", 235, ["6.68"], ["pseudoinverse", "linear_map"], ["projection"]),
        ("6.70", "THEOREM", "pseudoinverse provides best approximate solution", "6C", 236, ["6.68"], ["pseudoinverse"], ["norm", "distance", "orthogonal"]),
        ("7.10", "DEFINITION", "self-adjoint", "7A", 247, ["3.1"], ["operator"], ["self_adjoint", "inner_product"]),
        ("7.12", "THEOREM", "eigenvalues of self-adjoint operators", "7A", 247, ["7.10", "5.5"], ["eigenvalue", "operator"], ["self_adjoint"]),
        ("7.29", "THEOREM", "real spectral theorem", "7B", 259, ["7.10", "6.27"], ["diagonalizable", "basis", "eigenvalue"], ["spectral", "self_adjoint", "orthonormal"]),
        ("7.31", "THEOREM", "complex spectral theorem", "7B", 260, ["7.10", "6.27"], ["diagonalizable", "basis", "eigenvalue"], ["spectral", "self_adjoint", "orthonormal"]),
    ]

    decls: list[AxlerDeclaration] = []
    for num, kind, title, sec, pno, refs, eo_t, geo_t in mock_data:
        num_id = num.replace(".", "_")
        node_id = f"srcdecl:axler:{kind.lower()}:{num_id}"
        label = f"Axler {num} {kind.capitalize()} {title}"
        raw_mock = f"{num} {kind} {title} in section {sec}"
        h = hashlib.sha256(raw_mock.encode("utf-8")).hexdigest()
        
        status = "DUAL_DIRECT" if (eo_t and geo_t) else ("EO_ONLY_DIRECT" if eo_t else ("GEO_ONLY_DIRECT" if geo_t else "THEORETIC_DIRECT"))
        profile = {
            "eo_tags": sorted(eo_t),
            "geo_tags": sorted(geo_t),
            "direct_status": status,
        }
        decls.append(
            AxlerDeclaration(
                node_id=node_id,
                source_id=SOURCE_ID,
                label=label,
                decl_type=kind,
                chapter_section=sec,
                page=pno,
                statement_sha256=h,
                char_count=len(raw_mock),
                structural_refs=refs,
                representation_profile=profile,
            )
        )
    return decls


def get_axler_declarations(
    pdf_path: Path | None = None,
    slices: list[str] | None = None,
    use_mock: bool = False,
    auto_download: bool = True,
) -> list[AxlerDeclaration]:
    if use_mock:
        return generate_mock_axler_declarations()

    path = pdf_path or DEFAULT_CACHE_PATH
    if not path.exists():
        if auto_download:
            try:
                download_axler_pdf(path)
            except Exception as e:
                sys.stderr.write(f"Warning: Failed to download Axler PDF ({e}). Falling back to deterministic mock.\n")
                return generate_mock_axler_declarations()
        else:
            return generate_mock_axler_declarations()

    try:
        return parse_declarations_from_pdf(path, slices=slices)
    except Exception as e:
        sys.stderr.write(f"Warning: PDF parsing failed ({e}). Falling back to deterministic mock.\n")
        return generate_mock_axler_declarations()


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Axler LADR4e declarations for MAPEOGEO v0.12")
    parser.add_argument("--pdf-path", type=Path, default=DEFAULT_CACHE_PATH, help="Path to LADR4e.pdf")
    parser.add_argument("--out", type=Path, help="Output JSON path for extracted declarations metadata")
    parser.add_argument("--mock", action="store_true", help="Use deterministic mock declarations")
    parser.add_argument("--download", action="store_true", help="Force download PDF from official site")
    args = parser.parse_args()

    if args.download:
        download_axler_pdf(args.pdf_path)

    decls = get_axler_declarations(
        pdf_path=args.pdf_path,
        use_mock=args.mock,
        auto_download=True,
    )

    print(f"Extracted {len(decls)} Axler declarations.")
    dual_count = sum(1 for d in decls if d.representation_profile.get("direct_status") == "DUAL_DIRECT")
    eo_count = sum(1 for d in decls if d.representation_profile.get("direct_status") == "EO_ONLY_DIRECT")
    geo_count = sum(1 for d in decls if d.representation_profile.get("direct_status") == "GEO_ONLY_DIRECT")
    print(f"Profiles: {dual_count} DUAL_DIRECT, {eo_count} EO_ONLY_DIRECT, {geo_count} GEO_ONLY_DIRECT")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        out_dicts = [d.to_dict() for d in decls]
        # Strict zero prose verification
        for item in out_dicts:
            for forbidden in FORBIDDEN_PERSISTED_KEYS:
                assert forbidden not in item, f"Zero-prose violation: found '{forbidden}'"
        args.out.write_text(json.dumps(out_dicts, indent=2), encoding="utf-8")
        print(f"Saved declarations metadata to {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
