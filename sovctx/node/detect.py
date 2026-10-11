from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class FormatClassification:
    mime_type: str
    is_supported: bool
    is_pdf: bool
    is_html: bool
    is_text: bool
    is_image: bool
    is_encrypted: bool
    has_text_layer: bool
    character_count: int
    quarantine_reason: Optional[str] = None


def detect_format(data: bytes) -> FormatClassification:
    """Detect document format and inspect text characteristics deterministically."""
    if not data:
        return FormatClassification(
            mime_type="application/x-empty",
            is_supported=False,
            is_pdf=False,
            is_html=False,
            is_text=False,
            is_image=False,
            is_encrypted=False,
            has_text_layer=False,
            character_count=0,
            quarantine_reason="EMPTY_PAYLOAD",
        )

    # 1. PDF Check
    if data.startswith(b"%PDF-"):
        # Check for encryption marker
        is_encrypted = b"/Encrypt" in data
        if is_encrypted:
            return FormatClassification(
                mime_type="application/pdf",
                is_supported=False,
                is_pdf=True,
                is_html=False,
                is_text=False,
                is_image=False,
                is_encrypted=True,
                has_text_layer=False,
                character_count=0,
                quarantine_reason="ENCRYPTED_PASSWORD_PROTECTED_PDF",
            )

        # Quick check for presence of stream text operators (BT ... ET, /Font)
        has_text_operators = (b"BT" in data and b"ET" in data) or (b"/Font" in data)

        return FormatClassification(
            mime_type="application/pdf",
            is_supported=True,
            is_pdf=True,
            is_html=False,
            is_text=False,
            is_image=False,
            is_encrypted=False,
            has_text_layer=has_text_operators,
            character_count=0,
            quarantine_reason=None,
        )

    # 2. HTML Check
    sample = data[:2048].strip().lower()
    if (
        sample.startswith(b"<!doctype html")
        or sample.startswith(b"<html")
        or (b"<html" in sample and b"</html>" in data[-2048:].lower())
    ):
        return FormatClassification(
            mime_type="text/html",
            is_supported=True,
            is_pdf=False,
            is_html=True,
            is_text=False,
            is_image=False,
            is_encrypted=False,
            has_text_layer=True,
            character_count=len(data),
            quarantine_reason=None,
        )

    # 3. Image / Scan Check
    if (
        data.startswith(b"\x89PNG\r\n\x1a\n")
        or data.startswith(b"\xff\xd8\xff")
        or data.startswith(b"II*\x00")
        or data.startswith(b"MM\x00*")
        or data.startswith(b"RIFF") and b"WEBP" in data[:16]
    ):
        return FormatClassification(
            mime_type="image/scan",
            is_supported=True,
            is_pdf=False,
            is_html=False,
            is_text=False,
            is_image=True,
            is_encrypted=False,
            has_text_layer=False,
            character_count=0,
            quarantine_reason=None,
        )

    # 4. Plain Text Check
    try:
        decoded = data.decode("utf-8")
        # Check ratio of printable text to control chars
        control_chars = sum(1 for c in decoded[:2048] if ord(c) < 32 and c not in "\t\n\r")
        if control_chars / max(1, min(len(decoded), 2048)) < 0.05:
            return FormatClassification(
                mime_type="text/plain",
                is_supported=True,
                is_pdf=False,
                is_html=False,
                is_text=True,
                is_image=False,
                is_encrypted=False,
                has_text_layer=True,
                character_count=len(decoded),
                quarantine_reason=None,
            )
    except UnicodeDecodeError:
        pass

    # 5. Unsupported binary
    return FormatClassification(
        mime_type="application/octet-stream",
        is_supported=False,
        is_pdf=False,
        is_html=False,
        is_text=False,
        is_image=False,
        is_encrypted=False,
        has_text_layer=False,
        character_count=0,
        quarantine_reason="UNSUPPORTED_BINARY_FORMAT",
    )
