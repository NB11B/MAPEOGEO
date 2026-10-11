# SOVCTX-KG Jetson Nano Expansion Engineering Plan

**Target:** Jetson Nano 2 GB at `uow@192.168.55.1`  
**Graph:** SOVCTX-KG only  
**Repository branch:** `research/sovctx-kg`  
**Isolation rule:** MAPEOGEO canonical graph is not part of the SOVCTX runtime.

## 1. Objective

Use the existing Nano as a low-power, unattended source-acquisition, equation-extraction, behavioral-qualification, and graph-materialization node for SOVCTX-KG.

The Nano is **not** an authority that can promote historical claims by itself. It generates evidence-bearing candidate records. Promotion remains fail-closed through the SOVCTX provenance, fragment, equation, and behavioral gates.

## 2. Current live envelope

Observed Nano resources supplied from live census:

- Root filesystem: 58 GB
- Used: 22 GB
- Free: 34 GB
- RAM: 1.9 GB
- Available RAM: ~1.4 GB at idle
- Swap: 5.0 GB total / ~4.8 GB free
- CPU: 4 x Cortex-A57, idle at census
- Power mode: MAXN / 10 W
- Thermal range observed: 34-50 C
- Existing MAPEOGEO runtime footprint: 5.8 GB
- Existing MAPEOGEO canonical SQLite: 4.9 GB

This is sufficient for SOVCTX if ingestion is streamed and memory-bounded.

## 3. Isolation architecture

Recommended filesystem:

```
/home/uow/
  mapeogeo-m0/                 # existing; leave untouched
  sovctx-kg/                   # SOVCTX git worktree
  sovctx-data/
    raw/                       # content-addressed downloaded source blobs
    cache/                     # disposable HTTP/PDF extraction cache
    staging/                   # candidate JSONL and equation extraction
    quarantine/                # malformed/oversized/unsafe source files
    db/
      sovctx_work.sqlite3      # mutable acquisition/queue database
      sovctx_graph.sqlite3     # derived canonical materialization
    evidence/
      runs/
      manifests/
      equation_results/
    snapshots/
    logs/
    tmp/
```

### Hard rule

No normal SOVCTX process opens:

```
/home/uow/mapeogeo-m0/evidence/mapeogeo_canonical_graph_indexed.sqlite3
```

A future cross-graph bridge must be a separate read-only campaign and may emit only quarantined candidate crosswalk records.

## 4. Git deployment

Prefer a worktree to avoid duplicating repository objects:

```bash
cd /home/uow/mapeogeo-m0
git fetch origin research/sovctx-kg
git worktree add --detach /home/uow/sovctx-kg origin/research/sovctx-kg
```

For autonomous commits, use a dedicated Nano branch instead:

```bash
git worktree add -b nano/sovctx-ingest /home/uow/sovctx-kg origin/research/sovctx-kg
```

Recommended policy: Nano writes candidates/evidence to `nano/sovctx-ingest`; canonical promotion is reviewed/merged into `research/sovctx-kg`.

## 5. Runtime layers

### Layer A — Acquisition

Input: `sovctx/corpus/ingestion_queue.jsonl`

Responsibilities:
- fetch source URLs
- honor ETag / Last-Modified
- SHA-256 every payload
- content-address duplicate blobs
- record HTTP metadata
- classify HTML / PDF / image / text
- reject oversized payloads
- never execute downloaded content

Output:
- immutable raw blob
- acquisition ledger row
- candidate source status

### Layer B — Extraction

Preferred order:
1. native HTML/text
2. PDF text layer
3. PDF page extraction
4. mark `needs_ocr` if scan-only

Do not make OCR part of the normal Nano path initially. Scan-heavy sources should be queued for workstation/cloud OCR or handled one document at a time under an explicit resource budget.

Outputs:
- candidate source fragments
- equation-like text spans
- Russian/Latin terminology spans
- page/locator metadata

### Layer C — Equation normalization

For every candidate equation preserve:

```
original_notation
normalized_notation
source_fragment_id
symbols
symbol_semantics
assumptions
equation_kind
family_candidate
```

Normalization must never overwrite original notation.

### Layer D — Behavioral qualification

Run:

```bash
python sovctx/tools/validate_graph.py
python sovctx/tools/qualify_equations.py
python sovctx/tools/qualify.py
```

Behavioral PASS means only that the recorded equation satisfies declared transformations.

