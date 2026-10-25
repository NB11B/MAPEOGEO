# GEO-PRIME-GEOM-001 — Consecutive-leg triangle candidate generator

Test the hypothesis that the Pythagorean hypotenuse of legs n,n+1 is automatically prime when the triangle is primitive.

**Result:** falsified. Every such triangle has coprime legs, but (119,120,169) is a primitive integer right triangle whose hypotenuse is 13². (696,697,985) yields a composite nonsquare hypotenuse.

For integer c: n²+(n+1)²=c² iff (2n+1)²-2c²=-1, the negative Pell equation. This creates a sparse candidate subsequence; it is not a prime-only generator. Prime qualification still requires an independent multiplicative irreducibility check as established by GeoEulerPrime / GeoPrimeInteraction.

Local baseline: Python standard library, 8/8 tests passed, n=1..199999, 7 integer hypotenuses, 4 prime and 3 composite.

Run: `cd experiments/geo_prime_geom_001 && python -m unittest discover -v && python experiment.py`.

Future: prove Pell correspondence and primitive/composite counterexample in Lean; use native relational operator representation, generator scheduling and independent prime certificates. Do not claim that square-root or perfect-square screening suffices to establish primality.
