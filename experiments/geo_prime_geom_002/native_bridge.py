"""Use actual MAPEOGEO vendored PSMSL matrix and operator-basis APIs."""
from pathlib import Path
import sys
VENDOR=Path(__file__).resolve().parents[2]/"ngc_geometry_lab"/"ngc_geometry_lab"/"_vendor"/"mapeogeo"
if str(VENDOR) not in sys.path:sys.path.insert(0,str(VENDOR))
from mapeogeo.psmsl_operator_algebra_v1 import matmul, information_semantics, ordering_semantics
from mapeogeo.psmsl_operator_basis_v1 import discover_linear_operator_basis
T=((3.,4.),(2.,3.))
INV=((3.,-4.),(-2.,3.))
I=((1.,0.),(0.,1.))
J=((1.,0.),(0.,-2.))
def transpose(A):return tuple(tuple(A[j][i] for j in range(len(A))) for i in range(len(A[0])))
def run():
    q=matmul(matmul(transpose(T),J),T)
    t2=matmul(T,T)
    basis=discover_linear_operator_basis((T,t2,I))
    info=information_semantics(T)
    ordering=ordering_semantics(T,t2)
    return {"native_import":True,"inverse_exact":matmul(T,INV)==I and matmul(INV,T)==I,
            "norm_preserved":q==J,"operator_invertible":info.invertible,
            "basis_rank":basis.rank,"basis_indices":basis.basis_indices,
            "redundant_indices":basis.redundant_indices,
            "commutes_with_square":ordering.commutes}
if __name__=="__main__":print(run())
