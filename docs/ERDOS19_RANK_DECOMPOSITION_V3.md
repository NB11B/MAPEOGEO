# Erdős #19 Rank Decomposition v3

After falsifying the generic conflict-graph degeneracy route, v3 preserves the
dual linear-hypergraph representation and partitions shared vertices by
incidence rank |I(v)|.

A rank-r hyperedge consumes all C(r,2) clique pairs internally: by linearity,
no other shared vertex can contain any of those pairs.  Thus high-rank shared
vertices are not merely extra coloring constraints; they also remove potential
rank-2 edges from the pair component.

This branch adds bounded structural generators and measurements for:
- rank partition;
- high-rank/pair conflicts;
- clique incidence load;
- deterministic maximal linear families through rank 3.

These are falsification/search tools, not a proof of the EFL coloring bound.
