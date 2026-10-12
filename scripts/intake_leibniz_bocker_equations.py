"""SOVCTX Intake Script for the Leibniz-Bocker Mathematical Framework Equations.

Ingests into the canonical graph:
1. Entities: PERSON:BOCKER_NJ
2. Sources:
   - PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK
   - PUB:BOCKER_2025_LEIBNIZ_EXTENDED
3. Source Fragments:
   - FRAG:BOCKER_2025_INCREMENT_DEFINITION
   - FRAG:BOCKER_2025_COVARIANCE_OPERATOR
   - FRAG:BOCKER_2025_DECOMPOSITION_OF_MOTION
   - FRAG:BOCKER_2025_DIAGNOSTIC_TRINITY
   - FRAG:BOCKER_2025_STREAMING_OJA
4. Equation Family:
   - FAMILY:LEIBNIZ_BOCKER_GEOMETRIC_MOTION
5. Equations:
   - EQ:BOCKER_2025_INCREMENT (phi(t) = x(t+1) - x(t))
   - EQ:BOCKER_2025_INCREMENT_COVARIANCE (C(t) = E[phi phi^T])
   - EQ:BOCKER_2025_MOTION_DECOMPOSITION (phi(t) = E_k a(t) + r(t))
   - EQ:BOCKER_2025_COHERENCE (rho_k(t) = sum_k lambda_i / sum_N lambda_i)
   - EQ:BOCKER_2025_SUBSPACE_CURVATURE (Omega_k(t) = max theta_i / dt)
   - EQ:BOCKER_2025_PROJECTOR_CURVATURE (Omega_tilde_k(t) = ||P_{t+dt} - P_t||_F / dt)
   - EQ:BOCKER_2025_STREAMING_OJA_UPDATE (W_{t+1}^* = W_t + eta phi phi^T W_t)
6. Supporting Symbols, Assumptions, Invariants, and Behavioral Tests.
7. Edges: EXTRACTED_FROM, ENCODES_EQUATION, MEMBER_OF_EQUATION_FAMILY,
   HAS_SYMBOL, HAS_ASSUMPTION, PRESERVES_INVARIANT, HAS_BEHAVIORAL_TEST,
   and STRUCTURALLY_ANALOGOUS_TO comparison bridges.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

ROOT = Path(__file__).resolve().parents[1] / "sovctx"


def load_ids(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            obj = json.loads(line)
            if "id" in obj:
                ids.add(obj["id"])
    return ids


def append_records(path: Path, records: List[Dict[str, Any]]) -> int:
    existing_ids = load_ids(path)
    to_add = [r for r in records if r["id"] not in existing_ids]
    if not to_add:
        return 0

    with path.open("a", encoding="utf-8") as f:
        for r in to_add:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(to_add)


def main() -> None:
    print("=" * 75)
    print("SOVCTX: Ingesting Leibniz-Bocker Mathematical Equations & Subspace Calculus")
    print("=" * 75)

    # 1. Person Entity
    entities = [
        {"id": "PERSON:BOCKER_NJ", "type": "PERSON", "namespace": "MOD", "label": "Nathanael Joseph Bocker"},
    ]
    added_ent = append_records(ROOT / "graph" / "entities.jsonl", entities)
    print(f"[+] Entities: added {added_ent} records")

    # 2. Publications
    sources = [
        {
            "id": "PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK",
            "type": "PUBLICATION",
            "namespace": "MOD",
            "label": "Geometric Decomposition of Infinitesimal Motion: Evolving Spectral Subspaces on the Grassmann Manifold — The Leibniz–Bocker Framework",
            "publication_date": "2025",
            "provenance_class": "S1",
            "knowledge_status": "D",
            "verification_status": "verified_primary",
            "authors": ["PERSON:BOCKER_NJ"],
            "publisher": "Standalone Research Preprint",
            "notes": "Introduces infinitesimal motion phi(t)=x(t+1)-x(t), covariance operator C(t), Grassmannian frame E_k(t), and coherence/curvature/residual decomposition.",
        },
        {
            "id": "PUB:BOCKER_2025_LEIBNIZ_EXTENDED",
            "type": "PUBLICATION",
            "namespace": "MOD",
            "label": "The Leibniz/Bocker Framework: Extended Diagnostics, Curvature Metrics, and Streaming Implementation",
            "publication_date": "2025",
            "provenance_class": "S1",
            "knowledge_status": "D",
            "verification_status": "verified_primary",
            "authors": ["PERSON:BOCKER_NJ"],
            "publisher": "Standalone Research Preprint",
            "notes": "Introduces projector-based curvature, online Oja streaming subspace tracking, and spectral gap-curvature instability dynamics.",
        },
    ]
    added_src = append_records(ROOT / "corpus" / "sources.jsonl", sources)
    print(f"[+] Sources: added {added_src} records")

    # 3. Source Fragments
    fragments = [
        {
            "id": "FRAG:BOCKER_2025_INCREMENT_DEFINITION",
            "type": "SOURCE_FRAGMENT",
            "namespace": "MOD",
            "label": "Bocker 2025 definition of infinitesimal motion as primary data",
            "source_id": "PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK",
            "locator": "Section 1.1, p. 2",
            "source_language": "English",
            "extraction_language": "English",
            "evidence_basis": "direct_text_inspected",
            "verification_status": "verified_primary",
            "normalized_summary": (
                "Rather than modeling state x(t) directly, the framework takes change itself as the primary object, "
                "defining discrete infinitesimal motion phi(t) = x(t+1) - x(t)."
            ),
        },
        {
            "id": "FRAG:BOCKER_2025_COVARIANCE_OPERATOR",
            "type": "SOURCE_FRAGMENT",
            "namespace": "MOD",
            "label": "Bocker 2025 local covariance operator and evolving Grassmannian eigenspaces",
            "source_id": "PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK",
            "locator": "Section 1.2, p. 3; Section 2.2, p. 6",
            "source_language": "English",
            "extraction_language": "English",
            "evidence_basis": "direct_text_inspected",
            "verification_status": "verified_primary",
            "normalized_summary": (
                "Constructs local covariance operator C(t) = E[phi phi^T] over sliding windows or recursive updates; "
                "leading eigenvectors E_k(t) trace out trajectories on Grassmann manifold Gr(k, N)."
            ),
        },
        {
            "id": "FRAG:BOCKER_2025_DECOMPOSITION_OF_MOTION",
            "type": "SOURCE_FRAGMENT",
            "namespace": "MOD",
            "label": "Bocker 2025 orthogonal decomposition of infinitesimal change",
            "source_id": "PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK",
            "locator": "Section 1.4, p. 4; Section 2.6, p. 7",
            "source_language": "English",
            "extraction_language": "English",
            "evidence_basis": "direct_text_inspected",
            "verification_status": "verified_primary",
            "normalized_summary": (
                "Infinitesimal change decomposes as phi(t) = E_k(t) a(t) + r(t), where a(t) = E_k(t)^T phi(t) "
                "are harmonic coordinates and r(t) is the orthogonal residual satisfying E_k(t)^T r(t) = 0."
            ),
        },
        {
            "id": "FRAG:BOCKER_2025_DIAGNOSTIC_TRINITY",
            "type": "SOURCE_FRAGMENT",
            "namespace": "MOD",
            "label": "Bocker 2025 diagnostic trinity: coherence, curvature, and residual novelty",
            "source_id": "PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK",
            "locator": "Sections 2.7-2.9, pp. 7-8; Extended Section 2-3, p. 2",
            "source_language": "English",
            "extraction_language": "English",
            "evidence_basis": "direct_text_inspected",
            "verification_status": "verified_primary",
            "normalized_summary": (
                "Coherence rho_k measures variance concentration; max-angle curvature Omega_k and projector curvature "
                "Omega_tilde_k measure Grassmannian subspace rotation; residual norm ||r|| measures dimensional novelty."
            ),
        },
        {
            "id": "FRAG:BOCKER_2025_STREAMING_OJA",
            "type": "SOURCE_FRAGMENT",
            "namespace": "MOD",
            "label": "Bocker 2025 online Oja-style streaming subspace tracker",
            "source_id": "PUB:BOCKER_2025_LEIBNIZ_EXTENDED",
            "locator": "Section 4, p. 3",
            "source_language": "English",
            "extraction_language": "English",
            "evidence_basis": "direct_text_inspected",
            "verification_status": "verified_primary",
            "normalized_summary": (
                "Online update scheme W_{t+1}^* = W_t + eta_t phi phi^T W_t, W_{t+1} = qr(W_{t+1}^*) "
                "with recursive covariance Sigma_{t+1} = (1-alpha)Sigma_t + alpha phi phi^T for real-time tracking."
            ),
        },
    ]
    added_frag = append_records(ROOT / "corpus" / "source_fragments.jsonl", fragments)
    print(f"[+] Fragments: added {added_frag} records")

    # 4. Equation Family
    families = [
        {
            "id": "FAMILY:LEIBNIZ_BOCKER_GEOMETRIC_MOTION",
            "type": "EQUATION_FAMILY",
            "namespace": "MOD",
            "label": "Leibniz-Bocker infinitesimal motion and Grassmannian spectral dynamics",
            "status": "verified_primary",
            "behavior_focus": [
                "infinitesimal_increment",
                "subspace_rotation",
                "projector_curvature",
                "orthogonal_residual",
                "streaming_tracking",
            ],
        }
    ]
    added_fam = append_records(ROOT / "graph" / "equation_families.jsonl", families)
    print(f"[+] Equation Families: added {added_fam} records")

    # 5. Symbols
    symbols = [
        {"id": "SYMBOL:LB_X_T", "type": "SYMBOL", "namespace": "MOD", "label": "System multivariate state at step t", "symbol": "x(t)", "semantic_role": "state_vector"},
        {"id": "SYMBOL:LB_X_T_PLUS_1", "type": "SYMBOL", "namespace": "MOD", "label": "System state at step t+1", "symbol": "x(t+1)", "semantic_role": "state_vector"},
        {"id": "SYMBOL:LB_PHI_T", "type": "SYMBOL", "namespace": "MOD", "label": "Infinitesimal increment vector", "symbol": "\\phi(t)", "semantic_role": "increment_vector"},
        {"id": "SYMBOL:LB_C_T", "type": "SYMBOL", "namespace": "MOD", "label": "Local covariance operator of increments", "symbol": "C(t)", "semantic_role": "covariance_operator"},
        {"id": "SYMBOL:LB_E_K", "type": "SYMBOL", "namespace": "MOD", "label": "Dominant k-dimensional spectral frame on Gr(k, N)", "symbol": "E_k(t)", "semantic_role": "grassmannian_subspace"},
        {"id": "SYMBOL:LB_A_T", "type": "SYMBOL", "namespace": "MOD", "label": "Harmonic coordinates on spectral frame", "symbol": "a(t)", "semantic_role": "harmonic_coordinate"},
        {"id": "SYMBOL:LB_R_T", "type": "SYMBOL", "namespace": "MOD", "label": "Orthogonal residual novelty vector", "symbol": "r(t)", "semantic_role": "residual_novelty"},
        {"id": "SYMBOL:LB_RHO_K", "type": "SYMBOL", "namespace": "MOD", "label": "Rank-k spectral coherence ratio", "symbol": "\\rho_k(t)", "semantic_role": "coherence_metric"},
        {"id": "SYMBOL:LB_LAMBDA_I", "type": "SYMBOL", "namespace": "MOD", "label": "Eigenvalues of increment covariance", "symbol": "\\lambda_i(t)", "semantic_role": "eigenvalues"},
        {"id": "SYMBOL:LB_OMEGA_K", "type": "SYMBOL", "namespace": "MOD", "label": "Max-principal-angle Grassmannian curvature", "symbol": "\\Omega_k(t)", "semantic_role": "max_angle_curvature"},
        {"id": "SYMBOL:LB_THETA_I", "type": "SYMBOL", "namespace": "MOD", "label": "Principal angles between successive subspaces", "symbol": "\\theta_i", "semantic_role": "principal_angle"},
        {"id": "SYMBOL:LB_DELTA_T", "type": "SYMBOL", "namespace": "MOD", "label": "Temporal interval between successive observations", "symbol": "\\Delta t", "semantic_role": "time_increment"},
        {"id": "SYMBOL:LB_OMEGA_TILDE_K", "type": "SYMBOL", "namespace": "MOD", "label": "Projector-based Frobenius rotational curvature", "symbol": "\\tilde{\\Omega}_k(t)", "semantic_role": "projector_curvature"},
        {"id": "SYMBOL:LB_P_T", "type": "SYMBOL", "namespace": "MOD", "label": "Orthogonal projector onto dominant subspace", "symbol": "P_t", "semantic_role": "orthogonal_projector"},
        {"id": "SYMBOL:LB_W_T", "type": "SYMBOL", "namespace": "MOD", "label": "Online streaming subspace approximation frame", "symbol": "W_t", "semantic_role": "streaming_subspace_frame"},
        {"id": "SYMBOL:LB_ETA_T", "type": "SYMBOL", "namespace": "MOD", "label": "Learning rate for streaming subspace update", "symbol": "\\eta_t", "semantic_role": "learning_rate"},
    ]
    added_sym = append_records(ROOT / "graph" / "symbols.jsonl", symbols)
    print(f"[+] Symbols: added {added_sym} records")

    # 6. Assumptions
    assumptions = [
        {"id": "ASSUMPTION:LB_BOUNDED_INCREMENTS", "type": "ASSUMPTION", "namespace": "MOD", "label": "Bounded increment magnitude ||phi(t)|| <= M", "statement": "Increment norms are bounded uniformly across all observations.", "status": "active"},
        {"id": "ASSUMPTION:LB_LOCAL_STATIONARITY", "type": "ASSUMPTION", "namespace": "MOD", "label": "Local ergodicity and stationarity of increment field", "statement": "Increment statistics converge to well-defined local covariance operators.", "status": "active"},
        {"id": "ASSUMPTION:LB_SPECTRAL_GAP", "type": "ASSUMPTION", "namespace": "MOD", "label": "Uniform spectral gap lambda_k(t) - lambda_{k+1}(t) >= epsilon", "statement": "Dominant eigenspace is separated from remaining spectrum by positive gap, ruling out degeneracy.", "status": "active"},
        {"id": "ASSUMPTION:LB_SMOOTH_COVARIANCE", "type": "ASSUMPTION", "namespace": "MOD", "label": "Differentiable covariance evolution dC/dt finite a.e.", "statement": "Covariance operator varies differentiably in time.", "status": "active"},
        {"id": "ASSUMPTION:LB_NON_ZERO_VARIANCE", "type": "ASSUMPTION", "namespace": "MOD", "label": "Non-zero total increment variance", "statement": "Sum of eigenvalues of increment covariance is strictly positive.", "status": "active"},
    ]
    added_asm = append_records(ROOT / "graph" / "assumptions.jsonl", assumptions)
    print(f"[+] Assumptions: added {added_asm} records")

    # 7. Invariants
    invariants = [
        {"id": "INVARIANT:LB_TRANSLATIONAL_DRIFT", "type": "INVARIANT", "namespace": "MOD", "label": "State translation invariance of increment operator", "statement": "phi(t) is invariant under global static state translations x -> x + c.", "status": "verified"},
        {"id": "INVARIANT:LB_ORTHOGONAL_RESIDUAL", "type": "INVARIANT", "namespace": "MOD", "label": "Strict orthogonality of residual novelty E_k^T r = 0", "statement": "Harmonic projection and residual decompose the increment into strictly orthogonal components.", "status": "verified"},
        {"id": "INVARIANT:LB_COVARIANCE_SYMMETRY_PSD", "type": "INVARIANT", "namespace": "MOD", "label": "Symmetric positive semi-definiteness of covariance C(t)", "statement": "Covariance operator C(t) is symmetric and positive semi-definite with non-negative eigenvalues.", "status": "verified"},
        {"id": "INVARIANT:LB_COHERENCE_UNIT_BOUNDS", "type": "INVARIANT", "namespace": "MOD", "label": "Coherence bounded in unit interval [0, 1]", "statement": "Fraction of variance captured by leading k modes satisfies 0 <= rho_k <= 1.", "status": "verified"},
        {"id": "INVARIANT:LB_CURVATURE_NON_NEGATIVE", "type": "INVARIANT", "namespace": "MOD", "label": "Non-negativity of Grassmannian curvature", "statement": "Curvature metrics Omega_k and Omega_tilde_k are non-negative, equaling zero only under static subspaces.", "status": "verified"},
        {"id": "INVARIANT:LB_PROJECTOR_IDEMPOTENCE", "type": "INVARIANT", "namespace": "MOD", "label": "Idempotence and symmetry of projector P_t^2 = P_t", "statement": "Projector onto subspace is symmetric idempotent operator P_t = P_t^T = P_t^2.", "status": "verified"},
        {"id": "INVARIANT:LB_ORTHONORMAL_FRAME", "type": "INVARIANT", "namespace": "MOD", "label": "Orthonormality of tracking frame W_t^T W_t = I_k", "statement": "QR decomposition ensures online tracker maintains strictly orthonormal basis for k-dimensional subspace.", "status": "verified"},
    ]
    added_inv = append_records(ROOT / "graph" / "invariants.jsonl", invariants)
    print(f"[+] Invariants: added {added_inv} records")

    # 8. Behavioral Tests
    tests = [
        {
            "id": "TEST:LB_STATIC_ZERO_INCREMENT",
            "type": "BEHAVIORAL_TEST",
            "namespace": "MOD",
            "label": "Zero increment for static unchanged state",
            "equation_id": "EQ:BOCKER_2025_INCREMENT",
            "test_type": "boundary_zero",
            "given": "x(t+1) == x(t)",
            "expected": "phi(t) == 0",
            "qualification_role": "identity_consistency",
            "automatable": True,
            "evaluator": "symbolic_simplification",
            "result_semantics": "Stationary states produce null increment vector.",
        },
        {
            "id": "TEST:LB_COVARIANCE_PSD",
            "type": "BEHAVIORAL_TEST",
            "namespace": "MOD",
            "label": "Positive semi-definiteness of outer product covariance",
            "equation_id": "EQ:BOCKER_2025_INCREMENT_COVARIANCE",
            "test_type": "spectral_positivity",
            "given": "C(t) = phi phi^T",
            "expected": "min(eig(C(t))) >= 0",
            "qualification_role": "operator_validity",
            "automatable": True,
            "evaluator": "numpy_eigh",
            "result_semantics": "Covariance operator has all non-negative real eigenvalues.",
        },
        {
            "id": "TEST:LB_RESIDUAL_ORTHOGONALITY",
            "type": "BEHAVIORAL_TEST",
            "namespace": "MOD",
            "label": "Residual inner product with dominant frame equals zero",
            "equation_id": "EQ:BOCKER_2025_MOTION_DECOMPOSITION",
            "test_type": "orthogonality_check",
            "given": "r(t) = phi(t) - E_k a(t)",
            "expected": "max(abs(E_k^T r(t))) < 1e-12",
            "qualification_role": "subspace_orthogonality",
            "automatable": True,
            "evaluator": "matrix_multiply",
            "result_semantics": "Residual novelty lies strictly in the orthogonal complement of the dominant frame.",
        },
        {
            "id": "TEST:LB_COHERENCE_BOUNDS",
            "type": "BEHAVIORAL_TEST",
            "namespace": "MOD",
            "label": "Spectral coherence confined to unit interval",
            "equation_id": "EQ:BOCKER_2025_COHERENCE",
            "test_type": "range_bounds",
            "given": "lambda_i >= 0",
            "expected": "0.0 <= rho_k <= 1.0",
            "qualification_role": "metric_normalization",
            "automatable": True,
            "evaluator": "scalar_inequality",
            "result_semantics": "Coherence provides normalized effective dimensionality measure.",
        },
        {
            "id": "TEST:LB_ZERO_ROTATION_CURVATURE",
            "type": "BEHAVIORAL_TEST",
            "namespace": "MOD",
            "label": "Zero curvature under static invariant subspace",
            "equation_id": "EQ:BOCKER_2025_SUBSPACE_CURVATURE",
            "test_type": "invariance_null",
            "given": "E_k(t+dt) == E_k(t)",
            "expected": "Omega_k(t) == 0.0",
            "qualification_role": "curvature_gauge",
            "automatable": True,
            "evaluator": "svd_principal_angles",
            "result_semantics": "Subspaces that do not rotate have identically zero curvature.",
        },
        {
            "id": "TEST:LB_PROJECTOR_IDENTITY",
            "type": "BEHAVIORAL_TEST",
            "namespace": "MOD",
            "label": "Projector Frobenius curvature matches sum of squared sines",
            "equation_id": "EQ:BOCKER_2025_PROJECTOR_CURVATURE",
            "test_type": "geometric_identity",
            "given": "P_t = E_k E_k^T, P_{t+dt} = E_k' E_k'^T",
            "expected": "||P_{t+dt} - P_t||_F^2 == 2 * sum(sin(theta_i)^2)",
            "qualification_role": "grassmannian_identity",
            "automatable": True,
            "evaluator": "frobenius_vs_principal_angles",
            "result_semantics": "Projector curvature Frobenius norm exactly aggregates all principal angle rotational energies.",
        },
        {
            "id": "TEST:LB_OJA_STEP_ALIGNMENT",
            "type": "BEHAVIORAL_TEST",
            "namespace": "MOD",
            "label": "Online Oja tracker maintains orthonormal frame",
            "equation_id": "EQ:BOCKER_2025_STREAMING_OJA_UPDATE",
            "test_type": "orthonormal_preservation",
            "given": "W_{t+1} = qr(W_{t+1}^*)[0]",
            "expected": "||W_{t+1}^T W_{t+1} - I_k||_F < 1e-12",
            "qualification_role": "streaming_stability",
            "automatable": True,
            "evaluator": "qr_orthonormality",
            "result_semantics": "Streaming subspace frame preserves exact geometric orthonormality on Gr(k, N).",
        },
    ]
    added_tst = append_records(ROOT / "graph" / "behavioral_tests.jsonl", tests)
    print(f"[+] Behavioral Tests: added {added_tst} records")

    # 9. Equations
    equations = [
        {
            "id": "EQ:BOCKER_2025_INCREMENT",
            "type": "EQUATION",
            "namespace": "MOD",
            "label": "Leibniz-Bocker infinitesimal motion increment",
            "latex": "\\phi(t) = x(t+1) - x(t)",
            "original_notation": "\\phi(t) = x(t+1) - x(t)",
            "normalized_notation": "\\phi(t) = x(t+1) - x(t)",
            "equation_kind": "discrete_infinitesimal_motion",
            "source_ids": ["PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK", "PUB:BOCKER_2025_LEIBNIZ_EXTENDED"],
            "source_fragment_ids": ["FRAG:BOCKER_2025_INCREMENT_DEFINITION"],
            "transcription_status": "primary_text_transcription",
            "verification_status": "verified_primary",
            "symbol_ids": ["SYMBOL:LB_X_T", "SYMBOL:LB_X_T_PLUS_1", "SYMBOL:LB_PHI_T"],
            "input_symbol_ids": ["SYMBOL:LB_X_T", "SYMBOL:LB_X_T_PLUS_1"],
            "output_symbol_ids": ["SYMBOL:LB_PHI_T"],
            "assumption_ids": ["ASSUMPTION:LB_BOUNDED_INCREMENTS"],
            "invariant_ids": ["INVARIANT:LB_TRANSLATIONAL_DRIFT"],
            "behavioral_test_ids": ["TEST:LB_STATIC_ZERO_INCREMENT"],
            "native_context": "The fundamental object of analysis is discrete infinitesimal motion rather than static state.",
            "notes": "Realizes the Leibnizian thesis: understand the system by how it changes rather than what it is at a moment.",
        },
        {
            "id": "EQ:BOCKER_2025_INCREMENT_COVARIANCE",
            "type": "EQUATION",
            "namespace": "MOD",
            "label": "Leibniz-Bocker local covariance operator of motion",
            "latex": "C(t) = \\mathbb{E}[\\phi(t)\\phi(t)^\\top]",
            "original_notation": "C(t) = E[\\phi \\phi^T]",
            "normalized_notation": "C(t) = \\mathbb{E}[\\phi(t)\\phi(t)^\\top]",
            "equation_kind": "covariance_operator",
            "source_ids": ["PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK"],
            "source_fragment_ids": ["FRAG:BOCKER_2025_COVARIANCE_OPERATOR"],
            "transcription_status": "primary_text_transcription",
            "verification_status": "verified_primary",
            "symbol_ids": ["SYMBOL:LB_C_T", "SYMBOL:LB_PHI_T"],
            "input_symbol_ids": ["SYMBOL:LB_PHI_T"],
            "output_symbol_ids": ["SYMBOL:LB_C_T"],
            "assumption_ids": ["ASSUMPTION:LB_LOCAL_STATIONARITY"],
            "invariant_ids": ["INVARIANT:LB_COVARIANCE_SYMMETRY_PSD"],
            "behavioral_test_ids": ["TEST:LB_COVARIANCE_PSD"],
            "native_context": "Local covariance operator of infinitesimal tendencies whose dominant eigenspaces define trajectories on Gr(k, N).",
            "notes": "Transforms discrete increments into an evolving spectral manifold representation.",
        },
        {
            "id": "EQ:BOCKER_2025_MOTION_DECOMPOSITION",
            "type": "EQUATION",
            "namespace": "MOD",
            "label": "Leibniz-Bocker decomposition of infinitesimal motion",
            "latex": "\\phi(t) = E_k(t)a(t) + r(t)",
            "original_notation": "\\phi(t) = E_k(t)a(t) + r(t)",
            "normalized_notation": "\\phi(t) = E_k(t)a(t) + r(t)",
            "equation_kind": "spectral_subspace_decomposition",
            "source_ids": ["PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK"],
            "source_fragment_ids": ["FRAG:BOCKER_2025_DECOMPOSITION_OF_MOTION"],
            "transcription_status": "primary_text_transcription",
            "verification_status": "verified_primary",
            "symbol_ids": ["SYMBOL:LB_PHI_T", "SYMBOL:LB_E_K", "SYMBOL:LB_A_T", "SYMBOL:LB_R_T"],
            "input_symbol_ids": ["SYMBOL:LB_PHI_T", "SYMBOL:LB_E_K"],
            "output_symbol_ids": ["SYMBOL:LB_A_T", "SYMBOL:LB_R_T"],
            "assumption_ids": ["ASSUMPTION:LB_SPECTRAL_GAP"],
            "invariant_ids": ["INVARIANT:LB_ORTHOGONAL_RESIDUAL"],
            "behavioral_test_ids": ["TEST:LB_RESIDUAL_ORTHOGONALITY"],
            "native_context": "Decomposes motion into coordinates along the dominant Grassmannian frame and an orthogonal residual novelty vector.",
            "notes": "Enforces strict orthogonality E_k^T r = 0.",
        },
        {
            "id": "EQ:BOCKER_2025_COHERENCE",
            "type": "EQUATION",
            "namespace": "MOD",
            "label": "Leibniz-Bocker rank-k spectral coherence",
            "latex": "\\rho_k(t) = \\frac{\\sum_{i=1}^k \\lambda_i(t)}{\\sum_{i=1}^N \\lambda_i(t)}",
            "original_notation": "\\rho_k(t) = \\frac{\\lambda_1 + ... + \\lambda_k}{\\sum \\lambda_i}",
            "normalized_notation": "\\rho_k(t) = \\frac{\\sum_{i=1}^k \\lambda_i(t)}{\\sum_{i=1}^N \\lambda_i(t)}",
            "equation_kind": "effective_dimensionality_diagnostic",
            "source_ids": ["PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK", "PUB:BOCKER_2025_LEIBNIZ_EXTENDED"],
            "source_fragment_ids": ["FRAG:BOCKER_2025_DIAGNOSTIC_TRINITY"],
            "transcription_status": "primary_text_transcription",
            "verification_status": "verified_primary",
            "symbol_ids": ["SYMBOL:LB_RHO_K", "SYMBOL:LB_LAMBDA_I"],
            "input_symbol_ids": ["SYMBOL:LB_LAMBDA_I"],
            "output_symbol_ids": ["SYMBOL:LB_RHO_K"],
            "assumption_ids": ["ASSUMPTION:LB_NON_ZERO_VARIANCE"],
            "invariant_ids": ["INVARIANT:LB_COHERENCE_UNIT_BOUNDS"],
            "behavioral_test_ids": ["TEST:LB_COHERENCE_BOUNDS"],
            "native_context": "Fraction of total incremental variance captured by leading k modes on Gr(k, N).",
            "notes": "Quantifies the effective dimensional confinement of system motion.",
        },
        {
            "id": "EQ:BOCKER_2025_SUBSPACE_CURVATURE",
            "type": "EQUATION",
            "namespace": "MOD",
            "label": "Leibniz-Bocker max-angle Grassmannian rotational curvature",
            "latex": "\\Omega_k(t) = \\frac{1}{\\Delta t} \\max_{1 \\le i \\le k} \\theta_i(t, t+\\Delta t)",
            "original_notation": "\\Omega_k(t) = \\frac{1}{\\Delta t} \\max_i \\theta_i(t, t+\\Delta t)",
            "normalized_notation": "\\Omega_k(t) = \\frac{1}{\\Delta t} \\max_{1 \\le i \\le k} \\theta_i(t, t+\\Delta t)",
            "equation_kind": "grassmannian_rotational_curvature",
            "source_ids": ["PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK", "PUB:BOCKER_2025_LEIBNIZ_EXTENDED"],
            "source_fragment_ids": ["FRAG:BOCKER_2025_DIAGNOSTIC_TRINITY"],
            "transcription_status": "primary_text_transcription",
            "verification_status": "verified_primary",
            "symbol_ids": ["SYMBOL:LB_OMEGA_K", "SYMBOL:LB_THETA_I", "SYMBOL:LB_DELTA_T"],
            "input_symbol_ids": ["SYMBOL:LB_THETA_I", "SYMBOL:LB_DELTA_T"],
            "output_symbol_ids": ["SYMBOL:LB_OMEGA_K"],
            "assumption_ids": ["ASSUMPTION:LB_SPECTRAL_GAP"],
            "invariant_ids": ["INVARIANT:LB_CURVATURE_NON_NEGATIVE"],
            "behavioral_test_ids": ["TEST:LB_ZERO_ROTATION_CURVATURE"],
            "native_context": "Rate of dominant subspace rotation on Gr(k, N) via maximal principal angle, detecting instantaneous rotational shocks.",
            "notes": "Spikes in curvature signal structural regime reorientations.",
        },
        {
            "id": "EQ:BOCKER_2025_PROJECTOR_CURVATURE",
            "type": "EQUATION",
            "namespace": "MOD",
            "label": "Leibniz-Bocker complementary projector-based curvature",
            "latex": "\\tilde{\\Omega}_k(t) = \\frac{1}{\\Delta t} \\| P_{t+\\Delta t} - P_t \\|_F",
            "original_notation": "\\tilde{\\Omega}_k(t) = \\frac{1}{\\Delta t} ||P_{t+\\Delta t} - P_t||_F",
            "normalized_notation": "\\tilde{\\Omega}_k(t) = \\frac{1}{\\Delta t} \\| P_{t+\\Delta t} - P_t \\|_F",
            "equation_kind": "grassmannian_projector_curvature",
            "source_ids": ["PUB:BOCKER_2025_LEIBNIZ_EXTENDED"],
            "source_fragment_ids": ["FRAG:BOCKER_2025_DIAGNOSTIC_TRINITY"],
            "transcription_status": "primary_text_transcription",
            "verification_status": "verified_primary",
            "symbol_ids": ["SYMBOL:LB_OMEGA_TILDE_K", "SYMBOL:LB_P_T", "SYMBOL:LB_DELTA_T"],
            "input_symbol_ids": ["SYMBOL:LB_P_T", "SYMBOL:LB_DELTA_T"],
            "output_symbol_ids": ["SYMBOL:LB_OMEGA_TILDE_K"],
            "assumption_ids": ["ASSUMPTION:LB_SMOOTH_COVARIANCE"],
            "invariant_ids": ["INVARIANT:LB_PROJECTOR_IDEMPOTENCE"],
            "behavioral_test_ids": ["TEST:LB_PROJECTOR_IDENTITY"],
            "native_context": "Rotationally invariant Frobenius rate of projector evolution capturing total rotational energy on Gr(k, N).",
            "notes": "Forms two-scale curvature monitor with Omega_k.",
        },
        {
            "id": "EQ:BOCKER_2025_STREAMING_OJA_UPDATE",
            "type": "EQUATION",
            "namespace": "MOD",
            "label": "Leibniz-Bocker online streaming subspace tracking update",
            "latex": "W_{t+1}^* = W_t + \\eta_t \\phi(t)\\phi(t)^\\top W_t",
            "original_notation": "W_{t+1}^* = W_t + \\eta_t U_t, U_t = \\phi \\phi^T W_t",
            "normalized_notation": "W_{t+1}^* = W_t + \\eta_t \\phi(t)\\phi(t)^\\top W_t",
            "equation_kind": "streaming_subspace_tracker",
            "source_ids": ["PUB:BOCKER_2025_LEIBNIZ_EXTENDED"],
            "source_fragment_ids": ["FRAG:BOCKER_2025_STREAMING_OJA"],
            "transcription_status": "primary_text_transcription",
            "verification_status": "verified_primary",
            "symbol_ids": ["SYMBOL:LB_W_T", "SYMBOL:LB_PHI_T", "SYMBOL:LB_ETA_T"],
            "input_symbol_ids": ["SYMBOL:LB_W_T", "SYMBOL:LB_PHI_T", "SYMBOL:LB_ETA_T"],
            "output_symbol_ids": ["SYMBOL:LB_W_T"],
            "assumption_ids": ["ASSUMPTION:LB_BOUNDED_INCREMENTS"],
            "invariant_ids": ["INVARIANT:LB_ORTHONORMAL_FRAME"],
            "behavioral_test_ids": ["TEST:LB_OJA_STEP_ALIGNMENT"],
            "native_context": "Oja-style streaming update followed by QR orthonormalization for low-overhead real-time Grassmannian tracking.",
            "notes": "Reduces per-step tracking complexity from O(N^3) to O(k N^2).",
        },
    ]
    added_eq = append_records(ROOT / "graph" / "equations.jsonl", equations)
    print(f"[+] Equations: added {added_eq} records")

    # 10. Edges
    edges = [
        # Authorship
        {"id": "EDGE:BOCKER_AUTHORED_FRAMEWORK", "type": "EDGE", "namespace": "MOD", "label": "Bocker authored 2025 standalone framework preprint", "edge_type": "AUTHORED", "source": "PERSON:BOCKER_NJ", "target": "PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK"},
        {"id": "EDGE:BOCKER_AUTHORED_EXTENDED", "type": "EDGE", "namespace": "MOD", "label": "Bocker authored 2025 extended diagnostics preprint", "edge_type": "AUTHORED", "source": "PERSON:BOCKER_NJ", "target": "PUB:BOCKER_2025_LEIBNIZ_EXTENDED"},

        # Fragments EXTRACTED_FROM Sources
        {"id": "EDGE:FRAG_LB_INCREMENT_EXTRACTED", "type": "EDGE", "namespace": "MOD", "label": "Increment fragment extracted from 2025 framework preprint", "edge_type": "EXTRACTED_FROM", "source": "FRAG:BOCKER_2025_INCREMENT_DEFINITION", "target": "PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK"},
        {"id": "EDGE:FRAG_LB_COVARIANCE_EXTRACTED", "type": "EDGE", "namespace": "MOD", "label": "Covariance fragment extracted from 2025 framework preprint", "edge_type": "EXTRACTED_FROM", "source": "FRAG:BOCKER_2025_COVARIANCE_OPERATOR", "target": "PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK"},
        {"id": "EDGE:FRAG_LB_DECOMPOSITION_EXTRACTED", "type": "EDGE", "namespace": "MOD", "label": "Decomposition fragment extracted from 2025 framework preprint", "edge_type": "EXTRACTED_FROM", "source": "FRAG:BOCKER_2025_DECOMPOSITION_OF_MOTION", "target": "PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK"},
        {"id": "EDGE:FRAG_LB_DIAGNOSTIC_EXTRACTED", "type": "EDGE", "namespace": "MOD", "label": "Diagnostic trinity fragment extracted from 2025 framework preprint", "edge_type": "EXTRACTED_FROM", "source": "FRAG:BOCKER_2025_DIAGNOSTIC_TRINITY", "target": "PUB:BOCKER_2025_LEIBNIZ_FRAMEWORK"},
        {"id": "EDGE:FRAG_LB_OJA_EXTRACTED", "type": "EDGE", "namespace": "MOD", "label": "Streaming Oja fragment extracted from 2025 extended preprint", "edge_type": "EXTRACTED_FROM", "source": "FRAG:BOCKER_2025_STREAMING_OJA", "target": "PUB:BOCKER_2025_LEIBNIZ_EXTENDED"},

        # Fragments ENCODES_EQUATION (Mandatory in validate_graph.py)
        {"id": "EDGE:FRAG_ENCODES_EQ_INCREMENT", "type": "EDGE", "namespace": "MOD", "label": "Fragment encodes infinitesimal increment equation", "edge_type": "ENCODES_EQUATION", "source": "FRAG:BOCKER_2025_INCREMENT_DEFINITION", "target": "EQ:BOCKER_2025_INCREMENT"},
        {"id": "EDGE:FRAG_ENCODES_EQ_COVARIANCE", "type": "EDGE", "namespace": "MOD", "label": "Fragment encodes increment covariance equation", "edge_type": "ENCODES_EQUATION", "source": "FRAG:BOCKER_2025_COVARIANCE_OPERATOR", "target": "EQ:BOCKER_2025_INCREMENT_COVARIANCE"},
        {"id": "EDGE:FRAG_ENCODES_EQ_DECOMPOSITION", "type": "EDGE", "namespace": "MOD", "label": "Fragment encodes motion decomposition equation", "edge_type": "ENCODES_EQUATION", "source": "FRAG:BOCKER_2025_DECOMPOSITION_OF_MOTION", "target": "EQ:BOCKER_2025_MOTION_DECOMPOSITION"},
        {"id": "EDGE:FRAG_ENCODES_EQ_COHERENCE", "type": "EDGE", "namespace": "MOD", "label": "Fragment encodes spectral coherence equation", "edge_type": "ENCODES_EQUATION", "source": "FRAG:BOCKER_2025_DIAGNOSTIC_TRINITY", "target": "EQ:BOCKER_2025_COHERENCE"},
        {"id": "EDGE:FRAG_ENCODES_EQ_SUBSPACE_CURVATURE", "type": "EDGE", "namespace": "MOD", "label": "Fragment encodes max-angle curvature equation", "edge_type": "ENCODES_EQUATION", "source": "FRAG:BOCKER_2025_DIAGNOSTIC_TRINITY", "target": "EQ:BOCKER_2025_SUBSPACE_CURVATURE"},
        {"id": "EDGE:FRAG_ENCODES_EQ_PROJECTOR_CURVATURE", "type": "EDGE", "namespace": "MOD", "label": "Fragment encodes projector curvature equation", "edge_type": "ENCODES_EQUATION", "source": "FRAG:BOCKER_2025_DIAGNOSTIC_TRINITY", "target": "EQ:BOCKER_2025_PROJECTOR_CURVATURE"},
        {"id": "EDGE:FRAG_ENCODES_EQ_OJA", "type": "EDGE", "namespace": "MOD", "label": "Fragment encodes streaming Oja tracking equation", "edge_type": "ENCODES_EQUATION", "source": "FRAG:BOCKER_2025_STREAMING_OJA", "target": "EQ:BOCKER_2025_STREAMING_OJA_UPDATE"},

        # Equations MEMBER_OF_EQUATION_FAMILY
        {"id": "EDGE:EQ_INCREMENT_IN_FAMILY", "type": "EDGE", "namespace": "MOD", "label": "Increment equation member of Leibniz-Bocker family", "edge_type": "MEMBER_OF_EQUATION_FAMILY", "source": "EQ:BOCKER_2025_INCREMENT", "target": "FAMILY:LEIBNIZ_BOCKER_GEOMETRIC_MOTION"},
        {"id": "EDGE:EQ_COVARIANCE_IN_FAMILY", "type": "EDGE", "namespace": "MOD", "label": "Covariance equation member of Leibniz-Bocker family", "edge_type": "MEMBER_OF_EQUATION_FAMILY", "source": "EQ:BOCKER_2025_INCREMENT_COVARIANCE", "target": "FAMILY:LEIBNIZ_BOCKER_GEOMETRIC_MOTION"},
        {"id": "EDGE:EQ_DECOMPOSITION_IN_FAMILY", "type": "EDGE", "namespace": "MOD", "label": "Decomposition equation member of Leibniz-Bocker family", "edge_type": "MEMBER_OF_EQUATION_FAMILY", "source": "EQ:BOCKER_2025_MOTION_DECOMPOSITION", "target": "FAMILY:LEIBNIZ_BOCKER_GEOMETRIC_MOTION"},
        {"id": "EDGE:EQ_COHERENCE_IN_FAMILY", "type": "EDGE", "namespace": "MOD", "label": "Coherence equation member of Leibniz-Bocker family", "edge_type": "MEMBER_OF_EQUATION_FAMILY", "source": "EQ:BOCKER_2025_COHERENCE", "target": "FAMILY:LEIBNIZ_BOCKER_GEOMETRIC_MOTION"},
        {"id": "EDGE:EQ_SUBSPACE_CURVATURE_IN_FAMILY", "type": "EDGE", "namespace": "MOD", "label": "Subspace curvature equation member of Leibniz-Bocker family", "edge_type": "MEMBER_OF_EQUATION_FAMILY", "source": "EQ:BOCKER_2025_SUBSPACE_CURVATURE", "target": "FAMILY:LEIBNIZ_BOCKER_GEOMETRIC_MOTION"},
        {"id": "EDGE:EQ_PROJECTOR_CURVATURE_IN_FAMILY", "type": "EDGE", "namespace": "MOD", "label": "Projector curvature equation member of Leibniz-Bocker family", "edge_type": "MEMBER_OF_EQUATION_FAMILY", "source": "EQ:BOCKER_2025_PROJECTOR_CURVATURE", "target": "FAMILY:LEIBNIZ_BOCKER_GEOMETRIC_MOTION"},
        {"id": "EDGE:EQ_OJA_IN_FAMILY", "type": "EDGE", "namespace": "MOD", "label": "Streaming Oja equation member of Leibniz-Bocker family", "edge_type": "MEMBER_OF_EQUATION_FAMILY", "source": "EQ:BOCKER_2025_STREAMING_OJA_UPDATE", "target": "FAMILY:LEIBNIZ_BOCKER_GEOMETRIC_MOTION"},

        # Equations HAS_BEHAVIORAL_TEST
        {"id": "EDGE:EQ_INCREMENT_HAS_TEST", "type": "EDGE", "namespace": "MOD", "label": "Increment equation has zero test", "edge_type": "HAS_BEHAVIORAL_TEST", "source": "EQ:BOCKER_2025_INCREMENT", "target": "TEST:LB_STATIC_ZERO_INCREMENT"},
        {"id": "EDGE:EQ_COVARIANCE_HAS_TEST", "type": "EDGE", "namespace": "MOD", "label": "Covariance equation has PSD test", "edge_type": "HAS_BEHAVIORAL_TEST", "source": "EQ:BOCKER_2025_INCREMENT_COVARIANCE", "target": "TEST:LB_COVARIANCE_PSD"},
        {"id": "EDGE:EQ_DECOMPOSITION_HAS_TEST", "type": "EDGE", "namespace": "MOD", "label": "Decomposition equation has orthogonality test", "edge_type": "HAS_BEHAVIORAL_TEST", "source": "EQ:BOCKER_2025_MOTION_DECOMPOSITION", "target": "TEST:LB_RESIDUAL_ORTHOGONALITY"},
        {"id": "EDGE:EQ_COHERENCE_HAS_TEST", "type": "EDGE", "namespace": "MOD", "label": "Coherence equation has bounds test", "edge_type": "HAS_BEHAVIORAL_TEST", "source": "EQ:BOCKER_2025_COHERENCE", "target": "TEST:LB_COHERENCE_BOUNDS"},
        {"id": "EDGE:EQ_SUBSPACE_CURVATURE_HAS_TEST", "type": "EDGE", "namespace": "MOD", "label": "Subspace curvature equation has zero test", "edge_type": "HAS_BEHAVIORAL_TEST", "source": "EQ:BOCKER_2025_SUBSPACE_CURVATURE", "target": "TEST:LB_ZERO_ROTATION_CURVATURE"},
        {"id": "EDGE:EQ_PROJECTOR_CURVATURE_HAS_TEST", "type": "EDGE", "namespace": "MOD", "label": "Projector curvature equation has identity test", "edge_type": "HAS_BEHAVIORAL_TEST", "source": "EQ:BOCKER_2025_PROJECTOR_CURVATURE", "target": "TEST:LB_PROJECTOR_IDENTITY"},
        {"id": "EDGE:EQ_OJA_HAS_TEST", "type": "EDGE", "namespace": "MOD", "label": "Streaming Oja equation has alignment test", "edge_type": "HAS_BEHAVIORAL_TEST", "source": "EQ:BOCKER_2025_STREAMING_OJA_UPDATE", "target": "TEST:LB_OJA_STEP_ALIGNMENT"},

        # Equations HAS_ASSUMPTION
        {"id": "EDGE:EQ_INCREMENT_HAS_ASSUMPTION", "type": "EDGE", "namespace": "MOD", "label": "Increment equation has bounded assumption", "edge_type": "HAS_ASSUMPTION", "source": "EQ:BOCKER_2025_INCREMENT", "target": "ASSUMPTION:LB_BOUNDED_INCREMENTS"},
        {"id": "EDGE:EQ_COVARIANCE_HAS_ASSUMPTION", "type": "EDGE", "namespace": "MOD", "label": "Covariance equation has stationarity assumption", "edge_type": "HAS_ASSUMPTION", "source": "EQ:BOCKER_2025_INCREMENT_COVARIANCE", "target": "ASSUMPTION:LB_LOCAL_STATIONARITY"},
        {"id": "EDGE:EQ_DECOMPOSITION_HAS_ASSUMPTION", "type": "EDGE", "namespace": "MOD", "label": "Decomposition equation has spectral gap assumption", "edge_type": "HAS_ASSUMPTION", "source": "EQ:BOCKER_2025_MOTION_DECOMPOSITION", "target": "ASSUMPTION:LB_SPECTRAL_GAP"},
        {"id": "EDGE:EQ_COHERENCE_HAS_ASSUMPTION", "type": "EDGE", "namespace": "MOD", "label": "Coherence equation has non-zero variance assumption", "edge_type": "HAS_ASSUMPTION", "source": "EQ:BOCKER_2025_COHERENCE", "target": "ASSUMPTION:LB_NON_ZERO_VARIANCE"},
        {"id": "EDGE:EQ_CURVATURE_HAS_ASSUMPTION", "type": "EDGE", "namespace": "MOD", "label": "Curvature equation has spectral gap assumption", "edge_type": "HAS_ASSUMPTION", "source": "EQ:BOCKER_2025_SUBSPACE_CURVATURE", "target": "ASSUMPTION:LB_SPECTRAL_GAP"},
        {"id": "EDGE:EQ_PROJECTOR_HAS_ASSUMPTION", "type": "EDGE", "namespace": "MOD", "label": "Projector curvature has smooth covariance assumption", "edge_type": "HAS_ASSUMPTION", "source": "EQ:BOCKER_2025_PROJECTOR_CURVATURE", "target": "ASSUMPTION:LB_SMOOTH_COVARIANCE"},
        {"id": "EDGE:EQ_OJA_HAS_ASSUMPTION", "type": "EDGE", "namespace": "MOD", "label": "Streaming Oja has bounded increments assumption", "edge_type": "HAS_ASSUMPTION", "source": "EQ:BOCKER_2025_STREAMING_OJA_UPDATE", "target": "ASSUMPTION:LB_BOUNDED_INCREMENTS"},

        # Equations PRESERVES_INVARIANT
        {"id": "EDGE:EQ_INCREMENT_PRESERVES_INVARIANT", "type": "EDGE", "namespace": "MOD", "label": "Increment preserves translation drift invariant", "edge_type": "PRESERVES_INVARIANT", "source": "EQ:BOCKER_2025_INCREMENT", "target": "INVARIANT:LB_TRANSLATIONAL_DRIFT"},
        {"id": "EDGE:EQ_COVARIANCE_PRESERVES_INVARIANT", "type": "EDGE", "namespace": "MOD", "label": "Covariance preserves PSD symmetry invariant", "edge_type": "PRESERVES_INVARIANT", "source": "EQ:BOCKER_2025_INCREMENT_COVARIANCE", "target": "INVARIANT:LB_COVARIANCE_SYMMETRY_PSD"},
        {"id": "EDGE:EQ_DECOMPOSITION_PRESERVES_INVARIANT", "type": "EDGE", "namespace": "MOD", "label": "Decomposition preserves orthogonal residual invariant", "edge_type": "PRESERVES_INVARIANT", "source": "EQ:BOCKER_2025_MOTION_DECOMPOSITION", "target": "INVARIANT:LB_ORTHOGONAL_RESIDUAL"},
        {"id": "EDGE:EQ_COHERENCE_PRESERVES_INVARIANT", "type": "EDGE", "namespace": "MOD", "label": "Coherence preserves unit bounds invariant", "edge_type": "PRESERVES_INVARIANT", "source": "EQ:BOCKER_2025_COHERENCE", "target": "INVARIANT:LB_COHERENCE_UNIT_BOUNDS"},
        {"id": "EDGE:EQ_CURVATURE_PRESERVES_INVARIANT", "type": "EDGE", "namespace": "MOD", "label": "Curvature preserves non-negativity invariant", "edge_type": "PRESERVES_INVARIANT", "source": "EQ:BOCKER_2025_SUBSPACE_CURVATURE", "target": "INVARIANT:LB_CURVATURE_NON_NEGATIVE"},
        {"id": "EDGE:EQ_PROJECTOR_PRESERVES_INVARIANT", "type": "EDGE", "namespace": "MOD", "label": "Projector curvature preserves idempotence invariant", "edge_type": "PRESERVES_INVARIANT", "source": "EQ:BOCKER_2025_PROJECTOR_CURVATURE", "target": "INVARIANT:LB_PROJECTOR_IDEMPOTENCE"},
        {"id": "EDGE:EQ_OJA_PRESERVES_INVARIANT", "type": "EDGE", "namespace": "MOD", "label": "Streaming Oja preserves orthonormal frame invariant", "edge_type": "PRESERVES_INVARIANT", "source": "EQ:BOCKER_2025_STREAMING_OJA_UPDATE", "target": "INVARIANT:LB_ORTHONORMAL_FRAME"},

        # Structural Analogy Bridge (MODERN_FORMAL_ANALOGUE to SOVCTX relation-first mathematical grammar)
        {
            "id": "EDGE:LB_ANALOGUE_TO_LYAPUNOV_STABILITY",
            "type": "EDGE",
            "namespace": "MOD",
            "label": "Leibniz-Bocker Grassmannian motion family is structurally analogous to Lyapunov stability and structural motion systems",
            "edge_type": "STRUCTURALLY_ANALOGOUS_TO",
            "source": "FAMILY:LEIBNIZ_BOCKER_GEOMETRIC_MOTION",
            "target": "FAMILY:LYAPUNOV_STABILITY",
        },
    ]
    added_edg = append_records(ROOT / "graph" / "edges.jsonl", edges)
    print(f"[+] Edges: added {added_edg} records")

    print("\n[+] Leibniz-Bocker Equation Intake Complete.")


if __name__ == "__main__":
    main()
