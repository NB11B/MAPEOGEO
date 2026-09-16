from __future__ import annotations

import argparse
import json
from pathlib import Path

from .v2_campaign import V2_MODE_NAMES, run_v2_campaign


def _markdown(report: dict) -> str:
    lines = [
        "# PCT Goal Solver V2 — Composition Stress Campaign",
        "",
        f"**Scientific status:** {report['scientific_status']}",
        "",
        "V2 is a prospective composition-stress campaign. Its first sealed execution freezes the scientific result; CI status and artifact hashes are provenance, not scientific gates.",
        "",
        "## Sealed mode results",
        "",
        "| Mode | Correct outcomes | Wrong positives | Families | Multi-step families | Cross-class families | Mean states | Mean primitive executions |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in V2_MODE_NAMES:
        mode = report["modes"][name]
        lines.append(
            f"| {name} | {mode['correct_outcome_count']} | {mode['wrong_positive_count']} | "
            f"{mode['correct_outcome_family_count']} | {mode['multi_step_solved_family_count']} | "
            f"{mode['cross_class_solved_family_count']} | {mode['mean_expanded_states']:.2f} | "
            f"{mode['mean_primitive_executions']:.2f} |"
        )

    lines += ["", "## Frozen gates", ""]
    for gate, passed in report["gates"].items():
        lines.append(f"- **{'PASS' if passed else 'FAIL'}** — `{gate}`")

    lines += ["", "## Scientific conclusions", ""]
    for name, payload in report["conclusions"].items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"**{payload['status']}**")
        lines.append("")
        for key, value in payload.items():
            if key == "status":
                continue
            if isinstance(value, list):
                rendered = ", ".join(str(item) for item in value) or "none"
            else:
                rendered = str(value)
            lines.append(f"- {key}: {rendered}")
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
    report = run_v2_campaign()
    json_path = out_dir / "pct_goal_solver_v2_campaign.json"
    md_path = out_dir / "PCT_GOAL_SOLVER_V2_REPORT.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    explicit = report["modes"]["EXPLICIT/PRIMITIVE"]
    inferred = report["modes"]["INFERRED/PRIMITIVE"]
    print(
        "PCT_GOAL_SOLVER_V2: "
        f"{report['scientific_status']} "
        f"explicit_families={explicit['correct_outcome_family_count']} "
        f"explicit_wrong={explicit['wrong_positive_count']} "
        f"multistep={explicit['multi_step_solved_family_count']} "
        f"cross_class={explicit['cross_class_solved_family_count']} "
        f"inferred_blind_families={inferred['correct_outcome_family_count']} "
        f"gates={sum(report['gates'].values())}/{len(report['gates'])}"
    )
    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("generated-goal-solver-v2"))
    args = parser.parse_args()
    generate(args.out_dir)


if __name__ == "__main__":
    main()
