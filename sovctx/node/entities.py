from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Optional


def make_entity_id(
    entity_type: str,
    normalized_name: str,
    passage_id: str,
    char_start: int,
) -> str:
    """Generate deterministic entity mention ID bound to type, normalized name, passage, and offset."""
    preimage = f"{entity_type.upper()}\0{normalized_name.strip().lower()}\0{passage_id}\0{char_start}"
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:20]
    return f"SOVENT:{digest}"


@dataclass
class EntityMentionRecord:
    id: str
    entity_type: str  # PERSON, INSTITUTION, METHOD, INSTRUMENT
    surface_text: str
    normalized_name: str
    source_id: str
    passage_id: str
    char_start: int
    char_end: int
    confidence: float = 0.85
    details_json: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Known Historical Entities Registry
# ---------------------------------------------------------------------------

KNOWN_SOVIET_INSTITUTIONS: dict[str, dict[str, Any]] = {
    "ан ссср": {
        "canonical": "Академия наук СССР",
        "abbrev": "АН СССР",
        "temporal_relations": [{"relation": "RENAMED_TO", "target": "РАН", "year": 1991}],
    },
    "ан усср": {
        "canonical": "Академия наук УССР",
        "abbrev": "АН УССР",
        "temporal_relations": [{"relation": "RENAMED_TO", "target": "НАН Украины", "year": 1991}],
    },
    "мгу": {
        "canonical": "Московский государственный университет им. М. В. Ломоносова",
        "abbrev": "МГУ",
        "temporal_relations": [{"relation": "NAMED_AFTER", "target": "М. В. Ломоносов", "year": 1940}],
    },
    "миан": {
        "canonical": "Математический институт им. В. А. Стеклова АН СССР",
        "abbrev": "МИАН",
        "temporal_relations": [{"relation": "NAMED_AFTER", "target": "В. А. Стеклов", "year": 1926}],
    },
    "ипм": {
        "canonical": "Институт прикладной математики им. М. В. Келдыша АН СССР",
        "abbrev": "ИПМ им. Келдыша",
        "temporal_relations": [
            {"relation": "FOUNDED_AS", "target": "Отделение прикладной математики МИАН", "year": 1953},
            {"relation": "NAMED_AFTER", "target": "М. В. Келдыш", "year": 1978},
        ],
    },
    "ипм им. келдыша": {
        "canonical": "Институт прикладной математики им. М. В. Келдыша АН СССР",
        "abbrev": "ИПМ им. Келдыша",
        "temporal_relations": [
            {"relation": "NAMED_AFTER", "target": "М. В. Келдыш", "year": 1978},
        ],
    },
    "цаги": {
        "canonical": "Центральный аэрогидродинамический институт им. проф. Н. Е. Жуковского",
        "abbrev": "ЦАГИ",
        "temporal_relations": [{"relation": "FOUNDED_IN", "year": 1918}],
    },
    "мфти": {
        "canonical": "Московский физико-технический институт",
        "abbrev": "МФТИ",
        "temporal_relations": [{"relation": "FOUNDED_IN", "year": 1951}],
    },
    "ипу": {
        "canonical": "Институт проблем управления им. В. А. Трапезникова АН СССР",
        "abbrev": "ИПУ",
        "temporal_relations": [{"relation": "RENAMED_FROM", "target": "Институт автоматики и телемеханики", "year": 1969}],
    },
    "лгу": {
        "canonical": "Ленинградский государственный университет",
        "abbrev": "ЛГУ",
        "temporal_relations": [{"relation": "RENAMED_TO", "target": "СПбГУ", "year": 1991}],
    },
    "вц ан ссср": {
        "canonical": "Вычислительный центр им. А. А. Дородницына АН СССР",
        "abbrev": "ВЦ АН СССР",
        "temporal_relations": [{"relation": "FOUNDED_IN", "year": 1955}],
    },
    "ломи": {
        "canonical": "Ленинградское отделение Математического института им. В. А. Стеклова АН СССР",
        "abbrev": "ЛОМИ",
        "temporal_relations": [{"relation": "AFFILIATED_WITH", "target": "МИАН", "year": 1940}],
    },
    "гифти": {
        "canonical": "Горьковский исследовательский физико-технический институт",
        "abbrev": "ГИФТИ",
        "temporal_relations": [{"relation": "FOUNDED_IN", "year": 1932}],
    },
    "хмо": {
        "canonical": "Харьковское математическое общество",
        "abbrev": "ХМО",
        "temporal_relations": [{"relation": "FOUNDED_IN", "year": 1879}],
    },
}

