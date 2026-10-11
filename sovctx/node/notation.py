from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Optional


def make_symbol_occurrence_id(
    source_id: str,
    passage_id: str,
    symbol: str,
    char_start: int,
) -> str:
    preimage = f"{source_id}\0{passage_id}\0{symbol}\0{char_start}"
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:20]
    return f"SOVSYM:{digest}"


@dataclass
class SymbolOccurrence:
    id: str
    symbol: str
    source_id: str
    passage_id: str
    equation_witness_id: Optional[str]
    surface_context: str
    char_start: int
    char_end: int
    meaning_candidate: Optional[str] = None  # Invariant: NEVER assume global meaning!

    def to_dict(self) -> dict[str, str | None | int]:
        return asdict(self)


# Mathematical symbols regex
# 1. Function calls like V(x), f(t), K(x,y), F(s,y)
MATH_FUNCTION_REGEX = re.compile(
    r"\b([A-Za-zА-Яа-я\u0391-\u03C9\u0424])\s*\(([A-Za-z0-9,\s\+\-\*\/\^\._]+)\)"
)

# 2. Subscripted / derivative variables like u_tt, u_xx, c^2, x_i, K_0
MATH_SUBSCRIPT_REGEX = re.compile(
    r"\b([A-Za-z\u0391-\u03C9\u0424])(?:_[a-zA-Z0-9]+|\^[a-zA-Z0-9]+)+"
)

# 3. Isolated mathematical variable tokens (Latin or Greek letters surrounded by operators or standalone in formula clauses)
MATH_STANDALONE_SYMBOL_REGEX = re.compile(
    r"(?:(?<=[=\+\-\*\/\(\)\[\],><\s])|^)([A-Za-z\u0391-\u03C9\u0424])(?=(?:[=\+\-\*\/\(\)\[\],><\s]|$))"
)


def extract_symbol_occurrences(
    text: str,
    source_id: str,
    passage_id: str,
    equation_witness_id: Optional[str] = None,
) -> list[SymbolOccurrence]:
    """Extract mathematical symbol occurrences from text with exact context binding.

    Invariant: meaning_candidate is ALWAYS None at extraction time.
    """
    symbols: list[SymbolOccurrence] = []
    seen_spans: set[tuple[int, int]] = set()

    def add_symbol(sym: str, start: int, end: int) -> None:
        if (start, end) in seen_spans:
            return
        seen_spans.add((start, end))

        ctx_start = max(0, start - 30)
        ctx_end = min(len(text), end + 30)
        context = text[ctx_start:ctx_end].replace("\n", " ").strip()

        occ_id = make_symbol_occurrence_id(source_id, passage_id, sym, start)
        symbols.append(
            SymbolOccurrence(
                id=occ_id,
                symbol=sym,
                source_id=source_id,
                passage_id=passage_id,
                equation_witness_id=equation_witness_id,
                surface_context=context,
                char_start=start,
                char_end=end,
                meaning_candidate=None,  # Invariant: No global semantic assignment!
            )
        )

    # 1. Functions
    for m in MATH_FUNCTION_REGEX.finditer(text):
        add_symbol(m.group(0), m.start(), m.end())

    # 2. Subscripted / superscripted variables
    for m in MATH_SUBSCRIPT_REGEX.finditer(text):
        add_symbol(m.group(0), m.start(), m.end())

    # 3. Standalone symbols
    for m in MATH_STANDALONE_SYMBOL_REGEX.finditer(text):
        # Exclude common 1-letter prepositions in Russian ('в', 'и', 'с', 'к', 'у', 'о', 'а')
        tok = m.group(1)
        if tok.lower() in ("в", "и", "с", "к", "у", "о", "а", "я"):
            continue
        add_symbol(tok, m.start(1), m.end(1))

    return symbols
