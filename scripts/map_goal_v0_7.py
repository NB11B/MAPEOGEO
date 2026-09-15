#!/usr/bin/env python3
from __future__ import annotations
import base64
import gzip
from pathlib import Path
_IMPL=Path(__file__).with_name("map_goal_v0_7_impl.py.b64")
_payload=base64.b64decode(_IMPL.read_text(encoding="utf-8"))
_code=gzip.decompress(_payload).decode("utf-8")
exec(compile(_code,str(_IMPL)+"::decoded-gzip","exec"),globals(),globals())
