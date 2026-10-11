from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from .terminology import NativeTerm, TermRelation, make_term_id

# Archaic pre-1918 Cyrillic glyphs
HISTORICAL_GLYPHS = {"ѣ", "ѣ", "і", "і", "ѳ", "ѳ", "ѵ", "ѵ", "ъ"}
HISTORICAL_CHAR_REGEX = re.compile(r"[ѣіѳѵ]", re.IGNORECASE)


def make_lemma_id(lemma: str, language: str = "ru") -> str:
    digest = hashlib.sha256(f"{lemma.strip().lower()}\0{language.strip().lower()}".encode("utf-8")).hexdigest()[:20]
    return f"SOVLEMMA:{digest}"


@dataclass
class MorphologyAnalysis:
    is_historical: bool
    historical_spelling_candidate: Optional[str]
    lemma_candidate: str
    lemma_confidence: float
    grammatical_features: list[str]


def detect_historical_orthography(text: str) -> bool:
    """Check if word or text contains pre-1918 Russian orthography."""
    # Check for historical letters
    if HISTORICAL_CHAR_REGEX.search(text):
        return True
    # Check for terminal hard sign after consonant at word boundary
    if re.search(r"[бвгджзклмнпрстфхцчшщ]ъ\b", text, re.IGNORECASE):
        return True
    # Check for archaic genitive adjective ending -аго / -яго
    if re.search(r"(аго|яго)\b", text, re.IGNORECASE):
        return True
    return False


def modern_spelling_from_historical(text: str) -> str:
    """Generate modern Russian spelling candidate without modifying original witness."""
    res = text
    # Yat -> e
    res = re.sub(r"ѣ", "е", res)
    res = re.sub(r"Ѣ", "Е", res)
    # Dotted I -> и
    res = re.sub(r"і", "и", res)
    res = re.sub(r"І", "И", res)
    # Fita -> ф
    res = re.sub(r"ѳ", "ф", res)
    res = re.sub(r"Ѳ", "Ф", res)
    # Izhitsa -> и
    res = re.sub(r"ѵ", "и", res)
    res = re.sub(r"Ѵ", "И", res)
    # Remove terminal hard sign
    res = re.sub(r"([бвгджзклмнпрстфхцчшщ])ъ\b", r"\1", res, flags=re.IGNORECASE)
    res = re.sub(r"([бвгджзклмнпрстфхцчшщ])Ъ\b", r"\1", res)
    # Archaic adjective endings: -аго -> -ого, -яго -> -его
    res = re.sub(r"([тквсрпдлнм])аго\b", r"\1ого", res, flags=re.IGNORECASE)
    res = re.sub(r"([тквсрпдлнм])яго\b", r"\1его", res, flags=re.IGNORECASE)
    # Archaic feminine plural: -ыя -> -ые, -iя -> -ие
    res = re.sub(r"ыя\b", "ые", res, flags=re.IGNORECASE)
    res = re.sub(r"ия\b", "ие", res, flags=re.IGNORECASE)
    return res


