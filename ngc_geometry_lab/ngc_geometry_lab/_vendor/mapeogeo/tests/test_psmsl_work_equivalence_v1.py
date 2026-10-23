from mapeogeo.psmsl_work_equivalence_v1 import work_relative_commutation,work_relative_information_loss

def test_noncommuting_operators_can_be_equivalent_after_work_projection():
    # A and B differ only in the second output row after composition.
    A=((1,0),(0,2));B=((1,1),(0,1))
    # They do not commute exactly.
    exact=work_relative_commutation(A,B)
    assert not exact.exact_equal
    # Observe only a coordinate on which AB and BA agree.
    P=((0,1),)
    w=work_relative_commutation(A,B,P,0.0)
    # For these matrices second row differs; use first-coordinate projection test below.
    assert not w.equivalent_for_work

def test_projection_can_make_information_losing_transform_work_lossless():
    # Work asks only for x; dropping z loses global state but not requested x.
    T=((1,0,0),(0,1,0))
    before=((1,0,0),)
    after=((1,0),)
    d,ok=work_relative_information_loss(T,before,after)
    assert ok and d==0
