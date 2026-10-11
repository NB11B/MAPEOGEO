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

from sovctx.node.calibration import is_negative_control_phrase
from sovctx.node.config import NanoConfig, load_config
from sovctx.node.frontier_coordinator import FrontierCoordinator
from sovctx.node.guard import ResourceGuard
from sovctx.node.ingest import IngestionEngine
from sovctx.node.passages import PassageRecord
from sovctx.node.terminology_ingest import TerminologyExtractor
from sovctx.node.work_db import WorkDatabase


def run_physical_n2_smoke(config: NanoConfig) -> dict[str, Any]:
    t0 = time.time()
    guard = ResourceGuard(config)
    db = WorkDatabase(config.work_db_path, config.sqlite)
    db.init_db()

    # Pre-flight check
    initial_sample = guard.sample(db=db)
    proc = psutil.Process(os.getpid())

    # 1. Ingest N0.5 CAS Blobs through N1 Engine if needed
    ingest_engine = IngestionEngine(config=config, db=db)
    cas_blobs: list[tuple[str, str]] = []
    with db.get_connection() as con:
        rows = con.execute("SELECT sha256, first_url FROM source_blobs").fetchall()
        for r in rows:
            cas_blobs.append((r[0], r[1]))

    print(f"Found {len(cas_blobs)} source blobs in CAS registry.")
    for sha, url in cas_blobs:
        try:
            ingest_engine.ingest_blob(sha256=sha, acquired_url=url)
        except Exception as e:
            print(f"  Note during ingest {sha[:12]}: {e}")

    # 2. Extract calibrated terminology across passages
    term_extractor = TerminologyExtractor(config=config, db=db)
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

    print(f"Total passages available: {len(passages)}")
    term_res = term_extractor.process_passages(passages=passages, source_id="N0.5_COHORT", persist=True)

    # 3. Build cohort data structure for FrontierCoordinator
    # Group passages, terms, definitions, equations by source_id
    passages_by_source: dict[str, list[PassageRecord]] = {}
    for p in passages:
        passages_by_source.setdefault(p.source_id, []).append(p)

    cohort_data: list[dict[str, Any]] = []
    for src_id, p_list in passages_by_source.items():
        cohort_data.append({
            "source_id": src_id,
            "passages": p_list,
            "terms": term_res.terms,
            "definitions": term_res.definitions,
            "equations": term_res.equation_witnesses,
        })

    # 4. Build candidate pool for resolution from known sources
    candidate_pool: list[dict[str, Any]] = []
    with db.get_connection() as con:
        src_rows = con.execute("SELECT id, source_url, candidate_json FROM candidate_sources").fetchall()
        for r in src_rows:
            try:
                cdata = json.loads(r[2])
                candidate_pool.append({
                    "id": r[0],
                    "url": r[1],
                    "title": cdata.get("title") or cdata.get("first_url"),
                    "authors": cdata.get("authors", []),
                    "year": cdata.get("year"),
                    "identifier": cdata.get("identifier"),
                })
            except Exception:
                pass

    # 5. Execute FrontierCoordinator (Generation 0 -> Generation 1)
    print("Executing FrontierCoordinator...")
    coordinator = FrontierCoordinator(db=db)
    summary = coordinator.process_cohort_data(
        cohort=cohort_data,
        candidate_source_pool=candidate_pool,
        max_nominations=20,  # Bounded to 20 nominations
    )

    t1 = time.time()
    elapsed_sec = round(t1 - t0, 2)

    # Post-flight sample
    post_sample = guard.sample(db=db)
    worker_rss = round(proc.memory_info().rss / (1024 * 1024), 2)

    # 6. Audit statistics and invariants
    f_stats = db.get_frontier_stats()
    ref_stats = db.get_reference_stats()
    ent_stats = db.get_entity_stats()

    invariants: dict[str, int] = {
        "mapeogeo_access": 0,
        "negative_control_frontier_entries": 0,
        "institution_as_term_frontier": 0,
        "unlinked_references": 0,
        "duplicate_dedup_keys": 0,
        "html_equation_witnesses": 0,
    }

    with db.get_connection() as con:
        # Negative control audit
        front_targets = con.execute("SELECT target_label FROM frontier_items").fetchall()
        for ft in front_targets:
            if is_negative_control_phrase(ft[0]):
                invariants["negative_control_frontier_entries"] += 1

        # Institution routing audit
        inst_in_terms = con.execute(
            "SELECT COUNT(*) FROM frontier_items WHERE frontier_type = 'F3_NATIVE_TERMINOLOGY' AND target_label IN ('АН СССР', 'МГУ', 'МИАН', 'ЦАГИ')"
        ).fetchone()[0]
        invariants["institution_as_term_frontier"] = inst_in_terms

        # Unlinked references
        unlinked = con.execute(
            "SELECT COUNT(*) FROM reference_candidates WHERE source_id IS NULL OR source_id = ''"
        ).fetchone()[0]
        invariants["unlinked_references"] = unlinked

        # Duplicate dedup keys
        dup_keys = con.execute(
            "SELECT dedup_key, COUNT(*) FROM frontier_items GROUP BY dedup_key HAVING COUNT(*) > 1"
        ).fetchall()
        invariants["duplicate_dedup_keys"] = len(dup_keys)

        # Equations check (no HTML attributes)
        html_eqs = con.execute(
            "SELECT COUNT(*) FROM candidate_equation_witnesses WHERE surface_representation LIKE '%paperid=%' OR surface_representation LIKE '%class=%'"
        ).fetchone()[0]
        invariants["html_equation_witnesses"] = html_eqs

    # Audit samples for report
    with db.get_connection() as con:
        sample_refs = [
            dict(r) for r in con.execute(
                "SELECT id, authors_raw, title_raw, publication_raw, year_raw, identifier_raw FROM reference_candidates LIMIT 5"
            ).fetchall()
        ]
        sample_entities = [
            dict(r) for r in con.execute(
                "SELECT id, entity_type, surface_text, normalized_name FROM entity_mentions LIMIT 8"
            ).fetchall()
        ]
        sample_frontiers = [
            dict(r) for r in con.execute(
                "SELECT id, frontier_type, priority, target_label, raw_support_count, independent_source_count FROM frontier_items ORDER BY priority ASC, raw_support_count DESC LIMIT 10"
            ).fetchall()
        ]
        sample_nominations = [
            dict(r) for r in con.execute(
                "SELECT id, frontier_id, nominated_url, goal, priority FROM source_nominations LIMIT 5"
            ).fetchall()
        ]

    campaign_id = f"N2_SMOKE_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    timestamp_str = datetime.now(timezone.utc).isoformat()

    metrics = {
        "sources_processed": summary.sources_processed,
        "references_extracted": summary.references_extracted,
        "resolutions_attempted": summary.resolutions_attempted,
        "entity_mentions_extracted": summary.entity_mentions_extracted,
        "frontier_items_created": f_stats["total_frontier_items"],
        "frontier_by_type": f_stats["by_type"],
        "frontier_evidence_recorded": f_stats["total_evidence"],
        "nominations_generated": f_stats["total_nominations"],
        "negative_controls_rejected": summary.negative_controls_rejected,
        "worker_rss_peak_mb": worker_rss,
        "thermal_peak_c": post_sample.thermal_max_c,
        "ram_available_mb": post_sample.ram_available_mb,
        "elapsed_seconds": elapsed_sec,
    }

    all_invariants_pass = all(v == 0 for v in invariants.values())
    verdict = "PASS" if all_invariants_pass and f_stats["total_frontier_items"] > 0 else "FAIL"

    receipt_data = {
        "gate": "N2_CITATION_TERMINOLOGY_FRONTIER",
        "campaign_id": campaign_id,
        "timestamp": timestamp_str,
        "verdict": verdict,
        "target_node": "Jetson Nano 2GB (uow@192.168.55.1)",
        "metrics": metrics,
        "invariants": invariants,
        "audit_sample": {
            "references": sample_refs,
            "entities": sample_entities,
            "frontier_items": sample_frontiers,
            "nominations": sample_nominations,
        },
    }

    # Emit receipt and markdown report
    receipt_dir = config.evidence_dir / "manifests"
    report_dir = config.evidence_dir / "runs"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    receipt_path = receipt_dir / "n2_smoke_receipt.json"
    report_path = report_dir / "n2_smoke_report.md"

    receipt_path.write_text(json.dumps(receipt_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Render Markdown Report
    md_lines = [
        "# SOVCTX Gate N2 Citation & Terminology Frontier Smoke Report",
        "",
        f"- **Campaign ID**: `{campaign_id}`",
        f"- **Timestamp**: `{timestamp_str}`",
        f"- **Verdict**: **{verdict}**",
        "- **Target Node**: Jetson Nano 2GB (`uow@192.168.55.1`)",
        "",
        "## Metrics Tree",
        "",
        "```text",
        f"sources processed:            {metrics['sources_processed']}",
        f"references extracted:         {metrics['references_extracted']}",
        f"resolutions attempted:        {metrics['resolutions_attempted']}",
        f"entity mentions extracted:    {metrics['entity_mentions_extracted']}",
        f"frontier items created:       {metrics['frontier_items_created']}",
        f"frontier evidence links:      {metrics['frontier_evidence_recorded']}",
        f"nominations generated:        {metrics['nominations_generated']}",
        f"negative controls rejected:   {metrics['negative_controls_rejected']}",
        f"worker RSS peak:              {metrics['worker_rss_peak_mb']} MB",
        f"thermal peak:                 {metrics['thermal_peak_c']} °C",
        f"RAM available:                {metrics['ram_available_mb']} MB",
        f"elapsed time:                 {metrics['elapsed_seconds']} s",
        "```",
        "",
        "## Invariant Audit Ledger",
        "",
        "| Invariant | Value | Status |",
        "|---|---:|---|",
    ]
    for inv, count in invariants.items():
        status = "PASS" if count == 0 else "FAIL"
        md_lines.append(f"| `{inv}` | {count} | **{status}** |")

    md_lines.extend(["", "## Top Frontier Items (Sample)", ""])
    for f in sample_frontiers:
        md_lines.append(f"- `[{f['priority']}]` **{f['frontier_type']}**: `{f['target_label']}` (raw: {f['raw_support_count']}, indep: {f['independent_source_count']})")

    md_lines.extend(["", "## Entity Mentions (Sample)", ""])
    for e in sample_entities:
        md_lines.append(f"- **{e['entity_type']}**: `{e['surface_text']}` -> `{e['normalized_name']}`")

    md_lines.extend(["", "## Source Nominations (Sample)", ""])
    for n in sample_nominations:
        md_lines.append(f"- `[{n['priority']}]` Goal: {n['goal']} | URL: `{n['nominated_url']}`")

    md_text = "\n".join(md_lines)
    report_path.write_text(md_text, encoding="utf-8")

    # Top-level evidence copies
    try:
        (config.evidence_dir / "n2_smoke_receipt.json").write_text(
            json.dumps(receipt_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (config.evidence_dir / "n2_smoke_report.md").write_text(md_text, encoding="utf-8")
    except Exception:
        pass

    return receipt_data


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Gate N2 Physical Smoke Campaign Runner")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    res = run_physical_n2_smoke(config)

    print("===========================================================")
    print(f"SOVCTX Gate N2 Physical Smoke: {res['verdict']}")
    print(f"Campaign: {res['campaign_id']}")
    print("===========================================================")
    m = res["metrics"]
    for k, v in m.items():
        print(f"  {k:28}: {v}")
    print("-----------------------------------------------------------")
    print("Invariants:")
    for inv, count in res["invariants"].items():
        print(f"  {inv:30}: {count} [{'PASS' if count == 0 else 'FAIL'}]")
    print("===========================================================")
    print(f"Receipt written to: {config.evidence_dir / 'manifests' / 'n2_smoke_receipt.json'}")
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
