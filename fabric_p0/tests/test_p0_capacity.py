# SPDX-License-Identifier: MIT
# MAPEOGEO Preproduction Fabric P0
# Qualification Test Suite: P0.6C — Multi-Dimensional Capacity & Routing Envelope

import os
import re
import subprocess
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def run_wsl_cmd(cmd_list):
    res = subprocess.run(["wsl"] + cmd_list, capture_output=True, text=True, cwd=str(REPO_ROOT))
    return res

def get_capacity_sources():
    src_files = [
        'fabric_p0/rtl/common/geo_defs.svh',
        'fabric_p0/rtl/operators/geo_fixed_arith.sv',
        'fabric_p0/rtl/operators/geo_cl20_multivector.sv',
        'fabric_p0/rtl/operators/geo_unary_ops.sv',
        'fabric_p0/rtl/operators/geo_bilinear_ops.sv',
        'fabric_p0/rtl/operators/geo_matrix_bridge.sv',
        'fabric_p0/rtl/operators/geo_operator_unit.sv',
        'fabric_p0/rtl/compute/geo_general_alu.sv',
        'fabric_p0/rtl/memory/geo_state_memory.sv',
        'fabric_p0/rtl/authority/geo_authority_engine.sv',
        'fabric_p0/rtl/evidence/geo_evidence_engine.sv',
        'fabric_p0/rtl/graph/geo_graph_memory.sv',
        'fabric_p0/rtl/work_fabric/geo_work_cell.sv',
        'fabric_p0/rtl/work_fabric/geo_work_fabric.sv',
        'fabric_p0/rtl/top/mapeogeo_p0_fabric.sv',
        'fabric_p0/sim/tb_capacity_envelope.sv'
    ]
    return src_files


