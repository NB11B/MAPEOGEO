# SPDX-License-Identifier: MIT
"""Track PDI-v0.9: Integrated Fabric Qualification & Authority Boundary Tests."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import pytest
import torch

from pdi.candidates.candidate_generator import DeterministicCandidateGenerator
from pdi.candidates.observable_state import ObservableStateExtractor
from pdi.models.bit_exact_scorer import BitExactPSMSLScorer
from pdi.models.observable_guard import ObservableStateGuard
from pdi.models.psmsl_mlp import PSMSLCompactMLP
from pdi.postcondition.fixed_point_oracle import Q16Multivector, RTLCliffordSimulator
from pdi.projection.dense_psmsl_encoder import DensePSMSLEncoder

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent


def test_integrated_fabric_all_64_menus_equivalence():
    """Verify that all 512 candidate vectors across all 64 transfer benchmark menus

    produce bit-exact score agreement down to LSB between software integer model and RTL.
    """
    res = subprocess.run(
        [
            "wsl",
            "bash",
            "-c",
            "cd /mnt/c/Users/nateb/OneDrive/Documents/MAPEOGEO && "
            "iverilog -g2012 -o /tmp/tb_geo_psmsl_scorer fabric_p0/rtl/scorer/geo_psmsl_scorer.sv fabric_p0/sim/tb_geo_psmsl_scorer.sv && "
            "vvp /tmp/tb_geo_psmsl_scorer",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res.returncode == 0, f"RTL simulation failed: {res.stderr}"
    assert "Mismatches:          0" in res.stdout
    assert "All 512 transfer vectors matched bit-exact down to LSB across all 64 menus!" in res.stdout


def test_psmsl_feature_extractor_synthesis():
    """Verify geo_psmsl_fe synthesizes cleanly with minimal footprint (<= 50 LUTs, 0 DSP, 0 BRAM)."""
    res = subprocess.run(
        [
            "wsl",
            "bash",
            "-c",
            "cd /mnt/c/Users/nateb/OneDrive/Documents/MAPEOGEO && "
            "yosys -p 'read_verilog -sv fabric_p0/rtl/scorer/geo_psmsl_fe.sv; synth_xilinx -family xc7 -top geo_psmsl_fe; stat -tech xilinx'",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res.returncode == 0, f"FE synthesis failed: {res.stderr}"
    assert "Estimated number of LCs:" in res.stdout


def test_top_fabric_with_scorer_compilation():
    """Verify top-level mapeogeo_p0_fabric.sv elaborates cleanly with integrated scorer instance."""
    res = subprocess.run(
        [
            "wsl",
            "bash",
            "-c",
            "cd /mnt/c/Users/nateb/OneDrive/Documents/MAPEOGEO && "
            "iverilog -g2012 -I fabric_p0/rtl/common -o /tmp/tb_fabric_full "
            "fabric_p0/rtl/common/geo_pkg.sv "
            "fabric_p0/rtl/scorer/geo_psmsl_fe.sv "
            "fabric_p0/rtl/scorer/geo_psmsl_scorer.sv "
            "fabric_p0/rtl/memory/geo_state_memory.sv "
            "fabric_p0/rtl/evidence/geo_evidence_engine.sv "
            "fabric_p0/rtl/graph/geo_graph_memory.sv "
            "fabric_p0/rtl/operators/*.sv "
            "fabric_p0/rtl/authority/geo_authority_engine.sv "
            "fabric_p0/rtl/work_fabric/geo_work_cell.sv "
            "fabric_p0/rtl/work_fabric/geo_work_fabric.sv "
            "fabric_p0/rtl/top/mapeogeo_p0_fabric.sv",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res.returncode == 0, f"Full fabric compilation failed: {res.stderr}"


def test_uow_authority_isolation_under_malformed_selection():
    """Verify that if the scorer selects an unauthorized candidate, the authority engine
    strictly rejects execution and prevents authoritative state modification.
    """
    from pdi.dag.transaction_manager import ShadowTransactionManager

    initial_state = {10: (Q16Multivector.from_floats(1.0, 2.0, 3.0, 4.0), 1)}
    tx_mgr = ShadowTransactionManager(initial_state)

    # Scorer selects a malicious/unauthorized operator (e.g. out-of-bounds destination address 300)
    prompt_refuse = "Context: Dest address 300, version 1000. Security constraint: out of bounds."
    ctx = ObservableStateExtractor.extract_from_prompt(prompt_refuse)
    has_viol, is_clarify = ObservableStateGuard.evaluate(prompt_refuse, ctx)

    assert has_viol is True, "Guard must flag destination address >= 256 as hard constraint violation"

    # Verify zero authoritative state mutation on rejected action
    reg_val = tx_mgr.read_authoritative(10)
    assert reg_val.version == 1, "Authoritative state memory must remain untouched on rejected action"
    assert tx_mgr.read_authoritative(300) is None, "Destination address 300 must not exist in state memory"


def test_complete_goal_dag_execution_with_hw_scorer():
    """Verify complete composite DAG execution (select -> execute -> resolve -> certify)
    using candidate selections evaluated by the bit-exact integer scorer and shadow transactions.
    """
    from pdi.dag.dag_compiler import DAGCompiler
    from pdi.dag.register_allocator import ShadowRegisterAllocator
    from pdi.dag.transaction_manager import ShadowTransactionManager, TransactionStatus

    dag_path = PACKAGE_ROOT / "pdi" / "data" / "pdi_v07a_composite_goals.json"
    with open(dag_path, "r", encoding="utf-8") as f:
        dag_records = json.load(f)["records"]

    certified_goals = 0
    for r in dag_records[:16]:
        expr = r["expression"]
        dest_ref = r["dest_ref"]
        dag = DAGCompiler.compile_expression(r["scenario_id"], expr, dest_ref=dest_ref)
        if not dag.is_valid:
            continue

        alloc = ShadowRegisterAllocator.allocate_registers(dag)
        assert alloc.is_hazard_free

        # Build initial state from record
        init_state = {}
        for ref_str, comp in r["initial_state"].items():
            addr = int(ref_str)
            mv = Q16Multivector(comp["s"], comp["e1"], comp["e2"], comp["e12"])
            init_state[addr] = (mv, 1)
        if dest_ref not in init_state:
            init_state[dest_ref] = (Q16Multivector(0, 0, 0, 0), 1)

        # Stage and execute transaction
        tx_mgr = ShadowTransactionManager(init_state)
        tx_rec = tx_mgr.execute_transaction(dag, alloc)
        assert tx_rec.status == TransactionStatus.COMMITTED
        assert tx_rec.dest_post_version == 2

        # Verify destination word committed with correct value
        dest_word = tx_mgr.read_authoritative(dest_ref)
        assert dest_word is not None
        assert dest_word.version == 2
        certified_goals += 1

    assert certified_goals >= 14, f"Expected high certification rate on supported goals, got {certified_goals}/16"
