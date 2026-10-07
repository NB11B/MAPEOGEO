"""Canonical Mathematics Domain Adapter for the UoW Architecture.

Governing rule:
    Mathematics adapts to the kernel; the kernel does not adapt to mathematics.

Translates mathematical problem structures, theorems, and proofs into
generic UoW kernel abstractions without recreating kernel or proof infrastructure.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from mapeogeo.domains.mathematics.grammar_mapping import (
    FactoringAuditRecord,
    MathematicalGrammarFactorer,
)
from mapeogeo.domains.mathematics.obligations import MathematicalProofObligation
from mapeogeo.domains.mathematics.ontology import (
    MathematicalProblem,
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
from mapeogeo.proof.contracts import ProofCertificate, ProofStatus
from mapeogeo.proof.verifier import ProofEngine
from mapeogeo.routing.contracts import WorkContract


class MathematicsAdapter:
    """Canonical domain adapter binding formal mathematics to the UoW kernel."""

    def __init__(
        self,
        grammar: WorkGrammar | None = None,
        proof_engine: ProofEngine | None = None,
        certification_boundary: CertificationBoundary | None = None,
    ) -> None:
        self.grammar = grammar or WorkGrammar(base_alphabet_size=58)
        self.factorer = MathematicalGrammarFactorer(self.grammar)
        self.proof_engine = proof_engine or ProofEngine()
        self.certification_boundary = certification_boundary or CertificationBoundary(
            grammar=self.grammar
        )
        self.extractor = DeficiencyExtractor()

    def required_work(
        self,
        problem: MathematicalProblem | Mapping[str, Any],
    ) -> WorkContract:
        """Translate a mathematical problem into a domain-neutral WorkContract."""
        if isinstance(problem, MathematicalProblem):
            pid = problem.problem_id
            sigs = problem.required_signatures
            cost = round(problem.difficulty * problem.structural_distance, 3)
            domain = problem.domain
            weight = problem.weight
        else:
            pid = str(problem.get("id") or problem.get("problem_id", "Q-UNKNOWN"))
            sigs = tuple(str(s) for s in problem.get("required_signatures", ()))
            diff = float(problem.get("difficulty", 1.0))
            dist = float(problem.get("structural_distance", 1.0))
            cost = round(diff * dist, 3)
            domain = str(problem.get("domain", "Mathematics"))
            weight = float(problem.get("weight", 1.0))

        preconds = tuple(f"has_signature({s})" for s in sigs)
        postconds = (f"solved({pid})",)

        return WorkContract(
            contract_id=f"work:math:{pid}",
            source=f"math:problem:{pid}:unsolved",
            target=f"math:problem:{pid}:solved",
            preconditions=preconds,
            postconditions=postconds,
            cost=cost,
            error_tolerance=0.0,  # Exact mathematical rigor
            is_certified=False,
            metadata={"domain": domain, "weight": weight},
        )

    def candidate_machinery(
        self,
        deficiency: DeficiencyDistribution | DeficiencyRecord | Mapping[str, Any] | Any,
        state: KnowledgeState,
    ) -> list[MachineryNode]:
        """Propose candidate machinery nodes to eliminate detected deficiencies."""
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
            node_id = f"mach:math:{sig.lower()}"
            if any(n.node_id == node_id for n in state.certified_nodes):
                continue
            candidates.append(
                MachineryNode(
                    node_id=node_id,
                    provided_signatures=(sig,),
                    dependencies=(),
                    witness_id=None,
                    metadata={"source_signature": sig},
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
        """Factor a mathematical work item into literal frozen 6D coordinates."""
        if isinstance(work, str):
            work_id = f"work:expr:{abs(hash(work)) % 10000}"
            expr = work
        elif isinstance(work, dict):
            work_id = str(work.get("id", "work:dict"))
            expr = str(work.get("grammar_factorization") or work.get("expression", ""))
            witness_id = witness_id or work.get("witness_id")
            witness_symbol = witness_symbol or work.get("witness_certificate")
            witness_role = witness_role or work.get("name")
        else:
            work_id = getattr(work, "node_id", "work:obj")
            expr = getattr(work, "formal_statement", str(work))

        return self.factorer.factor_mathematical_work(
            work_id=work_id,
            expression=expr,
            witness_id=witness_id,
            witness_symbol=witness_symbol,
            witness_role=witness_role,
        )

    def certify(
        self,
        result: Any,
        proof_engine: ProofEngine | None = None,
        current_state: KnowledgeState | None = None,
    ) -> CertificationResult:
        """Certify mathematical work via ProofEngine replay and Kernel boundary."""
        engine = proof_engine or self.proof_engine

        # If a MathematicalProofObligation is passed, discharge it through ProofEngine
        if isinstance(result, MathematicalProofObligation):
            generic_ob = result.to_generic_obligation()
            generic_ev = result.to_generic_evidence()
            cert: ProofCertificate
            cert, _ = engine.discharge_obligation(
                obligation=generic_ob,
                evidence=generic_ev,
                verifier_semantic_id=result.verifier_semantic_id,
            )
            passed = cert.status == ProofStatus.FORMALLY_CHECKED and cert.admitted
            return CertificationResult(
                is_certified=passed,
                certificate_id=cert.certificate_id if passed else "",
                gates_passed=("syntax", "invariant", "proof_replay") if passed else (),
                failure_reason=None if passed else "Proof replay rejected",
            )

        if isinstance(result, MachineryCandidate):
            state = current_state or KnowledgeState.initial()
            return self.certification_boundary.certify_candidate(result, state)

        # If already a package dict or candidate dict, evaluate via 4-gate boundary
        if isinstance(result, dict):
            cand_id = result.get("candidate_id") or result.get("id") or "cand:math:dict"
            sigs = tuple(result.get("provided_signatures") or result.get("capabilities") or ())
            cost = float(result.get("cost", 10.0))
            nodes_data = result.get("nodes") or result.get("machinery_nodes") or ()
            nodes: list[MachineryNode] = []
            for nd in nodes_data:
                if isinstance(nd, MachineryNode):
                    nodes.append(nd)
                elif isinstance(nd, dict):
                    nd_sigs = tuple(nd.get("provided_signatures") or nd.get("capabilities", ()))
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
                provided_signatures=sigs if sigs else ("SIG_DEFAULT",),
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
            failure_reason="Unsupported mathematical result type",
        )

    def measure_ability(
        self,
        problem: MathematicalProblem | Mapping[str, Any],
        state: KnowledgeState,
    ) -> float:
        """Measure solve capability for a problem given current certified state."""
        if isinstance(problem, MathematicalProblem):
            sigs = problem.required_signatures
            base = problem.base_ability_pct
        else:
            sigs = tuple(problem.get("required_signatures", ()))
            base = float(problem.get("base_ability_pct", 0.0))

        if not sigs:
            return 1.0

        covered = sum(1 for s in sigs if s in state.signatures)
        if covered == len(sigs):
            return 1.0
        return base + (covered / len(sigs)) * (1.0 - base) * 0.5
