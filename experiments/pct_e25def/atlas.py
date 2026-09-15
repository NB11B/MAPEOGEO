from __future__ import annotations

from collections import Counter
import json

from experiments.pct_e25bc.executable import _EXECUTORS

from .model import EVIDENCE, LEVELS, load_real_component_manifest, validate_manifest


def _pass(evidence_refs: list[str], **extra) -> dict:
    return {"state": "PASS", "evidence_refs": evidence_refs, **extra}


def _nonpass(state: str, reason: str, **extra) -> dict:
    return {"state": state, "reason": reason, **extra}


def _evaluate_c0(component: dict) -> dict:
    h = component["source_statement_sha256"]
    ids = {component[k] for k in ("anchor_id", "eo_id", "geo_id", "formal_id")}
    if len(ids) != 4:
        return _nonpass("FAIL", "IDENTITY_NODE_COLLISION")
    if set(component["source_hashes"].values()) != {h}:
        return _nonpass("FAIL", "SOURCE_HASH_IDENTITY_MISMATCH")

    represents = [e for e in component["semantic_edges"] if e["type"] == "REPRESENTS"]
    expected = {
        (component["eo_id"], component["anchor_id"]),
        (component["geo_id"], component["anchor_id"]),
        (component["formal_id"], component["anchor_id"]),
    }
    observed = {(e["source"], e["target"]) for e in represents}
    if observed != expected:
        return _nonpass("FAIL", "REPRESENTATION_ANCHOR_BINDING_MISMATCH")
    return _pass([
        "evidence/pct_e25d_real_component_manifest.json",
        *[e["id"] for e in represents],
    ])


def _evaluate_c1(component: dict, c0: dict) -> dict:
    if c0["state"] != "PASS":
        return _nonpass("INVALID", "C0_IDENTITY_PRECONDITION_FAILED")
    certs = component["certificates"]
    v07, v08 = component["certificate_ids"]
    if any(certs[cid].get("status") != "PASS" for cid in (v07, v08)):
        return _nonpass("FAIL", "CERTIFICATE_STATUS_NOT_PASS")
    if certs[v07].get("contract") != component["contract"]:
        return _nonpass("FAIL", "EXECUTABLE_CERTIFICATE_CONTRACT_MISMATCH")
    if certs[v08].get("certificate_class") != "KERNEL_VERIFIED":
        return _nonpass("FAIL", "FORMAL_CERTIFICATE_NOT_KERNEL_VERIFIED")
    if certs[v08].get("formal_scope") != component["formal_scope"]:
        return _nonpass("FAIL", "FORMAL_SCOPE_CERTIFICATE_MISMATCH")

    edges = component["semantic_edges"]
    anchor_verify = any(e["type"] == "VERIFIED_BY" and e["source"] == component["anchor_id"] and e["target"] == v07 for e in edges)
    formal_verify = any(e["type"] == "VERIFIED_BY" and e["source"] == component["formal_id"] and e["target"] == v08 for e in edges)
    executable_equiv = any(
        e["type"] in {"SAME_SEMANTICS", "EQUIVALENT_TO"}
        and {e["source"], e["target"]} == {component["eo_id"], component["geo_id"]}
        and e.get("attributes", {}).get("certificate") == v07
        for e in edges
    )
    formal_equiv = [
        e for e in edges
        if e["type"] == "EQUIVALENT_TO"
        and e["source"] == component["formal_id"]
        and e["target"] in {component["eo_id"], component["geo_id"]}
        and e.get("attributes", {}).get("evidence") == "LEAN_KERNEL_VERIFIED"
        and e.get("attributes", {}).get("scope") == component["formal_scope"]
        and e.get("attributes", {}).get("source_statement_sha256") == component["source_statement_sha256"]
    ]
    if not (anchor_verify and formal_verify and executable_equiv and len(formal_equiv) == 2):
        return _nonpass("FAIL", "CERTIFICATE_EDGE_BINDING_MISMATCH")
    return _pass([
        "evidence/pct_e25d_real_component_manifest.json",
        v07,
        v08,
        *[e["id"] for e in edges if e["type"] in {"VERIFIED_BY", "SAME_SEMANTICS", "EQUIVALENT_TO"}],
    ])


def _load_frozen_e25c() -> dict:
    return json.loads((EVIDENCE / "pct_e25c_executable_cycle_audit.json").read_text(encoding="utf-8"))


