"""Wrong affine coefficient must cause a genuine Lean theorem error."""
from pathlib import Path
import subprocess,tempfile
from emit_lean import emit
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(dir=root) as td:
    bad=emit(Path(td)/"mutated.lean",mutation=True)
    proc=subprocess.run(["lake","env","lean",str(bad)],cwd=root,
                        capture_output=True,text=True,timeout=120)
    if proc.returncode==0:raise AssertionError("incorrect affine recurrence certified")
    if "error:" not in proc.stdout+proc.stderr:
        raise AssertionError("Lean error diagnostic missing")
print("Mutated Pell recurrence rejected")
