from __future__ import annotations

from pathlib import Path
import hashlib
import json

from .morphisms import canonical_json


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence"


def _load_json(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def _adapter_digest() -> str:
    payload = Path(__file__).with_name("morphisms.py").read_bytes()
    return hashlib.sha256(payload).hexdigest()


def build_provenance_record(component: dict, adapter_id: str, adapter_sha256: str, source_artifact: dict) -> dict:
    return {
        "component_id": component["component_id"],
        "source_statement_sha256": component["source_statement_sha256"],
        "contract": component["contract"],
        "formal_scope": component["formal_scope"],
        "source_artifact_digest": source_artifact["artifact_digest"],
        "source_commit_sha": source_artifact["commit_sha"],
        "eo_id": component["eo_id"],
        "geo_id": component["geo_id"],
        "formal_id": component["formal_id"],
        "certificate_ids": sorted(component["certificate_ids"]),
        "adapter_id": adapter_id,
        "adapter_sha256": adapter_sha256,
        "predecessor_evidence_ids": sorted({
            "evidence/pct_e25_graph_consistency_audit.json",
            "evidence/pct_e25c_executable_cycle_audit.json",
            "evidence/pct_e25d_real_component_manifest.json",
            "evidence/pct_e25d_closure_atlas.json",
            *component.get("evidence_refs", []),
        }),
    }


def _component_binding_valid(component: dict, source_artifact: dict) -> tuple[bool, list[str]]:
    problems: list[str] = []
    source_hash = component.get("source_statement_sha256")
    if component.get("provenance_class") != "REAL_SOURCE_BOUND":
        problems.append("NOT_REAL_SOURCE_BOUND")
    if not source_hash or len(source_hash) != 64:
        problems.append("MISSING_SOURCE_HASH")
    source_hashes = component.get("source_hashes", {})
    if not source_hashes or set(source_hashes.values()) != {source_hash}:
        problems.append("SOURCE_HASH_DIVERGENCE")
    if not component.get("formal_scope"):
        problems.append("MISSING_FORMAL_SCOPE")
    if not component.get("certificate_ids"):
        problems.append("MISSING_CERTIFICATES")
    certificates = component.get("certificates", {})
    for cert_id in component.get("certificate_ids", []):
        cert = certificates.get(cert_id)
        if not cert or cert.get("status") != "PASS":
            problems.append(f"CERTIFICATE_NOT_PASS:{cert_id}")
            continue
        cert_hash = cert.get("source_statement_sha256")
        if cert_hash and cert_hash != source_hash:
            problems.append(f"CERTIFICATE_HASH_MISMATCH:{cert_id}")
        cert_scope = cert.get("formal_scope")
        if cert_scope and cert_scope != component.get("formal_scope"):
            problems.append(f"CERTIFICATE_SCOPE_MISMATCH:{cert_id}")
    for field in ("artifact_digest", "commit_sha"):
        if not source_artifact.get(field):
            problems.append(f"MISSING_SOURCE_ARTIFACT_{field.upper()}")
    return not problems, problems


def run_c5b_audit() -> dict:
    manifest = _load_json("pct_e25d_real_component_manifest.json")
    atlas = _load_json("pct_e25d_closure_atlas.json")
    source_artifact = atlas["source_artifact"]
    adapter_sha256 = _adapter_digest()
    components = []
    for component in sorted(manifest["components"], key=lambda c: c["component_id"]):
        adapter_id = f"pct_e25gh.{component['contract']}.c5a.v1"
        valid, problems = _component_binding_valid(component, source_artifact)
        record = build_provenance_record(component, adapter_id, adapter_sha256, source_artifact)
        provenance_sha256 = hashlib.sha256(canonical_json(record).encode("ascii")).hexdigest()
        components.append({
            **record,
            "provenance_sha256": provenance_sha256,
            "provenance_state": "PASS" if valid else "FAIL",
            "problems": problems,
        })
    status = "PASS" if len(components) == 4 and all(c["provenance_state"] == "PASS" for c in components) else "FAIL"
    return {
        "experiment_id": "E25G_C5B_PROVENANCE_BINDING_AUDIT",
        "status": status,
        "component_count": len(components),
        "components": components,
        "source_artifact": {
            "artifact_digest": source_artifact["artifact_digest"],
            "commit_sha": source_artifact["commit_sha"],
            "artifact_id": source_artifact.get("artifact_id"),
            "workflow_run_id": source_artifact.get("workflow_run_id"),
        },
        "claim_boundary": "C5b validates source, scope, certificate, representation, adapter, and predecessor-evidence binding for the four frozen REAL_SOURCE_BOUND components only.",
    }