KNOWN_SOVIET_PERSONS: dict[str, str] = {
    "тихонов": "Тихонов А. Н.",
    "а. н. тихонов": "Тихонов А. Н.",
    "понтрягин": "Понтрягин Л. С.",
    "л. с. понтрягин": "Понтрягин Л. С.",
    "ляпунов": "Ляпунов А. М.",
    "а. м. ляпунов": "Ляпунов А. М.",
    "гельфанд": "Гельфанд И. М.",
    "и. м. гельфанд": "Гельфанд И. М.",
    "левитан": "Левитан Б. М.",
    "б. м. левитан": "Левитан Б. М.",
    "самарский": "Самарский А. А.",
    "а. а. самарский": "Самарский А. А.",
    "боголюбов": "Боголюбов Н. Н.",
    "н. н. боголюбов": "Боголюбов Н. Н.",
    "марков": "Марков А. А.",
    "а. а. марков": "Марков А. А.",
    "чебышев": "Чебышев П. Л.",
    "п. л. чебышев": "Чебышев П. Л.",
    "андронов": "Андронов А. А.",
    "соболев": "Соболев С. Л.",
    "келдыш": "Келдыш М. В.",
    "колмогоров": "Колмогоров А. Н.",
    "арнольд": "Арнольд В. И.",
    "власов": "Власов А. А.",
    "фаддеев": "Фаддеев Л. Д.",
    "болтянский": "Болтянский В. Г.",
    "гамкрелидзе": "Гамкрелидзе Р. В.",
    "мищенко": "Мищенко Е. Ф.",
    "красовский": "Красовский Н. Н.",
    "адамар": "Адамар Ж.",
    "лаврентьев": "Лаврентьев М. А.",
    "шаудер": "Шаудер Ю.",
    "штурм": "Штурм Ш.",
    "марченко": "Марченко В. А.",
    "крейн": "Крейн М. Г.",
    "уатт": "Уатт Д.",
    "понселе": "Понселе Ж.",
    "больцман": "Больцман Л.",
    "гиббс": "Гиббс Д.",
    "крылов": "Крылов Н. М.",
    "кирквуд": "Кирквуд Д.",
    "пуанкаре": "Пуанкаре А.",
    "биркгоф": "Биркгоф Д.",
    "лагранж": "Лагранж Ж.",
    "дирихле": "Дирихле П.",
    "некрасов": "Некрасов П. А.",
    "липпман": "Липпман Б.",
    "швингер": "Швингер Ю.",
    "ватсон": "Ватсон К.",
    "скорняков": "Скорняков Г. В.",
    "тер-мартиросян": "Тер-Мартиросян К. А.",
    "беллман": "Беллман Р.",
    "ландау": "Ландау Л. Д.",
    "джинс": "Джинс Д.",
}

KNOWN_SOVIET_METHODS: dict[str, str] = {
    "метод регуляризации": "Метод регуляризации Тихонова",
    "метод тихонова": "Метод регуляризации Тихонова",
    "принцип максимума": "Принцип максимума Понтрягина",
    "принцип максимума понтрягина": "Принцип максимума Понтрягина",
    "функция ляпунова": "Функция Ляпунова",
    "метод функций ляпунова": "Метод функций Ляпунова",
    "уравнение власова": "Уравнение Власова",
    "оператор штурма-лиувилля": "Оператор Штурма-Лиувилля",
    "обратная задача теории рассеяния": "Обратная задача Гельфанда-Левитана",
    "уравнение гельфанда-левитана": "Уравнение Гельфанда-Левитана",
    "метод моментов": "Метод моментов Чебышева-Маркова",
    "неравенство маркова": "Неравенство Маркова",
    "обратные задачи": "Обратные задачи математической физики",
    "обратная задача": "Обратные задачи математической физики",
    "обратных задач": "Обратные задачи математической физики",
    "самосогласованное поле": "Метод самосогласованного поля",
    "наилучшее приближение": "Метод наилучшего приближения Чебышева",
    "наилучшего приближения": "Метод наилучшего приближения Чебышева",
    "цепочка уравнений": "Цепочка уравнений ББГКИ",
    "цепочка ббгки": "Цепочка уравнений ББГКИ",
    "структурная устойчивость": "Теория структурной устойчивости",
    "структурной устойчивости": "Теория структурной устойчивости",
    "цепи маркова": "Цепи Маркова",
    "уравнения фаддеева": "Уравнения Фаддеева",
}

