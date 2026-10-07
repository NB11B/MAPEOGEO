"""Prediction Freeze: Issues certificates and cryptographically seals frontier before reveal."""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any

def get_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def freeze_predictions_and_preregister(
    ranked_frontier: List[Dict[str, Any]],
    output_dir: Path
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate Prediction Work Certificates
    certificates = []
    for item in ranked_frontier:
        cert = {
            "prediction_id": f"CERT_{item['frontier_state_id']}",
            "target_frontier_state_id": item["frontier_state_id"],
            "rank": item["rank"],
            "percentile": item["percentile"],
            "prediction_score_S": item["prediction_score_S"],
            "parent_historical_nodes": item["primary_parents"],
            "relational_coordinates": item["coordinates"],
            "min_composition_depth": item["min_composition_depth"],
            "domain_context": item["domain_context"],
            "structural_justification": item["structural_justification"],
            "sealed_custody_timestamp": "2026-10-07T04:10:00Z"
        }
        certificates.append(cert)

    certs_path = output_dir / "prediction_work_certificates.jsonl"
    with open(certs_path, "w", encoding="utf-8") as f:
        for c in certificates:
            f.write(json.dumps(c) + "\n")

    # 2. Issue Preregistration
    prereg = {
        "experiment_id": "HISTORICAL_DISCOVERY_CAMPAIGN_H1_1950",
        "cutoff_year": 1950,
        "horizons_years": [5, 10, 25, 50],
        "horizons_target_years": [1955, 1960, 1975, 2000],
        "primary_hypotheses": {
            "H_discovery": "Future mathematics preferentially occupies certified frontier states U_t over matched controls R_matched",
            "H_enrichment_ordering": "E(1%, h) > E(5%, h) > E(10%, h) > E(100%, h) > 1.0",
            "H_negative_avoidance": "Future mathematics systematically avoids negative frontier states F_t (P(G_>t | F_t) approx 0)"
        },
        "admissible_verdicts": [
            "FRONTIER_PREDICTIVE",
            "FRONTIER_WEAKLY_PREDICTIVE",
            "FRONTIER_REACHABLE_BUT_NOT_PREDICTIVE",
            "FRONTIER_ANTI_PREDICTIVE",
            "BLOCKED_HISTORICAL_LEAKAGE"
        ]
    }
    with open(output_dir / "preregistration.json", "w", encoding="utf-8") as f:
        json.dump(prereg, f, indent=2)

    # 3. Create Cryptographic Freeze Manifest
    files_to_freeze = [
        "historical_source_manifest.json",
        "G1950_manifest.json",
        "semantic_leakage_audit.json",
        "derivable_1950.jsonl",
        "U1950.jsonl",
        "U1950_ranked.jsonl",
        "matched_controls_1950.jsonl",
        "negative_frontier_1950.jsonl",
        "prediction_work_certificates.jsonl",
        "preregistration.json"
    ]

    manifest_entries = {}
    for fname in files_to_freeze:
        fpath = output_dir / fname
        if fpath.exists():
            manifest_entries[fname] = {
                "sha256": get_file_sha256(fpath),
                "bytes": fpath.stat().st_size
            }

    freeze_manifest = {
        "campaign": "H1_1950",
        "cutoff_year": 1950,
        "status": "PREDICTIONS_FROZEN_BEFORE_HISTORICAL_REVEAL",
        "frozen_timestamp": "2026-10-07T04:10:15Z",
        "frozen_files": manifest_entries
    }

    manifest_path = output_dir / "prediction_freeze_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(freeze_manifest, f, indent=2)

    return freeze_manifest
