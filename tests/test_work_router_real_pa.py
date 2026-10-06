import csv
import math

from scripts.qualify_work_router_real_pa import qualify


def write_iq(path, values):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["I", "Q"])
        writer.writeheader()
        for value in values:
            writer.writerow({"I": value.real, "Q": value.imag})


def test_real_pa_qualification_routes_without_waveform_materialization(tmp_path):
    xs = [complex(1, 0), complex(0.5, 0.5), complex(-0.25, 1.0), complex(1.0, -0.5)]
    ops = [
        2.0 * complex(math.cos(math.radians(2)), math.sin(math.radians(2))),
        1.5 * complex(math.cos(math.radians(15)), math.sin(math.radians(15))),
        0.8 * complex(math.cos(math.radians(-12)), math.sin(math.radians(-12))),
        2.5 * complex(math.cos(math.radians(1)), math.sin(math.radians(1))),
    ]
    ys = [x * op for x, op in zip(xs, ops)]
    inp, out = tmp_path / "in.csv", tmp_path / "out.csv"
    write_iq(inp, xs)
    write_iq(out, ys)

    report = qualify(inp, out, gain_db=3.0, phase_deg=10.0)
    assert report["status"] == "PASS"
    assert report["routed_gain_count"] == report["direct_gain_count"]
    assert report["routed_phase_count"] == report["direct_phase_count"] == 2
    assert report["materialization_required_for_gain_query"] is False
    assert report["materialization_required_for_phase_query"] is False
    assert report["waveform_reconstruction_nrmse"] < 1e-14
    assert report["routes"]["gain"] == ["pa.gain.threshold"]
    assert report["routes"]["phase"] == ["pa.phase.threshold"]
