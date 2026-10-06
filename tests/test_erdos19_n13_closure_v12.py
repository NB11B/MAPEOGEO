from mapeogeo.erdos19_n13_closure_v12 import evaluate_n13_closure
from mapeogeo.erdos19_bucket_uow_v12 import initial_buckets,update_bucket
from mapeogeo.erdos19_authority_v12 import AuthorityDependency,REQUIRED_IDS

def test_closure_requires_buckets_and_authority():
    s=initial_buckets()
    assert evaluate_n13_closure(s,[]).reason=="BUCKETS_OPEN"
    for m in range(33,55):
        s=update_bucket(s,m,status="CLOSED",generation_manifest="g",exhaustion_certificate="e",coloring_manifest="c")
    assert evaluate_n13_closure(s,[]).reason=="AUTHORITY_OPEN"
    deps=[AuthorityDependency(i,i,True,"d"*64) for i in REQUIRED_IDS]
    assert evaluate_n13_closure(s,deps).closed
