#!/usr/bin/env python3
from __future__ import annotations
import gzip
from pathlib import Path

_IMPL = Path(__file__).with_name("independent_dual_view_v0_6_impl.py.gz")
_code = gzip.decompress(_IMPL.read_bytes()).decode("utf-8")
exec(compile(_code, str(_IMPL) + "::decompressed", "exec"), globals(), globals())
