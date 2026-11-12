#!/usr/bin/env python3
"""Reject a changed source before replaying accepted statement bindings.

This checks identity only, not PDF semantics or mathematical correctness.
The accepted manifest is never changed and source bytes are never persisted here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re


def check_identity(pdf: Path, manifest: Path) -> dict:
    source = json.loads(manifest.read_text(encoding='utf-8'))['source_pdf']
    digest, size = source['sha256'], source['bytes']
    if not isinstance(digest, str) or re.fullmatch(r'[0-9a-f]{64}', digest) is None:
        raise ValueError('Manifest must provide a lowercase SHA-256 digest')
    if type(size) is not int or size <= 0:
        raise ValueError('Manifest must provide a positive integer byte count')
    h = hashlib.sha256()
    observed_size = 0
    with pdf.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
            observed_size += len(block)
    expected = {'sha256': digest, 'bytes': size}
    observed = {'sha256': h.hexdigest(), 'bytes': observed_size}
    matches = expected == observed
    return {'status': 'PASS' if matches else 'FAIL',
            'reason': 'SOURCE_IDENTITY_MATCH' if matches else 'SOURCE_IDENTITY_MISMATCH',
            'expected': expected, 'observed': observed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check_identity(args.pdf, args.manifest)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status':'FAIL', 'reason':'INVALID_INPUT', 'detail':str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
