# GEO-PRIME spectral partial 001

Partial source-destination observations of ONE known operator are treated as constraints on a finite permutation. All consistent permutations (bounded n<=8) are enumerated. The cycle length multiset identifies the exact characteristic polynomial as product of (x^L-1) over cycles L, and determines operator order (lcm of lengths), all without floating-point eigendecomposition. The method returns 'identified' if all completions share the same cycle-type (even if the full permutation is not unique); otherwise 'ambiguous'. 'identified' means spectral cycle type only, not full graph or family identifiability.

10 local tests passed; exact tests cover prime/composite full operators, underdetermined inputs, reconstructability with one missing edge, invalid and conflicting data, n cap. No composite/prime family claim can be made from a single operator's spectrum. This result is bounded exact enumeration (factorial complexity), not scalable inference. The deeper family and primality criteria require all nonidentity group elements and validated group closure.

Reproduce: cd experiments/geo_prime_spectral_partial_001 && python -m unittest discover -v
