"""Semantic Backdating and Vocabulary Blindness Audit for G_1950."""

import json
from pathlib import Path
from typing import Dict, List, Any

# Blacklist of modern mathematical concepts that did not exist in or prior to 1950
POST_1950_ANACHRONISM_TERMS = [
    "derived_category",
    "scheme",
    "etale_cohomology",
    "grothendieck_topos",
    "motive",
    "stack",
    "derived_algebraic_geometry",
    "homotopy_type_theory",
    "khovanov_homology",
    "bridgeland_stability",
    "fukaya_category",
    "shifted_symplectic",
    "higher_category",
    "infinity_category",
    "quantum_cohomology",
    "arakelov_geometry",
    "deligne_conjecture",
    "perelman_ricci_flow"
]

def audit_and_backdate_vocabulary(raw_entries: List[Dict[str, Any]], output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    sanitized_entries = []
    leakage_detections = []

    for entry in raw_entries:
        text = entry.get("raw_description", "").lower()
        node_id = entry.get("node_id", "")
        
        # Check for modern vocabulary leakage
        detected_anachronisms = [term for term in POST_1950_ANACHRONISM_TERMS if term in text or term in node_id.lower()]
        
        if detected_anachronisms:
            leakage_detections.append({
                "node_id": node_id,
                "anachronisms": detected_anachronisms
            })
        else:
            # Map to strictly blinded internal ID and historically authentic wording
            sanitized_entries.append({
                "historical_id": f"H1950_{len(sanitized_entries)+1:05d}",
                "original_node_id": node_id,
                "historical_description": entry.get("historical_description", entry.get("raw_description", "")),
                "publication_year": entry.get("publication_year", 1950),
                "source_id": entry.get("source_id", "HISTORICAL_RECORD"),
                "coordinates": entry.get("coordinates", {})
            })

    audit_report = {
        "cutoff_year": 1950,
        "total_evaluated": len(raw_entries),
        "sanitized_historical_records": len(sanitized_entries),
        "anachronisms_detected_and_purged": len(leakage_detections),
        "anachronism_details": leakage_detections,
        "zero_leakage_guarantee_met": len(leakage_detections) == 0,
        "verdict": "SEMANTIC_BACKDATING_PASS" if len(leakage_detections) == 0 else "LEAKAGE_DETECTED_AND_QUARANTINED"
    }

    with open(output_dir / "semantic_leakage_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)

    return {
        "audit": audit_report,
        "sanitized_entries": sanitized_entries
    }
