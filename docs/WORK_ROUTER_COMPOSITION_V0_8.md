# Runtime Primitive Composition v0.8

v0.8 tests whether independently registered mathematical capabilities compose
into useful work that was never registered end-to-end.

Qualified routes:

1. graph adjacency -> contract-bound graph Laplacian -> algebraic connectivity;
2. point cloud + sigma -> contract-bound Gaussian Gram -> spectral radius.

The end-to-end work routes are not registered as monolithic implementations.
The router discovers them by composing primitive edges.  Direct conventional
calculations are used as result controls.

The first-step edge semantics correspond to the frozen v0.3 contract-bound
implementations.  v0.8 remains deliberately 2x2/2-node for the spectral helper
so the qualification does not smuggle in an external numerical dependency.
