"""Fail-closed ingestion for GFYProof proof-carrying certificates.

GFYProof is treated as an independent executable verifier, not as a source
corpus and not as a Lean kernel. Successful ingestion may add executable
evidence and registered proof-eligible edges, but never SOURCE_DECLARATION or
KERNEL_VERIFIED status.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, MutableMapping

from scripts.compute_foundation_depth import (
    RegisteredEdgeEvidence,
    bound_edge_evidence_sha256,
    node_identity_sha256,
)


BRIDGE_SCHEMA = "mapeogeo.gfyproof.edge-certificate.v2"
PRODUCER_REPOSITORY = "NB11B/GFYProof"
VERIFIER_ID = "GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

SEMANTIC_VERIFIER_EDGE_TYPES: dict[str, frozenset[str]] = {
    "GFY.DFA_EQUIVALENCE.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.ROBDD_EQUIVALENCE.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.FARKAS_IMPLICATION.v1": frozenset(
        {"UPWARD_FOUNDATION_DEPENDENCY", "PROOF_DEPENDENCY"}
    ),
    "GFY.POLYNOMIAL_IDEAL_MEMBERSHIP.v1": frozenset(
        {"UPWARD_FOUNDATION_DEPENDENCY", "PROOF_DEPENDENCY"}
    ),
}

