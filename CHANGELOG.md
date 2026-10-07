# Changelog

All notable changes to `MAPEOGEOv2` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0.dev1] - 2026-10-07

### Added
- Wave 2: Bootstrapped canonical repository skeleton under `src/mapeogeo/`.
- Architectural AST invariant tests enforcing kernel, grammar, and graph domain-neutrality.
- Lexical and historical namespace hygiene enforcement prohibiting generation tokens in canonical source.
- Master provenance manifest `artifacts/releases/V2_PROVENANCE_MANIFEST.json`.
- Per-component provenance records under `docs/provenance/components/` initialized with `PENDING_V2_QUALIFICATION`.
- Infrastructure tooling: `pyproject.toml`, Ruff, mypy, pytest, and deterministic JSON / SHA-256 hashing tools.
- Preserved historical scientific provenance archive in `NB11B/MAPEOGEO` frozen at commit `74e51bd`.
