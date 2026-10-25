"""Require wrong inferred interaction coefficient to fail Lean, with diagnostics."""
from pathlib import Path
import subprocess,sys
from emit_lean import emit
root=Path(__file__).resolve().parents[2]
try:
    emit(3)
    p=subprocess.run(["lake","env","lean","MAPEOGEOFormal/GeoPrimeInferred.lean"],
                     cwd=root,capture_output=True,text=True,timeout=180)
    if p.returncode==0:
        raise AssertionError("wrong coefficient obtained a valid theorem")
    if "error:" not in p.stdout+p.stderr:
        raise AssertionError("failure was not a Lean proof diagnostic")
    print("Wrong coefficient 3 rejected by the Lean kernel")
finally:
    emit()
