# GEO-OPR-001 — Operand position and operator compositions

Exhaustive reference checks over the 9 ordered input pairs from {1,2,3}. Tested addition, multiplication, both exponent directions, applying squares/cubes before or after aggregation. Results: 108 evaluated paths, 23 unique outputs, 85 repeated-output paths, maximum 11 paths producing a single value. Ten local unit tests passed; the same algebraic identities were independently checked on 289 ordered pairs with operands 4..20.

**Claim boundary:** This is a reference calculation, not autonomous MAPEOGEO discovery of operators or relational quotient classes. A common numerical output is not necessarily equivalence of full computational work. Commutativity applies to addition and multiplication, not generally exponentiation. Squaring and cubing distribute over multiplication but have nonzero additive interaction residuals 2ab and 3ab(a+b).

Reproduction artifacts: test_operator.py and results.json. These evaluate fixed operator expressions without recursion; additional closure and native work-equivalence gates are future work.