It does not change:
- source verification status
- provenance class
- physical-truth status
- historical-influence status

### Layer E — Materialization/search

Rebuild derived SQLite:

```bash
python sovctx/tools/build_sqlite.py --output /home/uow/sovctx-data/db/sovctx_graph.sqlite3
```

Canonical truth remains JSONL in Git.

Add FTS/search tables only to the derived database.

## 6. Nano resource governor

Recommended hard thresholds:

```yaml
disk:
  stop_free_gb: 14
  warn_free_gb: 18
ram:
  stop_available_mb: 300
  warn_available_mb: 450
swap:
  stop_used_gb: 2.5
thermal:
  warn_c: 70
  stop_c: 77
load:
  max_1m: 3.25
workers:
  network: 2
  extraction: 1
  qualification: 1
```

Normal target RSS for any individual SOVCTX worker: **<= 650 MB**.

Do not use swap as normal working memory. Swap growth is a backpressure signal.

## 7. Storage budgets

With 34 GB currently free:

| Area | Initial cap |
|---|---:|
| raw source CAS | 6 GB |
| extraction/cache | 2 GB |
| mutable work DB | 2 GB |
| canonical derived DB | 3 GB |
| evidence/manifests | 2 GB |
| snapshots | 2 GB |
| temp/quarantine | 1 GB |
| planned SOVCTX maximum | 18 GB |
| minimum protected free space | 14 GB |

Raw content should be GC-safe by SHA references: never delete a blob referenced by an evidence manifest.

## 8. SQLite settings for 2 GB RAM

