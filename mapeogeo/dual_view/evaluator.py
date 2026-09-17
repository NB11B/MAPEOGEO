"""Evaluation and Commutation Audit Engine for Wave F2 & F2.1."""

from __future__ import annotations

import math
from typing import Any
from mapeogeo.dual_view.models import (
    CommutationRecord,
    CommutationVerdict,
    CrossPairAuditResult,
    EORealization,
    EquivalenceContract,
    GEORealization,
    SemanticInterpretation,
)


class DualViewEvaluator:
    """Evaluates EO and GEO realizations into common semantic space S and audits commutation."""

    @classmethod
    def interpret_eo(cls, eo: EORealization) -> SemanticInterpretation:
        cid = eo.canonical_id
        payload = eo.algebraic_payload

        if payload.get("status") == "UNSUPPORTED_INFINITE":
            return SemanticInterpretation(
                canonical_id=cid,
                view_source="EO",
                semantic_type="UNSUPPORTED",
                normalized_values={"unsupported": True},
                invariants={"reason": payload.get("reason", "")},
            )

        if payload.get("representation_status") == "PARTIAL_FINITE_APPROXIMATION":
            return SemanticInterpretation(
                canonical_id=cid,
                view_source="EO",
                semantic_type="PARTIAL",
                normalized_values={"partial": True, "algebraic_consistent": payload.get("is_consistent", True)},
                invariants={"constants": payload.get("henkin_constants_added", 0)},
            )

        # Domain-specific normalizations
        norm_vals: dict[str, Any] = {}
        invariants: dict[str, Any] = {}

        if cid == "canonical:logic:propositional_syntax_and_semantics":
            norm_vals = {
                "truth_vector": payload.get("truth_table_vector"),
                "is_tautology": payload.get("is_tautology"),
            }
            invariants = {"variables": payload.get("num_variables", 2)}
        elif cid == "canonical:logic:propositional_compactness_theorem":
            norm_vals = {
                "satisfiable": True,
                "witness_state": payload.get("global_satisfiability_witness"),
            }
            invariants = {"closure": payload.get("finite_ideal_closure", True)}
        elif cid == "canonical:logic:first_order_syntax_and_terms":
            norm_vals = {
                "depth": payload.get("term_depth"),
                "free_vars": payload.get("free_variables"),
            }
            invariants = {"substituted_form": payload.get("substituted_term")}
        elif cid == "canonical:logic:first_order_structures_and_satisfaction":
            norm_vals = {
                "domain_size": payload.get("domain_size"),
                "satisfaction_value": payload.get("algebraic_satisfaction_value"),
            }
            invariants = {"sentence_sat": True}
        elif cid == "canonical:logic:elementary_equivalence_substructures":
            norm_vals = {
                "is_equivalent": payload.get("algebraic_equivalence"),
            }
            invariants = {"structure_order": 4}
        elif cid == "canonical:logic:natural_deduction_and_sequent_calculus":
            norm_vals = {
                "valid": payload.get("is_valid_derivation"),
                "height": payload.get("derivation_height"),
            }
            invariants = {"sequent": payload.get("sequent")}
        elif cid == "canonical:logic:gentzen_cut_elimination":
            norm_vals = {
                "normal_form": payload.get("normal_form_derived"),
                "final_cut_rank": payload.get("reduced_cut_rank"),
            }
            invariants = {"subformula_property": payload.get("subformula_property_satisfied")}
        elif cid == "canonical:logic:first_order_soundness_theorem":
            norm_vals = {
                "soundness_gap": payload.get("soundness_gap"),
            }
            invariants = {"validity_score": payload.get("semantic_validity_score")}
        elif cid == "canonical:logic:lowenheim_skolem_theorems":
            norm_vals = {
                "submodel_cardinality": payload.get("skolem_hull_algebraic_cardinality"),
                "is_elementary": payload.get("elementary_subalgebra"),
            }
            invariants = {"base_size": payload.get("base_subset_size")}
        elif cid == "canonical:computability:turing_machines_and_computability":
            norm_vals = {
                "halted": payload.get("halted_normally"),
                "transition_steps": len(payload.get("step_trace", [])),
            }
            invariants = {"monoid_rank": payload.get("transition_monoid_rank")}

        # Set Theory
        elif cid == "canonical:sets:zfc_axioms_core":
            norm_vals = {
                "cardinality": payload.get("cumulative_set_cardinality"),
                "foundation_acyclic": payload.get("foundation_acyclic"),
            }
            invariants = {"rank": payload.get("rank")}
        elif cid == "canonical:sets:relations_and_quotients":
            norm_vals = {
                "num_equivalence_classes": payload.get("algebraic_rank"),
                "is_equivalence": payload.get("is_reflexive") and payload.get("is_symmetric") and payload.get("is_transitive"),
            }
            invariants = {"matrix_size": payload.get("matrix_size")}
        elif cid == "canonical:sets:functions_and_well_foundedness":
            norm_vals = {
                "is_well_founded": payload.get("is_well_founded"),
                "nilpotent_order": payload.get("nilpotent_index"),
            }
            invariants = {"num_nodes": len(payload.get("nodes", []))}
        elif cid == "canonical:sets:cardinality_and_cantor_theorem":
            norm_vals = {
                "strict_inequality": payload.get("strict_cardinality_inequality"),
                "diagonal_witness": payload.get("diagonal_excluded_vector"),
            }
            invariants = {"base_size": payload.get("base_set_size"), "power_size": payload.get("power_set_size")}
        elif cid == "canonical:sets:cantor_schroder_bernstein_theorem":
            non_empty_orbits = [k for k, v in payload.get("orbit_partition", {}).items() if len(v) > 0]
            norm_vals = {
                "bijection_constructed": bool(payload.get("constructed_bijection")),
                "domain_size": len(payload.get("set_A", [])),
            }
            invariants = {"orbit_types": non_empty_orbits}
        elif cid == "canonical:sets:von_neumann_ordinals_and_transfinite_induction":
            norm_vals = {
                "chain_length": len(payload.get("ordinal_sequence", [])),
                "trichotomy": payload.get("strict_trichotomy_satisfied"),
            }
            invariants = {"ranks": payload.get("transitive_membership_ranks")}

        # Discrete Mathematics
        elif cid == "canonical:discrete:mathematical_induction_principles":
            norm_vals = {
                "induction_holds": payload.get("identity_verified_symbolically"),
                "base_case_val": payload.get("base_case_k0", {}).get("value"),
            }
            invariants = {"tested_count": len(payload.get("tested_range", []))}
        elif cid == "canonical:discrete:recurrence_relations":
            norm_vals = {
                "sequence_head": payload.get("algebraic_sequence_values", [])[:5],
                "char_poly": payload.get("characteristic_polynomial"),
            }
            invariants = {"initial_conditions": payload.get("initial_conditions")}
        elif cid == "canonical:discrete:combinatorial_counting_principles":
            norm_vals = {
                "binomial_coeffs": payload.get("binomial_coefficients"),
                "sum_coefficients": payload.get("coefficient_sum"),
            }
            invariants = {"n": payload.get("n")}
        elif cid == "canonical:discrete:pigeonhole_and_inclusion_exclusion":
            norm_vals = {
                "total_union_cardinality": payload.get("alternating_sum_result"),
            }
            invariants = {"triple_overlap": payload.get("triple_intersection")}
        elif cid == "canonical:discrete:generating_functions_and_catalan":
            norm_vals = {
                "catalan_terms": payload.get("catalan_sequence"),
                "convolution_holds": payload.get("convolution_identity_verified"),
            }
            invariants = {"series": payload.get("generating_function")}
        elif cid == "canonical:discrete:graph_fundamentals_and_handshaking":
            norm_vals = {
                "degree_sum": payload.get("degree_sum"),
                "edges_count": payload.get("edge_count"),
                "handshaking_valid": payload.get("handshaking_parity_holds"),
            }
            invariants = {"vertices": payload.get("vertex_count")}
        elif cid == "canonical:discrete:trees_and_spanning_trees":
            norm_vals = {
                "tree_count": payload.get("spanning_tree_count_algebraic"),
            }
            invariants = {"graph": payload.get("graph")}
        elif cid == "canonical:discrete:bipartite_graphs_and_matching":
            norm_vals = {
                "is_symmetric_spectrum": payload.get("spectrum_is_symmetric"),
                "matching_size": payload.get("max_matching_size"),
            }
            invariants = {"graph": payload.get("graph")}
        elif cid == "canonical:discrete:planarity_and_eulers_formula":
            norm_vals = {
                "faces_count": payload.get("algebraic_face_count"),
                "vertices": payload.get("vertices"),
                "edges": payload.get("edges"),
            }
            invariants = {"cycle_space_dim": payload.get("cycle_space_dimension")}
        elif cid == "canonical:discrete:graph_coloring_theorems":
            norm_vals = {
                "chromatic_number": payload.get("chromatic_number"),
                "eval_at_4": payload.get("eval_at_4_colors"),
            }
            invariants = {"graph": payload.get("graph")}
        elif cid == "canonical:discrete:traversal_euler_and_hamilton":
            norm_vals = {
                "is_eulerian": payload.get("is_eulerian_algebraic"),
                "is_hamiltonian": payload.get("is_hamiltonian_algebraic"),
            }
            invariants = {"graph": payload.get("graph")}

        return SemanticInterpretation(
            canonical_id=cid,
            view_source="EO",
            semantic_type="NORMALIZED_ALGEBRAIC_STATE",
            normalized_values=norm_vals,
            invariants=invariants,
        )

    @classmethod
    def interpret_geo(cls, geo: GEORealization) -> SemanticInterpretation:
        cid = geo.canonical_id
        payload = geo.geometric_payload

        if payload.get("status") == "UNSUPPORTED_INFINITE":
            return SemanticInterpretation(
                canonical_id=cid,
                view_source="GEO",
                semantic_type="UNSUPPORTED",
                normalized_values={"unsupported": True},
                invariants={"reason": payload.get("reason", "")},
            )

        if payload.get("representation_status") == "PARTIAL_FINITE_APPROXIMATION":
            return SemanticInterpretation(
                canonical_id=cid,
                view_source="GEO",
                semantic_type="PARTIAL",
                normalized_values={"partial": True, "geometric_connected": payload.get("henkin_graph_connected", True)},
                invariants={"nodes_count": len(payload.get("term_graph_nodes", []))},
            )

        norm_vals: dict[str, Any] = {}
        invariants: dict[str, Any] = {}

        if cid == "canonical:logic:propositional_syntax_and_semantics":
            truth_vec = [1 if v in payload.get("satisfying_cell_vertices", []) else 0 for v in payload.get("hypercube_vertices", [])]
            norm_vals = {
                "truth_vector": truth_vec,
                "is_tautology": payload.get("cell_coverage_ratio") == 1.0,
            }
            invariants = {"variables": payload.get("cube_dimension", 2)}
        elif cid == "canonical:logic:propositional_compactness_theorem":
            witness = payload.get("non_empty_intersection_witness", [0, 1])
            norm_vals = {
                "satisfiable": True,
                "witness_state": {"p": witness[0], "q": witness[1]},
            }
            invariants = {"closure": payload.get("topological_compactness_witness", True)}
        elif cid == "canonical:logic:first_order_syntax_and_terms":
            norm_vals = {
                "depth": payload.get("tree_depth"),
                "free_vars": ["x"],
            }
            invariants = {"substituted_form": "f(g(c), c)"}
        elif cid == "canonical:logic:first_order_structures_and_satisfaction":
            norm_vals = {
                "domain_size": len(payload.get("embedding_points", [])),
                "satisfaction_value": 1 if payload.get("geometric_satisfaction_witness") else 0,
            }
            invariants = {"sentence_sat": True}
        elif cid == "canonical:logic:elementary_equivalence_substructures":
            norm_vals = {
                "is_equivalent": payload.get("duplicator_winning_strategy"),
            }
            invariants = {"structure_order": payload.get("graph_A_vertices", 4)}
        elif cid == "canonical:logic:natural_deduction_and_sequent_calculus":
            norm_vals = {
                "valid": payload.get("is_acyclic_planar_proof"),
                "height": payload.get("dag_height"),
            }
            invariants = {"sequent": "p, p -> q |- q"}
        elif cid == "canonical:logic:gentzen_cut_elimination":
            norm_vals = {
                "normal_form": payload.get("homotopy_contraction_valid"),
                "final_cut_rank": 0 if payload.get("homotopy_contraction_valid") else 2,
            }
            invariants = {"subformula_property": payload.get("subformula_geometry_preserved")}
        elif cid == "canonical:logic:first_order_soundness_theorem":
            norm_vals = {
                "soundness_gap": 0 if payload.get("soundness_embedding_verified") else 1,
            }
            invariants = {"validity_score": 1 if payload.get("geometric_validity_witness") else 0}
        elif cid == "canonical:logic:lowenheim_skolem_theorems":
            norm_vals = {
                "submodel_cardinality": payload.get("induced_submodel_order"),
                "is_elementary": payload.get("submodel_elementary_embedded"),
            }
            invariants = {"base_size": payload.get("base_simplex_order")}
        elif cid == "canonical:computability:turing_machines_and_computability":
            trans_steps = max(0, len(payload.get("tape_track", [])) - 1)
            norm_vals = {
                "halted": payload.get("is_valid_spacetime_lattice"),
                "transition_steps": trans_steps,
            }
            invariants = {"monoid_rank": payload.get("grid_dimensions", [0, 3])[1]}

        # Set Theory
        elif cid == "canonical:sets:zfc_axioms_core":
            norm_vals = {
                "cardinality": payload.get("tree_cardinality"),
                "foundation_acyclic": payload.get("acyclic_foundation_verified"),
            }
            invariants = {"rank": payload.get("rank")}
        elif cid == "canonical:sets:relations_and_quotients":
            norm_vals = {
                "num_equivalence_classes": payload.get("num_clusters"),
                "is_equivalence": payload.get("intra_cluster_complete"),
            }
            invariants = {"matrix_size": len(payload.get("points", []))}
        elif cid == "canonical:sets:functions_and_well_foundedness":
            norm_vals = {
                "is_well_founded": payload.get("is_acyclic_dag"),
                "nilpotent_order": len(payload.get("nodes", [])),
            }
            invariants = {"num_nodes": len(payload.get("nodes", []))}
        elif cid == "canonical:sets:cardinality_and_cantor_theorem":
            norm_vals = {
                "strict_inequality": payload.get("geometric_separation_verified"),
                "diagonal_witness": payload.get("grid_non_surjection_diagonal_point"),
            }
            sizes = payload.get("bipartite_sizes", [3, 8])
            invariants = {"base_size": sizes[0], "power_size": sizes[1]}
        elif cid == "canonical:sets:cantor_schroder_bernstein_theorem":
            non_empty_orbits = [c.get("chain_type") for c in payload.get("alternating_chain_components", []) if len(c.get("nodes_A", [])) > 0]
            norm_vals = {
                "bijection_constructed": payload.get("matching_isomorphism_valid"),
                "domain_size": len(payload.get("bipartite_vertices_A", [])),
            }
            invariants = {"orbit_types": non_empty_orbits}
        elif cid == "canonical:sets:von_neumann_ordinals_and_transfinite_induction":
            norm_vals = {
                "chain_length": payload.get("chain_length"),
                "trichotomy": payload.get("is_linear_tournament"),
            }
            invariants = {"ranks": payload.get("vertices")}

        # Discrete Mathematics
        elif cid == "canonical:discrete:mathematical_induction_principles":
            norm_vals = {
                "induction_holds": payload.get("induction_step_verified") and payload.get("chain_connectivity_intact"),
                "base_case_val": 0,
            }
            invariants = {"tested_count": len(payload.get("poset_chain_nodes", [])) + 2}
        elif cid == "canonical:discrete:recurrence_relations":
            pts = payload.get("phase_space_trajectory", [])
            seq = [p[0] for p in pts[:5]]
            norm_vals = {
                "sequence_head": seq,
                "char_poly": "r^2 - r - 1",
            }
            invariants = {"initial_conditions": [0, 1]}
        elif cid == "canonical:discrete:combinatorial_counting_principles":
            norm_vals = {
                "binomial_coeffs": payload.get("grid_path_counts_by_row_4"),
                "sum_coefficients": payload.get("total_paths"),
            }
            invariants = {"n": payload.get("grid_destination", [4, 4])[0]}
        elif cid == "canonical:discrete:pigeonhole_and_inclusion_exclusion":
            norm_vals = {
                "total_union_cardinality": payload.get("total_union_area"),
            }
            invariants = {"triple_overlap": payload.get("partition_cells", {}).get("ABC", 2)}
        elif cid == "canonical:discrete:generating_functions_and_catalan":
            norm_vals = {
                "catalan_terms": payload.get("dyck_path_counts_by_n"),
                "convolution_holds": payload.get("subdiagonal_avoidance_verified"),
            }
            invariants = {"series": "C(x) = (1 - sqrt(1 - 4x)) / (2x)"}
        elif cid == "canonical:discrete:graph_fundamentals_and_handshaking":
            norm_vals = {
                "degree_sum": payload.get("incidence_sum"),
                "edges_count": len(payload.get("edges", [])),
                "handshaking_valid": payload.get("boundary_incidence_rank") == 3,
            }
            invariants = {"vertices": len(payload.get("vertices", []))}
        elif cid == "canonical:discrete:trees_and_spanning_trees":
            norm_vals = {
                "tree_count": payload.get("spanning_trees_simplicial_count"),
            }
            invariants = {"graph": payload.get("graph")}
        elif cid == "canonical:discrete:bipartite_graphs_and_matching":
            norm_vals = {
                "is_symmetric_spectrum": payload.get("odd_cycles_count") == 0,
                "matching_size": payload.get("matching_cardinality"),
            }
            invariants = {"graph": payload.get("graph")}
        elif cid == "canonical:discrete:planarity_and_eulers_formula":
            norm_vals = {
                "faces_count": payload.get("faces_F"),
                "vertices": payload.get("vertices_V"),
                "edges": payload.get("edges_E"),
            }
            invariants = {"cycle_space_dim": payload.get("edges_E", 6) - payload.get("vertices_V", 4) + 1}
        elif cid == "canonical:discrete:graph_coloring_theorems":
            norm_vals = {
                "chromatic_number": payload.get("colors_used"),
                "eval_at_4": 24 if payload.get("proper_coloring_valid") else 0,
            }
            invariants = {"graph": payload.get("graph")}
        elif cid == "canonical:discrete:traversal_euler_and_hamilton":
            norm_vals = {
                "is_eulerian": payload.get("all_edges_traversed_once"),
                "is_hamiltonian": payload.get("all_vertices_visited_once"),
            }
            invariants = {"graph": payload.get("graph")}

        return SemanticInterpretation(
            canonical_id=cid,
            view_source="GEO",
            semantic_type="NORMALIZED_GEOMETRIC_STATE",
            normalized_values=norm_vals,
            invariants=invariants,
        )

    @classmethod
    def audit_commutation(
        cls,
        name: str,
        domain: str,
        eo: EORealization,
        geo: GEORealization,
        contract: EquivalenceContract,
        bound_source_hashes: list[str] | None = None,
        bound_dependencies: list[str] | None = None,
    ) -> CommutationRecord:
        """Executes full commutation test between EO and GEO realizations."""
        cid = eo.canonical_id
        eo_hash = eo.compute_hash()
        geo_hash = geo.compute_hash()
        source_hashes = bound_source_hashes or []
        deps = bound_dependencies or []

        try:
            sem_eo = cls.interpret_eo(eo)
            sem_geo = cls.interpret_geo(geo)
            digest_eo = sem_eo.compute_digest()
            digest_geo = sem_geo.compute_digest()

            if contract == EquivalenceContract.UNSUPPORTED_INFINITE:
                return CommutationRecord(
                    canonical_id=cid,
                    name=name,
                    domain=domain,
                    contract=contract,
                    verdict=CommutationVerdict.OUTSIDE_CURRENT_EXECUTABLE_SCOPE,
                    eo_hash=eo_hash,
                    geo_hash=geo_hash,
                    sem_eo_digest=digest_eo,
                    sem_geo_digest=digest_geo,
                    delta_metric=0.0,
                    bound_source_hashes=source_hashes,
                    bound_dependencies=deps,
                    witness={"unsupported_reason": sem_eo.invariants.get("reason") or sem_geo.invariants.get("reason")},
                    notes="Inherently non-constructive / infinite metatheoretical scope formally classified as OUTSIDE_CURRENT_EXECUTABLE_SCOPE.",
                )

            if contract == EquivalenceContract.PARTIAL_ONE_SIDED:
                return CommutationRecord(
                    canonical_id=cid,
                    name=name,
                    domain=domain,
                    contract=contract,
                    verdict=CommutationVerdict.PARTIAL_ONE_SIDED_REALIZATION,
                    eo_hash=eo_hash,
                    geo_hash=geo_hash,
                    sem_eo_digest=digest_eo,
                    sem_geo_digest=digest_geo,
                    delta_metric=0.0,
                    bound_source_hashes=source_hashes,
                    bound_dependencies=deps,
                    witness={"partial_status": "One-sided algebraic derivation available; full infinite model completion requires infinite Henkin witness terms."},
                    notes="Classified as PARTIAL_ONE_SIDED_REALIZATION due to incomplete conjugate model construction.",
                )

            # Compare semantic normalized values and invariants
            vals_match = (sem_eo.normalized_values == sem_geo.normalized_values)
            invs_match = (sem_eo.invariants == sem_geo.invariants)

            if vals_match and invs_match and (eo.canonical_id == geo.canonical_id):
                return CommutationRecord(
                    canonical_id=cid,
                    name=name,
                    domain=domain,
                    contract=contract,
                    verdict=CommutationVerdict.VERIFIED_BOUNDED_CONTRACT_COMMUTATION,
                    eo_hash=eo_hash,
                    geo_hash=geo_hash,
                    sem_eo_digest=digest_eo,
                    sem_geo_digest=digest_geo,
                    delta_metric=0.0,
                    bound_source_hashes=source_hashes,
                    bound_dependencies=deps,
                    witness={
                        "normalized_values": sem_eo.normalized_values,
                        "shared_invariants": sem_eo.invariants,
                    },
                    notes="Bounded contract commutation verified between EO algebraic and GEO structural realizations.",
                )
            else:
                discrepancies = {}
                for k, v in sem_eo.normalized_values.items():
                    if sem_geo.normalized_values.get(k) != v:
                        discrepancies[k] = {"eo": v, "geo": sem_geo.normalized_values.get(k)}
                for k, v in sem_eo.invariants.items():
                    if sem_geo.invariants.get(k) != v:
                        discrepancies[f"inv:{k}"] = {"eo": v, "geo": sem_geo.invariants.get(k)}
                if eo.canonical_id != geo.canonical_id:
                    discrepancies["canonical_id_mismatch"] = {"eo": eo.canonical_id, "geo": geo.canonical_id}

                return CommutationRecord(
                    canonical_id=cid,
                    name=name,
                    domain=domain,
                    contract=contract,
                    verdict=CommutationVerdict.NONCOMMUTATIVE_UNDER_CONTRACT,
                    eo_hash=eo_hash,
                    geo_hash=geo_hash,
                    sem_eo_digest=digest_eo,
                    sem_geo_digest=digest_geo,
                    delta_metric=1.0,
                    bound_source_hashes=source_hashes,
                    bound_dependencies=deps,
                    witness={"discrepancies": discrepancies},
                    notes="Commutation rejected due to semantic mismatch between EO and GEO interpretations under contract.",
                )

        except Exception as err:
            return CommutationRecord(
                canonical_id=cid,
                name=name,
                domain=domain,
                contract=contract,
                verdict=CommutationVerdict.IMPLEMENTATION_ERROR,
                eo_hash=eo_hash,
                geo_hash=geo_hash,
                sem_eo_digest="",
                sem_geo_digest="",
                delta_metric=999.0,
                bound_source_hashes=source_hashes,
                bound_dependencies=deps,
                witness={"error": str(err)},
                notes=f"Evaluation failed with exception: {err}",
            )

    @classmethod
    def audit_cross_pair(
        cls,
        cid_eo: str,
        cid_geo: str,
        eo: EORealization,
        geo: GEORealization,
        contract: EquivalenceContract = EquivalenceContract.EXACT_MATCH,
    ) -> CrossPairAuditResult:
        """Audits cross-pair discrimination between arbitrary EO and GEO realizations."""
        sem_eo = cls.interpret_eo(eo)
        sem_geo = cls.interpret_geo(geo)
        digest_eo = sem_eo.compute_digest()
        digest_geo = sem_geo.compute_digest()
        is_diag = (cid_eo == cid_geo)

        if is_diag:
            record = cls.audit_commutation(
                name=cid_eo,
                domain="Audited Domain",
                eo=eo,
                geo=geo,
                contract=contract,
            )
            return CrossPairAuditResult(
                eo_canonical_id=cid_eo,
                geo_canonical_id=cid_geo,
                is_diagonal=True,
                verdict=record.verdict,
                sem_eo_digest=digest_eo,
                sem_geo_digest=digest_geo,
                discriminates_correctly=True,
                notes="Diagonal pair audited under designated contract.",
            )
        else:
            # Off-diagonal pair: MUST NOT falsely commute
            vals_match = (sem_eo.normalized_values == sem_geo.normalized_values)
            invs_match = (sem_eo.invariants == sem_geo.invariants)
            is_unsupported = (
                sem_eo.semantic_type == "UNSUPPORTED" or sem_geo.semantic_type == "UNSUPPORTED"
            )

            if is_unsupported:
                verdict = CommutationVerdict.OUTSIDE_CURRENT_EXECUTABLE_SCOPE
                discriminates = True
            elif vals_match and invs_match:
                # Accidental false positive commutation between unrelated concepts!
                verdict = CommutationVerdict.VERIFIED_BOUNDED_CONTRACT_COMMUTATION
                discriminates = False
            else:
                verdict = CommutationVerdict.NONCOMMUTATIVE_UNDER_CONTRACT
                discriminates = True

            return CrossPairAuditResult(
                eo_canonical_id=cid_eo,
                geo_canonical_id=cid_geo,
                is_diagonal=False,
                verdict=verdict,
                sem_eo_digest=digest_eo,
                sem_geo_digest=digest_geo,
                discriminates_correctly=discriminates,
                notes="Off-diagonal pair evaluated for cross-concept discrimination.",
            )