def _evaluate_c2(component: dict, c1: dict, frozen_cycle: dict) -> dict:
    if c1["state"] != "PASS":
        return _nonpass("INVALID", "C1_CERTIFICATE_PRECONDITION_FAILED")
    if component["contract"] not in _EXECUTORS:
        return _nonpass("NOT_ESTABLISHED", "EXECUTABLE_ADAPTER_MISSING")
    exact_inputs, pairwise_equalities, all_paths_agree = _EXECUTORS[component["contract"]]()
    bindings_match = (
        frozen_cycle.get("contract") == component["contract"]
        and frozen_cycle.get("anchor") == component["anchor_id"]
        and frozen_cycle.get("eo") == component["eo_id"]
        and frozen_cycle.get("geo") == component["geo_id"]
        and frozen_cycle.get("formal") == component["formal_id"]
        and frozen_cycle.get("formal_scope") == component["formal_scope"]
        and frozen_cycle.get("source_statement_sha256") == component["source_statement_sha256"]
        and frozen_cycle.get("exact_inputs") == exact_inputs
        and frozen_cycle.get("pairwise_path_equalities") == pairwise_equalities
    )
    if not bindings_match:
        return _nonpass("FAIL", "EXECUTABLE_EVIDENCE_BINDING_MISMATCH")
    if not all_paths_agree or frozen_cycle.get("all_paths_agree") is not True:
        return _nonpass("FAIL", "EXECUTABLE_PATH_DISAGREEMENT")
    return _pass([
        "evidence/pct_e25c_executable_cycle_audit.json",
        f"fresh_executor:{component['contract']}",
    ], exact_inputs=exact_inputs, pairwise_path_equalities=pairwise_equalities)


def evaluate_component(component: dict, frozen_cycles: dict[str, dict]) -> dict:
    c0 = _evaluate_c0(component)
    c1 = _evaluate_c1(component, c0)
    c2 = _evaluate_c2(component, c1, frozen_cycles[component["contract"]])
    closure = {
        "C0": c0,
        "C1": c1,
        "C2": c2,
        "C3": _nonpass("NOT_APPLICABLE", component["applicability_reasons"]["C3"]),
        "C4": _nonpass("NOT_APPLICABLE", component["applicability_reasons"]["C4"]),
        "C5": _nonpass("NOT_ESTABLISHED", "EXACT_MORPHISM_PROVENANCE_NOT_SERIALIZED"),
    }

    last_pass = None
    blocking_gap = None
    for level in LEVELS:
        if not component["applicability"][level]:
            continue
        state = closure[level]["state"]
        if state == "PASS":
            last_pass = level
            continue
        blocking_gap = closure[level].get("reason")
        break

    return {
        "component_id": component["component_id"],
        "provenance_class": component["provenance_class"],
        "contract": component["contract"],
        "anchor_id": component["anchor_id"],
        "eo_id": component["eo_id"],
        "geo_id": component["geo_id"],
        "formal_id": component["formal_id"],
        "formal_scope": component["formal_scope"],
        "source_statement_sha256": component["source_statement_sha256"],
        "closure": closure,
        "applicability_mask": component["applicability"],
        "closure_frontier": last_pass,
        "blocking_gap": blocking_gap,
    }


def run_e25d() -> dict:
    manifest = load_real_component_manifest()
    validation = validate_manifest(manifest)
    if validation.get("status") != "PASS":
        return {
            "experiment_id": "E25D_CLOSURE_DEPTH_ATLAS",
            "status": "INVALID",
            "manifest_validation": validation,
            "components": [],
        }
    frozen = _load_frozen_e25c()
    cycles = {c["contract"]: c for c in frozen["cycles"]}
    components = [evaluate_component(c, cycles) for c in sorted(manifest["components"], key=lambda c: c["component_id"])]
    bad_states = {"FAIL", "INVALID", "ERROR"}
    bad = [
        (c["component_id"], level, c["closure"][level]["state"])
        for c in components for level in LEVELS
        if c["closure"][level]["state"] in bad_states
    ]
    frontier_histogram = Counter(c["closure_frontier"] for c in components)
    return {
        "experiment_id": "E25D_CLOSURE_DEPTH_ATLAS",
        "status": "PASS" if not bad else "FAIL",
        "source_artifact": manifest["source_artifact"],
        "real_components": len(components),
        "synthetic_components_counted_as_real": 0,
        "frontier_histogram": dict(sorted(frontier_histogram.items())),
        "components": components,
        "blocking_failures": bad,
        "claim_boundary": (
            "Closure levels are assigned only to the four frozen REAL_SOURCE_BOUND components. "
            "Synthetic E25B topology controls do not count as repository closure evidence."
        ),
    }
