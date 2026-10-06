# Invariant Query Layer v0.4

The invariant layer separates **what property the work asks about** from the
representation that currently carries enough information to answer it.

Initial intents:

- magnitude;
- threshold;
- alignment;
- stability;
- area change;
- rate;
- spectral content.

The same invariant may route differently by domain.  For example, stability
from a PSMSL planar generator uses `g < 0`, while stability from a general
state matrix routes through eigenvalues and spectral abscissa.  Both terminate
at the same semantic work target without requiring a common intermediate
representation.

Unsupported domain/invariant pairs fail closed as `UNRESOLVABLE`.

This layer is a bounded executable vocabulary, not natural-language semantic
understanding and not a claim that these invariants exhaust MAPEOGEO.
