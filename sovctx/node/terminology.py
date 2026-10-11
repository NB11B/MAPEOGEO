from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


def make_term_id(normalized_unicode: str, language: str = "ru") -> str:
    """Deterministic term identity based strictly on normalized unicode and language."""
    preimage = f"{normalized_unicode.strip().lower()}\0{language.strip().lower()}"
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:20]
    return f"SOVTERM:{digest}"


def make_occurrence_id(
    term_id: str,
    passage_id: str,
    char_start: int,
    char_end: int,
) -> str:
    """Deterministic term occurrence identity bound to passage and character span."""
    preimage = f"{term_id}\0{passage_id}\0{char_start}\0{char_end}"
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:24]
    return f"SOVTOCC:{digest}"


def make_definition_id(
    passage_id: str,
    char_start: int,
    char_end: int,
    trigger: str,
) -> str:
    """Deterministic definition candidate identity."""
    preimage = f"{passage_id}\0{char_start}\0{char_end}\0{trigger}"
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:20]
    return f"SOVDEF:{digest}"


@dataclass
class TechnicalityScore:
    score: float
    signals: list[str]


@dataclass
class NativeTerm:
    id: str
    surface_form: str
    normalized_unicode: str
    language: str = "ru"
    script: str = "Cyrillic"
    term_type: str = "single_token"  # single_token, compound_phrase, abbreviation, hyphenated
    technicality_score: float = 0.5
    signals: list[str] = field(default_factory=list)
    status: str = "CANDIDATE"
    rejection_reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["signals_json"] = json.dumps(self.signals, ensure_ascii=False)
        return d


@dataclass
class TermOccurrence:
    id: str
    term_id: str
    passage_id: str
    source_id: str
    surface_form: str
    char_start: int
    char_end: int
    sentence_index: int
    context_snippet: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TermRelation:
    id: str
    from_term_id: str
    to_term_id: str
    relation_type: str  # LEMMATIZED_AS, HISTORICAL_SPELLING_OF, VARIANT_SPELLING_OF, ABBREVIATION_OF, CONTAINS_TERM, TECHNICAL_TRANSLATION
    method: str
    confidence: float
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["details_json"] = json.dumps(self.details, ensure_ascii=False)
        return d


@dataclass
class DefinitionCandidate:
    id: str
    passage_id: str
    source_id: str
    subject_term_id: Optional[str]
    trigger: str
    defining_span: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Bounded definition trigger regex patterns
DEFINITION_TRIGGERS: list[tuple[re.Pattern[str], str, float]] = [
    (re.compile(r"\bназывается\b", re.IGNORECASE), "называется", 0.90),
    (re.compile(r"\bбудем\s+называть\b", re.IGNORECASE), "будем называть", 0.92),
    (re.compile(r"\bназовем\b", re.IGNORECASE), "назовем", 0.88),
    (re.compile(r"\bназовём\b", re.IGNORECASE), "назовём", 0.88),
    (re.compile(r"\bобозначим\b", re.IGNORECASE), "обозначим", 0.85),
    (re.compile(r"\bпод\s+(.+?)\s+понимается\b", re.IGNORECASE), "под ... понимается", 0.90),
    (re.compile(r"\bпод\s+(.+?)\s+будем\s+понимать\b", re.IGNORECASE), "под ... будем понимать", 0.90),
    (re.compile(r"\bопределяется\s+как\b", re.IGNORECASE), "определяется как", 0.92),
    (re.compile(r"\bпредставляет\s+собой\b", re.IGNORECASE), "представляет собой", 0.80),
]

# Morphological / scientific root patterns in Russian
SCIENTIFIC_STEM_PATTERNS = re.compile(
    r".*(ость|ение|ание|изм|ика|тор|ция|метр|скоп|граф|вектор|матриц|уравн|функц|интегр|дифф|устойч|спектр|пространств|теорем|лемм|поле|оператор|решени|задач).*",
    re.IGNORECASE,
)

