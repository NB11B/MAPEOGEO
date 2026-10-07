"""Permanent Release Test: Pairwise Cross-Domain Isolation Matrix.

Validates that valid artifacts and certificates from one domain cannot satisfy
another domain's certification boundary, proving that identical or compatible
grammar coordinate projections do not confer semantic cross-domain equivalence:

                Math    Physics    Software
Math             -         X          X
Physics          X         -          X
Software         X         X          -
"""

import pytest

from mapeogeo.domains.mathematics.adapter import MathematicsAdapter
from mapeogeo.domains.mathematics.ontology import Theorem, TheoremKind
from mapeogeo.domains.physics.adapter import PhysicsAdapter
from mapeogeo.domains.physics.ontology import EpistemicStatus, PhysicalHypothesis
from mapeogeo.domains.software.adapter import SoftwareAdapter
from mapeogeo.domains.software.ontology import (
    EpistemicSoftwareStatus,
    SoftwareCertificate,
    SoftwareCertificationVerdict,
)


@pytest.fixture
def math_theorem() -> Theorem:
    return Theorem(
        theorem_id="thm:prime_infinitude",
        name="Euclid Prime Infinitude",
        statement="There are infinitely many prime numbers",
        kind=TheoremKind.THEOREM,
        domain="number_theory",
        premises=(),
        conclusion="infinitely_many_primes",
    )


@pytest.fixture
def physics_hypothesis() -> PhysicalHypothesis:
    return PhysicalHypothesis(
        hypothesis_id="hyp:snell_law",
        model_name="Snell Law Refraction",
        latent_state=(1.0, 1.33),
        epistemic_status=EpistemicStatus.MEASUREMENT_SUPPORTED,
        null_space_dimension=0,
        is_source_identified=True,
    )


@pytest.fixture
def software_certificate() -> SoftwareCertificate:
    return SoftwareCertificate(
        certificate_id="cert:sw:raft_node:01",
        machinery_id="sw:pkg:raft_consensus",
        verdict=SoftwareCertificationVerdict.CERTIFIED,
        is_certified=True,
        gates_passed=("GATE_T", "GATE_U", "GATE_S", "GATE_L", "GATE_F"),
        falsifications_checked=("FALSIFIER_RACE",),
        epistemic_status=EpistemicSoftwareStatus.CERTIFIED_CAPABILITY,
        measured_latency_ms=12.5,
        timestamp="2026-10-07T12:00:00Z",
    )


# =========================================================================
# Row 1: Mathematics Artifact presented to other boundaries
# =========================================================================


def test_math_artifact_rejected_by_physics_boundary(math_theorem: Theorem) -> None:
    """Pairwise Cell: Math -> Physics [X].

    A mathematical theorem cannot satisfy a physical certification boundary.
    """
    phys_adapter = PhysicsAdapter()
    result = phys_adapter.certify(math_theorem)
    assert not result.is_certified
    assert "Unsupported physical result type" in (result.failure_reason or "")


def test_math_artifact_rejected_by_software_boundary(math_theorem: Theorem) -> None:
    """Pairwise Cell: Math -> Software [X].

    A mathematical theorem cannot satisfy a software certification boundary.
    """
    sw_adapter = SoftwareAdapter()
    result = sw_adapter.certify(math_theorem)
    assert not result.is_certified
    assert "Unsupported software result type" in (result.failure_reason or "")


# =========================================================================
# Row 2: Physics Artifact presented to other boundaries
# =========================================================================


def test_physics_artifact_rejected_by_math_boundary(
    physics_hypothesis: PhysicalHypothesis,
) -> None:
    """Pairwise Cell: Physics -> Math [X].

    A physical hypothesis cannot satisfy a mathematical proof engine.
    """
    math_adapter = MathematicsAdapter()
    result = math_adapter.certify(physics_hypothesis)
    assert not result.is_certified
    assert "Unsupported mathematical result type" in (result.failure_reason or "")


def test_physics_artifact_rejected_by_software_boundary(
    physics_hypothesis: PhysicalHypothesis,
) -> None:
    """Pairwise Cell: Physics -> Software [X].

    A physical hypothesis cannot satisfy a software certification boundary.
    """
    sw_adapter = SoftwareAdapter()
    result = sw_adapter.certify(physics_hypothesis)
    assert not result.is_certified
    assert "Unsupported software result type" in (result.failure_reason or "")


# =========================================================================
# Row 3: Software Artifact presented to other boundaries
# =========================================================================


def test_software_artifact_rejected_by_math_boundary(
    software_certificate: SoftwareCertificate,
) -> None:
    """Pairwise Cell: Software -> Math [X].

    A software certificate cannot discharge a mathematical proof obligation.
    """
    math_adapter = MathematicsAdapter()
    result = math_adapter.certify(software_certificate)
    assert not result.is_certified
    assert "Unsupported mathematical result type" in (result.failure_reason or "")


def test_software_artifact_rejected_by_physics_boundary(
    software_certificate: SoftwareCertificate,
) -> None:
    """Pairwise Cell: Software -> Physics [X].

    A software certificate cannot satisfy a physical empirical boundary.
    """
    phys_adapter = PhysicsAdapter()
    result = phys_adapter.certify(software_certificate)
    assert not result.is_certified
    assert "Unsupported physical result type" in (result.failure_reason or "")
