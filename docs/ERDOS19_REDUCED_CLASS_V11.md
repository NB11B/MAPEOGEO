# Exact Reduced n=13 Class Predicate v11

The target finite frontier is represented by witnessed membership, not an
inferred property.

An object is accepted only when:
1. it has 13 points;
2. it is a linear space (every point pair occurs exactly once);
3. its line count m lies in 33..54;
4. an explicit selected core is supplied;
5. that core contains every line of size >=3;
6. every core line has at least 13 neighbors inside the core's line-intersection
   graph.

The core is part of the certificate.  Failure to supply one is not interpreted
as nonexistence; it is an absent membership witness.

This predicate implements the stronger degree-13 reduced search class described
in the 2026 audit of Erdős #19.  The published SAT 2023 reduction uses an
(n-1)-reduced condition; the stronger degree-n core is a separately justified
counterexample-search reduction in that audit.
