from mapeogeo.erdos19_frontier13_v5 import LINES_33
from mapeogeo.erdos19_quantified_cocert_v6 import certify_instance,run_campaign,digest_instance


def test_frontier_seed_emits_verified_cocertificate():
    c=certify_instance(13,LINES_33)
    assert c.verified
    assert len(c.instance_digest)==64
    assert len(c.colors)==33


def test_certificate_digest_is_order_invariant():
    assert digest_instance(13,LINES_33)==digest_instance(13,tuple(reversed(LINES_33)))


def test_bounded_campaign_does_not_claim_universal_proof():
    r=run_campaign(13,[LINES_33])
    assert r.state=="BOUNDED_VERIFIED"
    assert r.generated==r.verified==1
    assert r.counterexample is None
    assert r.state!="PROVED"
