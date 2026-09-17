from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import importlib

from experiments.pct_goal_solver import v0_20_campaign as campaign
from experiments.pct_goal_solver import v0_20_goals as goals
from experiments.pct_goal_solver.model import Artifact
from experiments.pct_goal_solver.rigorous_math import certify_bezout


def test_scientific_status_distinguishes_engine_evidence_and_capability_failures() -> None:
    expected_keys = getattr(campaign, "EXPECTED_GATE_KEYS", frozenset())
    engine_keys = getattr(campaign, "ENGINE_GATE_KEYS", frozenset())
    evidence_keys = getattr(campaign, "EVIDENCE_GATE_KEYS", frozenset())
    capability_keys = getattr(campaign, "CAPABILITY_GATE_KEYS", frozenset())
    assert expected_keys
    assert expected_keys == engine_keys | evidence_keys | capability_keys

    all_green = {key: True for key in expected_keys}
    assert campaign.classify_scientific_status(all_green) == "SUPPORTED"

    engine_failed = dict(all_green)
    engine_failed[next(iter(engine_keys))] = False
    assert campaign.classify_scientific_status(engine_failed) == "ENGINE_INVALID"

    evidence_missing = dict(all_green)
    evidence_missing[next(iter(evidence_keys))] = False
    assert campaign.classify_scientific_status(evidence_missing) == "EVIDENCE_PARTIAL"

    unsupported = dict(all_green)
    unsupported[next(iter(capability_keys))] = False
    assert campaign.classify_scientific_status(unsupported) == "NOT_SUPPORTED"
    assert campaign.classify_scientific_status({}) == "ENGINE_INVALID"


def test_receipts_reject_out_of_range_counts_instead_of_clamping() -> None:
    gate = next(iter(campaign.GATE_DENOMINATORS))
    denominator = campaign.GATE_DENOMINATORS[gate]
    receipt = campaign._receipt(denominator + 1, gate, "test overflow")
    assert receipt["numerator"] == denominator + 1
    assert receipt["denominator"] == denominator
    assert receipt["passed"] is False
    assert receipt["integrity_error"] == "COUNT_OUT_OF_RANGE"


def test_terminal_candidate_controls_are_typed_and_never_goal_inputs() -> None:
    control_type = getattr(goals, "TerminalCandidateControl", None)
    build_controls = getattr(goals, "build_v0_20_terminal_controls", None)
    assert control_type is not None
    assert build_controls is not None
    controls = build_controls()
    assert controls
    assert {control.kind.value for control in controls} == {
        "DOMAIN_REFUSAL",
        "VALID_NEGATIVE_RESULT",
        "INVALID_TERMINAL_CERTIFICATE",
        "EXTERNAL_VALID_CERTIFICATE",
    }
    for control in controls:
        assert isinstance(control, control_type)
        assert all(
            input_artifact is not control.candidate
            and input_artifact.artifact_id != control.candidate.artifact_id
            for input_artifact in control.goal.inputs.values()
        )


def test_only_mathematically_nonunique_controls_claim_distinct_valid_alternatives() -> None:
    controls = goals.build_v0_20_terminal_controls()
    claimed = {
        control.family
        for control in controls
        if control.kind.value == "EXTERNAL_VALID_CERTIFICATE" and control.is_distinct_alternative
    }
    assert claimed == {"F2", "F3"}


def test_controls_use_public_terminal_authority_and_catch_corrupt_f3() -> None:
    verification = importlib.import_module("experiments.pct_goal_solver.v0_20_terminal_verification")
    controls = goals.build_v0_20_terminal_controls()
    corrupt_f3 = next(
        control
        for control in controls
        if control.family == "F3" and control.kind.value == "INVALID_TERMINAL_CERTIFICATE"
    )
    receipt = verification.verify_terminal_candidate(corrupt_f3.goal, corrupt_f3.candidate)
    assert receipt.passed is False
    assert receipt.verifier_class == corrupt_f3.goal.required_verifier_class

    for control in controls:
        observed = verification.verify_terminal_candidate(control.goal, control.candidate)
        assert observed.passed is control.expected_verification_pass, control.control_id


