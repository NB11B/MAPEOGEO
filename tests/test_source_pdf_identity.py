"""Source drift must never silently reuse accepted statement bindings."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/check_source_pdf_identity.py'


def run_guard(tmp_path, payload=b'accepted synthetic source', metadata=None):
    pdf = tmp_path / 'source.pdf'
    pdf.write_bytes(payload)
    expected = {'sha256': hashlib.sha256(b'accepted synthetic source').hexdigest(),
                'bytes': len(b'accepted synthetic source')}
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'source_pdf': expected if metadata is None else metadata}))
    result = subprocess.run([sys.executable, str(SCRIPT), str(pdf), '--manifest', str(manifest)],
                            text=True, capture_output=True)
    return result, pdf, manifest


def test_exact_source_passes_without_modification(tmp_path):
    result, pdf, manifest = run_guard(tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['status'] == 'PASS'
    assert report['observed'] == report['expected']
    assert pdf.read_bytes() == b'accepted synthetic source'
    assert json.loads(manifest.read_text())['source_pdf'] == report['expected']


def test_same_size_mutation_is_rejected(tmp_path):
    result, _, _ = run_guard(tmp_path, payload=b'rejected synthetic source')
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report['reason'] == 'SOURCE_IDENTITY_MISMATCH'
    assert report['expected']['sha256'] != report['observed']['sha256']
    assert report['expected']['bytes'] == report['observed']['bytes']


@pytest.mark.parametrize('metadata', [{}, {'sha256':'bad','bytes':1},
    {'sha256':'0'*64,'bytes':True}, {'sha256':'0'*64,'bytes':0},
    {'sha256':'0'*64,'bytes':'25'}, {'sha256':'0'*64}, {'bytes':25}])
def test_malformed_pin_fails_closed(tmp_path, metadata):
    result, _, _ = run_guard(tmp_path, metadata=metadata)
    assert result.returncode == 2, result.stderr
    assert json.loads(result.stdout)['reason'] == 'INVALID_INPUT'


def test_size_mismatch_is_rejected_even_when_digest_matches(tmp_path):
    payload = b'accepted synthetic source'
    result, _, _ = run_guard(tmp_path, metadata={'sha256':hashlib.sha256(payload).hexdigest(),'bytes':999})
    assert result.returncode == 1
    assert json.loads(result.stdout)['reason'] == 'SOURCE_IDENTITY_MISMATCH'


def test_missing_source_fails_closed(tmp_path):
    result, pdf, manifest = run_guard(tmp_path)
    pdf.unlink()
    result = subprocess.run([sys.executable, str(SCRIPT), str(pdf), '--manifest', str(manifest)],text=True,capture_output=True)
    assert result.returncode == 2
    assert json.loads(result.stdout)['reason'] == 'INVALID_INPUT'


def test_repository_source_manifest_has_required_identity_fields():
    source = json.loads((ROOT/'evidence/v0_7_acceptance_manifest.json').read_text())['source_pdf']
    assert source['sha256'] == 'a1f91e337445851d27f2f4adb61e8ccc0f8fac941f9e0254ad94ba6b91c7c49b'
    assert source['bytes'] == 24629575
