from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


def make_reference_id(
    source_sha: str,
    passage_id: str,
    reference_index: Optional[int],
    normalized_raw_ref: str,
) -> str:
    """Generate deterministic reference candidate ID bound to source, passage, and raw text."""
    idx_str = str(reference_index) if reference_index is not None else "0"
    preimage = f"{source_sha}\0{passage_id}\0{idx_str}\0{normalized_raw_ref.strip()}"
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:20]
    return f"SOVREF:{digest}"


@dataclass
class ReferenceCandidateRecord:
    id: str
    source_id: str
    passage_id: str
    reference_index: Optional[int]
    raw_reference: str
    authors_raw: Optional[str] = None  # JSON encoded list of author strings
    title_raw: Optional[str] = None
    publication_raw: Optional[str] = None
    year_raw: Optional[int] = None
    volume_raw: Optional[str] = None
    issue_raw: Optional[str] = None
    pages_raw: Optional[str] = None
    identifier_raw: Optional[str] = None
    language: str = "ru"
    extraction_method: str = "regex_citations_v0.2"
    confidence: float = 0.85

    def authors_list(self) -> list[str]:
        if not self.authors_raw:
            return []
        try:
            val = json.loads(self.authors_raw)
            if isinstance(val, list):
                return val
            return [str(val)]
        except Exception:
            return [self.authors_raw]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Soviet Bibliographic Extraction Patterns
# ---------------------------------------------------------------------------

# Author patterns:
# 1. Russian: "Тихонов А. Н.", "Тихонов А.Н.", "А. Н. Тихонов", "А.Н. Тихонов"
# 2. Latin: "Tikhonov A. N.", "A. N. Tikhonov"
AUTHOR_SURNAME_INITIALS = re.compile(
    r"\b([А-ЯЁA-Z][а-яёa-z]+)\s+([А-ЯЁA-Z]\.\s*[А-ЯЁA-Z]\.?|[А-ЯЁA-Z]\.)",
)
AUTHOR_INITIALS_SURNAME = re.compile(
    r"\b([А-ЯЁA-Z]\.\s*[А-ЯЁA-Z]\.?|[А-ЯЁA-Z]\.)\s+([А-ЯЁA-Z][а-яёa-z]+)",
)

# Year pattern: 1800 - 2029
YEAR_PATTERN = re.compile(r"\b(18\d{2}|19\d{2}|20[0-2]\d)(?:\s*г\.?)?\b")

# Volume pattern: "Т. 151", "Т. 39", "Vol. 151"
VOLUME_PATTERN = re.compile(r"\b(?:Т\.|Том|Vol\.|Volume)\s*(\d+)\b", re.IGNORECASE)

# Issue pattern: "№ 3", "вып. 4", "Вып. 4", "No. 3", "Issue 2"
ISSUE_PATTERN = re.compile(r"(?:№|вып\.|Вып\.|No\.|Issue)\s*(\d+)", re.IGNORECASE)

# Pages pattern: "С. 501–504", "С. 195-198", "pp. 12-18", "501–504 с."
PAGES_PATTERN = re.compile(
    r"(?:С\.|с\.|pp\.|p\.)\s*(\d+(?:[\u2013\u2014\-–]\d+)?)\b|\b(\d+)\s*(?:с|p)\.",
    re.IGNORECASE,
)

# Identifiers:
# DOI
DOI_PATTERN = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b", re.IGNORECASE)

# Math-Net.Ru
MATHNET_PATTERN = re.compile(
    r"(?:mathnet\.ru/(?:php/archive\.phtml\?.*?paperid=|present/)?([a-zA-Z0-9]+)|mathnet:([a-zA-Z0-9]+))",
    re.IGNORECASE,
)

# arXiv
ARXIV_PATTERN = re.compile(r"\b(arXiv:\s*\d{4}\.\d{4,5}(?:v\d+)?)\b", re.IGNORECASE)

# URL
URL_PATTERN = re.compile(r"(https?://\S+)")


def extract_authors(text: str) -> list[str]:
    """Extract list of structured author names in 'Surname I. O.' format."""
    authors: list[str] = []
    seen: set[str] = set()

    for m in AUTHOR_SURNAME_INITIALS.finditer(text):
        surname, initials = m.group(1), m.group(2).replace(" ", "")
        name = f"{surname} {initials}"
        if name not in seen:
            seen.add(name)
            authors.append(name)

    for m in AUTHOR_INITIALS_SURNAME.finditer(text):
        initials, surname = m.group(1).replace(" ", ""), m.group(2)
        name = f"{surname} {initials}"
        if name not in seen:
            seen.add(name)
            authors.append(name)

    return authors


