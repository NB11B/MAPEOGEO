from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


VALID_GENEALOGICAL_RELATIONS: frozenset[str] = frozenset({
    "RENAMED_TO",
    "RENAMED_FROM",
    "SUCCESSOR_OF",
    "MERGED_INTO",
    "TRANSFERRED_TO",
    "FOUNDED_AS",
    "NAMED_AFTER",
    "SPLIT_INTO",
    "AFFILIATED_WITH",
})

FORBIDDEN_COLLAPSE_RELATIONS: frozenset[str] = frozenset({
    "SAME_AS",
    "IDENTICAL_TO",
    "EQUIVALENT_TO",
    "SAME_CONCEPT",
})


@dataclass
class TemporalInterval:
    valid_from: Optional[int] = None
    valid_to: Optional[int] = None

    def contains_year(self, year: int) -> bool:
        if self.valid_from is not None and year < self.valid_from:
            return False
        if self.valid_to is not None and year > self.valid_to:
            return False
        return True


@dataclass
class InstitutionalGenealogyEvent:
    source_entity: str
    target_entity: str
    relation_type: str
    event_year: Optional[int]
    valid_from: Optional[int] = None
    valid_to: Optional[int] = None
    observed_at: str = field(default_factory=utc_now_iso)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Verified Historical Institutional Genealogy Registry
# ---------------------------------------------------------------------------

INSTITUTIONAL_GENEALOGY: dict[str, list[InstitutionalGenealogyEvent]] = {
    "ан ссср": [
        InstitutionalGenealogyEvent(
            source_entity="АН СССР",
            target_entity="РАН",
            relation_type="RENAMED_TO",
            event_year=1991,
            valid_from=1925,
            valid_to=1991,
            details={"decree": "Указ Президента РСФСР от 21.11.1991 № 228"},
        ),
    ],
    "ан усср": [
        InstitutionalGenealogyEvent(
            source_entity="АН УССР",
            target_entity="НАН Украины",
            relation_type="RENAMED_TO",
            event_year=1991,
            valid_from=1918,
            valid_to=1991,
            details={"context": "Постановление Президиума АН Украины 1991"},
        ),
    ],
    "ипм": [
        InstitutionalGenealogyEvent(
            source_entity="ИПМ",
            target_entity="Отделение прикладной математики МИАН",
            relation_type="FOUNDED_AS",
            event_year=1953,
            valid_from=1953,
            valid_to=1966,
            details={"original_name": "ОПМ МИАН"},
        ),
        InstitutionalGenealogyEvent(
            source_entity="ИПМ",
            target_entity="Институт прикладной математики АН СССР",
            relation_type="TRANSFERRED_TO",
            event_year=1966,
            valid_from=1966,
            valid_to=None,
            details={"context": "Выделен в самостоятельный институт АН СССР"},
        ),
        InstitutionalGenealogyEvent(
            source_entity="ИПМ",
            target_entity="М. В. Келдыш",
            relation_type="NAMED_AFTER",
            event_year=1978,
            valid_from=1978,
            valid_to=None,
            details={"context": "Присвоено имя академика М. В. Келдыша"},
        ),
    ],
    "ипу": [
        InstitutionalGenealogyEvent(
            source_entity="ИПУ",
            target_entity="Институт автоматики и телемеханики АН СССР",
            relation_type="RENAMED_FROM",
            event_year=1969,
            valid_from=1939,
            valid_to=1969,
            details={"previous_abbrev": "ИАТ"},
        ),
    ],
    "миан": [
        InstitutionalGenealogyEvent(
            source_entity="МИАН",
            target_entity="Физико-математический институт РАН",
            relation_type="FOUNDED_AS",
            event_year=1921,
            valid_from=1921,
            valid_to=1934,
            details={"founder": "В. А. Стеклов"},
        ),
        InstitutionalGenealogyEvent(
            source_entity="МИАН",
            target_entity="ФИАН",
            relation_type="SPLIT_INTO",
            event_year=1934,
            valid_from=1934,
            valid_to=None,
            details={"context": "Разделение ФМИ на МИАН и ФИАН"},
        ),
    ],
    "лгу": [
        InstitutionalGenealogyEvent(
            source_entity="ЛГУ",
            target_entity="СПбГУ",
            relation_type="RENAMED_TO",
            event_year=1991,
            valid_from=1919,
            valid_to=1991,
            details={"context": "Возвращение исторического наименования"},
        ),
    ],
}


def validate_genealogical_edge(relation_type: str) -> tuple[bool, Optional[str]]:
    """Strictly forbid flat identity collapse (SAME_AS, IDENTICAL_TO) across historical periods."""
    norm = relation_type.strip().upper()
    if norm in FORBIDDEN_COLLAPSE_RELATIONS:
        return False, f"Forbidden collapse relation '{relation_type}' across historical institution boundaries"
    if norm in VALID_GENEALOGICAL_RELATIONS:
        return True, None
    return False, f"Unrecognized genealogical relation '{relation_type}'"


def resolve_institutional_state(
    entity_name: str,
    source_year: Optional[int],
) -> dict[str, Any]:
    """Resolve temporal validity of an institution mention in the context of the source year."""
    norm = entity_name.strip().lower()
    events = INSTITUTIONAL_GENEALOGY.get(norm, [])

    if not events:
        return {
            "entity": entity_name,
            "source_year": source_year,
            "status": "UNKNOWN_GENEALOGY",
            "historical_active": True,
            "applicable_events": [],
        }

    applicable: list[dict[str, Any]] = []
    historical_active = True

    for ev in events:
        if source_year is not None:
            # Check if event was already in effect at source_year
            if ev.event_year is not None and source_year < ev.event_year:
                # Pre-event state
                applicable.append({
                    "event": ev.to_dict(),
                    "temporal_status": "FUTURE_EVENT",
                    "applies_at_source_year": False,
                })
            else:
                applicable.append({
                    "event": ev.to_dict(),
                    "temporal_status": "CONTEMPORARY_OR_PAST",
                    "applies_at_source_year": True,
                })
                if ev.relation_type == "RENAMED_TO" and source_year >= ev.event_year:
                    historical_active = False
        else:
            applicable.append({
                "event": ev.to_dict(),
                "temporal_status": "YEAR_UNSPECIFIED",
                "applies_at_source_year": True,
            })

    return {
        "entity": entity_name,
        "source_year": source_year,
        "status": "GENEALOGY_RESOLVED",
        "historical_active": historical_active,
        "applicable_events": applicable,
    }
