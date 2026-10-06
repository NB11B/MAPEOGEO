# Contract Primitive Loader v0.6

v0.6 tests automatic construction of executable router primitives from existing
MAPEOGEO endpoint contracts.

A verified endpoint contract supplies **authority**, not code.  An executable
primitive requires both:

1. a PASS, digest-bound endpoint contract for the exact semantic ID; and
2. an explicitly registered implementation for that semantic ID.

Contract without implementation -> candidate/non-executable edge.
Implementation without contract -> candidate/non-executable edge.
Only the conjunction becomes a certified executable edge.

This prevents automatic graph loading from confusing semantic equivalence with
an implementation capable of performing the transformation.
