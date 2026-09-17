from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from .constants import KNOWLEDGE_BASELINE_SHA
from .identity import verify_frozen_checkout


CAPABILITY_MATRIX = {
    "E5_DIRECT_CHAIN_MAP_CORRUPTION": "DIRECT_REPLAY",
    "E5_CHAIN_MAP_VALID_SEMANTIC_ADVERSARY": "CAPABILITY_NOT_EXPOSED",
    "E9_APPLICABILITY_REFUSAL": "DIRECT_REPLAY",
    "E11_PROBE_NULLSPACE": "CAPABILITY_NOT_EXPOSED",
    "E14_PERSISTENCE_INFORMATION_LOSS": "DIRECT_REPLAY",
    "E16_CROSS_VIEW_CORRESPONDENCE": "CAPABILITY_NOT_EXPOSED",
    "E17_EXACT_VS_FLOAT_RANK": "ADAPTER_REQUIRED",
    "E18_INCIDENCE_CORRUPTION_LOCALIZATION": "CAPABILITY_NOT_EXPOSED",
    "E23_GENERIC_COUNTEREXAMPLE_SEARCH": "CAPABILITY_NOT_EXPOSED",
    "E24_GRAPH_ATLAS_RELATIONAL_DISCRIMINATION": "CAPABILITY_NOT_EXPOSED",
}


def classify_main_capabilities(main_root: Path) -> dict[str, str]:
    verify_frozen_checkout(main_root, KNOWLEDGE_BASELINE_SHA)
    required = {
        "E5_DIRECT_CHAIN_MAP_CORRUPTION": main_root / "mapeogeo" / "pct" / "maps.py",
        "E9_APPLICABILITY_REFUSAL": main_root / "mapeogeo" / "pct" / "geometry.py",
        "E14_PERSISTENCE_INFORMATION_LOSS": main_root / "mapeogeo" / "pct" / "persistence.py",
        "E17_EXACT_VS_FLOAT_RANK": main_root / "mapeogeo" / "pct" / "chain.py",
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Frozen-main advertised capability source missing: {missing}")
    return dict(CAPABILITY_MATRIX)


def invoke_main_pct(
    repo_root: Path,
    main_root: Path,
    request: dict[str, Any],
    *,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    verify_frozen_checkout(main_root, KNOWLEDGE_BASELINE_SHA)
    protocol = repo_root / "experiments" / "pct_e26_e31" / "main_runner_protocol.py"
    if not protocol.is_file():
        raise FileNotFoundError(f"Main runner protocol missing: {protocol}")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(main_root.resolve())
    proc = subprocess.run(
        [sys.executable, str(protocol.resolve())],
        input=json.dumps(request, sort_keys=True, separators=(",", ":")),
        text=True,
        cwd=main_root,
        env=env,
        capture_output=True,
        timeout=timeout_seconds,
    )
    raw = proc.stdout.strip()
    try:
        output = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Frozen-main protocol returned invalid JSON; rc={proc.returncode}; "
            f"stdout={raw!r}; stderr={proc.stderr!r}"
        ) from exc

    if proc.returncode != 0 or "error" in output:
        raise RuntimeError(
            f"Frozen-main protocol failed; rc={proc.returncode}; "
            f"output={output!r}; stderr={proc.stderr!r}"
        )
    if output.get("checkout_sha") != KNOWLEDGE_BASELINE_SHA:
        raise RuntimeError(
            "Frozen-main protocol executed wrong checkout: "
            f"{output.get('checkout_sha')} != {KNOWLEDGE_BASELINE_SHA}"
        )
    if output.get("experimental_branch_on_sys_path") is not False:
        raise RuntimeError("Experimental branch leaked into frozen-main subprocess sys.path")
    return output
