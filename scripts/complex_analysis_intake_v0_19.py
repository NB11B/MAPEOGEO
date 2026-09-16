#!/usr/bin/env python3
"""MAPEOGEO v0.19 Complex Analysis, Several Complex Variables & Riemann Surfaces Expansion Runner.

Mathematics Expansion across Gallier (S_A), Axler (S_B), VMLS (S_C), CVX (S_D), Billingsley (S_E), Lee (S_F),
and Ahlfors/Krantz/Conway (S_G) establishing the connective complex-analytic, harmonic, conformal, several complex
variables, and Riemann surface foundation bridging Holomorphic Functions, Cauchy Theory, Residues, Conformal Mappings,
Hartogs Extension, Dolbeault Complex, and the Riemann-Roch Theorem.

Dashboard Metrics:
- N_source_total: Total source declarations across S_A, S_B, S_C, S_D, S_E, S_F, S_G (disjoint partition)
- N_section_anchors_total: Total section anchors (segregated from source declarations)
- N_canonical_total: Total canonical mathematical objects
- N_2_source_bridges, N_3_source_bridges, N_4_source_bridges, N_5_source_bridges, N_6_source_bridges, N_7_source_bridges
- D_domains_count, domains_list: Distinct mathematical domains (8 domains)
- representation_diversity: Average representation richness r_bar across 6 modalities
- edges_summary: Exact typed semantic bridge counts (SAME_SEMANTICS, SCOPED_OVERLAP, RELATED_TO)
"""

from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import gzip
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.import_complex_analysis_v0_19 import (
    FORBIDDEN_PERSISTED_KEYS,
    ComplexAnalysisDeclaration,
    build_complex_declarations,
    validate_complex_declarations,
)

STAGE = "v0.19"
GALLIER_SOURCE_ID = "GALLIER_QUAINTANCE_2020"
LEGACY_GALLIER_SOURCE_ID = "GALLIER_QUAINTANCE_MATH_DEEP"
AXLER_SOURCE_ID = "AXLER_LADR4E_2026_08_16"
VMLS_SOURCE_ID = "BOYD_VANDENBERGHE_VMLS_2018"
CVX_SOURCE_ID = "BOYD_VANDENBERGHE_CVX_2004"
BILLINGSLEY_SOURCE_ID = "BILLINGSLEY_PROB_MEASURE_1995"
LEE_SOURCE_ID = "LEE_SMOOTH_MANIFOLDS_2013"
AHLFORS_SOURCE_ID = "AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979"
FOUNDATION_SOURCE_ID = "FOUNDATION_MATHEMATICS_BASE"
SEALED_V019_ALIGNMENT_SHA256 = "ae2169f7edc3012d92c96c90c5d2707f5f08c62c89002287e90ce44a0e23f2c8"
SEALED_V019_ALIGNMENT_PATH = ROOT / "formal" / "cross_source_alignments_v0_19.json"
DEFAULT_AMENDMENTS_PATH = ROOT / "formal" / "mathematical_integrity_amendments_v0_20.json"
SEALED_V019_EVIDENCE_PATH = ROOT / "evidence" / "v0_19_scientific_results.json"

VALID_SOURCE_IDS = {
    GALLIER_SOURCE_ID,
    AXLER_SOURCE_ID,
    VMLS_SOURCE_ID,
    CVX_SOURCE_ID,
    BILLINGSLEY_SOURCE_ID,
    LEE_SOURCE_ID,
    AHLFORS_SOURCE_ID,
    FOUNDATION_SOURCE_ID,
}

VALID_ALIGNMENT_STATUSES = {
    "CROSS_SOURCE_SAME",
    "CROSS_SOURCE_SCOPED_OVERLAP",
    "CROSS_SOURCE_RELATED_NOT_SAME",
    "UNRESOLVED",
}

