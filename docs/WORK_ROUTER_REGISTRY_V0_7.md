# Frozen v0.3 Implementation Registry — v0.7

v0.7 registers bounded executable implementations for all eight frozen v0.3
endpoint semantic contracts.  The registry does not create authority: each
implementation becomes executable only through the v0.6 loader when the exact
semantic ID has a verified digest-bound endpoint contract.

The eight entries intentionally include different executable roles:
constructors, actions/conversions, and predicates/residual checks.  They are not
all treated as invertible state transformations.

Qualification checks both automatic binding of all eight contracts and direct
replay of representative fixture semantics.
