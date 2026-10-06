# Derived Mathematical Routes v0.5

v0.5 removes complete handwritten source-to-invariant routes for a bounded set
of queries.  The overlay registers only primitive certified transformations;
the existing fail-closed Dijkstra router composes them at runtime.

Qualification targets:

- vector norm from dot-self -> square root -> target alias;
- general linear stability from matrix -> eigenvalues -> real parts -> maximum;
- PSMSL planar stability from generator real part -> spectral abscissa;
- area expansion from directional scale coordinates -> log-area scale -> sign;
- dominant vibration frequency from window -> spectrum -> argmax.

Deliberately cheaper uncertified shortcuts are present for matrix->stability and
RMS->THD.  They may be discovered but must never execute.

This is route derivation over a bounded certified primitive overlay.  It is not
yet arbitrary traversal of the full raw MAPEOGEO graph.
