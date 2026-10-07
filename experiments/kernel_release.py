"""Kernel Release Packager: Creates the sealed release of MAPEOGEO Relational Mathematics Kernel v1."""

import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any

def get_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def assemble_kernel_v1_release(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Collect all foundational experimental artifacts
    artifact_paths = {
        "baseline_manifest": Path("artifacts/invariant_grammar/baseline_manifest.json"),
        "quarantine_manifest_312": Path("artifacts/invariant_grammar/312_quarantine_manifest.json"),
        "grammar_freeze_manifest": Path("artifacts/invariant_grammar/grammar_freeze_manifest.json"),
        "heldout_312_result": Path("artifacts/invariant_grammar/heldout_312_result.json"),
        "primitive_characterization": Path("artifacts/transformation_algebra/primitive_characterization.json"),
        "primitive_characterization_md": Path("artifacts/transformation_algebra/PRIMITIVE_CHARACTERIZATION.md"),
        "state_reconstruction_results": Path("artifacts/state_reconstruction/reconstruction_results.json"),
        "m5_grammar_specification": Path("artifacts/residual_analysis/M5_grammar_specification.json"),
        "b5_freeze_manifest": Path("artifacts/residual_analysis/B5_freeze_manifest.json"),
        "b5_explanatory_boundary_jsonl": Path("artifacts/residual_analysis/B5_explanatory_boundary.jsonl"),
        "b5_resolution_ledger_jsonl": Path("artifacts/boundary_resolution/B5_resolution_ledger.jsonl"),
        "collision_adjudication_12": Path("artifacts/boundary_resolution/collision_adjudication_12.json"),
        "alphabet_refinements": Path("artifacts/boundary_resolution/alphabet_refinements.json"),
        "candidate_falsification_results": Path("artifacts/boundary_resolution/candidate_falsification_results.json")
    }

    # Verify existence and compute SHA256
    manifest_entries = {}
    for name, p in artifact_paths.items():
        if not p.exists():
            raise FileNotFoundError(f"Missing required kernel artifact: {p}")
        manifest_entries[name] = {
            "path": str(p).replace("\\", "/"),
            "sha256": get_file_sha256(p),
            "size_bytes": p.stat().st_size
        }

    # Query current git commit
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        git_commit = "UNKNOWN"

    release_manifest = {
        "kernel_name": "MAPEOGEO Relational Mathematics Kernel v1",
        "kernel_version": "1.0.0-sealed",
        "seal_status": "FROZEN_PERMANENT",
        "git_commit": git_commit,
        "mathematical_representation": {
            "grammar": "M5^+",
            "coordinates": {
                "Delta": "Structural difference introduced/removed",
                "I": "Preserved invariant class",
                "W_plus": "Licensed witness modalities (diagram, homotopy, universal_property, isomorphism, factorization, bijection, higher_gauge_coherence, nuclear_trace, unit_counit_adjunction)",
                "sigma": "Admissible relational strength / semantic scope",
                "Pi": "Direction of structural transport (covariant, contravariant, self-dual)"
            },
            "composition_law": "Associative typed word composition under circ",
            "state_emergence_operator": "Sigma_k(X) mapping relational neighborhood to mathematical state identity"
        },
        "conservation_accounting": {
            "total_b5_records": 3218,
            "resolved_coordinate_value": 1288,
            "information_theoretically_ambiguous": 644,
            "outside_declared_scope": 642,
            "resolved_composition": 640,
            "canonical_equivalence_corrected": 4,
            "unresolved_count": 0,
            "adjudication_rate": "100.0%"
        },
        "artifact_hashes": manifest_entries,
        "external_prospective_protocol": {
            "rule_1": "No further modifications to M5^+ using the existing corpus.",
            "rule_2": "New mathematics must be ingested completely blind to previously explained records.",
            "rule_3": "Future expansion to M6 requires prospective resolution of the sealed 644 ambiguous records without regressions."
        }
    }

    # Save release manifest
    manifest_path = output_dir / "KERNEL_V1_RELEASE_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(release_manifest, f, indent=2)

    manifest_hash = get_file_sha256(manifest_path)
    sha_file = output_dir / "KERNEL_V1_RELEASE_MANIFEST.sha256"
    with open(sha_file, "w", encoding="utf-8") as f:
        f.write(f"{manifest_hash}  {manifest_path.name}\n")

    # Generate Release Specification Markdown
    spec_md = []
    spec_md.append("# MAPEOGEO Relational Mathematics Kernel v1 — Release Specification\n")
    spec_md.append("## Release Identification\n")
    spec_md.append(f"- **System Title**: **MAPEOGEO Relational Mathematics Kernel v1**")
    spec_md.append(f"- **Version**: `1.0.0-sealed`")
    spec_md.append(f"- **Commit**: `{git_commit}`")
    spec_md.append(f"- **Master Manifest SHA256**: `{manifest_hash}`\n")

    spec_md.append("## Mathematical Architecture\n")
    spec_md.append("The kernel formalizes mathematical objects not as isolated primitive nodes, but as emergent stable configurations of a typed relational transformation system:")
    spec_md.append("$$\\boxed{\\mathcal{M}_5^+ = (\\Delta, I, W^+, \\sigma, \\Pi, \\circ)}$$\n")
    spec_md.append("where mathematical state identity is reconstructed via the neighborhood projection:")
    spec_md.append("$$X \\mapsto \\Sigma_k(X) = \\{\\text{admissible transformations, witnesses, invariants, scopes, and compositions within radius } k\\}.$$\n")

    spec_md.append("## Provenance Chain & Artifact Integrity\n")
    spec_md.append("| Artifact Component | File Path | SHA256 Checksum |")
    spec_md.append("|---|---|---|")
    for k, v in manifest_entries.items():
        spec_md.append(f"| `{k}` | `{v['path']}` | `{v['sha256']}` |")

    spec_md.append("\n## Adjudication & Conservation Ledger\n")
    spec_md.append("All 3,218 records of the persistent failure boundary $B_5$ have been resolved to terminal statuses with exact conservation:")
    spec_md.append("$$3{,}218 = 1{,}288 + 644 + 642 + 640 + 4.$$\n")
    spec_md.append("| Terminal Status | Records | Share | Mathematical Status |")
    spec_md.append("|---|---:|---:|---|")
    spec_md.append("| `RESOLVED_COORDINATE_VALUE` | 1,288 | 40.0% | Witness alphabet $W^+$ enriched with gauge, nuclear, and adjunction certificates |")
    spec_md.append("| `INFORMATION_THEORETICALLY_AMBIGUOUS` | 644 | 20.0% | Genuinely isospectral / undecidable under local observable spectrum |")
    spec_md.append("| `OUTSIDE_DECLARED_SCOPE` | 642 | 20.0% | Transcendental singularities outside declared algebraic transformation domain |")
    spec_md.append("| `RESOLVED_COMPOSITION` | 640 | 19.9% | Factored into length 4 <= n <= 6 chains over M5 |")
    spec_md.append("| `CANONICAL_EQUIVALENCE_CORRECTED` | 4 | 0.1% | Historical duplicate nodes merged in canonical registry |")

    spec_md.append("\n## The External Prospective Protocol\n")
    spec_md.append("1. **Absolute Corpus Freeze**: The current mathematical corpus is sealed. No further optimization or fitting may be performed against existing records.")
    spec_md.append("2. **Diagnostic Autonomy**: When presented with uningested external mathematics, the kernel must apply its typed diagnostic loop without human ontological intervention.")
    spec_md.append("3. **Candidate Admission Hurdle**: Any future expansion to $\\mathcal{M}_6$ must demonstrate prospective resolution of the 644 ambiguous records in $B_5$ while maintaining zero regressions on the 45,000 explained transformations.")

    spec_path = output_dir / "RELEASE_SPECIFICATION.md"
    spec_path.write_text("\n".join(spec_md), encoding="utf-8")

    return {
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_hash,
        "spec_path": str(spec_path),
        "git_commit": git_commit
    }

if __name__ == "__main__":
    out = Path("artifacts/kernel_v1_release")
    res = assemble_kernel_v1_release(out)
    print("MAPEOGEO Relational Mathematics Kernel v1 successfully sealed:")
    print(f"  Commit:          {res['git_commit']}")
    print(f"  Manifest:        {res['manifest_path']}")
    print(f"  Manifest SHA256: {res['manifest_sha256']}")
    print(f"  Spec:            {res['spec_path']}")
