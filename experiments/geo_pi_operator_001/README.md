# GEO-PI-OPR-001: pi approximations and operator grammar control

The user's expression 2*(5+(2*3))/7 is exactly 22/7; omitting the outer 2 gives 11/7. The alternative ((1+1)+3+(2*3))/7 is also 11/7. 22/7 approximates π with absolute error ≈0.001264489 and relative error ≈0.0402499%. With q<=7, 22/7 is the closest p/q in the tested positive rational candidates. With q<=113, 355/113 is closer (~2.66764e-7 absolute error). This is a numerical relation, not evidence of a causal/geometric generating mechanism.

Reproduce: `cd experiments/geo_pi_operator_001 && python -m unittest discover -v && python experiment.py`.

Next prospective gate: enumerate typed operator ASTs using a fixed token budget, avoid selectively searching only expressions containing desired constants, compare out-of-sample approximations and unrelated irrational controls, and certify exact equality of alternative expressions in Lean. The relationship of Basel ζ(2)=π²/6 to cyclic operator geometry requires a separate theorem; numerical closeness of 22/7 proves no such link.
