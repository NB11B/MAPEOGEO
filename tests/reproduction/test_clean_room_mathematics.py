"""Clean-Room Reproduction Test for Mathematics Domain Adapter & Autonomous Kernel.

Replays the 80-problem clean-room campaign verifying:
1. Translating the fresh 80-problem corpus into domain-neutral WorkRequirements.
2. Generating blind candidate curricula without domain labels or historical knowledge.
3. Closed-loop multi-round execution:
   Round 1: CFT acquired (deficiency reduced by 459.0 to 923.78)
   Round 2: GMT acquired (deficiency reduced by 363.78 to 560.0)
   Round 3: ERGODIC acquired (deficiency reduced by 323.4 to 236.6)
   Round 4: MORSE acquired (deficiency reduced by 236.6 to 0.0)
   Round 5: REFUSE triggered (top efficiency J < \\tau_J = 1.5)
4. Formal Invariants:
   - Trajectory reproduced: CFT -> GMT -> ERGODIC -> MORSE -> REFUSE
   - Deficiency conservation holds strictly on every transition: Delta D = 0
   - Marginal utility decay: J_t(M_t^*) monotonically decreases across rounds
   - 4-gate certification passes for every acquired candidate
   - Final state covers all 8 functional signatures with 8 certified nodes
   - Refusal stopping rule terminates execution rationally at Round 5
"""

from __future__ import annotations

from typing import Any

from mapeogeo.domains.mathematics.adapter import MathematicsAdapter
from mapeogeo.domains.mathematics.clean_room import (
    BlindCurriculumGenerator,
    get_fresh_problem_corpus,
)
from mapeogeo.grammar.work_grammar import WorkGrammar
from mapeogeo.kernel.deficiency import DeficiencyExtractor, WorkRequirement
from mapeogeo.kernel.machinery import MachineryCandidate, MachineryNode
from mapeogeo.kernel.state import KnowledgeState
from mapeogeo.kernel.transition import (
    DEFAULT_REFUSAL_THRESHOLD_TAU_J,
    StateTransitionEngine,
)


def _cand_dict_to_machinery_candidate(c_dict: dict[str, Any]) -> MachineryCandidate:
    """Convert blind curriculum dictionary to a domain-neutral MachineryCandidate."""
    nodes: list[MachineryNode] = []
    witness_ids: list[str] = []
    for m in c_dict.get("machinery_nodes", []):
        wid = m.get("witness_id")
        if wid:
            witness_ids.append(wid)
        nodes.append(
            MachineryNode(
                node_id=m["id"],
                provided_signatures=tuple(c_dict["signatures"]),
                dependencies=tuple(m.get("dependencies", ())),
                witness_id=wid,
                metadata={"name": m.get("name", "")},
            )
        )
    return MachineryCandidate(
        candidate_id=c_dict["id"],
        provided_signatures=tuple(c_dict["signatures"]),
        cost=float(c_dict["cost"]),
        nodes=tuple(nodes),
        witness_ids=tuple(witness_ids),
        metadata={"name": c_dict.get("name", "")},
    )


