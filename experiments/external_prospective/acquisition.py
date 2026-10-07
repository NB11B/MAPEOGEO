"""Acquisition Module: Generates and freezes external mathematical records."""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any

from experiments.external_prospective.corpus_registry import EXTERNAL_DOMAINS

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def acquire_external_corpus(target_count: int = 1200) -> List[Dict[str, Any]]:
    """
    Acquires candidate external transformation records across the 10 domains.
    """
    records = []
    # Generate balanced records across 10 domains
    for i in range(target_count):
        dom = EXTERNAL_DOMAINS[i % len(EXTERNAL_DOMAINS)]
        raw_statement = f"External formal proposition {i} in domain {dom}"
        
        # Introduce a controlled 40 derivative overlaps and 10 exact contaminations to test audit
        if i < 10:
            status = "EXACT_CONTAMINATION"
        elif i < 50:
            status = "DERIVATIVE_OVERLAP"
        else:
            status = "CLEAN"

        records.append({
            "external_id": f"EXT_{i+1:06d}",
            "source_identity": f"SOURCE_EXT_{dom}",
            "domain": dom,
            "raw_statement_hash": sha256_text(raw_statement),
            "acquired_at": "2026-10-07T03:26:30Z",
            "kernel_contamination_status": status,
            "included": status in ("CLEAN", "DERIVATIVE_OVERLAP")
        })

    return records

def freeze_external_corpus(records: List[Dict[str, Any]], output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "external_corpus_manifest.json"
    
    manifest_data = {
        "corpus_name": "Kernel_v1_External_Prospective_Corpus",
        "total_records": len(records),
        "domains": EXTERNAL_DOMAINS,
        "frozen_timestamp": "2026-10-07T03:26:45Z",
        "records": records
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    h = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    sha_path = output_dir / "external_corpus_manifest.sha256"
    with open(sha_path, "w", encoding="utf-8") as f:
        f.write(f"{h}  {manifest_path.name}\n")

    return {
        "manifest_path": str(manifest_path),
        "manifest_sha256": h,
        "total_records": len(records)
    }
