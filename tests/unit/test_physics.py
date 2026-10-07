"""Unit Tests for Physics Domain Adapter Subsystem.

Tests:
1. Physical ontology and invariant enforcement (e.g. non-identifiability when null space > 0).
2. Translation of PhysicalObjective into domain-neutral WorkContract.
3. 5-Gate Physical Certification Boundary C_phys = { D, C, M, F, R }:
   - Gate D: Dimensional inconsistency rejection
   - Gate C: Conservation violation rejection
   - Gate M: Zero observations -> THEORETICALLY_ADMISSIBLE; residual > tol -> FALSIFIED
   - Gate F: Over-fitting and unearned source identification rejection
   - Gate R: Repeatability / replay verification
   - Full 5-gate pass -> MEASUREMENT_SUPPORTED
4. Latent generator inversion and non-identifiability:
   - Exact null space recovery
   - Equivalence class detection: Sigma(X1) = Sigma(X2) ==> AMBIGUOUS
   - Temporal collapse of null space under sequential rotating projections
5. Literal 6D grammar factoring and drift auditing.
6. Ability reach measurement and candidate machinery proposal.
"""

from __future__ import annotations

import pytest

from mapeogeo.domains.physics import (
    FactoringClassification,
    MeasuredObservation,
    PhysicalCertificationVerdict,
    PhysicalConstraint,
    PhysicalHypothesis,
    PhysicalObjective,
    PhysicsAdapter,
)
from mapeogeo.kernel.deficiency import DeficiencyRecord
from mapeogeo.kernel.state import KnowledgeState


def test_physics_ontology_and_epistemic_invariants() -> None:
    # 1. MeasuredObservation digest and shape validation
    obs = MeasuredObservation(
        observation_id="obs:sensor:1",
        sensor_id="sensor:bolometer:01",
        projection_matrix=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        values=(3.5, 4.2),
        units="watts",
    )
    assert obs.dimension == 2
    assert obs.latent_dimension == 3
    assert len(obs.digest) == 64

    # 2. Epistemic invariant: Source identification forbidden when null_space_dimension > 0
    with pytest.raises(ValueError, match="Source identification forbidden when null space"):
        PhysicalHypothesis(
            hypothesis_id="hyp:overclaimed",
            model_name="OverclaimedModel",
            latent_state=(1.0, 2.0, 3.0),
            is_source_identified=True,  # Illegal under rank deficiency!
            null_space_dimension=1,
        )

    # 3. Valid hypothesis under rank deficiency acknowledges ambiguity
    hyp = PhysicalHypothesis(
        hypothesis_id="hyp:honest",
        model_name="HonestPartialModel",
        latent_state=(1.0, 2.0, 0.0),
        is_source_identified=False,
        null_space_dimension=1,
    )
    assert not hyp.is_source_identified
    assert hyp.null_space_dimension == 1


def test_required_work_contract_translation() -> None:
    adapter = PhysicsAdapter()
    obj = PhysicalObjective(
        objective_id="PHYS-EM-01",
        title="Waveform Source Inversion",
        domain="Electrodynamics",
        required_signatures=("LATENT_WAVEFORM_INVERSE", "MAXWELL_ENERGY_CONSERVATION"),
        difficulty=1.5,
        structural_distance=4.0,
        novelty=1.2,
        depth=1.3,
    )

    contract = adapter.required_work(obj)
    assert contract.contract_id == "work:phys:PHYS-EM-01"
    assert contract.source == "physics:objective:PHYS-EM-01:unobserved"
    assert contract.target == "physics:objective:PHYS-EM-01:empirically_established"
    assert "has_signature(LATENT_WAVEFORM_INVERSE)" in contract.preconditions
    assert "has_signature(MAXWELL_ENERGY_CONSERVATION)" in contract.preconditions
    assert "physically_reconstructed(PHYS-EM-01)" in contract.postconditions
    assert contract.cost == 6.0


