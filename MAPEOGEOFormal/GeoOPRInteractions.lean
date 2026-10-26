import Mathlib
namespace MAPEOGEOFormal.GeoOPR

theorem discovered_square_interaction (a b : Nat) :
    (a+b)^2 = a^2 + b^2 + 2*a*b := by ring

theorem discovered_cube_interaction (a b : Nat) :
    (a+b)^3 = a^3 + b^3 + 3*a^2*b + 3*a*b^2 := by ring

end MAPEOGEOFormal.GeoOPR
#print axioms MAPEOGEOFormal.GeoOPR.discovered_square_interaction
#print axioms MAPEOGEOFormal.GeoOPR.discovered_cube_interaction
