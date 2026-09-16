from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECONSTRUCTOR = ROOT / "scripts" / "reconstruct_pipeline.py"
RIGOR_INTAKE = ROOT / "scripts" / "rigor_expansion_v0_21.py"
FROZEN_DECLARATIONS = ROOT / "formal" / "source_declarations_v0_21.json.gz"
FROZEN_EVIDENCE = ROOT / "evidence" / "v0_21_source_admission_manifest.json"


def test_v0_21_is_an_offline_reconstruction_target():
    text = RECONSTRUCTOR.read_text(encoding="utf-8")
    assert '"v0.21"' in text
    assert "rigor_expansion_v0_21.py" in text
    assert "source_declarations_v0_21.json.gz" in text
    assert "source_admission_v0_21.py" not in text.split("# Stage: v0.21")[-1]


def test_frozen_source_identity_inputs_are_committed():
    assert FROZEN_DECLARATIONS.exists()
    assert FROZEN_DECLARATIONS.stat().st_size > 100_000
    assert FROZEN_EVIDENCE.exists()
    assert RIGOR_INTAKE.exists()
