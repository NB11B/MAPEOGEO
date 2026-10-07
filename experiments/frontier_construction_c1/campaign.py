"""Master Campaign Orchestrator for Campaign C1 (Prospective Construction)."""

import json
from pathlib import Path
from typing import Dict, Any

from experiments.frontier_construction_c1.certificate_loader import load_and_verify_candidate_certificate
from experiments.frontier_construction_c1.realizability import adjudicate_realizability
from experiments.frontier_construction_c1.report import generate_c1_report

DEFAULT_OUTPUT_DIR = Path("artifacts/frontier_construction_c1")

def run_campaign_c1(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("CAMPAIGN C1: PROSPECTIVE CONSTRUCTION OF CANDIDATE #1 (U2026_CONST_0001)")
    print("=" * 70)

    # 1. Load Certificate and verify cryptographic custody
    print("Step 1: Loading frozen certificate and verifying SHA-256 seal...")
    cert_data = load_and_verify_candidate_certificate("U2026_CONST_0001")
    cert = cert_data["certificate"]

    # 2. Execute Realizability Adjudication Pipeline
    print("Step 2: Executing Type Check (Gate C1.1), Obligations O1-O3, and Obstruction Search...")
    adjudication = adjudicate_realizability(cert)

    # 3. Save Machine-Readable Artifacts
    print("Step 3: Saving machine-readable artifacts...")
    with open(output_dir / "certificate_audit.json", "w", encoding="utf-8") as f:
        json.dump(cert_data, f, indent=2)

    with open(output_dir / "realizability_adjudication.json", "w", encoding="utf-8") as f:
        json.dump(adjudication, f, indent=2)

    # 4. Generate Comprehensive Report
    print("Step 4: Generating PROSPECTIVE_CONSTRUCTION_C1_REPORT.md...")
    report_content = generate_c1_report(output_dir, adjudication, cert)

    print(f"Campaign C1 Complete. Official Verdict: {adjudication['verdict']}")
    return {
        "verdict": adjudication["verdict"],
        "adjudication": adjudication,
        "report": report_content
    }

if __name__ == "__main__":
    run_campaign_c1()
