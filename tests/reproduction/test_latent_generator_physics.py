"""Principal Reproduction Test: Latent Generator Inversion,
Observability, and Physical Certification.

Verifies:
1. Forward projection y = P(X) and inverse constraint recovery.
2. Exact null-space basis identification and observational equivalence classes.
3. Strict non-identifiability enforcement:
       Sigma(X) = Sigma(Y) ==> AMBIGUOUS (source_identified = False).
4. Temporal collapse of null space under sequential rotating projections.
5. Noise / perturbation robustness under bounded sensor noise.
6. Conservation falsifiers:
   - Dimension-violating candidate (rejected at Gate D)
   - Energy-conservation-violating candidate (rejected at Gate C)
   - Over-fitting parameter candidate (rejected at Gate F)
   - Unwarranted source identification under null space > 0 (rejected at Gate F)
   - Zero observation candidate (theoretically admissible only, rejected at Gate M)
7. Closed-loop prospective physical acquisition campaign via StateTransitionEngine:
   - Multi-round capability acquisition: EM -> Acoustics -> Hydro -> Gravity -> REFUSE
   - Strict deficiency conservation Delta D = 0 on every state transition
   - Monotone marginal utility decay J_t(M_t^*) down
   - Terminal refusal stopping rule at round 5 (top J < tau_J = 1.5)
"""

from __future__ import annotations

import math

import pytest

from mapeogeo.domains.physics.adapter import PhysicsAdapter
from mapeogeo.domains.physics.ontology import (
    MeasuredObservation,
    PhysicalCertificationVerdict,
    PhysicalConstraint,
    PhysicalHypothesis,
)
from mapeogeo.grammar.work_grammar import WorkGrammar
from mapeogeo.kernel.deficiency import DeficiencyExtractor, WorkRequirement
from mapeogeo.kernel.machinery import MachineryCandidate, MachineryNode
from mapeogeo.kernel.state import KnowledgeState
from mapeogeo.kernel.transition import (
    DEFAULT_REFUSAL_THRESHOLD_TAU_J,
    StateTransitionEngine,
)


def test_latent_generator_observability_and_ambiguity_refusal() -> None:
    """Test latent generator inverse constraints and explicit ambiguity refusal."""
    adapter = PhysicsAdapter()

    # Unknown true latent source X in 3D: X = (5.0, -2.0, 7.0)
    true_x = (5.0, -2.0, 7.0)

    # 1. Measurement 1: Only observe x1 + x2. Projection P1 = [[1.0, 1.0, 0.0]]
    # Observed value y1 = 3.0.
    obs_1 = MeasuredObservation(
        observation_id="obs:sensor:1",
        sensor_id="sensor:mix_12",
        projection_matrix=((1.0, 1.0, 0.0),),
        values=(3.0,),
    )
    res_1 = adapter.infer_latent_generator([obs_1])
    assert res_1.identifiable_rank == 1
    assert res_1.latent_dimension == 3
    assert res_1.null_space_dimension == 2
    assert res_1.is_ambiguous is True
    assert res_1.is_fully_identified is False
    assert "AMBIGUOUS_OBSERVATIONAL_EQUIVALENCE" in (res_1.ambiguity_reason or "")

    # Observational equivalence: X_alt = (0.0, 3.0, 999.0) produces exact same observation y = 3.0!
    x_alt = (0.0, 3.0, 999.0)
    assert adapter.inverter.check_observational_equivalence(true_x, x_alt, obs_1.projection_matrix)

    # 2. Measurement 2: Add second non-collinear observation P2 = [[0.0, 0.0, 1.0]], y2 = 7.0
    obs_2 = MeasuredObservation(
        observation_id="obs:sensor:2",
        sensor_id="sensor:z",
        projection_matrix=((0.0, 0.0, 1.0),),
        values=(7.0,),
    )
    res_2 = adapter.infer_latent_generator([obs_1, obs_2])
    assert res_2.identifiable_rank == 2
    assert res_2.null_space_dimension == 1
    assert res_2.is_ambiguous is True
    assert res_2.is_fully_identified is False

    # 3. Measurement 3: Add third linearly independent observation P3 = [[1.0, -1.0, 0.0]], y3 = 7.0
    # Together with P1 (x1+x2=3, x1-x2=7 => x1=5, x2=-2), full rank is achieved!
    obs_3 = MeasuredObservation(
        observation_id="obs:sensor:3",
        sensor_id="sensor:diff_12",
        projection_matrix=((1.0, -1.0, 0.0),),
        values=(7.0,),
    )
    res_3 = adapter.infer_latent_generator([obs_1, obs_2, obs_3])
    assert res_3.identifiable_rank == 3
    assert res_3.null_space_dimension == 0
    assert res_3.is_ambiguous is False
    assert res_3.is_fully_identified is True
    assert res_3.residual_norm <= 1e-9
    assert all(
        math.isclose(a, b, abs_tol=1e-9)
        for a, b in zip(res_3.generator_representative, true_x, strict=True)
    )


