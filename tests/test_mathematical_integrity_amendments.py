"""Integrity checks for explicit corrections to previously published identities."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AMENDMENTS = ROOT / "formal" / "mathematical_integrity_amendments_v0_20.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _manifest() -> dict:
    return json.loads(AMENDMENTS.read_text(encoding="utf-8"))


def test_amendment_manifest_has_unique_stable_identities() -> None:
    data = _manifest()
    assert data["schema_version"] == "v0.20-mathematical-integrity-amendments"
    amendments = data["amendments"]
    assert len(amendments) == 16
    ids = [entry["amendment_id"] for entry in amendments]
    assert len(ids) == len(set(ids))

    for entry in amendments:
        assert entry["status"] in {"ACTIVE_AMENDMENT", "REJECTED"}
        assert entry["reason"]
        assert entry["evidence_scope"]
        old = entry["historical_identity"]
        new = entry["corrected_identity"]
        assert old != new
        assert SHA256.fullmatch(old["identity_sha256"])
        assert SHA256.fullmatch(new["identity_sha256"])
        for identity in (old, new):
            payload = {key: value for key, value in identity.items() if key != "identity_sha256"}
            expected = hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            ).hexdigest()
            assert identity["identity_sha256"] == expected


def test_manifest_freezes_four_statement_corrections() -> None:
    data = _manifest()
    entries = {
        entry["corrected_identity"].get("subject_id"): entry
        for entry in data["amendments"]
        if entry["corrected_identity"].get("kind") == "SOURCE_STATEMENT"
    }
    expected = {
        "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:THEOREM:5.2": (
            "96ae8f6938c192f560301df371d22542d7a82526d52bdc08166d1a96c524ee21",
            "a9eab681d425833b6d71c51dc1c336e219e1542c4ec746aac41f4ae3b44f7e77",
        ),
        "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:LEMMA:5.10": (
            "dddf8a062a54471fd53aa5c1cd3e3801840f48edd1274f2af9099a2315b5a311",
            "7c35e44d42045ec3635341883034ba669b17c6191e2630229d9f86bc96ece4da",
        ),
        "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:THEOREM:7.4": (
            "95dc59c607d97a7d76cbb8ccaa1a81a0ee4a06876f733398558f090feb70fa7a",
            "65e2fc0485b7164b8a39f1aebf40945c5eb8b38d84fcae5f38f23f710eba3dac",
        ),
        "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:THEOREM:8.2": (
            "fb70ab0244e99ddf8abf411aafc8ac6d26c7c440b48f876e53fb4a71f3590cc7",
            "14e299755838ac421a9e8754073a8a735399a2deb4547a6e97daf35699805dc1",
        ),
    }
    assert set(expected) <= set(entries)
    for subject_id, (old_hash, new_hash) in expected.items():
        entry = entries[subject_id]
        assert entry["status"] == "ACTIVE_AMENDMENT"
        assert entry["historical_identity"]["statement_sha256"] == old_hash
        assert entry["corrected_identity"]["statement_sha256"] == new_hash


def test_manifest_rejects_false_axler_alignment_and_corrects_dolbeault_ref() -> None:
    amendments = _manifest()["amendments"]
    axler = next(a for a in amendments if a["amendment_id"].endswith("axler-eigenvector-alignment"))
    assert axler["status"] == "REJECTED"
    assert axler["wound_id"].startswith("wound:")
    assert axler["historical_edge_id"].startswith("e:rep:")
    assert axler["active_policy"] == "PRESERVE_WOUND_EXCLUDE_FROM_ACTIVE_SEMANTIC_GRAPH"
    assert axler["historical_identity"]["source_id"] == "srcdecl:axler:definition:5_8"
    assert axler["historical_identity"]["semantic_status"] == "CROSS_SOURCE_SAME"
    assert axler["historical_identity"]["source_statement_sha256"] == "09fee4067b558b9cf2a096ffeb0ef468aeff193fba12a20c0f65a5d358940cbc"
    assert axler["corrected_identity"]["semantic_status"] == "REJECTED"

    dolbeault = next(a for a in amendments if a["amendment_id"].endswith("dolbeault-reference"))
    assert dolbeault["status"] == "ACTIVE_AMENDMENT"
    assert dolbeault["historical_identity"]["structural_reference"].endswith("DEFINITION:2.2")
    assert dolbeault["corrected_identity"]["structural_reference"].endswith("THEOREM:2.2")
    assert dolbeault["historical_identity"]["subject_statement_sha256"] == "07a2f1ad2438a8959f74eb84dea91ee0ddf43d9e0087e72d439d30bc850e4d76"
    assert dolbeault["corrected_identity"]["target_statement_sha256"] == "78de592fcbbb8053e56ce225096d702b57170d4feded22589fdfb2f2af2d2412"


def test_manifest_binds_all_additional_statement_repairs_and_alignment_policies() -> None:
    amendments = _manifest()["amendments"]
    statement_entries = {
        item["corrected_identity"].get("subject_id"): item
        for item in amendments
        if item["corrected_identity"].get("kind") == "SOURCE_STATEMENT"
    }
    expected = {
        "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:DEFINITION:2.1": ("a9459e3fad6ce45e93a2ae7680370f06b722713a5a05a6c3b26ad558aadb4ca5", "9966c2d7c3ee1e3433ff582aadf6d494063956b53a0f2e03a0435a387792cf63"),
        "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:DEFINITION:3.4": ("3994a5074d8f6ea2a72a41f33c5965ea5724d01c6a09d45ca55b255dd06828c9", "68fb58f702d0b9a0c54c35748bc1737151fc0c7843b10c3e6cc2b63cdf049800"),
        "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:THEOREM:5.3": ("1a4395f086b83fd3850a2506d83f5d8fdb6c107b8371cb78205bedbb2c99af78", "3f8ff49b4849c4ab74edfdc1bdb10e0ed34d26e91d706c2864afe6b8c8b52bdf"),
        "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:THEOREM:5.12": ("bc7cd6740122b5d201dfb94494a0fee056c6f5d288bcc0040673f3fd2c5d1bb6", "7e88df1b6bbc7ddb1717d3ed8791aa3bd38ea7c5d37867e35e3a4533fc60ec25"),
        "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:THEOREM:6.8": ("337c874e953f43452c62a25f550e7dfd8554d35c57574fb9cffe943642103794", "0ed4477f39cace42d84da3a181f875910a21deea9fee34f3c7eaf062ec1b8181"),
        "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:DEFINITION:9.6": ("eebce280268c37a780fa37304cc0402dce944cd6267f26ff2c383fdb8db35e3f", "3133fb203fda2c0531fb85739864cc4ae217e724fb8f227edb2bb7a2a2dabb92"),
        "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:DEFINITION:9.7": ("400b717757ab374fbc9a2841b1a61ea57cdb9ea545ecf126738566fab8d21086", "336b01760e11ebe24619ab958bfc23ce4224e9984f977d63bca8b85491ccf4f7"),
    }
    for subject_id, (old_hash, new_hash) in expected.items():
        entry = statement_entries[subject_id]
        assert entry["historical_identity"]["statement_sha256"] == old_hash
        assert entry["corrected_identity"]["statement_sha256"] == new_hash

    duplicate = next(item for item in amendments if item["amendment_id"].endswith("duplicate-axler-6-55-alignment"))
    assert duplicate["historical_identity"]["source_statement_sha256"] == "f99edef93de87e14400af3be4215b9b07b857f325c7bb1a50536c9f72c632532"
    assert duplicate["historical_identity"]["occurrence_count"] == 2
    assert duplicate["corrected_identity"]["occurrence_count"] == 1

    conflicts = next(item for item in amendments if item["amendment_id"].endswith("global-relation-meet"))
    assert conflicts["historical_identity"]["conflicting_pair_count"] == 33
    assert conflicts["corrected_identity"]["ordering"] == ["RELATED_TO", "SCOPED_OVERLAP", "SAME_SEMANTICS"]
