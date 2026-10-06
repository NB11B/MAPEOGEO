# Erdős #19 Generator Validation v9

v9 validates canonical generation against an independent brute-force exact-cover
enumerator on small point sets.

Canonical generator:
- augment partial linear spaces by admissible lines;
- exact-canonicalize every partial child;
- retain one child per partial isomorphism class;
- stop at complete pair covers.

Independent control:
- recursively exact-cover all point pairs by candidate lines;
- do no partial isomorphism rejection;
- quotient only completed labeled covers.

Qualification requires exact equality of final canonical digest sets.  Missing
or extra isomorphism classes fail the test.  Passing this bounded comparison
validates the generator semantics, not scalability to n=13.
