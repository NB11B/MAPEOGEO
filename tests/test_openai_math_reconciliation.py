from experiments.openai_math_reconciliation_v1 import toks, build_index
def test_reconciliation_index_has_expected_token():
    objs=[{"id":"canonical:linear_algebra:vector_space","name":"Vector Space","description":"scalar multiplication over a field"}]
    sig,inv,by=build_index(objs)
    assert "vector" in inv
    assert "canonical:linear_algebra:vector_space" in inv["vector"]
    assert by["canonical:linear_algebra:vector_space"]["name"]=="Vector Space"
    assert "vector" in sig["canonical:linear_algebra:vector_space"]
def test_reconciliation_tokenizer_normalizes():
    assert {"rank","nullity"} <= toks("Rank-Nullity theorem")
