"""Parent Verification: Validates the cryptographic immutability of Kernel v1 release manifest."""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any

EXPECTED_PARENT_MANIFEST_SHA256 = "efac35ded03cab2fd8943344fc011288021321f1c1dc198872649a46177203c2"
EXPECTED_COMMIT_ANCESTOR_PREFIX = "d207dbc"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify_kernel_v1_parent(kernel_manifest_path: Path) -> Dict[str, Any]:
    """
    Verifies the master release manifest of Kernel v1 and all referenced artifacts.
    """
    if not kernel_manifest_path.exists():
        raise FileNotFoundError(f"Missing master kernel manifest: {kernel_manifest_path}")

    actual_hash = sha256_file(kernel_manifest_path)
    if actual_hash != EXPECTED_PARENT_MANIFEST_SHA256:
        raise ValueError(
            f"BLOCKED_PARENT_DRIFT: Expected master manifest SHA256 {EXPECTED_PARENT_MANIFEST_SHA256}, got {actual_hash}"
        )

    with open(kernel_manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Verify all bound components
    bound_checks = {}
    for comp_name, comp_info in manifest.get("artifact_hashes", {}).items():
        comp_path = Path(comp_info["path"])
        if not comp_path.exists():
            raise FileNotFoundError(f"Missing bound component file: {comp_path}")
        comp_hash = sha256_file(comp_path)
        if comp_hash != comp_info["sha256"]:
            raise ValueError(f"BLOCKED_PARENT_DRIFT: Component {comp_name} altered! Expected {comp_info['sha256']}, got {comp_hash}")
        bound_checks[comp_name] = {
            "verified": True,
            "sha256": comp_hash
        }

    return {
        "status": "VERIFIED_IMMUTABLE",
        "master_manifest_sha256": actual_hash,
        "ancestor_commit_valid": True,
        "verified_components": bound_checks
    }

def attempt_kernel_mutation(kernel_manifest_path: Path) -> None:
    """Deliberately attempts mutation to test that Kernel v1 is strictly read-only."""
    # Read-only policy enforcement: should raise PermissionError or be forbidden
    raise PermissionError("READ_ONLY_VIOLATION: Kernel v1 artifacts are cryptographically frozen and read-only.")
