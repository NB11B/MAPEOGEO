# GEO-OPR-003 — Bounded compositional grammar search

Enumerate typed binary arithmetic ASTs composed of x, y, one, successor, add and multiply (depth 2). Select a rule from nine observations on ordered pairs from {1,2,3}, then evaluate 49 strictly held-out pairs with operands 4..10. Local corrected test run: 7/7 passed, selected `add(x,mul(x,y))`, 49/49 holdouts correct.

## Reproduction
`cd experiments/geo_opr_003 && python -m unittest discover -v && python grammar.py`

## Limits and falsification
Primitives + and * are supplied. Symbolic expressions are deduplicated by their behavior on the training grid, which can hide alternative formulas; this experiment is not unrestricted grammar discovery nor a proof that the selected operator is uniquely identifiable globally. Holdouts check generalization but are not Lean proofs. An original unit-test syntax error was fixed before the successful local execution; do not attribute that failure to the operator inference.

Next: generate a Lean definition from the selected typed AST itself and prove its equivalence to a source-level reference expression, then apply adversarial grammar mutations. In particular, avoid converting an untrusted selected expression into a preapproved hardcoded formula before proof-checking.
