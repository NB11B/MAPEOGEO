"""Mutation must invalidate the stated theorem rather than merely change samples."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[2]
p=root/"MAPEOGEOFormal"/"GeoOPRSelected.lean"
s=p.read_text()
old="theorem selected_spec (a b : Nat) : selected a b = a + a*b := by"
if s.count(old)!=1:raise RuntimeError("missing theorem anchor")
bad=s.replace(old,"theorem selected_spec (a b : Nat) : selected a b = a + a*b + 1 := by")
with tempfile.TemporaryDirectory(dir=root) as d:
    f=Path(d)/"wrong.lean";f.write_text(bad)
    r=subprocess.run(["lake","env","lean",str(f)],cwd=root,capture_output=True,text=True,timeout=120)
    if r.returncode==0:raise AssertionError("invalid theorem accepted")
    if "error:" not in r.stdout+r.stderr:raise AssertionError("failure without Lean error diagnostic")
print("wrong theorem rejected by Lean")
