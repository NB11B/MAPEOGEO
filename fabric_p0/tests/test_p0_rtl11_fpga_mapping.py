# SPDX-License-Identifier: MIT
"""
MAPEOGEO P0 Gate RTL-11 Test Suite: Vendor FPGA Technology Mapping & Capacity-Matched Sizing
=============================================================================================
Validates that:
  1. Submodule and top-level designs map cleanly to standard vendor FPGA primitives.
  2. Sizing database and qualification report are structurally complete and validated.
  3. Operating frequencies across all 6 asynchronous clock domains exceed SDC specifications (WNS >= 0).
  4. Commercial FPGA device fits (XCU280, Agilex 7, Kintex KU040) are mathematically verified.
  5. Sizing curves scale monotonically with spatial width (N_I, N_E, N_M, N_O, N_A, N_W).
  6. Capacity law R_fabric = min(N_I, N_E, N_M, N_O / 2, N_A) is satisfied across all configurations.
  7. Medium config satisfies True 4-Wide Machine: (N_I=4, N_E=4, N_M=8, N_O=8, N_A=4, N_W=16).
  8. Evidence subsystem eliminates DSP48E2 blocks to preserve DSP budget for geometric arithmetic (RTL-11B).
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FABRIC_DIR = os.path.join(REPO_ROOT, "fabric_p0")
REPORTS_DIR = os.path.join(FABRIC_DIR, "reports")
DB_PATH = os.path.join(REPORTS_DIR, "fpga_mapping_database.json")
REPORT_PATH = os.path.join(REPORTS_DIR, "rtl_11_fpga_mapping_report.md")


@pytest.fixture(scope="module")
def fpga_db():
    assert os.path.exists(DB_PATH), f"Database file not found at {DB_PATH}"
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


class TestRTL11FPGAMappingAndSizing:
    """Test suite for Gate RTL-11 FPGA Technology Mapping and Capacity-Matched Sizing."""

    def test_rtl11_database_and_report_integrity(self, fpga_db):
        """Verify presence, structure, and integrity of RTL-11 database and report."""
        assert os.path.exists(REPORT_PATH), "RTL-11 report markdown does not exist"
        assert fpga_db["metadata"]["gate"] == "RTL-11"
        assert "target_fpga_profiles" in fpga_db
        assert "sdc_clock_specifications" in fpga_db
        assert "submodule_technology_breakdown" in fpga_db
        assert "fabric_configurations" in fpga_db

        # Check that all 4 configurations exist
        for cfg in ["One_Wide", "Small", "Medium", "Full_Width"]:
            assert cfg in fpga_db["fabric_configurations"]

    def test_rtl11_vendor_primitive_mapping_validity(self, fpga_db):
        """Verify that submodules map to valid vendor FPGA cell types."""
        submods = fpga_db["submodule_technology_breakdown"]
        required_submods = [
            "geo_operator_unit",
            "geo_authority_engine",
            "geo_state_memory_bank",
            "geo_evidence_engine",
            "geo_graph_memory",
            "geo_work_cell",
            "geo_async_fifo",
            "geo_reset_sync"
        ]

        for mod_name in required_submods:
            assert mod_name in submods, f"Missing submodule {mod_name} in mapping breakdown"
            cells = submods[mod_name]["cells"]
            assert "LUTs" in cells and cells["LUTs"] >= 0
            assert "FFs" in cells and cells["FFs"] >= 0
            assert "DSP48E2" in cells and cells["DSP48E2"] >= 0

        # Operator unit must use DSP48E2 blocks for multivector multipliers
        assert submods["geo_operator_unit"]["cells"]["DSP48E2"] == 220
        # Authority engine is purely logic/control: 0 DSPs
        assert submods["geo_authority_engine"]["cells"]["DSP48E2"] == 0
        # Evidence engine uses 0 DSP blocks (RTL-11B DSP-free mixing hardening)
        assert submods["geo_evidence_engine"]["cells"]["DSP48E2"] == 0

    def test_rtl11_true_1wide_artix7_demonstration_geometry(self, fpga_db):
        """Verify that the One_Wide demonstration configuration satisfies the Artix-7 capacity budget (N_O=2, 440 DSPs)."""
        one_cfg = fpga_db["fabric_configurations"]["One_Wide"]
        geo = one_cfg["geometry"]
        assert geo["N_I"] == 1
        assert geo["N_E"] == 1
        assert geo["N_M"] >= 1
        assert geo["N_O"] == 2, f"True 1-wide machine requires N_O=2 operator lanes, got {geo['N_O']}"
        assert geo["N_A"] == 1
        assert geo["N_W"] >= 4

        # Measured capacity law: R_fabric = min(N_I, N_E, N_M, N_O / 2, N_A)
        r_sustained = min(geo["N_I"], geo["N_E"], geo["N_M"], geo["N_O"] / 2.0, geo["N_A"])
        assert r_sustained == 1.0, f"Expected sustained rate 1.0 UoW/cycle, got {r_sustained}"

        # Check DSP count is 440
        assert one_cfg["primitive_cell_counts"]["DSP48E2"] == 440

        # Check Artix-7 XC7A200T fit
        a7_util = one_cfg["device_utilization_matrix"]["Xilinx_Artix7_XC7A200T"]
        assert a7_util["fits_in_device"] is True
        assert a7_util["dsp_util_pct"] <= 60.0  # 440 / 740 = 59.46%
        assert a7_util["lut_util_pct"] <= 35.0  # ~31.6%

    def test_rtl11_true_4wide_demonstration_geometry(self, fpga_db):
        """Verify that the Medium demonstration configuration satisfies the true 4-wide capacity law (N_O=8)."""
        med_cfg = fpga_db["fabric_configurations"]["Medium"]
        geo = med_cfg["geometry"]
        assert geo["N_I"] == 4
        assert geo["N_E"] == 4
        assert geo["N_M"] >= 4
        assert geo["N_O"] == 8, f"True 4-wide machine requires N_O=8 operator lanes, got {geo['N_O']}"
        assert geo["N_A"] == 4
        assert geo["N_W"] == 16

        # Measured capacity law: R_fabric = min(N_I, N_E, N_M, N_O / 2, N_A)
        r_sustained = min(geo["N_I"], geo["N_E"], geo["N_M"], geo["N_O"] / 2.0, geo["N_A"])
        assert r_sustained == 4.0, f"Expected sustained rate 4.0 UoW/cycle, got {r_sustained}"

    def test_rtl11_submodule_fmax_meets_sdc_specs(self, fpga_db):
        """Verify each submodule's achievable Fmax meets its SDC domain specification."""
        submods = fpga_db["submodule_technology_breakdown"]
        sdc_specs = fpga_db["sdc_clock_specifications"]

        for mod_name, mod_data in submods.items():
            domain = mod_data["domain"]
            if domain in sdc_specs:
                target_fmax = sdc_specs[domain]["target_freq_mhz"]
                achieved_fmax = mod_data["fmax_mhz"]
                assert achieved_fmax >= target_fmax, (
                    f"Submodule {mod_name} Fmax ({achieved_fmax} MHz) violates domain "
                    f"{domain} target ({target_fmax} MHz)"
                )

    def test_rtl11_timing_closure_all_domains(self, fpga_db):
        """Verify that all 6 asynchronous clock domains achieve positive slack (WNS >= 0, TNS == 0)."""
        configs = fpga_db["fabric_configurations"]
        sdc_specs = fpga_db["sdc_clock_specifications"]

        for cfg_name, cfg_data in configs.items():
            timing = cfg_data["timing_domain_metrics"]
            for clk_name, clk_spec in sdc_specs.items():
                assert clk_name in timing, f"Missing clock {clk_name} in config {cfg_name}"
                wns = timing[clk_name]["wns_ns"]
                tns = timing[clk_name]["tns_ns"]
                fmax = timing[clk_name]["fmax_mhz"]

                assert wns >= 0.0, f"Config {cfg_name} clock {clk_name} has negative WNS ({wns} ns)"
                assert tns == 0.0, f"Config {cfg_name} clock {clk_name} has non-zero TNS ({tns} ns)"
                assert fmax >= clk_spec["target_freq_mhz"], (
                    f"Config {cfg_name} clock {clk_name} Fmax {fmax} MHz < target {clk_spec['target_freq_mhz']} MHz"
                )

    def test_rtl11_fpga_device_capacity_fit(self, fpga_db):
        """Verify device capacity utilization against enterprise datacenter and benchtop targets."""
        configs = fpga_db["fabric_configurations"]

        # One_Wide Config must fit on Artix-7 XC7A200T (< 35% LUTs, < 60% DSPs)
        one_a7 = configs["One_Wide"]["device_utilization_matrix"]["Xilinx_Artix7_XC7A200T"]
        assert one_a7["fits_in_device"] is True
        assert one_a7["lut_util_pct"] < 35.0
        assert one_a7["dsp_util_pct"] < 60.0

        # Small Config must fit on XCU280 (< 10% LUTs) and Agilex 7 (< 10% ALMs)
        small_u280 = configs["Small"]["device_utilization_matrix"]["Xilinx_Alveo_U280"]
        assert small_u280["fits_in_device"] is True
        assert small_u280["lut_util_pct"] < 10.0

        # Medium True 4-Wide Config must fit on XCU280 (< 20% LUTs, < 25% DSPs) and Kintex KU040
        med_u280 = configs["Medium"]["device_utilization_matrix"]["Xilinx_Alveo_U280"]
        assert med_u280["fits_in_device"] is True
        assert med_u280["lut_util_pct"] < 20.0
        assert med_u280["dsp_util_pct"] < 25.0

        med_ku040 = configs["Medium"]["device_utilization_matrix"]["Xilinx_Kintex_KU040"]
        assert med_ku040["fits_in_device"] is True

        # Full-Width Config must fit on single XCU280 card (< 30% LUTs, < 45% DSPs)
        full_u280 = configs["Full_Width"]["device_utilization_matrix"]["Xilinx_Alveo_U280"]
        assert full_u280["fits_in_device"] is True
        assert full_u280["lut_util_pct"] <= 30.0
        assert full_u280["dsp_util_pct"] <= 45.0

    def test_rtl11_resource_scaling_monotonicity(self, fpga_db):
        """Verify monotonic scaling of physical resources with increasing fabric width."""
        c_one = fpga_db["fabric_configurations"]["One_Wide"]["primitive_cell_counts"]
        c_small = fpga_db["fabric_configurations"]["Small"]["primitive_cell_counts"]
        c_med = fpga_db["fabric_configurations"]["Medium"]["primitive_cell_counts"]
        c_full = fpga_db["fabric_configurations"]["Full_Width"]["primitive_cell_counts"]

        # LUT scaling: One < Small < Medium < Full
        assert c_one["LUTs"] < c_small["LUTs"] < c_med["LUTs"] < c_full["LUTs"]

        # Flip-Flop scaling: One < Small < Medium < Full
        assert c_one["FFs"] < c_small["FFs"] < c_med["FFs"] < c_full["FFs"]

        # DSP scaling: 440 (2 ops) -> 880 (4 ops) -> 1760 (8 ops) -> 3520 (16 ops) (100% geometric operator dedication)
        assert c_one["DSP48E2"] == 440
        assert c_small["DSP48E2"] == 880
        assert c_med["DSP48E2"] == 1760
        assert c_full["DSP48E2"] == 3520

    def test_rtl11_physical_throughput_scaling_linearity(self, fpga_db):
        """Verify physical throughput scaling achieves linear progression up to >= 1.33 GUoW/s."""
        tp_one = fpga_db["fabric_configurations"]["One_Wide"]["nominal_target_throughput_muow_s"]
        tp_small = fpga_db["fabric_configurations"]["Small"]["nominal_target_throughput_muow_s"]
        tp_med = fpga_db["fabric_configurations"]["Medium"]["nominal_target_throughput_muow_s"]
        tp_full = fpga_db["fabric_configurations"]["Full_Width"]["nominal_target_throughput_muow_s"]

        # 1-Wide Artix-7 baseline >= 120 MUoW/s
        assert tp_one >= 120.0

        # Baseline Small >= 330 MUoW/s
        assert tp_small >= 330.0

        # Medium achieves 2.0x scaling of Small (+- 5%)
        assert tp_med >= 1.95 * tp_small
        assert tp_med >= 660.0

        # Full-Width achieves 4.0x scaling of Small (+- 5%) and exceeds 1.33 GUoW/s (1330 MUoW/s)
        assert tp_full >= 3.90 * tp_small
        assert tp_full >= 1330.0

    def test_rtl11_evidence_engine_sha256_resource_budget(self, fpga_db):
        """Verify evidence engine SHA-256 DSP elimination and logic boundary."""
        ev_data = fpga_db["submodule_technology_breakdown"]["geo_evidence_engine"]
        assert ev_data["cells"]["DSP48E2"] == 0
        assert ev_data["cells"]["LUTs"] < 10000
        assert ev_data["cells"]["FFs"] < 5000
        assert ev_data["fmax_mhz"] >= 150.0
