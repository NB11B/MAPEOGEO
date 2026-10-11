from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from sovctx.node.config import NanoConfig
from sovctx.node.detect import detect_format
from sovctx.node.html_extract import extract_html_passages
from sovctx.node.ingest import IngestionEngine
from sovctx.node.language import classify_text
from sovctx.node.passages import (
    build_text_representations,
    detect_equation_witnesses,
    make_passage_id,
)
from sovctx.node.source import make_source_id
from sovctx.tools.qualify_n1 import run_n1_qualification


def test_detect_format() -> None:
    # 1. PDF
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"
    fmt_pdf = detect_format(pdf_bytes)
    assert fmt_pdf.is_pdf is True
    assert fmt_pdf.is_supported is True
    assert fmt_pdf.is_encrypted is False

    # 2. Encrypted PDF
    enc_pdf = b"%PDF-1.4\n/Encrypt 2 0 R\n%%EOF"
    fmt_enc = detect_format(enc_pdf)
    assert fmt_enc.is_pdf is True
    assert fmt_enc.is_encrypted is True
    assert fmt_enc.quarantine_reason == "ENCRYPTED_PASSWORD_PROTECTED_PDF"

    # 3. HTML
    html_bytes = b"<!DOCTYPE html><html><body><h1>Title</h1></body></html>"
    fmt_html = detect_format(html_bytes)
    assert fmt_html.is_html is True
    assert fmt_html.is_supported is True

    # 4. Image
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    fmt_img = detect_format(png_bytes)
    assert fmt_img.is_image is True
    assert fmt_img.is_supported is True


def test_classify_text_script_and_language() -> None:
    # Russian text
    ru_analysis = classify_text("Рассматривается краевая задача для уравнения Лапласа.")
    assert ru_analysis.script == "Cyrillic"
    assert ru_analysis.language == "ru"
    assert ru_analysis.confidence > 0.7

    # English text
    en_analysis = classify_text("We consider the boundary value problem for the Laplace equation.")
    assert en_analysis.script == "Latin"
    assert en_analysis.language == "en"
    assert en_analysis.confidence > 0.7

    # Mathematical text
    math_analysis = classify_text(r"\int_0^\infty e^{-st} f(t) dt = F(s)")
    assert math_analysis.script in ("Mathematical", "Latin")


def test_passage_preimage_and_text_tiers() -> None:
    raw = "Квазиустойчивое состояніе системы.  \u00A0  "
    src, uni, srch = build_text_representations(raw)

    # 1. text_source is exact
    assert src == raw
    # 2. text_unicode has safe NFC normalization and exotic space replacement, preserves Yat/I
    assert "состояніе" in uni
    assert "\u00A0" not in uni
    # 3. text_search is lowercased
    assert srch.strip().startswith("квазиустойчивое")

    pid = make_passage_id(
        source_sha256="abcd" * 16,
        page_physical=1,
        block_index=0,
        char_start=0,
        char_end=len(raw),
        representation_version="n1-v0.1",
    )
    assert pid.startswith("SOVPASS:")


def test_equation_witness_detection() -> None:
    text = "Основное уравнение движения: m*a = F, где F = -k*x. (1)"
    witnesses = detect_equation_witnesses(
        source_sha256="test_sha",
        passage_id="SOVPASS:test",
        physical_page=1,
        text=text,
        extraction_method="pdf_text",
    )
    assert len(witnesses) >= 1
    assert witnesses[0].source_id == "SOVSRC:test_sha"
    assert "=" in witnesses[0].extracted_surface


def test_html_passage_extraction() -> None:
    html = rb"""<!DOCTYPE html>
    <html>
    <body>
        <h1>Gelfand-Levitan 1951</h1>
        <p>On the determination of a differential equation from its spectral function.</p>
        <p>Linear integral equation K(x,y) + F(x,y) + \int K(x,s)F(s,y)ds = 0.</p>
    </body>
    </html>"""
    passages = extract_html_passages(html, "html_sha")
    assert len(passages) >= 2
    assert all(p.source_id == "SOVSRC:html_sha" for p in passages)
    assert all(p.page_physical == 1 for p in passages)


def test_n1_full_qualification_matrix() -> None:
    qualification_result = run_n1_qualification()
    assert qualification_result["verdict"] == "PASS"
    assert qualification_result["total_cases"] >= 13
