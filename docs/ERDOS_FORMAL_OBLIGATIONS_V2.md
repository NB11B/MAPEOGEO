# Erdős Formal Obligation Campaign v2

The v2 campaign inspects actual Lean statements from
google-deepmind/formal-conjectures rather than inferring mathematical work from
tags.  Six unresolved/formalized problems are decomposed into their currently
available lemmas and the missing bridge needed to close the research theorem.

The decomposition is diagnostic only.  It does not replace Lean elaboration and
does not mark any open theorem proved.

Initial cases: 19, 23, 60, 89, 97, 128.

The strongest immediate finding is that several deficits are not missing finite
computation.  Problems 60 and 89 expose an asymptotic/uniform bridge; Problem 19
reduces to a specific shared-vertex coloring existence problem; Problem 128
requires an extremal graph argument from induced-density assumptions.
