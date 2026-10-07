"""Certificate Loader and Cryptographic Integrity Verifier for Campaign C1.

Loads PWC_2026_U2026_CONST_0001 without modification and verifies SHA-256 seal.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Any

CERTIFICATE_PATH = Path("artifacts/rolling_historical_h2/frontier_2026/prediction_work_certificates_2026.jsonl")
FREEZE_MANIFEST_PATH = Path("artifacts/rolling_historical_h2/frontier_2026/prediction_freeze_manifest_2026.json")

def load_and_verify_candidate_certificate(candidate_id: str = "U2026_CONST_0001") -> Dict[str, Any]:
    """Loads Candidate #1 certificate from the sealed 2026 freeze and validates custody."""
    if not CERTIFICATE_PATH.exists():
        raise FileNotFoundError(f"Frozen certificate file not found: {CERTIFICATE_PATH}")

    target_cert = None
    all_certs = []
    with open(CERTIFICATE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            cert = json.loads(line)
            all_certs.append(cert)
            if cert.get("candidate_id") == candidate_id:
                target_cert = cert

    if not target_cert:
        raise ValueError(f"Candidate {candidate_id} not found in frozen certificates.")

    # Verify SHA-256 against manifest
    with open(FREEZE_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    serialized = json.dumps(all_certs, sort_keys=True)
    computed_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    expected_hash = manifest.get("prediction_work_certificates_hash")

    if computed_hash != expected_hash:
        raise ValueError(f"Integrity check failed! Computed: {computed_hash}, Expected: {expected_hash}")

    return {
        "certificate": target_cert,
        "integrity_verified": True,
        "manifest_hash": computed_hash,
        "custody_status": "SEALED_INTACT"
    }
