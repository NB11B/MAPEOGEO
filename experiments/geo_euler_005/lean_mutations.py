"""Negative Lean kernel tests: mutated grammar must not inherit original proof."""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
GENERATED=ROOT/"MAPEOGEOFormal"/"GeoEulerSelected.lean"
MUTATIONS={
    "addition_successor_removed":(
        "Nat.succ (selectedAdd a b)",
        "selectedAdd a b"),
    "multiplication_recurrence_replaced":(
        "selectedAdd (selectedMul a b) a",
        "Nat.succ (selectedMul a b)"),
    "multiplication_zero_changed":(
        "| 0 => 0\n  | b + 1 => selectedAdd",
        "| 0 => 1\n  | b + 1 => selectedAdd")
}

def main():
    original=GENERATED.read_text(encoding="utf-8")
    with TemporaryDirectory(dir=ROOT) as tmp:
        for name,(before,after) in MUTATIONS.items():
            if original.count(before)!=1:
                raise RuntimeError(f"mutation anchor invalid: {name}")
            target=Path(tmp)/(name+".lean")
            target.write_text(original.replace(before,after),encoding="utf-8")
            result=subprocess.run(["lake","env","lean",str(target)],cwd=ROOT,
                                  capture_output=True,text=True,timeout=120)
            if result.returncode==0:
                raise AssertionError(f"UNSAFE: mutated definition certified: {name}")
            print(f"REJECTED {name}: Lean exit code {result.returncode}")
    print("All intentional wrong-grammar mutations rejected by Lean")

if __name__=="__main__":
    main()
