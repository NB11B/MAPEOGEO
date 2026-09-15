from __future__ import annotations

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence"

LEVELS = ("C0", "C1", "C2", "C3", "C4", "C5")
ALLOWED_STATES = {"PASS", "FAIL", "NOT_APPLICABLE", "NOT_ESTABLISHED", "INVALID", "ERROR"}
EXPECTED_SOURCE_ARTIFACT = {
    "commit_sha": "9420f19953f56198630f86eb25fa5d6eb0828ea7",
    "workflow_run_id": 34933361147,
    "artifact_id": 10382242654,
    "artifact_digest": "sha256:d487602dd3c0b3a3c5302edde108758eda2b11975f5e0c2c4e659db63da2aabc",
}


def load_real_component_manifest() -> dict:
    return json.loads((EVIDENCE / "pct_e25d_real_component_manifest.json").read_text(encoding="utf-8"))


def canonical_json(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_manifest(manifest: dict) -> dict:
    errors: list[str] = []
    if manifest.get("source_artifact") != EXPECTED_SOURCE_ARTIFACT:
        errors.append("SOURCE_ARTIFACT_MISMATCH")

    components = manifest.get("components")
    if not isinstance(components, list):
        return {"status": "FAIL", "errors": ["COMPONENTS_NOT_LIST"]}

    ids = [c.get("component_id") for c in components if isinstance(c, dict)]
    if len(ids) != len(components) or len(ids) != len(set(ids)):
        errors.append("DUPLICATE_OR_MISSING_COMPONENT_ID")

    contracts = []
    required = {
        "component_id", "provenance_class", "contract", "anchor_id", "eo_id", "geo_id",
        "formal_id", "formal_scope", "source_statement_sha256", "source_hashes",
        "certificate_ids", "certificates", "semantic_edge_ids", "semantic_edges",
        "applicability", "applicability_reasons", "evidence_refs",
    }
    for component in components:
        if not isinstance(component, dict):
            errors.append("COMPONENT_NOT_OBJECT")
            continue
        missing = sorted(required - set(component))
        if missing:
            errors.append(f"MISSING_FIELDS:{component.get('component_id')}:{','.join(missing)}")
            continue
        if component["provenance_class"] != "REAL_SOURCE_BOUND":
            errors.append(f"NON_REAL_COMPONENT:{component['component_id']}")
        contracts.append(component["contract"])
        h = component["source_statement_sha256"]
        if not _is_sha256(h):
            errors.append(f"INVALID_SOURCE_HASH:{component['component_id']}")
        hashes = component["source_hashes"]
        if set(hashes) != {"anchor", "eo", "geo", "formal"} or set(hashes.values()) != {h}:
            errors.append(f"SOURCE_HASH_DIVERGENCE:{component['component_id']}")
        if len(component["certificate_ids"]) != 2 or set(component["certificate_ids"]) != set(component["certificates"]):
            errors.append(f"CERTIFICATE_BINDING_ERROR:{component['component_id']}")
        for cert_id, cert in component["certificates"].items():
            if cert.get("status") != "PASS" or cert.get("source_statement_sha256") != h:
                errors.append(f"CERTIFICATE_INVALID:{component['component_id']}:{cert_id}")
        if len(component["semantic_edge_ids"]) != len(set(component["semantic_edge_ids"])):
            errors.append(f"DUPLICATE_EDGE_ID:{component['component_id']}")
        edge_ids = [e.get("id") for e in component["semantic_edges"]]
        if edge_ids != component["semantic_edge_ids"]:
            errors.append(f"EDGE_INDEX_MISMATCH:{component['component_id']}")
        if set(component["applicability"]) != set(LEVELS):
            errors.append(f"APPLICABILITY_MASK_INCOMPLETE:{component['component_id']}")

    if set(contracts) != {"rank", "convex", "lp", "gauss"} or len(contracts) != 4:
        errors.append("REAL_CONTRACT_SET_MISMATCH")
    if errors:
        return {"status": "FAIL", "errors": errors}
    return {"status": "PASS", "components": len(components)}
