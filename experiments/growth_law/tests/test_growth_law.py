"""Unit test suite for Growth-Law Campaign."""

import pytest
from pathlib import Path
import json

from experiments.growth_law.e2_acquisition import acquire_e2_corpus, NEW_EXTERNAL_DOMAINS_E2
from experiments.growth_law.candidate_audit import audit_e2_contamination, audit_e2_candidate_novelty
from experiments.growth_law.growth_metrics import compute_growth_law_trajectory

def test_e2_acquisition_and_domains():
    records = acquire_e2_corpus(target_count=1500)
    assert len(records) == 1500
    assert len(NEW_EXTERNAL_DOMAINS_E2) == 10
    domains_present = {r["domain"] for r in records}
    assert domains_present == set(NEW_EXTERNAL_DOMAINS_E2)

def test_e2_contamination_gate():
    records = acquire_e2_corpus(target_count=1500)
    audit = audit_e2_contamination(records)
    assert audit["gate_passed"]
    assert audit["clean_count"] >= 1400

def test_candidate_novelty_folds_into_alphabet():
    res = audit_e2_candidate_novelty()
    assert res["disposition"] == "FOLD_INTO_M6_ALPHABET"
    assert res["delta_d"] == 0
    assert res["delta_a"] == 1
    assert not res["is_independent_dimension"]

def test_growth_rate_monotonic_decay():
    res = compute_growth_law_trajectory()
    assert res["coordinate_growth_rate_decaying"]
    assert res["g_sequence"] == [0.125, 0.100, 0.000]

def test_description_length_monotonic_compression():
    res = compute_growth_law_trajectory()
    assert res["description_length_compressing"]
    traj = res["trajectory"]
    assert traj[0]["description_length_bits_per_state"] > traj[1]["description_length_bits_per_state"]
    assert traj[1]["description_length_bits_per_state"] > traj[2]["description_length_bits_per_state"]
    assert traj[2]["description_length_bits_per_state"] > traj[3]["description_length_bits_per_state"]

def test_zero_regression_invariant_preserved():
    res = compute_growth_law_trajectory()
    assert res["all_zero_regressions"]
    assert res["dimension_saturation_observed"]
    assert res["supported_hypothesis"] == "HYPOTHESIS_2_RELATIONAL_BASIS"
