"""Pagination diagnostics must never treat changed mathematical text as equivalent."""
import hashlib
import importlib.util
from pathlib import Path
import pytest

PATH = Path(__file__).resolve().parents[1] / 'scripts/audit_lp_pagination_binding.py'

def audit(*args):
    assert PATH.exists(), 'pagination audit helper is missing'
    spec = importlib.util.spec_from_file_location('pagination_audit', PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.audit_span(*args)

def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()

def test_pagination_only_change_is_separate_diagnostic():
    body = 'Theorem 47.9. synthetic test x >= 0\n47.3. COMPLEMENTARY SLACKNESS CONDITIONS '
    r = audit(body+'1655', sha(body+'1621'), 1655, 1621)
    assert r['historical_span_reconstructed'] is True
    assert r['normalization_version'] == 'LP47_9_TRAILING_RUNNING_HEADER_PAGE_V1'
    assert r['pagination_normalized_sha256'] == sha(body.rstrip())
    assert r['qualifies_source_edition'] is False
    assert 'text' not in r

def test_changed_assumption_does_not_match():
    tail='\n47.3. COMPLEMENTARY SLACKNESS CONDITIONS '
    assert audit('x > 0'+tail+'1655', sha('x >= 0'+tail+'1621'),1655,1621)['historical_span_reconstructed'] is False

@pytest.mark.parametrize('span,page', [('x=1655',1655), ('x\n47.3. COMPLEMENTARY SLACKNESS CONDITIONS 1656',1655), ('x\n47.3. COMPLEMENTARY SLACKNESS CONDITIONS 1655\nextra',1655)])
def test_nonmatching_running_header_is_rejected(span,page):
    with pytest.raises(ValueError): audit(span,'0'*64,page,1621)

@pytest.mark.parametrize('hash_value,current,old', [('bad',1655,1621),('0'*64,True,1621),('0'*64,1655,0)])
def test_invalid_metadata_is_rejected(hash_value,current,old):
    with pytest.raises(ValueError): audit('x\n47.3. COMPLEMENTARY SLACKNESS CONDITIONS 1655',hash_value,current,old)


def test_committed_diagnostic_remains_nonqualifying_and_baseline_bound():
    import gzip
    import json
    root = PATH.parents[1]
    report = json.loads((root/'evidence/lp47_9_pagination_diagnostic_v1.json').read_text())
    baseline_bytes = (root/'data/mapeogeo_v0_11_graph.json.gz').read_bytes()
    baseline = json.loads(gzip.decompress(baseline_bytes))
    node = next(n for n in baseline['nodes'] if n['id']=='srcdecl:theorem:47_9')['attributes']
    assert report['baseline_graph_sha256'] == hashlib.sha256(baseline_bytes).hexdigest()
    assert report['accepted_statement_sha256'] == node['independent_profile']['statement_sha256']
    assert report['reconstructed_historical_sha256'] == report['accepted_statement_sha256']
    assert report['accepted_page_end'] == node['pdf_page_end']
    assert report['statement_chars'] == node['independent_profile']['statement_chars']
    assert report['accepted_source_pdf'] == json.loads((root/'evidence/v0_7_acceptance_manifest.json').read_text())['source_pdf']
    assert report['qualifies_source_edition'] is False
    assert report['status'] == 'DIAGNOSTIC_ONLY'
