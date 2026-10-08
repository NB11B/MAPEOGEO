# SPDX-License-Identifier: MIT
# MAPEOGEO Preproduction Fabric P0
# Qualification Test Suite: P0.1 - P0.4

import os
import subprocess
import pytest
from pathlib import Path
from fabric_p0.model.geo_reference import FixedPointModel, FixedCl20
from fabric_p0.model.geo_graph_reference import CSRGraphReference, GraphNode, GraphEdge

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def run_wsl_cmd(cmd_list):
    res = subprocess.run(["wsl"] + cmd_list, capture_output=True, text=True, cwd=str(REPO_ROOT))
    return res

def get_rtl_sources():
    rtl_dir = REPO_ROOT / 'fabric_p0' / 'rtl'
    defs = 'fabric_p0/rtl/common/geo_defs.svh'
    sv_files = sorted([p.relative_to(REPO_ROOT).as_posix() for p in rtl_dir.rglob('*.sv')])
    return [defs] + sv_files

class TestP01PrimitiveEquivalence:
    """P0.1 — Primitive operator equivalence across precision matrix and RTL."""

    @pytest.mark.parametrize("frac_bits", [1, 8, 16, 24, 30])
    def test_p01_parameterized_rtl_operators(self, frac_bits):
        """Compile and run operator qualification across FRAC_BITS in {1, 8, 16, 24, 30}."""
        src_files = [
            'fabric_p0/rtl/common/geo_defs.svh',
            'fabric_p0/rtl/operators/geo_fixed_arith.sv',
            'fabric_p0/rtl/operators/geo_cl20_multivector.sv',
            'fabric_p0/rtl/operators/geo_unary_ops.sv',
            'fabric_p0/rtl/operators/geo_bilinear_ops.sv',
            'fabric_p0/rtl/operators/geo_matrix_bridge.sv',
            'fabric_p0/rtl/operators/geo_operator_unit.sv',
            'fabric_p0/sim/tb_geo_operators.sv'
        ]
        vvp_path = f"/tmp/tb_ops_q{frac_bits}.vvp"
        
        compile_cmd = [
            "iverilog", "-g2012",
            "-Ifabric_p0/rtl/common",
            f"-Ptb_geo_operators.FRAC={frac_bits}",
            "-o", vvp_path
        ] + src_files

        comp_res = run_wsl_cmd(compile_cmd)
        assert comp_res.returncode == 0, f"iverilog compilation failed for FRAC={frac_bits}:\n{comp_res.stderr}"

        # Run simulation
        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed for FRAC={frac_bits}:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS ALL OPERATOR QUALIFICATION TESTS" in sim_res.stdout

    def test_p01_python_reference_model_algebra(self):
        """Verify Python golden model matches Cl(2,0) and M2(R) isomorphism."""
        model = FixedPointModel(width=32, frac=16)
        one = 1 << 16

        # e1 * e2 = e12
        e1 = FixedCl20(0, one, 0, 0)
        e2 = FixedCl20(0, 0, one, 0)
        prod, ovf = model.cl20_mul(e1, e2)
        assert not ovf
        assert prod == FixedCl20(0, 0, 0, one)

        # e2 * e1 = -e12
        prod2, ovf2 = model.cl20_mul(e2, e1)
        assert not ovf2
        assert prod2 == FixedCl20(0, 0, 0, -one)

        # Commutator [e1, e2] = e12
        comm, c_ovf = model.commutator(e1, e2)
        assert not c_ovf
        assert comm == FixedCl20(0, 0, 0, one)

        # Anticommutator {e1, e1} = 1
        acomm, a_ovf = model.anticommutator(e1, e1)
        assert not a_ovf
        assert acomm == FixedCl20(one, 0, 0, 0)

        # Matrix bridge round-trip
        # A = [3, 1; 2, 5]
        mv = model.matrix_to_cl20(3 << 16, 1 << 16, 2 << 16, 5 << 16)
        mat, m_ovf = model.cl20_to_matrix(mv)
        assert not m_ovf
        assert mat == (3 << 16, 1 << 16, 2 << 16, 5 << 16)