def test_affine_mean_value_certificate_accepts_any_interior_witness() -> None:
    verification = importlib.import_module("experiments.pct_goal_solver.v0_20_terminal_verification")
    control = next(
        control
        for control in goals.build_v0_20_terminal_controls()
        if control.family == "F2" and control.kind.value == "EXTERNAL_VALID_CERTIFICATE"
    )
    left, right = control.goal.inputs["interval"].value
    assert control.candidate.value.witness != (left + right) / 2
    assert verification.verify_terminal_candidate(control.goal, control.candidate).passed is True


def test_bezout_zero_pair_uses_total_gcd_convention() -> None:
    verification = importlib.import_module("experiments.pct_goal_solver.v0_20_terminal_verification")
    base = next(goal for goal in goals.build_v0_20_corpus()["SEALED_V0_20"] if goal.family == "F3")
    zero_goal = replace(
        base,
        inputs={
            "integer_a": replace(base.inputs["integer_a"], value=0),
            "integer_b": replace(base.inputs["integer_b"], value=0),
        },
    )
    candidate = Artifact(
        artifact_id="external:f3:zero",
        semantic_type=zero_goal.target.semantic_type,
        representation_class=zero_goal.target.representation_class,
        value=certify_bezout(0, 0),
        exactness_class="EXACT",
    )
    assert verification.verify_terminal_candidate(zero_goal, candidate).passed is True


def test_campaign_oracle_is_independent_and_x2_is_explicitly_unavailable() -> None:
    oracle_module = importlib.import_module("experiments.pct_goal_solver.campaign_oracles")
    forbidden = {
        "planner",
        "operators",
        "verifiers",
        "rigorous_math",
        "elliptic_periods",
    }
    dependencies = oracle_module.oracle_dependency_manifest()
    assert forbidden.isdisjoint(dependencies)

    x2 = next(goal for goal in goals.build_v0_20_corpus()["SEALED_V0_20"] if goal.family == "X2")
    oracle = oracle_module.build_independent_oracle(
        family=x2.family,
        inputs={key: artifact.value for key, artifact in x2.inputs.items()},
        constraints=dict(x2.constraints),
        tolerance=x2.allowed_numeric_tolerance,
    )
    assert oracle.authoritative is False
    assert oracle.availability == "UNAVAILABLE"
    assert oracle.reason == "NO_INDEPENDENT_X2_ORACLE"


def test_prospective_oracle_binds_structural_receipt_into_report_provenance() -> None:
    oracle_module = importlib.import_module("experiments.pct_goal_solver.campaign_oracles")
    receipt = oracle_module.oracle_independence_receipt()
    assert receipt["established"] is True
    assert len(receipt["source_sha256"]) == 64
    assert len(receipt["callable_binding_sha256"]) == 64
    assert receipt["callable_bindings"]
    assert "math.gcd" in receipt["reviewed_module_attributes"]
    assert "sp.diff" in receipt["reviewed_module_attributes"]

    goal = next(
        item
        for item in goals.build_v0_20_corpus()["VALIDATION_V0_20"]
        if item.family == "F1"
    )
    reported = goals.build_case_oracle(goal)
    assert reported["authoritative"] is True
    assert reported["authority_kind"] == "INDEPENDENT_MATHEMATICAL_ORACLE"
    assert reported["independence_receipt"] == receipt
    assert reported["independence_receipt_sha256"] == goals._digest(receipt)


def test_prospective_oracle_rejects_forbidden_from_import_source_injection() -> None:
    oracle_module = importlib.import_module("experiments.pct_goal_solver.campaign_oracles")
    module_file = oracle_module.Path(oracle_module.__file__).resolve()
    source = module_file.read_text(encoding="utf-8")
    injected = source + "\nfrom .planner import solve\n"
    receipt = oracle_module._assess_oracle_independence_source(injected, module_file)
    assert receipt["established"] is False
    assert receipt["reason"] == "UNREVIEWED_SOURCE_IMPORTS"


