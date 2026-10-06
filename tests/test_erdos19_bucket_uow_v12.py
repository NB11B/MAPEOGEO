from mapeogeo.erdos19_bucket_uow_v12 import initial_buckets,update_bucket,bucket_manifest,all_closed

def test_exact_22_bucket_schedule():
    s=initial_buckets()
    assert [x.m for x in s]==list(range(33,55))
    assert not all_closed(s)
    assert len(bucket_manifest(s))==64

def test_bucket_cannot_globally_close_without_all_three_artifacts():
    s=initial_buckets()
    s=update_bucket(s,33,status="CLOSED",generation_manifest="g",exhaustion_certificate="e",coloring_manifest="c")
    assert not all_closed(s)
