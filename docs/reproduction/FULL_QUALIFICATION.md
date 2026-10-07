# Full Release Qualification Reproduction Guide

This guide details the procedure for reproducing the end-to-end qualification verification of MAPEOGEO v2.

---

## 1. Environment Setup

Ensure clean Python 3.11+ environment:

```powershell
git checkout v2.0.0-rc1
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

---

## 2. Automated Static Verification

Run linting, formatting, and static typing:

```powershell
# Lint check
python -m ruff check src tests docs scripts

# Format check
python -m ruff format --check src tests docs scripts

# Strict static type check
python -m mypy src tests
```

Expected result: Zero errors across all checks.

---

## 3. Comprehensive Test Suite

Execute the complete pytest test suite:

```powershell
pytest -v
```

Expected result: 124 passing tests, 0 failures, 0 skipped.

---

## 4. Deterministic Replay Verification

Run the independent subprocess replay verification script:

```powershell
python scripts/verify_deterministic_replay.py
```

Expected output:
```text
Run 1 Hash: 0af7ae9ce06513ff2d6dd87e61a9554406d22eb807ea498e25cae28caeac7cfa
Run 2 Hash: 0af7ae9ce06513ff2d6dd87e61a9554406d22eb807ea498e25cae28caeac7cfa
DETERMINISTIC REPLAY VERIFIED: H(R1) == H(R2)
```

---

## 5. Provenance & Component Integrity Audit

Run the provenance manifest audit script:

```powershell
python scripts/audit_provenance.py
```

Expected output:
```text
Total files: 62
Matched: 62
Orphans: 0
Missing: 0
PROVENANCE AUDIT PASSED.
```
