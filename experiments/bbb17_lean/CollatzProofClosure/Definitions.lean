import ThreeTracks

namespace BBB17
namespace CollatzProofClosure

/-! # COLLATZ-C10: Unified Proof-Closure Definitions (`Definitions.lean`)

    Imports the frozen C1–C9 baseline (`ThreeTracks.lean` at `48e6502`) without
    re-implementing existing definitions, and defines the exact propositions,
    deficit quantities, and workstream targets for the C10 proof-closure campaign.
-/

/-- Exact integer deficit `E(w, m) = (D(w) - A(w)) * m - B(w)` in natural-number form
    (well-defined whenever `wordDelta w * m ≥ wordB w`). -/
def exactDeficit (w : List Bool) (m : Nat) : Nat :=
  wordDelta w * m - wordB w

/-- Canonical output `y₀(w) = F_w(wordResidue w)` on the canonical residue representative. -/
def canonicalOutput (w : List Bool) : Nat :=
  applyParityWord (wordResidue w) w

/-- Minimal representative output `y_min(w) = F_w(minWordRep w)`. -/
def minRepOutput (w : List Bool) : Nat :=
  applyParityWord (minWordRep w) w

/-- Discrete deficit quotient `q(w, m) = m - F_w(m)` at an admissible input `m`. -/
def deficitQuotient (w : List Bool) (m : Nat) : Nat :=
  m - applyParityWord m w

/-- 2-adic lift bit `ℓ(w, b) ∈ {0, 1}` when extending word `w` by step `b`. -/
def liftBit (w : List Bool) (b : Bool) : Nat :=
  if decide (canonicalOutput w % 2 = 1) = b then 0 else 1

/-- Open Obligation A (`EveryNatCrossesSpectrally` from C9):
    Every integer `n > 1` eventually encounters a first spectral crossing `w ∈ 𝓜`. -/
abbrev ObligationA_SpectralCrossing : Prop :=
  EveryNatCrossesSpectrally

/-- Open Obligation B (`MinimalCrossingDeficitPositive` from C9):
    Every first-crossing parity cylinder `w ∈ 𝓜` has a positive quantized deficit
    `Δ(w) * m_min(w) ≥ B(w) + D(w)` at its least positive representative `m_min(w) > 1`. -/
abbrev ObligationB_FirstCrossingDeficit : Prop :=
  MinimalCrossingDeficitPositive

/-- Complement of Obligation A for an individual integer `n`:
    `n` never encounters a first spectral crossing at any positive depth `r > 0`. -/
def NeverCrossesSpectrally (n : Nat) : Prop :=
  ∀ r : Nat, r > 0 → ¬IsFirstCrossing (parityWordOf r n)

/-- Independent Global Descent Criterion (WS3):
    Every integer `n > 1` admits a two-segment parity composition `w₁ ++ w₂`
    whose composite operator contracts (`D(w₁ ++ w₂) > A(w₁ ++ w₂)`) and has a
    strictly positive quantized deficit at `n`. -/
def EventualCompositeDeficitPositive (n : Nat) : Prop :=
  ∃ w₁ w₂ : List Bool,
    (w₁ ++ w₂).length > 0 ∧
    validParityWord n (w₁ ++ w₂) ∧
    wordD (w₁ ++ w₂) > wordA (w₁ ++ w₂) ∧
    wordDelta (w₁ ++ w₂) * n ≥ wordB (w₁ ++ w₂) + wordD (w₁ ++ w₂)

def UniversalCompositeDeficitPositive : Prop :=
  ∀ n : Nat, n > 1 → EventualCompositeDeficitPositive n

/-- 1-circuit parity word `allTrueWord a ++ replicate k false`:
    `a` consecutive odd steps followed by `k` even steps. -/
def oneCircuitWord (a k : Nat) : List Bool :=
  allTrueWord a ++ List.replicate k false

end CollatzProofClosure
end BBB17
