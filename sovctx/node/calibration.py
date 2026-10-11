from __future__ import annotations

import re
from typing import Tuple


# ---------------------------------------------------------------------------
# Equation Witness Calibration
# ---------------------------------------------------------------------------

# Patterns indicating HTML markup or URL parameters that must NEVER be
# captured as mathematical equations.
HTML_OR_URL_PATTERN = re.compile(
    r"""
    <\s*/?[a-zA-Z][a-zA-Z0-9]*\b[^>]*>        # HTML tags: <div ...>, </span>, etc.
    |\b(?:href|class|id|style|rel|src|type|name|action|method|xmlns|width|height|valign|align|color)=['"][^'"]*['"]
    |\b(?:href|class|id|style|rel|src|type|name|action|method|xmlns|width|height|valign|align|color)=[^\s>]+
    |\b(?:paperid|jrnid|option_lang|wshow)=[0-9a-zA-Z_%-]+
    |https?://\S+
    |www\.\S+
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Common HTML entity or tag residues
HTML_TAG_RESIDUE = re.compile(r"<\s*[^>]+>|&[a-zA-Z]+;|&#[0-9]+;")

# Indicators of genuine mathematical context
MATH_SYNTAX_INDICATORS = re.compile(
    r"""
    \\(?:int|sum|partial|frac|sqrt|alpha|beta|gamma|delta|epsilon|lambda|sigma|omega|infty|le|ge|approx|equiv|to|nabla|times|pm|cdot)\b
    |\b[a-zA-Z\u0400-\u04FF]\s*\(   # Function application: f(x), u(t), \phi(s)
    |[0-9a-zA-Z\u0400-\u04FF]+_[0-9a-zA-Z\u0400-\u04FF]+ # Subscripts: x_1, u_t
    |[0-9a-zA-Z\u0400-\u04FF]+\^[0-9a-zA-Z\u0400-\u04FF]+ # Superscripts: x^2
    |[\u0370-\u03FF]                # Greek characters
    |[\u2200-\u22FF]                # Mathematical operators Unicode block
    |[\u2190-\u21FF]                # Arrows Unicode block
    |\b[a-zA-Z]\b\s*[=+\-*/]\s*\b[a-zA-Z0-9]\b  # Simple variable equation: a = b, x + 1
    """,
    re.VERBOSE,
)


def is_valid_equation_line(line: str) -> bool:
    """Strictly filter out HTML attributes, URL parameters, and non-math lines containing '='."""
    clean = line.strip()
    if not clean:
        return False

    # 1. Reject if line contains HTML markup or URL parameters
    if HTML_OR_URL_PATTERN.search(clean):
        return False
    if HTML_TAG_RESIDUE.search(clean):
        return False

    # 2. Reject if line starts with typical web / code attributes
    if re.match(r"^[a-zA-Z_-]+=(?:'[^']*'|\"[^\"]*\"|\S+)$", clean):
        return False

    # 3. If line contains '=', ensure it's not surrounded by quotation marks or HTML-like tokens
    if "=" in clean:
        # Check if '=' is only inside quotes
        stripped_quotes = re.sub(r"'[^']*'|\"[^\"]*\"", "", clean)
        if "=" not in stripped_quotes:
            return False

        # Check for equation-like math tokens
        has_math_tokens = (
            MATH_SYNTAX_INDICATORS.search(clean) is not None
            or re.search(r"\b[a-zA-Z\u0400-\u04FF0-9_]\s*=\s*[a-zA-Z\u0400-\u04FF0-9_\\(\[]", clean) is not None
        )
        if not has_math_tokens:
            return False

    return True


# ---------------------------------------------------------------------------
# Calibrated Russian Scientific Definition Triggers
# ---------------------------------------------------------------------------

CALIBRATED_DEFINITION_TRIGGERS: list[tuple[re.Pattern[str], str, float]] = [
    # Explicit definition phrasing
    (re.compile(r"\bпод\s+(.+?)\s+понимается\b", re.IGNORECASE), "под ... понимается", 0.94),
    (re.compile(r"\bпод\s+(.+?)\s+будем\s+понимать\b", re.IGNORECASE), "под ... будем понимать", 0.93),
    (re.compile(r"\bпод\s+(.+?)\s+мы\s+понимаем\b", re.IGNORECASE), "под ... мы понимаем", 0.92),
    (re.compile(r"\bопределяется\s+как\b", re.IGNORECASE), "определяется как", 0.92),
    (re.compile(r"\bбудем\s+определять\s+как\b", re.IGNORECASE), "будем определять как", 0.90),
    (re.compile(r"\bносит\s+название\b", re.IGNORECASE), "носит название", 0.92),
    (re.compile(r"\bполучил(?:о|а)?\s+название\b", re.IGNORECASE), "получило название", 0.90),
    (re.compile(r"\bназывается\b", re.IGNORECASE), "называется", 0.90),
    (re.compile(r"\bбудем\s+называть\b", re.IGNORECASE), "будем называть", 0.92),
    (re.compile(r"\bназовем\b", re.IGNORECASE), "назовем", 0.88),
    (re.compile(r"\bназовём\b", re.IGNORECASE), "назовём", 0.88),
    (re.compile(r"\bвведем\s+понятие\b", re.IGNORECASE), "введем понятие", 0.92),
    (re.compile(r"\bвведём\s+понятие\b", re.IGNORECASE), "введём понятие", 0.92),
    (re.compile(r"\bвводится\s+понятие\b", re.IGNORECASE), "вводится понятие", 0.90),
    (re.compile(r"\bобозначим\b", re.IGNORECASE), "обозначим", 0.85),
    (re.compile(r"\bбудем\s+обозначать\b", re.IGNORECASE), "будем обозначать", 0.87),
    (re.compile(r"\bпредставляет\s+собой\b", re.IGNORECASE), "представляет собой", 0.82),
    (re.compile(r"[—–-]\s*это\b", re.IGNORECASE), "— это", 0.88),
]


# ---------------------------------------------------------------------------
# Negative Control Non-Technical Collocations
# ---------------------------------------------------------------------------

NON_TECHNICAL_COLLOCATIONS: frozenset[str] = frozenset({
    "разного типа",
    "различного типа",
    "разных типов",
    "в данном случае",
    "в этом случае",
    "в таких случаях",
    "таким образом",
    "тем самым",
    "в связи с этим",
    "в связи с чем",
    "с другой стороны",
    "с одной стороны",
    "в частности",
    "в настоящее время",
    "в общем виде",
    "в общем случае",
    "в то же время",
    "как правило",
    "прежде всего",
    "по крайней мере",
    "в соответствии с",
    "на самом деле",
    "до сих пор",
    "кроме того",
    "тем не менее",
    "вместе с тем",
    "с этой целью",
    "на основе",
    "в результате",
    "в силу этого",
    "по отношению к",
    "в той или иной",
    "в первую очередь",
})


def is_negative_control_phrase(phrase: str) -> bool:
    """Return True if the phrase is a generic non-technical discourse collocation."""
    norm = phrase.strip().lower()
    if norm in NON_TECHNICAL_COLLOCATIONS:
        return True
    # Substring check for known filler collocations
    for filler in NON_TECHNICAL_COLLOCATIONS:
        if filler == norm:
            return True
    return False
