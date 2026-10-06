from mapeogeo.erdos19_frontier13_v5 import LINES_33
from mapeogeo.erdos19_reduced_class_v11 import Reduced13Witness,verify_reduced13


def test_public_m33_seed_accepts_with_explicit_degree13_core():
    # Core indices from the public audit for m=33 are not embedded here;
    # derive a valid core by bounded subset pruning from all lines.
    core=list(range(len(LINES_33)))
    changed=True
    while changed:
        changed=False
        for i in list(core):
            d=sum(1 for j in core if j!=i and LINES_33[i]&LINES_33[j])
            if d<13 and len(LINES_33[i])==2:
                core.remove(i);changed=True
    r=verify_reduced13(LINES_33,Reduced13Witness(tuple(core)))
    assert r.member, r.reason


def test_missing_large_line_is_rejected():
    core=tuple(i for i,e in enumerate(LINES_33) if len(e)==2)
    r=verify_reduced13(LINES_33,Reduced13Witness(core))
    assert not r.member and r.reason=="CORE_OMITS_LARGE_LINE"


def test_wrong_bucket_is_rejected_before_core_claim():
    r=verify_reduced13(LINES_33[:32],Reduced13Witness(tuple(range(32))))
    assert not r.member
