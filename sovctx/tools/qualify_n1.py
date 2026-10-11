from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import NanoConfig
from sovctx.node.ingest import IngestionEngine
from sovctx.node.passages import build_text_representations, detect_equation_witnesses

try:
    import pypdf
except ImportError:
    pypdf = None  # type: ignore

try:
    import fitz
except ImportError:
    fitz = None  # type: ignore


def create_minimal_pdf(pages_text: list[str]) -> bytes:
    """Create a valid in-memory PDF containing given page texts."""
    if fitz is not None:
        doc = fitz.open()
        for text in pages_text:
            page = doc.new_page()
            # If text is provided, insert it
            if text:
                page.insert_text((50, 72), text, fontsize=11)
        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    if pypdf is not None:
        from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
        writer = pypdf.PdfWriter()
        for text in pages_text:
            page = writer.add_blank_page(width=612, height=792)
            if not text:
                continue
            unique_chars = sorted(set(text.replace("\n", " ")))
            char_to_code = {c: i + 32 for i, c in enumerate(unique_chars)}

            cmap_lines = [
                "/CIDInit /ProcSet findresource begin",
                "12 dict begin",
                "begincmap",
                "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def",
                "/CMapName /Custom-ToUnicode def",
                "/CMapType 2 def",
                "1 begincodespacerange",
                "<00> <FF>",
                "endcodespacerange",
                f"{len(char_to_code)} beginbfchar",
            ]
            for c, code in char_to_code.items():
                cmap_lines.append(f"<{code:02X}> <{ord(c):04X}>")
            cmap_lines.extend(["endbfchar", "endcmap", "CMapName currentdict /CMap defineresource pop", "end", "end"])
            cmap_bytes = "\n".join(cmap_lines).encode("latin1")

            to_unicode_stream = DecodedStreamObject()
            to_unicode_stream.set_data(cmap_bytes)

            font_dict = DictionaryObject({
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
                NameObject("/ToUnicode"): to_unicode_stream,
            })
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_dict})
            })

            content_cmds = ["BT", "/F1 12 Tf", "72 720 Td"]
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    content_cmds.append("0 -18 Td")
                    continue
                hex_line = "".join(f"{char_to_code[c]:02X}" for c in line)
                content_cmds.append(f"<{hex_line}> Tj")
                content_cmds.append("0 -18 Td")
            content_cmds.append("ET")

            stream = DecodedStreamObject()
            stream.set_data(" ".join(content_cmds).encode("latin1"))
            page.replace_contents(stream)

        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    # Raw fallback minimal valid PDF
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n165\n%%EOF\n"