def test_clean_room_80_problem_autonomous_acquisition_trajectory() -> None:
    """Replay clean-room campaign verifying exact trajectory and invariants."""
    grammar = WorkGrammar(base_alphabet_size=58)
    adapter = MathematicsAdapter(grammar=grammar)
    engine = StateTransitionEngine(
        grammar=grammar,
        refusal_threshold=DEFAULT_REFUSAL_THRESHOLD_TAU_J,
    )
    extractor = DeficiencyExtractor()
    generator = BlindCurriculumGenerator()

    # 1. Load canonical fresh problem corpus (80 problems across 4 untouched domains)
    problems = get_fresh_problem_corpus()
    assert len(problems) == 80

    # 2. Translate problems to domain-neutral WorkRequirements
    requirements: list[WorkRequirement] = [
        WorkRequirement(
            req_id=p.problem_id,
            required_signatures=p.required_signatures,
            weight=p.weight,
            metadata={"domain": p.domain, "difficulty": p.difficulty},
        )
        for p in problems
    ]

    # Verify initial deficiency severity
    state_0 = KnowledgeState.initial()
    dist_0 = extractor.extract_deficiencies(requirements, state_0)
    assert dist_0.total_requirements == 80
    assert dist_0.covered_requirements == 0
    assert dist_0.deficient_requirements == 80
    assert abs(dist_0.total_deficient_severity - 1382.78) < 1e-2

    # 3. Generate candidate curricula dynamically
    blind_candidates = generator.generate_candidate_curricula(
        [{"id": p.problem_id, "required_signatures": p.required_signatures} for p in problems]
    )
    assert len(blind_candidates) == 5

    # Register witness certificates via grammar factoring
    for c_dict in blind_candidates:
        for m in c_dict.get("machinery_nodes", []):
            if m.get("witness_id"):
                audit = adapter.factor_grammar(
                    work=m.get("grammar_factorization", ""),
                    witness_id=m["witness_id"],
                    witness_symbol=m.get("witness_certificate"),
                    witness_role=m.get("name"),
                )
                assert audit.is_compliant
                assert not audit.drift_detected

    candidate_pool = [_cand_dict_to_machinery_candidate(c) for c in blind_candidates]

    # Trajectory tracking
    selected_trajectory: list[str] = []
    utility_trajectory: list[float] = []

    # --- ROUND 1: CFT ACQUISITION ---
    outcome_1 = engine.step(requirements, state_0, candidate_pool)
    assert outcome_1.decision == "TRANSITION"
    assert outcome_1.champion is not None
    assert outcome_1.champion.candidate_id == "CANDIDATE_CFT"
    assert outcome_1.is_learning_event is True
    assert outcome_1.conservation_report is not None
    assert outcome_1.conservation_report["is_conserved"] is True
    assert outcome_1.conservation_report["d_resolved"] == 459.0
    state_1 = outcome_1.next_state
    selected_trajectory.append(outcome_1.champion.candidate_id)
    utility_trajectory.append(outcome_1.champion.cost_efficiency_j)

    dist_1 = extractor.extract_deficiencies(requirements, state_1)
    assert abs(dist_1.total_deficient_severity - 923.78) < 1e-2
    assert dist_1.covered_requirements == 20

    # --- ROUND 2: GMT ACQUISITION ---
    outcome_2 = engine.step(requirements, state_1, candidate_pool)
    assert outcome_2.decision == "TRANSITION"
    assert outcome_2.champion is not None
    assert outcome_2.champion.candidate_id == "CANDIDATE_GMT"
    assert outcome_2.is_learning_event is True
    assert outcome_2.conservation_report is not None
    assert outcome_2.conservation_report["is_conserved"] is True
    assert outcome_2.conservation_report["d_resolved"] == 363.78
    state_2 = outcome_2.next_state
    selected_trajectory.append(outcome_2.champion.candidate_id)
    utility_trajectory.append(outcome_2.champion.cost_efficiency_j)

    dist_2 = extractor.extract_deficiencies(requirements, state_2)
    assert abs(dist_2.total_deficient_severity - 560.00) < 1e-2
    assert dist_2.covered_requirements == 40

    # --- ROUND 3: ERGODIC ACQUISITION ---
    outcome_3 = engine.step(requirements, state_2, candidate_pool)
    assert outcome_3.decision == "TRANSITION"
    assert outcome_3.champion is not None
    assert outcome_3.champion.candidate_id == "CANDIDATE_ERGODIC"
    assert outcome_3.is_learning_event is True
    assert outcome_3.conservation_report is not None
    assert outcome_3.conservation_report["is_conserved"] is True
    assert outcome_3.conservation_report["d_resolved"] == 323.40
    state_3 = outcome_3.next_state
    selected_trajectory.append(outcome_3.champion.candidate_id)
    utility_trajectory.append(outcome_3.champion.cost_efficiency_j)

    dist_3 = extractor.extract_deficiencies(requirements, state_3)
    assert abs(dist_3.total_deficient_severity - 236.60) < 1e-2
    assert dist_3.covered_requirements == 60

    # --- ROUND 4: MORSE ACQUISITION ---
    outcome_4 = engine.step(requirements, state_3, candidate_pool)
    assert outcome_4.decision == "TRANSITION"
    assert outcome_4.champion is not None
    assert outcome_4.champion.candidate_id == "CANDIDATE_MORSE"
    assert outcome_4.is_learning_event is True
    assert outcome_4.conservation_report is not None
    assert outcome_4.conservation_report["is_conserved"] is True
    assert outcome_4.conservation_report["d_resolved"] == 236.60
    state_4 = outcome_4.next_state
    selected_trajectory.append(outcome_4.champion.candidate_id)
    utility_trajectory.append(outcome_4.champion.cost_efficiency_j)

    dist_4 = extractor.extract_deficiencies(requirements, state_4)
    assert dist_4.total_deficient_severity == 0.0
    assert dist_4.covered_requirements == 80
    assert dist_4.deficient_requirements == 0

    # --- ROUND 5: RATIONAL REFUSAL ---
    outcome_5 = engine.step(requirements, state_4, candidate_pool)
    assert outcome_5.decision == "REFUSE"
    assert outcome_5.verdict == "NO_MATERIAL_CAPABILITY_ACQUISITION_AVAILABLE"
    assert outcome_5.champion is not None
    assert outcome_5.champion.cost_efficiency_j < DEFAULT_REFUSAL_THRESHOLD_TAU_J
    # State remains unmutated at round 5
    assert outcome_5.next_state == state_4
    assert len(outcome_5.next_state.certified_nodes) == 8
    assert len(outcome_5.next_state.signatures) == 8

    # --- INVARIANT ASSERTIONS ---
    # 1. Exact canonical trajectory reproduced
    assert selected_trajectory == [
        "CANDIDATE_CFT",
        "CANDIDATE_GMT",
        "CANDIDATE_ERGODIC",
        "CANDIDATE_MORSE",
    ]

    # 2. Monotone marginal utility decay J_t(M_t^*) down
    for i in range(len(utility_trajectory) - 1):
        assert utility_trajectory[i] > utility_trajectory[i + 1], (
            f"Marginal utility failed to decrease: {utility_trajectory}"
        )
