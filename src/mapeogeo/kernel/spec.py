"""Formal 9-Tuple Kernel Specification: K = (M_6, Omega, rho, G, D, P, U, C, A).

Defines the domain-neutral Unit-of-Work control architecture.
"""

from __future__ import annotations

import hashlib
from typing import NamedTuple


class ComponentSpec(NamedTuple):
    symbol: str
    name: str
    formal_signature: str
    invariants: tuple[str, ...]


KERNEL_9_TUPLE: tuple[ComponentSpec, ...] = (
    ComponentSpec(
        symbol="M_6",
        name="Work Grammar",
        formal_signature="(Delta, I, W, sigma, Pi, Gamma, circ)",
        invariants=(
            "Dimension d = 6 strictly invariant (Delta d = 0)",
            "Zero coordinate relabeling",
            "Extension strictly confined to witness coordinate W",
        ),
    ),
    ComponentSpec(
        symbol="Omega",
        name="Obstruction Operator",
        formal_signature="Omega(W) -> {0, 1} x Index",
        invariants=(
            "Monotone obstruction detection",
            "Sound dependency and witness verification",
        ),
    ),
    ComponentSpec(
        symbol="rho",
        name="Repair Operator",
        formal_signature="rho(W, Omega) -> W'",
        invariants=(
            "Strict acyclicity of dependency graphs",
            "Zero regression on valid prior components",
        ),
    ),
    ComponentSpec(
        symbol="G",
        name="Knowledge State",
        formal_signature="G_t = (Signatures_t, Witnesses_t, Machinery_t)",
        invariants=(
            "Monotone capability accumulation",
            "Strict provenance tracing for all admitted machinery",
        ),
    ),
    ComponentSpec(
        symbol="D",
        name="Deficiency Extractor",
        formal_signature="D_t(Q) = Required(Q) \\ ReachableCertifiedWork(Q | G_t)",
        invariants=(
            "Functional deficiency extraction without domain labels",
            "Deficiency Conservation Law: D_t = D_res U D_red U D_unc U D_exp",
        ),
    ),
    ComponentSpec(
        symbol="P",
        name="Prospective Planner",
        formal_signature="P(G_t, M) -> (\\widehat{\\Delta A}_t, \\widehat{D}_{t+1})",
        invariants=(
            "Prospective prediction prior to commitment",
            "Next-limiting deficiency estimation",
        ),
    ),
    ComponentSpec(
        symbol="U",
        name="Utility Model",
        formal_signature="J_t(M) = \\widehat{\\Delta A}_t(M) / Cost(M)",
        invariants=(
            "Cost-efficiency normalization",
            "Marginal utility decay on redundant acquisitions",
        ),
    ),
    ComponentSpec(
        symbol="C",
        name="Certification Boundary",
        formal_signature="C(M, G_t) -> {0, 1} x Certificate",
        invariants=(
            "Fail-closed 4-gate verification",
            "Zero uncertified machinery admission",
        ),
    ),
    ComponentSpec(
        symbol="A",
        name="State Transition & Admission Engine",
        formal_signature="A(G_t, M*) -> G_{t+1} | REFUSE",
        invariants=(
            "Atomic state transition upon certification",
            "Rational refusal: max_M J_t(M) < tau_J ==> REFUSE",
        ),
    ),
)


def compute_kernel_9_tuple_seal() -> str:
    """Compute the deterministic SHA-256 seal of the formal 9-tuple specification."""
    hasher = hashlib.sha256()
    for comp in KERNEL_9_TUPLE:
        hasher.update(comp.symbol.encode())
        hasher.update(comp.name.encode())
        hasher.update(comp.formal_signature.encode())
        for inv in comp.invariants:
            hasher.update(inv.encode())
    return hasher.hexdigest()
