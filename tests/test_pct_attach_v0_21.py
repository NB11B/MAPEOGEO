from __future__ import annotations

import json
from pathlib import Path
import pytest

from mapeogeo.pct.attach import (
    PCTAttachment,
    PCTAttachmentRegistry,
    execute_attachment,
    verify_commutation_square,
)

ROOT = Path(__file__).resolve().parents[1]


def test_subject_bound_pct_attachment_requires_valid_target_node():
    # Attempting to create an attachment without a valid target node fails
    with pytest.raises(ValueError, match="Subject node ID is required"):
        PCTAttachment(
            attachment_id="pct:test:invalid",
            subject_node_id="",  # Empty target node
            contract_type="B4_COMMUTATION",
            scope={"domain": "SIMPLICIAL_COMPLEX"},
            validator=lambda: True,
        )


def test_commutation_square_verification():
    # Test commutative square f \circ a == b \circ g
    # e.g., d \circ \alpha == \alpha' \circ \partial
    a = lambda x: 2 * x
    b = lambda x: 3 * x
    f = lambda x: 3 * x
    g = lambda x: 2 * x

    # For all x: f(a(x)) = 3*(2*x) = 6x, b(g(x)) = 3*(2*x) = 6x -> Commutes
    domain_samples = [0, 1, 2, 5, 10, -3]
    assert verify_commutation_square(a, b, f, g, domain_samples) is True

    # Non-commuting maps
    f_bad = lambda x: 3 * x + 1
    assert verify_commutation_square(a, b, f_bad, g, domain_samples) is False


def test_attachment_execution_receipt_ledger():
    attachment = PCTAttachment(
        attachment_id="pct:stokes:simplex_attachment",
        subject_node_id="srcdecl:stokes_simplex_eo",
        contract_type="B4_BOUNDARY_COMMUTING",
        scope={"domain": "SIMPLICIAL_COMPLEX", "coefficient_ring": "RAT"},
        validator=lambda: True,
    )

    receipt = execute_attachment(attachment)
    assert receipt.passed is True
    assert receipt.attachment_id == "pct:stokes:simplex_attachment"
    assert receipt.subject_node_id == "srcdecl:stokes_simplex_eo"
    assert len(receipt.execution_digest) == 64
