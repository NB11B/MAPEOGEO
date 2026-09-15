# Third-Party Notices and Source Licensing

MAPEOGEO uses external mathematical sources as research references and provenance anchors. Unless explicitly stated otherwise, MAPEOGEO does not redistribute those source works and does not claim any rights in them.

## Gallier and Quaintance reference corpus

**Work:** *Algebra, Topology, Differential Calculus, and Optimization Theory for Computer Science and Machine Learning*  
**Authors:** Jean Gallier and Jocelyn Quaintance  
**Source:** https://www.cis.upenn.edu/~jean/math-deep.pdf  
**Version used for the initial research:** April 14, 2025  
**Copyright notice shown in the source:** © Jean Gallier

No separate permissive license for the book was identified in the source used for this research. The book PDF is therefore **not included** in this repository.

The v0.4 source-ingestion workflow may download the PDF transiently from the original source in order to derive structural research metadata. The workflow removes the transient PDF after processing and does not publish the PDF, page images, theorem prose, proof prose, excerpts, or other source-text payloads as repository files or workflow artifacts.

Persistent MAPEOGEO source-ingestion artifacts are limited to bibliographic/provenance metadata, chapter identifiers, declaration types and numbers, PDF-page locators, hashes and character counts, proof-presence flags, explicit numbered cross-references, generated graph structure, and audit results.

Users who want the book should obtain it from the original source and comply with the copyright holder's terms.

## NB11B EO/GEO repositories

MAPEOGEO refers to results and concepts developed in related NB11B repositories, including `GeometricElementaryOperators` and `GEOSDP`. The current MAPEOGEO source-ingestion stage does not vendor source files from those repositories. Any future vendoring or direct code reuse must preserve the applicable license and provenance of the originating repository at the time of reuse.

## Mathematical facts

Mathematical facts, formulas, identities, theorem numbers, and theorem relationships are used as mathematical content. The particular expression, exposition, diagrams, and prose of third-party sources remain protected to the extent provided by applicable law.

## Research artifacts

The JSON graphs, test harnesses, reports, importer code, and independently generated numerical evidence in this repository are original MAPEOGEO research artifacts unless a file states otherwise. Their use is governed by `LICENSE.md`.
