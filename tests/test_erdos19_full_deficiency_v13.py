from pathlib import Path
from mapeogeo.erdos19_external_adapters_v13 import ExternalCanonicalAdapter,ExternalColoringAdapter
from mapeogeo.erdos19_authority_ingest_v13 import AuthoritySpec,ingest_authority
from mapeogeo.erdos19_campaign_v13 import checkpoint,resume
from mapeogeo.erdos19_bucket_uow_v12 import initial_buckets

def test_missing_external_tools_fail_closed():
    assert not ExternalCanonicalAdapter(("definitely_missing_tool_xyz",)).canonicalize(3,()).verified
    assert not ExternalColoringAdapter(("definitely_missing_solver_xyz",)).available()

def test_authority_ingestion_is_digest_bound(tmp_path):
    p=tmp_path/"a";p.write_bytes(b"proof")
    import hashlib
    d=hashlib.sha256(b"proof").hexdigest()
    assert ingest_authority(AuthoritySpec("X",d),p).verified
    assert not ingest_authority(AuthoritySpec("X","0"*64),p).verified

def test_campaign_checkpoint_replays(tmp_path):
    p=tmp_path/"campaign.json"
    c=checkpoint(initial_buckets(),p)
    assert resume(p).manifest==c.manifest
