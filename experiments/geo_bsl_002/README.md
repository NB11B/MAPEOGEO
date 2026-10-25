# GEO-BSL-002: Representation invariance vs base-dependent dynamics

## Scope
Tests the hypothesis that Basel/cycle spectral invariants are artifacts of a chosen positional number base. Distinguishes (A) changing notation while preserving integers/graphs from (B) changing the operation by selecting a base parameter.

## Execute
```bash
python -m unittest discover -s experiments/geo_bsl_002 -v
python -c "from experiments.geo_bsl_002.test_base import summary; import json; print(json.dumps(summary(),indent=2))"
```

## Local results (2026-10-25)
- 6/6 unit tests passed.
- 6078/6078 integer positional encodings round-tripped correctly across bases 2,3,7,10,16,36.
- 5/5 cycle and 5/5 path graph spectral identities checked (sizes 5,8,16,31,64).
- 5/5 random vertex relabelings preserved spectra to <3e-12.
- At integer 19, sum of digit squares is 3 in base 2, 29 in base 7, and 82 in base 10.
- Digit-square dynamics from integer 19: base 7 eventually cycles 29->17->13->37->29, while bases 2 and 10 reach fixed point 1.
- The signed-digit IFS f_d(x)=(x+d)/b, d in {-1,0,1}, explicitly changes contraction ratio with b. Similarity dimension log(3)/log(b) requires separation assumptions to identify with attractor dimension; it was NOT numerically qualified here.

## Qualification boundaries
No arithmetic operation was reconstructed by the native MAPEOGEO machinery. The base-sensitive dynamical examples are mathematical *control cases*, not proof of a privileged base or general statement about number-system uniqueness. Numerical calculations use float64; this is not a formal proof of base invariance. A digit-square map is different for different b by its very definition. Basel value itself is invariant under changes of numeral notation because it is defined on integers rather than digit strings.

## Next gates
- G6: semantic-preserving base conversions in native MAPEOGEO codecs.
- G7: independently learned base-conditional transition graph reconstruction with masked bases and held-out integers.
- G8: separate the base of notation from base used in the dynamical rule.
- G9: signed-digit IFS geometry with overlap/separation certificates.
- G10: blind out-of-distribution qualification and adversarial controls.
