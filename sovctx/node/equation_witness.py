from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


def make_equation_witness_id(
    source_sha256: str,
    passage_id: str,
    extracted_surface: str,
) -> str:
    preimage = f"{source_sha256}\0{passage_id}\0{extracted_surface.strip()}"
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:20]
    return f"SOVEQW:{digest}"


@dataclass
class EquationWitnessRecord:
    id: str
    source_id: str
    passage_id: str
    page_physical: int
    surface_representation: str
    locator: Optional[str]
    neighboring_terms: list[str] = field(default_factory=list)
    neighboring_symbols: list[str] = field(default_factory=list)
    extraction_method: str = "pdf_text"
    confidence: float = 0.90

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["neighboring_terms_json"] = json.dumps(self.neighboring_terms, ensure_ascii=False)
        d["neighboring_symbols_json"] = json.dumps(self.neighboring_symbols, ensure_ascii=False)
        return d


EQUATION_LOCATOR_PATTERN = re.compile(
    r"\(([0-9]+(?:\.[0-9]+)*|[a-zA-Z]|\*)\)\s*$"
)

# Mathematical relational operators indicating an equation
EQUATION_OPERATOR_PATTERN = re.compile(
    r"(=|\\le|\\ge|\u2264|\u2265|\\approx|\u2248|\\equiv|\u2261|\\sim|\u223c|\\to|\u2192)"
)


def extract_equation_witnesses_from_passage(
    text: str,
    source_id: str,
    passage_id: str,
    page_physical: int,
    extraction_method: str = "pdf_text",
) -> list[EquationWitnessRecord]:
    """Identify mathematical equations and retain unnormalized historical notation as witnesses."""
    from .notation import extract_symbol_occurrences

    witnesses: list[EquationWitnessRecord] = []
    lines = text.split("\n")

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue

        # Check for equation relational operator or LaTeX commands
        has_eq_op = EQUATION_OPERATOR_PATTERN.search(line_s) is not None
        has_math_cmd = any(cmd in line_s for cmd in (r"\int", r"\sum", r"\partial", r"\frac", "^2", "_t", "_x"))

        if has_eq_op or has_math_cmd:
            # Check for equation locator like (1) or (2.4)
            loc_match = EQUATION_LOCATOR_PATTERN.search(line_s)
            locator = loc_match.group(0) if loc_match else None

            # Extract symbols occurring within this equation
            symbols = extract_symbol_occurrences(
                line_s,
                source_id=source_id,
                passage_id=passage_id,
            )
            symbol_strings = [s.symbol for s in symbols]

            source_sha = source_id.replace("SOVSRC:", "")
            wit_id = make_equation_witness_id(source_sha, passage_id, line_s)

            witnesses.append(
                EquationWitnessRecord(
                    id=wit_id,
                    source_id=source_id,
                    passage_id=passage_id,
                    page_physical=page_physical,
                    surface_representation=line_s,  # Exact unnormalized representation
                    locator=locator,
                    neighboring_terms=[],  # Filled by coordinator
                    neighboring_symbols=symbol_strings,
                    extraction_method=extraction_method,
                    confidence=0.92 if has_eq_op else 0.85,
                )
            )

    return witnesses