def extract_identifier(text: str) -> Optional[str]:
    """Extract standardized identifier (DOI, Math-Net, arXiv, or URL)."""
    doi_m = DOI_PATTERN.search(text)
    if doi_m:
        return f"doi:{doi_m.group(1)}"

    mathnet_m = MATHNET_PATTERN.search(text)
    if mathnet_m:
        pid = mathnet_m.group(1) or mathnet_m.group(2)
        return f"mathnet:{pid}"

    arxiv_m = ARXIV_PATTERN.search(text)
    if arxiv_m:
        return arxiv_m.group(1)

    url_m = URL_PATTERN.search(text)
    if url_m:
        return url_m.group(1)

    return None


def parse_single_reference(
    raw_text: str,
    source_id: str,
    passage_id: str,
    reference_index: Optional[int] = None,
) -> ReferenceCandidateRecord:
    """Parse an individual bibliographic reference item into structured fields."""
    clean_text = raw_text.strip()
    source_sha = source_id.replace("SOVSRC:", "")

    # Index prefix removal if present in text, e.g. "[1] ..." or "1. ..."
    prefix_m = re.match(r"^(?:\[(\d+)\]|(\d+)[\.\)])\s*(.*)", clean_text)
    if prefix_m:
        idx_str = prefix_m.group(1) or prefix_m.group(2)
        if reference_index is None and idx_str.isdigit():
            reference_index = int(idx_str)
        content_text = prefix_m.group(3).strip()
    else:
        content_text = clean_text

    # Extract year
    year_m = YEAR_PATTERN.search(content_text)
    year = int(year_m.group(1)) if year_m else None

    # Extract volume
    vol_m = VOLUME_PATTERN.search(content_text)
    volume = vol_m.group(1) if vol_m else None

    # Extract issue
    iss_m = ISSUE_PATTERN.search(content_text)
    issue = iss_m.group(1) if iss_m else None

    # Extract pages
    pages_m = PAGES_PATTERN.search(content_text)
    pages = (pages_m.group(1) or pages_m.group(2)) if pages_m else None

    # Extract identifier
    identifier = extract_identifier(content_text)

    # Extract authors and title/publication:
    # Standard Soviet reference format:
    # Authors. Title // Journal. Year. Vol. Issue. Pages.
    # OR: Authors. Title. M.: Publisher, Year.
    authors: list[str] = []
    title: Optional[str] = None
    publication: Optional[str] = None

    if "//" in content_text:
        parts = content_text.split("//", 1)
        before_slash = parts[0].strip()
        after_slash = parts[1].strip()

        authors = extract_authors(before_slash)
        # Title is what remains of before_slash after removing authors
        title_cand = before_slash
        for a in authors:
            title_cand = title_cand.replace(a, "").strip()
        # Clean leading/trailing punctuation
        title = title_cand.strip(" .,-–—") if title_cand else None

        # Publication venue is the text in after_slash before year / volume
        pub_cand = after_slash
        # Cut off at year or volume if present
        if year_m and str(year) in pub_cand:
            pub_cand = pub_cand.split(str(year))[0]
        pub_cand = re.split(r"\b(?:Т\.|Том|Vol\.|№|Вып\.|вып\.)\b", pub_cand)[0]
        pub_cand = pub_cand.strip(" .,-–—")
        publication = pub_cand if pub_cand else None
    else:
        authors = extract_authors(content_text)
        # Attempt to split title and publisher/location
        rem = content_text
        for a in authors:
            rem = rem.replace(a, "").strip()
        rem = rem.strip(" .,-–—")
        # Split on city/publisher pattern: e.g. "М.: Наука" or "М.: Гостехиздат"
        pub_split = re.split(r"\b([М|Л|СПб|Киев|Харьков|Новосибирск]\s*:\s*[^,\.]+)", rem)
        if len(pub_split) > 1:
            title = pub_split[0].strip(" .,-–—")
            publication = pub_split[1].strip(" .,-–—")
        else:
            title = rem if rem else None

    # Language heuristic
    has_cyrillic = bool(re.search(r"[\u0400-\u04FF]", content_text))
    language = "ru" if has_cyrillic else "en"

    ref_id = make_reference_id(source_sha, passage_id, reference_index, content_text)

    return ReferenceCandidateRecord(
        id=ref_id,
        source_id=source_id,
        passage_id=passage_id,
        reference_index=reference_index,
        raw_reference=content_text,
        authors_raw=json.dumps(authors, ensure_ascii=False) if authors else None,
        title_raw=title,
        publication_raw=publication,
        year_raw=year,
        volume_raw=volume,
        issue_raw=issue,
        pages_raw=pages,
        identifier_raw=identifier,
        language=language,
        extraction_method="regex_citations_v0.2",
        confidence=0.88 if authors and (title or year) else 0.70,
    )


def extract_references_from_passage(
    passage_text: str,
    source_id: str,
    passage_id: str,
) -> list[ReferenceCandidateRecord]:
    """Deterministically extract all reference items from a bibliography passage."""
    lines = passage_text.splitlines()
    candidates: list[ReferenceCandidateRecord] = []

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
                candidates.append(
                    parse_single_reference(full_text, source_id, passage_id, current_idx)
                )
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
        candidates.append(
            parse_single_reference(full_text, source_id, passage_id, current_idx)
        )

    return candidates
