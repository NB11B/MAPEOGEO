"""Kernel Adapter: Read-only access to frozen Kernel v1 transformation grammar."""

import json
from pathlib import Path
from typing import Dict, Any

class KernelV1Adapter:
    def __init__(self, kernel_manifest_path: Path):
        self.manifest_path = kernel_manifest_path
        with open(kernel_manifest_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)
        
        m5_path = Path(self.manifest["artifact_hashes"]["m5_grammar_specification"]["path"])
        with open(m5_path, "r", encoding="utf-8") as f:
            self.m5_spec = json.load(f)

    @property
    def valid_deltas(self):
        return self.m5_spec["coordinates"]["Delta"]["alphabet"]

    @property
    def valid_invariants(self):
        return self.m5_spec["coordinates"]["I"]["alphabet"]

    @property
    def valid_witnesses(self):
        return self.m5_spec["coordinates"]["W"]["alphabet"]

    @property
    def valid_scopes(self):
        return self.m5_spec["coordinates"]["sigma"]["alphabet"]

    @property
    def valid_polarities(self):
        return self.m5_spec["coordinates"]["Pi"]["alphabet"]
