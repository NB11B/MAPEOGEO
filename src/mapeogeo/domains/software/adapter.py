"""Canonical Software Domain Adapter for the UoW Architecture.

Governing rule:
    Software adapts to the kernel; the kernel does not adapt to software.
    source code exists != software capability certified.

Binds software engineering requirements, architecture graphs, and interface
contracts to the domain-neutral UoW kernel without modifying shared substrates.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, overload

from mapeogeo.domains.software.certification import SoftwareCertificationBoundary
from mapeogeo.domains.software.grammar_mapping import (
    FactoringAuditRecord,
    SoftwareGrammarFactorer,
)
from mapeogeo.domains.software.ontology import (
    SoftwareCertificate,
    SoftwareEvidence,
    SoftwareMachinery,
    SoftwareObjective,
    SoftwareRequirement,
)
from mapeogeo.grammar.work_grammar import WorkGrammar
from mapeogeo.kernel.certification import CertificationBoundary, CertificationResult
from mapeogeo.kernel.deficiency import (
    DeficiencyDistribution,
    DeficiencyExtractor,
    DeficiencyRecord,
)
from mapeogeo.kernel.machinery import MachineryCandidate, MachineryNode
from mapeogeo.kernel.state import KnowledgeState
from mapeogeo.routing.contracts import WorkContract


class SoftwareAdapter:
    """Canonical domain adapter binding software systems engineering to the UoW Kernel."""

    def __init__(
        self,
        grammar: WorkGrammar | None = None,
        certification_boundary: CertificationBoundary | None = None,
        software_certifier: SoftwareCertificationBoundary | None = None,
    ) -> None:
        self.grammar = grammar or WorkGrammar(base_alphabet_size=58)
        self.certification_boundary = certification_boundary or CertificationBoundary(
            grammar=self.grammar
        )
        self.software_certifier = software_certifier or SoftwareCertificationBoundary()
        self.factorer = SoftwareGrammarFactorer(grammar=self.grammar)
        self.extractor = DeficiencyExtractor()

    def register_witness(self, witness_id: str, symbol: str, role: str) -> None:
        """Register a software witness certificate symbol into the work grammar."""
        self.grammar.register_witness(witness_id, symbol, role)

    def required_work(
        self,
        work: SoftwareRequirement | SoftwareObjective | Mapping[str, Any],
    ) -> WorkContract:
        """Translate a software requirement or objective into a domain-neutral WorkContract."""
        if isinstance(work, SoftwareRequirement):
            req_id = work.requirement_id
            sigs = work.required_signatures
            weight = work.weight
            domain = work.domain
            latency_bound = work.contracts.latency_bound_ms
        elif isinstance(work, SoftwareObjective):
            req_id = work.objective_id
            sigs = tuple(sig for req in work.requirements for sig in req.required_signatures)
            weight = sum(req.weight for req in work.requirements)
            domain = work.system_domain
            latency_bound = work.sla_latency_target_ms
        elif isinstance(work, Mapping):
            req_id = str(work.get("id") or work.get("requirement_id", "REQ-SW-000"))
            sigs = tuple(str(s) for s in work.get("required_signatures", ()))
            weight = float(work.get("weight", 10.0))
            domain = str(work.get("domain", "Software Systems"))
            contracts = work.get("contracts") or work.get("verification_contracts") or {}
            if isinstance(contracts, Mapping):
                latency_bound = float(contracts.get("latency_bound_ms", 100.0))
            else:
                latency_bound = 100.0
        else:
            req_id = "REQ-SW-UNKNOWN"
            sigs = ()
            weight = 10.0
            domain = "Software Systems"
            latency_bound = 100.0

        preconditions = tuple(f"has_capability({sig})" for sig in sigs)
        postconditions = (f"software_requirement_satisfied({req_id})",)

        return WorkContract(
            contract_id=f"work:sw:{req_id}",
            source=f"sw:requirement:{req_id}:unfulfilled",
            target=f"sw:requirement:{req_id}:fulfilled",
            preconditions=preconditions,
            postconditions=postconditions,
            cost=round(weight, 3),
            error_tolerance=latency_bound / 1000.0,
            is_certified=False,
            metadata={"domain": domain, "weight": weight, "latency_bound_ms": latency_bound},
        )

    def candidate_machinery(
        self,
        deficiency: DeficiencyDistribution | DeficiencyRecord | Mapping[str, Any] | Any,
        state: KnowledgeState,
    ) -> list[MachineryNode]:
        """Propose candidate machinery nodes to eliminate detected software deficiencies."""
        if hasattr(deficiency, "signature_frequency") and isinstance(
            deficiency.signature_frequency, dict
        ):
            missing = set(deficiency.signature_frequency.keys())
        elif hasattr(deficiency, "missing"):
            missing = set(deficiency.missing)
        elif hasattr(deficiency, "missing_capabilities"):
            missing = set(deficiency.missing_capabilities)
        elif isinstance(deficiency, Mapping):
            sig_freq = deficiency.get("signature_frequency")
            missing = set(
                deficiency.get("missing_capabilities")
                or deficiency.get("missing")
                or (sig_freq.keys() if isinstance(sig_freq, dict) else [])
            )
        else:
            missing = set()

        candidates: list[MachineryNode] = []
        for sig in sorted(missing):
            node_id = f"mach:sw:{sig.lower()}"
            if any(n.node_id == node_id for n in state.certified_nodes):
                continue
            candidates.append(
                MachineryNode(
                    node_id=node_id,
                    provided_signatures=(sig,),
                    dependencies=(),
                    witness_id=None,
                    metadata={"source_signature": sig, "domain": "software"},
                )
            )

        return candidates

    def factor_grammar(
        self,
        work: Any,
        witness_id: str | None = None,
        witness_symbol: str | None = None,
        witness_role: str | None = None,
    ) -> FactoringAuditRecord:
        """Factor software work into literal 6D coordinates and audit for drift."""
        if isinstance(work, SoftwareMachinery):
            work_id = work.machinery_id
            expr = f"{work.name} \\circ {work.witness_id or 'circ'}"
            witness_id = witness_id or work.witness_id
            witness_symbol = witness_symbol or work.witness_symbol
            witness_role = witness_role or work.name
        elif isinstance(work, SoftwareRequirement):
            work_id = work.requirement_id
            expr = f"{work.title} \\to {work.contracts.type_contract}"
        elif isinstance(work, Mapping):
            work_id = str(work.get("id") or work.get("machinery_id", "work:sw:obj"))
            expr = str(work.get("grammar_factorization") or work.get("expression", ""))
            witness_id = witness_id or work.get("witness_id")
            witness_symbol = witness_symbol or work.get("witness_certificate")
            witness_role = witness_role or work.get("name")
        else:
            work_id = getattr(work, "node_id", "work:sw:obj")
            expr = getattr(work, "formal_statement", str(work))

        return self.factorer.factor_software_work(
            work_id=work_id,
            expression=expr,
            witness_id=witness_id,
            witness_symbol=witness_symbol,
            witness_role=witness_role,
        )

    @overload
    def certify(
        self,
        result: SoftwareMachinery,
        evidence: SoftwareEvidence | None = ...,
        requirements: Sequence[SoftwareRequirement] = ...,
        execution_authority: str = ...,
        current_state: KnowledgeState | None = ...,
    ) -> SoftwareCertificate: ...

    @overload
    def certify(
        self,
        result: MachineryCandidate | Mapping[str, Any] | Any,
        evidence: SoftwareEvidence | None = ...,
        requirements: Sequence[SoftwareRequirement] = ...,
        execution_authority: str = ...,
        current_state: KnowledgeState | None = ...,
    ) -> SoftwareCertificate | CertificationResult: ...

    def certify(
        self,
        result: Any,
        evidence: SoftwareEvidence | None = None,
        requirements: Sequence[SoftwareRequirement] = (),
        execution_authority: str = "STANDARD",
        current_state: KnowledgeState | None = None,
    ) -> SoftwareCertificate | CertificationResult:
        """Certify software work via 5-gate software boundary or 4-gate kernel boundary."""
        # 1. Software machinery package empirical verification
        if isinstance(result, SoftwareMachinery):
            return self.software_certifier.certify_software(
                machinery=result,
                evidence=evidence,
                requirements=requirements,
                execution_authority=execution_authority,
            )

        # 2. Kernel machinery candidate admission
        if isinstance(result, MachineryCandidate):
            state = current_state or KnowledgeState.initial()
            return self.certification_boundary.certify_candidate(result, state)

        # 3. Dict-based candidate adapter
        if isinstance(result, dict):
            cand_id = result.get("candidate_id") or result.get("id") or "cand:sw:dict"
            sigs = tuple(result.get("provided_signatures") or result.get("signatures") or ())
            cost = float(result.get("cost", 10.0))
            nodes_data = result.get("nodes") or result.get("machinery_nodes") or ()
            nodes: list[MachineryNode] = []
            for nd in nodes_data:
                if isinstance(nd, MachineryNode):
                    nodes.append(nd)
                elif isinstance(nd, dict):
                    nd_sigs = tuple(nd.get("provided_signatures") or nd.get("capabilities", sigs))
                    nodes.append(
                        MachineryNode(
                            node_id=nd.get("node_id") or nd.get("id", "node:0"),
                            provided_signatures=nd_sigs,
                            dependencies=tuple(nd.get("dependencies", ())),
                            witness_id=nd.get("witness_id"),
                        )
                    )
            witness_ids = tuple(result.get("witness_ids", ()))
            candidate = MachineryCandidate(
                candidate_id=cand_id,
                provided_signatures=sigs if sigs else ("SIG_SW_DEFAULT",),
                cost=cost if cost > 0 else 1.0,
                nodes=tuple(nodes),
                witness_ids=witness_ids,
            )
            state = current_state or KnowledgeState.initial()
            return self.certification_boundary.certify_candidate(candidate, state)

        return CertificationResult(
            is_certified=False,
            certificate_id="",
            gates_passed=(),
            failure_reason="Unsupported software result type",
        )

    def measure_ability(
        self,
        work: SoftwareRequirement | SoftwareObjective | Mapping[str, Any],
        state: KnowledgeState,
    ) -> float:
        """Measure solve capability for a software requirement given current certified state."""
        if isinstance(work, SoftwareRequirement):
            sigs = work.required_signatures
            weight = work.weight
        elif isinstance(work, SoftwareObjective):
            sigs = tuple(sig for req in work.requirements for sig in req.required_signatures)
            weight = sum(req.weight for req in work.requirements)
        elif isinstance(work, Mapping):
            sigs = tuple(str(s) for s in work.get("required_signatures", ()))
            weight = float(work.get("weight", 10.0))
        else:
            return 0.0

        if not sigs:
            return 0.0

        satisfied = sum(1 for sig in sigs if sig in state.signatures)
        ratio = satisfied / len(sigs)
        return round(ratio * weight, 3)
