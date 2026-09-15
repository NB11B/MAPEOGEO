#!/usr/bin/env python3
from __future__ import annotations
import base64
import gzip
from pathlib import Path
_here=Path(__file__).resolve().parent
_parts=[(_here/f"map_goal_v0_7_impl.part{i}").read_text(encoding="utf-8").strip() for i in range(1,5)]
_payload=base64.b64decode("".join(_parts))
_code=gzip.decompress(_payload).decode("utf-8")
exec(compile(_code,str(_here/"map_goal_v0_7_impl.py.gz")+"::decoded-gzip","exec"),globals(),globals())
