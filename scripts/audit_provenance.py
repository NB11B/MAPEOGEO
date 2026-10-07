import json
from pathlib import Path

manifest = json.load(open("artifacts/releases/V2_PROVENANCE_MANIFEST.json"))
prov_dir = Path("docs/provenance/components")

audit = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "MAPEOGEO v2 Provenance Reconciliation Audit",
    "canonical_version": "v2.0.0-rc2-candidate",
    "audit_status": "PASS",
    "total_components": len(manifest["components"]),
    "disposition_summary": {
        "native_v2_modules": [
            "src/mapeogeo/__init__.py",
            "src/mapeogeo/domains/__init__.py",
        ],
        "ported_with_provenance_components": len(manifest["components"]),
    },
    "components": [],
    "failures": [],
}

all_src_files = {p.as_posix().replace("\\", "/") for p in Path("src").rglob("*.py")}
claimed_files = set(audit["disposition_summary"]["native_v2_modules"])

for c in manifest["components"]:
    cid = c["component_id"]
    status = c["v2_qualification_status"]
    comp_audit = {
        "component_id": cid,
        "target_module": c["target_module"],
        "source_repository": c["source_repository"],
        "source_branch": c["source_branch"],
        "source_commit": c["source_commit"],
        "port_strategy": c.get("port_strategy", "EXTRACT_CANONICAL"),
        "historical_qualification": c["source_qualification_status"],
        "v2_qualification": status,
        "target_files_count": len(c["target_files"]),
        "disposition": "ported-with-provenance",
    }

    if status != "QUALIFIED_CANONICAL_V2":
        audit["failures"].append(f"{cid}: status is {status}, expected QUALIFIED_CANONICAL_V2")
        audit["audit_status"] = "FAIL"

    for tf in c["target_files"]:
        normalized_tf = tf.replace("\\", "/")
        claimed_files.add(normalized_tf)
        if not Path(normalized_tf).is_file():
            audit["failures"].append(f"{cid}: target file does not exist: {tf}")
            audit["audit_status"] = "FAIL"

    audit["components"].append(comp_audit)

orphan_code = all_src_files - claimed_files
audit["orphan_code_detected"] = sorted(orphan_code)
if orphan_code:
    audit["failures"].append(f"Orphan production code detected: {orphan_code}")
    audit["audit_status"] = "FAIL"

print("Provenance Audit Status:", audit["audit_status"])
print("Failures:", audit["failures"])
print("Total audited source files:", len(claimed_files))

Path("artifacts/releases/V2_PROVENANCE_AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n")
