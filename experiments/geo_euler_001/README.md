# GEO-EULER-001: Prime generator ablation

Study the completed multiplicative relation system generated from 1 by the prime set, then ablate a generator. Reconstruct all integers at or below N by forming prime-power combinations, independently evaluate reciprocal-square partial sums, and compare the finite Euler product for the selected primes.

**Result (local, 2026-10-25):** 10/10 tests passed; 168 primes <=1000 generated all 1000 positive integers <=1000. The direct partial sum is 1.64393456668156, the product over primes <=1000 is 1.64472519023867, and the infinite Basel reference is 1.64493406684823. Removing p=2,3,5,7,11 produced the exact predicted product ratio 1-p^-2 to numerical tolerance. These are separate truncations; their different values are expected.

Execute: `cd experiments/geo_euler_001 && python -m unittest discover -v && python experiment.py`.

**Qualification boundaries:** this implementation enumerates known primes with the sieve; it is not autonomous discovery of unique factorization or of Euler's product. Operator order invariance applies to the completed commutative multiplication closure, not necessarily intermediate execution traces. Unique factorization and Euler-product convergence are established mathematics. Full MAPEOGEO-native operator discovery and proof-certificate integration remain open.

**Next gates:** generate multiplication through repeated addition from successor; discover rather than supply prime generators; prove closure/uniqueness independent of candidate labels; compare quotient representations and state/relationship saturation; add adversarial nonprime generators, partial closures, and blinded independent holdouts.
