"""Supply-chain and execution contract for the unmerged main repair branch."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "requirements-math-rigor-v0-20.lock"
WORKFLOW = ROOT / ".github" / "workflows" / "math-rigor-v0-20.yml"
SHA256_OPTION = re.compile(r"--hash=sha256:[0-9a-f]{64}(?:\s|$)")
PINNED_ACTION = re.compile(r"uses:\s+[^\s@]+@[0-9a-f]{40}(?:\s|$)")


def _logical_requirements(text: str) -> list[str]:
    logical: list[str] = []
    pending = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        pending = f"{pending} {line}".strip()
        if pending.endswith("\\"):
            pending = pending[:-1].rstrip()
            continue
        logical.append(pending)
        pending = ""
    assert not pending, "unterminated requirement continuation"
    return logical


def test_dependency_lock_is_exact_and_hash_required() -> None:
    """Removing a version pin or wheel hash must invalidate the CI lock."""

    rows = _logical_requirements(LOCK.read_text(encoding="utf-8"))
    assert rows
    for row in rows:
        requirement = row.split()[0]
        assert "==" in requirement
        assert "@" not in requirement
        assert SHA256_OPTION.search(row), row


def test_rigor_workflow_runs_the_integrity_boundary_on_the_repair_branch() -> None:
    """Dropping a required verification phase must break this branch contract."""

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "agent/main-math-rigor-v0-20" in text
    assert "python -m pip install --require-hashes --only-binary=:all:" in text
    assert "python -m pytest -q" in text
    assert text.count("scripts/reconstruct_pipeline.py --target-stage foundation") == 2
    assert "scripts/generate_mathematical_integrity_report.py" in text
    assert "v0_20_mathematical_integrity_report.json" in text
    assert "leanprover/lean-action@38fbc41a8c28c4cbaec22d7f7de508ec2e7c0dd9" in text
    assert "git diff --exit-code" in text


def test_every_external_action_is_pinned_to_an_immutable_commit() -> None:
    """Replacing an action SHA with a moving tag must fail review automatically."""

    lines = [line.strip() for line in WORKFLOW.read_text(encoding="utf-8").splitlines()]
    action_lines = [line for line in lines if line.startswith("uses:") or " uses:" in line]
    assert action_lines
    assert all(PINNED_ACTION.search(line) for line in action_lines), action_lines
