# Erdős #19 Canonical Augmentation v8

v8 replaces factorial permutation enumeration as the first canonicalization
stage with a colored bipartite incidence-graph refinement:

- point vertices form one color class;
- line vertices form another, initially refined by line size;
- iterative color refinement uses multisets of neighboring colors.

The resulting digest is an isomorphism invariant and a fast partition/refinement
key.  It is NOT treated as a complete canonical label when non-singleton color
cells remain.  Such instances return NEEDS_CANONICAL_BACKEND.

This fail-closed distinction allows canonical augmentation to use cheap
refinement for easy/asymmetric cases while routing symmetric cases to a future
nauty/Traces-style canonical-labeling implementation.