class TestP02AutonomousExecution:
    """P0.2 — Autonomous single-UoW execution and zero-mutation guarantee."""

    def test_p02_autonomous_single_uow(self):
        """Execute autonomous boot, UoW dispatch, commit, evidence append, and zero-mutation check."""
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
            'fabric_p0/sim/tb_single_uow.sv'
        ]
        vvp_path = "/tmp/tb_single_uow.vvp"

        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-Ifabric_p0/rtl/common", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "Autonomous boot completed successfully" in sim_res.stdout
        assert "Received autonomous egress signal: UoW=101, status=0" in sim_res.stdout
        assert "Chained root updated" in sim_res.stdout
        assert "Zero-mutation guarantee confirmed: Delta S == 0" in sim_res.stdout
        assert "PASS AUTONOMOUS SINGLE-UoW EXECUTION QUALIFICATION" in sim_res.stdout


class TestP03ConcurrentExecution:
    """P0.3 — Concurrent UoW execution & physical timing / ordering invariance."""

    def test_p03_concurrency_and_reordering_invariance(self):
        """Execute concurrent independent and dependent UoWs under permuted ordering."""
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
            'fabric_p0/sim/tb_concurrent_uow.sv'
        ]
        vvp_path = "/tmp/tb_concurrent_uow.vvp"

        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-Ifabric_p0/rtl/common", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "Terminal states match exactly: S_f^(1) == S_f^(2)" in sim_res.stdout
        assert "PASS CONCURRENT UoW EXECUTION QUALIFICATION" in sim_res.stdout