def test_prospective_oracle_callable_substitution_revokes_report_authority(monkeypatch) -> None:
    oracle_module = importlib.import_module("experiments.pct_goal_solver.campaign_oracles")
    goal = next(
        item
        for item in goals.build_v0_20_corpus()["VALIDATION_V0_20"]
        if item.family == "F1"
    )

    monkeypatch.setattr(oracle_module, "_f1", lambda _inputs: None)
    reported = goals.build_case_oracle(goal)
    assert reported["authoritative"] is False
    assert reported["authority_kind"] == "INDEPENDENCE_NOT_ESTABLISHED"
    assert reported["oracle_availability"] == "UNAVAILABLE"
    assert reported["reason"] == "ORACLE_INDEPENDENCE_NOT_ESTABLISHED"
    assert reported["independence_receipt"]["established"] is False
    assert (
        reported["independence_receipt"]["reason"]
        == "INTERNAL_CALLABLE_BINDING_MISMATCH"
    )


def test_prospective_oracle_in_place_code_substitution_revokes_authority(monkeypatch) -> None:
    oracle_module = importlib.import_module("experiments.pct_goal_solver.campaign_oracles")
    assert oracle_module.oracle_independence_receipt()["established"] is True

    def forged_f1(_inputs):
        return None

    monkeypatch.setattr(oracle_module._f1, "__code__", forged_f1.__code__)
    receipt = oracle_module.oracle_independence_receipt()
    assert receipt["established"] is False
    assert receipt["reason"] == "INTERNAL_CALLABLE_CODE_MISMATCH"


def test_prospective_oracle_in_place_module_substitution_revokes_warm_authority(
    monkeypatch,
) -> None:
    oracle_module = importlib.import_module("experiments.pct_goal_solver.campaign_oracles")
    assert oracle_module.oracle_independence_receipt()["established"] is True

    for module, attribute in (
        (oracle_module.math, "gcd"),
        (oracle_module.math, "isfinite"),
        (oracle_module.sp, "diff"),
        (oracle_module.sp, "Poly"),
    ):
        with monkeypatch.context() as patch:
            patch.setattr(module, attribute, lambda *args, **kwargs: None)
            receipt = oracle_module.oracle_independence_receipt()
            assert receipt["established"] is False, (module, attribute)
            assert receipt["reason"] == "MODULE_ATTRIBUTE_BINDING_MISMATCH"


def test_scored_g10_g11_roots_use_frozen_binary64_coordinates(monkeypatch) -> None:
    base_goals = importlib.import_module("experiments.pct_goal_solver.goals")

    def fail_trig(*_args, **_kwargs):
        raise AssertionError("scored goal construction must not call runtime trigonometry")

    with monkeypatch.context() as patch:
        patch.setattr(base_goals.math, "sin", fail_trig)
        patch.setattr(base_goals.math, "cos", fail_trig)
        g10 = {
            index: base_goals._BUILDERS["G10"](f"frozen:g10:{index}", index)
            for index in range(6)
        }
        g11 = {
            index: base_goals._BUILDERS["G11"](f"frozen:g11:{index}", index)
            for index in range(6)
        }
        for family in ("G10", "G11"):
            for index in range(6):
                goals._build_goal(f"frozen:{family.lower()}:{index}", family, index)

    def hex_points(value):
        return tuple((x.hex(), y.hex()) for x, y in value)

    assert hex_points(g10[0].inputs["body"].value) == (
        ("0x1.f89e910a9febep-1", "0x1.5a7c46826cf64p-3"),
        ("-0x1.475374cc77ddcp-1", "0x1.89b3d9960cbefp-1"),
        ("-0x1.6296387c501c8p-2", "-0x1.e052eb36a7fc5p-1"),
    )
    assert hex_points(g10[2].inputs["body"].value) == (
        ("0x1.e7984403158a2p-1", "0x1.38614a8b8c3afp-2"),
        ("-0x1.38614a8b8c3afp-2", "0x1.e7984403158a2p-1"),
        ("-0x1.e7984403158a2p-1", "-0x1.38614a8b8c3aep-2"),
        ("0x1.38614a8b8c3a5p-2", "-0x1.e7984403158a4p-1"),
    )
    assert hex_points(g10[4].inputs["body"].value) == tuple(
        (x.hex(), y.hex()) for x, y in base_goals._FROZEN_G10_PENTAGON
    )
    assert hex_points(g11[4].inputs["body_a"].value) == tuple(
        (x.hex(), y.hex()) for x, y in base_goals._FROZEN_G11_PENTAGON
    )
    assert hex_points(g11[4].inputs["body_b"].value) == tuple(
        (x.hex(), y.hex()) for x, y in base_goals._FROZEN_G11_PENTAGON_IMAGE
    )
    assert not hasattr(goals, "_regular_polygon")


