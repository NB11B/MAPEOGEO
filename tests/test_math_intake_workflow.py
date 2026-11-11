"""Keep real proof verification independent without relaxing qualification.

These checks inspect the Actions job/command contracts and execute the actual
aggregate shell gate. They do not simulate Lean or claim proof verification.
"""
from __future__ import annotations

import itertools
import os
from pathlib import Path
import shlex
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/math-intake-v0-11.yml"
QUALIFIED = "mapeogeo-pinch-intake-v0.11"


@pytest.fixture
def workflow():
    # BaseLoader preserves GitHub's `on` key and action input scalars as strings.
    return yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


@pytest.fixture
def jobs(workflow):
    return workflow["jobs"]


def commands(job):
    for index, step in enumerate(job["steps"]):
        for line in step.get("run", "").replace("\\\n", " ").splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                yield index, shlex.split(line)


def action_steps(job, action):
    return [(i, step) for i, step in enumerate(job["steps"])
            if step.get("uses", "").split("@")[0] == action]


def test_python_and_proof_jobs_are_independent_and_fail_closed(jobs):
    assert {"python-tests", "proof-verification", "math-intake-v0-11"} <= jobs.keys(), (
        "Python discovery and real proofs need independent jobs plus the existing qualification status"
    )
    for name in ("python-tests", "proof-verification"):
        job = jobs[name]
        assert not job.get("needs"), f"{name} must run even when the other job fails"
        assert "if" not in job
        assert job["timeout-minutes"] == "40"
        assert "continue-on-error" not in job
        for step in job["steps"]:
            assert "continue-on-error" not in step
            assert step.get("if") in (None, "always()", "success()")
    python_commands = [command for _, command in commands(jobs["python-tests"])]
    assert python_commands.count(["pytest"]) == 1, "Keep unrestricted root discovery"
    assert [command for command in python_commands if "pytest" in command[:3]] == [["pytest"]]
    for path in ("scripts/audit_pinch_source_v0_11.py", "scripts/pinch_contracts_v0_11.py",
                 "scripts/pinch_intake_v0_11.py", "tests/test_pinch_source_audit_v0_11.py",
                 "tests/test_pinch_intake_v0_11.py", "tests/validate_pinch_intake_v0_11.py"):
        assert ["python", "-m", "py_compile", path] in python_commands
    assert not any(command[:1] == ["pytest"] for _, command in commands(jobs["proof-verification"]))


# Scientific thresholds and graph/certificate connections are qualification
# boundaries: moving jobs must not change these commands or their order.
PROOF_COMMANDS = [
    '''python scripts/independent_dual_view_v0_6.py "$RUNNER_TEMP/mapeogeo-source/math-deep.pdf"
       --base-graph data/gallier_quaintance_graph_v0_3.json.gz --out-dir "$RUNNER_TEMP/mapeogeo-v06"
       --min-declarations 1355 --min-definitions 463 --min-proofs 609 --min-resolved-deps 638
       --max-unresolved-rate 0.0938 --min-eo-direct 0.70 --min-geo-direct 0.70
       --min-dual-direct 0.60 --max-no-direct 0.15 --max-permutation-p 0.05''',
    '''python scripts/map_goal_v0_7.py "$RUNNER_TEMP/mapeogeo-source/math-deep.pdf"
       --v06-dir "$RUNNER_TEMP/mapeogeo-v06" --out-dir "$RUNNER_TEMP/mapeogeo-v07"
       --min-holdout-edges 100 --min-dual-filter-recall 0.75 --min-dual-filter-reduction 0.20
       --max-retrieval-p 0.05 --min-same-semantics-promotions 2 --min-total-certificates 4''',
    '''python scripts/formal_bridge_v0_8.py
       --base-graph "$RUNNER_TEMP/mapeogeo-v07/mapeogeo_map_goal_v0_7_graph.json"
       --bindings formal/source_bindings_v0_8.json --lean-file MAPEOGEOFormal/SourceBound.lean
       --out-dir "$RUNNER_TEMP/mapeogeo-v08" --independent-checker leanchecker
       --independent-checker-status PASS --nanoda-status TOOLING_BLOCKED''',
    'python tests/validate_formal_bridge_v0_8.py "$RUNNER_TEMP/mapeogeo-v08"',
    '''python scripts/proof_paths_v0_9.py
       --base-graph "$RUNNER_TEMP/mapeogeo-v08/mapeogeo_formal_v0_8_graph.json.gz"
       --bindings formal/proof_paths_v0_9.json --lean-file MAPEOGEOFormal/ProofPaths.lean
       --out-dir "$RUNNER_TEMP/mapeogeo-v09" --independent-checker leanchecker
       --independent-checker-status PASS''',
    'python tests/validate_proof_paths_v0_9.py "$RUNNER_TEMP/mapeogeo-v09"',
    'python scripts/audit_pinch_source_v0_11.py --graph "$RUNNER_TEMP/mapeogeo-v09/mapeogeo_s5_v0_9_graph.json.gz"',
    '''python scripts/pinch_intake_v0_11.py
       --base-graph "$RUNNER_TEMP/mapeogeo-v09/mapeogeo_s5_v0_9_graph.json.gz"
       --bindings formal/pinch_bindings_v0_11.json --lean-file MAPEOGEOFormal/PinchV011.lean
       --out-dir artifacts/pinch_intake_v0_11 --independent-checker leanchecker
       --independent-checker-status PASS
       --checker-evidence-file "$RUNNER_TEMP/checker-evidence/leanchecker.log"''',
    'python tests/validate_pinch_intake_v0_11.py artifacts/pinch_intake_v0_11',
]