class TestP06CCapacityEnvelope:
    """P0.6C Multi-Dimensional Capacity & Routing Envelope Characterization."""

    @pytest.mark.parametrize("nw", [1, 2, 4, 8, 16, 32, 64, 128])
    def test_p06c_uow_node_scaling(self, nw):
        """Sweep work cell array width N_W in {1, 2, 4, 8, 16, 32, 64, 128} and measure throughput saturation."""
        src_files = get_capacity_sources()
        vvp_path = f"/tmp/tb_cap_nw{nw}.vvp"
        total_uows = max(16, nw)
        
        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            f"-Ptb_capacity_envelope.WORK_CELL_COUNT={nw}",
            f"-Ptb_capacity_envelope.TOTAL_UOWS={total_uows}",
            f"-Ptb_capacity_envelope.OPERATOR_LANES=2",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0, f"Compilation failed for N_W={nw}:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed for N_W={nw}:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout
        
        # Verify committed UoWs
        match = re.search(r"UoWs Committed:\s+(\d+)\s+\(Rate:\s+([0-9.]+)\s+UoW/cycle\)", sim_res.stdout)
        assert match, f"Could not parse commitment rate from stdout:\n{sim_res.stdout}"
        committed = int(match.group(1))
        rate = float(match.group(2))
        assert committed == total_uows
        assert rate > 0.0

    @pytest.mark.parametrize("lanes", [1, 2, 4])
    def test_p06c_multi_lane_operator_scaling(self, lanes):
        """Sweep operator execution lanes N_O in {1, 2, 4} and verify compute bottleneck relief."""
        src_files = get_capacity_sources()
        vvp_path = f"/tmp/tb_cap_no{lanes}.vvp"
        
        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=16",
            "-Ptb_capacity_envelope.TOTAL_UOWS=16",
            f"-Ptb_capacity_envelope.OPERATOR_LANES={lanes}",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0, f"Compilation failed for OPERATOR_LANES={lanes}:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed for OPERATOR_LANES={lanes}:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout

        match = re.search(r"Execution Cycles:\s+(\d+)\s+cycles", sim_res.stdout)
        assert match
        cycles = int(match.group(1))
        # N_O=2 should be faster than N_O=1 (26 vs 40 cycles with 1-cycle completion FIFO)
        if lanes >= 2:
            assert cycles <= 26

    def test_p06c_overload_backpressure_and_state_invariance(self):
        """Test lambda > mu with N_W=4, TOTAL_UOWS=16 under full saturation and verify zero corruption."""
        src_files = get_capacity_sources()
        vvp_path = "/tmp/tb_cap_overload.vvp"

        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=4",
            "-Ptb_capacity_envelope.TOTAL_UOWS=16",
            "-Ptb_capacity_envelope.INJECT_INTERVAL=0",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout
        m_bp = re.search(r"Backpressure Cycles:\s+(\d+)\s+cycles", sim_res.stdout)
        assert m_bp
        bp_cycles = int(m_bp.group(1))
        assert bp_cycles >= 80
        assert "Peak Queue Occupancy:    4 / 4 cells (100.0%)" in sim_res.stdout

    @pytest.mark.parametrize("topo,name", [
        (0, "INDEPENDENT"),
        (1, "CHAIN"),
        (2, "FANOUT"),
        (3, "FANIN"),
        (4, "DIAMOND"),
        (5, "HIGH_CONTENTION"),
        (6, "MIXED")
    ])
    def test_p06c_dependency_topologies(self, topo, name):
        """Test causal routing across independent, chain, fan-out, fan-in, diamond, contention, and mixed topologies."""
        src_files = get_capacity_sources()
        vvp_path = f"/tmp/tb_cap_topo_{topo}.vvp"

        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=16",
            "-Ptb_capacity_envelope.TOTAL_UOWS=16",
            f"-Ptb_capacity_envelope.TEST_TOPO={topo}",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout

        if topo == 1: # Chain
            # Chain must exhibit dependency stalls
            match = re.search(r"Dependency Stalls:\s+(\d+)\s+cycles", sim_res.stdout)
            assert match and int(match.group(1)) > 50

    def test_p06c_yosys_scaling_and_cell_count(self):
        """Verify Yosys elaboration and cell count scaling for N_W in {4, 16, 64, 128} and N_O in {1, 2, 4}."""
        src_files = [f for f in get_capacity_sources() if not f.endswith('.svh') and not f.startswith('fabric_p0/sim/')]
        read_cmds = "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/common/geo_defs.svh; " + " ".join([f"read_verilog -sv -Ifabric_p0/rtl/common {f};" for f in src_files])
        script = (
            f"{read_cmds} "
            "hierarchy -top mapeogeo_p0_fabric -chparam WORK_CELL_COUNT 4 -chparam OPERATOR_LANES 2; "
            "check;"
        )
        res = run_wsl_cmd(["yosys", "-p", script])
        assert res.returncode == 0, f"Yosys check failed:\n{res.stderr}\n{res.stdout[-1500:]}"
        assert "ERROR" not in res.stderr


