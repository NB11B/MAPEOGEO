"""Minimal Obstruction and Repair Signatures Specification.

Defines the mathematical signature structure for:
- Obstruction Signature Omega(X)
- Repair Transformation rho(Omega)
"""

from typing import Dict, List, Any, Optional

class ObstructionSignature:
    """Represents a minimal obstruction signature Omega(X)."""

    def __init__(
        self,
        signature_type: str,
        defect_locus: str,
        intensity: float,
        inconsistent_subset: List[str],
        witness: Optional[str] = None
    ):
        self.signature_type = signature_type
        self.defect_locus = defect_locus
        self.intensity = intensity
        self.inconsistent_subset = inconsistent_subset
        self.witness = witness

    def is_vanishing(self) -> bool:
        return self.signature_type == "NONE" or self.intensity == 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signature_type": self.signature_type,
            "defect_locus": self.defect_locus,
            "intensity": round(self.intensity, 4),
            "is_vanishing": self.is_vanishing(),
            "inconsistent_subset": self.inconsistent_subset,
            "witness": self.witness
        }

class RepairTransformation:
    """Represents a minimal domain repair rho(Omega)."""

    def __init__(
        self,
        repair_type: str,
        target_subsystem: str,
        domain_restriction: str,
        expected_retention_ratio: float
    ):
        self.repair_type = repair_type
        self.target_subsystem = target_subsystem
        self.domain_restriction = domain_restriction
        self.expected_retention_ratio = expected_retention_ratio

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repair_type": self.repair_type,
            "target_subsystem": self.target_subsystem,
            "domain_restriction": self.domain_restriction,
            "expected_retention_ratio": round(self.expected_retention_ratio, 4)
        }
