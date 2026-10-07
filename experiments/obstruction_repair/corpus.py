"""Obstruction and Repair Corpus for Campaign C1–C3 and Historical Mathematics.

Contains mathematical obstruction/repair examples parameterized strictly by structural
features, without using nominal labels (e.g. 'phantom', 'Telescope', 'truncation')
as discovery features:
- feature_smashing_defect
- feature_operadic_infinity
- feature_domain_closure_defect
- feature_measure_nonadditivity
- feature_self_referential_comprehension
- feature_coordinate_bound_overflow
- feature_unfunctorial_pairing
- feature_non_abelian_multiplicativity
"""

from typing import Dict, List, Any

OBSTRUCTION_REPAIR_CORPUS: List[Dict[str, Any]] = [
    # 1. Prospective Candidate C1
    {
        "case_id": "CASE_C1_CHROMATIC_CONDENSED",
        "domain": "Condensed_Homotopy",
        "historical_era": 2026,
        "structural_features": {
            "feature_smashing_defect": 1.0,
            "feature_operadic_infinity": 0.0,
            "feature_domain_closure_defect": 0.0,
            "feature_measure_nonadditivity": 0.0,
            "feature_self_referential_comprehension": 0.0,
            "feature_coordinate_bound_overflow": 0.0,
            "feature_unfunctorial_pairing": 0.0,
            "feature_non_abelian_multiplicativity": 0.0
        },
        "is_obstructed": True,
        "obstruction_signature_type": "SMASHING_LIMIT_MISMATCH",
        "repair_type": "RESTRICT_TO_NUCLEAR_SUBCATEGORY",
        "description": "Adjunction demanding infinite product commutation under left Bousfield localization lacking smashing property."
    },
    # 2. Prospective Candidate C2
    {
        "case_id": "CASE_C2_PRISMATIC_STACK",
        "domain": "Prismatic_Geometry",
        "historical_era": 2026,
        "structural_features": {
            "feature_smashing_defect": 0.0,
            "feature_operadic_infinity": 0.0,
            "feature_domain_closure_defect": 0.0,
            "feature_measure_nonadditivity": 0.0,
            "feature_self_referential_comprehension": 0.0,
            "feature_coordinate_bound_overflow": 0.0,
            "feature_unfunctorial_pairing": 0.0,
            "feature_non_abelian_multiplicativity": 0.0
        },
        "is_obstructed": False,
        "obstruction_signature_type": "NONE",
        "repair_type": "IDENTITY_REPAIR",
        "description": "Quasi-syntomic derived pushforward and Nygaard duality on adic prismatic crystals."
    },
    # 3. Prospective Candidate C3
    {
        "case_id": "CASE_C3_CUBICAL_MODULI",
        "domain": "Type_Theory",
        "historical_era": 2026,
        "structural_features": {
            "feature_smashing_defect": 0.0,
            "feature_operadic_infinity": 1.0,
            "feature_domain_closure_defect": 0.0,
            "feature_measure_nonadditivity": 0.0,
            "feature_self_referential_comprehension": 0.0,
            "feature_coordinate_bound_overflow": 0.0,
            "feature_unfunctorial_pairing": 0.0,
            "feature_non_abelian_multiplicativity": 0.0
        },
        "is_obstructed": True,
        "obstruction_signature_type": "INFINITE_COHERENCE_DIVERGENCE",
        "repair_type": "TRUNCATE_HOMOTOPY_LEVEL",
        "description": "Constructive Kan composition and univalence glueing on infinite-dimensional universe of structured ring spectra."
    },
    # 4. Classical: Unbounded Operators on Hilbert Space
    {
        "case_id": "CASE_HIST_HILBERT_UNBOUNDED",
        "domain": "Functional_Analysis",
        "historical_era": 1930,
        "structural_features": {
            "feature_smashing_defect": 0.0,
            "feature_operadic_infinity": 0.0,
            "feature_domain_closure_defect": 1.0,
            "feature_measure_nonadditivity": 0.0,
            "feature_self_referential_comprehension": 0.0,
            "feature_coordinate_bound_overflow": 0.0,
            "feature_unfunctorial_pairing": 0.0,
            "feature_non_abelian_multiplicativity": 0.0
        },
        "is_obstructed": True,
        "obstruction_signature_type": "DOMAIN_DIVERGENCE_OBSTRUCTION",
        "repair_type": "RESTRICT_TO_DENSE_CLOSED_DOMAIN",
        "description": "Attempting total definition of differential operators on full Hilbert space without domain restriction."
    },
    # 5. Classical: Riemann Integral on Discontinuous Functions
    {
        "case_id": "CASE_HIST_LEBESGUE_INTEGRATION",
        "domain": "Real_Analysis",
        "historical_era": 1905,
        "structural_features": {
            "feature_smashing_defect": 0.0,
            "feature_operadic_infinity": 0.0,
            "feature_domain_closure_defect": 0.0,
            "feature_measure_nonadditivity": 1.0,
            "feature_self_referential_comprehension": 0.0,
            "feature_coordinate_bound_overflow": 0.0,
            "feature_unfunctorial_pairing": 0.0,
            "feature_non_abelian_multiplicativity": 0.0
        },
        "is_obstructed": True,
        "obstruction_signature_type": "MEASURE_ADDITIVITY_OBSTRUCTION",
        "repair_type": "PASS_TO_SIGMA_ADDITIVE_MEASURABILITY",
        "description": "Failure of pointwise limit of Riemann integrable functions to remain Riemann integrable."
    },
    # 6. Classical: Naive Set Comprehension (Russell's Paradox)
    {
        "case_id": "CASE_HIST_RUSSELL_PARADOX",
        "domain": "Set_Theory",
        "historical_era": 1908,
        "structural_features": {
            "feature_smashing_defect": 0.0,
            "feature_operadic_infinity": 0.0,
            "feature_domain_closure_defect": 0.0,
            "feature_measure_nonadditivity": 0.0,
            "feature_self_referential_comprehension": 1.0,
            "feature_coordinate_bound_overflow": 0.0,
            "feature_unfunctorial_pairing": 0.0,
            "feature_non_abelian_multiplicativity": 0.0
        },
        "is_obstructed": True,
        "obstruction_signature_type": "SELF_REFERENTIAL_COMPREHENSION_OBSTRUCTION",
        "repair_type": "RESTRICT_TO_STRATIFIED_SEPARATION_ZFC",
        "description": "Unrestricted predicate comprehension yielding Russell class {x : x \\notin x}."
    },
    # 7. Historical Positive: Serre Sheaf Cohomology (1955)
    {
        "case_id": "CASE_HIST_POS_SERRE_FAC",
        "domain": "Algebraic_Geometry",
        "historical_era": 1955,
        "structural_features": {
            "feature_smashing_defect": 0.0,
            "feature_operadic_infinity": 0.0,
            "feature_domain_closure_defect": 0.0,
            "feature_measure_nonadditivity": 0.0,
            "feature_self_referential_comprehension": 0.0,
            "feature_coordinate_bound_overflow": 0.0,
            "feature_unfunctorial_pairing": 0.0,
            "feature_non_abelian_multiplicativity": 0.0
        },
        "is_obstructed": False,
        "obstruction_signature_type": "NONE",
        "repair_type": "IDENTITY_REPAIR",
        "description": "Coherent sheaf cohomology on projective algebraic varieties."
    },
    # 8. Historical Positive: Cartan-Eilenberg Ext (1956)
    {
        "case_id": "CASE_HIST_POS_CARTAN_EILENBERG",
        "domain": "Homological_Algebra",
        "historical_era": 1956,
        "structural_features": {
            "feature_smashing_defect": 0.0,
            "feature_operadic_infinity": 0.0,
            "feature_domain_closure_defect": 0.0,
            "feature_measure_nonadditivity": 0.0,
            "feature_self_referential_comprehension": 0.0,
            "feature_coordinate_bound_overflow": 0.0,
            "feature_unfunctorial_pairing": 0.0,
            "feature_non_abelian_multiplicativity": 0.0
        },
        "is_obstructed": False,
        "obstruction_signature_type": "NONE",
        "repair_type": "IDENTITY_REPAIR",
        "description": "Derived functor resolutions in module categories with enough projectives."
    },
    # 9. Historical Positive: Grothendieck Schemes (1960)
    {
        "case_id": "CASE_HIST_POS_GROTHENDIECK_EGA",
        "domain": "Algebraic_Geometry",
        "historical_era": 1960,
        "structural_features": {
            "feature_smashing_defect": 0.0,
            "feature_operadic_infinity": 0.0,
            "feature_domain_closure_defect": 0.0,
            "feature_measure_nonadditivity": 0.0,
            "feature_self_referential_comprehension": 0.0,
            "feature_coordinate_bound_overflow": 0.0,
            "feature_unfunctorial_pairing": 0.0,
            "feature_non_abelian_multiplicativity": 0.0
        },
        "is_obstructed": False,
        "obstruction_signature_type": "NONE",
        "repair_type": "IDENTITY_REPAIR",
        "description": "Prime spectrum locally ringed space gluing on Zariski basic opens."
    },
    # 10. Historical Negative Control: Coordinate Bound Overflow
    {
        "case_id": "CASE_HIST_NEG_BOUND_OVERFLOW",
        "domain": "Combinatorics",
        "historical_era": 1950,
        "structural_features": {
            "feature_smashing_defect": 0.0,
            "feature_operadic_infinity": 0.0,
            "feature_domain_closure_defect": 0.0,
            "feature_measure_nonadditivity": 0.0,
            "feature_self_referential_comprehension": 0.0,
            "feature_coordinate_bound_overflow": 1.0,
            "feature_unfunctorial_pairing": 0.0,
            "feature_non_abelian_multiplicativity": 0.0
        },
        "is_obstructed": True,
        "obstruction_signature_type": "AXIOMATIC_DEGREE_VIOLATION",
        "repair_type": "RESTRICT_TO_BOUNDED_DEGREE",
        "description": "Composition depth delta = 99 exceeding finite grammar saturation."
    },
    # 11. Historical Negative Control: Non-Functorial Pairing
    {
        "case_id": "CASE_HIST_NEG_NONFUNCTORIAL",
        "domain": "Category_Theory",
        "historical_era": 1970,
        "structural_features": {
            "feature_smashing_defect": 0.0,
            "feature_operadic_infinity": 0.0,
            "feature_domain_closure_defect": 0.0,
            "feature_measure_nonadditivity": 0.0,
            "feature_self_referential_comprehension": 0.0,
            "feature_coordinate_bound_overflow": 0.0,
            "feature_unfunctorial_pairing": 1.0,
            "feature_non_abelian_multiplicativity": 0.0
        },
        "is_obstructed": True,
        "obstruction_signature_type": "UNFUNCTORIAL_PAIRING",
        "repair_type": "ENFORCE_PENTAGON_COHERENCE",
        "description": "Adjunction candidate whose unit-counit pairing violates associativity."
    },
    # 12. Historical Negative Control: Non-Abelian Determinant
    {
        "case_id": "CASE_HIST_NEG_NONABELIAN_DET",
        "domain": "Linear_Algebra",
        "historical_era": 1940,
        "structural_features": {
            "feature_smashing_defect": 0.0,
            "feature_operadic_infinity": 0.0,
            "feature_domain_closure_defect": 0.0,
            "feature_measure_nonadditivity": 0.0,
            "feature_self_referential_comprehension": 0.0,
            "feature_coordinate_bound_overflow": 0.0,
            "feature_unfunctorial_pairing": 0.0,
            "feature_non_abelian_multiplicativity": 1.0
        },
        "is_obstructed": True,
        "obstruction_signature_type": "COMMUTATIVITY_DEFECT_OBSTRUCTION",
        "repair_type": "PASS_TO_DIEUDONNE_DETERMINANT",
        "description": "Attempting naive multiplicative determinant on general non-commutative matrix rings."
    }
]

def load_obstruction_corpus() -> List[Dict[str, Any]]:
    """Returns the standardized, balanced obstruction-repair corpus."""
    return list(OBSTRUCTION_REPAIR_CORPUS)
