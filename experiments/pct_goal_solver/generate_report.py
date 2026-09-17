from __future__ import annotations

import argparse
import json
from pathlib import Path

from .campaign import MODE_NAMES, run_campaign


def _markdown(report: dict) -> str:
    lines = [
        "# PCT Goal-Directed Mixed-Domain Solver Campaign",
        "",
        f"**Scientific status:** {report['scientific_status']}",
        "",
        "This report evaluates the solver as a mathematical operator-search system. CI status and artifact hashes are not scientific gates.",
        "",
        "## Sealed mode results",
        "",
        "| Mode | Correct PASS | Wrong positives | Solved families | Multi-step families | Cross-class families | Mean states | Mean primitive executions |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in MODE_NAMES:
        mode = report["modes"][name]
        lines.append(
            f"| {name} | {mode['correct_pass_count']} | {mode['wrong_positive_count']} | "
            f"{mode['solved_family_count']} | {mode['multi_step_solved_family_count']} | "
            f"{mode['cross_class_solved_family_count']} | {mode['mean_expanded_states']:.2f} | "
            f"{mode['mean_primitive_executions']:.2f} |"
        )

    lines += ["", "## Preregistered gates", ""]
    for gate, passed in report["gates"].items():
        lines.append(f"- **{'PASS' if passed else 'FAIL'}** — `{gate}`")

    lines += ["", "## Scientific conclusions", ""]
    for name, payload in report["conclusions"].items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"**{payload['status']}**")
        lines.append("")
        if name == "GOAL_DIRECTED_SOLVING":
            lines.append(f"Solved families: {', '.join(payload['solved_families']) or 'none'}")
            lines.append(f"Wrong positives: {payload['wrong_positive_count']}")
        elif name == "INFERRED_COMPATIBILITY":
            coverage = payload["class_coverage"]
            lines.append(
                f"Correct sealed PASS cases by class: exact={coverage['EXACT']}, "
                f"symbolic={coverage['SYMBOLIC']}, numerical={coverage['NUMERICAL']}."
            )
            lines.append(f"Solved families: {', '.join(payload['solved_families']) or 'none'}")
            lines.append(f"Wrong positives: {payload['wrong_positive_count']}")
        elif name == "MIXED_DOMAIN_COMPOSITION":
            lines.append(f"Multi-step families: {', '.join(payload['multi_step_families']) or 'none'}")
            lines.append(f"Cross-class families: {', '.join(payload['cross_class_families']) or 'none'}")
        elif name == "MACRO_SYNTHESIS":
            lines.append(f"Macro-used sealed cases: {payload['macro_used_case_count']}")
            lines.append(f"Verified work reductions: {payload['reduction_with_macro_count']}")
            lines.append(f"Semantic changes: {payload['semantic_change_count']}")
        lines.append("")

    lines += [
        "## Claim boundary",
        "",
        f"Supported scope: {report['claim_boundary']['supported_scope']}.",
        "",
        "Not claimed:",
    ]
    for claim in report["claim_boundary"]["not_claimed"]:
        lines.append(f"- {claim}")
    lines.append("")
    return "\n".join(lines)


def generate(out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = run_campaign()
    json_path = out_dir / "pct_goal_solver_campaign.json"
    md_path = out_dir / "PCT_GOAL_SOLVER_REPORT.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    print(
        "PCT_GOAL_SOLVER: "
        f"{report['scientific_status']} "
        f"explicit_families={report['modes']['EXPLICIT/PRIMITIVE']['solved_family_count']} "
        f"explicit_wrong={report['modes']['EXPLICIT/PRIMITIVE']['wrong_positive_count']} "
        f"inferred_families={report['modes']['INFERRED/PRIMITIVE']['solved_family_count']} "
        f"gates={sum(report['gates'].values())}/{len(report['gates'])}"
    )
    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("generated-goal-solver"))
    args = parser.parse_args()
    generate(args.out_dir)


if __name__ == "__main__":
    main()
