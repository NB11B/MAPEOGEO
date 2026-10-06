# Erdős #19 Symmetry-Aware Exhaustion Certificate v7

v7 implements the authority side missing from the bounded FORALL/EXISTS
co-certificate campaign.

For a finite raw generated class:
1. canonicalize every instance under all vertex permutations;
2. quotient into isomorphism classes;
3. emit one canonical representative per class;
4. SHA-256 bind the representative manifest;
5. independently replay every raw instance and require its canonical form to
   occur in the manifest.

This proves coverage only relative to the supplied finite raw class.  It does
not prove that the raw generator itself enumerates the mathematical target
class.  Generator completeness remains a separate certificate obligation.

Permutation canonicalization is factorial and intentionally limited to small
qualification classes.  n=13 requires a stronger canonical-labeling backend.
