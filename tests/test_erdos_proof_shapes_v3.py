from mapeogeo.proof_shape import classify_signature


def test_erdos89_shape():
    s="theorem erdos_89 : (fun n => n/(n:ℝ).log.sqrt) =O[atTop] (fun n => D n) := by"
    d=classify_signature(s)
    assert d.shape=="ASYMPTOTIC"
    assert "ASYMPTOTIC" in d.features


def test_erdos60_shape():
    s="theorem erdos_60 : ∃ c : ℝ, c > 0 ∧ ∀ᶠ n : ℕ in atTop, ∀ G, P G → Q G := by"
    d=classify_signature(s)
    assert d.shape=="EVENTUAL"
    assert "EXISTS" in d.features and "FORALL" in d.features


def test_erdos19_shape():
    s="theorem erdos_19 : answer(sorry) ↔ ∀ V n C, chromatic C = n := by"
    d=classify_signature(s)
    assert d.shape=="UNIVERSAL"
    assert "ANSWER_EQUIV" in d.features


def test_erdos23_shape():
    s="theorem erdos_23 : answer(sorry) ↔ ∀ n V G, triangleFree G → ∃ H, H ≤ G := by"
    d=classify_signature(s)
    assert d.shape=="MIXED_QUANTIFIER"
    assert "QORDER_AE" in d.features


def test_unknown_atomic_stays_atomic():
    assert classify_signature("theorem t (n : ℕ) : Prime n := by").shape=="ATOMIC_OR_PARAMETERIZED"
