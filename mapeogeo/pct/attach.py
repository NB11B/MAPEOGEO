from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Callable


@dataclass
class PCTReceipt:
    attachment_id: str
    subject_node_id: str
    contract_type: str
    passed: bool
    execution_digest: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "attachment_id": self.attachment_id,
            "subject_node_id": self.subject_node_id,
            "contract_type": self.contract_type,
            "passed": self.passed,
            "execution_digest": self.execution_digest,
            "timestamp": self.timestamp,
        }


@dataclass
class PCTAttachment:
    attachment_id: str
    subject_node_id: str
    contract_type: str
    scope: dict[str, Any]
    validator: Callable[[], bool]

    def __post_init__(self):
        if not self.subject_node_id or not self.subject_node_id.strip():
            raise ValueError("Subject node ID is required and cannot be empty")
        if not self.attachment_id or not self.attachment_id.strip():
            raise ValueError("Attachment ID is required and cannot be empty")


class PCTAttachmentRegistry:
    def __init__(self):
        self._attachments: dict[str, PCTAttachment] = {}

    def register(self, attachment: PCTAttachment) -> None:
        self._attachments[attachment.attachment_id] = attachment

    def get_by_id(self, attachment_id: str) -> PCTAttachment | None:
        return self._attachments.get(attachment_id)

    def get_by_subject(self, subject_node_id: str) -> list[PCTAttachment]:
        return [a for a in self._attachments.values() if a.subject_node_id == subject_node_id]


def verify_commutation_square(
    a: Callable[[Any], Any],
    b: Callable[[Any], Any],
    f: Callable[[Any], Any],
    g: Callable[[Any], Any],
    domain_samples: list[Any],
) -> bool:
    r"""Verifies f \circ a == b \circ g for all sample inputs."""
    for x in domain_samples:
        try:
            lhs = f(a(x))
            rhs = b(g(x))
            if lhs != rhs:
                return False
        except Exception:
            return False
    return True


def execute_attachment(attachment: PCTAttachment) -> PCTReceipt:
    try:
        passed = bool(attachment.validator())
    except Exception:
        passed = False

    payload = f"{attachment.attachment_id}:{attachment.subject_node_id}:{attachment.contract_type}:{passed}:{json.dumps(attachment.scope, sort_keys=True)}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    ts = datetime.now(timezone.utc).isoformat()

    return PCTReceipt(
        attachment_id=attachment.attachment_id,
        subject_node_id=attachment.subject_node_id,
        contract_type=attachment.contract_type,
        passed=passed,
        execution_digest=digest,
        timestamp=ts,
    )
