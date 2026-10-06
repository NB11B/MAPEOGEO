from mapeogeo.pa_condition_monitor import evaluate, fit_region


def test_monitor_flags_departure_and_localizes_coordinate():
    rows=[
        [1.0,0.0,0.00,0.00],
        [1.1,0.1,0.05,0.02],
        [0.9,-0.1,-0.05,-0.02],
        [1.05,0.05,0.02,0.01],
        [0.95,-0.05,-0.02,-0.01],
    ]
    region=fit_region(rows,quantile=0.8)
    d=evaluate(region,{"gain":1.0,"phase":0.0,"delta_gain":0.0,"delta_phase":3.0})
    assert d.state=="DEPARTURE"
    assert d.dominant_coordinate=="delta_phase"


def test_missing_coordinate_is_underdetermined_not_fault():
    region=fit_region([[1,0,0,0],[1.1,.1,.1,.1],[.9,-.1,-.1,-.1]],quantile=.9)
    d=evaluate(region,{"gain":1.0,"phase":0.0,"delta_gain":0.0})
    assert d.state=="UNDERDETERMINED"
    assert d.missing==("delta_phase",)
    assert d.score is None
