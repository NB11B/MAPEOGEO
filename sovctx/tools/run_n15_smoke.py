from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import NanoConfig, load_config
from sovctx.node.guard import ResourceGuard
from sovctx.node.ingest import IngestionEngine
from sovctx.node.passages import PassageRecord
from sovctx.node.terminology_ingest import TerminologyExtractor
from sovctx.node.work_db import WorkDatabase


def run_physical_n15_smoke(config: NanoConfig) -> dict[str, Any]:
    t0 = time.time()
    guard = ResourceGuard(config)
    db = WorkDatabase(config.work_db_path, config.sqlite)
    db.init_db()

    # Pre-flight check
    initial_sample = guard.sample(db=db)
    proc = psutil.Process(os.getpid())

    # 1. Ingest N0.5 CAS Blobs through N1 Engine
    ingest_engine = IngestionEngine(config=config, db=db)
    cas_blobs: list[tuple[str, str]] = []
    with db.get_connection() as con:
        rows = con.execute("SELECT sha256, first_url FROM source_blobs").fetchall()
        for r in rows:
            cas_blobs.append((r[0], r[1]))

    print(f"Found {len(cas_blobs)} source blobs in CAS registry.")
    ingested_sources = []
    extractor_errors = 0

    for sha, url in cas_blobs:
        try:
            res = ingest_engine.ingest_blob(sha256=sha, acquired_url=url)
            ingested_sources.append(res)
            print(f"  Ingested {res.source_id[:16]}...: {res.status} ({res.passage_count} passages)")
        except Exception as e:
            extractor_errors += 1
            print(f"  Error ingesting {sha[:12]}: {e}")

    # 2. Fetch all candidate passages from DB
    passages: list[PassageRecord] = []
    with db.get_connection() as con:
        rows = con.execute("SELECT candidate_source_id, candidate_json FROM candidate_fragments").fetchall()
        for r in rows:
            data = json.loads(r[1])
            passages.append(
                PassageRecord(
                    id=data["id"],
                    source_id=data["source_id"],
                    page_physical=data.get("page_physical", 1),
                    page_printed=data.get("page_printed"),
                    page_printed_method=data.get("page_printed_method"),
                    page_printed_confidence=data.get("page_printed_confidence", 0.0),
                    block_index=data.get("block_index", 0),
                    char_start=data.get("char_start", 0),
                    char_end=data.get("char_end", len(data.get("text_source", ""))),
                    text_source=data.get("text_source", ""),
                    text_unicode=data.get("text_unicode", ""),
                    text_search=data.get("text_search", ""),
                    language=data.get("language", "ru"),
                    script=data.get("script", "Cyrillic"),
                    language_confidence=data.get("language_confidence", 1.0),
                    extraction_method=data.get("extraction_method", "plain_text"),
                )
            )

    print(f"Total passages available for terminology extraction: {len(passages)}")
    ru_passages = [p for p in passages if p.language == "ru"]

    # 3. Execute N1.5 Terminology Extraction
    term_extractor = TerminologyExtractor(config=config, db=db)
    term_res = term_extractor.process_passages(
        passages=passages,
        source_id="N0.5_COHORT",
        persist=True,
    )

    t1 = time.time()
    elapsed_sec = round(t1 - t0, 2)

    # Post-flight sample
    post_sample = guard.sample(db=db)
    worker_rss = round(proc.memory_info().rss / (1024 * 1024), 2)

    # 4. Query Database Cumulative Statistics
    stats = db.get_terminology_stats()
    with db.get_connection() as con:
        multiword_count = con.execute(
            "SELECT COUNT(*) FROM candidate_terms WHERE term_type = 'compound_phrase'"
        ).fetchone()[0]
        historical_count = con.execute(
            "SELECT COUNT(*) FROM candidate_term_relations WHERE relation_type = 'HISTORICAL_SPELLING_OF'"
        ).fetchone()[0]

    # 5. Extract Deterministic Samples for Audit
    with db.get_connection() as con:
        sample_terms = [
            dict(r) for r in con.execute(
                "SELECT id, surface_form, normalized_unicode, term_type, technicality_score FROM candidate_terms ORDER BY technicality_score DESC, id LIMIT 20"
            ).fetchall()
        ]
        sample_multiwords = [
            dict(r) for r in con.execute(
                "SELECT id, surface_form, normalized_unicode, technicality_score FROM candidate_terms WHERE term_type = 'compound_phrase' ORDER BY id LIMIT 10"
            ).fetchall()
        ]
        sample_symbols = [
            dict(r) for r in con.execute(
                "SELECT id, symbol, passage_id, surface_context FROM candidate_symbol_occurrences ORDER BY id LIMIT 10"
            ).fetchall()
        ]
        sample_equations = [
            dict(r) for r in con.execute(
                "SELECT id, passage_id, surface_representation, locator FROM candidate_equation_witnesses ORDER BY id LIMIT 5"
            ).fetchall()
        ]
        sample_definitions = [
            dict(r) for r in con.execute(
                "SELECT id, passage_id, trigger, defining_span FROM candidate_definition_spans ORDER BY id LIMIT 5"
            ).fetchall()
        ]

    campaign_id = f"N1.5_SMOKE_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    timestamp_str = datetime.now(timezone.utc).isoformat()

    metrics = {
        "sources_processed": len(cas_blobs),
        "passages_processed": len(passages),
        "russian_passages": len(ru_passages),
        "terms_extracted": stats["occurrences"],
        "unique_native_terms": stats["terms"],
        "multiword_terms": multiword_count,
        "historical_forms": historical_count,
        "symbol_witnesses": stats["symbols"],
        "equation_witnesses": stats["equation_witnesses"],
        "definition_candidates": stats["definitions"],
        "extractor_errors": extractor_errors,
        "worker_rss_peak_mb": worker_rss,
        "thermal_peak_c": post_sample.thermal_max_c,
        "ram_available_mb": post_sample.ram_available_mb,
        "elapsed_seconds": elapsed_sec,
    }

    receipt_data = {
        "gate": "N1.5_NATIVE_TERMINOLOGY",
        "campaign_id": campaign_id,
        "timestamp": timestamp_str,
        "verdict": "PASS" if extractor_errors == 0 and stats["terms"] > 0 else "FAIL",
        "target_node": "Jetson Nano 2GB (uow@192.168.55.1)",
        "metrics": metrics,
        "audit_sample": {
            "term_occurrences_20": sample_terms,
            "multiword_phrases_10": sample_multiwords,
            "symbol_occurrences_10": sample_symbols,
            "equation_witnesses_5": sample_equations,
            "definition_candidates_5": sample_definitions,
        },
    }

    # Emit receipt and markdown report
    receipt_dir = config.evidence_dir / "manifests"
    report_dir = config.evidence_dir / "runs"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    receipt_path = receipt_dir / "n15_smoke_receipt.json"
    report_path = report_dir / "n15_smoke_report.md"

    receipt_path.write_text(json.dumps(receipt_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Render Markdown Report
    md_lines = [
        "# SOVCTX Gate N1.5 Physical Smoke Qualification Report",
        "",
        f"- **Campaign ID**: `{campaign_id}`",
        f"- **Timestamp**: `{timestamp_str}`",
        f"- **Verdict**: **{receipt_data['verdict']}**",
        "- **Target Node**: Jetson Nano 2GB (`uow@192.168.55.1`)",
        "",
        "## Metrics Tree",
        "",
        "```text",
        f"sources processed:        {metrics['sources_processed']}",
        f"passages processed:       {metrics['passages_processed']}",
        f"Russian passages:         {metrics['russian_passages']}",
        f"terms extracted:          {metrics['terms_extracted']}",
        f"unique native terms:      {metrics['unique_native_terms']}",
        f"multiword terms:          {metrics['multiword_terms']}",
        f"historical forms:         {metrics['historical_forms']}",
        f"symbol witnesses:         {metrics['symbol_witnesses']}",
        f"equation witnesses:       {metrics['equation_witnesses']}",
        f"definition candidates:    {metrics['definition_candidates']}",
        f"extractor errors:         {metrics['extractor_errors']}",
        f"worker RSS peak:          {metrics['worker_rss_peak_mb']} MB",
        f"thermal peak:             {metrics['thermal_peak_c']} °C",
        f"RAM available:            {metrics['ram_available_mb']} MB",
        f"elapsed time:             {metrics['elapsed_seconds']} s",
        "```",
        "",
        "## Deterministic Audit Sample",
        "",
        "### Top 5 Multiword Technical Phrases",
    ]
    for m in sample_multiwords[:5]:
        md_lines.append(f"- `{m['surface_form']}` (score: {m['technicality_score']})")

    md_lines.extend(["", "### Top 5 Definition Candidates"])
    for d in sample_definitions[:5]:
        md_lines.append(f"- Trigger: `{d['trigger']}` | Span: `{d['defining_span'][:80]}...`")

    md_lines.extend(["", "### Top 5 Symbol Occurrences"])
    for s in sample_symbols[:5]:
        md_lines.append(f"- Symbol: `{s['symbol']}` | Context: `{s['surface_context']}`")

    md_text = "\n".join(md_lines)
    report_path.write_text(md_text, encoding="utf-8")

    # Top-level evidence copies
    try:
        (config.evidence_dir / "n15_smoke_receipt.json").write_text(
            json.dumps(receipt_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (config.evidence_dir / "n15_smoke_report.md").write_text(md_text, encoding="utf-8")
    except Exception:
        pass

    return receipt_data


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Gate N1.5 Physical Smoke Qualification Runner")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    res = run_physical_n15_smoke(config)

    print("===========================================================")
    print(f"SOVCTX Gate N1.5 Physical Smoke: {res['verdict']}")
    print(f"Campaign: {res['campaign_id']}")
    print("===========================================================")
    m = res["metrics"]
    for k, v in m.items():
        print(f"  {k:25}: {v}")
    print("===========================================================")
    print(f"Receipt written to: {config.evidence_dir / 'manifests' / 'n15_smoke_receipt.json'}")
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
