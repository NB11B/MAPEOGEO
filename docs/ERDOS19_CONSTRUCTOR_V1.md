# Erdős #19 Shared-Coloring Constructor v1

The Formal Conjectures file for Problem #19 already proves that an EFL
configuration is n-colorable if its shared vertices admit an n-coloring that is
injective inside each clique.  This module attacks exactly that missing proof
object on finite instances.

Representation:
- one variable per shared vertex;
- color domain {0,...,n-1};
- one all-different constraint for the shared vertices in each clique.

A deterministic backtracking constructor searches the finite CSP and every
returned coloring is independently checked against the obligation.

This is bounded constructor synthesis, not a proof that a coloring exists for
every EFL configuration.  Universal promotion requires a certified constructor
or theorem covering arbitrary n/configurations.