class TestP04GraphSubsystem:
    """P0.4 — Native CSR graph subsystem and semantic neighborhood traversal."""

    def test_p04_python_graph_reference_model(self):
        """Verify Python golden model on frozen graph fixture."""
        ref = CSRGraphReference(max_nodes=256, max_edges=1024)
        nodes = [
            GraphNode(0, 0, 1, 1, 1),   # Node 0: 0 edges
            GraphNode(0, 1, 2, 1, 1),   # Node 1: 1 edge -> 2
            GraphNode(1, 3, 3, 1, 1),   # Node 2: 3 edges -> 3, 4, 5
            GraphNode(4, 2, 4, 1, 1),   # Node 3: 2 edges -> 6, 6
            GraphNode(6, 1, 4, 1, 1),   # Node 4: 1 edge -> 7
            GraphNode(7, 1, 4, 1, 1),   # Node 5: 1 edge -> 1 (cycle)
            GraphNode(8, 1, 5, 1, 1),   # Node 6: 1 edge -> 8
            GraphNode(9, 1, 5, 1, 1),   # Node 7: 1 edge -> 9
            GraphNode(10, 1, 6, 1, 1),  # Node 8: 1 edge -> 10
            GraphNode(11, 0, 7, 1, 1),  # Node 9: 0 edges
            GraphNode(11, 0, 7, 1, 1),  # Node 10: 0 edges
            GraphNode(11, 1, 8, 1, 1),  # Node 11: 1 edge -> 999 (malformed)
        ]
        edges = [
            GraphEdge(2, 0x10, 0),      # Edge 0 (from 1)
            GraphEdge(3, 0x10, 0),      # Edge 1 (from 2)
            GraphEdge(4, 0x20, 0),      # Edge 2 (from 2)
            GraphEdge(5, 0x30, 0),      # Edge 3 (from 2)
            GraphEdge(6, 0x10, 0),      # Edge 4 (from 3)
            GraphEdge(6, 0x20, 0),      # Edge 5 (from 3)
            GraphEdge(7, 0x20, 0),      # Edge 6 (from 4)
            GraphEdge(1, 0x10, 0),      # Edge 7 (from 5 -> cycle back to 1)
            GraphEdge(8, 0x10, 0),      # Edge 8 (from 6)
            GraphEdge(9, 0x20, 0),      # Edge 9 (from 7)
            GraphEdge(10, 0x10, 0),     # Edge 10 (from 8)
            GraphEdge(999, 0x10, 0),    # Edge 11 (from 11 -> malformed)
        ]
        ref.load_graph(nodes, edges)

        # Radii parity tests from Node 1
        nb1, err1, _ = ref.neighborhood(1, radius=1)
        assert not err1 and [n[0] for n in nb1] == [2]

        nb2, err2, _ = ref.neighborhood(1, radius=2)
        assert not err2 and [n[0] for n in nb2] == [2, 3, 4, 5]

        nb3, err3, _ = ref.neighborhood(1, radius=3)
        assert not err3 and [n[0] for n in nb3] == [2, 3, 4, 5, 6, 7]

        # Relation filtered
        nb_r1, err_r1, _ = ref.neighborhood(1, radius=3, relation_filter=0x10)
        assert not err_r1 and [n[0] for n in nb_r1] == [2, 3, 6]

        # Zero-edge
        nb0, _, _ = ref.neighborhood(0, radius=2)
        assert len(nb0) == 0

        # Malformed
        _, _, malformed = ref.neighborhood(11, radius=1)
        assert malformed

    def test_p04_rtl_graph_memory_simulation(self):
        """Compile and run tb_geo_graph_memory.sv under Icarus Verilog."""
        src_files = [
            'fabric_p0/rtl/common/geo_defs.svh',
            'fabric_p0/rtl/graph/geo_graph_memory.sv',
            'fabric_p0/sim/tb_geo_graph_memory.sv'
        ]
        vvp_path = "/tmp/tb_graph_mem.vvp"

        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-Ifabric_p0/rtl/common", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "NEIGHBORHOOD r=1: 1 hit" in sim_res.stdout
        assert "NEIGHBORHOOD r=2: 4 hits" in sim_res.stdout
        assert "NEIGHBORHOOD r=3: 6 hits" in sim_res.stdout
        assert "DETERMINISTIC ORDER: Identical traversal order" in sim_res.stdout
        assert "RELATION-FILTERED NEIGHBORHOOD: Filtered path" in sim_res.stdout
        assert "BOUNDS CHECK: Out-of-bounds start_node=300" in sim_res.stdout
        assert "MALFORMED TARGET: Malformed target=999" in sim_res.stdout
        assert "PASS ALL NATIVE GRAPH MEMORY QUALIFICATION TESTS" in sim_res.stdout


class TestP05GraphWork:
    """P0.5 — Native graph-derived work lifecycle, E9-shaped traversal, and scaling invariance."""

    def test_p05_native_graph_work_simulation(self):
        """Execute autonomous E9-shaped graph traversal, graph conditions, and scaling invariance."""
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
            'fabric_p0/sim/tb_graph_work.sv'
        ]
        vvp_path = "/tmp/tb_graph_work.vvp"

        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-Ifabric_p0/rtl/common", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "Autonomous boot completed" in sim_res.stdout
        assert "Zero-Mutation Guarantee confirmed: Canary State[10] unmutated" in sim_res.stdout or "Confirmed: Canary State[10] unmutated" in sim_res.stdout
        assert "Parity Ratio: 17 / 17 = 1.0 (Strictly invariant to |G|!)" in sim_res.stdout or "Strictly invariant to |G|!" in sim_res.stdout
        assert "PASS P0.5 NATIVE GRAPH WORK QUALIFICATION" in sim_res.stdout