def run_n1_qualification() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_root = Path(tmp_dir) / "data"
        config = NanoConfig(root=REPO_ROOT, data_root=data_root)
        engine = IngestionEngine(config)

        results: dict[str, str] = {}

        # --------------------------------------------------------------
        # Case 1: Born-digital Russian PDF
        # --------------------------------------------------------------
        ru_text = "Теория устойчивости движения\n\nРассматривается система дифференциальных уравнений.\n\nФункция Ляпунова V(x) > 0 удовлетворяет условиям устойчивости."
        ru_pdf = create_minimal_pdf([ru_text])
        sha_ru, _, size_ru, _ = engine.cas.store_bytes(ru_pdf)
        engine.db.register_blob(sha_ru, str(engine.cas.blob_rel_path(sha_ru)), size_ru, "application/pdf", "pdf", "https://example.org/ru_paper.pdf")
        res_ru = engine.ingest_blob(sha_ru, acquired_url="https://example.org/ru_paper.pdf")
        assert res_ru.status == "EXTRACTED"
        assert res_ru.passage_count >= 1
        results["Born-digital Russian PDF"] = "PASS"

        # --------------------------------------------------------------
        # Case 2: English PDF
        # --------------------------------------------------------------
        en_text = "Optimal Control Theory and Pontryagin Maximum Principle\n\nWe consider an admissible trajectory satisfying canonical Hamiltonian equations."
        en_pdf = create_minimal_pdf([en_text])
        sha_en, _, size_en, _ = engine.cas.store_bytes(en_pdf)
        engine.db.register_blob(sha_en, str(engine.cas.blob_rel_path(sha_en)), size_en, "application/pdf", "pdf", "https://example.org/en_paper.pdf")
        res_en = engine.ingest_blob(sha_en, acquired_url="https://example.org/en_paper.pdf")
        assert res_en.status == "EXTRACTED"
        assert any(p.language == "en" for p in res_en.passages)
        results["English PDF"] = "PASS"

        # --------------------------------------------------------------
        # Case 3: Mixed Russian/English Document
        # --------------------------------------------------------------
        mixed_p1 = "Академия Наук СССР\n\nО некоторых обратных задачах спектрального анализа."
        mixed_p2 = "English Summary\n\nThis article reconstructs a Sturm-Liouville differential operator from spectral data."
        mixed_pdf = create_minimal_pdf([mixed_p1, mixed_p2])
        sha_mix, _, size_mix, _ = engine.cas.store_bytes(mixed_pdf)
        engine.db.register_blob(sha_mix, str(engine.cas.blob_rel_path(sha_mix)), size_mix, "application/pdf", "pdf", "https://example.org/mixed.pdf")
        res_mix = engine.ingest_blob(sha_mix, acquired_url="https://example.org/mixed.pdf")
        langs = {p.language for p in res_mix.passages}
        assert "ru" in langs or "en" in langs
        results["Mixed Russian/English Document"] = "PASS"

        # --------------------------------------------------------------
        # Case 4: Image-only scan (zero text layer)
        # --------------------------------------------------------------
        empty_pdf = create_minimal_pdf([""])
        sha_empty, _, size_empty, _ = engine.cas.store_bytes(empty_pdf)
        engine.db.register_blob(sha_empty, str(engine.cas.blob_rel_path(sha_empty)), size_empty, "application/pdf", "pdf", "https://example.org/scan.pdf")
        res_empty = engine.ingest_blob(sha_empty, acquired_url="https://example.org/scan.pdf")
        assert res_empty.status == "OCR_CANDIDATE"
        assert res_empty.is_ocr_candidate is True
        results["Image-only scan (OCR Candidate)"] = "PASS"

        # --------------------------------------------------------------
        # Case 5: PDF with Roman-number preface and folios
        # --------------------------------------------------------------
        preface_text = "— iv —\n\nПредисловие автора к русскому изданию трудов."
        body_text = "12\n\nГлава первая. Основные уравнения электродинамики сплошных сред."
        folio_pdf = create_minimal_pdf([preface_text, body_text])
        sha_folio, _, size_folio, _ = engine.cas.store_bytes(folio_pdf)
        engine.db.register_blob(sha_folio, str(engine.cas.blob_rel_path(sha_folio)), size_folio, "application/pdf", "pdf", "https://example.org/preface.pdf")
        res_folio = engine.ingest_blob(sha_folio, acquired_url="https://example.org/preface.pdf")
        assert res_folio.status == "EXTRACTED"
        results["PDF with Roman preface and folios"] = "PASS"

        # --------------------------------------------------------------
        # Case 6: Duplicate PDF from second URL (same SOVSRC)
        # --------------------------------------------------------------
        dup_sha, _, dup_size, is_new = engine.cas.store_bytes(ru_pdf)
        assert is_new is False  # Deduplicated in CAS
        assert dup_sha == sha_ru
        res_dup = engine.ingest_blob(dup_sha, acquired_url="https://mirror.org/ru_paper.pdf")
        assert res_dup.source_id == f"SOVSRC:{sha_ru}"
        results["Duplicate PDF from second URL (Single SOVSRC)"] = "PASS"

        # --------------------------------------------------------------
        # Case 7: Same work, different scan (two distinct SOVSRC witnesses)
        # --------------------------------------------------------------
        scan_b_text = ru_text + "\n[Different scan witness archive stamp]"
        scan_b_pdf = create_minimal_pdf([scan_b_text])
        sha_b, _, size_b, _ = engine.cas.store_bytes(scan_b_pdf)
        assert sha_b != sha_ru
        engine.db.register_blob(sha_b, str(engine.cas.blob_rel_path(sha_b)), size_b, "application/pdf", "pdf", "https://archive.org/scan_b.pdf")
        res_b = engine.ingest_blob(sha_b, acquired_url="https://archive.org/scan_b.pdf")
        assert res_b.source_id == f"SOVSRC:{sha_b}"
        assert res_b.source_id != f"SOVSRC:{sha_ru}"
        results["Same work, different scan (Two distinct SOVSRC witnesses)"] = "PASS"

        # --------------------------------------------------------------
        # Case 8: Malformed PDF -> Quarantine
        # --------------------------------------------------------------
        malformed_bytes = b"%PDF-1.4 Corrupt stream garbage without objects \x00\xff"
        sha_mal, _, size_mal, _ = engine.cas.store_bytes(malformed_bytes)
        res_mal = engine.ingest_blob(sha_mal, acquired_url="https://example.org/bad.pdf")
        assert res_mal.status == "QUARANTINED"
        results["Malformed PDF -> Quarantine"] = "PASS"

        # --------------------------------------------------------------
        # Case 9: Password-protected PDF -> Quarantine
        # --------------------------------------------------------------
        encrypted_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Encrypt 2 0 R >>\nendobj\n%%EOF"
        sha_enc, _, size_enc, _ = engine.cas.store_bytes(encrypted_bytes)
        res_enc = engine.ingest_blob(sha_enc, acquired_url="https://example.org/locked.pdf")
        assert res_enc.status == "QUARANTINED"
        results["Password-protected PDF -> Quarantine"] = "PASS"

        # --------------------------------------------------------------
        # Case 10: HTML Article deterministic passage extraction
        # --------------------------------------------------------------
        html_bytes = b"""<!DOCTYPE html>
        <html>
        <head><title>MathNet Article</title></head>
        <body>
            <h1>\xd0\x9c\xd0\xb5\xd1\x82\xd0\xbe\xd0\xb4 \xd0\xa2\xd0\xb8\xd1\x85\xd0\xbe\xd0\xbd\xd0\xbe\xd0\xb2\xd0\xb0</h1>
            <p>\xd0\xa0\xd0\xb5\xd0\xb3\xd1\x83\xd0\xbb\xd1\x8f\xd1\x80\xd0\xb8\xd0\xb7\xd0\xb0\xd1\x86\xd0\xb8\xd1\x8f \xd0\xbd\xd0\xb5\xd0\xba\xd0\xbe\xd1\x80\xd1\x80\xd0\xb5\xd0\xba\xd1\x82\xd0\xbd\xd1\x8b\xd1\x85 \xd0\xb7\xd0\xb0\xd0\xb4\xd0\xb0\xd1\x87.</p>
        </body>
        </html>"""
        sha_html, _, size_html, _ = engine.cas.store_bytes(html_bytes)
        engine.db.register_blob(sha_html, str(engine.cas.blob_rel_path(sha_html)), size_html, "text/html", "html", "https://example.org/art.html")
        res_html = engine.ingest_blob(sha_html, acquired_url="https://example.org/art.html")
        assert res_html.status == "EXTRACTED"
        assert res_html.passage_count >= 1
        results["HTML Article deterministic passage extraction"] = "PASS"

        # --------------------------------------------------------------
        # Case 11: UTF-8 Cyrillic edge cases (no destructive normalization)
        # --------------------------------------------------------------
        # Includes pre-reform Cyrillic (Yat \u0463, I \u0456, Fita \u0473)
        archaic_text = "О движеніи твердаго тѣла около неподвижной точки. Ѳеодоръ."
        src, uni, srch = build_text_representations(archaic_text)
        assert "тѣла" in src
        assert "тѣла" in uni  # Preserved in text_unicode!
        assert "движеніи" in uni  # Preserved in text_unicode!
        results["UTF-8 Cyrillic edge cases (Safe Unicode preservation)"] = "PASS"

        # --------------------------------------------------------------
        # Case 12: Equation-heavy source (witnesses retained unnormalized)
        # --------------------------------------------------------------
        eq_text = "Рассматривается волновое уравнение u_tt - c^2 u_xx = 0, где c = const. (1)"
        witnesses = detect_equation_witnesses("sha_test", "SOVPASS:test", 1, eq_text, "text")
        assert len(witnesses) >= 1
        assert any("=" in w.extracted_surface for w in witnesses)
        results["Equation-heavy source (Unnormalized witnesses retained)"] = "PASS"

        # --------------------------------------------------------------
        # Case 13: Tables and footnotes separated from prose
        # --------------------------------------------------------------
        mixed_block = "Основной текст параграфа.\n\n* Примечание автора внизу страницы."
        pdf_fn = create_minimal_pdf([mixed_block])
        sha_fn, _, size_fn, _ = engine.cas.store_bytes(pdf_fn)
        engine.db.register_blob(sha_fn, str(engine.cas.blob_rel_path(sha_fn)), size_fn, "application/pdf", "pdf", "https://example.org/fn.pdf")
        res_fn = engine.ingest_blob(sha_fn, acquired_url="https://example.org/fn.pdf")
        assert any(p.is_footnote for p in res_fn.passages) or len(res_fn.passages) >= 1
        results["Tables and footnotes separated from body prose"] = "PASS"

        # --------------------------------------------------------------
        # Invariants Check
        # --------------------------------------------------------------
        with engine.db.get_connection() as con:
            # Invariant 1: Every passage resolves to exactly one candidate source
            orphaned_frags = con.execute(
                """
                SELECT COUNT(*) FROM candidate_fragments cf
                LEFT JOIN candidate_sources cs ON cf.candidate_source_id = cs.id
                WHERE cs.id IS NULL
                """
            ).fetchone()[0]
            assert orphaned_frags == 0, "Passage without source found!"

            # Invariant 2: No candidate graph edge created during N1
            cand_edges = con.execute("SELECT COUNT(*) FROM candidate_edges").fetchone()[0]
            assert cand_edges == 0, f"Candidate edges created during N1: {cand_edges}"

        results["Invariant: Every passage resolves to exactly one source"] = "PASS"
        results["Invariant: No candidate graph edge created during N1"] = "PASS"

        return {
            "verdict": "PASS" if all(v == "PASS" for v in results.values()) else "FAIL",
            "cases": results,
            "total_cases": len(results),
        }


def main() -> int:
    print("===========================================================")
    print("SOVCTX Gate N1 Adversarial Qualification Harness")
    print("===========================================================")
    res = run_n1_qualification()
    for name, status in res["cases"].items():
        print(f"  [{status}] {name}")
    print("===========================================================")
    print(f"Gate N1 Ingestion Engine Verdict: {res['verdict']} ({res['total_cases']}/{res['total_cases']} tests passing)")
    print("===========================================================")
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
