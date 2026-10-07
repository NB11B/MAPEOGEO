"""Pytest Test Suite for Mathematical Proof Verification Audit Layer."""

import pytest
from proof_verification.audit_engine import MathematicalProofAuditEngine
from proof_verification.proof_packet_t1 import ProofPacketT1
from proof_verification.proof_packet_t2 import ProofPacketT2
from proof_verification.proof_packet_t4r import ProofPacketT4R
from proof_verification.proof_packet_t5 import ProofPacketT5
from proof_verification.proof_packet_t3 import ProofPacketT3

VALID_AXIS_1 = {"EXISTING_THEOREM", "NEW_COROLLARY", "NEW_THEOREM", "CONJECTURE", "UNDERDETERMINED", "FALSE"}
VALID_AXIS_2 = {"FORMAL_PROOF_COMPLETE", "HUMAN_PROOF_COMPLETE", "PROOF_SKETCH_ONLY", "SOURCE_ASSEMBLY_ONLY", "COUNTEREXAMPLE_FOUND"}

def test_unforgiving_axes_vocabulary():
    packets = [ProofPacketT1(), ProofPacketT2(), ProofPacketT4R(), ProofPacketT5(), ProofPacketT3()]
    for p in packets:
        v = p.audit_verdict
        assert v["axis_1_novelty"] in VALID_AXIS_1, f"Invalid Axis 1 for {p.target_id}: {v['axis_1_novelty']}"
        assert v["axis_2_rigor"] in VALID_AXIS_2, f"Invalid Axis 2 for {p.target_id}: {v['axis_2_rigor']}"

def test_t1_prismatic_audit():
    p = ProofPacketT1()
    res = p.audit()
    assert res["verdict"]["axis_1_novelty"] == "NEW_COROLLARY"
    assert res["verdict"]["axis_2_rigor"] == "HUMAN_PROOF_COMPLETE"
    assert res["num_hypotheses"] == 4
    assert res["num_lemmas"] == 5

def test_t2_nuclear_limits_audit():
    p = ProofPacketT2()
    res = p.audit()
    assert res["verdict"]["axis_1_novelty"] == "EXISTING_THEOREM"
    assert res["verdict"]["axis_2_rigor"] == "HUMAN_PROOF_COMPLETE"
    assert res["necessity_audited"] is True

def test_t4r_chromatic_audit():
    p = ProofPacketT4R()
    res = p.audit()
    assert res["verdict"]["axis_1_novelty"] == "CONJECTURE"
    assert res["verdict"]["axis_2_rigor"] == "PROOF_SKETCH_ONLY"
    assert res["ext1_canonicity_audited"] is True

def test_t5_operadic_audit():
    p = ProofPacketT5()
    res = p.audit()
    assert res["verdict"]["axis_1_novelty"] == "UNDERDETERMINED"
    assert res["verdict"]["axis_2_rigor"] == "COUNTEREXAMPLE_FOUND"
    assert res["counterexample_documented"] is True

def test_t3_cubical_audit():
    p = ProofPacketT3()
    res = p.audit()
    assert res["verdict"]["axis_1_novelty"] == "NEW_COROLLARY"
    assert res["verdict"]["axis_2_rigor"] == "HUMAN_PROOF_COMPLETE"
    assert res["syntactic_hypotheses_audited"] is True

def test_master_audit_engine():
    engine = MathematicalProofAuditEngine()
    ledger = engine.run_audit()
    assert len(ledger["summary_table"]) == 5
    assert len(ledger["detailed_packets"]) == 5

def test_kernel_v3_regression_zero():
    from experiments.kernel_v3_release import assemble_kernel_v3_release
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = assemble_kernel_v3_release(Path(tmp_dir))
        assert manifest["total_regressions"] == 0
        assert manifest["release_version"] == "v3.0.0"