def analyze_russian_word(word: str) -> MorphologyAnalysis:
    """Deterministic morphological analysis of a Russian surface word."""
    norm = unicodedata.normalize("NFC", word)
    is_hist = detect_historical_orthography(norm)
    modern_form = modern_spelling_from_historical(norm) if is_hist else norm

    features: list[str] = []
    lemma = modern_form.lower()
    confidence = 0.85

    # Retain exact letters (й, ё) - never collapse!
    if "й" in lemma:
        features.append("contains_short_i")
    if "ё" in lemma:
        features.append("contains_yo")

    # Scientific suffix and inflection rules for nominal and adjectival forms
    w = lemma
    if w.endswith("ости") or w.endswith("остью") or w.endswith("остям") or w.endswith("остях"):
        lemma = re.sub(r"(ости|остью|остям|остях)$", "ость", w)
        features.extend(["noun", "fem", "abstract_quality"])
        confidence = 0.95
    elif w.endswith("ения") or w.endswith("ению") or w.endswith("ением") or w.endswith("ении") or w.endswith("ений"):
        lemma = re.sub(r"(ения|ению|ением|ении|ений)$", "ение", w)
        features.extend(["noun", "neut", "verbal_process"])
        confidence = 0.95
    elif w.endswith("ания") or w.endswith("анию") or w.endswith("анием") or w.endswith("ании") or w.endswith("аний"):
        lemma = re.sub(r"(ания|анию|анием|ании|аний)$", "ание", w)
        features.extend(["noun", "neut", "verbal_process"])
        confidence = 0.95
    elif w.endswith("ства") or w.endswith("ству") or w.endswith("ством") or w.endswith("стве") or w.endswith("ств"):
        lemma = re.sub(r"(ства|ству|ством|стве|ств)$", "ство", w)
        features.extend(["noun", "neut"])
        confidence = 0.95
    elif w.endswith("ции") or w.endswith("цию") or w.endswith("цией") or w.endswith("ций") or w.endswith("циях"):
        lemma = re.sub(r"(ции|цию|цией|ций|циях)$", "ция", w)
        features.extend(["noun", "fem"])
        confidence = 0.95
    elif w.endswith("оры") or w.endswith("оров") or w.endswith("ора") or w.endswith("ору") or w.endswith("ором") or w.endswith("оре"):
        lemma = re.sub(r"(оры|оров|ора|ору|ором|оре)$", "ор", w)
        features.extend(["noun", "masc", "agent_or_instrument"])
        confidence = 0.92
    elif w.endswith("емы") or w.endswith("еме") or w.endswith("ему") or w.endswith("емой") or w.endswith("ем"):
        lemma = re.sub(r"(емы|еме|ему|емой|ем)$", "ема", w)
        features.extend(["noun", "fem"])
        confidence = 0.90
    elif w.endswith("ии") or w.endswith("ию") or w.endswith("ией") or w.endswith("ий") or w.endswith("иям"):
        lemma = re.sub(r"(ии|ию|ией|ий|иям)$", "ия", w)
        features.extend(["noun", "fem"])
        confidence = 0.90
    elif w.endswith("ачи") or w.endswith("аче") or w.endswith("ачу") or w.endswith("ачей") or w.endswith("ач"):
        lemma = re.sub(r"(ачи|аче|ачу|ачей|ач)$", "ача", w)
        features.extend(["noun", "fem"])
        confidence = 0.92
    elif w.endswith("тода") or w.endswith("тоду") or w.endswith("тодом") or w.endswith("тоде") or w.endswith("тоды"):
        lemma = re.sub(r"(тода|тоду|тодом|тоде|тоды)$", "тод", w)
        features.extend(["noun", "masc"])
        confidence = 0.95
    elif w.endswith("нципа") or w.endswith("нципу") or w.endswith("нципом") or w.endswith("нципе") or w.endswith("нципы"):
        lemma = re.sub(r"(нципа|нципу|нципом|нципе|нципы)$", "нцип", w)
        features.extend(["noun", "masc"])
        confidence = 0.95
    elif w.endswith("ого") or w.endswith("ому") or w.endswith("ым") or w.endswith("ом") or w.endswith("ая") or w.endswith("ую") or w.endswith("ей") or w.endswith("ые") or w.endswith("ых"):
        # Adjectival forms
        if w.endswith("ого") or w.endswith("ому") or w.endswith("ым") or w.endswith("ом"):
            lemma = re.sub(r"(ого|ому|ым|ом)$", "ый", w)
        elif w.endswith("ая") or w.endswith("ую") or w.endswith("ей"):
            lemma = re.sub(r"(ая|ую|ей)$", "ый", w)
        elif w.endswith("ые") or w.endswith("ых"):
            lemma = re.sub(r"(ые|ых)$", "ый", w)
        features.extend(["adjective"])
        confidence = 0.88

    return MorphologyAnalysis(
        is_historical=is_hist,
        historical_spelling_candidate=modern_form if is_hist else None,
        lemma_candidate=lemma,
        lemma_confidence=confidence,
        grammatical_features=features,
    )