KNOWN_SOVIET_INSTRUMENTS: dict[str, str] = {
    "бэсм": "ЭВМ БЭСМ",
    "бэсм-6": "ЭВМ БЭСМ-6",
    "мэсм": "ЭВМ МЭСМ",
    "стрела": "ЭВМ Стрела",
    "сетунь": "Троичная ЭВМ Сетунь",
    "м-20": "ЭВМ М-20",
    "урал-1": "ЭВМ Урал-1",
    "сейсмограф": "Сейсмограф Галицына",
    "сейсмографов": "Сейсмограф Галицына",
    "интерферометр": "Интерферометр Фабри-Перо",
    "интерферометра": "Интерферометр Фабри-Перо",
    "катетометр": "Катетометр",
    "делительная машина": "Делительная машина",
}


def is_institution_entity(text: str) -> bool:
    """Return True if text or token refers to a known Soviet research/academic institution."""
    norm = text.strip().lower()
    return norm in KNOWN_SOVIET_INSTITUTIONS


def extract_entity_mentions(
    passage_text: str,
    source_id: str,
    passage_id: str,
) -> list[EntityMentionRecord]:
    """Extract deterministic historical entity mentions (Person, Institution, Method, Instrument)."""
    mentions: list[EntityMentionRecord] = []
    text_lower = passage_text.lower()

    # 1. Institutions
    for key, info in KNOWN_SOVIET_INSTITUTIONS.items():
        pattern = r"\b" + re.escape(key) + r"\b"
        for m in re.finditer(pattern, text_lower):
            start, end = m.span()
            surface = passage_text[start:end]
            eid = make_entity_id("INSTITUTION", info["abbrev"], passage_id, start)
            mentions.append(
                EntityMentionRecord(
                    id=eid,
                    entity_type="INSTITUTION",
                    surface_text=surface,
                    normalized_name=info["canonical"],
                    source_id=source_id,
                    passage_id=passage_id,
                    char_start=start,
                    char_end=end,
                    confidence=0.95,
                    details_json=json.dumps(info, ensure_ascii=False),
                )
            )

    # 2. Methods / Principles
    for key, canonical in KNOWN_SOVIET_METHODS.items():
        pattern = r"\b" + re.escape(key) + r"\b"
        for m in re.finditer(pattern, text_lower):
            start, end = m.span()
            surface = passage_text[start:end]
            eid = make_entity_id("METHOD", canonical, passage_id, start)
            mentions.append(
                EntityMentionRecord(
                    id=eid,
                    entity_type="METHOD",
                    surface_text=surface,
                    normalized_name=canonical,
                    source_id=source_id,
                    passage_id=passage_id,
                    char_start=start,
                    char_end=end,
                    confidence=0.90,
                    details_json=json.dumps({"method_type": "theoretical_or_computational"}),
                )
            )

    # 3. Persons
    # Match full surname + initials pattern or known surnames with grammatical case inflections
    for key, canonical in KNOWN_SOVIET_PERSONS.items():
        if key.endswith("ский"):
            stem = key[:-4]
            pattern = r"\b" + re.escape(stem) + r"ск(?:ий|ого|ому|им|ом)\b"
        else:
            pattern = r"\b" + re.escape(key) + r"(?:а|у|ом|ем|ым|е)?\b"
        for m in re.finditer(pattern, text_lower):
            start, end = m.span()
            surface = passage_text[start:end]
            eid = make_entity_id("PERSON", canonical, passage_id, start)
            mentions.append(
                EntityMentionRecord(
                    id=eid,
                    entity_type="PERSON",
                    surface_text=surface,
                    normalized_name=canonical,
                    source_id=source_id,
                    passage_id=passage_id,
                    char_start=start,
                    char_end=end,
                    confidence=0.88,
                    details_json=json.dumps({"canonical_author": canonical}, ensure_ascii=False),
                )
            )

    # 4. Instruments
    for key, canonical in KNOWN_SOVIET_INSTRUMENTS.items():
        pattern = r"\b" + re.escape(key) + r"\b"
        for m in re.finditer(pattern, text_lower):
            start, end = m.span()
            surface = passage_text[start:end]
            eid = make_entity_id("INSTRUMENT", canonical, passage_id, start)
            mentions.append(
                EntityMentionRecord(
                    id=eid,
                    entity_type="INSTRUMENT",
                    surface_text=surface,
                    normalized_name=canonical,
                    source_id=source_id,
                    passage_id=passage_id,
                    char_start=start,
                    char_end=end,
                    confidence=0.92,
                    details_json=json.dumps({"hardware_type": "computing_system"}, ensure_ascii=False),
                )
            )

    return mentions
