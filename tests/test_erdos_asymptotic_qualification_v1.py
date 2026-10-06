from mapeogeo.erdos_asymptotic_qualification import qualify_erdos60,qualify_erdos89


def test_erdos89_finite_campaign_stops_before_proof():
    r=qualify_erdos89([(100,20),(1000,80)])
    assert r.state=="FINITE_EVIDENCE"
    assert "Lean eventual" in r.missing_bridge


def test_erdos60_finite_campaign_stops_before_proof():
    r=qualify_erdos60([(100,5),(400,15)])
    assert r.state=="FINITE_EVIDENCE"
    assert "uniform eventual" in r.missing_bridge
