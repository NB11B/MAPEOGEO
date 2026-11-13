# Separately requalified v0.9 source correction, version 1

## Historical binding is invalid

The historical `srcdecl:lemma:3_6` fingerprint does not identify Lemma 3.6's
statement. It identifies a line-wrapped citation inside Proposition 3.20's
proof on PDF pages 97–98. The old declaration recognizer accepts a number at
the start of any line, without requiring declaration punctuation; its duplicate
selector then picks the longest candidate. The citation incorrectly won.
Matching that historical hash is not evidence that the lemma was source-bound.
The original graph, configuration and acceptance manifests remain historical
records and are not silently rewritten or treated as valid corrected evidence.

## Narrow correction and extraction provenance

The corrected path uses `formal/proof_paths_v0_9_corrected_v1.json`, separately
identified as `CORRECTED_SOURCE_V1`. Its only changed statement pins are:

- Lemma 3.6: the genuine 248-character statement on page 77, lines 36–38,
  SHA256 `7b23d4bb370df45d743d82405c8339622c804dee0a3d0575ace2638bde9fd955`.
- Proposition 6.7: the PyMuPDF 1.28.2 representation, SHA256
  `ed9e437c8a539615e0759d0f6ccfea972afe87ad106a304c780d9e6ff59895d3`.
  Independent visual review confirms its negated-index relation. The old hash
  is reproduced by 1.26.6 and differs through extraction ordering, not PDF bytes.

The correction generator requires the unchanged original PDF SHA256 and byte
count and exactly PyMuPDF 1.28.2. It verifies fixed declaration/proof boundaries,
all reviewed hashes and the actual Theorem 3.7 proof citation to Lemma 3.6.
The corrected node deliberately uses `CORRECTED_STATEMENT_ONLY` semantic
profiling, rather than the legacy statement-plus-proof heuristic. Its exact
existing ontology/family edges must remain unchanged, or the repair fails.
The old profiling data is retained in the superseded node.
It corrects the lemma's page, statement, proof, and detector metadata, adding
its genuine source proof block. It retains the superseded node metadata and
reason in an explicit audit. It rejects unexpected inputs rather than applying
a generic corpus repair. Existing v0.6/v0.7 retrieval graphs and metrics remain
unchanged; the corrected graph is a new downstream input, not historical replay.

The hash-only audit binds the input graph, corrected bindings, PDF, extractor,
and exact boundaries. No source prose or PDF is persisted in repository or
workflow artifacts. The full raw PDF remains transient and is removed by the
existing unconditional cleanup.

## Mathematical and proof scope

The genuine lemma states that adjoining an outside-span vector preserves an
independent family. The existing Lean theorem proves the corresponding
set-level assertion over a division ring. Independent mathematical review
checked the correspondence: an independent family is injective; its range is
independent; the added vector is outside that range; a fresh family index
corresponds to set insertion. A field/vector space is a valid specialization.
This family-to-set correspondence is reviewed mathematics, not an additional
kernel-checked wrapper. The kernel checks the existing scoped set theorem.

Theorem 3.7's genuine proof on page 78 explicitly cites Lemma 3.6. Its statement
hash and the existing path edge are checked, not guessed from similar wording.
All other frozen path bindings, dependency gates, proof-escape checks, Lean
checks and qualification thresholds remain unchanged. Corrected-source
provenance is an additional gate and is required before support certificates
can be emitted. Historical mode cannot silently inherit a corrected graph.

## Claim boundary

This repairs one declaration identity and explicitly migrates one extraction
fingerprint. It does not certify the old mislabeled span, fix the declaration
recognizer across the corpus, establish full indexed-family formalization, or
resolve the independent full-Python collection blockers. Hosted qualification
must be reported against the exact corrected commit and remains subject to
all existing aggregate gates.
