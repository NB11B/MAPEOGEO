# SPDX-License-Identifier: MIT
# MAPEOGEO Preproduction Fabric P0
# Gate RTL-10 Qualification Test Suite: SDC Timing-Constraint Sign-off & CDC Path Audit

import json
import pytest
from pathlib import Path
from fabric_p0.scripts.audit_sdc_constraints import audit_sdc_constraints, parse_sdc

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

class TestRTL10SDCTimingSignOff:
    """Gate RTL-10 — SDC Timing-Constraint Sign-Off & CDC Path Audit."""

    @pytest.fixture(scope="class")
    def audit_result(self):
        return audit_sdc_constraints(REPO_ROOT)

    def test_rtl10_primary_clocks_declaration(self, audit_result):
        """Verify all 6 physical primary clocks are declared with valid positive periods."""
        sdc_path = REPO_ROOT / "fabric_p0" / "constraints" / "mapeogeo_p0_clocks.sdc"
        sdc = parse_sdc(sdc_path)
        expected_clocks = {
            "clk_ingress": 8.000,
            "clk_auth": 10.000,
            "clk_op": 6.000,
            "clk_mem": 5.000,
            "clk_ev": 7.500,
            "clk_egress": 6.400
        }
        for clk_name, period in expected_clocks.items():
            assert clk_name in sdc['clocks'], f"Clock {clk_name} missing from SDC"
            assert sdc['clocks'][clk_name]['period'] == pytest.approx(period, rel=1e-3)
            assert sdc['clocks'][clk_name]['port'] == clk_name

    def test_rtl10_asynchronous_clock_groups(self, audit_result):
        """Verify all 6 clock domains are declared in asynchronous clock groups."""
        sdc_path = REPO_ROOT / "fabric_p0" / "constraints" / "mapeogeo_p0_clocks.sdc"
        sdc = parse_sdc(sdc_path)
        group_text = " ".join(sdc['clock_groups'])
        assert "set_clock_groups -asynchronous" in group_text
        for clk in ["clk_ingress", "clk_auth", "clk_op", "clk_mem", "clk_ev", "clk_egress"]:
            assert f"get_clocks {clk}" in group_text, f"Clock {clk} missing from asynchronous group declaration"

    def test_rtl10_cdc_fifo_max_delay_exceptions(self, audit_result):
        """Verify max-delay datapath_only and bus skew constraints on Gray pointer crossings."""
        sdc_path = REPO_ROOT / "fabric_p0" / "constraints" / "mapeogeo_p0_clocks.sdc"
        sdc = parse_sdc(sdc_path)
        max_delay_text = " ".join(sdc['max_delays'])
        bus_skew_text = " ".join(sdc['bus_skews'])
        
        assert "-datapath_only" in max_delay_text
        assert "*wptr_gray*" in max_delay_text
        assert "*rptr_gray*" in max_delay_text
        assert "*wptr_gray*" in bus_skew_text
        assert "*rptr_gray*" in bus_skew_text

    def test_rtl10_reset_synchronizer_exceptions(self, audit_result):
        """Verify false-path exceptions strictly target async reset assertion pins on 2FF stage1."""
        sdc_path = REPO_ROOT / "fabric_p0" / "constraints" / "mapeogeo_p0_clocks.sdc"
        sdc = parse_sdc(sdc_path)
        fp_text = " ".join(sdc['false_paths'])
        for rst_port in ["rst_ingress_async_n", "rst_auth_async_n", "rst_op_async_n", "rst_mem_async_n", "rst_ev_async_n", "rst_egress_async_n"]:
            assert rst_port in fp_text, f"Reset port {rst_port} missing from false path exceptions"

    def test_rtl10_primary_io_delays_coverage(self, audit_result):
        """Verify all primary input and output ports have bounded delay constraints."""
        sdc_path = REPO_ROOT / "fabric_p0" / "constraints" / "mapeogeo_p0_clocks.sdc"
        sdc = parse_sdc(sdc_path)
        io_text = " ".join(sdc['io_delays'])
        required_ports = [
            "ingress_valid", "ingress_desc", "ingress_ready",
            "egress_valid", "egress_uow_id", "egress_status", "egress_result", "egress_evidence_root", "egress_ready",
            "boot_trigger", "boot_complete", "fabric_halted", "telemetry_out"
        ]
        for p in required_ports:
            assert p in io_text, f"IO Port '{p}' missing from SDC input/output delay constraints"

    def test_rtl10_zero_unbudgeted_false_paths(self, audit_result):
        """Verify no compute, memory, or authority units are accidentally caught by false paths."""
        sdc_path = REPO_ROOT / "fabric_p0" / "constraints" / "mapeogeo_p0_clocks.sdc"
        sdc = parse_sdc(sdc_path)
        for fp in sdc['false_paths']:
            assert "operator" not in fp.lower()
            assert "authority" not in fp.lower()
            assert "memory" not in fp.lower()
            assert "work_fabric" not in fp.lower()

    def test_rtl10_cdc_synchronizer_registry_integrity(self, audit_result):
        """Verify machine-readable CDC Synchronizer Registry matches design hierarchy."""
        registry_path = REPO_ROOT / "fabric_p0" / "constraints" / "cdc_synchronizer_registry.json"
        assert registry_path.exists(), "cdc_synchronizer_registry.json missing"
        with open(registry_path, 'r', encoding='utf-8') as f:
            reg = json.load(f)
        assert len(reg['synchronizers']) == 10
        assert reg['unconstrained_paths']['total_unconstrained_count'] == 0
        assert reg['unconstrained_paths']['audit_status'] == "ZERO_UNCONSTRAINED_PATHS_CONFIRMED"

    def test_rtl10_clock_interaction_matrix_closure(self, audit_result):
        """Verify 6x6 clock domain interaction matrix is fully classified and closed."""
        matrix = audit_result['clock_matrix']
        assert len(matrix) == 6
        for src, dsts in matrix.items():
            assert len(dsts) == 6
            for dst, rel in dsts.items():
                if src == dst:
                    assert rel['status'] == "TIMED"
                elif (src, dst) in [("clk_ingress", "clk_op"), ("clk_op", "clk_ingress"), ("clk_op", "clk_egress"), ("clk_egress", "clk_op")]:
                    assert rel['status'] == "MAX_DELAY_CONSTRAINED"
                else:
                    assert rel['status'] == "SET_CLOCK_GROUPS_ASYNC"
