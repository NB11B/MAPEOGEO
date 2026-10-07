"""Generate Public API Specification for MAPEOGEO v2."""

import importlib
import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

modules = [
    "mapeogeo.kernel",
    "mapeogeo.grammar",
    "mapeogeo.graph",
    "mapeogeo.routing",
    "mapeogeo.proof",
    "mapeogeo.psmsl",
    "mapeogeo.domains.mathematics",
    "mapeogeo.domains.physics",
    "mapeogeo.domains.software",
]

api_catalog = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "MAPEOGEO v2 Public API Specification",
    "canonical_version": "v2.0.0-rc1-candidate",
    "public_surface": {},
}

total_symbols = 0
for m in modules:
    mod = importlib.import_module(m)
    symbols = getattr(mod, "__all__", [k for k in dir(mod) if not k.startswith("_")])
    symbols = sorted(symbols)
    total_symbols += len(symbols)
    api_catalog["public_surface"][m] = {
        "count": len(symbols),
        "symbols": symbols,
    }

api_catalog["total_public_symbols"] = total_symbols
print("Total public symbols:", total_symbols)
Path("artifacts/releases/V2_PUBLIC_API.json").write_text(json.dumps(api_catalog, indent=2) + "\n")
print("Wrote artifacts/releases/V2_PUBLIC_API.json")
