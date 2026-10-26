# GEO-PRIME-EXP-001: consecutive-operand exponentiation

Hypothesis: F(n)=n^(n+1)+(n+1)^n always generates primes. **Falsified:** F(3)=145=5·29; F(4)=1649=17·97.

**Exact modular theorem (mathematical argument):** For every prime q>=5, F(q−2) is divisible by q. Put n=q−2; modulo q, n=-2, n+1=-1. Because q is odd, F(n)=2^(q−1)−1 (mod q), which vanishes by Fermat's little theorem. Since F(q−2)>q, the result is composite.

**Second obstruction:** n=6k+1 for k>=1 gives F(n)=0 (mod 3). n=1 is an exception: F(1)=3 is prime.

**Sandbox qualification:** 8/8 tests passed with SymPy independent primality checking on n<=50; only indices 1 and 2 are prime in that finite interval. The previous pure trial-division test timed out for large powers; this was a harness issue and was corrected. Modular factor certificates are exact, with no dependence on probabilistic primality classifications for their arithmetic validation.

**Boundary:** These congruence families do not prove that every n>=3 produces a composite. The result is an infinite family of composite terms, not a universal classification. Future Lean proof of the Fermat obstruction and discovery of other residue-class factors must be independently verified. Do not equate prime status with geometric primitiveness.

Run: `cd experiments/geo_prime_exp_001 && python -m pip install sympy && python -m unittest discover -v && python experiment.py`.
