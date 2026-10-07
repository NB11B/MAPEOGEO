"""Canonical Physics Domain Adapter for the UoW Architecture.

Governing rule:
    Physics adapts to the kernel; the kernel does not adapt to physics.
    Mathematical admissibility != physical establishment.
    Effect observed != source identified.

Binds physical inverse problems, sensor observations, and empirical certification
to the domain-neutral UoW kernel without modifying shared substrates.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, overload

from mapeogeo.domains.physics.certification import PhysicalCertificationBoundary
from mapeogeo.domains.physics.grammar_mapping import (
    FactoringAuditRecord,
    PhysicalGrammarFactorer,
)
from mapeogeo.domains.physics.latent_inference import (
    LatentGeneratorInverter,
    LatentInferenceResult,
)
from mapeogeo.domains.physics.ontology import (
    MeasuredObservation,
    PhysicalCertificate,
    PhysicalConstraint,
    PhysicalHypothesis,
    PhysicalObjective,
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


class PhysicsAdapter:
    """Canonical domain adapter binding empirical physics to the UoW kernel."""

    def __init__(
        self,
        grammar: WorkGrammar | None = None,
        certification_boundary: CertificationBoundary | None = None,
        physical_certifier: PhysicalCertificationBoundary | None = None,
    ) -> None:
        self.grammar = grammar or WorkGrammar(base_alphabet_size=58)
        self.factorer = PhysicalGrammarFactorer(self.grammar)
        self.inverter = LatentGeneratorInverter()
        self.physical_certifier = physical_certifier or PhysicalCertificationBoundary()
        self.certification_boundary = certification_boundary or CertificationBoundary(
            grammar=self.grammar
        )
        self.extractor = DeficiencyExtractor()
        self._stored_observations: list[MeasuredObservation] = []

    def record_observation(self, observation: MeasuredObservation) -> None:
        """Register a new empirical measurement."""
        self._stored_observations.append(observation)

    def observations(self, state: KnowledgeState | None = None) -> tuple[MeasuredObservation, ...]:
        """Return available sensor measurements."""
        return tuple(self._stored_observations)

    def required_work(
        self,
        objective: PhysicalObjective | Mapping[str, Any],
    ) -> WorkContract:
        """Translate a physical objective into a domain-neutral WorkContract."""
        if isinstance(objective, PhysicalObjective):
            obj_id = objective.objective_id
            sigs = objective.required_signatures
            cost = round(objective.difficulty * objective.structural_distance, 3)
            domain = objective.domain
            weight = objective.weight
            tol = 1e-4
        else:
            obj_id = str(objective.get("id") or objective.get("objective_id", "PHYS-001"))
            sigs = tuple(str(s) for s in objective.get("required_signatures", ()))
            diff = float(objective.get("difficulty", 1.0))
            dist = float(objective.get("structural_distance", 1.0))
            cost = round(diff * dist, 3)
            domain = str(objective.get("domain", "Physics"))
            weight = float(objective.get("weight", 1.0))
            tol = float(objective.get("tolerance", 1e-4))

        preconds = tuple(f"has_signature({s})" for s in sigs)
        postconds = (f"physically_reconstructed({obj_id})",)

        return WorkContract(
            contract_id=f"work:phys:{obj_id}",
            source=f"physics:objective:{obj_id}:unobserved",
            target=f"physics:objective:{obj_id}:empirically_established",
            preconditions=preconds,
            postconditions=postconds,
            cost=cost,
            error_tolerance=tol,
            is_certified=False,
            metadata={"domain": domain, "weight": weight},
        )

    def candidate_machinery(
        self,
        deficiency: DeficiencyDistribution | DeficiencyRecord | Mapping[str, Any] | Any,
        state: KnowledgeState,
    ) -> list[MachineryNode]:
        """Propose candidate machinery nodes to eliminate detected physical deficiencies."""
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
            node_id = f"mach:phys:{sig.lower()}"
            if any(n.node_id == node_id for n in state.certified_nodes):
                continue
            candidates.append(
                MachineryNode(
                    node_id=node_id,
                    provided_signatures=(sig,),
                    dependencies=(),
                    witness_id=None,
                    metadata={"source_signature": sig, "domain": "physics"},
                )
            )

        return candidates

    def infer_latent_generator(
        self,
        observations: Sequence[MeasuredObservation],
    ) -> LatentInferenceResult:
        """Infer latent generator constraints from physical sensor measurements."""
        return self.inverter.invert_observations(observations)

    def factor_grammar(
        self,
        work: Any,
        witness_id: str | None = None,
        witness_symbol: str | None = None,
        witness_role: str | None = None,
    ) -> FactoringAuditRecord:
        """Factor physical work into literal frozen 6D coordinates."""
        if isinstance(work, str):
            work_id = f"work:phys:{abs(hash(work)) % 10000}"
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

        return self.factorer.factor_physical_work(
            work_id=work_id,
            expression=expr,
            witness_id=witness_id,
            witness_symbol=witness_symbol,
            witness_role=witness_role,
        )

    @overload
    def certify(
        self,
        result: PhysicalHypothesis,
        observations: Sequence[MeasuredObservation] = ...,
        constraints: Sequence[PhysicalConstraint] = ...,
        repeat_observations: Sequence[MeasuredObservation] | None = ...,
        current_state: KnowledgeState | None = ...,
    ) -> PhysicalCertificate: ...

    @overload
    def certify(
        self,
        result: MachineryCandidate | Mapping[str, Any] | Any,
        observations: Sequence[MeasuredObservation] = ...,
        constraints: Sequence[PhysicalConstraint] = ...,
        repeat_observations: Sequence[MeasuredObservation] | None = ...,
        current_state: KnowledgeState | None = ...,
    ) -> PhysicalCertificate | CertificationResult: ...

    def certify(
        self,
        result: Any,
        observations: Sequence[MeasuredObservation] = (),
        constraints: Sequence[PhysicalConstraint] = (),
        repeat_observations: Sequence[MeasuredObservation] | None = None,
        current_state: KnowledgeState | None = None,
    ) -> PhysicalCertificate | CertificationResult:
        """Certify physical work via 5-gate physical boundary or 4-gate kernel boundary."""
        # 1. Physical hypothesis empirical certification
        if isinstance(result, PhysicalHypothesis):
            obs_to_use = observations or self.observations()
            return self.physical_certifier.certify_hypothesis(
                hypothesis=result,
                observations=obs_to_use,
                constraints=constraints,
                repeat_observations=repeat_observations,
            )

        # 2. Kernel machinery candidate admission
        if isinstance(result, MachineryCandidate):
            state = current_state or KnowledgeState.initial()
            return self.certification_boundary.certify_candidate(result, state)

        # 3. Dict-based candidate adapter
        if isinstance(result, dict):
            cand_id = result.get("candidate_id") or result.get("id") or "cand:phys:dict"
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
                provided_signatures=sigs if sigs else ("SIG_PHYS_DEFAULT",),
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
            failure_reason="Unsupported physical result type",
        )

    def measure_ability(
        self,
        objective: PhysicalObjective | Mapping[str, Any],
        state: KnowledgeState,
    ) -> float:
        """Measure capability reach for a physical objective under current state."""
        if isinstance(objective, PhysicalObjective):
            sigs = objective.required_signatures
            base = objective.base_ability_pct
        else:
            sigs = tuple(objective.get("required_signatures", ()))
            base = float(objective.get("base_ability_pct", 0.0))

        if not sigs:
            return 1.0

        covered = sum(1 for s in sigs if s in state.signatures)
        if covered == len(sigs):
            return 1.0
        return base + (covered / len(sigs)) * (1.0 - base) * 0.5
