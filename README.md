# MAPEOGEO v2: Canonical Unit-of-Work Architecture

`MAPEOGEOv2` is the canonical production implementation of the Unit-of-Work (UoW) paradigm, establishing an autonomous, domain-neutral control kernel coupled with modular domain adapters.

---

## Repository Roles & Custody Boundary

| Repository | Role | Custody & Lineage |
|---|---|---|
| **`NB11B/MAPEOGEO`** | **Historical Research & Provenance** | Historical research laboratory, full branch lineage, frozen experiment provenance, and scientific custody archive (frozen at commit `74e51bd`). |
| **`NB11B/MAPEOGEOv2`** | **Canonical Production Architecture** | Clean Git ancestry bootstrapped from initial commit `d664f8c`. Contains canonical, clean-roomed, and qualified components ported under strict provenance tracking. |

---

## Architectural Principles

The repository enforces a strict three-layer architecture:

$$\boxed{\text{UoW Kernel} \longrightarrow \text{Domain Adapters} \longrightarrow \text{Experiments / Qualification}}$$

1. **UoW Kernel Layer (`src/mapeogeo/kernel/`)**:
   - Governed by the formal 9-tuple:
     $$\mathcal{K} = (\mathcal{M}_6, \Omega, \rho, G, D, P, U, C, A)$$
   - Domain-neutral: strictly forbidden from importing any domain adapter (`src/mapeogeo/domains/`).
   - Implements deficiency extraction, prospective planning, utility-driven candidate selection, certification, and autonomous refusal ($\max J_t < \tau_J \implies \texttt{REFUSE}$).

2. **Domain Adapters Layer (`src/mapeogeo/domains/`)**:
   - Modular adapters for specific target fields (`mathematics`, `physics`, `software`).
   - Projects domain-specific problem structures, coordinate spaces, and obligations onto the domain-neutral UoW representation.

3. **Subsystem Layers**:
   - `grammar`: Coordinate spaces and factorization grammars.
   - `graph`: Relational topology and dependency graphs.
   - `routing`: Dispatch contracts, routers, and power control.
   - `proof`: Formal obligation handling and verification certificates.
   - `psmsl`: Operator algebra and representation languages.

---

## Architectural Invariants & Enforcement

Automated architectural tests (`tests/architecture/`) enforce the following constraints on every build:

1. **Directional Isolation**:
   $$\boxed{\texttt{mapeogeo.kernel} \;\not\rightarrow\; \texttt{mapeogeo.domains}}$$
   The kernel must never import, directly or transitively, from domain adapters.

2. **Lexical & Namespace Hygiene**:
   Canonical code in `src/mapeogeo/` must not contain historical campaign generation tokens (`gen2`, `gen8`, `gen12`, `kernel_v3`, `wave_f4`, `experiment.*`).

3. **Qualification Lifecycle**:
   Source qualification in `NB11B/MAPEOGEO` does not automatically grant qualification in `v2`. Ported components must transition through explicit verification gates:
   $$\texttt{UNPORTED} \longrightarrow \texttt{PENDING\_V2\_QUALIFICATION} \longrightarrow \texttt{V2\_QUALIFIED}$$

---

## Provenance Tracking

All components ported into `v2` maintain explicit provenance envelopes:
- Master Manifest: [`artifacts/releases/V2_PROVENANCE_MANIFEST.json`](artifacts/releases/V2_PROVENANCE_MANIFEST.json)
- Per-Component Records: `docs/provenance/components/*.json`
- Component Template: [`docs/provenance/components/template.json`](docs/provenance/components/template.json)

---

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/NB11B/MAPEOGEOv2.git
cd MAPEOGEOv2

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

### Verification & Testing

```bash
# Run pytest test suite (including architectural invariant tests)
pytest

# Run static type checking
mypy

# Run code style and linter checks
ruff check .
```
