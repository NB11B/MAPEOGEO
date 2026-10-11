from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from .language import classify_text

REPRESENTATION_VERSION = "n1-v0.1"
EXTRACTOR_VERSION = "sovctx-extract-0.1"


def make_passage_id(
    source_sha256: str,
    page_physical: int,
    block_index: int,
    char_start: int,
    char_end: int,
    representation_version: str = REPRESENTATION_VERSION,
) -> str:
    """Compute deterministic passage identity including source hash and representation version."""
    preimage = (
        f"{source_sha256}\0"
        f"{representation_version}\0"
        f"{page_physical}\0"
        f"{block_index}\0"
        f"{char_start}\0"
        f"{char_end}"
    )
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:24]
    return f"SOVPASS:{digest}"


def make_equation_witness_id(source_sha256: str, passage_id: str, extracted_surface: str) -> str:
    preimage = f"{source_sha256}\0{passage_id}\0{extracted_surface.strip()}"
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:20]
    return f"SOVEQW:{digest}"


def build_text_representations(raw_text: str) -> tuple[str, str, str]:
    """Generate three strictly separated text representations:

    1. text_source: Exact witness as extracted, no alteration or modernization.
    2. text_unicode: Safe Unicode NFC normalization with preserved spelling & archaic glyphs.
    3. text_search: Lowercased, diacritics stripped, purely for derived indexing/FTS.
    """
    text_source = raw_text

    # Safe NFC normalization, standardize exotic whitespace without losing content
    normalized_nfc = unicodedata.normalize("NFC", raw_text)
    # Replace non-breaking and special spaces with standard space
    text_unicode = re.sub(r"[\u00A0\u2000-\u200B\u3000]", " ", normalized_nfc)

    # Search representation: lowercased, decompose and strip combining marks (stress marks/accents)
    # Note: Cyrillic combining breve (\u0306) forming 'й' from 'и' must be preserved,
    # as 'й' is a distinct Russian alphabet letter (consonant), not an optional accent.
    decomposed = unicodedata.normalize("NFD", text_unicode.lower())
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn" or c == "\u0306")
    text_search = unicodedata.normalize("NFC", stripped)

    return text_source, text_unicode, text_search


@dataclass
class EquationWitness:
    witness_id: str
    source_id: str
    passage_id: str
    physical_page: int
    bounding_locator: Optional[str]
    extracted_surface: str
    extraction_method: str
    confidence: float


@dataclass
class PassageRecord:
    id: str
    source_id: str  # SOVSRC:<blob_sha256>
    page_physical: int
    page_printed: Optional[str]
    page_printed_method: Optional[str]
    page_printed_confidence: float
    block_index: int
    char_start: int
    char_end: int
    text_source: str
    text_unicode: str
    text_search: str
    language: str
    script: str
    language_confidence: float
    is_footnote: bool = False
    is_table: bool = False
    is_reference: bool = False
    equation_witnesses: list[EquationWitness] = field(default_factory=list)
    extraction_method: str = "pdf_text"
    extractor_version: str = EXTRACTOR_VERSION
    representation_version: str = REPRESENTATION_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "page_physical": self.page_physical,
            "page_printed": self.page_printed,
            "page_printed_method": self.page_printed_method,
            "page_printed_confidence": self.page_printed_confidence,
            "block_index": self.block_index,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "text_source": self.text_source,
            "text_unicode": self.text_unicode,
            "text_search": self.text_search,
            "language": self.language,
            "script": self.script,
            "language_confidence": self.language_confidence,
            "is_footnote": self.is_footnote,
            "is_table": self.is_table,
            "is_reference": self.is_reference,
            "equation_witnesses": [asdict(w) for w in self.equation_witnesses],
            "extraction_method": self.extraction_method,
            "extractor_version": self.extractor_version,
            "representation_version": self.representation_version,
        }

    def to_candidate_fragment(self) -> dict[str, Any]:
        locator = f"p.{self.page_physical}#b{self.block_index}"
        if self.page_printed:
            locator += f" [printed: {self.page_printed}]"
        return {
            "id": self.id,
            "candidate_source_id": self.source_id,
            "source_url": "",
            "sha256": self.source_id.replace("SOVSRC:", ""),
            "locator": locator,
            "candidate_json": json.dumps(self.to_dict(), ensure_ascii=False),
            "status": "CANDIDATE",
        }


# Mathematical pattern heuristics for detecting equation witnesses without normalizing them
EQUATION_PATTERNS = [
    re.compile(r"\$\$([^$]+)\$\$"),  # Display LaTeX
    re.compile(r"\$([^$]{3,})\$"),   # Inline LaTeX
    re.compile(r"\b([a-zA-Z\u0370-\u03FF\u0400-\u04FF]\s*=\s*[^;\.\n]{3,}\b(?:\s*\(\d+[\.\d]*\))?)"),  # Standard equalities
    re.compile(r"\\(?:begin|int|sum|prod|frac|partial|sqrt)"),
    re.compile(r"\b\d+\s*=\s*[\w\+\-\*/\^\(\)]+"),
]


def detect_equation_witnesses(
    source_sha256: str,
    passage_id: str,
    physical_page: int,
    text: str,
    extraction_method: str,
) -> list[EquationWitness]:
    """Detect candidate mathematical equation witnesses without modifying native source notation."""
    witnesses: list[EquationWitness] = []
    seen: set[str] = set()

    for pattern in EQUATION_PATTERNS:
        for match in pattern.finditer(text):
            surface = match.group(0).strip()
            if len(surface) < 3 or surface in seen:
                continue
            # Filter trivial matches like single words with '='
            if "=" in surface or "\\" in surface:
                seen.add(surface)
                wid = make_equation_witness_id(source_sha256, passage_id, surface)
                witnesses.append(
                    EquationWitness(
                        witness_id=wid,
                        source_id=f"SOVSRC:{source_sha256}",
                        passage_id=passage_id,
                        physical_page=physical_page,
                        bounding_locator=f"char:{match.start()}-{match.end()}",
                        extracted_surface=surface,
                        extraction_method=extraction_method,
                        confidence=0.85,
                    )
                )

    return witnesses
