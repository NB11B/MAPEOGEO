from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Optional

from .language import classify_text
from .passages import (
    PassageRecord,
    build_text_representations,
    detect_equation_witnesses,
    make_passage_id,
)
from .references import is_bibliography_header


class TextBlockExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[str] = []
        self._current_text: list[str] = []
        self._in_ignored = False
        self._ignored_tags = {"script", "style", "nav", "noscript", "svg"}
        self._block_tags = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre"}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() in self._ignored_tags:
            self._in_ignored = True
        elif tag.lower() in self._block_tags:
            self._flush_block()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._ignored_tags:
            self._in_ignored = False
        elif tag.lower() in self._block_tags:
            self._flush_block()

    def handle_data(self, data: str) -> None:
        if not self._in_ignored:
            self._current_text.append(data)

    def _flush_block(self) -> None:
        if self._current_text:
            text = "".join(self._current_text).strip()
            if text:
                self.blocks.append(text)
            self._current_text = []

    def close(self) -> None:
        self._flush_block()
        super().close()


def extract_html_passages(
    html_bytes: bytes,
    source_sha256: str,
) -> list[PassageRecord]:
    """Extract deterministic passage records from HTML source bytes."""
    try:
        html_str = html_bytes.decode("utf-8")
    except UnicodeDecodeError:
        html_str = html_bytes.decode("latin-1", errors="replace")

    parser = TextBlockExtractor()
    parser.feed(html_str)
    parser.close()

    source_id = f"SOVSRC:{source_sha256}"
    passages: list[PassageRecord] = []
    char_offset = 0
    in_bibliography = False

    for block_idx, block_text in enumerate(parser.blocks):
        clean_text = block_text.strip()
        if not clean_text:
            continue

        block_start = char_offset
        block_end = block_start + len(clean_text)
        char_offset = block_end + 1

        if is_bibliography_header(clean_text.splitlines()[0]):
            in_bibliography = True

        text_src, text_uni, text_srch = build_text_representations(clean_text)
        lang_analysis = classify_text(text_uni)

        pid = make_passage_id(
            source_sha256=source_sha256,
            page_physical=1,
            block_index=block_idx,
            char_start=block_start,
            char_end=block_end,
        )

        eq_witnesses = detect_equation_witnesses(
            source_sha256=source_sha256,
            passage_id=pid,
            physical_page=1,
            text=text_src,
            extraction_method="html_text",
        )

        record = PassageRecord(
            id=pid,
            source_id=source_id,
            page_physical=1,
            page_printed=None,
            page_printed_method=None,
            page_printed_confidence=0.0,
            block_index=block_idx,
            char_start=block_start,
            char_end=block_end,
            text_source=text_src,
            text_unicode=text_uni,
            text_search=text_srch,
            language=lang_analysis.language,
            script=lang_analysis.script,
            language_confidence=lang_analysis.confidence,
            is_footnote=False,
            is_table=False,
            is_reference=in_bibliography,
            equation_witnesses=eq_witnesses,
            extraction_method="html_text",
        )
        passages.append(record)

    return passages