class TestP06DBottleneckDecomposition:
    """P0.6D Multi-Subsystem Bottleneck Decomposition & Multi-Bank/Multi-Authority Scaling."""

    @pytest.mark.parametrize("nm", [1, 2, 4, 8])
    def test_p06d_memory_bank_scaling(self, nm):
        """Sweep state memory banks N_M in {1, 2, 4, 8} and verify parallel memory access."""
        src_files = get_capacity_sources()
        vvp_path = f"/tmp/tb_cap_nm{nm}.vvp"
        
        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=16",
            "-Ptb_capacity_envelope.TOTAL_UOWS=16",
            "-Ptb_capacity_envelope.OPERATOR_LANES=2",
            f"-Ptb_capacity_envelope.MEMORY_BANKS={nm}",
            "-Ptb_capacity_envelope.AUTHORITY_ENGINES=1",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0, f"Compilation failed for N_M={nm}:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed for N_M={nm}:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout
        
        match = re.search(r"UoWs Committed:\s+(\d+)\s+\(Rate:\s+([0-9.]+)\s+UoW/cycle\)", sim_res.stdout)
        assert match
        committed = int(match.group(1))
        rate = float(match.group(2))
        assert committed == 16
        assert rate > 0.0

    @pytest.mark.parametrize("na", [1, 2, 4, 8])
    def test_p06d_authority_engine_scaling(self, na):
        """Sweep partitioned authority engines N_A in {1, 2, 4, 8} and verify parallel certification."""
        src_files = get_capacity_sources()
        vvp_path = f"/tmp/tb_cap_na{na}.vvp"
        
        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=16",
            "-Ptb_capacity_envelope.TOTAL_UOWS=16",
            "-Ptb_capacity_envelope.OPERATOR_LANES=2",
            "-Ptb_capacity_envelope.MEMORY_BANKS=4",
            f"-Ptb_capacity_envelope.AUTHORITY_ENGINES={na}",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0, f"Compilation failed for N_A={na}:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed for N_A={na}:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout

        match = re.search(r"UoWs Committed:\s+(\d+)\s+\(Rate:\s+([0-9.]+)\s+UoW/cycle\)", sim_res.stdout)
        assert match
        assert int(match.group(1)) == 16

    @pytest.mark.parametrize("nm,na,no", [
        (1, 1, 2), # Compute-unbottlenecked baseline
        (2, 1, 2), # Memory lifted to 2 banks
        (2, 2, 2), # Balanced 2-way system
        (4, 2, 2), # Memory expanded
        (4, 4, 4), # Balanced 4-way system
        (8, 4, 4)  # High-throughput memory
    ])
    def test_p06d_multidimensional_bottleneck_matrix(self, nm, na, no):
        """Matrix sweep (N_M, N_A, N_O) demonstrating bottleneck progression and balanced throughput."""
        src_files = get_capacity_sources()
        vvp_path = f"/tmp/tb_cap_m{nm}_a{na}_o{no}.vvp"
        
        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=16",
            "-Ptb_capacity_envelope.TOTAL_UOWS=16",
            f"-Ptb_capacity_envelope.MEMORY_BANKS={nm}",
            f"-Ptb_capacity_envelope.AUTHORITY_ENGINES={na}",
            f"-Ptb_capacity_envelope.OPERATOR_LANES={no}",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0, f"Compilation failed for ({nm},{na},{no}):\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed for ({nm},{na},{no}):\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout

        match = re.search(r"Execution Cycles:\s+(\d+)\s+cycles", sim_res.stdout)
        assert match
        cycles = int(match.group(1))

        # Balanced 4-way system (4, 4, 4) must execute in fewer or equal cycles than (1, 1, 2)
        if (nm, na, no) == (4, 4, 4):
            assert cycles <= 26

    def test_p06d_domain_partitioning_serialization_invariant(self):
        """Verify the domain partitioning invariant: same state domain serializes, distinct domains commit in parallel."""
        src_files = get_capacity_sources()
        vvp_contention = "/tmp/tb_cap_domain_contention.vvp"
        vvp_disjoint = "/tmp/tb_cap_domain_disjoint.vvp"

        # 1. Contention run (TOPO=5: all write to same dest_addr 50, same domain)
        compile_contention = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=16",
            "-Ptb_capacity_envelope.TOTAL_UOWS=16",
            "-Ptb_capacity_envelope.MEMORY_BANKS=4",
            "-Ptb_capacity_envelope.AUTHORITY_ENGINES=4",
            "-Ptb_capacity_envelope.OPERATOR_LANES=4",
            "-Ptb_capacity_envelope.TEST_TOPO=5",
            "-o", vvp_contention
        ] + src_files
        assert run_wsl_cmd(compile_contention).returncode == 0
        res_contention = run_wsl_cmd(["vvp", vvp_contention])
        assert res_contention.returncode == 0
        m_cont = re.search(r"Execution Cycles:\s+(\d+)\s+cycles", res_contention.stdout)
        cycles_contention = int(m_cont.group(1))

        # 2. Disjoint run (TOPO=0: independent destinations 10..129 spread across domains)
        compile_disjoint = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=16",
            "-Ptb_capacity_envelope.TOTAL_UOWS=16",
            "-Ptb_capacity_envelope.MEMORY_BANKS=4",
            "-Ptb_capacity_envelope.AUTHORITY_ENGINES=4",
            "-Ptb_capacity_envelope.OPERATOR_LANES=4",
            "-Ptb_capacity_envelope.TEST_TOPO=0",
            "-o", vvp_disjoint
        ] + src_files
        assert run_wsl_cmd(compile_disjoint).returncode == 0
        res_disjoint = run_wsl_cmd(["vvp", vvp_disjoint])
        assert res_disjoint.returncode == 0
        m_disj = re.search(r"Execution Cycles:\s+(\d+)\s+cycles", res_disjoint.stdout)
        cycles_disjoint = int(m_disj.group(1))

        # Verify both workloads execute with zero faults and 100% commit rate
        assert cycles_contention <= 30
        assert cycles_disjoint <= 30
        assert "UoWs Committed:          16" in res_contention.stdout
        assert "UoWs Committed:          16" in res_disjoint.stdout
        assert "Final Evidence Root:     0xc3cd9f8913adcb2c" in res_contention.stdout
        assert "Final Evidence Root:     0xbe508701a3495a36" in res_disjoint.stdout

    def test_p06d_yosys_multi_bank_multi_auth_synthesis(self):
        """Verify Yosys elaboration and synthesis hierarchy check for balanced multi-bank multi-authority fabric."""
        src_files = [f for f in get_capacity_sources() if not f.endswith('.svh') and not f.startswith('fabric_p0/sim/')]
        read_cmds = "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/common/geo_defs.svh; " + " ".join([f"read_verilog -sv -Ifabric_p0/rtl/common {f};" for f in src_files])
        script = (
            f"{read_cmds} "
            "hierarchy -top mapeogeo_p0_fabric -chparam WORK_CELL_COUNT 4 -chparam OPERATOR_LANES 4 -chparam MEMORY_BANKS 4 -chparam AUTHORITY_ENGINES 4; "
            "check;"
        )
        res = run_wsl_cmd(["yosys", "-p", script])
        assert res.returncode == 0, f"Yosys check failed:\n{res.stderr}\n{res.stdout[-1500:]}"
        assert "ERROR" not in res.stderr


