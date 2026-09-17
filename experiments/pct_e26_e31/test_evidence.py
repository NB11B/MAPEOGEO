from __future__ import annotations

import json
from pathlib import Path

from experiments.pct_e26_e31.generate_evidence import EVIDENCE_FILENAMES, generate


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "evidence"
FROZEN_MAIN = ROOT / ".crossbranch" / "frozen-main"


def test_evidence_filename_set_is_complete() -> None:
    assert EVIDENCE_FILENAMES == (
        "pct_e26_cross_branch_manifest.json",
        "pct_e27_heldout_relational_recovery.json",
        "pct_e28_minimal_evidence_nullspace.json",
        "pct_e29_rule_discovery_falsification.json",
        "pct_e30_main_pct_adversarial_replay.json",
        "pct_e31_bidirectional_closure.json",
    )


def test_fresh_generation_matches_frozen_evidence_byte_for_byte(tmp_path: Path) -> None:
    generated = tmp_path / "generated"
    generate(generated, ROOT, FROZEN_MAIN)
    for filename in EVIDENCE_FILENAMES:
        candidate = generated / filename
        frozen = EVIDENCE_DIR / filename
        assert candidate.is_file(), filename
        assert frozen.is_file(), filename
        assert candidate.read_bytes() == frozen.read_bytes(), filename


def test_frozen_evidence_is_valid_json_and_self_identifies() -> None:
    expected_ids = {
        "pct_e26_cross_branch_manifest.json": "E26_CROSS_BRANCH_CORPUS_BINDING",
        "pct_e27_heldout_relational_recovery.json": "E27_SEALED_HELDOUT_RELATIONAL_RECOVERY",
        "pct_e28_minimal_evidence_nullspace.json": "E28_MINIMAL_EVIDENCE_ERASURE_NULLSPACE",
        "pct_e29_rule_discovery_falsification.json": "E29_STRUCTURAL_RULE_DISCOVERY_FALSIFICATION",
        "pct_e30_main_pct_adversarial_replay.json": "E30_MAIN_PCT_ADVERSARIAL_REPLAY",
        "pct_e31_bidirectional_closure.json": "E31_BIDIRECTIONAL_SOLVER_VERIFIER_CLOSURE",
    }
    for filename, experiment_id in expected_ids.items():
        payload = json.loads((EVIDENCE_DIR / filename).read_text(encoding="utf-8"))
        assert payload["experiment_id"] == experiment_id
