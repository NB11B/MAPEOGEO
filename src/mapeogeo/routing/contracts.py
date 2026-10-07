"""Domain-neutral Work Contracts and Resource/Authority Specifications.

Provides:
- WorkContract: Atomic, typed capability step with pre/post-conditions and invariants.
- ResourceRequirement: Extensible multi-resource specification (CPU, RAM, GPU, NPU, energy).
- AuthorityRequirement: Explicit permission and security clearance specifications.
- RoutingBudget: Multi-dimensional resource, tolerance, and cost envelope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ResourceRequirement:
    """Multi-resource specification for a work contract.

    Preserves historical resource vocabulary {CPU, RAM, GPU, NPU, energy}
    while remaining extensible without hardcoded hardware assumptions.
    """

    cpu_cores: float = 0.0
    ram_mb: float = 0.0
    gpu_count: float = 0.0
    npu_count: float = 0.0
    energy_joules: float = 0.0
    custom: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.cpu_cores < 0 or self.ram_mb < 0 or self.gpu_count < 0 or self.npu_count < 0:
            raise ValueError("Hardware resource requirements must be non-negative")
        if self.energy_joules < 0:
            raise ValueError("Energy requirement must be non-negative")

    def combine(self, other: ResourceRequirement) -> ResourceRequirement:
        """Combine resource requirements along a route composition."""
        all_custom_keys = set(self.custom.keys()) | set(other.custom.keys())
        merged_custom = {
            k: round(self.custom.get(k, 0.0) + other.custom.get(k, 0.0), 4) for k in all_custom_keys
        }
        return ResourceRequirement(
            cpu_cores=round(self.cpu_cores + other.cpu_cores, 4),
            ram_mb=round(self.ram_mb + other.ram_mb, 4),
            gpu_count=round(self.gpu_count + other.gpu_count, 4),
            npu_count=round(self.npu_count + other.npu_count, 4),
            energy_joules=round(self.energy_joules + other.energy_joules, 4),
            custom=merged_custom,
        )

    def fits_in(self, budget: RoutingBudget) -> bool:
        """Check if this requirement fits within a given routing budget."""
        if self.cpu_cores > budget.max_cpu_cores:
            return False
        if self.ram_mb > budget.max_ram_mb:
            return False
        if self.gpu_count > budget.max_gpu_count:
            return False
        if self.npu_count > budget.max_npu_count:
            return False
        if self.energy_joules > budget.max_energy_joules:
            return False
        for k, v in self.custom.items():
            if v > budget.custom_limits.get(k, float("inf")):
                return False
        return True


@dataclass(frozen=True)
class AuthorityRequirement:
    """Security clearance and authority credential requirement.

    INVARIANT:
        Authority is strictly independent of capability:
            can execute != authorized to execute.
    A route with sufficient machinery but insufficient authority must be rejected,
    not merely penalized.
    """

    required_role: str = ""
    security_clearance: str = ""
    allowed_scopes: frozenset[str] = frozenset()
    requires_audit_receipt: bool = False

    def is_authorized(
        self,
        granted_roles: set[str] | frozenset[str],
        granted_scopes: set[str] | frozenset[str],
        has_audit_receipt: bool = False,
    ) -> bool:
        """Verify whether credentials satisfy the authority boundary."""
        if self.required_role and self.required_role not in granted_roles:
            return False
        if self.allowed_scopes and not self.allowed_scopes.issubset(granted_scopes):
            return False
        if self.requires_audit_receipt and not has_audit_receipt:
            return False
        return True


@dataclass(frozen=True)
class RoutingBudget:
    """Resource, tolerance, and financial budget for route resolution."""

    max_cost: float = float("inf")
    max_cpu_cores: float = float("inf")
    max_ram_mb: float = float("inf")
    max_gpu_count: float = float("inf")
    max_npu_count: float = float("inf")
    max_energy_joules: float = float("inf")
    max_tolerance: float = float("inf")
    custom_limits: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.max_cost < 0 or self.max_tolerance < 0:
            raise ValueError("Budgets must be non-negative")


@dataclass(frozen=True)
class WorkContract:
    """Typed execution contract for an atomic work step."""

    contract_id: str
    source: str
    target: str
    preconditions: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    cost: float = 1.0
    error_tolerance: float = 0.0
    is_certified: bool = True
    requires_materialization: bool = False
    resources: ResourceRequirement = field(default_factory=ResourceRequirement)
    authority: AuthorityRequirement = field(default_factory=AuthorityRequirement)
    invariants: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.contract_id:
            raise ValueError("contract_id must be non-empty")
        if not self.source or not self.target:
            raise ValueError("source and target must be non-empty")
        if self.cost < 0:
            raise ValueError("cost must be non-negative")
        if self.error_tolerance < 0:
            raise ValueError("error_tolerance must be non-negative")

    def satisfies_preconditions(self, available_conditions: set[str] | frozenset[str]) -> bool:
        """Check if all declared preconditions are satisfied by available conditions."""
        return set(self.preconditions).issubset(available_conditions)