def test_exact_and_nuisance_signatures_do_not_conflate_raw_cases() -> None:
    signatures = getattr(goals, "case_signatures", None)
    assert signatures is not None
    g2 = next(goal for goal in goals.build_v0_20_corpus()["SEALED_V0_20"] if goal.family == "G2")
    observation = g2.inputs["observation_matrix"]
    scaled = replace(
        g2,
        inputs={
            **g2.inputs,
            "observation_matrix": replace(
                observation,
                value=tuple(tuple(Fraction(7) * entry for entry in row) for row in observation.value),
            ),
        },
    )
    original_signature = signatures(g2)
    scaled_signature = signatures(scaled)
    assert original_signature.exact_sha256 != scaled_signature.exact_sha256
    assert original_signature.nuisance_relation == "G2_NONZERO_RATIONAL_SCALAR"
    assert original_signature.nuisance_sha256 == scaled_signature.nuisance_sha256


def test_provenance_uses_explicit_implementation_and_lock_manifests() -> None:
    manifest = campaign.build_implementation_manifest()
    paths = {row["path"] for row in manifest["files"]}
    assert {
        "experiments/pct_goal_solver/planner.py",
        "experiments/pct_goal_solver/v0_20_campaign.py",
        "experiments/pct_goal_solver/v0_20_goals.py",
        "experiments/pct_goal_solver/v0_20_terminal_verification.py",
        "experiments/pct_goal_solver/campaign_oracles.py",
    } <= paths
    assert all(len(row["sha256"]) == 64 for row in manifest["files"])
    lock_binding = campaign.build_dependency_lock_binding()
    assert set(lock_binding) == {"status", "lock_manifest_sha256", "files", "reason"}
    assert lock_binding["status"] in {"BOUND", "UNBOUND"}
    assert lock_binding["lock_manifest_sha256"] is None or len(lock_binding["lock_manifest_sha256"]) == 64


def test_no_macro_use_receives_no_conservation_or_efficiency_credit() -> None:
    def case(mode: str) -> dict:
        return {
            "goal_id": "sealed:test",
            "family": "X1",
            "observation": {
                "verdict": "PASS",
                "macro_ids": [],
                "expanded_state_count": 3,
                "primitive_execution_count": 3,
                "semantic_certificate": {"complete": True, "verdict": "PASS", "mode": mode},
            },
        }

    modes = {
        "EXPLICIT/PRIMITIVE": {"cases": [case("primitive")]},
        "EXPLICIT/SYNTHESIZED": {"cases": [case("synthesized")]},
    }
    analysis = campaign._macro_analysis(modes)
    assert analysis["macro_use_count"] == 0
    assert analysis["exact_conservation_count"] == 0
    assert analysis["efficiency_credit_count"] == 0


