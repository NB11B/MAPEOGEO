from __future__ import annotations

import re
import unicodedata
from typing import NamedTuple


class LanguageAnalysis(NamedTuple):
    script: str  # "Cyrillic", "Latin", "Mixed", "Mathematical"
    language: str  # "ru", "en", "de", "fr", "und"
    confidence: float
    cyrillic_ratio: float
    latin_ratio: float


RUSSIAN_MARKERS = {
    "и", "в", "не", "на", "с", "что", "как", "по", "для", "это",
    "при", "из", "от", "к", "до", "или", "если", "так", "мы",
    "уравнение", "теорема", "функция", "системы", "метод", "решение",
    "где", "пусть", "доказательство", "оператор", "пространство",
}

ENGLISH_MARKERS = {
    "the", "and", "of", "to", "in", "is", "that", "for", "with",
    "as", "on", "are", "by", "this", "from", "at", "be", "an",
    "equation", "theorem", "function", "system", "method", "proof",
    "operator", "space", "we", "have", "then", "let",
}


def classify_text(text: str) -> LanguageAnalysis:
    """Classify the primary script and language of an extracted passage deterministically."""
    if not text or not text.strip():
        return LanguageAnalysis(
            script="Unknown",
            language="und",
            confidence=0.0,
            cyrillic_ratio=0.0,
            latin_ratio=0.0,
        )

    # Count character types
    cyrillic_count = 0
    latin_count = 0
    math_count = 0
    total_alpha = 0

    for ch in text:
        code = ord(ch)
        # Cyrillic
        if (0x0400 <= code <= 0x04FF) or (0x0500 <= code <= 0x052F) or (0x2DE0 <= code <= 0x2DFF):
            cyrillic_count += 1
            total_alpha += 1
        # Latin
        elif (0x0041 <= code <= 0x005A) or (0x0061 <= code <= 0x007A) or (0x00C0 <= code <= 0x024F):
            latin_count += 1
            total_alpha += 1
        # Greek or Math Symbols
        elif (0x0370 <= code <= 0x03FF) or (0x2200 <= code <= 0x22FF) or (0x2190 <= code <= 0x21FF):
            math_count += 1

    if total_alpha == 0:
        if math_count > 0:
            return LanguageAnalysis(
                script="Mathematical",
                language="und",
                confidence=0.9,
                cyrillic_ratio=0.0,
                latin_ratio=0.0,
            )
        return LanguageAnalysis(
            script="Symbolic",
            language="und",
            confidence=0.5,
            cyrillic_ratio=0.0,
            latin_ratio=0.0,
        )

    cyrillic_ratio = cyrillic_count / total_alpha
    latin_ratio = latin_count / total_alpha

    # Script determination
    if cyrillic_ratio >= 0.75:
        script = "Cyrillic"
    elif latin_ratio >= 0.75:
        script = "Latin"
    else:
        script = "Mixed"

    # Token-level lexical checks
    tokens = [t.lower() for t in re.findall(r"\b\w+\b", text)]
    ru_hits = sum(1 for t in tokens if t in RUSSIAN_MARKERS)
    en_hits = sum(1 for t in tokens if t in ENGLISH_MARKERS)

    if script == "Cyrillic" or cyrillic_ratio > 0.5:
        language = "ru"
        confidence = min(1.0, 0.6 + 0.4 * cyrillic_ratio + 0.1 * min(ru_hits, 4))
    elif script == "Latin":
        if en_hits >= 1 or latin_ratio > 0.8:
            language = "en"
            confidence = min(1.0, 0.6 + 0.3 * latin_ratio + 0.1 * min(en_hits, 4))
        else:
            language = "en"
            confidence = 0.7
    else:
        # Mixed: determine by word hits or dominant alphabet
        if cyrillic_count >= latin_count:
            language = "ru"
            confidence = round(cyrillic_ratio, 2)
        else:
            language = "en"
            confidence = round(latin_ratio, 2)

    return LanguageAnalysis(
        script=script,
        language=language,
        confidence=round(confidence, 2),
        cyrillic_ratio=round(cyrillic_ratio, 3),
        latin_ratio=round(latin_ratio, 3),
    )
