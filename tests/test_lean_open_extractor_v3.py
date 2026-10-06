from mapeogeo.lean_open_extractor import research_open_signatures


def test_extracts_multiple_research_open_theorems():
    src="""
@[category research open, AMS 5]
theorem a : ∀ n, ∃ m, n < m := by
  sorry
@[category test, AMS 5]
theorem ignored : True := by trivial
@[category research open, AMS 52]
theorem b : (fun n => n) =O[atTop] (fun n => n^2) := by
  sorry
"""
    xs=research_open_signatures(src)
    assert [x[0] for x in xs]==["a","b"]
    assert xs[0][2].shape=="MIXED_QUANTIFIER"
    assert xs[1][2].shape=="ASYMPTOTIC"