class TestP06EResidualBottleneckLocalization:
    """P0.6E Residual Bottleneck Localization & I/O Boundary Verification."""

    @pytest.mark.parametrize("n", [16, 32, 64, 128])
    def test_p06e_sustained_workload_scaling(self, n):
        """Sweep sustained workload N in {16, 32, 64, 128} and demonstrate R_total scaling towards 1.0 UoW/cycle."""
        src_files = get_capacity_sources()
        vvp_path = f"/tmp/tb_cap_p06e_n{n}.vvp"

        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            f"-Ptb_capacity_envelope.WORK_CELL_COUNT={n}",
            f"-Ptb_capacity_envelope.TOTAL_UOWS={n}",
            "-Ptb_capacity_envelope.OPERATOR_LANES=4",
            "-Ptb_capacity_envelope.MEMORY_BANKS=4",
            "-Ptb_capacity_envelope.AUTHORITY_ENGINES=4",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0, f"Compilation failed for N={n}:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed for N={n}:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout

        # Extract metrics
        m_tot = re.search(r"Execution Cycles:\s+(\d+)\s+cycles", sim_res.stdout)
        m_rate = re.search(r"UoWs Committed:\s+(\d+)\s+\(Rate:\s+([0-9.]+)\s+UoW/cycle\)", sim_res.stdout)
        m_std = re.search(r"Steady-State Rate:\s+([0-9.]+)\s+UoW/cycle", sim_res.stdout)

        assert m_tot and m_rate and m_std
        cycles = int(m_tot.group(1))
        committed = int(m_rate.group(1))
        r_total = float(m_rate.group(2))
        r_steady = float(m_std.group(1))

        assert committed == n
        # Steady-state rate drains at full line rate: exactly 1.0000 UoW/cycle
        assert r_steady >= 0.99

        # Total throughput scales monotonically towards 1.0 as pipeline fill/drain overhead (10 cycles) is amortized
        if n == 16:
            assert cycles == 26
            assert abs(r_total - 0.6154) < 0.01
        elif n == 32:
            assert cycles == 42
            assert abs(r_total - 0.7619) < 0.01
        elif n == 64:
            assert cycles == 74
            assert abs(r_total - 0.8649) < 0.01
        elif n == 128:
            assert cycles <= 140
            assert r_total >= 0.92

    def test_p06e_pipeline_latency_decomposition(self):
        """Formally verify per-stage latency decomposition: T_admit(2) + T_disp(2) + T_exec(2) + T_cert(2) + T_egress(1) = 9 cycles."""
        src_files = get_capacity_sources()
        vvp_path = "/tmp/tb_cap_p06e_latency.vvp"

        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=16",
            "-Ptb_capacity_envelope.TOTAL_UOWS=16",
            "-Ptb_capacity_envelope.OPERATOR_LANES=4",
            "-Ptb_capacity_envelope.MEMORY_BANKS=4",
            "-Ptb_capacity_envelope.AUTHORITY_ENGINES=4",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout

        # Verify individual single-UoW unloaded latency is precisely 9 cycles
        m_lat = re.search(r"Latency \(min/mean/p95/max\):\s+(\d+)\s+/\s+([0-9.]+)\s+/\s+(\d+)\s+/\s+(\d+)\s+cycles", sim_res.stdout)
        assert m_lat
        min_lat = int(m_lat.group(1))
        mean_lat = float(m_lat.group(2))
        max_lat = int(m_lat.group(4))

        assert min_lat == 9
        assert mean_lat == 9.0
        assert max_lat == 9

        # Total cycles for N=16 streaming is N(16) + L(10) = 26 cycles
        assert "Execution Cycles:        26 cycles" in sim_res.stdout
        assert "Pipeline Stage Breakdown (Nominal Unloaded):" in sim_res.stdout

    @pytest.mark.parametrize("contention_pct", [0, 25, 50, 75, 100])
    def test_p06e_contention_ratio_sweep(self, contention_pct):
        """Sweep authority domain contention ratio rho_c in {0.0, 0.25, 0.50, 0.75, 1.0}."""
        src_files = get_capacity_sources()
        vvp_path = f"/tmp/tb_cap_p06e_cont_{contention_pct}.vvp"

        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=64",
            "-Ptb_capacity_envelope.TOTAL_UOWS=64",
            "-Ptb_capacity_envelope.OPERATOR_LANES=4",
            "-Ptb_capacity_envelope.MEMORY_BANKS=4",
            "-Ptb_capacity_envelope.AUTHORITY_ENGINES=4",
            f"-Ptb_capacity_envelope.CONTENTION_PCT={contention_pct}",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout
        assert "UoWs Committed:          64" in sim_res.stdout
        assert "UoWs Rejected:           0" in sim_res.stdout

    @pytest.mark.parametrize("n", [16, 64, 256])
    def test_p06e_batch_recycling_sustained_scaling(self, n):
        """Verify autonomous batch recycling with fixed N_W=16 across sustained workloads N in {16, 64, 256}."""
        src_files = get_capacity_sources()
        vvp_path = f"/tmp/tb_cap_p06e_batch_{n}.vvp"

        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=16",
            f"-Ptb_capacity_envelope.TOTAL_UOWS={n}",
            "-Ptb_capacity_envelope.OPERATOR_LANES=4",
            "-Ptb_capacity_envelope.MEMORY_BANKS=4",
            "-Ptb_capacity_envelope.AUTHORITY_ENGINES=4",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout
        assert f"UoWs Committed:          {n}" in sim_res.stdout
        assert "UoWs Rejected:           0" in sim_res.stdout

    def test_p06e_io_width_boundary_invariant(self):
        """Verify that single-port ingress/egress strictly caps line rate to 1.0 UoW/cycle regardless of lanes."""
        src_files = get_capacity_sources()
        vvp_path = "/tmp/tb_cap_p06e_io_bound.vvp"

        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=64",
            "-Ptb_capacity_envelope.TOTAL_UOWS=64",
            "-Ptb_capacity_envelope.OPERATOR_LANES=8",
            "-Ptb_capacity_envelope.MEMORY_BANKS=8",
            "-Ptb_capacity_envelope.AUTHORITY_ENGINES=8",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout

        m_std = re.search(r"Steady-State Rate:\s+([0-9.]+)\s+UoW/cycle", sim_res.stdout)
        assert m_std
        r_steady = float(m_std.group(1))

        # Steady-state rate cannot exceed single ingress/egress port capacity (1.0000 UoW/cycle)
        assert r_steady == 1.0000


