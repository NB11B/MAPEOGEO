from mapeogeo.erdos19_global_closure_v13 import evaluate_global
def test_unknown_cutoff_is_irreducible_external_math_deficit():
    assert evaluate_global(True,None,False).reason=="EFFECTIVE_CUTOFF_UNKNOWN"
def test_known_cutoff_still_requires_intermediate_cases():
    assert evaluate_global(True,100,False).reason=="INTERMEDIATE_N_OPEN"