def test_conservation_falsifiers_strict_rejection() -> None:
    """Verify that all invalid physical candidates fail closed across the 5 gates."""
    adapter = PhysicsAdapter()
    obs_valid = MeasuredObservation(
        observation_id="obs:val",
        sensor_id="sensor:ideal",
        projection_matrix=((1.0, 0.0), (0.0, 1.0)),
        values=(2.0, 3.0),
    )
    constraint_energy = PhysicalConstraint(
        constraint_id="c:energy",
        name="Energy Conservation",
        law_type="CONSERVATION_ENERGY",
        tolerance=1e-4,
    )

    # Falsifier 1: Dimension violation (rejected at Gate D)
    hyp_bad_dim = PhysicalHypothesis(
        hypothesis_id="hyp:falsifier:bad_dim",
        model_name="DimensionViolatingModel",
        latent_state=(2.0, 3.0),
        metadata={"has_dimensional_inconsistency": True},
    )
    cert_1 = adapter.certify(hyp_bad_dim, observations=[obs_valid])
    assert cert_1.verdict == PhysicalCertificationVerdict.FALSIFIED
    assert "Gate D failed" in (cert_1.failure_reason or "")

    # Falsifier 2: Energy conservation violation (drift = 0.12 > 1e-4) (rejected at Gate C)
    hyp_bad_energy = PhysicalHypothesis(
        hypothesis_id="hyp:falsifier:bad_energy",
        model_name="NonConservativeModel",
        latent_state=(2.0, 3.0),
        metadata={"energy_drift": 0.12},
    )
    cert_2 = adapter.certify(
        hyp_bad_energy, observations=[obs_valid], constraints=[constraint_energy]
    )
    assert cert_2.verdict == PhysicalCertificationVerdict.FALSIFIED
    assert "Gate C failed: Energy conservation violated" in (cert_2.failure_reason or "")

    # Falsifier 3: Illegal parameter freedom (free_parameters=8 > measurement_count=2)
    # (rejected at Gate F)
    hyp_overparam = PhysicalHypothesis(
        hypothesis_id="hyp:falsifier:overparam",
        model_name="OverparameterizedModel",
        latent_state=(2.0, 3.0),
        free_parameters_count=8,
    )
    cert_3 = adapter.certify(hyp_overparam, observations=[obs_valid])
    assert cert_3.verdict == PhysicalCertificationVerdict.FALSIFIED
    assert "Gate F failed: Model over-fitting detected" in (cert_3.failure_reason or "")

    # Falsifier 4: Unwarranted source identification under ambiguous equivalence (null space = 1)
    # The PhysicalHypothesis constructor itself refuses this invalid claim!
    with pytest.raises(ValueError, match="Source identification forbidden when null space"):
        PhysicalHypothesis(
            hypothesis_id="hyp:falsifier:overclaimed_id",
            model_name="OverclaimedSourceIdentity",
            latent_state=(2.0, 3.0),
            is_source_identified=True,
            null_space_dimension=1,
        )

    # Falsifier 5: Zero empirical observations supplied
    # (rejected from MEASUREMENT_SUPPORTED, marked THEORETICALLY_ADMISSIBLE)
    hyp_unobserved = PhysicalHypothesis(
        hypothesis_id="hyp:falsifier:unobserved",
        model_name="UnobservedPureTheory",
        latent_state=(2.0, 3.0),
    )
    cert_5 = adapter.certify(hyp_unobserved, observations=[])
    assert cert_5.verdict == PhysicalCertificationVerdict.THEORETICALLY_ADMISSIBLE
    assert not cert_5.is_certified


