# SPDX-License-Identifier: MIT
"""Pytest Wrapper for PDI-v0.5 Extended Hardware Stress Simulation."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent


def test_v05_hardware_stress_simulation():
    """Executes tb_pdi_v05_hardware_stress in WSL Icarus Verilog simulation."""
    vvp_path = "/tmp/tb_v05_stress.vvp"
    src_files = [
        "fabric_p0/rtl/operators/geo_fixed_arith.sv",
        "fabric_p0/rtl/operators/geo_cl20_multivector.sv",
        "fabric_p0/rtl/operators/geo_unary_ops.sv",
        "fabric_p0/rtl/operators/geo_bilinear_ops.sv",
        "fabric_p0/rtl/operators/geo_matrix_bridge.sv",
        "fabric_p0/rtl/operators/geo_operator_unit.sv",
        "fabric_p0/rtl/compute/geo_general_alu.sv",
        "fabric_p0/rtl/memory/geo_state_memory.sv",
        "fabric_p0/rtl/authority/geo_authority_engine.sv",
        "fabric_p0/rtl/evidence/geo_evidence_engine.sv",
        "fabric_p0/rtl/graph/geo_graph_memory.sv",
        "fabric_p0/rtl/work_fabric/geo_work_cell.sv",
        "fabric_p0/rtl/work_fabric/geo_work_fabric.sv",
        "fabric_p0/rtl/top/mapeogeo_p0_fabric.sv",
        "pdi/rtl/pdi_ingress.sv",
        "pdi/rtl/pdi_packet_validator.sv",
        "pdi/rtl/pdi_egress.sv",
        "pdi/rtl/pdi_uow_bridge.sv",
        "pdi/tests/tb_pdi_v05_hardware_stress.sv",
    ]

    compile_cmd = ["wsl", "iverilog", "-g2012", "-Ifabric_p0/rtl/common", "-Ipdi/rtl", "-o", vvp_path] + src_files
    c_res = subprocess.run(compile_cmd, capture_output=True, text=True, cwd=str(PACKAGE_ROOT))
    assert c_res.returncode == 0, f"Compilation failed:\n{c_res.stderr}"

    run_cmd = ["wsl", "vvp", vvp_path]
    r_res = subprocess.run(run_cmd, capture_output=True, text=True, cwd=str(PACKAGE_ROOT))
    assert r_res.returncode == 0, f"Simulation failed:\n{r_res.stderr}\n{r_res.stdout}"
    assert "4 PASSED, 0 FAILED" in r_res.stdout, f"Stress test failed:\n{r_res.stdout}"
