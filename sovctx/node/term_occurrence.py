from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator

from .terminology import (
    COMMON_SCIENTIFIC_COLLOCATIONS,
    RUSSIAN_STOPWORDS,
    NativeTerm,
    TermOccurrence,
    make_occurrence_id,
    make_term_id,
)

# Abbreviations that must not be split into sentence boundaries
ABBREVIATION_PROTECTION = [
    (re.compile(r"\bт\.\s*е\.", re.IGNORECASE), "т_е_ABBR"),
    (re.compile(r"\bи\s+т\.\s*д\.", re.IGNORECASE), "и_т_д_ABBR"),
    (re.compile(r"\bи\s+т\.\s*п\.", re.IGNORECASE), "и_т_п_ABBR"),
    (re.compile(r"\bрис\.", re.IGNORECASE), "рис_ABBR"),
    (re.compile(r"\bур\.", re.IGNORECASE), "ур_ABBR"),
    (re.compile(r"\bтабл\.", re.IGNORECASE), "табл_ABBR"),
    (re.compile(r"\bстр\.", re.IGNORECASE), "стр_ABBR"),
    (re.compile(r"\bгл\.", re.IGNORECASE), "гл_ABBR"),
    (re.compile(r"\bим\.", re.IGNORECASE), "им_ABBR"),
    (re.compile(r"\bАН\s+СССР\b"), "АН_СССР_ABBR"),
]


def split_sentences(text: str) -> list[tuple[int, int, str]]:
    """Split text into sentences while protecting Russian scientific abbreviations.

    Returns: list of (char_start, char_end, sentence_text)
    """
    if not text.strip():
        return []

    # Protect abbreviations
    masked = text
    for pat, repl in ABBREVIATION_PROTECTION:
        masked = pat.sub(repl, masked)

    # Split by standard sentence boundaries
    sentences: list[tuple[int, int, str]] = []
    # Match sentences
    pattern = re.compile(r"([^\.\?!]+[\.\?!]+(?:['\"]\s*|\s+|$)|[^\.\?!]+$)")
    for match in pattern.finditer(masked):
        start = match.start()
        end = match.end()
        raw_sentence = text[start:end]
        if raw_sentence.strip():
            sentences.append((start, end, raw_sentence))

    if not sentences:
        sentences.append((0, len(text), text))

    return sentences


@dataclass
class TokenSpan:
    surface: str
    char_start: int
    char_end: int
    sentence_idx: int


# Token regex matching Cyrillic (including archaic Yat/I/Fita/Izhitsa: U+0400 to U+04FF), Latin, and hyphenated forms
TOKEN_PATTERN = re.compile(
    r"[A-Za-z\u0400-\u04FF]+(?:-[A-Za-z\u0400-\u04FF]+)*",
    re.UNICODE,
)


def extract_token_spans(text: str, sentence_spans: list[tuple[int, int, str]]) -> list[TokenSpan]:
    """Extract individual words and hyphenated tokens with their exact character offsets and sentence index."""
    tokens: list[TokenSpan] = []
    for s_idx, (s_start, s_end, s_text) in enumerate(sentence_spans):
        for m in TOKEN_PATTERN.finditer(s_text):
            tok_start = s_start + m.start()
            tok_end = s_start + m.end()
            tok_str = text[tok_start:tok_end]
            tokens.append(TokenSpan(surface=tok_str, char_start=tok_start, char_end=tok_end, sentence_idx=s_idx))
    return tokens


