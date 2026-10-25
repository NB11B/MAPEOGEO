import Mathlib
import MAPEOGEOFormal.GeoPrimeBoundedOrbit

namespace MAPEOGEOFormal.GeoPrimeOrbit

/-- The residue 1 is unreachable from 0 by increments of 3 modulo 9. -/
theorem nine_step_three_not_full :
    ¬ BoundedCoverage 9 (3 : ZMod 9) := by
  intro h
  obtain ⟨t, ht⟩ := h (1 : ZMod 9)
  have hv : ((t.val : ZMod 9) * (3 : ZMod 9)) = 1 := by
    simpa [iterateStep_eq] using ht
  have htlt : t.val < 9 := t.isLt
  interval_cases t.val <;> norm_num at hv <;> contradiction

end MAPEOGEOFormal.GeoPrimeOrbit
#print axioms MAPEOGEOFormal.GeoPrimeOrbit.nine_step_three_not_full