Recommended mutable work database defaults:

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA temp_store=FILE;
PRAGMA cache_size=-65536;
PRAGMA mmap_size=67108864;
PRAGMA busy_timeout=5000;
```

Keep write transactions short.

Recommended ingest transaction batch:
- 25 source documents, or
- 100 candidate fragments, or
- 100 candidate equations,
whichever comes first.

Checkpoint WAL after every batch.

## 9. Candidate/authority boundary

Nano records have explicit lifecycle states:

```
DISCOVERED
-> ACQUIRED
-> EXTRACTED
-> CANDIDATE
-> BEHAVIOR_QUALIFIED
-> EVIDENCE_COMPLETE
-> PROMOTION_READY
-> CANONICAL
```

Only the final transition may modify canonical SOVCTX JSONL.

No candidate may use:
- `verified_primary`
- `verified_scan`
- `DOCUMENTED_INFLUENCE`
unless the required source/fragment gate is actually satisfied.

## 10. Work database

Recommended tables:

```
fetch_queue
fetch_attempts
source_blobs
candidate_sources
candidate_fragments
candidate_equations
candidate_symbols
candidate_claims
candidate_edges
behavior_runs
promotion_queue
quarantine
daemon_runs
resource_samples
```

Every candidate row includes:
- source URL
- SHA-256
- acquisition timestamp
- parser version
- originating queue item
- candidate JSON
- status
- rejection reason if applicable

## 11. Source crawler priorities

### P0 equation/source families

1. Rodimov 1976 full text / scans
2. Zolotarev multicavity manuscript scans
3. Grebennikov-Zolotarev 1984 letter primary image
4. Grebennikov/Grebennikov/Zolotarev 1986 proceedings primary pages
5. Markov 1906 original text
6. Andronov-Pontryagin 1937 *Rough Systems*
7. Faddeev 1959 inverse-scattering equations
8. Bernstein 1961 full article
9. Gelfand-Gurfinkel-Tsetlin 1962 pp. 66-73
10. Okhotsimsky 1956 oriented-satellite report

### P1 expansion

- Euler/Petersburg corpus
- Chebyshev mechanism synthesis
- Lyapunov 1892 direct equation transcription
- Pontryagin 1960 remaining maximum-principle equations
- Tikhonov 1963 remaining convergence/Euler equations
- Vlasov 1938/1967 dispersion relations
- Mandelstam/Papaleksi/Andronov nonlinear oscillations
- Leontovich/Fock/Malyuzhinets/Ufimtsev radio physics
- Soviet bionics volumes
- Keldysh/Eneev trajectory-control equations

## 12. Source discovery strategy

The Nano should use bounded frontier expansion.

A source may nominate:
- explicit citations
- author bibliography
- institutional series
- references with Soviet/Russian dates/institutions
- equation antecedents
- direct correspondence

Each nomination is a candidate queue item, not a graph edge.

Maximum automatic citation depth per campaign: **2**.

Maximum new candidate URLs per source: **25**.

This prevents crawler explosion.

## 13. Equation behavioral pipeline

For every extracted equation:

```
source equation
-> parse symbols
-> preserve native notation
-> identify equation family
-> generate candidate behavioral tests
-> run exact tests where possible
-> store result artifact
-> human/source review
-> promotion
```

Preferred automated test classes:
- substitution
- scaling
- index shift
- symmetry
- composition
- limiting case
- dimensional structure
- monotonicity
- invariance
- reversibility
- domain boundaries

Never generate a proof-status claim from a behavioral test.

## 14. Daemons

Recommended processes:

```
sovctx-resource-guard
sovctx-acquire
sovctx-extract
sovctx-equation-qualify
sovctx-materialize
sovctx-audit
```

Only one CPU-heavy extraction/qualification task runs at a time.

The resource guard may pause every worker through a shared `PAUSE` file or SQLite runtime flag.

## 15. Schedule

Recommended operating cadence:

- acquisition: small batch every hour while network is available
- extraction: continuous single worker while resource gate is green
- equation qualification: after each promoted/candidate equation batch
- SQLite rebuild: after canonical changes only
- audit manifest: after each campaign/batch
- snapshot: daily if canonical graph changed
- full qualification: daily and before any Git push

## 16. Fault tests

Qualification campaign **NANO-SOVCTX-0** should include:

1. network disappears mid-fetch
2. HTTP 404/403/429
3. duplicate URL with identical bytes
4. different URL with identical SHA-256
5. truncated PDF
6. corrupt PDF
7. scan-only PDF
8. 100 MB payload rejection
9. disk falls below stop threshold
10. RAM falls below stop threshold
11. swap exceeds threshold
12. thermal stop condition
13. worker killed mid-transaction
14. WAL recovery
15. duplicate candidate IDs
16. malformed JSONL candidate
17. claim attempts primary promotion without fragment
18. equation fragment/source mismatch
19. behavior test without evaluator
20. attempted write/open of MAPEOGEO canonical DB by SOVCTX process

All must fail closed.

## 17. Endurance gates

### N0 — Isolation
- directory/db/process separation
- no MAPEOGEO database opens
- graph validator PASS

### N1 — 100-source qualification
- 100 source acquisitions
- zero duplicate canonical blobs
- zero provenance promotions outside policy
- deterministic rebuild PASS

### N2 — Equation campaign
- >= 25 new source-grounded equations or explicit no-equation dispositions
- 100% equation source-fragment binding
- automated behavior tests PASS where declared

### N3 — 24-hour endurance
- unattended
- no OOM
- no thermal stop that fails to recover
- no DB corruption
- protected disk floor retained

### N4 — 7-day campaign
- bounded storage growth
- deterministic canonical digest after rebuild
- complete evidence manifests
- no cross-graph contamination

## 18. Cross-graph policy

SOVCTX and MAPEOGEO remain independent canonical graphs.

Future bridge directory:

```
sovctx/bridge/
  candidates.jsonl
  evidence/
```

Only these relations may be proposed initially:

```
CANDIDATE_REPRESENTS
STRUCTURALLY_ANALOGOUS_TO
CANDIDATE_OPERATOR_MATCH
```

Never auto-promote to:

```
REPRESENTS
SAME_SEMANTICS
SAME_OPERATOR
```

The MAPEOGEO graph is never a truth source for SOVCTX historical claims.

## 19. Immediate implementation order

1. create Nano worktree and `/home/uow/sovctx-data`
2. deploy Python runtime using stdlib where possible
3. deploy resource governor
4. create work SQLite + schema
5. import current ingestion queue
6. implement HTTP acquisition + content-addressed blob store
7. implement HTML/PDF extraction
8. implement candidate fragment/equation writer
9. reuse current SOVCTX validators and equation qualifier
10. run N0 isolation tests
11. run a 10-source smoke campaign
12. expand to N1 100-source campaign
13. only then enable unattended hourly acquisition

## 20. Non-goals for initial Nano phase

Do not initially:
- run a large LLM
- run bulk OCR
- ingest into MAPEOGEO
- auto-merge canonical graph changes
- infer undocumented historical influence
- treat behavioral equivalence as semantic equivalence
- use the 5 GB swap as routine memory

The Nano's advantage here is persistent, low-power, deterministic acquisition and qualification—not model size.