class TestP06E7HardwareWorkload:
    """P0.6 — E7 32,768 hardware workload, dual compositions, and kappa-collision vs oriented separation."""

    def test_p06_e7_hardware_workload_simulation(self):
        """Execute autonomous hardware workload generator on projector triples."""
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
            'fabric_p0/rtl/work_fabric/geo_e7_work_generator.sv',
            'fabric_p0/sim/tb_e7_workload.sv'
        ]
        vvp_path = "/tmp/tb_e7_workload.vvp"

        # Test with 64 triples
        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-Ifabric_p0/rtl/common", "-DCFG_TOTAL_TRIPLES=64", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "Autonomous boot completed" in sim_res.stdout
        assert "Triples Completed            : 64" in sim_res.stdout
        assert "Oriented Separations Seen" in sim_res.stdout
        assert "Kappa Collisions Detected" in sim_res.stdout
        assert "PASS P0.6 E7 HARDWARE WORKLOAD QUALIFICATION" in sim_res.stdout

    def test_p06_architecture_scaling_sweep(self):
        """Execute architecture scaling sweep across work cell counts N_workcell in {1, 2, 4, 8}."""
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
            'fabric_p0/rtl/work_fabric/geo_e7_work_generator.sv',
            'fabric_p0/sim/tb_e7_workload.sv'
        ]

        sweep_results = {}
        for n_cells in [1, 2, 4, 8]:
            vvp_path = f"/tmp/tb_e7_sweep_{n_cells}.vvp"
            comp_res = run_wsl_cmd([
                "iverilog", "-g2012", "-Ifabric_p0/rtl/common",
                f"-DCFG_WORK_CELL_COUNT={n_cells}",
                "-DCFG_TOTAL_TRIPLES=32",
                "-o", vvp_path
            ] + src_files)
            assert comp_res.returncode == 0, f"Compilation failed for N={n_cells}:\n{comp_res.stderr}"

            sim_res = run_wsl_cmd(["vvp", vvp_path])
            assert sim_res.returncode == 0, f"Simulation failed for N={n_cells}:\n{sim_res.stderr}\n{sim_res.stdout}"
            assert "PASS P0.6 E7 HARDWARE WORKLOAD QUALIFICATION" in sim_res.stdout
            sweep_results[n_cells] = sim_res.stdout

        assert len(sweep_results) == 4

    def test_p06b_exhaustive_e7_completion(self):
        """P0.6B — Exhaustive E7 qualification: run complete 32,768 triples (or 1024 baseline) with zero dropped work and evidence."""
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
            'fabric_p0/rtl/work_fabric/geo_e7_work_generator.sv',
            'fabric_p0/sim/tb_e7_workload.sv'
        ]
        triples = int(os.environ.get("P06B_TRIPLES", "1024"))
        vvp_path = f"/tmp/tb_e7_exhaustive_{triples}.vvp"

        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-Ifabric_p0/rtl/common", f"-DCFG_TOTAL_TRIPLES={triples}", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert f"Triples Completed            : {triples}" in sim_res.stdout
        assert "Telemetry UoW Rejected       : 0" in sim_res.stdout
        assert "Oriented Separations Seen" in sim_res.stdout
        assert "Kappa Collisions Detected" in sim_res.stdout
        assert "PASS P0.6 E7 HARDWARE WORKLOAD QUALIFICATION" in sim_res.stdout


class TestP07AutonomousClosure:
    """P0.7 — Autonomous E10 Bounded Universe Closure."""

    def test_p07_autonomous_e10_closure(self):
        """Execute autonomous E10 bounded closure in RTL: discover -> execute -> certify -> commit -> CLOSED_BOUNDED_UNIVERSE."""
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
            'fabric_p0/sim/tb_e10_closure.sv'
        ]
        vvp_path = "/tmp/tb_e10_closure.vvp"

        # 1. Full Autonomous Closure (20 probes, full rank 6, K^T K = 6*I + 4*J)
        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-Ifabric_p0/rtl/common", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "Closure Disposition          : CLOSED_BOUNDED_UNIVERSE" in sim_res.stdout
        assert "Closure Reached Flag         : 1" in sim_res.stdout
        assert "Probes Committed             : 20" in sim_res.stdout
        assert "Graph Edges Mutated          : 20" in sim_res.stdout
        assert "Incidence Matrix Diag Sum    : 60" in sim_res.stdout
        assert "Incidence Matrix Offdiag Sum : 120" in sim_res.stdout
        assert "Telemetry UoW Committed      : 40" in sim_res.stdout
        assert "Telemetry UoW Rejected       : 0" in sim_res.stdout
        assert "PASS P0.7 AUTONOMOUS E10 BOUNDED CLOSURE QUALIFICATION" in sim_res.stdout

    def test_p07_e10_restricted_nullity_detection(self):
        """Verify negative test: restricted family missing element 5 detects explicit null space and refuses false closure."""
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
            'fabric_p0/sim/tb_e10_closure.sv'
        ]
        vvp_path = "/tmp/tb_e10_nullity.vvp"

        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-Ifabric_p0/rtl/common", "-DCFG_RESTRICT_NULLITY=1", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "Closure Reached Flag         : 0" in sim_res.stdout
        assert "Probes Committed             : 10" in sim_res.stdout
        assert "PASS P0.7 E10 RESTRICTED NULLITY DETECTION (EXPLICIT NULL SPACE)" in sim_res.stdout