def test_unauthorized_macro_claim_cannot_earn_credit_even_with_forged_parity() -> None:
    certificate = {"complete": True, "verdict": "PASS", "candidate": "same"}

    def case(*, macro_ids: list[str], expanded: int, executions: int) -> dict:
        return {
            "goal_id": "sealed:forged-macro",
            "family": "X1",
            "observation": {
                "verdict": "PASS",
                "macro_ids": macro_ids,
                "expanded_state_count": expanded,
                "primitive_execution_count": executions,
                "semantic_certificate": certificate,
            },
        }

    modes = {
        "EXPLICIT/PRIMITIVE": {
            "cases": [case(macro_ids=[], expanded=9, executions=7)]
        },
        "EXPLICIT/SYNTHESIZED": {
            "cases": [case(macro_ids=["forged:macro"], expanded=1, executions=1)]
        },
    }
    analysis = campaign._macro_analysis(modes)
    row = analysis["evaluations"][0]
    assert row["unauthorized_macro_claim"] is True
    assert row["macro_rescue"] is True
    assert row["exact_conservation"] is False
    assert row["work_reduced"] is False
    assert row["efficiency_credit"] is False
    assert analysis["unauthorized_macro_claim_count"] == 1
    assert analysis["macro_rescue_count"] == 1

    primitive_claim = {
        "EXPLICIT/PRIMITIVE": {
            "cases": [case(macro_ids=["forged:primitive"], expanded=9, executions=7)]
        },
        "EXPLICIT/SYNTHESIZED": {
            "cases": [case(macro_ids=[], expanded=1, executions=1)]
        },
    }
    primitive_analysis = campaign._macro_analysis(primitive_claim)
    primitive_row = primitive_analysis["evaluations"][0]
    assert primitive_row["primitive_macro_claim"] is True
    assert primitive_row["unauthorized_macro_claim"] is True
    assert primitive_row["macro_rescue"] is True

    binding_claim = {
        "EXPLICIT/PRIMITIVE": {
            "cases": [case(macro_ids=[], expanded=9, executions=7)]
        },
        "EXPLICIT/SYNTHESIZED": {
            "cases": [case(macro_ids=[], expanded=1, executions=1)]
        },
    }
    binding_claim["EXPLICIT/SYNTHESIZED"]["cases"][0]["observation"][
        "semantic_certificate"
    ] = {
        **certificate,
        "macro_bindings": {
            "type": "tuple",
            "items": [{"forged": "binding"}],
        },
    }
    binding_analysis = campaign._macro_analysis(binding_claim)
    binding_row = binding_analysis["evaluations"][0]
    assert binding_row["synthesized_macro_claim"] is True
    assert binding_row["unauthorized_macro_claim"] is True
    assert binding_row["efficiency_credit"] is False

    path_claim = {
        "EXPLICIT/PRIMITIVE": {
            "cases": [case(macro_ids=[], expanded=9, executions=7)]
        },
        "EXPLICIT/SYNTHESIZED": {
            "cases": [case(macro_ids=[], expanded=1, executions=1)]
        },
    }
    path_claim["EXPLICIT/SYNTHESIZED"]["cases"][0]["observation"]["operator_path"] = [
        "CERT_MACRO:forged",
        "VERIFY_CANDIDATE",
    ]
    path_analysis = campaign._macro_analysis(path_claim)
    path_row = path_analysis["evaluations"][0]
    assert path_row["synthesized_macro_claim"] is True
    assert path_row["unauthorized_macro_claim"] is True
    assert path_row["macro_rescue"] is True


def test_hash_lock_parser_requires_every_exact_pin_and_full_sha256() -> None:
    valid = """
    alpha==1.2.3 \\
        --hash=sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    beta-core==4.5+local \\
        --hash=sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
    """
    assert campaign._is_hash_locked_requirements(valid) is True
    assert campaign._is_hash_locked_requirements(
        valid + "gamma==7.0\n"
    ) is False
    assert campaign._is_hash_locked_requirements(
        "gamma>=7.0 \\\n--hash=sha256:" + "c" * 64
    ) is False
    assert campaign._is_hash_locked_requirements(
        "gamma==7.0 \\\n--hash=sha256:" + "C" * 64
    ) is False
    assert campaign._is_hash_locked_requirements(
        "gamma==7.0 \\\n--hash=sha256:" + "d" * 63
    ) is False
    assert campaign._is_hash_locked_requirements("gamma==7.0 \\") is False
