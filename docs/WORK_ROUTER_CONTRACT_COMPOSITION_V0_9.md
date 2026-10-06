# Composable Execution Contracts v0.9

v0.9 adds work-tolerance-aware route qualification.  Every executable primitive
must have both mathematical certification and an execution contract containing:

- an input/domain validity predicate;
- a conservative absolute-error contribution.

For the bounded v0.9 model, route error composes conservatively by addition.
The router searches only certified, domain-valid paths whose composed error does
not exceed the requested work tolerance, then minimizes cost within that
admissible set.

Qualification includes competing routes: a cheap two-edge approximation with
0.06 composed error and an expensive direct route with 0.005 error.  Loose work
tolerance selects the cheap route; tight tolerance selects the accurate route.
Uncertified and domain-invalid routes remain inadmissible regardless of cost or
nominal error.

Additive absolute error is intentionally conservative and not universal.
Future contracts may supply transformation-specific propagation functions.