def test_proof_job_preserves_scientific_checks_and_real_checker_order(jobs, workflow):
    proof = jobs["proof-verification"]
    actual = [(index, argv) for index, argv in commands(proof)
              if argv[:1] == ["python"] and len(argv) > 1 and argv[1].endswith(".py")]
    assert [argv for _, argv in actual] == [shlex.split(command) for command in PROOF_COMMANDS]
    for index, _ in actual:
        assert "if" not in proof["steps"][index]
        assert "||" not in proof["steps"][index]["run"]
    [(lean_index, lean)] = action_steps(proof, "leanprover/lean-action")
    assert lean["uses"] == "leanprover/lean-action@38fbc41a8c28c4cbaec22d7f7de508ec2e7c0dd9"
    assert lean["with"] == {
        "auto-config": "false", "build": "true", "test": "false",
        "use-mathlib-cache": "true", "use-github-cache": "true",
        "leanchecker": "true", "nanoda": "false",
    }
    assert "if" not in lean
    assert lean_index < actual[0][0]
    assert sum(len(action_steps(job, "leanprover/lean-action")) for job in jobs.values()) == 1
    assert workflow["env"]["SOURCE_URL"] == "https://www.cis.upenn.edu/~jean/math-deep.pdf"
    download = next(step for step in proof["steps"] if "curl " in step.get("run", ""))
    assert "if" not in download
    assert "--fail" in shlex.split(download["run"])
    cleanup = next(step for step in proof["steps"]
                   if step.get("run") == 'rm -f "$RUNNER_TEMP/mapeogeo-source/math-deep.pdf"')
    assert cleanup["if"] == "always()"


def test_lean_runs_before_fallible_source_download_and_audit(jobs):
    proof = jobs["proof-verification"]
    [(lean_index, _)] = action_steps(proof, "leanprover/lean-action")
    download_index = next(i for i, step in enumerate(proof["steps"])
                          if "curl " in step.get("run", ""))
    audit_index = next(i for i, argv in commands(proof)
                       if argv[:2] == ["python", "scripts/audit_pinch_source_v0_11.py"])
    assert lean_index < download_index < audit_index, (
        "A failed source fetch/audit must not prevent real Lean verification"
    )


def test_existing_qualification_status_runs_after_every_dependency_outcome(jobs):
    gate = jobs["math-intake-v0-11"]
    assert set(gate["needs"]) == {"python-tests", "proof-verification"}
    assert gate["if"] == "always()"
    assert "continue-on-error" not in gate
    check = gate["steps"][0]
    assert check["id"] == "require-success"
    assert "if" not in check and "continue-on-error" not in check
    assert check["env"] == {
        "PYTHON_RESULT": "${{ needs.python-tests.result }}",
        "PROOF_RESULT": "${{ needs.proof-verification.result }}",
        "EVIDENCE_ARTIFACT_ID": "${{ needs.proof-verification.outputs.evidence-artifact-id }}",
    }
    assert "${{" not in check["run"], "Pass job results via env, not shell interpolation"


@pytest.mark.parametrize("python_result,proof_result", list(itertools.product(
    ("success", "failure", "cancelled", "skipped", ""), repeat=2)))
def test_qualification_shell_requires_both_successes(jobs, python_result, proof_result):
    script = jobs["math-intake-v0-11"]["steps"][0]["run"]
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
        env={**os.environ, "PYTHON_RESULT": python_result, "PROOF_RESULT": proof_result,
             "EVIDENCE_ARTIFACT_ID": "12345"},
        capture_output=True, text=True, check=False,
    )
    assert (result.returncode == 0) == (python_result == proof_result == "success"), result.stdout + result.stderr


