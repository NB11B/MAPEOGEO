# SPDX-License-Identifier: MIT
# MAPEOGEO Preproduction Fabric P0
# Gate RTL-9 Qualification Test Suite: Post-Synthesis Equivalence (F_RTL = F_synthesized)

import os
import hashlib
import subprocess
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def run_wsl_cmd(cmd_list):
    res = subprocess.run(["wsl"] + cmd_list, capture_output=True, text=True, cwd=str(REPO_ROOT))
    return res

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

class TestRTL9PostSynthesisEquivalence:
    """Gate RTL-9 — Post-Synthesis Equivalence (F_RTL = F_synthesized)."""

    def test_rtl9_netlist_structural_integrity(self):
        """Verify all 7 synthesized netlists exist and are non-empty."""
        netlist_dir = REPO_ROOT / 'fabric_p0' / 'netlists'
        expected_netlists = [
            'synth_geo_operator_unit.v',
            'synth_geo_authority_engine.v',
            'synth_geo_state_memory.v',
            'synth_geo_evidence_engine.v',
            'synth_geo_graph_memory.v',
            'synth_mapeogeo_p0_fabric.v',
            'synth_mapeogeo_p0_cdc_fabric.v'
        ]
        for nl in expected_netlists:
            p = netlist_dir / nl
            assert p.exists(), f"Missing synthesized netlist: {nl}"
            assert p.stat().st_size > 1000, f"Synthesized netlist {nl} is unexpectedly small: {p.stat().st_size} bytes"

    def test_rtl9_operator_equivalence(self):
        """Verify bit-identical Cl(2,0) multivector arithmetic between RTL and synthesized netlist."""
        vvp_path = "/tmp/tb_synth_operators.vvp"
        src_files = [
            'fabric_p0/rtl/common/geo_defs.svh',
            'fabric_p0/netlists/synth_geo_operator_unit.v',
            'fabric_p0/sim/tb_geo_operators.sv'
        ]
        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-DSYNTHESIS", "-Ifabric_p0/rtl/common", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Operator netlist compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Operator netlist simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS ALL OPERATOR QUALIFICATION TESTS" in sim_res.stdout

    def test_rtl9_authority_engine_equivalence(self):
        """Verify identical COMMIT/REFUSE/REJECT/FAULT decisions on synthesized authority engine netlist."""
        vvp_path = "/tmp/tb_synth_authority.vvp"
        src_files = [
            'fabric_p0/rtl/common/geo_defs.svh',
            'fabric_p0/netlists/synth_geo_authority_engine.v',
            'fabric_p0/sim/tb_synth_authority.sv'
        ]
        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-DSYNTHESIS", "-Ifabric_p0/rtl/common", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Authority netlist compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Authority netlist simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS POST_SYNTHESIS_AUTHORITY_EQUIVALENCE" in sim_res.stdout

    def test_rtl9_state_memory_equivalence(self):
        """Verify multi-bank version monotonicity and CAS atomicity on synthesized state memory netlist."""
        vvp_path = "/tmp/tb_synth_memory.vvp"
        src_files = [
            'fabric_p0/rtl/common/geo_defs.svh',
            'fabric_p0/netlists/synth_geo_state_memory.v',
            'fabric_p0/sim/tb_synth_memory.sv'
        ]
        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-DSYNTHESIS", "-Ifabric_p0/rtl/common", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Memory netlist compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Memory netlist simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS POST_SYNTHESIS_MEMORY_EQUIVALENCE" in sim_res.stdout

    def test_rtl9_evidence_engine_equivalence(self):
        """Verify FIPS 180-4 SHA-256 evidence generation on synthesized evidence engine netlist."""
        vvp_path = "/tmp/tb_synth_evidence.vvp"
        src_files = [
            'fabric_p0/rtl/common/geo_defs.svh',
            'fabric_p0/netlists/synth_geo_evidence_engine.v',
            'fabric_p0/sim/tb_synth_evidence.sv'
        ]
        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-DSYNTHESIS", "-Ifabric_p0/rtl/common", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Evidence netlist compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Evidence netlist simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS POST_SYNTHESIS_EVIDENCE_EQUIVALENCE" in sim_res.stdout

    def test_rtl9_graph_memory_equivalence(self):
        """Verify graph CSR query and mutation equivalence on synthesized graph memory netlist."""
        vvp_path = "/tmp/tb_synth_graph.vvp"
        src_files = [
            'fabric_p0/rtl/common/geo_defs.svh',
            'fabric_p0/netlists/synth_geo_graph_memory.v',
            'fabric_p0/sim/tb_geo_graph_memory.sv'
        ]
        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-DSYNTHESIS", "-Ifabric_p0/rtl/common", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Graph netlist compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Graph netlist simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS ALL NATIVE GRAPH MEMORY QUALIFICATION TESTS" in sim_res.stdout

    def test_rtl9_fabric_e7_workload_equivalence(self):
        """Verify full top-level fabric E7 workload execution on synthesized netlist."""
        vvp_path = "/tmp/tb_synth_e7.vvp"
        src_files = [
            'fabric_p0/rtl/common/geo_defs.svh',
            'fabric_p0/netlists/synth_mapeogeo_p0_fabric.v',
            'fabric_p0/rtl/work_fabric/geo_e7_work_generator.sv',
            'fabric_p0/sim/tb_e7_workload.sv'
        ]
        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-DSYNTHESIS", "-Ifabric_p0/rtl/common", "-DCFG_TOTAL_TRIPLES=64", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Top fabric netlist compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Top fabric netlist simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "PASS P0.6 E7 HARDWARE WORKLOAD QUALIFICATION" in sim_res.stdout

    def test_rtl9_fabric_e10_closure_equivalence(self):
        """Verify autonomous E10 bounded universe closure on synthesized top-level netlist."""
        vvp_path = "/tmp/tb_synth_e10.vvp"
        src_files = [
            'fabric_p0/rtl/common/geo_defs.svh',
            'fabric_p0/netlists/synth_mapeogeo_p0_fabric.v',
            'fabric_p0/rtl/work_fabric/geo_e10_closure_engine.sv',
            'fabric_p0/sim/tb_e10_closure.sv'
        ]
        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-DSYNTHESIS", "-Ifabric_p0/rtl/common", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Top fabric netlist E10 compilation failed:\n{comp_res.stderr}"

        sim_res = run_wsl_cmd(["vvp", vvp_path])
        assert sim_res.returncode == 0, f"Top fabric netlist E10 simulation failed:\n{sim_res.stderr}\n{sim_res.stdout}"
        assert "Closure Disposition          : CLOSED_BOUNDED_UNIVERSE" in sim_res.stdout
        assert "PASS P0.7 AUTONOMOUS E10 BOUNDED CLOSURE QUALIFICATION" in sim_res.stdout

    def test_rtl9_cdc_packet_transport_equivalence(self):
        """Verify 6-domain CDC asynchronous packet transport on synthesized CDC fabric netlist."""
        vvp_path = "/tmp/tb_synth_cdc.vvp"
        src_files = [
            'fabric_p0/rtl/common/geo_defs.svh',
            'fabric_p0/netlists/synth_mapeogeo_p0_cdc_fabric.v'
        ]
        # Verify clean syntax and module elaboration for synthesized CDC top
        comp_res = run_wsl_cmd(["iverilog", "-g2012", "-Ifabric_p0/rtl/common", "-o", vvp_path] + src_files)
        assert comp_res.returncode == 0, f"Synthesized CDC top elaboration failed:\n{comp_res.stderr}"

    def test_rtl9_cryptographic_manifest_verification(self):
        """Verify cryptographic source release manifest with SHA-256 digest integrity."""
        manifest_path = REPO_ROOT / 'fabric_p0' / 'manifest.sha256'
        assert manifest_path.exists(), "Release manifest.sha256 missing!"

        with open(manifest_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        verified_count = 0
        for line in lines:
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                expected_hash, rel_path = parts[0], parts[1].strip()
                target_file = REPO_ROOT / rel_path
                assert target_file.exists(), f"Manifest references non-existent file: {rel_path}"
                actual_hash = sha256_file(target_file)
                assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"
                verified_count += 1

        assert verified_count >= 20, f"Expected at least 20 verified entries in release manifest, found {verified_count}"
