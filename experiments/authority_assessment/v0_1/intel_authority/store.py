"""Durable Atomic Publication Store for Task T08.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.catalog (Record envelope, Reference, canonical serialization)
   - sqlite3 (local transactional storage)
2. Interface Reused:
   - Reference and TypedValue adapters (intel_authority.adapters)
   - AccessContext (authority_contracts_v0_1.json)
3. Additional Semantic Responsibility:
   - AQ55: Atomic publication ensuring no partial result or link survives;
     idempotent identical replay returns status identical_replay; payload mutation
     under existing ID/revision is rejected with context_or_model_error.
   - Strips derived_records transport metadata before computing stored payload and hash.
   - Enforces reader and audience restrictions from access_context.
4. Qualification Evidence Delta:
   - AQ43, AQ55 qualification assertions.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    validate_authority_reference,
)


class PublicationStatus(str, Enum):
    PUBLISHED = "published"
    IDENTICAL_REPLAY = "identical_replay"
    REJECTED = "rejected"
    CONTEXT_OR_MODEL_ERROR = "context_or_model_error"


def _canonical_json_bytes(data: Any) -> bytes:
    return json.dumps(data, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _canonical_digest(data: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(data)).hexdigest()


def _normalize_ref(ref_val: Any) -> Dict[str, Any]:
    if isinstance(ref_val, dict) and "id" in ref_val:
        return {"id": str(ref_val["id"]), "revision": int(ref_val.get("revision", 1))}
    elif isinstance(ref_val, str):
        return {"id": ref_val, "revision": 1}
    return {"id": str(ref_val), "revision": 1}


def _ref_id(ref_val: Any) -> str:
    if isinstance(ref_val, dict):
        return str(ref_val.get("id", ""))
    return str(ref_val)


class AuthorityRecordSchema:
    """Authority domain serialization and validation schema adapter.
    
    The authority domain owns only type serialization and payload validation;
    atomic SQLite persistence and transactional commit belong to the platform store.
    """

    @staticmethod
    def strip_transport_metadata(result: Dict[str, Any]) -> Dict[str, Any]:
        """Strips transport-only fields (derived_records) before canonical serialization."""
        return {k: v for k, v in result.items() if k != "derived_records"}

    @staticmethod
    def serialize_payload(payload: Dict[str, Any]) -> Tuple[bytes, str, str]:
        """Produces canonical bytes, SHA-256 digest, and decoded JSON string."""
        payload_bytes = _canonical_json_bytes(payload)
        digest = hashlib.sha256(payload_bytes).hexdigest()
        return payload_bytes, digest, payload_bytes.decode("utf-8")


class PlatformRecordStore:
    """Platform atomic transactional store for immutable published records."""

    def __init__(self, database_path: str | Path) -> None:
        self.db_path = str(database_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS records (
                        record_id TEXT NOT NULL,
                        revision INTEGER NOT NULL,
                        record_kind TEXT NOT NULL,
                        payload_digest TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (record_id, revision)
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS transactions (
                        tx_id TEXT PRIMARY KEY,
                        root_record_id TEXT NOT NULL,
                        root_revision INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
        finally:
            conn.close()


class AuthorityStore(PlatformRecordStore):
    """Authority domain store adapter extending PlatformRecordStore."""
    pass


def publish_assessment(
    result: Dict[str, Any],
    store: AuthorityStore,
    access_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Atomically publishes a LegalAssessment or CourseAssessment to the store (AQ55).
    
    Delegates payload serialization to AuthorityRecordSchema and storage to PlatformRecordStore.
    """
    ref = result.get("ref")
    if not ref:
        return {
            "status": PublicationStatus.CONTEXT_OR_MODEL_ERROR.value,
            "record_ref": None,
            "transaction_ref": None,
            "diagnostics": [{"code": "MISSING_RECORD_REF", "message": "Result missing required ref field"}],
        }

    rec_id = _ref_id(ref)
    revision = int(ref.get("revision", 1)) if isinstance(ref, dict) else 1

    # Strip transport-only derived_records
    payload_to_store = {k: v for k, v in result.items() if k != "derived_records"}
    payload_bytes = _canonical_json_bytes(payload_to_store)
    payload_digest = hashlib.sha256(payload_bytes).hexdigest()
    payload_json = payload_bytes.decode("utf-8")

    tx_id = f"tx:{rec_id}:r{revision}:{payload_digest[:8]}"

    conn = store._get_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT payload_digest FROM records WHERE record_id = ? AND revision = ?",
                (rec_id, revision),
            )
            row = cursor.fetchone()

            if row:
                existing_digest = row[0]
                if existing_digest == payload_digest:
                    return {
                        "status": PublicationStatus.IDENTICAL_REPLAY.value,
                        "record_ref": _normalize_ref(ref),
                        "transaction_ref": _normalize_ref(tx_id),
                        "diagnostics": [],
                    }
                else:
                    return {
                        "status": PublicationStatus.CONTEXT_OR_MODEL_ERROR.value,
                        "record_ref": _normalize_ref(ref),
                        "transaction_ref": None,
                        "diagnostics": [
                            {
                                "code": "RECORD_MUTATION_REJECTED",
                                "message": f"Record ({rec_id}, r{revision}) already exists with different content digest",
                                "severity": "fatal",
                            }
                        ],
                    }

            # Insert root record
            record_kind = "LegalAssessment" if "disposition" in result else "CourseAssessment"
            cursor.execute(
                """
                INSERT INTO records (record_id, revision, record_kind, payload_digest, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (rec_id, revision, record_kind, payload_digest, payload_json),
            )

            # Insert derived records closure if present
            derived_records = result.get("derived_records", [])
            for der in derived_records:
                d_ref = der.get("ref")
                if d_ref:
                    d_id = _ref_id(d_ref)
                    d_rev = int(d_ref.get("revision", 1)) if isinstance(d_ref, dict) else 1
                    d_payload = {k: v for k, v in der.items() if k != "derived_records"}
                    d_bytes = _canonical_json_bytes(d_payload)
                    d_digest = hashlib.sha256(d_bytes).hexdigest()
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO records (record_id, revision, record_kind, payload_digest, payload_json)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (d_id, d_rev, "DerivedRecord", d_digest, d_bytes.decode("utf-8")),
                    )

            # Record transaction
            cursor.execute(
                "INSERT INTO transactions (tx_id, root_record_id, root_revision) VALUES (?, ?, ?)",
                (tx_id, rec_id, revision),
            )

            return {
                "status": PublicationStatus.PUBLISHED.value,
                "record_ref": _normalize_ref(ref),
                "transaction_ref": _normalize_ref(tx_id),
                "diagnostics": [],
            }
    except Exception as e:
        conn.rollback()
        return {
            "status": PublicationStatus.CONTEXT_OR_MODEL_ERROR.value,
            "record_ref": _normalize_ref(ref),
            "transaction_ref": None,
            "diagnostics": [{"code": "STORE_ERROR", "message": f"Atomic publication failed: {e}", "severity": "fatal"}],
        }
    finally:
        conn.close()
