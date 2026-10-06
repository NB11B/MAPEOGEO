"""Real measured-I/Q qualification for Work Router v0.1.

Input format is OpenDPD-style CSV with columns I,Q.  The campaign derives the
physical complex transfer r=y/x, stores only log-gain and phase coordinates for
the routed queries, and cross-checks decisions against direct complex arithmetic.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Iterable

from mapeogeo.work_router import Outcome, RouteEdge, WorkRequest, WorkRouter


def read_iq(path: Path) -> list[complex]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [complex(float(row["I"]), float(row["Q"])) for row in reader]


def pa_router() -> WorkRouter:
    return WorkRouter(
        (
            RouteEdge("pa.gain.threshold", "pa.log_gain", "work.gain_above_threshold", 0.5, True, "compare log-gain", requires=("work.gain_threshold_log",)),
            RouteEdge("pa.phase.threshold", "pa.phase", "work.phase_excursion", 0.5, True, "compare abs phase", requires=("work.phase_threshold_rad",)),
            RouteEdge("pa.operator.motion", "pa.operator_steps", "work.operator_motion", 1.0, True, "difference operator coordinates"),
            RouteEdge("pa.materialize.iq", "pa.operator_coordinates", "pa.output_iq", 8.0, True, "exp(log_gain+i phase)*input", materializes=True),
            RouteEdge("pa.unsafe.waveform-shortcut", "pa.operator_coordinates", "work.phase_excursion", 0.01, False, "uncertified shortcut"),
        )
    )


def qualify(input_path: Path, output_path: Path, *, gain_db: float = 3.0, phase_deg: float = 10.0) -> dict:
    inputs = read_iq(input_path)
    outputs = read_iq(output_path)
    if len(inputs) != len(outputs):
        raise ValueError("input/output sample counts differ")

    gain_threshold_log = gain_db * math.log(10.0) / 20.0
    phase_threshold = math.radians(phase_deg)
    log_gain: list[float] = []
    phase: list[float] = []
    direct_gain_count = 0
    direct_phase_count = 0
    reconstruction_sq = 0.0
    output_sq = 0.0

    for x, y in zip(inputs, outputs):
        if abs(x) <= 1e-15:
            continue
        r = y / x
        lg = math.log(abs(r))
        ph = math.atan2(r.imag, r.real)
        log_gain.append(lg)
        phase.append(ph)
        direct_gain_count += int(20.0 * math.log10(abs(y) / abs(x)) > gain_db)
        direct_phase_count += int(abs(math.atan2((y / x).imag, (y / x).real)) > phase_threshold)
        reconstructed = x * math.exp(lg) * complex(math.cos(ph), math.sin(ph))
        reconstruction_sq += abs(reconstructed - y) ** 2
        output_sq += abs(y) ** 2

    router = pa_router()
    gain_decision = router.decide(
        WorkRequest("work.gain_above_threshold"),
        available={"pa.log_gain", "work.gain_threshold_log"},
    )
    phase_decision = router.decide(
        WorkRequest("work.phase_excursion"),
        available={"pa.phase", "work.phase_threshold_rad"},
    )
    materialization_decision = router.decide(
        WorkRequest("pa.output_iq", require_materialized=True),
        available={"pa.operator_coordinates"},
    )

    if gain_decision.outcome != Outcome.EXECUTE or phase_decision.outcome != Outcome.EXECUTE:
        raise AssertionError("certified scalar routes must execute")
    if materialization_decision.outcome not in {Outcome.EXECUTE, Outcome.MATERIALIZE}:
        raise AssertionError("explicit waveform request must expose materialization route")

    routed_gain_count = sum(value > gain_threshold_log for value in log_gain)
    routed_phase_count = sum(abs(value) > phase_threshold for value in phase)
    if routed_gain_count != direct_gain_count:
        raise AssertionError("routed gain decisions disagree with direct complex arithmetic")
    if routed_phase_count != direct_phase_count:
        raise AssertionError("routed phase decisions disagree with direct complex arithmetic")

    dlog = [b - a for a, b in zip(log_gain, log_gain[1:])]
    dphase = []
    for a, b in zip(phase, phase[1:]):
        delta = b - a
        while delta > math.pi:
            delta -= 2.0 * math.pi
        while delta <= -math.pi:
            delta += 2.0 * math.pi
        dphase.append(delta)

    rms = lambda values: math.sqrt(sum(v * v for v in values) / len(values))
    return {
        "status": "PASS",
        "samples": len(log_gain),
        "gain_threshold_db": gain_db,
        "phase_threshold_deg": phase_deg,
        "routed_gain_count": routed_gain_count,
        "direct_gain_count": direct_gain_count,
        "routed_phase_count": routed_phase_count,
        "direct_phase_count": direct_phase_count,
        "operator_motion": {
            "rms_delta_log_gain": rms(dlog),
            "rms_delta_phase_deg": math.degrees(rms(dphase)),
        },
        "waveform_reconstruction_nrmse": math.sqrt(reconstruction_sq / output_sq),
        "routes": {
            "gain": [edge.edge_id for edge in gain_decision.route.edges],
            "phase": [edge.edge_id for edge in phase_decision.route.edges],
            "materialize": [edge.edge_id for edge in materialization_decision.route.edges],
        },
        "materialization_required_for_gain_query": gain_decision.route.materializes,
        "materialization_required_for_phase_query": phase_decision.route.materializes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--gain-db", type=float, default=3.0)
    parser.add_argument("--phase-deg", type=float, default=10.0)
    args = parser.parse_args()
    report = qualify(args.input, args.output, gain_db=args.gain_db, phase_deg=args.phase_deg)
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        args.report.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
