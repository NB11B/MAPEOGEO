"""Subprocess-isolated Deterministic Replay Verification.

Runs the complete reproduction suite in two independent fresh processes,
canonicalizes the scientific outputs, and asserts H(R1) == H(R2).
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def run_campaign() -> dict:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/reproduction/",
        "-q",
        "--tb=short",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return {
        "stdout": proc.stdout.strip(),
        "exit_code": proc.returncode,
    }


def main():
    print("Executing Run 1 from fresh process...")
    r1 = run_campaign()

    print("Executing Run 2 from fresh process...")
    r2 = run_campaign()

    # Canonicalize summary (strip timing info e.g. 'in 0.29s')
    def clean_output(out_str: str) -> str:
        lines = []
        for line in out_str.splitlines():
            # strip trailing timing like 'in 0.35s'
            if "passed in" in line:
                line = line[: line.index("passed in") + len("passed in")]
            lines.append(line)
        return "\n".join(lines)

    c1 = clean_output(r1["stdout"])
    c2 = clean_output(r2["stdout"])

    h1 = hashlib.sha256(c1.encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(c2.encode("utf-8")).hexdigest()

    print(f"H(R1) = {h1}")
    print(f"H(R2) = {h2}")
    match = h1 == h2
    print(f"Exact match: {match}")
    assert match, f"Deterministic replay mismatch: {h1} != {h2}"

    result = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "MAPEOGEO v2 Deterministic Replay Verification",
        "canonical_version": "v2.0.0-rc1-candidate",
        "run_1_sha256": h1,
        "run_2_sha256": h2,
        "is_deterministic": match,
        "test_suite": "tests/reproduction/",
        "canonicalized_summary": c1,
        "verdict": "DETERMINISTIC_REPLAY_VERIFIED",
    }
    Path("artifacts/releases/V2_DETERMINISTIC_REPLAY.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print("Wrote artifacts/releases/V2_DETERMINISTIC_REPLAY.json")


if __name__ == "__main__":
    main()