SOURCE_ID_TO_CORPUS = {
    GALLIER_SOURCE_ID: "GALLIER",
    AXLER_SOURCE_ID: "AXLER",
    VMLS_SOURCE_ID: "VMLS",
    CVX_SOURCE_ID: "CVX",
    BILLINGSLEY_SOURCE_ID: "BILLINGSLEY",
    LEE_SOURCE_ID: "LEE",
    AHLFORS_SOURCE_ID: "AHLFORS",
    FOUNDATION_SOURCE_ID: "FOUNDATION",
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RELATION_STRENGTH = {
    "RELATED_TO": 0,
    "SCOPED_OVERLAP": 1,
    "SAME_SEMANTICS": 2,
}


def _register_source_record(
    registry: dict[str, dict[str, str]],
    *,
    node_id: str,
    source_id: str,
    corpus: str,
    statement_sha256: str,
    count_status: str = "ADMISSIBLE_SOURCE_DECLARATION",
) -> None:
    if not _SHA256_RE.fullmatch(statement_sha256):
        raise ValueError(f"invalid authoritative statement_sha256 for {node_id}")
    record = {
        "source_id": source_id,
        "corpus": corpus,
        "statement_sha256": statement_sha256,
        "count_status": count_status,
    }
    previous = registry.get(node_id)
    if previous is not None and previous != record:
        raise ValueError(f"conflicting authoritative source identity: {node_id}")
    registry[node_id] = record


@lru_cache(maxsize=1)
def authoritative_source_registry() -> dict[str, dict[str, str]]:
    """Return exact source/corpus/hash identities from sealed or curated registries."""
    from scripts.import_analysis_v0_15 import generate_additional_analysis_declarations
    from scripts.import_billingsley_v0_17 import generate_billingsley_declarations
    from scripts.import_diffgeom_v0_18 import generate_diffgeom_declarations
    from scripts.import_topology_v0_16 import generate_supplementary_topology_anchors

    registry: dict[str, dict[str, str]] = {}
    with gzip.open(ROOT / "data" / "mapeogeo_v0_11_graph.json.gz", "rt", encoding="utf-8") as handle:
        sealed_graph = json.load(handle)
    for node in sealed_graph.get("nodes", []):
        if node.get("type") != "STATEMENT":
            continue
        attrs = node.get("attributes", {})
        digest = attrs.get("independent_profile", {}).get("statement_sha256")
        if isinstance(digest, str):
            _register_source_record(
                registry,
                node_id=node["id"],
                source_id=GALLIER_SOURCE_ID,
                corpus="GALLIER",
                statement_sha256=digest,
            )

    for manifest_name, expected_source, corpus in (
        ("axler_declarations_manifest.json", AXLER_SOURCE_ID, "AXLER"),
        ("vmls_declarations_manifest.json", VMLS_SOURCE_ID, "VMLS"),
        ("cvx_declarations_manifest.json", CVX_SOURCE_ID, "CVX"),
    ):
        entries = json.loads((ROOT / "formal" / manifest_name).read_text(encoding="utf-8"))
        for item in entries:
            if item.get("source_id") != expected_source:
                raise ValueError(f"authoritative source mismatch in {manifest_name}")
            _register_source_record(
                registry,
                node_id=item["node_id"],
                source_id=expected_source,
                corpus=corpus,
                statement_sha256=item["statement_sha256"],
            )

    for item in generate_additional_analysis_declarations():
        _register_source_record(
            registry,
            node_id=item.node_id,
            source_id=item.source_id,
            corpus=SOURCE_ID_TO_CORPUS[item.source_id],
            statement_sha256=item.statement_sha256,
            count_status=(
                "EXCLUDED_HISTORICAL_COUNT_ARTIFACT"
                if item.source_id == GALLIER_SOURCE_ID
                else "ADMISSIBLE_SOURCE_DECLARATION"
            ),
        )

    for declarations, source_id, corpus in (
        (generate_billingsley_declarations(), BILLINGSLEY_SOURCE_ID, "BILLINGSLEY"),
        (generate_diffgeom_declarations(), LEE_SOURCE_ID, "LEE"),
        (build_complex_declarations(), AHLFORS_SOURCE_ID, "AHLFORS"),
    ):
        for item in declarations:
            item_source = item.source_id if source_id is None else source_id
            item_corpus = SOURCE_ID_TO_CORPUS[item_source] if corpus is None else corpus
            _register_source_record(
                registry,
                node_id=item.node_id,
                source_id=item_source,
                corpus=item_corpus,
                statement_sha256=item.statement_sha256,
            )
    for item in generate_supplementary_topology_anchors():
        _register_source_record(
            registry,
            node_id=item.node_id,
            source_id=item.source_id,
            corpus=SOURCE_ID_TO_CORPUS[item.source_id],
            statement_sha256=item.statement_sha256,
            count_status="SECTION_ANCHOR",
        )
    return registry


def _identity_sha256(identity: dict[str, Any]) -> str:
    payload = {key: value for key, value in identity.items() if key != "identity_sha256"}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _derived_relation(a: dict[str, Any], b: dict[str, Any]) -> str:
    if a["status"] == "CROSS_SOURCE_SAME" and b["status"] == "CROSS_SOURCE_SAME":
        return "SAME_SEMANTICS"
    if "CROSS_SOURCE_SCOPED_OVERLAP" in (a["status"], b["status"]):
        return "SCOPED_OVERLAP"
    return "RELATED_TO"


def _contextual_pair_relations(
    canonical_objects: list[dict[str, Any]],
) -> dict[tuple[str, str], list[dict[str, str]]]:
    relations: dict[tuple[str, str], list[dict[str, str]]] = {}
    for canonical in canonical_objects:
        alignments = canonical.get("alignments", [])
        for index, left in enumerate(alignments):
            for right in alignments[index + 1 :]:
                if left.get("corpus") == right.get("corpus"):
                    continue
                pair = tuple(sorted((left["source"], right["source"])))
                relations.setdefault(pair, []).append(
                    {
                        "canonical_id": canonical["id"],
                        "relation": _derived_relation(left, right),
                    }
                )
    return relations


def load_active_alignment_projection(
    sealed_path: Path = SEALED_V019_ALIGNMENT_PATH,
    amendments_path: Path = DEFAULT_AMENDMENTS_PATH,
) -> dict[str, Any]:
    """Project immutable v0.19 history into the amended v0.20 active view."""
    sealed_bytes = sealed_path.read_bytes()
    actual_digest = hashlib.sha256(sealed_bytes).hexdigest()
    if actual_digest != SEALED_V019_ALIGNMENT_SHA256:
        raise ValueError(
            "sealed v0.19 alignment digest mismatch: "
            f"expected {SEALED_V019_ALIGNMENT_SHA256}, got {actual_digest}"
        )
    projection = copy.deepcopy(json.loads(sealed_bytes.decode("utf-8")))
    manifest = json.loads(amendments_path.read_text(encoding="utf-8"))
    amendments = manifest.get("amendments", [])
    for amendment in amendments:
        for key in ("historical_identity", "corrected_identity"):
            identity = amendment.get(key, {})
            if identity.get("identity_sha256") != _identity_sha256(identity):
                raise ValueError(f"invalid amendment identity hash: {amendment.get('amendment_id')}")

    registry = authoritative_source_registry()
    for amendment in amendments:
        corrected = amendment.get("corrected_identity", {})
        if corrected.get("kind") == "SOURCE_STATEMENT":
            subject_id = corrected.get("subject_id")
            if (
                subject_id not in registry
                or corrected.get("statement_sha256")
                != registry[subject_id]["statement_sha256"]
            ):
                raise ValueError(
                    f"statement amendment is not source-hash-bound: {amendment.get('amendment_id')}"
                )
    false_source = "srcdecl:axler:definition:5_8"
    false_canonical = "canonical:complex:liouville_and_fundamental_theorem_algebra"
    false_amendment = next(
        (
            item for item in amendments
            if item.get("amendment_id") == "amendment:v0.20:complex:axler-eigenvector-alignment"
        ),
        None,
    )
    if false_amendment is None or false_amendment.get("status") != "REJECTED":
        raise ValueError("missing rejected Axler alignment amendment")
    historical = false_amendment["historical_identity"]
    if (
        historical.get("source_id") != false_source
        or historical.get("canonical_id") != false_canonical
        or historical.get("source_statement_sha256")
        != registry[false_source]["statement_sha256"]
    ):
        raise ValueError("Axler alignment amendment is not source-hash-bound")

    duplicate_amendment = next(
        (
            item for item in amendments
            if item.get("amendment_id")
            == "amendment:v0.20:complex:duplicate-axler-6-55-alignment"
        ),
        None,
    )
    duplicate_source = "srcdecl:axler:definition:6_55"
    if duplicate_amendment is None:
        raise ValueError("missing duplicate Axler alignment amendment")
    duplicate_old = duplicate_amendment.get("historical_identity", {})
    duplicate_new = duplicate_amendment.get("corrected_identity", {})
    if (
        duplicate_old.get("source_id") != duplicate_source
        or duplicate_old.get("source_statement_sha256")
        != registry[duplicate_source]["statement_sha256"]
        or duplicate_new.get("source_statement_sha256")
        != registry[duplicate_source]["statement_sha256"]
        or duplicate_old.get("occurrence_count") != 2
        or duplicate_new.get("occurrence_count") != 1
    ):
        raise ValueError("duplicate alignment amendment is not source-hash-bound")

    conflict_amendment = next(
        (
            item for item in amendments
            if item.get("amendment_id")
            == "amendment:v0.20:complex:global-relation-meet"
        ),
        None,
    )
    if (
        conflict_amendment is None
        or conflict_amendment.get("historical_identity", {}).get("conflicting_pair_count") != 33
        or conflict_amendment.get("corrected_identity", {}).get("conflicting_pair_count") != 33
        or conflict_amendment.get("corrected_identity", {}).get("ordering")
        != ["RELATED_TO", "SCOPED_OVERLAP", "SAME_SEMANTICS"]
    ):
        raise ValueError("invalid global relation-meet amendment")

    dolbeault_amendment = next(
        (
            item for item in amendments
            if item.get("amendment_id") == "amendment:v0.20:complex:dolbeault-reference"
        ),
        None,
    )
    dolbeault_subject = f"decl:{AHLFORS_SOURCE_ID}:DEFINITION:9.4"
    dolbeault_target = f"decl:{AHLFORS_SOURCE_ID}:THEOREM:2.2"
    if dolbeault_amendment is None:
        raise ValueError("missing Dolbeault reference amendment")
    dolbeault_old = dolbeault_amendment.get("historical_identity", {})
    dolbeault_new = dolbeault_amendment.get("corrected_identity", {})
    if (
        dolbeault_old.get("subject_statement_sha256")
        != registry[dolbeault_subject]["statement_sha256"]
        or dolbeault_new.get("subject_statement_sha256")
        != registry[dolbeault_subject]["statement_sha256"]
        or dolbeault_new.get("structural_reference") != dolbeault_target
        or dolbeault_new.get("target_statement_sha256")
        != registry[dolbeault_target]["statement_sha256"]
    ):
        raise ValueError("Dolbeault amendment is not source-hash-bound")

    wounds: list[dict[str, Any]] = []
    removed_false = 0
    duplicate_count = 0
    for canonical in projection.get("canonical_objects", []):
        active: list[dict[str, Any]] = []
        seen_sources: set[str] = set()
        for alignment in canonical.get("alignments", []):
            if canonical["id"] == false_canonical and alignment.get("source") == false_source:
                removed_false += 1
                wounds.append(
                    {
                        "kind": "REJECTED_FALSE_ALIGNMENT",
                        "canonical_id": canonical["id"],
                        "source_id": false_source,
                        "source_statement_sha256": registry[false_source]["statement_sha256"],
                        "amendment_id": false_amendment["amendment_id"],
                    }
                )
                continue
            source = alignment.get("source")
            if source in seen_sources:
                duplicate_count += 1
                wounds.append(
                    {
                        "kind": "DUPLICATE_ALIGNMENT",
                        "canonical_id": canonical["id"],
                        "source_id": source,
                        "source_statement_sha256": registry[source]["statement_sha256"],
                    }
                )
                continue
            seen_sources.add(source)
            active.append(alignment)
        canonical["alignments"] = active
    if removed_false != 1 or duplicate_count != 1:
        raise ValueError(
            f"unexpected historical alignment defects: false={removed_false}, duplicates={duplicate_count}"
        )

    overrides: list[dict[str, Any]] = []
    for pair, contexts in sorted(_contextual_pair_relations(projection["canonical_objects"]).items()):
        observed = {item["relation"] for item in contexts}
        if len(observed) <= 1:
            continue
        meet = min(observed, key=RELATION_STRENGTH.__getitem__)
        record = {
            "endpoints": list(pair),
            "contextual_relations": contexts,
            "emitted_relation": meet,
        }
        overrides.append(record)
        wounds.append({"kind": "RELATION_CONFLICT_DOWNGRADED", **record})
    if len(overrides) != 33:
        raise ValueError(f"unexpected cross-canonical conflict count: {len(overrides)}")

    projection["schema_version"] = "v0.20-active-alignment-projection"
    projection["sealed_source_sha256"] = actual_digest
    projection["active_relation_overrides"] = overrides
    projection["integrity_wounds"] = wounds
    return projection


def bridge_edge_id(canonical_id: str, edge_type: str, source_a: str, source_b: str) -> str:
    """Return a deterministic identifier for one scoped semantic contract.

    Sorting the endpoints makes the identity independent of iteration order.  Including
    both the canonical object and relation type prevents a relation in one mathematical
    context from silently overwriting a different relation for the same endpoints.
    """

    contract = {
        "canonical_id": canonical_id,
        "edge_type": edge_type,
        "endpoints": sorted((source_a, source_b)),
    }
    encoded = json.dumps(
        contract,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"e:bridge:contract:{hashlib.sha256(encoded).hexdigest()}"


def represents_edge_id(
    canonical_id: str,
    source_id: str,
    canonical_contract_sha256: str,
) -> str:
    """Return a deterministic identifier for one source-to-contract assertion.

    Historical stages used only the endpoints in ``REPRESENTS`` identifiers, so a
    later canonical-contract revision reused the same identifier for a different
    evidence payload.  Binding the active identifier to the canonical contract
    keeps historical assertions visible without allowing payload collisions.
    """
    if not _SHA256_RE.fullmatch(canonical_contract_sha256):
        raise ValueError("invalid canonical contract digest for REPRESENTS edge")
    contract = {
        "canonical_contract_sha256": canonical_contract_sha256,
        "canonical_id": canonical_id,
        "source_id": source_id,
    }
    encoded = json.dumps(
        contract,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"e:rep:contract:{hashlib.sha256(encoded).hexdigest()}"


def _canonical_contract_sha256(canonical: dict[str, Any]) -> str:
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_binding(node: dict[str, Any]) -> tuple[str, str, str]:
    """Return the registered source identity, corpus, and exact statement hash."""
    attributes = node.get("attributes", {})
    bound_source_id = attributes.get("source_id")
    statement_sha256 = attributes.get("statement_sha256")
    if node.get("type") == "STATEMENT" and attributes.get("source") == LEGACY_GALLIER_SOURCE_ID:
        bound_source_id = GALLIER_SOURCE_ID
        segment_sha256 = attributes.get("source_segment_sha256")
        statement_sha256 = attributes.get("independent_profile", {}).get("statement_sha256")
        if not isinstance(segment_sha256, str) or not _SHA256_RE.fullmatch(segment_sha256):
            raise ValueError(f"invalid source_segment_sha256 for {node.get('id')}")
    if bound_source_id not in VALID_SOURCE_IDS:
        raise ValueError(f"invalid source identity for alignment endpoint {node.get('id')}")
    corpus = SOURCE_ID_TO_CORPUS[bound_source_id]
    stored_corpus = attributes.get("corpus")
    if stored_corpus is not None and stored_corpus != corpus:
        raise ValueError(
            f"corpus mismatch for {node.get('id')}: node={stored_corpus!r}, source identity={corpus!r}"
        )
    if not isinstance(statement_sha256, str) or not _SHA256_RE.fullmatch(statement_sha256):
        raise ValueError(f"invalid statement_sha256 for alignment endpoint {node.get('id')}")
    authoritative = authoritative_source_registry().get(node.get("id"))
    if authoritative is None:
        raise ValueError(
            f"alignment endpoint is absent from authoritative source registry: {node.get('id')}"
        )
    if (
        authoritative["source_id"] != bound_source_id
        or authoritative["corpus"] != corpus
        or authoritative["statement_sha256"] != statement_sha256
    ):
        raise ValueError(
            f"authoritative source/statement_sha256 mismatch for {node.get('id')}"
        )
    return bound_source_id, corpus, statement_sha256


def partition_v0_19_source_declarations(
    nodes: list[dict[str, Any]],
) -> dict[str, int]:
    """Count admissible declarations only through the authoritative registry."""
    count_key = {
        "FOUNDATION": "S_0_foundation",
        "GALLIER": "S_A_gallier",
        "AXLER": "S_B_axler",
        "VMLS": "S_C_vmls",
        "CVX": "S_D_cvx",
        "BILLINGSLEY": "S_E_billingsley",
        "LEE": "S_F_lee",
        "AHLFORS": "S_G_ahlfors",
    }
    counts = {key: 0 for key in count_key.values()}
    for node in nodes:
        if node.get("type") not in {"SOURCE_DECLARATION", "STATEMENT"}:
            raise ValueError(f"partition member is not a source declaration: {node.get('id')}")
        _source_id, corpus, _digest = _source_binding(node)
        count_status = authoritative_source_registry()[node["id"]]["count_status"]
        if count_status == "EXCLUDED_HISTORICAL_COUNT_ARTIFACT":
            continue
        if count_status != "ADMISSIBLE_SOURCE_DECLARATION":
            raise ValueError(
                f"non-declaration registry record in source partition: {node.get('id')}"
            )
        try:
            counts[count_key[corpus]] += 1
        except KeyError as exc:
            raise ValueError(f"unregistered source corpus: {corpus}") from exc
    return counts


def validate_alignment_contracts(graph: dict[str, Any], alignments_data: dict[str, Any]) -> None:
    """Validate source-bound alignment contracts without trusting names or prefixes."""

    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("alignment graph must contain a nodes list")

    by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            raise ValueError("graph node is missing a stable identity")
        if node_id in by_id:
            raise ValueError(f"duplicate graph node identity: {node_id}")
        by_id[node_id] = node

    canonical_objects = alignments_data.get("canonical_objects")
    if not isinstance(canonical_objects, list):
        raise ValueError("alignment document must contain canonical_objects")

    seen_canonical: set[str] = set()
    for canonical in canonical_objects:
        canonical_id = canonical.get("id")
        if not isinstance(canonical_id, str) or not canonical_id.startswith("canonical:"):
            raise ValueError(f"invalid canonical identity: {canonical_id!r}")
        if canonical_id in seen_canonical:
            raise ValueError(f"duplicate canonical identity: {canonical_id}")
        seen_canonical.add(canonical_id)
        if not canonical.get("name") or not canonical.get("domain"):
            raise ValueError(f"incomplete canonical contract: {canonical_id}")

        alignments = canonical.get("alignments")
        if not isinstance(alignments, list) or not alignments:
            raise ValueError(f"canonical contract has no alignments: {canonical_id}")

        seen_sources: dict[str, tuple[str, str]] = {}
        for alignment in alignments:
            source_id = alignment.get("source")
            corpus = alignment.get("corpus")
            status = alignment.get("status")
            if status not in VALID_ALIGNMENT_STATUSES:
                raise ValueError(f"invalid alignment status in {canonical_id}: {status!r}")
            if source_id in seen_sources:
                previous = seen_sources[source_id]
                current = (corpus, status)
                if previous != current:
                    raise ValueError(
                        "conflicting alignment contract for endpoint "
                        f"{source_id} in {canonical_id}: {previous!r} versus {current!r}"
                    )
                raise ValueError(f"duplicate alignment endpoint {source_id} in {canonical_id}")
            seen_sources[source_id] = (corpus, status)

            node = by_id.get(source_id)
            if node is None:
                raise ValueError(
                    "Fail-closed provenance error: Source declaration "
                    f"'{source_id}' referenced in canonical object '{canonical_id}' "
                    f"({corpus}) is not present in graph!"
                )
            if node.get("type") not in {
                "SOURCE_DECLARATION",
                "SOURCE_SECTION_ANCHOR",
                "STATEMENT",
            }:
                raise ValueError(
                    f"alignment endpoint is not a source declaration or section anchor: {source_id}"
                )

            _bound_source_id, expected_corpus, _statement_sha256 = _source_binding(node)
            if corpus != expected_corpus:
                raise ValueError(
                    f"corpus mismatch for {source_id}: contract={corpus!r}, "
                    f"source identity={expected_corpus!r}"
                )

    contextual = _contextual_pair_relations(canonical_objects)
    conflicts = {
        pair: contexts
        for pair, contexts in contextual.items()
        if len({item["relation"] for item in contexts}) > 1
    }
    override_records = alignments_data.get("active_relation_overrides", [])
    if not isinstance(override_records, list):
        raise ValueError("active_relation_overrides must be a list")
    overrides: dict[tuple[str, str], dict[str, Any]] = {}
    for record in override_records:
        endpoints = record.get("endpoints")
        if not isinstance(endpoints, list) or len(endpoints) != 2:
            raise ValueError("invalid active relation override endpoints")
        pair = tuple(sorted(endpoints))
        if pair in overrides:
            raise ValueError(f"duplicate active relation override: {pair}")
        overrides[pair] = record
    for pair, contexts in conflicts.items():
        record = overrides.get(pair)
        if record is None:
            raise ValueError(f"cross-canonical relation conflict without projection: {pair}")
        observed = {item["relation"] for item in contexts}
        meet = min(observed, key=RELATION_STRENGTH.__getitem__)
        if record.get("emitted_relation") != meet or record.get("contextual_relations") != contexts:
            raise ValueError(f"invalid conservative relation meet for {pair}")
    if set(overrides) != set(conflicts):
        raise ValueError("active relation overrides do not exactly match conflicts")


def load_json_or_gz(path: Path) -> dict[str, Any]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_v0_19_evidence_path(out_dir: Path, requested: Path | None) -> Path:
    path = requested or (out_dir / "v0_20_active_scientific_results.json")
    if path.resolve() == SEALED_V019_EVIDENCE_PATH.resolve():
        raise ValueError("refusing to overwrite sealed v0.19 evidence")
    return path


def save_graph_gz(graph: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    for node in graph.get("nodes", []):
        attrs = node.get("attributes", {})
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            if forbidden in node or forbidden in attrs:
                raise ValueError(f"Zero-prose violation in node {node.get('id')}: found key '{forbidden}'")

    payload = (
        json.dumps(
            graph,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b",
            prefix=f".{out_path.name}.",
            suffix=".tmp",
            dir=out_path.parent,
            delete=False,
        ) as raw:
            temporary_path = Path(raw.name)
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                compressed.write(payload)
            raw.flush()
            os.fsync(raw.fileno())
        os.replace(temporary_path, out_path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def add_node(nodes: list[dict], by_id: dict[str, dict], node: dict) -> bool:
    nid = node["id"]
    if nid not in by_id:
        nodes.append(node)
        by_id[nid] = node
        return True
    else:
        existing = by_id[nid]
        if "attributes" in node:
            existing.setdefault("attributes", {}).update(node["attributes"])
        return False


def add_edge(edges: list[dict], edge_ids: set[str], edge: dict) -> bool:
    eid = edge["id"]
    if eid not in edge_ids:
        edges.append(edge)
        edge_ids.add(eid)
        return True
    existing = next((item for item in edges if item.get("id") == eid), None)
    if existing != edge:
        raise ValueError(f"edge ID collision with different payload: {eid}")
    return False


def ingest_complex_declarations(
    graph: dict[str, Any],
    declarations: list[ComplexAnalysisDeclaration],
) -> dict[str, Any]:
    validate_complex_declarations(declarations)
    nodes: list[dict] = graph.setdefault("nodes", [])
    edges: list[dict] = graph.setdefault("edges", [])
    by_id = {n["id"]: n for n in nodes}
    edge_ids = {e["id"] for e in edges if "id" in e}

    for decl in declarations:
        node_dict = {
            "id": decl.node_id,
            "type": "SOURCE_DECLARATION",
            "label": decl.label,
            "attributes": {
                "source_id": decl.source_id,
                "corpus": "AHLFORS",
                "decl_type": decl.decl_type,
                "chapter_section": decl.chapter_section,
                "page": decl.page,
                "statement_sha256": decl.statement_sha256,
                "statement_chars": decl.char_count,
                "direct_status": decl.representation_profile.get("direct_status", "THEORETIC_DIRECT"),
                "eo_tags": decl.representation_profile.get("eo_tags", []),
                "geo_tags": decl.representation_profile.get("geo_tags", []),
                "representation_kinds": decl.representation_profile.get("representation_kinds", []),
                "diversity_count": len(decl.representation_profile.get("representation_kinds", [])),
                "stage": STAGE,
            },
        }
        add_node(nodes, by_id, node_dict)

        # Structural references
        for target_id in decl.structural_refs:
            edge_id = f"e:dep:{decl.node_id}:{target_id}"
            add_edge(
                edges,
                edge_ids,
                {
                    "id": edge_id,
                    "type": "PROOF_DEPENDENCY",
                    "source": decl.node_id,
                    "target": target_id,
                    "attributes": {
                        "dep_type": "STRUCTURAL_REFERENCE",
                        "dependency_status": "DECLARED_NOT_KERNEL_VERIFIED",
                        "source_statement_sha256": decl.statement_sha256,
                        "target_statement_sha256": by_id[target_id]["attributes"]["statement_sha256"],
                        "stage": STAGE,
                    },
                },
            )

    return graph


def ingest_v0_19_canonical_alignments(
    graph: dict[str, Any],
    alignments_path: Path,
    amendments_path: Path = DEFAULT_AMENDMENTS_PATH,
) -> dict[str, Any]:
    nodes: list[dict] = graph.setdefault("nodes", [])
    edges: list[dict] = graph.setdefault("edges", [])
    by_id = {n["id"]: n for n in nodes}
    edge_ids = {e["id"] for e in edges if "id" in e}

    if alignments_path.resolve() == SEALED_V019_ALIGNMENT_PATH.resolve():
        alignments_data = load_active_alignment_projection(
            alignments_path,
            amendments_path,
        )
    else:
        alignments_data = json.loads(alignments_path.read_text(encoding="utf-8"))
    validate_alignment_contracts(graph, alignments_data)
    canonical_objects = alignments_data.get("canonical_objects", [])
    relation_overrides = {
        tuple(record["endpoints"]): record["emitted_relation"]
        for record in alignments_data.get("active_relation_overrides", [])
    }

    alignment_summary = {
        "total_canonical_objects": len(canonical_objects),
        "total_alignments": 0,
        "gallier_alignments": 0,
        "axler_alignments": 0,
        "vmls_alignments": 0,
        "cvx_alignments": 0,
        "billingsley_alignments": 0,
        "lee_alignments": 0,
        "ahlfors_alignments": 0,
        "cross_source_same": 0,
        "cross_source_scoped_overlap": 0,
        "cross_source_related": 0,
        "unresolved": 0,
        "two_source_canonical_objects": 0,
        "three_source_canonical_objects": 0,
        "four_source_canonical_objects": 0,
        "five_source_canonical_objects": 0,
        "six_source_canonical_objects": 0,
        "seven_source_canonical_objects": 0,
        "representation_diversity": {
            "abstract": 0,
            "algebraic": 0,
            "geometric": 0,
            "computational": 0,
            "applied": 0,
            "formal": 0,
        },
    }

    for co in canonical_objects:
        cid = co["id"]
        cname = co["name"]
        domain = co.get("domain", "General Mathematics")
        desc = co.get("description", "")
        formal_decl = co.get("formal_decl", None)
        rep_diversity = co.get("representation_kinds", ["abstract"])
        diversity_count = len(rep_diversity)
        canonical_contract_sha256 = _canonical_contract_sha256(co)

        for rk in rep_diversity:
            if rk in alignment_summary["representation_diversity"]:
                alignment_summary["representation_diversity"][rk] += 1

        # Canonical Object Node
        add_node(
            nodes,
            by_id,
            {
                "id": cid,
                "type": "CANONICAL_OBJECT",
                "label": cname,
                "attributes": {
                    "domain": domain,
                    "description": desc,
                    "formal_decl": formal_decl,
                    "representation_diversity": rep_diversity,
                    "diversity_count": diversity_count,
                    "canonical_contract_sha256": canonical_contract_sha256,
                    "stage": STAGE,
                },
            },
        )

        alignments = co.get("alignments", [])
        gallier_sources = []
        axler_sources = []
        vmls_sources = []
        cvx_sources = []
        billingsley_sources = []
        lee_sources = []
        ahlfors_sources = []

        for al in alignments:
            src_id = al["source"]
            corpus = al["corpus"]
            status = al.get("status", "CROSS_SOURCE_SAME")

            alignment_summary["total_alignments"] += 1

            # Fail-closed provenance check: verify source declaration node exists in graph
            if src_id not in by_id:
                raise ValueError(
                    f"Fail-closed provenance error: Source declaration '{src_id}' referenced in canonical object '{cid}' ({corpus}) is not present in graph!"
                )
            bound_source_id, bound_corpus, source_statement_sha256 = _source_binding(by_id[src_id])
            if bound_corpus != corpus:
                raise ValueError(
                    f"corpus mismatch for {src_id}: contract={corpus!r}, source={bound_corpus!r}"
                )

            if corpus == "AXLER":
                alignment_summary["axler_alignments"] += 1
                axler_sources.append((src_id, status))
            elif corpus == "GALLIER":
                alignment_summary["gallier_alignments"] += 1
                gallier_sources.append((src_id, status))
            elif corpus == "VMLS":
                alignment_summary["vmls_alignments"] += 1
                vmls_sources.append((src_id, status))
            elif corpus == "CVX":
                alignment_summary["cvx_alignments"] += 1
                cvx_sources.append((src_id, status))
            elif corpus == "BILLINGSLEY":
                alignment_summary["billingsley_alignments"] += 1
                billingsley_sources.append((src_id, status))
            elif corpus == "LEE":
                alignment_summary["lee_alignments"] += 1
                lee_sources.append((src_id, status))
            elif corpus == "AHLFORS":
                alignment_summary["ahlfors_alignments"] += 1
                ahlfors_sources.append((src_id, status))

            if status == "CROSS_SOURCE_SAME":
                alignment_summary["cross_source_same"] += 1
            elif status == "CROSS_SOURCE_SCOPED_OVERLAP":
                alignment_summary["cross_source_scoped_overlap"] += 1
            elif status == "CROSS_SOURCE_RELATED_NOT_SAME":
                alignment_summary["cross_source_related"] += 1
            elif status == "UNRESOLVED":
                alignment_summary["unresolved"] += 1

            # REPRESENTS edge: Source Declaration -> Canonical Object
            rep_edge_id = represents_edge_id(cid, src_id, canonical_contract_sha256)
            add_edge(
                edges,
                edge_ids,
                {
                    "id": rep_edge_id,
                    "type": "REPRESENTS",
                    "source": src_id,
                    "target": cid,
                    "attributes": {
                        "corpus": corpus,
                        "alignment_status": status,
                        "source_id": bound_source_id,
                        "source_statement_sha256": source_statement_sha256,
                        "canonical_contract_sha256": canonical_contract_sha256,
                        "evidence_status": "CURATED_ALIGNMENT_NOT_KERNEL_VERIFIED",
                        "stage": STAGE,
                    },
                },
            )

        # Multi-source multi-corpus tracking
        active_corpora = set()
        if gallier_sources:
            active_corpora.add("GALLIER")
        if axler_sources:
            active_corpora.add("AXLER")
        if vmls_sources:
            active_corpora.add("VMLS")
        if cvx_sources:
            active_corpora.add("CVX")
        if billingsley_sources:
            active_corpora.add("BILLINGSLEY")
        if lee_sources:
            active_corpora.add("LEE")
        if ahlfors_sources:
            active_corpora.add("AHLFORS")

        num_corpora = len(active_corpora)
        if num_corpora >= 2:
            alignment_summary["two_source_canonical_objects"] += 1
        if num_corpora >= 3:
            alignment_summary["three_source_canonical_objects"] += 1
        if num_corpora >= 4:
            alignment_summary["four_source_canonical_objects"] += 1
        if num_corpora >= 5:
            alignment_summary["five_source_canonical_objects"] += 1
        if num_corpora >= 6:
            alignment_summary["six_source_canonical_objects"] += 1
        if num_corpora >= 7:
            alignment_summary["seven_source_canonical_objects"] += 1

        # Synthesize typed semantic bridge edges between distinct corpora under this canonical object
        all_sources = []
        for s, st in gallier_sources:
            all_sources.append((s, "GALLIER", st))
        for s, st in axler_sources:
            all_sources.append((s, "AXLER", st))
        for s, st in vmls_sources:
            all_sources.append((s, "VMLS", st))
        for s, st in cvx_sources:
            all_sources.append((s, "CVX", st))
        for s, st in billingsley_sources:
            all_sources.append((s, "BILLINGSLEY", st))
        for s, st in lee_sources:
            all_sources.append((s, "LEE", st))
        for s, st in ahlfors_sources:
            all_sources.append((s, "AHLFORS", st))

        for i in range(len(all_sources)):
            src_a, corp_a, stat_a = all_sources[i]
            for j in range(i + 1, len(all_sources)):
                src_b, corp_b, stat_b = all_sources[j]
                if corp_a != corp_b:
                    edge_type = relation_overrides.get(
                        tuple(sorted((src_a, src_b))),
                        _derived_relation(
                            {"status": stat_a},
                            {"status": stat_b},
                        ),
                    )

                    scoped_bridge_id = bridge_edge_id(cid, edge_type, src_a, src_b)
                    add_edge(
                        edges,
                        edge_ids,
                        {
                            "id": scoped_bridge_id,
                            "type": edge_type,
                            "source": src_a,
                            "target": src_b,
                            "attributes": {
                                "canonical_id": cid,
                                "canonical_contract_sha256": canonical_contract_sha256,
                                "source_corpora": [corp_a, corp_b],
                                "endpoint_statement_sha256": {
                                    src_a: _source_binding(by_id[src_a])[2],
                                    src_b: _source_binding(by_id[src_b])[2],
                                },
                                "evidence_status": "CURATED_ALIGNMENT_NOT_KERNEL_VERIFIED",
                                "stage": STAGE,
                            },
                        },
                    )

    graph["_alignment_summary_v0_19"] = alignment_summary
    return graph


def normalize_domain(name: str) -> str:
    mapping = {
        "Linear Algebra": "Linear Algebra",
        "Applied Linear Algebra": "Applied Linear Algebra & Optimization",
        "Applied Linear Algebra & Optimization": "Applied Linear Algebra & Optimization",
        "Convex Analysis & Optimization": "Convex Analysis & Optimization",
        "Differential Calculus & Real Analysis": "Differential Calculus & Real Analysis",
        "Topology & Metric Spaces": "Topology & Metric Spaces",
        "Measure Theory & Probability": "Measure Theory & Probability",
        "Differential Geometry & Lie Groups": "Differential Geometry & Lie Groups",
        "Complex Analysis & Riemann Surfaces": "Complex Analysis & Riemann Surfaces",
        "Foundational Mathematics": "Foundational Mathematics",
    }
    return mapping.get(name, name)


def run_v0_19_intake(
    base_graph_path: Path,
    alignments_path: Path,
    out_dir: Path,
    amendments_path: Path = DEFAULT_AMENDMENTS_PATH,
    evidence_path: Path | None = None,
) -> dict[str, Any]:
    print(f"[{STAGE} Intake] Loading base graph: {base_graph_path}")
    base_graph = load_json_or_gz(base_graph_path)

    print(f"[{STAGE} Intake] Extracting Source G (Complex Analysis, SCV & Riemann Surfaces) declarations...")
    complex_decls = build_complex_declarations()
    print(f"[{STAGE} Intake] Ingesting {len(complex_decls)} Source G declarations...")
    graph = ingest_complex_declarations(base_graph, complex_decls)

    print(f"[{STAGE} Intake] Ingesting canonical cross-source alignments from: {alignments_path}")
    graph = ingest_v0_19_canonical_alignments(
        graph,
        alignments_path,
        amendments_path,
    )

    # Compute graph metrics
    nodes = graph["nodes"]
    edges = graph["edges"]

    raw_source_nodes = [
        n for n in nodes
        if n.get("type") in ("SOURCE_DECLARATION", "STATEMENT")
        and n.get("type") != "SOURCE_SECTION_ANCHOR"
    ]
    section_anchor_nodes = [n for n in nodes if n.get("type") == "SOURCE_SECTION_ANCHOR"]
    canonical_nodes = [n for n in nodes if n.get("type") == "CANONICAL_OBJECT"]

    source_counts = partition_v0_19_source_declarations(raw_source_nodes)
    excluded_source_nodes = [
        node
        for node in raw_source_nodes
        if authoritative_source_registry()[node["id"]]["count_status"]
        == "EXCLUDED_HISTORICAL_COUNT_ARTIFACT"
    ]
    admissible_source_count = len(raw_source_nodes) - len(excluded_source_nodes)

    for node in section_anchor_nodes:
        _source_binding(node)
        if authoritative_source_registry()[node["id"]]["count_status"] != "SECTION_ANCHOR":
            raise ValueError(f"unregistered section anchor role: {node.get('id')}")

    # Verify disjoint partition completeness
    sum_sources = sum(source_counts.values())
    if sum_sources != admissible_source_count:
        raise ValueError(
            "Provenance integrity violation: disjoint partition sum "
            f"({sum_sources}) != admissible source declarations ({admissible_source_count})"
        )

    # Multi-source canonical count
    domains_set = set()
    total_rep_kinds = 0
    multi_source_counts = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}

    # Map canonical objects to connected corpora
    canonical_corpora_map: dict[str, set[str]] = {}
    for e in edges:
        if e.get("type") == "REPRESENTS":
            cid = e.get("target")
            corp = e.get("attributes", {}).get("corpus")
            if cid and corp:
                canonical_corpora_map.setdefault(cid, set()).add(corp)

    for co in canonical_nodes:
        attrs = co.get("attributes", {})
        dom = attrs.get("domain")
        if dom:
            domains_set.add(normalize_domain(dom))
        rk_list = attrs.get("representation_diversity", [])
        total_rep_kinds += len(rk_list) if rk_list else 1

        connected_corps = canonical_corpora_map.get(co["id"], set())
        nc = len(connected_corps)
        for k in range(2, 8):
            if nc >= k:
                multi_source_counts[k] += 1

    r_bar = round(total_rep_kinds / max(len(canonical_nodes), 1), 3)

    # Bridge counts
    bridge_same = sum(1 for e in edges if e.get("type") == "SAME_SEMANTICS")
    bridge_scoped = sum(1 for e in edges if e.get("type") == "SCOPED_OVERLAP")
    bridge_related = sum(1 for e in edges if e.get("type") == "RELATED_TO")
    total_cross_bridges = bridge_same + bridge_scoped + bridge_related

    edge_type_counts = {}
    for e in edges:
        et = e.get("type", "UNKNOWN")
        edge_type_counts[et] = edge_type_counts.get(et, 0) + 1

    dashboard = {
        "stage": STAGE,
        "N_source_total": admissible_source_count,
        "N_source_records_raw": len(raw_source_nodes),
        "N_source_records_excluded": len(excluded_source_nodes),
        "source_breakdown": source_counts,
        "disjoint_partition_verified": True,
        "N_section_anchors_total": len(section_anchor_nodes),
        "N_canonical_total": len(canonical_nodes),
        "multi_source_bridges": {
            "two_source_or_more": multi_source_counts[2],
            "three_source_or_more": multi_source_counts[3],
            "four_source_or_more": multi_source_counts[4],
            "five_source_or_more": multi_source_counts[5],
            "six_source_or_more": multi_source_counts[6],
            "seven_source_or_more": multi_source_counts[7],
        },
        "domains": {
            "count": len(domains_set),
            "list": sorted(list(domains_set)),
        },
        "representation_diversity": {
            "average_richness_r_bar": r_bar,
        },
        "edges_summary": {
            "total_edges": len(edges),
            "SAME_SEMANTICS": bridge_same,
            "SCOPED_OVERLAP": bridge_scoped,
            "RELATED_TO": bridge_related,
            "total_cross_source_bridges": total_cross_bridges,
            "edge_types": edge_type_counts,
        },
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    graph_out = out_dir / "mapeogeo_v0_19_graph.json.gz"
    dashboard_out = out_dir / "complex_analysis_v0_19_dashboard.json"
    evidence_out = resolve_v0_19_evidence_path(out_dir, evidence_path)

    print(f"[{STAGE} Intake] Saving compressed graph to {graph_out}")
    save_graph_gz(graph, graph_out)

    print(f"[{STAGE} Intake] Saving dashboard to {dashboard_out}")
    dashboard_out.write_text(
        json.dumps(dashboard, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"[{STAGE} Intake] Saving scientific evidence to {evidence_out}")
    evidence_out.parent.mkdir(parents=True, exist_ok=True)
    evidence_out.write_text(
        json.dumps(dashboard, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"[{STAGE} Intake] Success! Total nodes: {len(nodes)}, Total edges: {len(edges)}")
    print(f"[{STAGE} Intake] Semantic Bridges: {total_cross_bridges} (SAME: {bridge_same}, SCOPED: {bridge_scoped}, REL: {bridge_related})")
    print(f"[{STAGE} Intake] Distinct Domains: {len(domains_set)} -> {sorted(list(domains_set))}")
    return dashboard


def main() -> int:
    parser = argparse.ArgumentParser(description="MAPEOGEO v0.19 Complex Analysis Intake Pipeline")
    parser.add_argument(
        "--base-graph",
        type=Path,
        default=ROOT / "artifacts" / "diffgeom_v0_18" / "mapeogeo_v0_18_graph.json.gz",
        help="Path to previous stage graph (v0.18 or foundation backfill)",
    )
    parser.add_argument(
        "--alignments",
        type=Path,
        default=ROOT / "formal" / "cross_source_alignments_v0_19.json",
        help="Path to v0.19 canonical alignments JSON",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "artifacts" / "complex_analysis_v0_19",
        help="Directory to save v0.19 graph and dashboard",
    )
    parser.add_argument(
        "--amendments",
        type=Path,
        default=DEFAULT_AMENDMENTS_PATH,
        help="Path to source-bound v0.20 mathematical-integrity amendments",
    )
    parser.add_argument(
        "--evidence-out",
        type=Path,
        default=None,
        help="Optional additive active evidence path; sealed v0.19 evidence is forbidden",
    )
    args = parser.parse_args()

    run_v0_19_intake(
        args.base_graph,
        args.alignments,
        args.out_dir,
        args.amendments,
        args.evidence_out,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
