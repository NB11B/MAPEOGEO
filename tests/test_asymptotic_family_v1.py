import math
from mapeogeo.asymptotic_family import (
    EventualBoundCertificate,erdos60_reference,erdos89_reference,eventual_lower_bound,normalize_growth,
)


def test_normalized_growth_coordinates_are_log_ratios():
    s=normalize_growth([(100,50.0)],lambda n:25.0)
    assert math.isclose(s[0].log_ratio,math.log(2.0),rel_tol=1e-12)


def test_finite_erdos89_data_never_certifies_conjecture():
    obs=[(100,20.0),(1000,80.0),(10000,300.0)]
    d=eventual_lower_bound(obs,erdos89_reference)
    assert d.state=="FINITE_EVIDENCE"
    assert d.certificate is None


def test_finite_erdos60_data_never_certifies_eventual_sqrt_bound():
    d=eventual_lower_bound([(100,12.0),(400,30.0)],erdos60_reference)
    assert d.state=="FINITE_EVIDENCE"


def test_explicit_eventual_certificate_is_required_for_certified_state():
    cert=EventualBoundCertificate("lower",0.01,1000,"lean:example.theorem")
    d=eventual_lower_bound([(100,12.0)],erdos60_reference,certificate=cert)
    assert d.state=="CERTIFIED"
    assert d.certificate.theorem_id=="lean:example.theorem"


def test_no_data_is_underdetermined():
    assert eventual_lower_bound([],erdos89_reference).state=="UNDERDETERMINED"
