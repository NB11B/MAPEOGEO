"""Slice 10 Tests: Campaign Execution, Reporting & Clean-Room Pipeline Reconstruction."""

import json
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_FILE = REPO_ROOT / "docs" / "V0_22_WAVE_F5_REPORT.md"
WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "wave-f5-v0-22.yml"


def test_wave_f5_campaign_execution(tmp_path):
    from scripts.wave_f5_campaign import run_wave_f5_campaign

    certs_out = tmp_path / "wave_f5_certificates.json"
    ledger_out = tmp_path / "wave_f5_campaign_ledger.json"

    result = run_wave_f5_campaign(output_certs=certs_out, output_ledger=ledger_out)
    assert result["total_contracts"] == 18
    assert result["passed_contracts"] == 18
    assert result["falsifications_verified"] >= 18
    assert certs_out.exists()
    assert ledger_out.exists()

    with open(certs_out, "r", encoding="utf-8") as f:
        certs_data = json.load(f)
    assert certs_data["schema_version"] == "0.22"
    assert len(certs_data["certificates"]) == 18


def test_wave_f5_report_generation(tmp_path):
    from scripts.generate_wave_f5_report import generate_report

    report_out = tmp_path / "V0_22_WAVE_F5_REPORT.md"
    report_text = generate_report(output_path=report_out)

    assert "Wave F5" in report_text
    assert "Functional Analysis" in report_text
    assert "Ordinary Differential Equations" in report_text
    assert "Q01" in report_text and "Q18" in report_text
    assert report_out.exists()


def test_reconstruct_pipeline_supports_wave_f5():
    reconstruct_script = REPO_ROOT / "scripts" / "reconstruct_pipeline.py"
    with open(reconstruct_script, "r", encoding="utf-8") as f:
        content = f.read()
    assert "wave_f5" in content, "scripts/reconstruct_pipeline.py must support --target-stage wave_f5"


def test_workflow_file_exists():
    assert WORKFLOW_FILE.exists(), ".github/workflows/wave-f5-v0-22.yml must exist"
    with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
        workflow_content = f.read()
    assert "wave_f5" in workflow_content or "pytest" in workflow_content
