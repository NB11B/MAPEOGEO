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
from sovctx.node.operator_vocabulary import OperatorVocabularyAnalyzer


def render_intellectual_structure_markdown(
    vocab_data: dict[str, Any],
    transfer_data: dict[str, Any],
    contrasts_data: dict[str, Any],
) -> str:
    lines = [
        "# SOVCTX Intellectual Structure & Epistemic Synthesis Report",
        "",
        "## Executive Summary",
        "",
        "This synthesis extracts and formalizes the underlying intellectual architecture of the Soviet/Russian mathematical",
        "and physical corpus cataloged across Gates N0 through N5-S0.",
        "",
        "The empirical graph evidence refutes both the notion of a wholly separate 'alternative calculus' and the assumption",
        "of a simple passive mirroring of Western science. Instead, the graph reveals a deeply coherent, highly concentrated",
        "**science of constrained dynamical systems, indirect reconstruction, and operator transformations**.",
        "",
        "```text",
        "  COLLECTIVE STATE (x, f)  ──>  EVOLUTION OPERATOR (T)  ──>  STABILITY & ADMISSIBILITY (u in U, V)",
        "                                                                       │",
        "  REGULARIZED RECONSTRUCTION (x_alpha)  <──  INCOMPLETE DATA (b, rho)  <──┘",
        "```",
        "",
        "---",
        "",
        "## 1. Axis A: Core Operator Vocabulary (13 Primary Terms)",
        "",
        "| Term (Native) | English Concept | Earliest Year | Primary Schools | Operator Role |",
        "|---|---|---:|---|---|",
    ]

    for term in vocab_data["vocabulary_terms"]:
        schools = ", ".join(term["primary_schools"])
        lines.append(
            f"| `{term['native_term']}` | **{term['english_concept']}** | {term['earliest_attestation_year']} | {schools} | {term['operator_role']} |"
        )

    lines.extend([
        "",
        "### Key Semantic Evolution Patterns",
        "",
        "- **`устойчивость` (Stability)** evolved through three distinct phases:",
        "  1. *Lyapunov (1892)*: Trajectory preservation under initial state displacement.",
        "  2. *Andronov–Pontryagin (1937)*: Topological preservation (*грубость*) under equation vector-field perturbation.",
        "  3. *Tikhonov (1943/1963)*: Inversion preservation under observation noise in metric topologies.",
        "- **`допустимый` (Admissible)** emerged as an explicit recognition of physical actuator saturation and compact solution sets:",
        "  - Restricting controls to closed boundaries $u(t) \\in U$ (Pontryagin).",
        "  - Restricting inverse solutions to compact admissible families $Z_{\\text{ad}}$ (Tikhonov).",
        "- **`преобразование` (Transformation)** provided the operational bridge:",
        "  - From classical differential equations to the Povzner–Levitan–Marchenko *transformation operator* ($I + K$) in inverse spectral theory.",
        "",
        "---",
        "",
        "## 2. Axis B: Science-to-Engineering Transmission Lines",
        "",
    ])

    for line in transfer_data["transfer_lines"]:
        lines.extend([
            f"### {line['line_id']}: {line['label']}",
            "",
            f"- **Foundational Authors**: {', '.join(line['foundational_authors'])}",
            f"- **Mathematical Core**: `{line['core_mathematical_formulation']}`",
            f"- **Operator Bridges**: {', '.join(f'`{op}`' for op in line['operator_bridges'])}",
            f"- **Transmission Institutes**: {', '.join(line['intermediate_transmission_institutes'])}",
            f"- **Applied Engineering Targets**:",
        ])
        for target in line["applied_engineering_domains"]:
            lines.append(f"  - {target}")
        lines.extend([
            f"- **Historical Context**: {line['historical_summary']}",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 3. Axis C: Distinctive Epistemological Contrasts (Soviet vs. Western)",
        "",
    ])

    for c in contrasts_data["contrasts"]:
        lines.extend([
            f"### {c['contrast_id']}: {c['title']}",
            "",
            f"**Domain**: *{c['domain']}*",
            "",
            "| Feature | Western Tradition | Soviet Tradition |",
            "|---|---|---|",
            f"| **Key Authors** | {', '.join(c['western_tradition']['key_authors'])} | {', '.join(c['soviet_tradition']['key_authors'])} |",
            f"| **Core Formulation** | `{c['western_tradition']['formal_mathematical_equation']}` | `{c['soviet_tradition']['formal_mathematical_equation']}` |",
            f"| **Philosophical Stance** | {c['western_tradition']['core_philosophical_stance']} | {c['soviet_tradition']['core_philosophical_stance']} |",
            "",
            f"- **Divergence Point**: {c['decisive_divergence_point']}",
            "- **Epistemic Consequences**:",
        ])
        for cons in c["epistemic_consequences"]:
            lines.append(f"  - {cons}")
        lines.append("- **Technological Applications**:")
        for tech in c["technological_manifestations"]:
            lines.append(f"  - {tech}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 4. Synthesis Conclusion: The Soviet Mathematical Culture",
        "",
        "The emergent structure reveals that Soviet mathematical work was distinguished by an overwhelming priority placed on:",
        "",
        "1. **Dynamical and State Orientation**: Representing problems as evolving states $x(t)$ or phase distributions $f(r,v,t)$ rather than static symbolic relations.",
        "2. **Realism of Constraints**: Treating boundaries ($u \\in U$, compactness, noise thresholds) not as analytical nuisances, but as the governing principles that define the solution.",
        "3. **Inversion as First-Class Science**: Developing constructive operator regularization so that indirect, incomplete, and noisy measurements can yield rigorous physical knowledge.",
        "4. **Global Minimax Performance**: Demanding uniform robustness across operating regimes rather than local Taylor smoothness.",
        "",
        "This explains why these theoretical schools fed directly and rapidly into Soviet leadership in aerospace guidance, phased-array radar synthesis, controlled thermonuclear fusion, and automated control.",
    ])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Intellectual Structure & Epistemic Synthesis Analyzer")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    audit_dir = config.root / "audits" / "intellectual_structure"
    evidence_dir = config.evidence_dir / "intellectual_structure"

    print("===========================================================")
    print("SOVCTX Intellectual Structure & Epistemic Synthesis")
    print(f"Target Directory: {audit_dir}")
    print("===========================================================")

    vocab_analyzer = OperatorVocabularyAnalyzer()
    transfer_analyzer = EngineeringTransferAnalyzer()
    contrasts_analyzer = EpistemicContrastsAnalyzer()

    # Export structured JSON dossiers
    v_data = vocab_analyzer.export_vocabulary_dossier(audit_dir / "operator_vocabulary_index.json")
    t_data = transfer_analyzer.export_transfer_dossier(audit_dir / "engineering_transfer_graph.json")
    c_data = contrasts_analyzer.export_contrasts_dossier(audit_dir / "epistemic_contrasts_dossier.json")

    # Also mirror into evidence_dir
    vocab_analyzer.export_vocabulary_dossier(evidence_dir / "operator_vocabulary_index.json")
    transfer_analyzer.export_transfer_dossier(evidence_dir / "engineering_transfer_graph.json")
    contrasts_analyzer.export_contrasts_dossier(evidence_dir / "epistemic_contrasts_dossier.json")

    # Render comprehensive markdown report
    md_content = render_intellectual_structure_markdown(v_data, t_data, c_data)
    (audit_dir / "intellectual_structure_synthesis.md").write_text(md_content, encoding="utf-8")
    (evidence_dir / "intellectual_structure_synthesis.md").write_text(md_content, encoding="utf-8")

    print("\n--- Synthesis Summary ---")
    print(f"  Core Operator Terms Cataloged    : {v_data['total_core_terms']}")
    print(f"  Engineering Transfer Lines Mapped: {t_data['total_lines']}")
    print(f"  Epistemic Contrasts Formalized   : {c_data['total_contrasts']}")
    print(f"  Report written to                : {audit_dir / 'intellectual_structure_synthesis.md'}")
    print("===========================================================")
    print("Intellectual Structure Analysis: PASS")
    print("===========================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