def test_five_gate_physical_certification_boundary() -> None:
    adapter = PhysicsAdapter()

    # Create synthetic true source X = (3.0, 4.0)
    true_x = (3.0, 4.0)
    # Full rank projection: P = identity
    obs_full = MeasuredObservation(
        observation_id="obs:full",
        sensor_id="sensor:exact",
        projection_matrix=((1.0, 0.0), (0.0, 1.0)),
        values=true_x,
    )

    constraint_energy = PhysicalConstraint(
        constraint_id="c:energy",
        name="Hamiltonian Energy Conservation",
        law_type="CONSERVATION_ENERGY",
        tolerance=1e-4,
    )

    # 1. Gate D failure: Dimensional inconsistency
    hyp_dim_err = PhysicalHypothesis(
        hypothesis_id="hyp:dim_err",
        model_name="DimErrModel",
        latent_state=true_x,
        metadata={"has_dimensional_inconsistency": True},
    )
    cert_d = adapter.certify(hyp_dim_err, observations=[obs_full])
    assert cert_d.verdict == PhysicalCertificationVerdict.FALSIFIED
    assert "Gate D failed" in (cert_d.failure_reason or "")

    # 2. Gate C failure: Conservation violation
    hyp_cons_err = PhysicalHypothesis(
        hypothesis_id="hyp:cons_err",
        model_name="ConsErrModel",
        latent_state=true_x,
        metadata={"energy_drift": 0.05},
    )
    cert_c = adapter.certify(
        hyp_cons_err,
        observations=[obs_full],
        constraints=[constraint_energy],
    )
    assert cert_c.verdict == PhysicalCertificationVerdict.FALSIFIED
    assert "Gate C failed: Energy conservation violated" in (cert_c.failure_reason or "")

    # 3. Gate M: Zero observations -> THEORETICALLY_ADMISSIBLE
    hyp_theory = PhysicalHypothesis(
        hypothesis_id="hyp:pure_theory",
        model_name="UnmeasuredTheory",
        latent_state=true_x,
    )
    cert_m_zero = adapter.certify(hyp_theory, observations=[])
    assert cert_m_zero.verdict == PhysicalCertificationVerdict.THEORETICALLY_ADMISSIBLE
    assert not cert_m_zero.is_certified

    # 4. Gate M: Residual error exceeds tolerance -> FALSIFIED
    hyp_wrong = PhysicalHypothesis(
        hypothesis_id="hyp:wrong_values",
        model_name="WrongModel",
        latent_state=(10.0, 20.0),
    )
    cert_m_err = adapter.certify(hyp_wrong, observations=[obs_full])
    assert cert_m_err.verdict == PhysicalCertificationVerdict.FALSIFIED
    assert "Gate M failed: Residual error" in (cert_m_err.failure_reason or "")

    # 5. Gate F failure: Over-fitting (free parameters > measurement count)
    hyp_overfit = PhysicalHypothesis(
        hypothesis_id="hyp:overfit",
        model_name="OverfitModel",
        latent_state=true_x,
        free_parameters_count=10,  # 10 free parameters for 2 measurements
    )
    cert_f_overfit = adapter.certify(hyp_overfit, observations=[obs_full])
    assert cert_f_overfit.verdict == PhysicalCertificationVerdict.FALSIFIED
    assert "Gate F failed: Model over-fitting detected" in (cert_f_overfit.failure_reason or "")

    # 6. Full 5-Gate PASS -> MEASUREMENT_SUPPORTED
    hyp_sound = PhysicalHypothesis(
        hypothesis_id="hyp:sound",
        model_name="SoundPhysicalModel",
        latent_state=true_x,
        is_source_identified=True,
        null_space_dimension=0,
        free_parameters_count=0,
        metadata={"energy_drift": 0.0},
    )
    cert_pass = adapter.certify(
        hyp_sound,
        observations=[obs_full],
        constraints=[constraint_energy],
        repeat_observations=[obs_full],
    )
    assert cert_pass.is_certified
    assert cert_pass.verdict == PhysicalCertificationVerdict.MEASUREMENT_SUPPORTED
    assert len(cert_pass.gates_passed) == 5
    assert cert_pass.residual_error == 0.0


def test_latent_generator_inversion_and_non_identifiability() -> None:
    adapter = PhysicsAdapter()

    # Single projection P = [[1.0, 0.0]] onto 2D latent state X = (3.0, 4.0)
    # Observable response: y = 3.0. Dimension 2 is unobserved!
    obs_partial = MeasuredObservation(
        observation_id="obs:part",
        sensor_id="sensor:x_only",
        projection_matrix=((1.0, 0.0),),
        values=(3.0,),
    )

    res = adapter.infer_latent_generator([obs_partial])
    assert res.identifiable_rank == 1
    assert res.latent_dimension == 2
    assert res.null_space_dimension == 1
    assert res.is_ambiguous is True
    assert res.is_fully_identified is False
    assert "AMBIGUOUS_OBSERVATIONAL_EQUIVALENCE" in (res.ambiguity_reason or "")
    assert res.generator_representative == (3.0, 0.0)
    assert res.null_space_basis == ((0.0, 1.0),)

    # Observational equivalence: X1 = (3.0, 4.0) and X2 = (3.0, -99.0) produce same observation
    p_mat = ((1.0, 0.0),)
    assert adapter.inverter.check_observational_equivalence((3.0, 4.0), (3.0, -99.0), p_mat)

    # Rotating projection collapses null space: P2 = [[0.0, 1.0]], y2 = 4.0
    obs_ortho = MeasuredObservation(
        observation_id="obs:ortho",
        sensor_id="sensor:y_only",
        projection_matrix=((0.0, 1.0),),
        values=(4.0,),
    )
    res_collapsed = adapter.infer_latent_generator([obs_partial, obs_ortho])
    assert res_collapsed.identifiable_rank == 2
    assert res_collapsed.null_space_dimension == 0
    assert res_collapsed.is_ambiguous is False
    assert res_collapsed.is_fully_identified is True
    assert res_collapsed.generator_representative == (3.0, 4.0)


