# Erdős #19 Degeneracy-Bridge Falsification v2

Candidate bridge under test:

    every EFL shared-vertex conflict graph H has degeneracy(H) < n.

The dual incidence representation makes a direct counterexample family obvious:
take one shared vertex for every pair of the n clique indices.  Incidence sets
are all 2-subsets of [n].  Distinct incidence sets intersect in at most one
index, so this is a valid linear family.

Its conflict graph is the line graph L(K_n), which is 2(n-2)-regular.  Thus its
degeneracy is 2(n-2), and the proposed strict bound d(H)<n fails for n>=4.

This falsifies only the degeneracy proof route.  It does not falsify the EFL
coloring statement; L(K_n) remains n-colorable in the relevant range because
the needed coloring corresponds to an edge-coloring of K_n.