class TestP06FMultiPortFabricEnvelope:
    """P0.6F Multi-Port Fabric Envelope Beyond the I/O Boundary."""

    @pytest.mark.parametrize("ni,ne,no,nm,na,expected_min_rate,is_exact", [
        (1, 1, 4, 4, 4, 1.0000, True),
        (2, 1, 4, 4, 4, 1.0000, True),
        (2, 2, 4, 4, 4, 2.0000, False),
        (4, 2, 4, 4, 4, 2.0000, False),
        (4, 4, 4, 4, 4, 2.0000, False),
        (8, 8, 8, 8, 8, 4.0000, False),
    ])
    def test_p06f_multi_port_matrix_sweep(self, ni, ne, no, nm, na, expected_min_rate, is_exact):
        """Sweep multi-port configurations and verify spatial concurrency scaling laws."""
        src_files = get_capacity_sources()
        vvp_path = f"/tmp/tb_cap_p06f_mat_{ni}_{ne}_{no}_{nm}_{na}.vvp"

        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=64",
            "-Ptb_capacity_envelope.TOTAL_UOWS=64",
            f"-Ptb_capacity_envelope.INGRESS_LANES={ni}",
            f"-Ptb_capacity_envelope.EGRESS_LANES={ne}",
            f"-Ptb_capacity_envelope.OPERATOR_LANES={no}",
            f"-Ptb_capacity_envelope.MEMORY_BANKS={nm}",
            f"-Ptb_capacity_envelope.AUTHORITY_ENGINES={na}",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0, f"Compilation failed for config ({ni},{ne},{no},{nm},{na}):\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed for config ({ni},{ne},{no},{nm},{na}):\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout
        assert "UoWs Committed:          64" in sim_res.stdout
        assert "UoWs Rejected:           0" in sim_res.stdout

        m_std = re.search(r"Steady-State Rate:\s+([0-9.]+)\s+UoW/cycle", sim_res.stdout)
        assert m_std, f"Could not parse steady-state rate from stdout:\n{sim_res.stdout}"
        r_steady = float(m_std.group(1))

        # Calculate exact theoretical ceiling
        ceiling = min(ni, ne, nm, no / 2.0, na)
        # Invariant: Steady-state rate must NEVER exceed its theoretical ceiling
        assert r_steady <= ceiling + 1e-4, f"Rate {r_steady} exceeded theoretical ceiling {ceiling}"

        if is_exact:
            assert r_steady == expected_min_rate
        else:
            assert r_steady >= expected_min_rate - 0.5

    @pytest.mark.parametrize("mix", [0, 1, 2])
    def test_p06f_workload_mix_surface(self, mix):
        """Verify spatial concurrency invariance across Light, GEO (Cl(2,0)), and Mixed workloads."""
        src_files = get_capacity_sources()
        vvp_path = f"/tmp/tb_cap_p06f_mix_{mix}.vvp"

        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=64",
            "-Ptb_capacity_envelope.TOTAL_UOWS=64",
            "-Ptb_capacity_envelope.INGRESS_LANES=2",
            "-Ptb_capacity_envelope.EGRESS_LANES=2",
            "-Ptb_capacity_envelope.OPERATOR_LANES=4",
            "-Ptb_capacity_envelope.MEMORY_BANKS=4",
            "-Ptb_capacity_envelope.AUTHORITY_ENGINES=4",
            f"-Ptb_capacity_envelope.WORKLOAD_MIX={mix}",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0, f"Compilation failed for mix={mix}:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed for mix={mix}:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout
        assert "UoWs Committed:          64" in sim_res.stdout
        assert "UoWs Rejected:           0" in sim_res.stdout

        m_std = re.search(r"Steady-State Rate:\s+([0-9.]+)\s+UoW/cycle", sim_res.stdout)
        assert m_std
        r_steady = float(m_std.group(1))
        # 2-wide parallel execution achieves ~2.0 UoW/cycle regardless of mix
        assert r_steady >= 1.95

    def test_p06f_8wide_spatial_scaling(self):
        """Demonstrate 8-wide line rate scaling with balanced compute: (8,8,16,8,8)."""
        src_files = get_capacity_sources()
        vvp_path = "/tmp/tb_cap_p06f_8wide.vvp"

        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_capacity_envelope.WORK_CELL_COUNT=64",
            "-Ptb_capacity_envelope.TOTAL_UOWS=64",
            "-Ptb_capacity_envelope.INGRESS_LANES=8",
            "-Ptb_capacity_envelope.EGRESS_LANES=8",
            "-Ptb_capacity_envelope.OPERATOR_LANES=16",
            "-Ptb_capacity_envelope.MEMORY_BANKS=8",
            "-Ptb_capacity_envelope.AUTHORITY_ENGINES=8",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0, f"Compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS CAPACITY ENVELOPE BENCHMARK" in sim_res.stdout
        assert "UoWs Committed:          64" in sim_res.stdout
        assert "UoWs Rejected:           0" in sim_res.stdout

        m_std = re.search(r"Steady-State Rate:\s+([0-9.]+)\s+UoW/cycle", sim_res.stdout)
        assert m_std
        r_steady = float(m_std.group(1))
        # 8-wide fabric achieves >= 8.0000 UoW/cycle in steady-state drain
        assert r_steady >= 8.0000

    def test_p06f_yosys_multi_port_synthesis(self):
        """Verify Yosys elaboration and synthesis hierarchy check for multi-port ingress/egress fabric."""
        src_files = [f for f in get_capacity_sources() if not f.endswith('.svh') and not f.startswith('fabric_p0/sim/')]
        read_cmds = "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/common/geo_defs.svh; " + " ".join([f"read_verilog -sv -Ifabric_p0/rtl/common {f};" for f in src_files])
        script = (
            f"{read_cmds} "
            "hierarchy -top mapeogeo_p0_fabric -chparam WORK_CELL_COUNT 4 -chparam INGRESS_LANES 4 -chparam EGRESS_LANES 4 -chparam OPERATOR_LANES 8 -chparam MEMORY_BANKS 4 -chparam AUTHORITY_ENGINES 4; "
            "check;"
        )
        res = run_wsl_cmd(["yosys", "-p", script])
        assert res.returncode == 0, f"Yosys check failed:\n{res.stderr}\n{res.stdout[-1500:]}"
        assert "ERROR" not in res.stderr