# Common Russian scientific multiword patterns (Adjective + Noun, Noun + Genitive Noun)
COMMON_SCIENTIFIC_COLLOCATIONS = {
    ("электромагнитное", "поле"),
    ("электромагнитного", "поля"),
    ("электромагнитному", "полю"),
    ("электромагнитным", "полем"),
    ("функция", "ляпунова"),
    ("функции", "ляпунова"),
    ("функцию", "ляпунова"),
    ("дифференциальное", "уравнение"),
    ("дифференциального", "уравнения"),
    ("дифференциальных", "уравнений"),
    ("дифференциальным", "уравнениям"),
    ("интегральное", "уравнение"),
    ("интегрального", "уравнения"),
    ("интегральных", "уравнений"),
    ("спектральная", "функция"),
    ("спектральной", "функции"),
    ("спектральную", "функцию"),
    ("обратная", "задача"),
    ("обратной", "задачи"),
    ("обратную", "задачу"),
    ("устойчивость", "движения"),
    ("устойчивости", "движения"),
    ("устойчивостью", "движения"),
    ("твердое", "тело"),
    ("твердого", "тела"),
    ("твердаго", "тѣла"),
    ("неподвижная", "точка"),
    ("неподвижной", "точки"),
    ("волновое", "уравнение"),
    ("волнового", "уравнения"),
    ("собственное", "значение"),
    ("собственного", "значения"),
    ("собственные", "значения"),
    ("краевая", "задача"),
    ("краевой", "задачи"),
    ("краевую", "задачу"),
    ("метод", "тихонова"),
    ("метода", "тихонова"),
    ("принцип", "максимума"),
    ("принципа", "максимума"),
    ("оператор", "штурма-лиувилля"),
    ("оператора", "штурма-лиувилля"),
    ("квазиустойчивое", "состояние"),
    ("квазиустойчивого", "состояния"),
}

# Stopwords that should not be extracted as standalone single-token terms
RUSSIAN_STOPWORDS = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все", "она",
    "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за", "бы", "по", "только", "ее",
    "мне", "было", "вот", "от", "меня", "еще", "нет", "о", "об", "из", "ему", "теперь",
    "когда", "даже", "ну", "вдруг", "ли", "если", "уже", "или", "ни", "быть", "был",
    "него", "до", "вас", "нибудь", "опять", "уж", "вам", "ведь", "там", "потом", "себя",
    "ничего", "ей", "может", "они", "тут", "где", "есть", "надо", "ней", "для", "мы",
    "тебя", "их", "чем", "была", "сам", "чтоб", "без", "будто", "чего", "раз", "тоже",
    "себе", "под", "будет", "ж", "тогда", "кто", "этот", "того", "потому", "этого",
    "какой", "совсем", "ним", "здесь", "этом", "один", "почти", "мой", "тем", "чтобы",
    "нее", "сейчас", "были", "куда", "зачем", "всех", "никогда", "можно", "при", "наконец",
    "два", "об", "другой", "хоть", "после", "над", "больше", "тот", "через", "эти", "нас",
    "про", "всего", "них", "какая", "много", "разве", "три", "эту", "моя", "впрочем",
    "хорошо", "свою", "этой", "перед", "иногда", "лучше", "чуть", "том", "нельзя",
}


def compute_technicality(
    term: str,
    term_type: str,
    occurs_in_definition: bool = False,
    near_equation: bool = False,
    source_frequency: int = 1,
    is_hyphenated: bool = False,
    is_abbreviation: bool = False,
    is_eponym: bool = False,
) -> TechnicalityScore:
    """Compute continuous technicality score in [0.0, 1.0] with explainable evidence signals."""
    signals: list[str] = []
    score = 0.35  # Baseline

    if term_type == "compound_phrase":
        score += 0.25
        signals.append("multiword_noun_phrase")

    if SCIENTIFIC_STEM_PATTERNS.match(term):
        score += 0.20
        signals.append("scientific_suffix_or_structure")

    if occurs_in_definition:
        score += 0.25
        signals.append("occurs_in_definition_pattern")

    if near_equation:
        score += 0.15
        signals.append("occurs_near_equation")

    if source_frequency >= 2:
        score += 0.15
        signals.append("repeated_within_source")

    if is_hyphenated:
        score += 0.10
        signals.append("hyphenated_technical_term")

    if is_abbreviation:
        score += 0.20
        signals.append("scientific_abbreviation")

    if is_eponym:
        score += 0.20
        signals.append("capitalization_or_symbol_context")

    clamped_score = max(0.0, min(1.0, round(score, 2)))
    return TechnicalityScore(score=clamped_score, signals=signals)