@pytest.mark.parametrize("artifact_id", ["", "0", "-1", "abc", "1,2", "12\n34", " 123 "])
def test_qualification_refuses_missing_or_malformed_artifact_id(jobs, artifact_id):
    script = jobs["math-intake-v0-11"]["steps"][0]["run"]
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
        env={**os.environ, "PYTHON_RESULT": "success", "PROOF_RESULT": "success",
             "EVIDENCE_ARTIFACT_ID": artifact_id},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0, "Never let download-artifact fall back to all artifacts"


def test_source_binding_audit_requires_fresh_validated_v09_graph(jobs):
    proof = jobs["proof-verification"]
    argv_by_step = list(commands(proof))
    validation_index = next(i for i, argv in argv_by_step
                            if argv[:2] == ["python", "tests/validate_proof_paths_v0_9.py"])
    audit_index = next(i for i, argv in argv_by_step
                       if argv[:2] == ["python", "scripts/audit_pinch_source_v0_11.py"])
    graph = "$RUNNER_TEMP/mapeogeo-v09/mapeogeo_s5_v0_9_graph.json.gz"
    assert validation_index < audit_index
    assert [argv for i, argv in argv_by_step if i == audit_index] == [
        ["test", "-s", graph],
        ["python", "scripts/audit_pinch_source_v0_11.py", "--graph", graph],
    ], "Require the fresh graph before auditing; never use the stale fallback"


def test_qualified_artifact_is_published_only_after_aggregate_success(jobs):
    proof = jobs["proof-verification"]
    [(staging_index, staging)] = action_steps(proof, "actions/upload-artifact")
    assert staging_index == len(proof["steps"]) - 1
    assert staging["if"] == "success()"
    assert "unqualified" in staging["with"]["name"]
    assert staging["with"]["name"] != QUALIFIED
    assert staging["with"]["retention-days"] == "1"
    assert staging["with"]["if-no-files-found"] == "error"
    assert staging["with"]["path"] == "artifacts/pinch_intake_v0_11/"
    gate = jobs["math-intake-v0-11"]
    [(download_index, download)] = action_steps(gate, "actions/download-artifact")
    [(publish_index, publish)] = action_steps(gate, "actions/upload-artifact")
    assert 0 < download_index < publish_index
    assert download["if"] == publish["if"] == "success()"
    assert download["with"]["path"] == staging["with"]["path"]
    assert publish["with"] == {"name": QUALIFIED, "path": staging["with"]["path"],
                                "if-no-files-found": "error", "retention-days": "30"}
    assert all("continue-on-error" not in step for step in gate["steps"])


def test_artifact_download_uses_producer_id_when_only_failed_jobs_are_rerun(jobs):
    # A successful proof job is not rerun when only Python/aggregate failed.
    # Its immutable artifact ID must survive a change in github.run_attempt.
    proof = jobs["proof-verification"]
    [(_, staging)] = action_steps(proof, "actions/upload-artifact")
    assert staging.get("id") == "stage-evidence"
    assert proof.get("outputs") == {
        "evidence-artifact-id": "${{ steps.stage-evidence.outputs.artifact-id }}",
    }
    [(_, download)] = action_steps(jobs["math-intake-v0-11"], "actions/download-artifact")
    assert download["with"] == {
        "artifact-ids": "${{ needs.proof-verification.outputs.evidence-artifact-id }}",
        "path": "artifacts/pinch_intake_v0_11/",
        "merge-multiple": "true",
    }


def test_workflow_regression_runs_in_ci_with_declared_parser_dependency(workflow, jobs):
    test_path = "tests/test_math_intake_workflow.py"
    for event in ("push", "pull_request"):
        assert test_path in workflow["on"][event]["paths"]
    bridge = yaml.load((ROOT / ".github/workflows/gfyproof_bridge_v1.yml").read_text(), Loader=yaml.BaseLoader)
    bridge_commands = [argv for _, argv in commands(bridge["jobs"]["verify"])]
    assert any(argv[:3] == ["python", "-m", "pytest"] and test_path in argv for argv in bridge_commands)
    for job in (jobs["python-tests"], bridge["jobs"]["verify"]):
        assert any(argv[:4] == ["python", "-m", "pip", "install"] and
                   any(arg.lower().startswith("pyyaml") for arg in argv) for _, argv in commands(job))
