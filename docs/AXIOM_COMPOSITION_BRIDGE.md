# Cross-version compositional proof qualification bridge

This is an additive research/provenance note; MAPEOGEO historical experiments and the frozen baseline remain unchanged.

## Provenance

Axiom's CFSG formalization highlights proof decomposition, dependency composition, counterexample-driven repair, and final kernel auditing. Source: https://axiommath.ai/research/the-enormous-theorem-formalized/

## Link to canonical v2

The canonical metadata-consistency prototype is in `NB11B/MAPEOGEOv2` at `tools/proof_obligation_audit.py` on branch `feature/axiom-proof-obligation-audit-20261027`. Export historical theorem nodes using source identity, exact statement, scope, source SHA256, dependency list, and an explicit proof-evidence status. Unresolved references and WOUND states must remain visible. Never promote SOURCE, EO, GEO, FORMAL_LINKED, or a computation certificate to KERNEL_VERIFIED based on heuristics.

The v2 auditor only checks declared metadata. Before consuming an audit in production, independently rerun Lean, verify actual declarations and axioms, bind logs to the exact source revision, and check exact formal specification equivalence.

## Requested v3

No repository named `NB11B/MAPEOGEOv3` was visible through the linked GitHub installation on 2026-10-27. Integration is blocked pending a verifiable repository address. Do not create an unrequested replacement repository.

## Candidate experiments

Compare GEO-guided proof obligation ordering to unassisted dependency ordering with the same theorem targets, prover, wall-clock budgets, and independent kernel certification. Measure target closure, proof search effort, counterexamples discovered, and failed assumption promotions.
