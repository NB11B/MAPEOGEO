# Research Lineage and Historical Provenance

MAPEOGEO v2 is reconstructed from historical research conducted in `NB11B/MAPEOGEO` (frozen at commit `74e51bd`).

---

## 1. Scientific Custody Boundary

The historical repository `NB11B/MAPEOGEO` remains the immutable scientific archive. It retains:
- Full branch history across exploratory lineages.
- Unedited raw experimental notebooks and execution logs.
- Historical qualification manifests for Generative Curricula (Gen 2 through Gen 12).
- Historical UoW Kernel and Work Router iterations (v0.1 through v0.9).

**Governing Custody Rule**: Historical commits and artifacts are never retroactively modified or re-written. All modernization occurs via clean-room extraction into `MAPEOGEOv2`.

---

## 2. Source Branch Lineage Mapping

| Historical Research Branch / Artifact | Conceptual Role | Canonical v2 Destination |
|---|---|---|
| `work-router-lineage` (v0.1–v0.9) | Goal dispatch & routing heuristics | `src/mapeogeo/routing/` |
| `kernel-lineage` (v0.1–v0.9) | State transitions & deficiency tracking | `src/mapeogeo/kernel/` |
| `gen11-autonomous-curriculum` | Theorem proving & mathematics experiments | `src/mapeogeo/domains/mathematics/` |
| `gen12-adaptive-curriculum` | Empirical physics & system identification | `src/mapeogeo/domains/physics/` |
| `software-uow-reproduction` | Clean-room software synthesis reproduction | `src/mapeogeo/domains/software/` |
| `psmsl-substrate` | Phase-space macro-state language | `src/mapeogeo/psmsl/` |
| `graph-relational-core` | Relational dependency networks | `src/mapeogeo/graph/` |
| `proof-obligation-framework` | Proof certificates & verification gates | `src/mapeogeo/proof/` |
