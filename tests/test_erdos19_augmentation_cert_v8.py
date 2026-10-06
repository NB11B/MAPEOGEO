from mapeogeo.erdos19_augmentation_cert_v8 import certify_augmentation,replay_augmentation


def test_augmentation_certificate_replays():
    parent=({0,1},{0,2})
    c=certify_augmentation(3,parent,{1,2})
    assert len(c.parent_digest)==len(c.child_digest)==len(c.certificate_digest)==64
    assert replay_augmentation(3,parent,c)


def test_relabelled_parent_child_has_same_structural_digests():
    a=certify_augmentation(3,({0,1},{0,2}),{1,2})
    b=certify_augmentation(3,({1,2},{1,0}),{2,0})
    assert a.parent_digest==b.parent_digest
    assert a.child_digest==b.child_digest
