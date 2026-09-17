from __future__ import annotations

from copy import deepcopy

from .multipath import load_trust_projection, _identity_audit, _certificate_audit
from .executable import run_e25c

def run_synthetic_layer_attacks() -> dict:
    base = load_trust_projection()

    anchor_swap = deepcopy(base)
    for edge in anchor_swap["edges"]:
        if edge["type"] == "REPRESENTS" and edge["source"] == "repr:eo:theorem:6_16":
            edge["target"] = "srcdecl:definition:44_6"
            break
    a0 = _identity_audit(anchor_swap)["pass"]

    certificate_flip = deepcopy(base)
    for node in certificate_flip["nodes"]:
        if node["id"] == "cert:v07:theorem:6_16":
            node.setdefault("attributes", {})["status"] = "FAIL"
            break
    c0 = _identity_audit(certificate_flip)["pass"]
    c1 = _certificate_audit(certificate_flip)["pass"] if c0 else False

    e0 = _identity_audit(base)["pass"]
    e1 = _certificate_audit(base)["pass"] if e0 else False
    e2 = run_e25c(mutate_contract="rank", mutate_view="GEO")["status"] == "PASS" if e1 else False

    return {
        "anchor_swap": {
            "C0_identity": "PASS" if a0 else "FAIL",
            "C1_certificate": "NOT_REACHED" if not a0 else ("PASS" if _certificate_audit(anchor_swap)["pass"] else "FAIL"),
            "C2_executable": "NOT_REACHED" if not a0 else "UNTESTED",
        },
        "certificate_flip": {
            "C0_identity": "PASS" if c0 else "FAIL",
            "C1_certificate": "PASS" if c1 else "FAIL",
            "C2_executable": "NOT_REACHED" if not c1 else "UNTESTED",
        },
        "executable_mutation": {
            "C0_identity": "PASS" if e0 else "FAIL",
            "C1_certificate": "PASS" if e1 else "FAIL",
            "C2_executable": "PASS" if e2 else "FAIL",
        },
    }
