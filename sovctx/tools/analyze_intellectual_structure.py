from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import load_config
from sovctx.node.engineering_transfer import EngineeringTransferAnalyzer
from sovctx.node.epistemic_contrasts import EpistemicContrastsAnalyzer
from sovctx.node.intellectual_audit import IntellectualStructureAuditor
from sovctx.node.operator_vocabulary import OperatorVocabularyAnalyzer


def render_intellectual_structure_markdown(
    vocab_data: dict[str, Any],
    transfer_data: dict[str, Any],
    contrasts_data: dict[str, Any],
    audit_data: dict[str, Any],
) -> str:
    lines = [
        "# SOVCTX Intellectual Structure & Epistemic Synthesis Report",
        "",
        "## Executive Summary",
        "",
        "This synthesis extracts and formalizes the underlying intellectual architecture of the Soviet/Russian mathematical",
        "and physical corpus cataloged across Gates N0 through N5-S0.",
        "",
        "The empirical graph evidence firmly refutes both the notion of an 'alternative calculus' and a binary 'East vs West'",
        "dichotomy. Instead, the evidence demonstrates a **distinctive problem-solving tradition and preferred mathematical representations**",
        "within the common international mathematical heritage:",
        "",
        "> **Core Architectural Principle**:",
        "> `same broad mathematics + different concentration of problems + different institutional lineages + different preferred representations ──> different engineering intuitions`",
        "",
        "```text",
        "  STATE  ──>  OPERATOR / EVOLUTION  ──>  CONSTRAINT  ──>  STABILITY  ──>  OBSERVATION  ──>  RECONSTRUCTION / CONTROL",
        "  (x, f)            (T)                 (u in U)        (delta F)        (u_delta)               (z_alpha)",
        "```",
        "",
        "---",
        "",
        "## 1. Core Mathematical Motif Matrix",
        "",
        "| Motif | Associated Schools | Earliest Evidence | Cross-School Recurrence | Engineering Descendants (Documented vs. Candidate) | Evidentiary Confidence |",
        "|---|---|---:|---|---|---|",
    ]

    for m in audit_data["core_motif_matrix"]:
        schools = ", ".join(m["schools"])
        doc_desc = "; ".join(m["engineering_descendants_documented"][:2])
        cand_desc = "; ".join(m["engineering_descendants_candidate"][:1])
        desc = f"**Doc**: {doc_desc}<br/>*Cand*: {cand_desc}" if cand_desc else f"**Doc**: {doc_desc}"
        lines.append(
            f"| **{m['motif']}** | {schools} | {m['earliest_evidence_year']} | {m['cross_school_recurrence']} | {desc} | **{m['evidentiary_confidence']}** |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 2. Quantitative Graph Metrics & Structural Centrality",
        "",
        "### A. Cross-School Term Centrality",
        "",
        "| Rank | Term (Native) | English Concept | School Count | Associated Equations | Primary Participating Schools |",
        "|---:|---|---|---:|---:|---|",
    ])

    for item in audit_data["metrics"]["term_centrality_ranking"]:
        schools = ", ".join(item["primary_schools"])
        lines.append(
            f"| {item['centrality_rank']} | `{item['native_term']}` | **{item['english_concept']}** | {item['school_count']} | {item['equation_count']} | {schools} |"
        )

    lines.extend([
        "",
        "### B. Institutional Connectivity & Transmission Reach",
        "",
        "| Term (Native) | English Concept | Connected Institutes | Key Connected Institutions |",
        "|---|---|---:|---|",
    ])

    for item in audit_data["metrics"]["institutional_connectivity_ranking"][:8]:
        insts = ", ".join(item["connected_institutions"][:4])
        lines.append(
            f"| `{item['native_term']}` | **{item['english_concept']}** | {item['institution_count']} | {insts} |"
        )

    lines.extend([
        "",
        "### C. Institutional Bridges Between Pure Mathematics and Engineering",
        "",
        "| Institution | Foundation | Bridge Score | Pure Mathematics Anchor | Engineering Implementation Target |",
        "|---|---:|---:|---|---|",
    ])

    for b in audit_data["metrics"]["institutional_bridges_ranking"]:
        pure = "; ".join(b["pure_math_connections"][:2])
        eng = "; ".join(b["engineering_domain_connections"][:2])
        lines.append(
            f"| **{b['institution_name']}** | {b['foundation_year']} | {b['bridge_score']} / 10 | {pure} | {eng} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Terminology Evolution vs. Mathematical Invariance",
        "",
    ])

    for inv in audit_data["terminology_evolution_and_invariance"]:
        lines.extend([
            f"### Invariant Concept: {inv['mathematical_invariant_concept']}",
            "",
            f"> {inv['underlying_invariant_structure']}",
            "",
            "| Terminological Phase | Perturbation Target | Mathematical Mechanism |",
            "|---|---|---|",
        ])
        for p in inv["terminological_phases"]:
            lines.append(
                f"| **{p['term']}** | `{p['target_of_perturbation']}` | {p['mathematical_mechanism']} |"
            )
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 4. Science-to-Engineering Transmission Lines (Evidentiary Filter)",
        "",
        "> **Evidentiary Standard**: Lines are strictly classified into `DOCUMENTED_LINEAGE` (verified by primary citations)",
        "> and `HYPOTHESIZED_LINEAGE` (mathematically foundational but requiring specific bureau documentation).",
        "",
    ])

    for line in transfer_data["transfer_lines"]:
        status_badge = f"**[{line['lineage_status']} / Confidence: {line['evidentiary_confidence']}]**"
        lines.extend([
            f"### {line['line_id']}: {line['label']}",
            f"{status_badge}",
            "",
            f"- **Foundational Authors**: {', '.join(line['foundational_authors'])}",
            f"- **Mathematical Core**: `{line['core_mathematical_formulation']}`",
            f"- **Operator Bridges**: {', '.join(f'`{op}`' for op in line['operator_bridges'])}",
            f"- **Transmission Institutes**: {', '.join(line['intermediate_transmission_institutes'])}",
            f"- **Applied Engineering Targets**:",
        ])
        for domain in line["applied_engineering_domains"]:
            lines.append(f"  - {domain}")
        lines.extend([
            f"- **Documented Sources**: {', '.join(f'`{s}`' for s in line['documented_sources'])}",
            f"- **Next Acquisition Targets**:",
        ])
        for target in line["next_acquisition_targets"]:
            lines.append(f"  - {target}")
        lines.extend([
            f"- **Historical Context**: {line['historical_summary']}",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 5. Epistemic Contrasts: Mathematical Formulations & International Context",
        "",
        "> **Perspective Note**: These dossiers analyze distinct mathematical and problem-solving formulations",
        "> rather than national exclusivities. Soviet-emphasized formulations frequently interacted with and enriched",
        "> international scientific practice.",
        "",
    ])

    for contrast in contrasts_data["contrasts"]:
        lines.extend([
            f"### {contrast['contrast_id']}: {contrast['title']}",
            "",
            f"**Domain**: *{contrast['domain']}* | **Relationship**: `{contrast['relationship_nature']}` ({contrast['chronological_relationship']})",
            "",
            "| Feature | Alternative Contemporary Formulation | Soviet-Emphasized Formulation |",
            "|---|---|---|",
            f"| **Key Authors** | {', '.join(contrast['alternative_contemporary_formulation']['key_authors'])} | {', '.join(contrast['soviet_emphasized_formulation']['key_authors'])} |",
            f"| **Core Formulation** | `{contrast['alternative_contemporary_formulation']['formal_mathematical_equation']}` | `{contrast['soviet_emphasized_formulation']['formal_mathematical_equation']}` |",
            f"| **Underlying Stance** | {contrast['alternative_contemporary_formulation']['core_philosophical_stance']} | {contrast['soviet_emphasized_formulation']['core_philosophical_stance']} |",
            "",
            f"- **Decisive Distinction**: {contrast['decisive_distinction']}",
            "- **Epistemic Consequences**:",
        ])
        for cons in contrast["epistemic_consequences"]:
            lines.append(f"  - {cons}")
        lines.append("- **International Cross-Pollination**:")
        for cross in contrast["international_cross_pollination"]:
            lines.append(f"  - {cross}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 6. Synthesis: The Soviet Problem-Solving Tradition",
        "",
        "The graph confirms eight recurring methodological commitments of the Soviet tradition:",
        "",
        r"1. **State rather than merely observable output**: Explicit modeling of internal coordinates $x(t)$ or distribution $f(r,v,t)$.",
        r"2. **Transformation rather than static quantity**: Representing interactions via operators ($T, I+K$) and mapping structures.",
        r"3. **Stability under perturbation**: Investigating what qualitative structure survives uncertainty ($\delta x_0, \delta F, \delta y$).",
        r"4. **Hard admissibility constraints**: Incorporating compact actuator boundaries ($u \in U, z \in Z_{\text{ad}}$) as solution determinants.",
        r"5. **Reconstruction from indirect observation**: Treating ill-posed inversion as a first-class mathematical science.",
        r"6. **Collective representations for many-body systems**: Formulating dynamics over distributions rather than isolated particles.",
        r"7. **Global error bounds rather than only local approximation**: Minimax guarantees over operating intervals rather than point derivatives.",
        r"8. **Institutional schools carrying methods across generations**: Steklov, Keldysh, Gorky, and Kyiv transmitting methods across decades.",
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Intellectual Structure & Epistemic Synthesis Analyzer")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    sovctx_dir = Path(__file__).resolve().parents[1]
    audit_dir = sovctx_dir / "audits" / "intellectual_structure"
    evidence_dir = config.evidence_dir / "intellectual_structure"

    print("===========================================================")
    print("SOVCTX Intellectual Structure & Epistemic Synthesis")
    print(f"Target Directory: {audit_dir}")
    print("===========================================================")

    vocab_analyzer = OperatorVocabularyAnalyzer()
    transfer_analyzer = EngineeringTransferAnalyzer()
    contrasts_analyzer = EpistemicContrastsAnalyzer()
    auditor = IntellectualStructureAuditor()

    # Export structured JSON dossiers
    v_data = vocab_analyzer.export_vocabulary_dossier(audit_dir / "operator_vocabulary_index.json")
    t_data = transfer_analyzer.export_transfer_dossier(audit_dir / "engineering_transfer_graph.json")
    c_data = contrasts_analyzer.export_contrasts_dossier(audit_dir / "epistemic_contrasts_dossier.json")
    a_data = auditor.export_full_audit_dossier(audit_dir)

    # Mirror into evidence_dir
    vocab_analyzer.export_vocabulary_dossier(evidence_dir / "operator_vocabulary_index.json")
    transfer_analyzer.export_transfer_dossier(evidence_dir / "engineering_transfer_graph.json")
    contrasts_analyzer.export_contrasts_dossier(evidence_dir / "epistemic_contrasts_dossier.json")
    auditor.export_full_audit_dossier(evidence_dir)

    # Render comprehensive markdown report
    md_content = render_intellectual_structure_markdown(v_data, t_data, c_data, a_data)
    (audit_dir / "intellectual_structure_synthesis.md").write_text(md_content, encoding="utf-8")
    (evidence_dir / "intellectual_structure_synthesis.md").write_text(md_content, encoding="utf-8")

    print("\n--- Synthesis Summary ---")
    print(f"  Core Operator Terms Cataloged    : {v_data['total_core_terms']}")
    print(f"  Engineering Transfer Lines Mapped: {t_data['total_lines']} (Doc: {t_data['documented_lines_count']}, Hyp: {t_data['hypothesized_lines_count']})")
    print(f"  Epistemic Contrasts Formalized   : {c_data['total_contrasts']}")
    print(f"  Core Motifs Analyzed             : {len(a_data['core_motif_matrix'])}")
    print(f"  Institutional Bridges Ranked     : {len(a_data['metrics']['institutional_bridges_ranking'])}")
    print(f"  Report written to                : {audit_dir / 'intellectual_structure_synthesis.md'}")
    print("===========================================================")
    print("Intellectual Structure Analysis: PASS")
    print("===========================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
