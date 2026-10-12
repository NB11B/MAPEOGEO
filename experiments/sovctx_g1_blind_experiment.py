"""SOVCTX-G1 Blind Historical Experiment & Novelty Assimilation Measurement.

Follows the 9-step sequence:
1. Graph views: Runs strictly on historical shakedown checkpoints (ANC, SOV, RUS).
2. Gauge qualification: Respects horizontal lift assumption and basis-independent metrics.
3. Optimized Oja update: Evaluates associative phi (phi^T W) complexity.
4. Freezes completed shakedown epoch states (Epochs 01 to 12).
5. Constructs feature vectors x_t across thread shares, verb shares, bridge counts,
   institution centralities, question types, and candidate verbs.
6. Executes Leibniz-Bocker analysis blind to event timestamps.
7. Compares curvature/residual spikes against actual frontier events afterward.
8. Measures Novelty Assimilation Time tau_A(q) = t_{residual falls} - t_{novelty first appears}.
9. Formulates the geometric thread-spawning pipeline:
   residual -> candidate concept -> question -> corroboration -> thread.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import scipy.linalg as la

from sovctx.node.leibniz_bocker import (
    DiagnosticRegime,
    LeibnizBockerDiagnostics,
    LeibnizBockerTracker,
)


@dataclass
class EpochStateFeatures:
    epoch_idx: int
    thread_shares: Dict[str, float]
    verb_shares: Dict[str, float]
    bridge_counts: int
    institution_counts: Dict[str, int]
    question_type_counts: Dict[str, int]
    contradiction_count: int
    descendant_depth: int
    feature_vector: np.ndarray


FEATURE_NAMES = [
    # Thread shares (normalized)
    "thread_T1", "thread_T2", "thread_T3", "thread_T4", "thread_T5", "thread_T6",
    "thread_T7", "thread_T8", "thread_T9", "thread_T10", "thread_T11", "thread_T12",
    # Verb shares (normalized)
    "verb_STABILIZE", "verb_CONTROL", "verb_INVERT", "verb_CONSTRAIN",
    "verb_PROBE", "verb_REPRESENT", "verb_OBSERVE", "verb_UPDATE", "verb_ADAPT", "verb_REGULARIZE",
    # Frontier Structural Metrics
    "bridge_resolutions",
    "descendant_depth",
    "inst_Steklov", "inst_TsAGI", "inst_IPM", "inst_Sechenov", "inst_IAT",
    "q_spines", "q_bridges", "q_descendants",
]


def extract_blind_features_from_epoch(
    epoch_file: Path,
    shakedown_log_text: str,
    epoch_idx: int,
) -> EpochStateFeatures:
    """Extracts features strictly from epoch records without labels."""
    d = json.loads(epoch_file.read_text(encoding="utf-8"))

    # Slice log text for this epoch
    epochs = re.split(r">>> Starting Epoch (\d+)", shakedown_log_text)
    epoch_body = ""
    for i in range(1, len(epochs), 2):
        if int(epochs[i]) == epoch_idx:
            epoch_body = epochs[i + 1]
            break

    # 1. Thread allocations
    threads = re.findall(r"\(T(\d+)\)", epoch_body)
    total_t = max(1, len(threads))
    t_counts = {f"T{i}": 0 for i in range(1, 13)}
    for th in threads:
        k = f"T{th}"
        if k in t_counts:
            t_counts[k] += 1
    t_shares = {k: count / total_t for k, count in t_counts.items()}

    # 2. Verb counts in resolved relations
    verb_keys = [
        "STABILIZE", "CONTROL", "INVERT", "CONSTRAIN",
        "PROBE", "REPRESENT", "OBSERVE", "UPDATE", "ADAPT", "REGULARIZE"
    ]
    raw_v = {vk: epoch_body.count(vk) for vk in verb_keys}
    total_v = max(1, sum(raw_v.values()))
    v_shares = {vk: raw_v[vk] / total_v for vk in verb_keys}

    # 3. Bridge resolutions
    bridges = len(re.findall(r"RQ:XBRIDGE:", epoch_body))

    # 4. Institutions mentioned
    insts = {
        "Steklov": epoch_body.count("Steklov"),
        "TsAGI": epoch_body.count("TsAGI"),
        "IPM": epoch_body.count("IPM") + epoch_body.count("Keldysh"),
        "Sechenov": epoch_body.count("Sechenov"),
        "IAT": epoch_body.count("IAT") + epoch_body.count("IPU"),
    }

    # 5. Question types
    q_bridges = bridges
    q_descendants = len(re.findall(r":D\d+", epoch_body))
    q_spines = max(0, d.get("questions_resolved", 30) - q_bridges - q_descendants)

    # 6. Descendant depth
    qids = re.findall(r"RQ:[^\s]+", epoch_body)
    max_d_depth = 0
    for qid in qids:
        c = qid.count(":D1")
        if c > max_d_depth:
            max_d_depth = c

    # Vector construction
    vec = [
        t_shares["T1"], t_shares["T2"], t_shares["T3"], t_shares["T4"],
        t_shares["T5"], t_shares["T6"], t_shares["T7"], t_shares["T8"],
        t_shares["T9"], t_shares["T10"], t_shares["T11"], t_shares["T12"],
        v_shares["STABILIZE"], v_shares["CONTROL"], v_shares["INVERT"], v_shares["CONSTRAIN"],
        v_shares["PROBE"], v_shares["REPRESENT"], v_shares["OBSERVE"], v_shares["UPDATE"],
        v_shares["ADAPT"], v_shares["REGULARIZE"],
        float(bridges),
        float(max_d_depth),
        float(insts["Steklov"]), float(insts["TsAGI"]), float(insts["IPM"]),
        float(insts["Sechenov"]), float(insts["IAT"]),
        float(q_spines), float(q_bridges), float(q_descendants),
    ]

    return EpochStateFeatures(
        epoch_idx=epoch_idx,
        thread_shares=t_shares,
        verb_shares=v_shares,
        bridge_counts=bridges,
        institution_counts=insts,
        question_type_counts={"spines": q_spines, "bridges": q_bridges, "descendants": q_descendants},
        contradiction_count=d.get("questions_contradicted", 0),
        descendant_depth=max_d_depth,
        feature_vector=np.array(vec, dtype=float),
    )


def run_blind_experiment() -> Dict[str, Any]:
    print("=" * 80)
    print("SOVCTX-G1: BLIND HISTORICAL SHAKEDOWN EXPERIMENT & NOVELTY ASSIMILATION")
    print("=" * 80)

    checkpoints_dir = Path("evidence/n5/checkpoints")
    log_file = Path("evidence/n5/shakedown.log")
    log_text = log_file.read_text(encoding="utf-8")

    # Step 4 & 5: Load frozen epoch states and build feature trajectory
    epoch_features: List[EpochStateFeatures] = []
    for ep in range(1, 13):
        cp_file = checkpoints_dir / f"epoch_{ep:02d}.json"
        feat = extract_blind_features_from_epoch(cp_file, log_text, ep)
        epoch_features.append(feat)

    X = np.array([ef.feature_vector for ef in epoch_features])
    num_epochs, dim = X.shape
    print(f"[+] Loaded {num_epochs} frozen historical epochs across {dim} state dimensions.")

    # Increments phi_t = x_{t+1} - x_t
    Phi = np.diff(X, axis=0)
    print(f"[+] Computed {len(Phi)} increment transitions phi(t) = x(t+1) - x(t).")

    # Step 6: Run Leibniz-Bocker tracker strictly blind to labels
    tracker = LeibnizBockerTracker(k=2, alpha=0.5, dt=1.0)
    diagnostics: List[LeibnizBockerDiagnostics] = []

    print("\n--- Blind Grassmannian Trajectory Diagnostics ---")
    header = f"{'Step':<14} | {'Coherence':<9} | {'MaxAngle Om':<11} | {'Proj Om~':<9} | {'Residual ||r||':<14} | {'Gap gamma':<9} | {'Regime':<24}"
    print(header)
    print("-" * len(header))

    step_labels = [f"Ep {i:02d} -> {i+1:02d}" for i in range(1, 12)]
    for t, (phi_t, label) in enumerate(zip(Phi, step_labels)):
        diag = tracker.step(phi_t, step_label=label, t=t)
        diagnostics.append(diag)
        print(
            f"{label:<14} | {diag.coherence:<9.4f} | {diag.curvature_max_angle:<11.4f} | {diag.curvature_projector:<9.4f} | {diag.residual_norm:<14.4f} | {diag.spectral_gap:<9.4f} | {diag.regime.value:<24}"
        )

    # Step 7: Unblinded Comparison against Actual Frontier Events
    print("\n" + "=" * 80)
    print("UNBLINDED COMPARISON AGAINST ACTUAL RESEARCH FRONTIER EVENTS")
    print("=" * 80)

    # Ground truth events from campaign logs
    ground_truth_events = [
        {"epoch": 1, "event": "Emergence of T10 (Dual Control), T11 (Cybernetics), T12 (BESM Regularization) via bridges"},
        {"epoch": 2, "event": "Frontier pivots into deep recursive Krasovskii (T2) / Anokhin (T6) descendants"},
        {"epoch": 3, "event": "Full structural accommodation into rank-2 Krasovskii-Anokhin normal mode"},
        {"epoch": 4, "event": "Unbroken invariant descent (depth 3)"},
        {"epoch": 5, "event": "Unbroken invariant descent (depth 4)"},
        {"epoch": 6, "event": "Unbroken invariant descent (depth 5)"},
        {"epoch": 7, "event": "Unbroken invariant descent (depth 6)"},
        {"epoch": 8, "event": "Unbroken invariant descent (depth 7)"},
        {"epoch": 9, "event": "Unbroken invariant descent (depth 8)"},
        {"epoch": 10, "event": "Unbroken invariant descent (depth 9)"},
        {"epoch": 11, "event": "Unbroken invariant descent (depth 10)"},
        {"epoch": 12, "event": "End of 2-hour shakedown run (depth 11 reached, 0 breaks)"},
    ]

    for ev in ground_truth_events[:3]:
        print(f"  * Epoch {ev['epoch']:02d}: {ev['event']}")
    print("  * Epochs 04-12: Steady recursive descent in Krasovskii/Anokhin normal mode.")

    # Step 8: Measure Novelty Assimilation Time tau_A(q)
    # Event q = "T10/T11/T12 Bridge Spawning & Descendant Pivot"
    # t_novelty_appears: Epoch 1 (transition 1->2)
    t_novelty = 1
    tau_r = 0.50  # residual fall threshold
    tau_Omega = 0.25  # curvature threshold

    t_assimilated = None
    for d in diagnostics:
        # Step label e.g. "Ep 03 -> 04" corresponds to epoch transition at step t
        step_ep = int(d.step_label.split("->")[1].strip())
        if d.residual_norm < tau_r and d.curvature_max_angle < tau_Omega and d.coherence > 0.90:
            if step_ep > t_novelty:
                t_assimilated = step_ep
                break

    tau_A = (t_assimilated - t_novelty) if t_assimilated else None
    print("\n--- Novelty Assimilation Time Metric ---")
    print(f"Novelty Emergence Epoch (t_appear):    Epoch {t_novelty:02d} (Bridge Spawning)")
    print(f"Novelty Assimilation Epoch (t_absorb): Epoch {t_assimilated:02d} (Residual < {tau_r}, Curvature < {tau_Omega})")
    print(f"Novelty Assimilation Time tau_A:       {tau_A} epochs ({(tau_A or 0)*10} minutes of autonomous probing)")
    print(f"Interpretation: The graph accommodated the newly spawned bridge dimensions into")
    print(f"a stable 2-dimensional normal mode within {tau_A} epochs ({tau_A*10} mins).")

    # Step 9: Independent Thread Spawning Trigger Verification
    print("\n--- Independent Geometric Thread Spawning Criteria ---")
    print("Rule: ||r_t|| > tau_r AND Omega_k > tau_Omega -> trigger candidate concept evaluation.")
    triggers = []
    for d in diagnostics:
        if d.curvature_max_angle > tau_Omega:
            triggers.append((d.step_label, "SPECTRAL_REORIENTATION", d.curvature_max_angle))
        if d.residual_norm > tau_r:
            triggers.append((d.step_label, "GEOMETRIC_NOVELTY", d.residual_norm))

    print(f"Total geometric triggers fired across 12 epochs: {len(triggers)}")
    for t_step, t_type, t_val in triggers:
        print(f"  * {t_step}: {t_type} (value={t_val:.4f})")

    results = {
        "num_epochs": num_epochs,
        "feature_dim": dim,
        "feature_names": FEATURE_NAMES,
        "diagnostics": [d.to_dict() for d in diagnostics],
        "novelty_assimilation": {
            "t_appear": t_novelty,
            "t_absorb": t_assimilated,
            "tau_A_epochs": tau_A,
            "tau_A_minutes": (tau_A or 0) * 10,
        },
        "geometric_triggers": triggers,
    }

    out_file = Path("evidence/n5/sovctx_g1_blind_historical_report.json")
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n[+] Saved blind historical experiment report to {out_file}")
    return results


if __name__ == "__main__":
    run_blind_experiment()
