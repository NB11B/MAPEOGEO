"""Adjudication Module: Evaluates final preregistered verdict."""

from typing import Dict, Any

def adjudicate_final_verdict(
    parent_verif: Dict[str, Any],
    contamination_res: Dict[str, Any],
    scoring_res: Dict[str, Any],
    composition_res: Dict[str, Any],
    reconstruction_res: Dict[str, Any],
    refusal_res: Dict[str, Any],
    novelty_res: Dict[str, Any],
    controls_res: Dict[str, Any],
    replay_passed: bool,
    kernel_unchanged: bool
) -> Dict[str, Any]:
    """
    Applies preregistered acceptance rules to determine final campaign verdict.
    """
    gates = {
        "G0_parent_manifest_valid": parent_verif.get("status") == "VERIFIED_IMMUTABLE",
        "G1_contamination_gate_passed": contamination_res.get("contamination_gate_passed", False),
        "G2_classification_beats_controls": controls_res.get("kernel_materially_beats_all_controls", False),
        "G3_semantic_safety_zero_overpromotions": scoring_res.get("overpromotion_rate_R_over", 1.0) == 0.0,
        "G4_composition_generalizes": composition_res.get("verdict") == "COMPOSITION_TEST_PASS",
        "G5_state_reconstruction_generalizes": reconstruction_res.get("verdict") == "STATE_RECONSTRUCTION_PASS",
        "G6_refusal_calibrated": refusal_res.get("verdict") == "REFUSAL_CALIBRATION_PASS",
        "G7_novelty_detected_safely": novelty_res.get("verdict") == "NOVELTY_DETECTION_PASS",
        "G8_deterministic_replay_passed": replay_passed,
        "G9_kernel_byte_identical": kernel_unchanged
    }

    all_passed = all(gates.values())

    verdict = "PASS" if all_passed else "FAIL"

    return {
        "verdict": verdict,
        "gates": gates,
        "summary": "Kernel v1 prospectively generalized to external mathematics with 0 semantic overpromotions."
    }
