from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .cas import BlobStore
from .config import NanoConfig, load_config
from .detect import detect_format
from .html_extract import extract_html_passages
from .passages import PassageRecord
from .pdf_extract import (
    EncryptedPDFError,
    MalformedPDFError,
    extract_pdf_passages,
)
from .source import SourceRecord, make_source_id
from .work_db import CandidateSource, WorkDatabase


@dataclass
class IngestionResult:
    source_id: str
    sha256: str
    status: str  # "SUCCESS", "OCR_CANDIDATE", "QUARANTINED", "ALREADY_INGESTED"
    passage_count: int
    equation_witness_count: int
    is_ocr_candidate: bool
    format: str
    quarantine_reason: Optional[str] = None
    passages: list[PassageRecord] = None  # type: ignore

    def __post_init__(self):
        if self.passages is None:
            self.passages = []


class IngestionEngine:
    """Deterministic N1 Source Ingestion Engine for SOVCTX.

    Transforms raw immutable CAS blobs into faithful, provenance-preserving
    source records, physical passages, and unnormalized equation witnesses.
    Never creates candidate graph edges or interprets historical influence.
    """

    def __init__(
        self,
        config: Optional[NanoConfig] = None,
        db: Optional[WorkDatabase] = None,
        cas: Optional[BlobStore] = None,
    ) -> None:
        self.config = config or load_config()
        self.config.ensure_directories()
        self.db = db or WorkDatabase(self.config.work_db_path, self.config.sqlite)
        self.db.init_db()
        self.cas = cas or BlobStore(
            cas_root=self.config.raw_dir,
            max_payload_bytes=self.config.crawler.max_payload_mb * 1024 * 1024,
            quarantine_dir=self.config.quarantine_dir,
        )

    def ingest_blob(
        self,
        sha256: str,
        acquired_url: Optional[str] = None,
        force_reingest: bool = False,
    ) -> IngestionResult:
        source_id = make_source_id(sha256)

        # Check if already ingested in database
        if not force_reingest:
            with self.db.get_connection() as con:
                row = con.execute(
                    "SELECT * FROM candidate_sources WHERE id = ?",
                    (source_id,),
                ).fetchone()
                if row:
                    passages_count = con.execute(
                        "SELECT COUNT(*) FROM candidate_fragments WHERE candidate_source_id = ?",
                        (source_id,),
                    ).fetchone()[0]
                    return IngestionResult(
                        source_id=source_id,
                        sha256=sha256,
                        status="ALREADY_INGESTED",
                        passage_count=passages_count,
                        equation_witness_count=0,
                        is_ocr_candidate=row["status"] == "OCR_CANDIDATE",
                        format="known",
                    )

        # Read blob from CAS
        try:
            raw_bytes = self.cas.read_blob(sha256)
        except FileNotFoundError:
            return IngestionResult(
                source_id=source_id,
                sha256=sha256,
                status="QUARANTINED",
                passage_count=0,
                equation_witness_count=0,
                is_ocr_candidate=False,
                format="unknown",
                quarantine_reason="BLOB_NOT_FOUND_IN_CAS",
            )

        # 1. Format Detection
        fmt = detect_format(raw_bytes)
        if not fmt.is_supported or fmt.quarantine_reason:
            reason = fmt.quarantine_reason or "UNSUPPORTED_FORMAT"
            self.db.record_quarantine(
                quarantine_reason=reason,
                url=acquired_url,
                sha256=sha256,
                metadata={"format": fmt.mime_type},
            )
            return IngestionResult(
                source_id=source_id,
                sha256=sha256,
                status="QUARANTINED",
                passage_count=0,
                equation_witness_count=0,
                is_ocr_candidate=False,
                format=fmt.mime_type,
                quarantine_reason=reason,
            )

        # 2. Text Extraction by Format
        passages: list[PassageRecord] = []
        is_ocr = False
        format_name = "unknown"

        if fmt.is_pdf:
            format_name = "pdf"
            try:
                pdf_res = extract_pdf_passages(raw_bytes, source_sha256=sha256)
                passages = pdf_res.passages
                is_ocr = pdf_res.is_ocr_candidate
            except (EncryptedPDFError, MalformedPDFError) as err:
                reason = type(err).__name__
                self.db.record_quarantine(
                    quarantine_reason=reason,
                    url=acquired_url,
                    sha256=sha256,
                    metadata={"error": str(err)},
                )
                return IngestionResult(
                    source_id=source_id,
                    sha256=sha256,
                    status="QUARANTINED",
                    passage_count=0,
                    equation_witness_count=0,
                    is_ocr_candidate=False,
                    format=format_name,
                    quarantine_reason=reason,
                )

        elif fmt.is_html:
            format_name = "html"
            passages = extract_html_passages(raw_bytes, source_sha256=sha256)

        elif fmt.is_image:
            format_name = "image"
            is_ocr = True
            passages = []

        elif fmt.is_text:
            format_name = "text"
            # Plain text document: single physical page, segment by paragraphs
            text_str = raw_bytes.decode("utf-8", errors="replace")
            from .passages import build_text_representations, make_passage_id
            from .language import classify_text
            text_src, text_uni, text_srch = build_text_representations(text_str)
            lang = classify_text(text_uni)
            pid = make_passage_id(sha256, 1, 0, 0, len(text_str))
            passages = [
                PassageRecord(
                    id=pid,
                    source_id=source_id,
                    page_physical=1,
                    page_printed=None,
                    page_printed_method=None,
                    page_printed_confidence=0.0,
                    block_index=0,
                    char_start=0,
                    char_end=len(text_str),
                    text_source=text_src,
                    text_unicode=text_uni,
                    text_search=text_srch,
                    language=lang.language,
                    script=lang.script,
                    language_confidence=lang.confidence,
                    extraction_method="plain_text",
                )
            ]

        # 3. Build Source Record
        status = "OCR_CANDIDATE" if is_ocr else "EXTRACTED"
        source_rec = SourceRecord(
            source_id=source_id,
            sha256=sha256,
            byte_size=len(raw_bytes),
            format=format_name,
            acquired_urls=[acquired_url] if acquired_url else [],
            status=status,
            passage_count=len(passages),
        )

        # 4. Persist to Work Database
        with self.db.get_connection() as con:
            row = con.execute("SELECT sha256 FROM source_blobs WHERE sha256 = ?", (sha256,)).fetchone()
            if not row:
                self.db.register_blob(
                    sha256=sha256,
                    storage_path=str(self.cas.blob_rel_path(sha256)),
                    byte_size=len(raw_bytes),
                    content_type=fmt.mime_type or "application/octet-stream",
                    inferred_type=format_name,
                    first_url=acquired_url or "",
                )

        cand_src = CandidateSource(
            id=source_id,
            source_url=acquired_url or "",
            sha256=sha256,
            acquired_at=source_rec.first_acquired_at,
            parser_version="n1-v0.1",
            originating_queue_item=None,
            candidate_json=json.dumps(source_rec.to_dict(), ensure_ascii=False),
            status=status,
        )
        self.db.insert_candidate_source(cand_src)

        # Insert candidate fragments / passages
        total_equations = 0
        with self.db.get_connection() as con:
            for p in passages:
                total_equations += len(p.equation_witnesses)
                frag_data = p.to_candidate_fragment()
                con.execute(
                    """
                    INSERT OR REPLACE INTO candidate_fragments (
                        id, candidate_source_id, source_url, sha256, locator,
                        extracted_at, parser_version, candidate_json, status
                    ) VALUES (?, ?, ?, ?, ?, datetime('now'), 'n1-v0.1', ?, 'CANDIDATE')
                    """,
                    (
                        frag_data["id"],
                        frag_data["candidate_source_id"],
                        frag_data["source_url"],
                        frag_data["sha256"],
                        frag_data["locator"],
                        frag_data["candidate_json"],
                    ),
                )
            con.commit()

        return IngestionResult(
            source_id=source_id,
            sha256=sha256,
            status=status,
            passage_count=len(passages),
            equation_witness_count=total_equations,
            is_ocr_candidate=is_ocr,
            format=format_name,
            passages=passages,
        )