class TestP0SynthesisNeutrality:
    """Verify vendor-neutral synthesis clean check with Yosys."""

    def test_p0_yosys_synthesis_check(self):
        """Run Yosys elaboration and synthesis hierarchy check on top-level fabric, graph subsystem, E7 generator, and E10 closure engine."""
        # 1. Elaboration and check on top-level fabric (including graph subsystem)
        yosys_script_fabric = (
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/common/geo_defs.svh; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/operators/geo_fixed_arith.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/operators/geo_cl20_multivector.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/operators/geo_unary_ops.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/operators/geo_bilinear_ops.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/operators/geo_matrix_bridge.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/operators/geo_operator_unit.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/compute/geo_general_alu.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/memory/geo_state_memory.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/authority/geo_authority_engine.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/evidence/geo_evidence_engine.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/graph/geo_graph_memory.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/work_fabric/geo_work_cell.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/work_fabric/geo_work_fabric.sv; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/top/mapeogeo_p0_fabric.sv; "
            "hierarchy -top mapeogeo_p0_fabric; "
            "check;"
        )
        res_fabric = run_wsl_cmd(["yosys", "-p", yosys_script_fabric])
        assert res_fabric.returncode == 0, f"Yosys fabric check failed:\n{res_fabric.stderr}\n{res_fabric.stdout[-1500:]}"
        assert "ERROR" not in res_fabric.stderr

        # 2. Elaboration and check on native CSR graph memory
        yosys_script_graph = (
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/common/geo_defs.svh; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/graph/geo_graph_memory.sv; "
            "hierarchy -top geo_graph_memory; "
            "check;"
        )
        res_graph = run_wsl_cmd(["yosys", "-p", yosys_script_graph])
        assert res_graph.returncode == 0, f"Yosys graph check failed:\n{res_graph.stderr}\n{res_graph.stdout[-1500:]}"
        assert "ERROR" not in res_graph.stderr

        # 3. Elaboration and check on E7 hardware workload generator
        yosys_script_e7 = (
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/common/geo_defs.svh; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/work_fabric/geo_e7_work_generator.sv; "
            "hierarchy -top geo_e7_work_generator; "
            "check;"
        )
        res_e7 = run_wsl_cmd(["yosys", "-p", yosys_script_e7])
        assert res_e7.returncode == 0, f"Yosys E7 generator check failed:\n{res_e7.stderr}\n{res_e7.stdout[-1500:]}"
        assert "ERROR" not in res_e7.stderr

        # 4. Elaboration and check on E10 autonomous closure engine
        yosys_script_e10 = (
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/common/geo_defs.svh; "
            "read_verilog -sv -Ifabric_p0/rtl/common fabric_p0/rtl/work_fabric/geo_e10_closure_engine.sv; "
            "hierarchy -top geo_e10_closure_engine; "
            "check;"
        )
        res_e10 = run_wsl_cmd(["yosys", "-p", yosys_script_e10])
        assert res_e10.returncode == 0, f"Yosys E10 closure engine check failed:\n{res_e10.stderr}\n{res_e10.stdout[-1500:]}"
        assert "ERROR" not in res_e10.stderr