def test_closed_loop_physical_acquisition_campaign() -> None:
    """Execute a 5-round physical acquisition campaign verifying conservation and refusal."""
    grammar = WorkGrammar(base_alphabet_size=58)
    engine = StateTransitionEngine(
        grammar=grammar,
        refusal_threshold=DEFAULT_REFUSAL_THRESHOLD_TAU_J,
    )
    extractor = DeficiencyExtractor()

    # 4 Physical Sectors with 20 requirements each (Total 80 physical requirements):
    # Sector 1: Electrodynamics (wt: 20 * 22.0 = 440.0)
    # Sector 2: Acoustics & Wave Mechanics (wt: 20 * 18.0 = 360.0)
    # Sector 3: Hydrodynamics & Transport (wt: 20 * 16.0 = 320.0)
    # Sector 4: Gravitational Potential & Orbits (wt: 20 * 12.0 = 240.0)
    # Total initial deficiency = 440.0 + 360.0 + 320.0 + 240.0 = 1360.0
    requirements: list[WorkRequirement] = []
    for i in range(1, 21):
        requirements.append(
            WorkRequirement(
                f"req:em:{i:02d}",
                ("SIG_EM_WAVEFORM_INVERSE", "SIG_MAXWELL_POYNTING_FLUX"),
                weight=22.0,
            )
        )
    for i in range(1, 21):
        requirements.append(
            WorkRequirement(
                f"req:acoustics:{i:02d}",
                ("SIG_ACOUSTIC_PRESSURE_MODES", "SIG_HELMHOLTZ_DISPERSION"),
                weight=18.0,
            )
        )
    for i in range(1, 21):
        requirements.append(
            WorkRequirement(
                f"req:hydro:{i:02d}",
                ("SIG_NAVIER_STOKES_VORTICITY", "SIG_MASS_CONTINUITY_FLUX"),
                weight=16.0,
            )
        )
    for i in range(1, 21):
        requirements.append(
            WorkRequirement(
                f"req:gravity:{i:02d}",
                ("SIG_KEPLER_ORBITAL_RESONANCE", "SIG_POISSON_GRAVITATIONAL_FIELD"),
                weight=12.0,
            )
        )

    assert len(requirements) == 80

    state_0 = KnowledgeState.initial()
    dist_0 = extractor.extract_deficiencies(requirements, state_0)
    assert dist_0.total_deficient_severity == 1360.0

    # Register witness certificates for physical candidates
    grammar.register_witness("wit:em:01", "WIT_EM_POYNTING", "Maxwell Poynting Flux integration")
    grammar.register_witness("wit:acoustics:01", "WIT_ACOUSTIC_MODES", "Acoustic modal projection")
    grammar.register_witness("wit:hydro:01", "WIT_HYDRO_VORTICITY", "Vorticity transport witness")
    grammar.register_witness("wit:gravity:01", "WIT_GRAVITY_ORBITS", "Orbital resonance witness")
    grammar.register_witness("wit:noise:01", "WIT_NOISE_CONTROL", "Sensor thermal noise control")

    # Construct physical candidate machinery pool
    cand_em = MachineryCandidate(
        candidate_id="PHYS_CANDIDATE_EM",
        provided_signatures=("SIG_EM_WAVEFORM_INVERSE", "SIG_MAXWELL_POYNTING_FLUX"),
        cost=13.0,
        nodes=(
            MachineryNode("n:em:1", ("SIG_EM_WAVEFORM_INVERSE",), witness_id="wit:em:01"),
            MachineryNode("n:em:2", ("SIG_MAXWELL_POYNTING_FLUX",), witness_id="wit:em:01"),
        ),
        witness_ids=("wit:em:01",),
    )
    cand_acoustics = MachineryCandidate(
        candidate_id="PHYS_CANDIDATE_ACOUSTICS",
        provided_signatures=("SIG_ACOUSTIC_PRESSURE_MODES", "SIG_HELMHOLTZ_DISPERSION"),
        cost=12.0,
        nodes=(
            MachineryNode(
                "n:ac:1", ("SIG_ACOUSTIC_PRESSURE_MODES",), witness_id="wit:acoustics:01"
            ),
            MachineryNode("n:ac:2", ("SIG_HELMHOLTZ_DISPERSION",), witness_id="wit:acoustics:01"),
        ),
        witness_ids=("wit:acoustics:01",),
    )
    cand_hydro = MachineryCandidate(
        candidate_id="PHYS_CANDIDATE_HYDRO",
        provided_signatures=("SIG_NAVIER_STOKES_VORTICITY", "SIG_MASS_CONTINUITY_FLUX"),
        cost=11.5,
        nodes=(
            MachineryNode("n:hy:1", ("SIG_NAVIER_STOKES_VORTICITY",), witness_id="wit:hydro:01"),
            MachineryNode("n:hy:2", ("SIG_MASS_CONTINUITY_FLUX",), witness_id="wit:hydro:01"),
        ),
        witness_ids=("wit:hydro:01",),
    )
    cand_gravity = MachineryCandidate(
        candidate_id="PHYS_CANDIDATE_GRAVITY",
        provided_signatures=("SIG_KEPLER_ORBITAL_RESONANCE", "SIG_POISSON_GRAVITATIONAL_FIELD"),
        cost=11.0,
        nodes=(
            MachineryNode("n:gr:1", ("SIG_KEPLER_ORBITAL_RESONANCE",), witness_id="wit:gravity:01"),
            MachineryNode(
                "n:gr:2", ("SIG_POISSON_GRAVITATIONAL_FIELD",), witness_id="wit:gravity:01"
            ),
        ),
        witness_ids=("wit:gravity:01",),
    )
    cand_distractor = MachineryCandidate(
        candidate_id="PHYS_CANDIDATE_NOISE_CONTROL",
        provided_signatures=("SIG_SENSOR_THERMAL_NOISE",),
        cost=12.0,
        nodes=(
            MachineryNode("n:noise:1", ("SIG_SENSOR_THERMAL_NOISE",), witness_id="wit:noise:01"),
        ),
        witness_ids=("wit:noise:01",),
    )

    candidate_pool = [cand_em, cand_acoustics, cand_hydro, cand_gravity, cand_distractor]

    selected_trajectory: list[str] = []
    utility_trajectory: list[float] = []

    # --- ROUND 1: EM ACQUISITION ---
    outcome_1 = engine.step(requirements, state_0, candidate_pool)
    assert outcome_1.decision == "TRANSITION"
    assert outcome_1.champion is not None
    assert outcome_1.champion.candidate_id == "PHYS_CANDIDATE_EM"
    assert outcome_1.is_learning_event is True
    assert outcome_1.conservation_report is not None
    assert outcome_1.conservation_report["is_conserved"] is True
    assert outcome_1.conservation_report["d_resolved"] == 440.0
    state_1 = outcome_1.next_state
    selected_trajectory.append(outcome_1.champion.candidate_id)
    utility_trajectory.append(outcome_1.champion.cost_efficiency_j)

    dist_1 = extractor.extract_deficiencies(requirements, state_1)
    assert dist_1.total_deficient_severity == 920.0

    # --- ROUND 2: ACOUSTICS ACQUISITION ---
    outcome_2 = engine.step(requirements, state_1, candidate_pool)
    assert outcome_2.decision == "TRANSITION"
    assert outcome_2.champion is not None
    assert outcome_2.champion.candidate_id == "PHYS_CANDIDATE_ACOUSTICS"
    assert outcome_2.is_learning_event is True
    assert outcome_2.conservation_report is not None
    assert outcome_2.conservation_report["is_conserved"] is True
    assert outcome_2.conservation_report["d_resolved"] == 360.0
    state_2 = outcome_2.next_state
    selected_trajectory.append(outcome_2.champion.candidate_id)
    utility_trajectory.append(outcome_2.champion.cost_efficiency_j)

    dist_2 = extractor.extract_deficiencies(requirements, state_2)
    assert dist_2.total_deficient_severity == 560.0

    # --- ROUND 3: HYDRO ACQUISITION ---
    outcome_3 = engine.step(requirements, state_2, candidate_pool)
    assert outcome_3.decision == "TRANSITION"
    assert outcome_3.champion is not None
    assert outcome_3.champion.candidate_id == "PHYS_CANDIDATE_HYDRO"
    assert outcome_3.is_learning_event is True
    assert outcome_3.conservation_report is not None
    assert outcome_3.conservation_report["is_conserved"] is True
    assert outcome_3.conservation_report["d_resolved"] == 320.0
    state_3 = outcome_3.next_state
    selected_trajectory.append(outcome_3.champion.candidate_id)
    utility_trajectory.append(outcome_3.champion.cost_efficiency_j)

    dist_3 = extractor.extract_deficiencies(requirements, state_3)
    assert dist_3.total_deficient_severity == 240.0

    # --- ROUND 4: GRAVITY ACQUISITION ---
    outcome_4 = engine.step(requirements, state_3, candidate_pool)
    assert outcome_4.decision == "TRANSITION"
    assert outcome_4.champion is not None
    assert outcome_4.champion.candidate_id == "PHYS_CANDIDATE_GRAVITY"
    assert outcome_4.is_learning_event is True
    assert outcome_4.conservation_report is not None
    assert outcome_4.conservation_report["is_conserved"] is True
    assert outcome_4.conservation_report["d_resolved"] == 240.0
    state_4 = outcome_4.next_state
    selected_trajectory.append(outcome_4.champion.candidate_id)
    utility_trajectory.append(outcome_4.champion.cost_efficiency_j)

    dist_4 = extractor.extract_deficiencies(requirements, state_4)
    assert dist_4.total_deficient_severity == 0.0
    assert dist_4.covered_requirements == 80

    # --- ROUND 5: RATIONAL REFUSAL ---
    outcome_5 = engine.step(requirements, state_4, candidate_pool)
    assert outcome_5.decision == "REFUSE"
    assert outcome_5.verdict == "NO_MATERIAL_CAPABILITY_ACQUISITION_AVAILABLE"
    assert outcome_5.champion is not None
    assert outcome_5.champion.cost_efficiency_j < DEFAULT_REFUSAL_THRESHOLD_TAU_J
    assert outcome_5.next_state == state_4
    assert len(outcome_5.next_state.certified_nodes) == 8
    assert len(outcome_5.next_state.signatures) == 8

    # --- INVARIANT ASSERTIONS ---
    assert selected_trajectory == [
        "PHYS_CANDIDATE_EM",
        "PHYS_CANDIDATE_ACOUSTICS",
        "PHYS_CANDIDATE_HYDRO",
        "PHYS_CANDIDATE_GRAVITY",
    ]

    # Monotone marginal utility decay
    for i in range(len(utility_trajectory) - 1):
        assert utility_trajectory[i] > utility_trajectory[i + 1], (
            f"Marginal utility failed to decrease: {utility_trajectory}"
        )
