#!/usr/bin/env python3
"""Stream a complete, pinned source corpus into the existing MAPEOGEO graph.

Source presence, lexical declaration extraction, and formal verification have
separate meanings. This importer emits source records and explicit references;
it never elaborates Lean, executes upstream scripts, or issues proof certificates.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import contextlib
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PIN_PATH = ROOT / "formal" / "openai_math_source_pin.json"
FORBIDDEN_KEYS = {
    "statement_text", "proof_text", "source_prose", "page_image", "excerpt",
    "raw_content", "raw_text", "raw_bytes", "source_text", "full_text",
}
PROMOTED_NODE_TYPES = {"CERTIFICATE", "CANONICAL_OBJECT", "REPRESENTATION"}
PROMOTED_EDGE_TYPES = {
    "SAME_SEMANTICS", "SCOPED_OVERLAP", "IMPLIES", "PROVES", "VERIFIES",
    "KERNEL_VERIFIED", "HAS_CERTIFICATE", "PROOF_DEPENDENCY", "DEPENDS_ON",
}
VERIFIED_VALUES = {"VERIFIED", "PASS", "KERNEL_VERIFIED", "EXECUTABLE_VERIFIED"}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_metadata_only(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise ValueError(f"forbidden source prose payload key: {key}")
            assert_metadata_only(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            assert_metadata_only(child)


def _assert_no_promotion(item: dict, edge: bool = False) -> None:
    if item.get("type") in (PROMOTED_EDGE_TYPES if edge else PROMOTED_NODE_TYPES):
        raise ValueError("source intake cannot create semantic equivalence or certificate promotion")
    attrs = item.get("attributes", {})
    for key, value in attrs.items():
        if ("verification" in key or "evidence_status" == key) and isinstance(value, str) and value in VERIFIED_VALUES:
            raise ValueError("source intake cannot create proof verification promotion")


def _git(repo: Path, *args: str) -> bytes:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if proc.returncode:
        raise ValueError(f"Git source revision/identity check failed: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def git_inventory(repo: Path, revision: str) -> list[dict]:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("source revision must be a complete 40-character commit SHA")
    head = _git(repo, "rev-parse", "HEAD").decode().strip()
    if head != revision:
        raise ValueError(f"source HEAD {head} does not match pinned revision {revision}")
    entries = []
    for entry in _git(repo, "ls-tree", "-r", "-z", "-l", revision).split(b"\0"):
        if not entry:
            continue
        header, raw_path = entry.split(b"\t", 1)
        mode, kind, digest, size = header.decode("ascii").split()
        path = raw_path.decode("utf-8", errors="strict")
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts or kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"unsupported tracked source entry: {path!r} ({mode} {kind})")
        entries.append({"path": path, "mode": mode, "type": kind, "sha": digest, "size": int(size)})
    if len({entry["path"] for entry in entries}) != len(entries):
        raise ValueError("duplicate tracked source path")
    return sorted(entries, key=lambda entry: entry["path"])


def source_bytes(repo: Path, entry: dict) -> bytes:
    path = repo / entry["path"]
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(repo.resolve()):
        raise ValueError(f"source content path is missing or escapes repository: {entry['path']}")
    raw = path.read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if len(raw) != entry["size"] or blob != entry["sha"]:
        raise ValueError(f"source content does not match pinned Git blob identity: {entry['path']}")
    return raw


def parse_catalogue(contents: str) -> list[dict]:
    headers = list(re.finditer(r"^\*\*(\d{3})\.\s+(.+?)\*\*", contents, re.MULTILINE))
    families = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(contents)
        segment = contents[header.start():end]
        manuscripts = [{"title": title, "pdf_path": path} for title, path in re.findall(
            r"&emsp;\[([^\n]+?)\]\((preprints/[^\n]+?\.pdf)\)", segment)]
        families.append({"family_id": header.group(1), "title": header.group(2),
                         "catalogue_span_sha256": hashlib.sha256(segment.encode()).hexdigest(),
                         "start_line": contents.count("\n", 0, header.start()) + 1,
                         "manuscripts": manuscripts})
    if len({family["family_id"] for family in families}) != len(families):
        raise ValueError("duplicate catalogue family identity")
    return families


class GraphStream:
    """Atomic deterministic core-graph writer with bounded payload memory.

    Only digest registries are retained across source files. Edges are spooled
    compressed until every node exists, then all endpoints are checked before
    the destination is replaced. Duplicate IDs require identical payloads.
    """
    def __init__(self, path: Path, base: dict, metadata: dict):
        self.path, self.base, self.metadata = Path(path), base, metadata
        self.node_signatures: dict[bytes, bytes] = {}
        self.edge_signatures: dict[bytes, bytes] = {}
        self.node_types, self.edge_types = Counter(), Counter()
        self.node_digest, self.edge_digest = hashlib.sha256(), hashlib.sha256()
        self.nodes_count = self.edges_count = 0
        self._temporary = self._edge_path = None
        self._raw = self._out = self._edge_raw = self._edge_out = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        raw = tempfile.NamedTemporaryFile(dir=self.path.parent, prefix=".graph-", delete=False)
        edge_raw = tempfile.NamedTemporaryFile(dir=self.path.parent, prefix=".edges-", delete=False)
        self._temporary, self._edge_path = Path(raw.name), Path(edge_raw.name)
        self._raw, self._edge_raw = raw, edge_raw
        self._out = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6)
        self._edge_out = gzip.GzipFile(filename="", mode="wb", fileobj=edge_raw, mtime=0, compresslevel=1)
        meta = {key: value for key, value in self.base.items() if key not in {"nodes", "edges"}}
        meta.setdefault("graph_id", "mapeogeo-openai-math-source-intake")
        meta.setdefault("schema_version", "0.20-source-intake-v1")
        meta.setdefault("required_views", ["EO", "GEO", "FORMAL", "NATURAL"])
        old_intakes = list(meta.get("source_intakes", []))
        if self.metadata not in old_intakes:
            old_intakes.append(self.metadata)
        meta["source_intakes"] = old_intakes
        self._out.write(canonical_bytes(meta)[:-1] + b',"nodes":[')
        try:
            for node in self.base.get("nodes", []):
                self._node(node, imported=False)
            for edge in self.base.get("edges", []):
                self._edge(edge, imported=False)
        except BaseException:
            self._cleanup()
            raise
        return self

    @staticmethod
    def _identity(item: dict) -> bytes:
        if not isinstance(item.get("id"), str) or not item["id"]:
            raise ValueError("graph item requires a nonempty id")
        return hashlib.sha256(item["id"].encode()).digest()

    def _node(self, node: dict, imported: bool):
        if imported:
            assert_metadata_only(node)
            _assert_no_promotion(node)
        payload = canonical_bytes(node)
        identity, signature = self._identity(node), hashlib.sha256(payload).digest()
        if identity in self.node_signatures:
            if not imported:
                raise ValueError(f"duplicate node id in base graph: {node['id']}")
            if self.node_signatures[identity] != signature:
                raise ValueError(f"conflicting node id collision: {node['id']}")
            return
        self.node_signatures[identity] = signature
        if self.nodes_count:
            self._out.write(b",\n")
        self._out.write(payload)
        self.node_digest.update(payload + b"\n")
        self.nodes_count += 1
        self.node_types[node.get("type", "UNKNOWN")] += 1

    def add_node(self, node: dict):
        self._node(node, imported=True)

    def _edge(self, edge: dict, imported: bool):
        if imported:
            assert_metadata_only(edge)
            _assert_no_promotion(edge, edge=True)
        if not isinstance(edge.get("source"), str) or not isinstance(edge.get("target"), str):
            raise ValueError("edge endpoint identifiers must be strings")
        payload = canonical_bytes(edge)
        identity, signature = self._identity(edge), hashlib.sha256(payload).digest()
        if identity in self.edge_signatures:
            if not imported:
                raise ValueError(f"duplicate edge id in base graph: {edge['id']}")
            if self.edge_signatures[identity] != signature:
                raise ValueError(f"conflicting edge id collision: {edge['id']}")
            return
        self.edge_signatures[identity] = signature
        self._edge_out.write(payload + b"\n")
        self.edges_count += 1
        self.edge_types[edge.get("type", "UNKNOWN")] += 1

    def add_edge(self, edge: dict):
        self._edge(edge, imported=True)

    def _finish(self):
        self._edge_out.close()
        self._edge_raw.close()
        self._out.write(b'],"edges":[')
        first = True
        with gzip.open(self._edge_path, "rb") as edges:
            for line in edges:
                edge = json.loads(line)
                for endpoint in (edge["source"], edge["target"]):
                    if hashlib.sha256(endpoint.encode()).digest() not in self.node_signatures:
                        raise ValueError(f"dangling edge endpoint: {endpoint}")
                if not first:
                    self._out.write(b",\n")
                first = False
                self._out.write(line.rstrip(b"\n"))
                self.edge_digest.update(line)
        self._out.write(b"]}\n")
        self._out.close()
        self._raw.flush()
        os.fsync(self._raw.fileno())
        self._raw.close()
        os.replace(self._temporary, self.path)
        self._temporary = None

    def _cleanup(self):
        for handle in (self._out, self._edge_out, self._raw, self._edge_raw):
            with contextlib.suppress(Exception):
                if handle is not None:
                    handle.close()
        for path in (self._temporary, self._edge_path):
            if path is not None:
                with contextlib.suppress(FileNotFoundError):
                    path.unlink()

    def __exit__(self, exc_type, exc, traceback):
        try:
            if exc_type is None:
                self._finish()
        finally:
            self._cleanup()


def _load_graph(path: Path) -> dict:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        graph = json.load(handle)
    if not isinstance(graph.get("nodes"), list) or not isinstance(graph.get("edges"), list):
        raise ValueError("base graph requires node and edge arrays")
    return graph


def _node(node_id: str, node_type: str, label: str, **attrs) -> dict:
    return {"id": node_id, "type": node_type, "label": label,
            "attributes": {"stage": "openai_math", "verification_status": "UNTESTED", **attrs}}


def _edge(kind: str, source: str, target: str, **attrs) -> dict:
    identity = hashlib.sha256(canonical_bytes([kind, source, target, attrs])).hexdigest()
    return {"id": "oam:edge:" + identity, "type": kind, "source": source, "target": target,
            "attributes": {"stage": "openai_math", "evidence_status": "UNVERIFIED", **attrs}}


def _resource_id(prefix: str, path: str) -> str:
    return prefix + ":file:" + path


def _resolve_reference(path: str, reference: dict, paths: set[str]) -> tuple[str | None, str]:
    target, kind = reference["target"], reference["kind"]
    if kind == "lean_import":
        candidate = "lean/" + target.replace(".", "/") + ".lean"
        return (candidate, "RESOLVED") if candidate in paths else (None, "EXTERNAL_MODULE")
    if kind == "tex_label":
        return None, "SYMBOLIC_LABEL"
    if kind in {"tex_reference", "tex_citation"}:
        return None, "SYMBOLIC_REFERENCE"
    if kind in {"tex_input", "tex_include"}:
        if not target or any(marker in target for marker in ("#", "\\", "{", "}")):
            return None, "SYMBOLIC_REFERENCE"
        candidate = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
        candidates = [candidate] if candidate.endswith(".tex") else [candidate, candidate + ".tex"]
        for candidate in candidates:
            if candidate in paths:
                return candidate, "RESOLVED"
        return None, "UNRESOLVED_REFERENCE"
    try:
        parts = urlsplit(target)
    except ValueError:
        return None, "MALFORMED_REFERENCE"
    if parts.scheme or parts.netloc:
        return None, "EXTERNAL_RESOURCE"
    target = unquote(parts.path)
    if not target:
        return path, "LOCAL_ANCHOR"
    candidates = [posixpath.normpath(posixpath.join(posixpath.dirname(path), target))]
    for candidate in candidates:
        if candidate in paths:
            return candidate, "RESOLVED"
    return None, "UNRESOLVED_REFERENCE"


def _write_json(path: Path, value: dict):
    assert_metadata_only(value)
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    temporary = path.with_name("." + path.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def run_intake(source_repo: Path, base_path: Path, out_dir: Path) -> dict:
    """Publish the graph, manifest and receipt as one complete directory.

    Exact replays are accepted. A different existing destination is preserved;
    callers must choose a new output directory for a changed intake.
    """
    out_dir = out_dir.absolute()
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(dir=out_dir.parent, prefix=".openai-math-intake-"))
    try:
        report = _build_intake(source_repo, base_path, stage)
        if out_dir.exists():
            if not out_dir.is_dir():
                raise ValueError("intake destination exists and is not a directory")
            existing, created = {p.name for p in out_dir.iterdir()}, {p.name for p in stage.iterdir()}
            if not existing:
                os.replace(stage, out_dir)
            elif existing == created and all(
                (out_dir / name).is_file() and sha256_file(out_dir / name) == sha256_file(stage / name)
                for name in created
            ):
                return report
            else:
                raise ValueError("different intake output already exists; select a fresh --out-dir")
        else:
            os.replace(stage, out_dir)
        return report
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def _build_intake(source_repo: Path, base_path: Path, out_dir: Path) -> dict:
    from mapeogeo.openai_math_source import scan_source
    from scripts.io_utils import atomic_write_deterministic_json_gzip
    import yaml

    pin = json.loads(PIN_PATH.read_text())
    revision, expected = pin["revision"], pin["expected"]
    prefix = "oam:" + revision
    source_repo = source_repo.resolve()
    entries = git_inventory(source_repo, revision)
    paths = {entry["path"] for entry in entries}
    by_path = {entry["path"]: entry for entry in entries}
    tree = _git(source_repo, "rev-parse", revision + "^{tree}").decode().strip()
    if tree != pin["tree"]:
        raise ValueError("source root tree does not match pin")
    if len(entries) != expected["tracked_files"] or sum(entry["size"] for entry in entries) != expected["tracked_bytes"]:
        raise ValueError("complete source tree count/byte total does not match source pin")
    catalogue_raw = source_bytes(source_repo, by_path["CONTENTS.md"])
    families = parse_catalogue(catalogue_raw.decode())
    manuscripts = [paper for family in families for paper in family["manuscripts"]]
    configs = []
    for path in sorted(paths):
        if path.startswith("lean/ComparatorChallenges/") and path.endswith(".json"):
            config = json.loads(source_bytes(source_repo, by_path[path]))
            configs.append({"path": path, **config})
    formalization = yaml.safe_load(source_bytes(source_repo, by_path["lean/formalization.yaml"]))
    main_results = formalization["status"]["main_results"]
    scopes = sorted(path for path in paths if re.fullmatch(r"lean/docs/\d{3}\.md", path))
    observed = {
        "tracked_files": len(entries), "tracked_bytes": sum(entry["size"] for entry in entries),
        "families": len(families), "manuscripts": len(manuscripts), "scope_documents": len(scopes),
        "comparator_configurations": len(configs),
        "selected_theorem_occurrences": sum(len(config["theorem_names"]) for config in configs),
        "catalogue_main_results": len(main_results),
    }
    if observed != expected:
        raise ValueError(f"source catalogue coverage differs from pin: {observed}")
    if len({paper["pdf_path"] for paper in manuscripts}) != len(manuscripts):
        raise ValueError("duplicate catalogue manuscript path")
    if any(paper["pdf_path"] not in paths for paper in manuscripts):
        raise ValueError("catalogue references a missing manuscript")
    base = _load_graph(base_path)
    if any(str(node["id"]).startswith("oam:") for node in base["nodes"]):
        raise ValueError("base already contains a source intake; replay from its preserved foundation base")
    base_hash = sha256_file(base_path)
    metadata = {"repository": pin["repository"], "revision": revision, "tree": tree,
                "base_graph_sha256": base_hash, "intake_version": 1,
                "source_pin_sha256": sha256_file(PIN_PATH),
                "implementation_sha256": {name: sha256_file(ROOT / name) for name in (
                    "scripts/openai_math_intake.py", "mapeogeo/openai_math_source.py", "scripts/io_utils.py")},
                "verification_scope": "SOURCE_IDENTITY_AND_LEXICAL_STRUCTURE_ONLY"}
    out_dir.mkdir(parents=True, exist_ok=True)
    graph_path = out_dir / "mapeogeo_openai_math_graph.json.gz"
    repo_id = prefix + ":repository"
    counts, reference_counts, dispositions, diagnostics = Counter(), Counter(), Counter(), Counter()
    inventory_digest = hashlib.sha256()
    target_lookups: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    target_matches = Counter()
    target_ids: list[str] = []
    resource_manifest: list[dict] = []
    print(f"Pinned {len(entries):,} source files; writing full graph", flush=True)

    with GraphStream(graph_path, base, metadata) as graph:
        graph.add_node(_node(repo_id, "SOURCE_REPOSITORY", "OpenAI mathematics repository",
                             repository=pin["repository"], revision=revision, root_tree=tree,
                             url=pin["url"], license=pin["license"], tracked_files=len(entries),
                             tracked_bytes=observed["tracked_bytes"], source_origin="MODEL_PRODUCED_RESEARCH"))
        # Logical catalogue records preserve family scope without inheriting proof status.
        family_ids = {family["family_id"] for family in families}
        for family in families:
            family_id = prefix + ":family:" + family["family_id"]
            graph.add_node(_node(family_id, "SOURCE_FAMILY", family["title"],
                                 family_id=family["family_id"], source_resource=_resource_id(prefix, "CONTENTS.md"),
                                 catalogue_span_sha256=family["catalogue_span_sha256"], start_line=family["start_line"]))
            graph.add_edge(_edge("CONTAINS_SOURCE_RECORD", repo_id, family_id))
            graph.add_edge(_edge("SOURCE_DOCUMENTS", family_id, _resource_id(prefix, "CONTENTS.md")))
            for paper in family["manuscripts"]:
                directory = paper["pdf_path"].rsplit("/", 1)[0]
                paper_id = prefix + ":manuscript:" + directory
                graph.add_node(_node(paper_id, "SOURCE_DOCUMENT", paper["title"],
                                     directory=directory, catalogue_pdf=paper["pdf_path"], family_id=family["family_id"]))
                graph.add_edge(_edge("CONTAINS_SOURCE_RECORD", family_id, paper_id))
                graph.add_edge(_edge("HAS_SOURCE_RESOURCE", paper_id, _resource_id(prefix, paper["pdf_path"])))
        paper_dirs = {paper["pdf_path"].split("/")[1] for paper in manuscripts}
        config_ids = {}
        for config in configs:
            config_id = prefix + ":configuration:" + config["path"]
            config_ids[config["path"]] = config_id
            graph.add_node(_node(config_id, "FORMAL_CHECK_CONFIGURATION", PurePosixPath(config["path"]).stem,
                                 source_resource=_resource_id(prefix, config["path"]),
                                 challenge_module=config["challenge_module"], solution_module=config["solution_module"],
                                 selected_theorem_names=config["theorem_names"],
                                 permitted_axioms=config.get("permitted_axioms", []),
                                 definition_names=config.get("definition_names", []),
                                 external_checker_configuration={key: config[key] for key in ("enable_nanoda", "external_kernels") if key in config},
                                 independent_run_status="NOT_RUN", statement_correspondence_status="UNREVIEWED"))
            graph.add_edge(_edge("SOURCE_DOCUMENTS", config_id, _resource_id(prefix, config["path"])))
            for role in ("challenge_module", "solution_module"):
                module_path = "lean/" + config[role].replace(".", "/") + ".lean"
                if module_path not in paths:
                    raise ValueError(f"missing Comparator module: {module_path}")
                graph.add_edge(_edge("CONFIGURES_SOURCE_CHECK", config_id, _resource_id(prefix, module_path), role=role))
            for ordinal, theorem in enumerate(config["theorem_names"]):
                target_id = config_id + ":target:" + str(ordinal)
                target_ids.append(target_id)
                graph.add_node(_node(target_id, "FORMAL_TARGET", theorem, theorem_name=theorem,
                                     configuration=config_id, target_ordinal=ordinal,
                                     kernel_verification_status="UNTESTED", correspondence_status="UNREVIEWED"))
                graph.add_edge(_edge("SELECTS_FORMAL_TARGET", config_id, target_id))
                solution_path = "lean/" + config["solution_module"].replace(".", "/") + ".lean"
                target_lookups[solution_path][theorem].append(target_id)
        for index, result in enumerate(main_results):
            config_path = "lean/" + result["comparator_config"]
            result_path = "lean/" + result["file"]
            if config_path not in config_ids or result_path not in paths:
                raise ValueError("formalization catalogue has unresolved file/configuration")
            result_id = prefix + ":catalogue-result:" + str(index)
            graph.add_node(_node(result_id, "FORMAL_CATALOGUE_RECORD", result["declaration"],
                                 theorem_name=result["declaration"], upstream_scope=formalization["status"].get("scope"),
                                 upstream_review_status=formalization.get("review", {}).get("status"),
                                 source_resource=_resource_id(prefix, "lean/formalization.yaml"), catalogue_ordinal=index))
            graph.add_edge(_edge("SOURCE_DOCUMENTS", result_id, config_ids[config_path]))
            graph.add_edge(_edge("SOURCE_DOCUMENTS", result_id, _resource_id(prefix, result_path)))
        for path in scopes:
            family = PurePosixPath(path).stem
            if family not in family_ids:
                raise ValueError(f"scope note has no catalogue family: {path}")
            graph.add_edge(_edge("HAS_SCOPE_DOCUMENT", prefix + ":family:" + family, _resource_id(prefix, path),
                                 scope_correspondence_status="UPSTREAM_DESCRIPTION"))

        for index, entry in enumerate(entries, start=1):
            path = entry["path"]
            raw = source_bytes(source_repo, entry)
            content_hash = hashlib.sha256(raw).hexdigest()
            resource_id = _resource_id(prefix, path)
            scan = scan_source(path, raw)
            disposition = scan["disposition"]
            dispositions[disposition] += 1
            record_meta = {**entry, "sha256": content_hash, "disposition": disposition,
                           "lexical_records": len(scan["records"]), "references": len(scan["references"]),
                           "diagnostic_codes": sorted({item["code"] for item in scan["diagnostics"]})}
            resource_manifest.append(record_meta)
            inventory_digest.update(canonical_bytes(record_meta) + b"\n")
            graph.add_node(_node(resource_id, "SOURCE_RESOURCE", path,
                                 path=path, git_blob_sha=entry["sha"], sha256=content_hash,
                                 size_bytes=entry["size"], mode=entry["mode"], repository_revision=revision,
                                 locator=pin["url"] + "/blob/" + revision + "/" + path,
                                 format=PurePosixPath(path).suffix.lower(), extraction_disposition=disposition,
                                 lexical_record_count=len(scan["records"]), source_integrity_status="HASH_VERIFIED"))
            graph.add_edge(_edge("HAS_SOURCE_RESOURCE", repo_id, resource_id))
            components = path.split("/")
            if len(components) >= 3 and components[0] == "preprints" and components[1] in paper_dirs:
                graph.add_edge(_edge("HAS_SOURCE_RESOURCE", prefix + ":manuscript:" + "/".join(components[:2]), resource_id))
            record_ids = {}
            for ordinal, record in enumerate(scan["records"]):
                start, end = record["start_byte"], record["end_byte"]
                if not 0 <= start <= end <= len(raw):
                    raise ValueError(f"invalid source record byte span: {path}")
                if hashlib.sha256(raw[start:end]).hexdigest() != record["span_sha256"]:
                    raise ValueError(f"source record span hash mismatch: {path}")
                record_id = resource_id + ":record:" + str(start) + ":" + str(ordinal)
                record_ids[start] = record_id
                counts[record["kind"]] += 1
                graph.add_node(_node(record_id, "SOURCE_RECORD", record["name"],
                                     **record, source_resource=resource_id, source_sha256=content_hash,
                                     context_sha256=content_hash, extraction_status="LEXICAL_CANDIDATE",
                                     hypothesis_interpretation_status="UNRESOLVED",
                                     semantic_alignment_status="UNRESOLVED", kernel_verification_status="UNTESTED"))
                graph.add_edge(_edge("CONTAINS_SOURCE_RECORD", resource_id, record_id))
                qualified = record.get("qualified_name")
                if qualified in target_lookups.get(path, {}):
                    for target_id in target_lookups[path][qualified]:
                        graph.add_edge(_edge("LEXICALLY_MATCHES_TARGET", target_id, record_id,
                                             match_status="LEXICAL_NAME_ONLY", correspondence_status="UNREVIEWED"))
                        target_matches[target_id] += 1
            for ordinal, reference in enumerate(scan["references"]):
                resolved, status = _resolve_reference(path, reference, paths)
                reference_counts[status] += 1
                source_id = record_ids.get(reference.get("record_start_byte"), resource_id)
                attrs = {"reference_kind": reference["kind"], "start_line": reference["start_line"],
                         "reference_ordinal": ordinal, "resolution_status": status}
                if resolved:
                    graph.add_edge(_edge("SOURCE_REFERENCE", source_id, _resource_id(prefix, resolved), **attrs))
                else:
                    reference_id = resource_id + ":reference:" + str(ordinal)
                    graph.add_node(_node(reference_id, "SOURCE_REFERENCE_RECORD", reference["target"],
                                         target_identifier=reference["target"], source_resource=resource_id,
                                         **attrs, status="UNRESOLVED", deficit_kind="UNRESOLVED_DEFICIT",
                                         semantic_dependency_status="NOT_ESTABLISHED"))
                    graph.add_edge(_edge("HAS_UNRESOLVED_REFERENCE", source_id, reference_id,
                                         status="UNRESOLVED", **attrs))
            for ordinal, diagnostic in enumerate(scan["diagnostics"]):
                diagnostics[diagnostic["code"]] += 1
                diagnostic_id = resource_id + ":diagnostic:" + str(ordinal)
                graph.add_node(_node(diagnostic_id, "UNRESOLVED_DEFICIT", diagnostic["code"],
                                     **diagnostic, source_resource=resource_id, status="UNRESOLVED"))
                graph.add_edge(_edge("HAS_WOUND", resource_id, diagnostic_id, status="UNRESOLVED"))
            if index % 5000 == 0:
                print(f"Scanned {index:,}/{len(entries):,} files; {sum(counts.values()):,} lexical records", flush=True)
        for target_id in target_ids:
            if target_matches[target_id] != 1:
                reason = "LEXICAL_TARGET_NOT_UNIQUELY_RESOLVED"
                deficit_id = target_id + ":resolution-deficit"
                graph.add_node(_node(deficit_id, "UNRESOLVED_DEFICIT", reason,
                                     status="UNRESOLVED", lexical_matches=target_matches[target_id],
                                     deficit_kind=reason, requires="LEAN_ELABORATION_AND_STATEMENT_REVIEW"))
                graph.add_edge(_edge("HAS_WOUND", target_id, deficit_id, status="UNRESOLVED"))
        print(f"All source files scanned; checking {graph.edges_count:,} edge endpoints and sealing output", flush=True)
    manifest = {"source": metadata, "inventory_sha256": inventory_digest.hexdigest(),
                "resources": resource_manifest}
    manifest_path = out_dir / "source_manifest.json.gz"
    atomic_write_deterministic_json_gzip(manifest_path, manifest)
    report = {
        "status": "PASS", "scope": "COMPLETE_REPOSITORY_SOURCE_INTAKE",
        "source": metadata, "coverage": observed,
        "graph": {"nodes": graph.nodes_count, "edges": graph.edges_count,
                  "node_types": dict(sorted(graph.node_types.items())), "edge_types": dict(sorted(graph.edge_types.items())),
                  "nodes_payload_sha256": graph.node_digest.hexdigest(), "edges_payload_sha256": graph.edge_digest.hexdigest(),
                  "sha256": sha256_file(graph_path), "size_bytes": graph_path.stat().st_size},
        "base": {"nodes": len(base["nodes"]), "edges": len(base["edges"]), "sha256": base_hash,
                 "preservation": "EXACT_NODE_AND_EDGE_PAYLOADS"},
        "extraction": {"lexical_records": sum(counts.values()), "records_by_kind": dict(sorted(counts.items())),
                       "resource_dispositions": dict(sorted(dispositions.items())), "diagnostics": dict(sorted(diagnostics.items())),
                       "reference_resolutions": dict(sorted(reference_counts.items())),
                       "unique_lexical_target_matches": sum(target_matches[target_id] == 1 for target_id in target_ids)},
        "source_manifest": {"sha256": sha256_file(manifest_path), "inventory_sha256": inventory_digest.hexdigest()},
        "verification": {"all_tracked_source_bytes_match_git_blobs": True,
                         "all_edge_endpoints_exist": True, "unique_node_and_edge_ids": True,
                         "no_source_prose_persisted": True, "new_kernel_certificates": 0,
                         "new_semantic_equivalence_edges": 0, "lean_checker_runs": 0,
                         "upstream_formalization_review": formalization.get("review", {}).get("status"),
                         "formal_semantic_extraction": "NOT_ELABORATED",
                         "canonical_reconciliation": "UNRESOLVED_PER_SOURCE_RECORD"},
    }
    _write_json(out_dir / "intake_report.json", report)
    print(json.dumps({"status": report["status"], "coverage": observed,
                      "nodes": graph.nodes_count, "edges": graph.edges_count,
                      "lexical_records": sum(counts.values()), "graph_sha256": report["graph"]["sha256"]}, indent=2), flush=True)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--base-graph", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        run_intake(args.source_repo, args.base_graph, args.out_dir)
    except (ValueError, OSError, KeyError) as error:
        print(f"OpenAI mathematics intake failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
