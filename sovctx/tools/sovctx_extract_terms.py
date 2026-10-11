from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import load_config
from sovctx.node.passages import PassageRecord
from sovctx.node.terminology_ingest import TerminologyExtractor
from sovctx.node.work_db import WorkDatabase


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SOVCTX Gate N1.5 Native Terminology Extractor"
    )
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    parser.add_argument("--source-id", type=str, default=None, help="Process passages for specific SOVSRC ID")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of passages to process (default: 100)")
    parser.add_argument("--json", action="store_true", help="Output summary as JSON")
    args = parser.parse_args()

    config = load_config(args.config)
    db = WorkDatabase(config.work_db_path, config.sqlite)
    extractor = TerminologyExtractor(config=config, db=db)

    # Fetch candidate passages
    passages: list[PassageRecord] = []
    with db.get_connection() as con:
        if args.source_id:
            query = """
            SELECT candidate_source_id, candidate_json
            FROM candidate_fragments
            WHERE candidate_source_id = ?
            LIMIT ?
            """
            rows = con.execute(query, (args.source_id, args.limit)).fetchall()
        else:
            query = """
            SELECT candidate_source_id, candidate_json
            FROM candidate_fragments
            LIMIT ?
            """
            rows = con.execute(query, (args.limit,)).fetchall()

        for row in rows:
            data = json.loads(row[1])
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

    if not passages:
        print("No candidate passages found to process.")
        return 0

    source_id = args.source_id or passages[0].source_id
    result = extractor.process_passages(passages, source_id=source_id, persist=True)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        stats = db.get_terminology_stats()
        print("===========================================================")
        print("SOVCTX Gate N1.5 Native Terminology Extraction")
        print("===========================================================")
        print(f"Passages Processed:    {len(passages)}")
        print(f"Terms Extracted:       {len(result.terms)}")
        print(f"Occurrences Bound:     {len(result.occurrences)}")
        print(f"Relations Inferred:    {len(result.relations)}")
        print(f"Definitions Detected:  {len(result.definitions)}")
        print(f"Symbols Bound:         {len(result.symbols)}")
        print(f"Equation Witnesses:    {len(result.equation_witnesses)}")
        print("-----------------------------------------------------------")
        print("Database Cumulative Terminology Totals:")
        print(f"├── Total Unique Terms:        {stats['terms']}")
        print(f"├── Total Term Occurrences:    {stats['occurrences']}")
        print(f"├── Total Term Relations:      {stats['relations']}")
        print(f"├── Total Definition Spans:    {stats['definitions']}")
        print(f"├── Total Symbol Occurrences:  {stats['symbols']}")
        print(f"└── Total Equation Witnesses:  {stats['equation_witnesses']}")
        print("===========================================================")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
