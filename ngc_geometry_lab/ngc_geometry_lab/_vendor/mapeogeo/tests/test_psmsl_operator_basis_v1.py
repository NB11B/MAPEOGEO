from mapeogeo.psmsl_operator_basis_v1 import discover_linear_operator_basis

def test_operator_basis_removes_linear_redundancy():
    I=((1,0),(0,1));R=((0,-1),(1,0));twoI=((2,0),(0,2))
    b=discover_linear_operator_basis((I,R,twoI))
    assert b.rank==2
    assert b.basis_indices==(0,1)
    assert b.redundant_indices==(2,)

def test_independent_matrix_operators_remain():
    A=((1,0),(0,0));B=((0,0),(0,1));C=((0,1),(0,0))
    b=discover_linear_operator_basis((A,B,C))
    assert b.rank==3 and b.redundant_indices==()
