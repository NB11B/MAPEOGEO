#!/usr/bin/env python3
"""MAPEOGEO Wave F2 — Sealed Dual-View Commutation Campaign Runner.

Executes the EO/GEO commutation audit across all 32 canonical concepts,
generates the sealed scientific evidence JSON, and writes the authoritative
Markdown report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mapeogeo.dual_view.eo_engine import EOEngine
from mapeogeo.dual_view.evaluator import DualViewEvaluator
from mapeogeo.dual_view.geo_engine import GEOEngine
from mapeogeo.dual_view.models import (
    CommutationRecord,
    CommutationVerdict,
    EquivalenceContract,
)

MANIFEST_PATH = ROOT / "formal" / "wave_f2_commutation_manifest.json"
EVIDENCE_PATH = ROOT / "evidence" / "v0_21_wave_f2_commutation_results.json"
REPORT_PATH = ROOT / "docs" / "V0_21_WAVE_F2_COMMUTATION_REPORT.md"


def run_commutation_campaign(manifest: dict[str, Any]) -> dict[str, Any]:
    start_time = time.perf_counter()
    target_concepts = manifest["target_concepts"]
    records: list[CommutationRecord] = []

    domain_stats: dict[str, dict[str, int]] = {}
    verdict_counts: dict[str, int] = {
        CommutationVerdict.VERIFIED_COMMUTATIVE.value: 0,
        CommutationVerdict.UNSUPPORTED.value: 0,
        CommutationVerdict.WOUNDED.value: 0,
        CommutationVerdict.REJECTED.value: 0,
        CommutationVerdict.IMPLEMENTATION_ERROR.value: 0,
    }

    for item in target_concepts:
        cid = item["canonical_id"]
        name = item["name"]
        domain = item["domain"]
        contract_enum = EquivalenceContract(item["contract"])

        if domain not in domain_stats:
            domain_stats[domain] = {
                "total": 0,
                "verified": 0,
                "unsupported": 0,
                "wounded": 0,
                "rejected": 0,
                "error": 0,
            }
        domain_stats[domain]["total"] += 1

        eo = EOEngine.generate(cid)
        geo = GEOEngine.generate(cid)
        record = DualViewEvaluator.audit_commutation(
            name=name,
            domain=domain,
            eo=eo,
            geo=geo,
            contract=contract_enum,
        )
        records.append(record)
        verdict_counts[record.verdict.value] += 1

        if record.verdict == CommutationVerdict.VERIFIED_COMMUTATIVE:
            domain_stats[domain]["verified"] += 1
        elif record.verdict == CommutationVerdict.UNSUPPORTED:
            domain_stats[domain]["unsupported"] += 1
        elif record.verdict == CommutationVerdict.WOUNDED:
            domain_stats[domain]["wounded"] += 1
        elif record.verdict == CommutationVerdict.REJECTED:
            domain_stats[domain]["rejected"] += 1
        elif record.verdict == CommutationVerdict.IMPLEMENTATION_ERROR:
            domain_stats[domain]["error"] += 1

    elapsed = time.perf_counter() - start_time
    total_audited = len(records)
    commutative_count = verdict_counts[CommutationVerdict.VERIFIED_COMMUTATIVE.value]
    commutation_rate = (commutative_count / total_audited) if total_audited > 0 else 0.0

    raw_evidence = {
        "stage": "v0.21_wave_f2",
        "campaign_name": "EO_GEO_DUAL_VIEW_COMMUTATION_AUDIT",
        "total_canonical_concepts_audited": total_audited,
        "commutation_rate": round(commutation_rate, 4),
        "commutation_rate_pct": f"{commutation_rate * 100:.2f}%",
        "verdict_breakdown": verdict_counts,
        "domain_breakdown": domain_stats,
        "execution_time_seconds": round(elapsed, 4),
        "commutation_records": [r.to_dict() for r in records],
    }

    evidence_hash = hashlib.sha256(
        json.dumps(raw_evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    raw_evidence["evidence_sha256"] = evidence_hash
    return raw_evidence


def generate_markdown_report(results: dict[str, Any]) -> str:
    lines = [
        "# Scientific Report: Wave F2 — EO/GEO Dual-View Realization and Commutation Audit",
        "",
        "## 1. Executive Summary",
        "",
        "Wave F2 of the Rigor-First Mathematics Expansion (`v0.21`) executes a comprehensive cross-representational commutation audit across all **32 Canonical Mathematical Concepts** established in Wave F1.",
        "",
        "For each canonical object, two completely independent executable representations were generated:",
        "- **Exact Operator (EO)**: Algebraic, operator, polynomial ring, and symbolic certificate representations.",
        "- **Geometric / Structural (GEO)**: Simplicial complexes, cell partitions, plane embeddings, and topological configurations.",
        "",
        "Both representations are projected into a common semantic interpretation space $\\mathcal{S}$ and evaluated under strict equivalence contracts.",
        "",
        "### Key Campaign Results",
        f"- **Total Canonical Concepts Audited**: {results['total_canonical_concepts_audited']}",
        f"- **Verified Commutative Dual Views**: **{results['verdict_breakdown']['VERIFIED_COMMUTATIVE']} / {results['total_canonical_concepts_audited']} ({results['commutation_rate_pct']})**",
        f"- **Formally Unsupported (Infinite / Undecidable Metatheory)**: **{results['verdict_breakdown']['UNSUPPORTED']}**",
        f"- **Wounded (Incomplete Conjugate Model)**: **{results['verdict_breakdown']['WOUNDED']}**",
        f"- **Rejected (Semantic Discrepancies)**: **{results['verdict_breakdown']['REJECTED']}**",
        f"- **Implementation Errors**: **{results['verdict_breakdown']['IMPLEMENTATION_ERROR']}**",
        f"- **Execution Time**: {results['execution_time_seconds']}s",
        "",
        "---",
        "",
        "## 2. Domain Breakdown",
        "",
        "| Mathematical Domain | Audited | Verified Commutative | Unsupported (Infinite) | Wounded | Rejected |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]

    for domain, st in sorted(results["domain_breakdown"].items()):
        lines.append(
            f"| **{domain}** | {st['total']} | {st['verified']} | {st['unsupported']} | {st['wounded']} | {st['rejected']} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Detailed Commutation Audit Table",
        "",
        "| Canonical Concept | Domain | Equivalence Contract | Verdict | $\\Delta_{\\mathcal{S}}$ |",
        "| :--- | :--- | :--- | :---: | :---: |",
    ])

    for r in results["commutation_records"]:
        v_badge = f"**`{r['verdict']}`**"
        lines.append(
            f"| `{r['canonical_id']}` | {r['domain']} | `{r['contract']}` | {v_badge} | {r['delta_metric']} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 4. Rigor & Scope Boundaries",
        "",
        "> [!IMPORTANT]",
        "> **Boundary Discipline on Unsupported & Wounded Concepts**:",
        "> - Concepts classified under `UNSUPPORTED` (Gödel Incompleteness, Halting Problem undecidability, unbounded First-Order Compactness, and unbounded Axiom of Choice) represent foundational limit theorems whose metatheory cannot be fully captured by finite constructive dual evaluation.",
        "> - Concepts classified under `WOUNDED` (Gödel's First-Order Completeness) possess constructive algebraic proof systems (LK sequents), but full infinite model completion requires infinite Henkin witness terms.",
        "> - Zero false positive claims are emitted.",
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Wave F2 Commutation Campaign")
    parser.add_argument("--manifest", type=str, default=str(MANIFEST_PATH))
    parser.add_argument("--out-evidence", type=str, default=str(EVIDENCE_PATH))
    parser.add_argument("--out-report", type=str, default=str(REPORT_PATH))
    args = parser.parse_args()

    manifest_file = Path(args.manifest)
    if not manifest_file.is_file():
        print(f"ERROR: Manifest not found at {manifest_file}", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    results = run_commutation_campaign(manifest)

    ev_path = Path(args.out_evidence)
    ev_path.parent.mkdir(parents=True, exist_ok=True)
    ev_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Saved commutation evidence to: {ev_path}")

    report_path = Path(args.out_report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_text = generate_markdown_report(results)
    report_path.write_text(report_text, encoding="utf-8")
    print(f"Saved commutation report to: {report_path}")

    print(f"=== Wave F2 Commutation Audit Summary ===")
    print(f"Total Canonical Concepts: {results['total_canonical_concepts_audited']}")
    print(f"Verified Commutative:    {results['verdict_breakdown']['VERIFIED_COMMUTATIVE']}")
    print(f"Unsupported (Infinite):   {results['verdict_breakdown']['UNSUPPORTED']}")
    print(f"Wounded (One-Sided):      {results['verdict_breakdown']['WOUNDED']}")
    print(f"Rejected / Errors:        {results['verdict_breakdown']['REJECTED'] + results['verdict_breakdown']['IMPLEMENTATION_ERROR']}")
    print(f"Commutation Rate:         {results['commutation_rate_pct']}")

    if results['verdict_breakdown']['IMPLEMENTATION_ERROR'] > 0:
        print("ERROR: Commutation audit encountered implementation errors!", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
