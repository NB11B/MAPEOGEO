# SOVCTX-KG Query Examples

Canonical truth remains JSONL. SQLite is a derived materialization.

## Build

```bash
python sovctx/tools/validate_graph.py
python sovctx/tools/build_sqlite.py
```

## Basic graph queries

```bash
python sovctx/tools/query_graph.py stats
python sovctx/tools/query_graph.py node PUB:GELFAND_TSETLIN_1961_NONLOCAL
python sovctx/tools/query_graph.py claims --source PUB:GELFAND_TSETLIN_1961_NONLOCAL
python sovctx/tools/query_graph.py operator OP:NONLOCAL_MOVE
python sovctx/tools/query_graph.py open
```

## Neighbors

```bash
python sovctx/tools/query_graph.py neighbors PERSON:BERNSTEIN_NA
python sovctx/tools/query_graph.py neighbors PUB:GELFAND_TSETLIN_1961_NONLOCAL --direction out
python sovctx/tools/query_graph.py neighbors PUB:GELFAND_TSETLIN_1961_NONLOCAL --edge-type ASSERTS
```

## Path queries

Any graph path:

```bash
python sovctx/tools/query_graph.py path PUB:GELFAND_TSETLIN_1961_NONLOCAL PERSON:BERNSTEIN_NA
```

Exclude analytical/synthesis edges:

```bash
python sovctx/tools/query_graph.py path \
  PUB:GELFAND_TSETLIN_1961_NONLOCAL PERSON:BERNSTEIN_NA \
  --documented-only --source-native-only
```

The documented/source-native path mode is intended for historical genealogy questions where structural analogy or SOVCTX synthesis must not be allowed to create a path.
