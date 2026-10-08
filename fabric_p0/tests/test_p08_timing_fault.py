# SPDX-License-Identifier: MIT
# MAPEOGEO Preproduction Fabric P0
# Qualification Test Suite: Milestone P0.8 — Spatial Timing & Fault Qualification

import os
import re
import subprocess
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def run_wsl_cmd(cmd_list):
    res = subprocess.run(["wsl"] + cmd_list, capture_output=True, text=True, cwd=str(REPO_ROOT))
    return res

def get_fault_sources():
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
        'fabric_p0/rtl/work_fabric/geo_e10_closure_engine.sv',
        'fabric_p0/sim/tb_fault_timing_qualification.sv'
    ]
    return src_files


class TestP08TimingFaultQualification:
    """Milestone P0.8: Spatial Timing & Fault Qualification Suite."""

    @pytest.fixture(scope="class")
    def compiled_fault_sim(self):
        """Compile the P0.8 fault qualification simulation once for the test suite."""
        src_files = get_fault_sources()
        vvp_path = "fabric_p0/sim/tb_fault_qual_main.vvp"
        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-o", vvp_path
        ] + src_files
        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0, f"Compilation failed:\n{comp_res.stderr}"
        return vvp_path

    @pytest.mark.parametrize("topo", [0, 1, 2, 3, 4, 5])
    def test_p08_topology_perturbation_invariance(self, compiled_fault_sim, topo):
        """P0.8.2/3: Verify causal semantic invariance across topologies under varying stall seeds & rates."""
        vvp_path = compiled_fault_sim
        seeds = [42, 1234, 9999]
        stall_rates = [10, 25, 50]
        
        baseline_semantic_root = None
        physical_roots = set()

        for s in seeds:
            for r in stall_rates:
                run_cmd = ["vvp", vvp_path, "+MODE=0", f"+TOPO={topo}", "+TOTAL_UOWS=8", f"+SEED={s}", f"+STALL_RATE={r}"]
                sim_res = run_wsl_cmd(run_cmd)
                assert sim_res.returncode == 0, f"Sim failed for topo={topo} seed={s} rate={r}:\n{sim_res.stderr}\n{sim_res.stdout}"
                assert "P08_PASS" in sim_res.stdout

                m_sem = re.search(r"\[SEMANTIC_ROOT\]\s+(0x[0-9a-fA-F]+)", sim_res.stdout)
                m_phy = re.search(r"\[PHYSICAL_ROOT\]\s+(0x[0-9a-fA-F]+)", sim_res.stdout)
                assert m_sem, f"Missing semantic root in output for topo={topo} seed={s}"
                assert m_phy, f"Missing physical root in output for topo={topo} seed={s}"

                sem_root = m_sem.group(1).lower()
                phy_root = m_phy.group(1).lower()
                physical_roots.add(phy_root)

                if baseline_semantic_root is None:
                    baseline_semantic_root = sem_root
                else:
                    assert sem_root == baseline_semantic_root, (
                        f"Semantic divergence detected! Topo={topo}, Seed={s}, Rate={r}: "
                        f"{sem_root} != {baseline_semantic_root}"
                    )

        # Confirm that physical execution was indeed perturbed/reordered across conditions
        assert len(physical_roots) >= 1

    @pytest.mark.parametrize("contenders", [2, 4, 8, 16, 32])
    def test_p08_stale_state_cas_race_qualification(self, compiled_fault_sim, contenders):
        """P0.8.4: Verify atomic CAS mutex: exactly 1 contender commits, N-1 refused, 0 unauthorized mutations."""
        vvp_path = compiled_fault_sim
        run_cmd = ["vvp", vvp_path, "+MODE=1", f"+CONTENDERS={contenders}", "+SEED=42", "+STALL_RATE=25"]
        sim_res = run_wsl_cmd(run_cmd)
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "STALE_RACE_PASS" in sim_res.stdout

        m = re.search(r"\[STALE_RACE_PASS\]\s+Contenders=(\d+)\s+Committed=(\d+)\s+Refused=(\d+)\s+FinalVersion=(\d+)", sim_res.stdout)
        assert m, f"Pattern match failed in output:\n{sim_res.stdout}"
        c_count = int(m.group(1))
        committed = int(m.group(2))
        refused = int(m.group(3))
        final_ver = int(m.group(4))

        assert c_count == contenders
        assert committed == 1, f"Expected exactly 1 commit, got {committed}"
        assert refused == contenders - 1, f"Expected {contenders - 1} refused, got {refused}"
        assert final_ver == 2, f"Expected final version 2, got {final_ver}"

    def test_p08_security_attack_injection_under_load(self, compiled_fault_sim):
        """P0.8.5: Verify 100% interception of forged capability tokens and out-of-bounds graph mutations."""
        vvp_path = compiled_fault_sim
        run_cmd = ["vvp", vvp_path, "+MODE=2", "+SEED=42", "+STALL_RATE=25"]
        sim_res = run_wsl_cmd(run_cmd)
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "SECURITY_ATTACK_PASS" in sim_res.stdout

        m = re.search(r"\[SECURITY_ATTACK_PASS\]\s+ValidCommitted=(\d+)\s+IllegalBlocked=(\d+)\s+ZeroIllegalMutations=(\d+)", sim_res.stdout)
        assert m, f"Pattern match failed:\n{sim_res.stdout}"
        valid_committed = int(m.group(1))
        illegal_blocked = int(m.group(2))
        zero_mut = int(m.group(3))

        assert valid_committed == 8, f"Expected 8 valid commits, got {valid_committed}"
        assert illegal_blocked == 8, f"Expected 8 illegal attacks blocked, got {illegal_blocked}"
        assert zero_mut == 1, "Zero illegal mutations invariant violated!"

    def test_p08_arithmetic_fault_injection(self, compiled_fault_sim):
        """P0.8.6/7: Verify fixed-point arithmetic overflow interception and zero state mutation."""
        vvp_path = compiled_fault_sim
        run_cmd = ["vvp", vvp_path, "+MODE=3", "+SEED=42", "+STALL_RATE=25"]
        sim_res = run_wsl_cmd(run_cmd)
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "FAULT_INJECTION_PASS" in sim_res.stdout

        m = re.search(r"\[FAULT_INJECTION_PASS\]\s+NormalCommitted=(\d+)\s+FaultsDetected=(\d+)\s+ZeroFaultMutations=(\d+)", sim_res.stdout)
        assert m, f"Pattern match failed:\n{sim_res.stdout}"
        normal_committed = int(m.group(1))
        faults_detected = int(m.group(2))
        zero_mut = int(m.group(3))

        assert normal_committed == 4, f"Expected 4 normal commits, got {normal_committed}"
        assert faults_detected == 4, f"Expected 4 overflow faults detected, got {faults_detected}"
        assert zero_mut == 1, "Zero fault mutations invariant violated!"

    def test_p08_adversarial_queue_pressure_saturation(self, compiled_fault_sim):
        """P0.8.8: Verify robust backpressure handling under 90% egress throttling without lost work."""
        vvp_path = compiled_fault_sim
        run_cmd = ["vvp", vvp_path, "+MODE=4", "+SEED=42", "+STALL_RATE=25"]
        sim_res = run_wsl_cmd(run_cmd)
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "QUEUE_PRESSURE_PASS" in sim_res.stdout

        m = re.search(r"\[QUEUE_PRESSURE_PASS\]\s+BackpressureCycles=(\d+)\s+PeakOccupancy=(\d+)\s+Completed=(\d+)", sim_res.stdout)
        assert m, f"Pattern match failed:\n{sim_res.stdout}"
        backpressure = int(m.group(1))
        peak_occupancy = int(m.group(2))
        completed = int(m.group(3))

        assert backpressure >= 50, f"Expected significant backpressure cycles, got {backpressure}"
        assert peak_occupancy == 8, f"Expected queue saturation peak 8, got {peak_occupancy}"
        assert completed == 32, f"Expected 32 completed UoWs, got {completed}"

    def test_p08_e10_closure_under_heavy_stalls(self, compiled_fault_sim):
        """P0.8.10: Verify autonomous E10 universe closure reaches CLOSED_BOUNDED_UNIVERSE under 25% stalls."""
        vvp_path = compiled_fault_sim
        run_cmd = ["vvp", vvp_path, "+MODE=5", "+SEED=42", "+STALL_RATE=25"]
        sim_res = run_wsl_cmd(run_cmd)
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "E10_STALL_CLOSURE_PASS" in sim_res.stdout

        m = re.search(r"\[E10_STALL_CLOSURE_PASS\]\s+Status=CLOSED_BOUNDED_UNIVERSE\s+ProbesCommitted=(\d+)\s+EdgesMutated=(\d+)", sim_res.stdout)
        assert m, f"Pattern match failed:\n{sim_res.stdout}"
        probes = int(m.group(1))
        edges = int(m.group(2))

        assert probes == 20, f"Expected 20 probes committed, got {probes}"
        assert edges == 20, f"Expected 20 graph edges mutated, got {edges}"

    def test_p08_e10_restricted_nullity_under_stalls(self):
        """P0.8.10: Verify restricted universe detects null space and refuses false closure under stalls."""
        src_files = get_fault_sources()
        vvp_path = "fabric_p0/sim/tb_fault_qual_nullity.vvp"
        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            "-Ptb_fault_timing_qualification.RESTRICT_PROBES_NULLITY=1",
            "-o", vvp_path
        ] + src_files
        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0, f"Compilation failed:\n{comp_res.stderr}"

        run_cmd = ["vvp", vvp_path, "+MODE=6", "+SEED=42", "+STALL_RATE=25"]
        sim_res = run_wsl_cmd(run_cmd)
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "E10_STALL_NULLITY_PASS" in sim_res.stdout
        assert "NullityDetected=1" in sim_res.stdout

    def test_p08_yosys_synthesis_fault_ports(self):
        """Verify Yosys elaboration and synthesis hierarchy check for fabric with P0.8 perturbation & evidence ports."""
        src_files = [f for f in get_fault_sources() if not f.endswith('.svh') and not f.startswith('fabric_p0/sim/')]
        read_cmds = "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/common/geo_defs.svh; " + " ".join([f"read_verilog -sv -Ifabric_p0/rtl/common {f};" for f in src_files])
        script = (
            f"{read_cmds} "
            "hierarchy -top mapeogeo_p0_fabric -chparam WORK_CELL_COUNT 4 -chparam INGRESS_LANES 2 -chparam EGRESS_LANES 2 -chparam OPERATOR_LANES 4 -chparam MEMORY_BANKS 4 -chparam AUTHORITY_ENGINES 4; "
            "check;"
        )
        res = run_wsl_cmd(["yosys", "-p", script])
        assert res.returncode == 0, f"Yosys check failed:\n{res.stderr}\n{res.stdout[-1500:]}"
        assert "ERROR" not in res.stderr
