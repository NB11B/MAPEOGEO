#!/usr/bin/env python3
"""Wrapper script for validating MAPEOGEO PCT v0.10 artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.validate_pct_v0_10 import main

if __name__ == "__main__":
    sys.exit(main())
