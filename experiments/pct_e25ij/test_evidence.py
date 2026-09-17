import json
from pathlib import Path

from experiments.pct_e25ij.lifecycle import run_e25i_audit
from experiments.pct_e25ij.scenarios import run_e25j_scenarios


def test_frozen_e25ij_evidence_matches_fresh_execution():
    root = Path(__file__).resolve().parents[2]
    i = run_e25i_audit()
    j = run_e25j_scenarios()
    assert json.loads((root / "evidence/pct_e25i_closure_receipt_ledger.json").read_text()) == i["ledger"]
    assert json.loads((root / "evidence/pct_e25i_derived_closure_snapshot.json").read_text()) == i["snapshot"]
    assert json.loads((root / "evidence/pct_e25j_revocation_staleness.json").read_text()) == j
