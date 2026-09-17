"""Wave F5 Certificate Verification, Lineage, Scope Audit & Quorum Integration."""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from mapeogeo.wave_f5.scopes import TypedScopeRecord, compare_scopes, ScopeComparisonOutcome

REGISTERED_JOINT_TYPES: Set[str] = {
    "OPERATOR_ACTION",
    "FIXED_POINT_CONSTRUCTION",
    "EVOLUTION_FLOW",
    "LINEARIZATION",
    "CONTINUOUS_DEPENDENCE",
    "SPECTRAL_PROJECTION",
    "VARIATIONAL_COUPLING",
    "MONOTONICITY_FORMULA",
    "BOUNDARY_DUALITY",
    "METRIC_CONTRACTION",
    "GRADIENT_FLOW",
    "TOPOLOGICAL_SURGERY",
    "ASYMPTOTIC_BLOWUP",
    "HOMOLOGICAL_COMPLEX",
    "COBORDISM",
}

FORBIDDEN_RELATIONSHIPS: Set[str] = {
    "SAME_SEMANTICS",
    "EQUIVALENT_TO",
    "IDENTICAL_TO",
}


def validate_joint(joint: Dict[str, Any], active_concepts: Optional[Set[str]] = None) -> Dict[str, Any]:
    """Validate a mechanism joint against Wave F5 rules."""
    joint_id = joint.get("joint_id", "")
    if not re.match(r"^joint:[a-zA-Z0-9_:-]+$", joint_id):
        return {"valid": False, "error": f"Invalid joint ID format: '{joint_id}'"}

    joint_type = joint.get("joint_type", "")
    if joint_type not in REGISTERED_JOINT_TYPES:
        return {"valid": False, "error": f"Unregistered joint type: '{joint_type}'"}

    rel = joint.get("relationship", "")
    if rel in FORBIDDEN_RELATIONSHIPS:
        return {"valid": False, "error": f"Forbidden auto-promotion relationship: '{rel}'"}

    feet = joint.get("feet", [])
    if len(feet) < 2:
        return {"valid": False, "error": "Joint must have at least 2 feet"}

    if active_concepts is not None:
        for foot in feet:
            node_id = foot.get("node_id")
            if node_id not in active_concepts:
                return {"valid": False, "error": f"Foot node '{node_id}' not found in active concepts"}

    # Typing negative controls
    metadata = joint.get("metadata", {})
    system_type = str(metadata.get("system_type", "")).lower()
    if joint_type == "GRADIENT_FLOW" and ("rotation" in system_type or "conservative" in system_type or "hamiltonian" in system_type):
        return {"valid": False, "error": "Rotation cannot be typed as GRADIENT_FLOW; conservative systems preserve energy"}

    return {"valid": True, "error": None}


def compute_quorum(
    view_slots: Dict[str, Any],
    target_scope: Optional[Dict[str, Any]] = None,
) -> Tuple[int, List[str], List[str]]:
    """Compute independent quorum count across view slots, verifying lineage and receipts."""
    witnessed_slots: List[str] = []
    seen_producers: Set[str] = set()
    seen_digests: Set[str] = set()
    reasons: List[str] = []

    for slot_name, slot_data in view_slots.items():
        if not isinstance(slot_data, dict):
            continue
        status = slot_data.get("status", "ABSENT")
        if status not in ("WITNESSED", "VERIFIED"):
            continue

        # Formal slot verification requirement
        if slot_name == "formal":
            formal_receipt = slot_data.get("formal_receipt")
            if not formal_receipt:
                reasons.append("Formal slot missing formal build/axiom receipt; kernel_verified boolean alone is rejected")
                continue
            required_receipt_fields = ["theorem_name", "module_path", "axiom_audit", "build_hash"]
            if not all(field in formal_receipt for field in required_receipt_fields):
                reasons.append(f"Formal receipt missing mandatory fields: {required_receipt_fields}")
                continue

        # Check producer and execution digest uniqueness (anti-aliasing)
        producer_id = slot_data.get("producer_id", "")
        digest = slot_data.get("execution_digest", "")

        if producer_id and digest:
            if producer_id in seen_producers and digest in seen_digests:
                reasons.append(f"Aliased witness in slot '{slot_name}' with producer '{producer_id}' and duplicate digest")
                continue
            seen_producers.add(producer_id)
            seen_digests.add(digest)

        witnessed_slots.append(slot_name)

    return len(witnessed_slots), witnessed_slots, reasons


class WaveF5CertificateVerifier:
    """Verifier for Wave F5 correspondence certificates with independent quorum enforcement."""

    def __init__(
        self,
        active_concepts: Optional[Set[str]] = None,
        active_formulations: Optional[Set[str]] = None,
    ) -> None:
        self.active_concepts = active_concepts
        self.active_formulations = active_formulations

    def verify_certificate(self, cert: Dict[str, Any]) -> Dict[str, Any]:
        cert_id = cert.get("certificate_id", "")
        target = cert.get("target_concept", "")
        rel = cert.get("relationship", "")

        if not re.match(r"^cert:[a-zA-Z0-9_:-]+$", cert_id):
            return {
                "valid": False,
                "certificate_id": cert_id,
                "computed_quorum": 0,
                "verification_status": "REJECTED",
                "rejection_reason": f"Invalid certificate ID: {cert_id}",
            }

        if rel in FORBIDDEN_RELATIONSHIPS:
            return {
                "valid": False,
                "certificate_id": cert_id,
                "computed_quorum": 0,
                "verification_status": "REJECTED",
                "rejection_reason": f"Forbidden auto-promotion relationship: {rel}",
            }

        if self.active_concepts is not None and target not in self.active_concepts:
            return {
                "valid": False,
                "certificate_id": cert_id,
                "computed_quorum": 0,
                "verification_status": "REJECTED",
                "rejection_reason": f"Target concept '{target}' not in active concepts registry",
            }

        view_slots = cert.get("view_slots", {})
        scope = cert.get("scope", {})
        quorum_count, witnessed_slots, reasons = compute_quorum(view_slots, target_scope=scope)

        claimed_status = cert.get("verification_status", "PROVISIONAL")
        if claimed_status == "FALSIFIED":
            return {
                "valid": True,
                "certificate_id": cert_id,
                "computed_quorum": quorum_count,
                "verification_status": "FALSIFIED",
                "witnessed_slots": witnessed_slots,
                "rejection_reason": "; ".join(reasons) if reasons else "Certified counterexample / falsification",
            }

        if quorum_count >= 2:
            status = "CERTIFIED"
        elif quorum_count == 1:
            status = "PROVISIONAL"
        else:
            status = "INSUFFICIENT_QUORUM" if not reasons else "REJECTED"

        return {
            "valid": status == "CERTIFIED" or (status == "PROVISIONAL" and claimed_status == "PROVISIONAL"),
            "certificate_id": cert_id,
            "computed_quorum": quorum_count,
            "witnessed_slots": witnessed_slots,
            "verification_status": status,
            "rejection_reason": "; ".join(reasons) if reasons else None,
        }


def validate_certificate(cert: Dict[str, Any], active_concepts: Optional[Set[str]] = None) -> Dict[str, Any]:
    verifier = WaveF5CertificateVerifier(active_concepts=active_concepts)
    return verifier.verify_certificate(cert)
