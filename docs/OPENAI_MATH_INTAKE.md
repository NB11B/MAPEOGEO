# Complete OpenAI mathematics source intake

MAPEOGEO's `openai-math` reconstruction stage adds the complete tracked
[OpenAI mathematics repository](https://github.com/openai/math) to the preserved
foundation graph. It records source identity, catalogue structure, formalization
configurations, lexical declarations, and explicit references. Every tracked
resource receives an extraction disposition.

The source is fixed at commit
`adc7f1241b42e322a6451854ab7e4b4c146bf78a`, with root tree
`a8e3481a92772ee311cdc9dd6409cd7b927a3fc1`. The intake validates the checkout's
HEAD, root tree, inventory totals, and every tracked resource's bytes against
that revision. The source pin is committed in
[`formal/openai_math_source_pin.json`](../formal/openai_math_source_pin.json).
The upstream checkout remains outside MAPEOGEO.

## Coverage and catalogue structure

The pinned source inventory contains **132,851 tracked files** and
**2,181,791,366 bytes**. These totals cover the entire Git tree, including Lean,
TeX, Markdown, PDFs, configuration files, and other supporting resources.
Catalogue coverage and source-file coverage have separate denominators:

| Source category | Pinned count | Representation |
| --- | ---: | --- |
| Tracked resources | 132,851 | One `SOURCE_RESOURCE` per tracked path |
| Tracked resource bytes | 2,181,791,366 | Exact Git blob and SHA-256 bindings |
| Catalogue families | 372 | `SOURCE_FAMILY` records preserving the actual family IDs |
| Catalogue manuscripts | 722 | `SOURCE_DOCUMENT` records linked to their catalogue PDF and resources |
| Formalization scope documents | 235 | Source resources linked to their catalogue families |
| Comparator configurations | 405 | `FORMAL_CHECK_CONFIGURATION` records |
| Selected theorem occurrences | 507 | `FORMAL_TARGET` records preserving configuration and ordinal |
| YAML-listed main results | 185 | `FORMAL_CATALOGUE_RECORD` records |

The 372 family IDs are noncontinuous. The importer reads the actual IDs from
`CONTENTS.md` and preserves them; it does not generate families from a numeric
range. Manuscripts retain their directory and catalogue PDF identity, and
tracked resources under each manuscript directory are linked to that document.

The 507 selected occurrences come from all 405 Comparator configurations.
Each occurrence has its own configuration and target ordinal, so repeated
names retain their distinct source contexts. The 185 entries in
`lean/formalization.yaml` are a narrower upstream main-result catalogue and
remain separately identifiable. The 235 scope documents describe upstream
formalization scope and are attached to the corresponding family.

Configuration metadata preserves the selected theorem names, challenge and
solution modules, permitted axioms, definition names, and configured external
checker options when present. Recording these settings does not execute the
configured checks.

## Evidence recorded in the graph

The intake appends source types outside the historical mathematical declaration
and proof-evidence registries:

| Node type | Evidence represented |
| --- | --- |
| `SOURCE_REPOSITORY` | Frozen repository revision, root tree, origin, licence, and inventory totals |
| `SOURCE_RESOURCE` | Exact tracked path, Git mode, byte size, Git blob identity, SHA-256, and disposition |
| `SOURCE_FAMILY` | Catalogue family ID, title metadata, and catalogue locator/hash |
| `SOURCE_DOCUMENT` | Manuscript directory and catalogue PDF relationship |
| `FORMAL_CHECK_CONFIGURATION` | Upstream Comparator configuration metadata |
| `FORMAL_TARGET` | A selected theorem occurrence in a configuration |
| `FORMAL_CATALOGUE_RECORD` | An entry in the upstream YAML main-result catalogue |
| `SOURCE_RECORD` | A located lexical declaration or mathematical-environment candidate |
| `SOURCE_REFERENCE_RECORD` | Explicit reference metadata whose target remains unresolved |
| `UNRESOLVED_DEFICIT` | A machine-coded extraction or target-resolution deficit |

No raw source, proof prose, excerpts, or page images are persisted in the graph.
Paths, declaration names, explicit reference targets, catalogue titles, structured
configuration metadata, locators, and hashes provide the source description.
The original files remain available in the separately retained upstream checkout.

Each resource records its repository revision, exact path, Git blob SHA-1,
SHA-256, tracked size and mode, and a revision-specific upstream locator. Each
lexical record links to its full-file resource and repeats that file's SHA-256
as both `source_sha256` and `context_sha256`. It also carries half-open byte
locators, one-based line locators, a `span_sha256`, and a `header_sha256`.
These bindings preserve the complete file context needed for later interpretation.
A standalone span hash does not establish the declaration's hypotheses or meaning.

The intake receipt binds the source pin, preserved foundation file, and
implementation files by SHA-256. The source manifest records every tracked
resource's content identity, extraction disposition, lexical record/reference
counts, and diagnostic codes. Its inventory digest covers the ordered resource
metadata.

## Lexical extraction

[`mapeogeo/openai_math_source.py`](../mapeogeo/openai_math_source.py) exposes:

```python
scan_source(path: str, data: bytes) -> dict
```

The result contains `records`, `references`, `disposition`, and `diagnostics`.
The scanner processes one exact resource at a time and reads no additional files.

### Lean

Lean extraction recognizes `theorem`, `lemma`, `def`, `abbrev`, `instance`,
`structure`, `inductive`, `opaque`, `class`, `axiom`, and `example` commands.
Nested block comments, line comments, escaped ordinary strings,
hash-delimited raw strings, and character literals are masked while preserving
original UTF-8 byte offsets. Quoted and primed identifiers, common declaration
modifiers and attributes, multiline declaration names, local instances, and
instance priority metadata are handled lexically. Anonymous instances and
examples receive deterministic names derived from their kind and byte position.

Namespace, section, and mutual-block delimiters determine the lexical
`qualified_name`. This name expresses the visible namespace stack; elaboration
may assign a different identity, including private/generated names. A declaration
span ends at the next recognized source command keyword and can include
intervening whitespace or comments. The header hash stops before a visible
outermost `:=`, `where`, or constructor `|`, respecting binder delimiters and
quoted identifiers.

Lean import directives become explicit source references. The importer resolves
an import when its module path maps to a tracked `lean/<module>.lean` resource.
An import outside that tree retains an `EXTERNAL_MODULE` reference state.

### TeX and Markdown

TeX extraction records recognized mathematical environments, aliases declared by
`newtheorem` in that file, proof environments, equation environments, and
bracket/double-dollar display mathematics. A label inside a recognized record
can supply its name; otherwise the name derives from the environment kind and
byte position. Environment headers and complete source spans are hashed.
Comments and verbatim environments/inline verb syntax are masked in source order,
including explicit diagnostics for unterminated verbatim syntax.

The scanner records explicit input/include directives, references, citations,
labels, and supported bibliography/include metadata. Markdown extraction
records ordinary explicit inline links. Reference metadata can identify its
containing TeX record when that relationship is available lexically.

### Dispositions and limits

| Disposition | Meaning |
| --- | --- |
| `lean_lexically_scanned` | Lean lexical extraction completed, with any diagnostics retained separately |
| `tex_lexically_scanned` | TeX lexical extraction completed, with any diagnostics retained separately |
| `markdown_lexically_scanned` | Supported Markdown inline links were inspected |
| `metadata_only` | Resource identity is retained; its format has no lexical extractor |
| `binary_metadata_only` | Resource identity is retained for binary content or a known binary format |
| `decode_error` | Supported text could not be decoded as UTF-8; an explicit diagnostic is retained |

Lexical extraction does not expand macros, elaborate Lean, synthesize generated
constructors, traverse TeX includes, or interpret Markdown reference-style links
and autolinks. A TeX alias defined exclusively in another resource remains
outside the single-file environment classifier. Nested/macro-expanded reference
arguments and same-line compound Lean commands can require later interpretation.
Unclosed scopes/environments, unsupported formats, and decoding failures remain
machine-coded deficits attached to their source resource.

Masking and ordinary scanning avoid repeated whole-file-tail copies. Per-file
memory includes the input, masked bytes, line offsets, extracted metadata, and
scope stacks. Hashing nested TeX records revisits overlapping spans; adversarially
deep mathematical-environment nesting can increase the hashing work beyond a
strictly linear scan.

## Meaning of statuses and references

All imported nodes begin with `verification_status: UNTESTED`, and imported
edges carry `evidence_status: UNVERIFIED`. More specific fields identify the
work actually performed:

| Field or status | Interpretation |
| --- | --- |
| Resource `source_integrity_status: HASH_VERIFIED` | Tracked source bytes match their pinned Git blob and recorded SHA-256 |
| Record `extraction_status: LEXICAL_CANDIDATE` | A source construct was located by the lexical scanner |
| Record hypothesis/semantic statuses `UNRESOLVED` | Hypotheses and mathematical alignment await interpretation |
| Record/target `kernel_verification_status: UNTESTED` | No kernel check was performed by this intake |
| Configuration `independent_run_status: NOT_RUN` | Configured proof/checker execution was not run |
| Configuration/target correspondence `UNREVIEWED` | Source-to-statement correspondence awaits review |
| Scope `UPSTREAM_DESCRIPTION` | The relationship retains the upstream description of scope |
| Target match `LEXICAL_NAME_ONLY` | A source name matched the selected target name in its solution file |
| Receipt `status: PASS` | The source intake's identity, coverage, serialization, and structural checks passed |

The intake performs **zero Lean checker runs**, creates **zero kernel
certificates**, and adds **zero semantic-equivalence edges**. It does not add
proof, implication, canonical-identity, or certificate promotions to the
historical registries. Upstream review metadata remains attributed to upstream.
The receipt explicitly records `formal_semantic_extraction: NOT_ELABORATED` and
`canonical_reconciliation: UNRESOLVED_PER_SOURCE_RECORD`.

References to existing tracked resources receive `SOURCE_REFERENCE` edges with
`RESOLVED` or Markdown `LOCAL_ANCHOR` resolution states. TeX labels remain
`SYMBOLIC_LABEL` records even when their identifiers resemble URLs or filenames.
Parameterized TeX input/include targets retain `SYMBOLIC_REFERENCE` status.
Symbolic TeX references/citations,
external modules/resources, malformed targets, and unresolved paths retain
`SOURCE_REFERENCE_RECORD` nodes and `HAS_UNRESOLVED_REFERENCE` edges. Their
resolution states preserve the reason: `SYMBOLIC_LABEL`, `SYMBOLIC_REFERENCE`, `EXTERNAL_MODULE`,
`EXTERNAL_RESOURCE`, `MALFORMED_REFERENCE`, or `UNRESOLVED_REFERENCE`.
`semantic_dependency_status: NOT_ESTABLISHED` records the remaining
interpretation deficit. A located source reference establishes an explicit
source relationship; it does not establish mathematical dependency.

A selected theorem with zero or multiple lexical matches receives a
`LEXICAL_TARGET_NOT_UNIQUELY_RESOLVED` deficit. A unique name match remains
unreviewed and requires Lean elaboration and statement review for stronger claims.

## Preservation and validation

The importer copies the foundation graph's existing node and edge payloads
verbatim into the merged graph. Historical declaration identities, payloads,
proof statuses, and certificates remain preserved. Imported records are additive
and use source-revision/path/span-derived identities.

The writer enforces unique emitted IDs, rejects conflicting payloads sharing an
ID, and checks every edge endpoint against the complete node registry before
sealing the graph. Tracked content mismatches, source-pin mismatches, catalogue
coverage mismatches, missing configured modules, and missing catalogue manuscript
resources fail the intake. A base graph that already contains `oam:` intake nodes
is rejected; deterministic replay starts from the preserved foundation base.

## Running the intake

Run these commands from the MAPEOGEO repository root with Python 3.12 and Git
available. Install the dedicated dependency set:

```bash
python -m pip install -r requirements-openai-math-intake.txt
```

Prepare an external checkout at the pinned commit. For example:

```bash
git clone https://github.com/openai/math.git ../openai-math-source
git -C ../openai-math-source checkout --detach adc7f1241b42e322a6451854ab7e4b4c146bf78a
```

The complete reconstruction target runs the existing chain through foundation
and then the source intake:

```bash
python scripts/reconstruct_pipeline.py \
  --target-stage openai-math \
  --openai-math-source ../openai-math-source
```

The integrated target writes to `artifacts/openai_math`. Its foundation input is
`artifacts/foundation_backfill/mapeogeo_foundation_graph.json.gz`. Existing
reconstruction targets remain available.

To reuse a separately preserved foundation base and choose the destination
explicitly, run the intake directly:

```bash
python scripts/openai_math_intake.py \
  --source-repo ../openai-math-source \
  --base-graph artifacts/foundation_backfill/mapeogeo_foundation_graph.json.gz \
  --out-dir artifacts/openai_math
```

The source-independent scanner, intake, and integration tests are:

```bash
python -m pytest -q tests/test_openai_math_source.py \
  tests/test_openai_math_intake.py \
  tests/test_openai_math_reconstruction.py
```

The GitHub workflow at
[`.github/workflows/openai-math-intake.yml`](../.github/workflows/openai-math-intake.yml)
runs source-independent tests for relevant changes. Its manually dispatched
`full_intake` option fetches the pinned source revision, reconstructs foundation,
runs the entire intake, and uploads the three output artifacts.

## Artifacts, publication, and replay

A successful destination is a complete directory containing exactly:

| Artifact | Contents |
| --- | --- |
| `mapeogeo_openai_math_graph.json.gz` | The full merged core graph, including preserved foundation and all imported source metadata |
| `source_manifest.json.gz` | Exact tracked-resource inventory, identities, dispositions, and extraction counts |
| `intake_report.json` | Coverage, graph and manifest hashes, counts, preservation evidence, resolution/diagnostic totals, and verification scope |

The importer builds these files in a temporary sibling staging directory. It
publishes the complete directory only after graph endpoint checks, manifest
construction, and report creation have completed. Failed staging is cleaned up.
An existing destination with the exact same three files and byte hashes is
accepted as an identical replay. A changed existing destination is preserved and
the command fails with an instruction to select a fresh `--out-dir`.

For an independent replay, use the same pinned checkout, preserved foundation
base, source pin, implementation, and runtime, and select a fresh directory:

```bash
python scripts/openai_math_intake.py \
  --source-repo ../openai-math-source \
  --base-graph artifacts/foundation_backfill/mapeogeo_foundation_graph.json.gz \
  --out-dir artifacts/openai_math_replay

sha256sum artifacts/openai_math/mapeogeo_openai_math_graph.json.gz \
  artifacts/openai_math_replay/mapeogeo_openai_math_graph.json.gz
sha256sum artifacts/openai_math/source_manifest.json.gz \
  artifacts/openai_math_replay/source_manifest.json.gz
sha256sum artifacts/openai_math/intake_report.json \
  artifacts/openai_math_replay/intake_report.json
```

The corresponding hashes must match. Canonical serialization, deterministic
ordering, fixed gzip metadata, and the absence of volatile run timestamps support
byte-for-byte replay. Implementation changes alter the implementation binding;
use a fresh destination for the resulting intake.

## Memory and downstream readers

The graph writer streams nodes and spools edges to compressed temporary storage
until endpoint validation can complete. It does not retain millions of node/edge
payloads. Memory still grows with compact ID/payload digest registries, the
tracked-resource inventory and manifest, configuration/catalogue metadata, the
small foundation base, and the current file's scanner results. Adequate memory
and disk capacity are required for the complete corpus and staging artifacts.

The merged graph has millions of source records. Consumers must stream its
arrays with a parser such as `ijson`; loading the full output with `json.load`
can exhaust memory. For example, count nodes without materializing the array:

```python
import gzip
import ijson

with gzip.open("artifacts/openai_math/mapeogeo_openai_math_graph.json.gz", "rb") as handle:
    node_count = sum(1 for _ in ijson.items(handle, "nodes.item"))
print(node_count)
```

Repeat with `edges.item` for edges. Preserve the original foundation base for
replay; feeding the large merged graph back as the base is unsupported.

## Independent verification

The independent verifier reads the merged graph once with `ijson` and uses a
temporary SQLite database for identity and endpoint checks. It rechecks the
complete Git tree and source bytes, source span hashes, original graph payloads,
catalogue/configuration coverage, evidence statuses, reference classifications,
and the receipt's content digests. Its receipt also binds the verifier itself by
SHA-256. It imports no intake implementation code.

```bash
python scripts/verify_openai_math_intake.py \
  --source-repo ../openai-math-source \
  --base-graph artifacts/foundation_backfill/mapeogeo_foundation_graph.json.gz \
  --graph artifacts/openai_math/mapeogeo_openai_math_graph.json.gz \
  --manifest artifacts/openai_math/source_manifest.json.gz \
  --report artifacts/openai_math/intake_report.json \
  --output artifacts/openai_math_verification.json
```

The verifier receipt is separate from the three-file intake directory so that
an identical intake can still be replayed into that directory.

## Measured acceptance

The corrected full source intake and independent serialized-output audit both
passed. The committed receipt is
[`evidence/openai_math_intake_acceptance.json`](../evidence/openai_math_intake_acceptance.json).

| Measured item | Result |
| --- | ---: |
| Tracked resources / source bytes | 132,851 / 2,181,791,366 |
| Lexical source records and checked span hashes | 3,762,712 |
| Merged graph nodes | 4,224,730 |
| Merged graph edges | 4,547,502 |
| Historical nodes / edges preserved exactly | 3,314 / 27,994 |
| Unique lexical target matches | 406 / 507 |
| Explicit target-resolution deficits | 101 |
| Resolved source references | 286,062 |
| Symbolic TeX labels | 89,221 |
| Graph size, compressed bytes | 716,438,229 |
| Manifest size, compressed bytes | 11,066,708 |
| Independent audit elapsed time | 393.1 seconds |
| Independent audit peak RSS | 134,224 KiB |

The lexical total includes declarations, instances, proofs, and mathematical
environments at their individual source locations. The 101 unmatched selected
target occurrences remain represented with explicit deficits. Targets imported
through other modules require later elaboration and correspondence review.

The scanner recorded 106 unmatched named Lean ends, five unmatched TeX
environment ends, and one unclosed TeX environment. A further 1,217 supporting
resources received an explicit metadata-only disposition. These observations
remain visible in the graph and receipt.

The graph SHA-256 is:

```text
5d3a647cc88e19efe646a5da72ce2f8e640e338a22cbfe13b80e4f0aae9aa145
```

The source manifest SHA-256 is:

```text
d772f93446503c80c1484c33566c809caa4c480179e8ab83d36d173f18297a9a
```

Fresh focused validation passed **78 tests**, including the existing relevant
source-integrity suites. The committed software fixture verifies identical
outputs across fresh directories, identical same-directory replay, and preservation
of prior output after an injected publication failure. The corrected full corpus
received one complete import and one independent audit; a second complete
corrected-corpus replay was not run.

The broad repository suite was attempted and interrupted after more than ten
minutes in unrelated experimental campaigns. Its partial progress showed 126
passes, 19 failures, and eight setup errors; this is not a complete suite result.
The existing E26-E31 experiments require frozen fixture checkouts absent in this
environment. A separate existing GFYProof bridge test failed against its pinned
dependency because `build_edge_certificate` does not accept
`verifier_semantic_id`. These broader issues are recorded in the acceptance
receipt and were not changed by the source intake.

Source interpretation remains lexical, canonical reconciliation remains
unresolved, and Lean checker execution remains at zero.
