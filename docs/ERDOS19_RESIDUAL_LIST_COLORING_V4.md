# Erdős #19 Residual List-Coloring Decomposition v4

This experiment colors rank>=3 incidence hyperedges first.  Their colors become
forbidden at every clique index they touch.  Each remaining rank-2 hyperedge
{u,v} therefore receives a list of colors available at both endpoints.  The
residual problem is an exact list-edge-coloring CSP on the rank-2 graph.

Two failure modes are kept distinct:
1. a particular high-rank coloring leaves an impossible residual list problem;
2. every proper high-rank coloring leaves an impossible residual problem.

v4 exhausts high-rank color assignments on the bounded generated families
(n<=6, rank<=3) and independently verifies every combined coloring.  Bounded
success is evidence for the decomposition strategy, not a universal proof.
