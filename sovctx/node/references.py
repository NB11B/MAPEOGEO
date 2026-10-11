from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


BIBLIOGRAPHY_HEADERS = [
    re.compile(r"^\s*(?:список\s+(?:цитированной\s+)?литературы|литература|библиография|библиографический\s+список)\s*[:\.]?$", re.IGNORECASE),
    re.compile(r"^\s*(?:references|bibliography|works\s+cited|literature\s+cited)\s*[:\.]?$", re.IGNORECASE),
]

REFERENCE_ITEM_PATTERN = re.compile(
    r"^(?:\[\d+\]|\d+[\.\)])\s+(.*)",
    re.MULTILINE
)


@dataclass
class ReferenceCandidate:
    raw_reference: str
    reference_index: Optional[int]
    authors_extracted: list[str]
    year_extracted: Optional[int]
    title_extracted: Optional[str]


def is_bibliography_header(line: str) -> bool:
    clean = line.strip()
    return any(p.match(clean) for p in BIBLIOGRAPHY_HEADERS)


def extract_references_from_text(text: str) -> list[ReferenceCandidate]:
    """Extract individual reference items from a bibliography block deterministically."""
    candidates: list[ReferenceCandidate] = []
    lines = text.splitlines()

    current_item: list[str] = []
    current_idx: Optional[int] = None

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        match = re.match(r"^(?:\[(\d+)\]|(\d+)[\.\)])\s*(.*)", line_str)
        if match:
            # Flush previous item
            if current_item:
                full_text = " ".join(current_item).strip()
                candidates.append(_parse_reference_item(full_text, current_idx))
                current_item = []

            num_str = match.group(1) or match.group(2)
            current_idx = int(num_str) if num_str and num_str.isdigit() else None
            rest = match.group(3)
            if rest:
                current_item.append(rest)
        else:
            if current_item:
                current_item.append(line_str)

    if current_item:
        full_text = " ".join(current_item).strip()
        candidates.append(_parse_reference_item(full_text, current_idx))

    return candidates


def _parse_reference_item(raw_text: str, index: Optional[int]) -> ReferenceCandidate:
    # Extract 4-digit year (1800-2029)
    year_match = re.search(r"\b(18\d{2}|19\d{2}|20[0-2]\d)\b", raw_text)
    year = int(year_match.group(1)) if year_match else None

    # Simple heuristic author extraction: words before initials or year
    author_matches = re.findall(
        r"\b([А-ЯЁA-Z][а-яёa-z]+)\s+([А-ЯЁA-Z]\.\s*[А-ЯЁA-Z]\.?)", raw_text
    )
    authors = [f"{m[0]} {m[1].strip()}" for m in author_matches]

    return ReferenceCandidate(
        raw_reference=raw_text,
        reference_index=index,
        authors_extracted=authors,
        year_extracted=year,
        title_extracted=None,
    )