def extract_occurrences_from_passage(
    passage_id: str,
    source_id: str,
    text: str,
) -> tuple[list[NativeTerm], list[TermOccurrence], list[tuple[str, str, str]]]:
    """Scan passage text for single tokens, multiword technical phrases, hyphenated terms, and abbreviations.

    Returns:
    - terms: list of unique NativeTerm records
    - occurrences: list of TermOccurrence records
    - phrase_contains: list of (parent_term_id, child_term_id, phrase_str) for CONTAINS_TERM edges
    """
    from .language import classify_text
    from .morphology import analyze_russian_word
    from .terminology import compute_technicality

    sentences = split_sentences(text)
    token_spans = extract_token_spans(text, sentences)

    term_registry: dict[str, NativeTerm] = {}
    occurrences: list[TermOccurrence] = []
    phrase_contains: list[tuple[str, str, str]] = []

    def get_context_snippet(start: int, end: int) -> str:
        ctx_start = max(0, start - 40)
        ctx_end = min(len(text), end + 40)
        return text[ctx_start:ctx_end].replace("\n", " ").strip()

    # 1. Process Multiword Collocations (Bigrams and Trigrams)
    for i in range(len(token_spans) - 1):
        t1 = token_spans[i]
        t2 = token_spans[i + 1]

        # Only form collocations within the same sentence and adjacent words
        if t1.sentence_idx == t2.sentence_idx and (t2.char_start - t1.char_end) <= 2:
            pair = (t1.surface.lower(), t2.surface.lower())
            is_collocation = pair in COMMON_SCIENTIFIC_COLLOCATIONS

            # Also check Adjective + Noun pattern heuristic (e.g. ends in -ое, -ая, -ый + noun)
            is_adj_noun = (
                re.search(r"(ое|ая|ый|ий|ой|ые|их|ым|ого|ему|ей|ую)$", pair[0]) is not None
                and not pair[0] in RUSSIAN_STOPWORDS
                and not pair[1] in RUSSIAN_STOPWORDS
                and len(pair[0]) > 3
                and len(pair[1]) > 3
            )

            if is_collocation or is_adj_noun:
                phrase_surface = text[t1.char_start : t2.char_end]
                phrase_norm = phrase_surface
                lang_cls = classify_text(phrase_norm)
                term_id = make_term_id(phrase_norm, lang_cls.language)

                tech = compute_technicality(
                    phrase_norm,
                    term_type="compound_phrase",
                    is_eponym=any(c.isupper() for c in phrase_surface.split()[1:]),
                )

                if term_id not in term_registry:
                    term_registry[term_id] = NativeTerm(
                        id=term_id,
                        surface_form=phrase_surface,
                        normalized_unicode=phrase_norm,
                        language=lang_cls.language,
                        script=lang_cls.script,
                        term_type="compound_phrase",
                        technicality_score=tech.score,
                        signals=tech.signals,
                    )

                occ_id = make_occurrence_id(term_id, passage_id, t1.char_start, t2.char_end)
                occurrences.append(
                    TermOccurrence(
                        id=occ_id,
                        term_id=term_id,
                        passage_id=passage_id,
                        source_id=source_id,
                        surface_form=phrase_surface,
                        char_start=t1.char_start,
                        char_end=t2.char_end,
                        sentence_index=t1.sentence_idx,
                        context_snippet=get_context_snippet(t1.char_start, t2.char_end),
                    )
                )

    # 2. Process Individual Tokens
    for span in token_spans:
        raw_word = span.surface
        lower_word = raw_word.lower()

        # Filter out trivial punctuation or short common stopwords
        if lower_word in RUSSIAN_STOPWORDS or len(raw_word) < 2:
            continue

        is_hyphen = "-" in raw_word
        is_abbr = raw_word.isupper() and len(raw_word) <= 6
        is_eponym = raw_word[0].isupper() and not raw_word.isupper() and len(raw_word) > 2

        term_type = "abbreviation" if is_abbr else ("hyphenated" if is_hyphen else "single_token")

        lang_cls = classify_text(raw_word)
        term_id = make_term_id(raw_word, lang_cls.language)

        tech = compute_technicality(
            raw_word,
            term_type=term_type,
            is_hyphenated=is_hyphen,
            is_abbreviation=is_abbr,
            is_eponym=is_eponym,
        )

        if term_id not in term_registry:
            term_registry[term_id] = NativeTerm(
                id=term_id,
                surface_form=raw_word,
                normalized_unicode=raw_word,
                language=lang_cls.language,
                script=lang_cls.script,
                term_type=term_type,
                technicality_score=tech.score,
                signals=tech.signals,
            )

        occ_id = make_occurrence_id(term_id, passage_id, span.char_start, span.char_end)
        occurrences.append(
            TermOccurrence(
                id=occ_id,
                term_id=term_id,
                passage_id=passage_id,
                source_id=source_id,
                surface_form=raw_word,
                char_start=span.char_start,
                char_end=span.char_end,
                sentence_index=span.sentence_idx,
                context_snippet=get_context_snippet(span.char_start, span.char_end),
            )
        )

    # 3. Build CONTAINS_TERM links between multiword phrases and their subterms
    for t_id, t_term in term_registry.items():
        if t_term.term_type == "compound_phrase":
            words = t_term.surface_form.split()
            for w in words:
                w_id = make_term_id(w, t_term.language)
                if w_id in term_registry:
                    phrase_contains.append((t_id, w_id, t_term.surface_form))

    return list(term_registry.values()), occurrences, phrase_contains
