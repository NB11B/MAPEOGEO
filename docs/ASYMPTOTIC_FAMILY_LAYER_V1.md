# Asymptotic / Family Operator Layer v1

This layer represents work over families of mathematical objects and separates
finite normalized evidence from certified eventual statements.

For positive quantity P(n) and positive reference f(n), the PSMSL-style growth
coordinate is

    z(n) = log(P(n) / f(n)).

Finite z(n) samples are useful for search, counterexample hunting, and route
economics, but never certify Big-O/Omega/eventual claims.  A CERTIFIED state
requires an explicit EventualBoundCertificate carrying a theorem/proof ID,
constant, and threshold.

Qualification targets:
- Erdős #89 with reference n/sqrt(log n);
- Erdős #60 with reference sqrt(n).

The design follows mathlib's asymptotic semantics: Big-O is an eventual
constant-multiple relation along a filter, not a finite trend fit.