def test_physics_grammar_factoring_literal_coordinates_and_drift() -> None:
    adapter = PhysicsAdapter()

    # 1. Exact factoring with witness extension
    res_wit = adapter.factor_grammar(
        work="w_phys_1",
        witness_id="wit:sensor:bolometer",
        witness_symbol="WIT_BOLOMETER_FLUX",
        witness_role="Bolometer flux integration",
    )
    assert res_wit.classification == FactoringClassification.WITNESS_EXTENSION
    assert res_wit.is_compliant
    assert not res_wit.drift_detected

    # 2. Composition over coordinates
    res_comp = adapter.factor_grammar(
        work=r"\Pi_{\mathrm{sensor}} \circ \Gamma_{\mathrm{flow}} \circ wit:sensor:bolometer",
        witness_id="wit:sensor:bolometer",
    )
    assert res_comp.classification in {
        FactoringClassification.EXACT_FACTOR,
        FactoringClassification.COMPOSITION,
    }
    assert res_comp.is_compliant

    # 3. Semantic drift: forbidden relabeling of Gamma as connection
    res_drift = adapter.factor_grammar(
        work=r"\Gamma_{\mathrm{affine_connection}} \circ w",
        witness_id="w",
    )
    assert res_drift.classification == FactoringClassification.SEMANTIC_DRIFT
    assert res_drift.drift_detected
    assert not res_drift.is_compliant

    # 4. Illegal coordinate dimension expansion beyond d=6
    res_dim = adapter.factor_grammar(
        work=r"\Delta \circ EXTENDED_DIMENSION \circ w",
        witness_id="w",
    )
    assert res_dim.classification == FactoringClassification.NEW_COORDINATE_REQUIRED
    assert res_dim.drift_detected
    assert not res_dim.is_compliant


def test_physics_candidate_machinery_and_ability_measurement() -> None:
    adapter = PhysicsAdapter()
    obj = PhysicalObjective(
        objective_id="PHYS-TEST-02",
        title="Physical Reach Test",
        domain="Acoustics",
        difficulty=1.0,
        structural_distance=1.0,
        novelty=1.0,
        depth=1.0,
        required_signatures=("ACOUSTIC_WAVE_INVERSE", "HELMHOLTZ_ENERGY_CONSERVATION"),
    )

    state = KnowledgeState.initial()
    assert adapter.measure_ability(obj, state) == 0.0

    deficiency = DeficiencyRecord(
        req_id="d:phys:01",
        weight=2.0,
        required=("ACOUSTIC_WAVE_INVERSE", "HELMHOLTZ_ENERGY_CONSERVATION"),
        missing=("ACOUSTIC_WAVE_INVERSE", "HELMHOLTZ_ENERGY_CONSERVATION"),
        covered=(),
        is_covered=False,
        coverage_ratio=0.0,
    )
    candidates = adapter.candidate_machinery(deficiency, state)
    assert len(candidates) == 2
    assert {c.provided_signatures[0] for c in candidates} == {
        "ACOUSTIC_WAVE_INVERSE",
        "HELMHOLTZ_ENERGY_CONSERVATION",
    }

    # Step 1: acquire ACOUSTIC_WAVE_INVERSE
    node_1 = (
        candidates[0]
        if candidates[0].provided_signatures[0] == "ACOUSTIC_WAVE_INVERSE"
        else candidates[1]
    )
    state_1 = state.transition(
        new_signatures=("ACOUSTIC_WAVE_INVERSE",),
        new_nodes=[node_1],
    )
    assert 0.0 < adapter.measure_ability(obj, state_1) < 1.0

    # Step 2: acquire HELMHOLTZ_ENERGY_CONSERVATION
    node_2 = (
        candidates[1]
        if candidates[0].provided_signatures[0] == "ACOUSTIC_WAVE_INVERSE"
        else candidates[0]
    )
    state_2 = state_1.transition(
        new_signatures=("HELMHOLTZ_ENERGY_CONSERVATION",),
        new_nodes=[node_2],
    )
    assert adapter.measure_ability(obj, state_2) == 1.0
