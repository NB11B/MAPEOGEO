#!/usr/bin/env python3
from pathlib import Path
import gzip

payload = Path(__file__).with_name("run_v0_3_impl.py.gz")
source = gzip.decompress(payload.read_bytes())
virtual_file = str(Path(__file__).with_name("run_v0_3_impl.py"))
exec(compile(source, virtual_file, "exec"), {"__name__": "__main__", "__file__": virtual_file})
