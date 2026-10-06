# Erdős #19 Quantified Co-Certificate Operator v6

This is the first bounded proof operator for a FORALL-instance / EXISTS-witness
shape.

For every generated valid n-point linear-space instance H:
1. canonicalize and SHA-256 bind the instance;
2. run an exact n-edge-coloring constructor;
3. independently verify the coloring;
4. emit a co-certificate binding the instance digest to the coloring.

If coloring fails, the campaign returns COUNTEREXAMPLE with the exact instance.
If all generated instances verify, the state is BOUNDED_VERIFIED, never PROVED.

Universal promotion requires a separately certified exhaustion/generation proof
showing that every member of the target reduced class was generated (or a
general theorem replacing enumeration).
