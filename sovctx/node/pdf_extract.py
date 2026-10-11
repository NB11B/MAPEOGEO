from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Optional

from .detect import detect_format
from .language import classify_text
from .passages import (
    PassageRecord,
    build_text_representations,
    detect_equation_witnesses,
    make_passage_id,
)
from .references import is_bibliography_header

try:
    import pypdf
except ImportError:
    pypdf = None  # type: ignore

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore


class MalformedPDFError(Exception):
    """Raised when PDF bytes cannot be parsed or are corrupted."""


class EncryptedPDFError(Exception):
    """Raised when PDF is password protected."""


@dataclass
class PDFExtractionResult:
    passages: list[PassageRecord]
    physical_page_count: int
    is_ocr_candidate: bool
    total_characters: int
    has_text_layer: bool


def detect_printed_page(lines: list[str]) -> tuple[Optional[str], Optional[str], float]:
    """Detect printed page number from header or footer lines with calibrated confidence."""
    if not lines:
        return None, None, 0.0

    candidates: list[tuple[str, str, float]] = []

    # Check top lines (header)
    for line in lines[:2]:
        clean = line.strip()
        # Single isolated number
        if re.match(r"^\d{1,4}$", clean):
            candidates.append((clean, "header_single_number", 0.95))
        # Roman numeral preface
        elif re.match(r"^(?:[ivxlcdm]+|[IVXLCDM]+)$", clean):
            candidates.append((clean.lower(), "header_roman_preface", 0.90))
        # Form like "- 12 -" or "— 12 —"
        m = re.match(r"^[\-—\s]*(\d{1,4})[\-—\s]*$", clean)
        if m:
            candidates.append((m.group(1), "header_decorated_number", 0.92))

    # Check bottom lines (footer)
    for line in lines[-2:]:
        clean = line.strip()
        if re.match(r"^\d{1,4}$", clean):
            candidates.append((clean, "footer_single_number", 0.95))
        elif re.match(r"^(?:[ivxlcdm]+|[IVXLCDM]+)$", clean):
            candidates.append((clean.lower(), "footer_roman_preface", 0.90))
        m = re.match(r"^[\-—\s]*(\d{1,4})[\-—\s]*$", clean)
        if m:
            candidates.append((m.group(1), "footer_decorated_number", 0.92))

    if candidates:
        # Sort by confidence descending
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates[0]

    return None, None, 0.0


def extract_pdf_passages(
    pdf_bytes: bytes,
    source_sha256: str,
) -> PDFExtractionResult:
    """Extract physical-page segmented passages and equation witnesses from a PDF deterministically."""
    fmt = detect_format(pdf_bytes)
    if fmt.is_encrypted:
        raise EncryptedPDFError("PDF is encrypted / password protected")

    pages_text: list[str] = []

    # Attempt extraction via pypdf or fitz
    if pypdf is not None:
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            if reader.is_encrypted:
                raise EncryptedPDFError("PDF is encrypted / password protected")
            for page in reader.pages:
                text = page.extract_text() or ""
                pages_text.append(text)
        except EncryptedPDFError:
            raise
        except Exception as exc:
            # Try fitz fallback if pypdf fails
            if fitz is not None:
                try:
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    if doc.is_encrypted:
                        raise EncryptedPDFError("PDF is encrypted")
                    pages_text = [page.get_text() for page in doc]
                except Exception:
                    raise MalformedPDFError(f"Corrupt or unreadable PDF: {exc}")
            else:
                raise MalformedPDFError(f"Corrupt or unreadable PDF: {exc}")
    elif fitz is not None:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if doc.is_encrypted:
                raise EncryptedPDFError("PDF is encrypted")
            pages_text = [page.get_text() for page in doc]
        except Exception as exc:
            raise MalformedPDFError(f"Corrupt or unreadable PDF: {exc}")
    else:
        raise RuntimeError("No PDF extraction backend (pypdf or fitz) available")

    total_chars = sum(len(p.strip()) for p in pages_text)
    page_count = len(pages_text)

    # Text density check: if less than 50 characters across document, treat as OCR candidate
    is_ocr_candidate = (total_chars < 50) or (page_count > 0 and (total_chars / page_count) < 20)

    passages: list[PassageRecord] = []
    if is_ocr_candidate:
        return PDFExtractionResult(
            passages=[],
            physical_page_count=page_count,
            is_ocr_candidate=True,
            total_characters=total_chars,
            has_text_layer=False,
        )

    in_bibliography = False
    source_id = f"SOVSRC:{source_sha256}"

    for page_idx, raw_page_text in enumerate(pages_text, start=1):
        if not raw_page_text.strip():
            continue

        lines = raw_page_text.splitlines()
        printed_page, printed_method, printed_conf = detect_printed_page(lines)

        # Break page into block paragraphs (split on double newlines)
        raw_blocks = re.split(r"\n\s*\n", raw_page_text)
        char_offset = 0

        for block_idx, block_text in enumerate(raw_blocks):
            clean_block = block_text.strip()
            if not clean_block:
                continue

            block_start = char_offset
            block_end = block_start + len(clean_block)
            char_offset = block_end + 2  # accounted for newline separator

            # Check for bibliography header
            first_line = clean_block.splitlines()[0]
            if is_bibliography_header(first_line):
                in_bibliography = True

            # Check if footnote
            is_fn = bool(re.match(r"^[\*†‡\d]{1,3}[\)\.]\s+", clean_block))
            # Check if table
            is_tbl = bool(
                re.match(r"^(?:таблица|table)\s+\d+", clean_block, re.IGNORECASE)
                or clean_block.count("\t") > 4
            )

            # Build 3 text representations
            text_src, text_uni, text_srch = build_text_representations(clean_block)

            # Language classification
            lang_analysis = classify_text(text_uni)

            # Generate passage ID
            pid = make_passage_id(
                source_sha256=source_sha256,
                page_physical=page_idx,
                block_index=block_idx,
                char_start=block_start,
                char_end=block_end,
            )

            # Equation witness detection
            eq_witnesses = detect_equation_witnesses(
                source_sha256=source_sha256,
                passage_id=pid,
                physical_page=page_idx,
                text=text_src,
                extraction_method="pdf_text",
            )

            record = PassageRecord(
                id=pid,
                source_id=source_id,
                page_physical=page_idx,
                page_printed=printed_page,
                page_printed_method=printed_method,
                page_printed_confidence=printed_conf,
                block_index=block_idx,
                char_start=block_start,
                char_end=block_end,
                text_source=text_src,
                text_unicode=text_uni,
                text_search=text_srch,
                language=lang_analysis.language,
                script=lang_analysis.script,
                language_confidence=lang_analysis.confidence,
                is_footnote=is_fn,
                is_table=is_tbl,
                is_reference=in_bibliography,
                equation_witnesses=eq_witnesses,
                extraction_method="pdf_text",
            )
            passages.append(record)

    return PDFExtractionResult(
        passages=passages,
        physical_page_count=page_count,
        is_ocr_candidate=False,
        total_characters=total_chars,
        has_text_layer=True,
    )
