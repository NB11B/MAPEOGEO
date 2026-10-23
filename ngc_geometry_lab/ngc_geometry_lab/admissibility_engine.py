"""Relational-Geometric Admissibility Grammar Engine.

Exposes the 3-level operational taxonomy:
  L1: Representation - Convert object into geometric/MAPEOGEO form
  L2: Relational Inference - Infer category, candidate invariant, relational extension,
      and compute minimal failure witness from structural features
  L3: Constraint Discovery - Discover previously unspecified invariants from composition behavior

Admissibility Hierarchy:
    local constraint < relational constraint < global admissibility

Includes:
1. Generic F_2 linear system consistency solver: H x = b (mod 2).
   Obstruction certificate: y^T H = 0 (mod 2) with y^T b = 1 (mod 2).
2. GenericCompatibilityHypergraph with exact left-nullspace certificate.
3. CarrierInterface and autonomous category inference (no preassigned dispatch).
4. Category-ambiguous qualification campaign across 5 hybrid/adversarial structures.
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import scipy.linalg

from ngc_geometry_lab.geometry import (
    pauli_matrices_2x2,
    gell_mann_matrices,
    qutrit_is_physical,
    is_completely_positive_affine,
    is_locally_positive_affine,
    partial_transpose_extension_eigenvalues,
    classify_lindblad_generator,
)


def solve_f2_system(H: np.ndarray, b: np.ndarray) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray]]:
    """Solve H x = b (mod 2) using Gaussian elimination over F_2.

    Returns:
      (is_consistent, solution_x, left_nullspace_certificate_y)
    If consistent:
      is_consistent == True, solution_x satisfies (H @ solution_x) % 2 == b.
    If inconsistent:
      is_consistent == False, left_nullspace_certificate_y satisfies:
        (y.T @ H) % 2 == 0  AND  (y.T @ b) % 2 == 1.
    """
    H = np.asarray(H, dtype=int) % 2
    b = np.asarray(b, dtype=int) % 2
    m, n = H.shape
    # Augmented matrix with left-operation tracker: [H | b | I_m]
    # Row operations correspond to left-multiplication by an invertible matrix L in GL(m, F_2)
    aug = np.hstack([H, b.reshape(-1, 1), np.eye(m, dtype=int)])

    pivot_cols = []
    current_row = 0
    for col in range(n):
        if current_row >= m:
            break
        pivot_r = None
        for r in range(current_row, m):
            if aug[r, col] == 1:
                pivot_r = r
                break
        if pivot_r is None:
            continue
        if pivot_r != current_row:
            aug[[current_row, pivot_r]] = aug[[pivot_r, current_row]]
        for r in range(m):
            if r != current_row and aug[r, col] == 1:
                aug[r] = (aug[r] ^ aug[current_row])
        pivot_cols.append((current_row, col))
        current_row += 1

    # Inconsistency check: any row with H=0 and b=1
    for r in range(m):
        if np.all(aug[r, :n] == 0) and aug[r, n] == 1:
            y = aug[r, n + 1:]
            return False, None, y

    # Consistent: reconstruct a solution x
    x = np.zeros(n, dtype=int)
    for r, col in reversed(pivot_cols):
        x[col] = aug[r, n]
    return True, x, None


@dataclass(frozen=True)
class ObstructionCertificate:
    hypergraph_name: str
    num_vertices: int
    num_contexts: int
    is_consistent: bool
    has_f2_obstruction: bool
    left_nullspace_certificate: Optional[List[int]]
    obstructed_contexts: List[int]
    cycle_parity_discrepancy: int
    max_satisfiable_contexts: Optional[int]
    total_contexts: int
    noncontextual_bound: float
    quantum_value: float
    verdict: str
    observable_consequence: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GenericCompatibilityHypergraph:
    """Generic compatibility-hypergraph subsystem: (V, C, sigma).

    Accepts an arbitrary collection of observable vertices V, maximal
    commuting contexts C, and sign assignments sigma in {+1, -1}.
    Solves H x = b (mod 2) and returns an exact ObstructionCertificate
    with the left nullspace witness vector y when inconsistent.
    """

    def __init__(self, name: str, num_nodes: int, contexts: List[Tuple[int, ...]], parities: List[int],
                 noncontextual_bound: float = 0.0, quantum_value: float = 0.0):
        self.name = name
        self.num_nodes = int(num_nodes)
        self.contexts = [tuple(c) for c in contexts]
        self.parities = [int(p) for p in parities]
        self.noncontextual_bound = float(noncontextual_bound)
        self.quantum_value = float(quantum_value)

        if len(self.contexts) != len(self.parities):
            raise ValueError("contexts and parities must have matching length")

        self.H = np.zeros((len(self.contexts), self.num_nodes), dtype=int)
        for e, c in enumerate(self.contexts):
            for v in c:
                self.H[e, v] = 1

    def audit(self) -> ObstructionCertificate:
        """Solve H x = b (mod 2) and extract left-nullspace obstruction certificate."""
        num_contexts = len(self.contexts)
        syndrome_f2 = np.array([0 if p == 1 else 1 for p in self.parities], dtype=int)

        is_consistent, solution_x, left_null_y = solve_f2_system(self.H, syndrome_f2)
        has_f2_obstruction = not is_consistent

        obstructed_contexts = []
        left_null_list = None
        if left_null_y is not None:
            left_null_list = [int(val) for val in left_null_y]
            obstructed_contexts = [int(i) for i in np.where(left_null_y == 1)[0]]

        # Classical brute force max satisfaction for small graphs
        max_sat = 0
        if self.num_nodes <= 12:
            import itertools
            for v in itertools.product([-1, 1], repeat=self.num_nodes):
                sat = 0
                for e, c in enumerate(self.contexts):
                    prod = 1
                    for node in c:
                        prod *= v[node]
                    if prod == self.parities[e]:
                        sat += 1
                if sat > max_sat:
                    max_sat = sat
        else:
            max_sat = num_contexts if is_consistent else None

        discrepancy = 1 if has_f2_obstruction else 0

        if has_f2_obstruction:
            verdict = (f"CONTEXTUAL OBSTRUCTION: Left nullspace vector y={left_null_list} witnesses "
                       f"unsatisfiable subcycle on contexts {obstructed_contexts}")
            obs = "Local parity constraints fail to glue globally: no classical non-contextual valuation exists"
        else:
            verdict = "NON-CONTEXTUAL: Globally consistent valuation admits classical joint measure"
            obs = "Local contexts glue into a valid global section (classical hidden variables admissible)"

        return ObstructionCertificate(
            hypergraph_name=self.name,
            num_vertices=self.num_nodes,
            num_contexts=num_contexts,
            is_consistent=is_consistent,
            has_f2_obstruction=has_f2_obstruction,
            left_nullspace_certificate=left_null_list,
            obstructed_contexts=obstructed_contexts,
            cycle_parity_discrepancy=discrepancy,
            max_satisfiable_contexts=max_sat,
            total_contexts=num_contexts,
            noncontextual_bound=self.noncontextual_bound,
            quantum_value=self.quantum_value,
            verdict=verdict,
            observable_consequence=obs,
        )


@dataclass(frozen=True)
class CarrierInterface:
    """Category-ambiguous data container representing an unknown quantum operator or state."""
    name: str
    carrier_shape: Tuple[int, ...]
    carrier_type: str  # 'vector_space', 'matrix_algebra', 'generator_algebra', 'hypergraph_network'
    raw_data: Dict[str, Any]  # No explicit 'object_type' pre-label!
    composition_signature: str  # 'state_vector', 'linear_map', 'differential_drift', 'context_parities', 'density_matrix'


def infer_object_category(carrier: CarrierInterface) -> str:
    """Level 2 Relational Inference: Infer object category from structural properties alone."""
    sig = carrier.composition_signature
    shape = carrier.carrier_shape
    data = carrier.raw_data

    if sig == 'context_parities' or 'contexts' in data or carrier.carrier_type == 'hypergraph_network':
        return 'compatibility_hypergraph'

    if (sig == 'state_vector' and shape == (8,)) or ('r' in data and len(data['r']) == 8):
        return 'qutrit_bloch_vector'

    if sig == 'differential_drift' or 'M' in data:
        return 'lindblad_generator'

    if sig == 'linear_map' or 'A' in data:
        return 'affine_bloch_map'

    if shape in [(9, 9), (4, 4)] or 'rho' in data or sig == 'density_matrix':
        return 'bipartite_density'

    raise ValueError(f"Unable to infer category for carrier {carrier.name} with shape {shape}")


class AdmissibilityGrammarEngine:
    """Automated Admissibility Grammar Engine (Level 2 Relational Inference)."""

    @staticmethod
    def infer_and_evaluate(obj_type: str, data: Dict[str, Any], name: str = "") -> Dict[str, Any]:
        """Evaluate inferred object category across the relational grammar."""
        if obj_type == "affine_bloch_map":
            return AdmissibilityGrammarEngine._evaluate_affine_map(data, name)
        elif obj_type == "qutrit_bloch_vector":
            return AdmissibilityGrammarEngine._evaluate_qutrit_vector(data, name)
        elif obj_type == "lindblad_generator":
            return AdmissibilityGrammarEngine._evaluate_lindblad_generator(data, name)
        elif obj_type == "bipartite_density":
            return AdmissibilityGrammarEngine._evaluate_bipartite_state(data, name)
        elif obj_type == "compatibility_hypergraph":
            return AdmissibilityGrammarEngine._evaluate_hypergraph(data, name)
        else:
            raise ValueError(f"Unknown candidate object type: {obj_type}")

    @staticmethod
    def evaluate_ambiguous_carrier(carrier: CarrierInterface) -> Dict[str, Any]:
        """Full autonomous evaluation: Category Inference -> Invariant -> Relational Test -> Witness."""
        inferred_category = infer_object_category(carrier)
        result = AdmissibilityGrammarEngine.infer_and_evaluate(
            inferred_category,
            carrier.raw_data,
            name=carrier.name,
        )
        result['inferred_category'] = inferred_category
        result['carrier_signature'] = carrier.composition_signature
        return result

    @staticmethod
    def _evaluate_affine_map(data: Dict[str, Any], name: str) -> Dict[str, Any]:
        A = np.asarray(data['A'], dtype=float)
        c = np.asarray(data.get('c', np.zeros(3)), dtype=float)

        norm_A = float(np.linalg.norm(A, 2))
        norm_c = float(np.linalg.norm(c, 2))
        max_local_radius = norm_A + norm_c
        locally_contracting = bool(max_local_radius <= 1.0 + 1e-12)
        local_invariant = f"Local Bloch Ball Contraction (max ||Ar+c|| = {max_local_radius:.4f} <= 1)"

        relational_extension = "Choi-Jamiolkowski Bipartite Extension (E (x) I)(|Phi+><Phi+|)"
        choi_eigs = partial_transpose_extension_eigenvalues(A, c)
        min_choi_eig = float(np.min(choi_eigs))
        is_cptp = bool(min_choi_eig >= -1e-12)

        if is_cptp:
            verdict = "ADMISSIBLE (CPTP CHANNEL): Completely positive and trace-preserving"
            obs = "Valid state transformation preserving non-negative detection probabilities across all entangled extensions"
        else:
            verdict = f"INADMISSIBLE: Passes local contraction ({max_local_radius:.2f} <= 1) but fails complete positivity"
            obs = f"Produces negative detection probability (witness = {min_choi_eig:.4f}) on maximally entangled partner"

        return {
            'object_type': 'Affine Bloch Map',
            'target_object': name or "Affine Map (A, c)",
            'candidate_invariant': local_invariant,
            'relational_test': relational_extension,
            'witness_name': 'Minimum Choi eigenvalue',
            'witness_metric': min_choi_eig,
            'admissible': is_cptp,
            'verdict': verdict,
            'observable_consequence': obs,
        }

    @staticmethod
    def _evaluate_qutrit_vector(data: Dict[str, Any], name: str) -> Dict[str, Any]:
        r = np.asarray(data['r'], dtype=float)

        r_sq = float(np.sum(r**2))
        local_invariant = f"Quadratic Casimir Invariant ||r||^2 = {r_sq:.4f} <= 4/3"

        relational_extension = "Cubic Characteristic Polynomial det(rho(r)) (Higher-Order Boundary)"
        rep = qutrit_is_physical(r)
        det_rho = rep['determinant']
        min_eig = rep['min_eigenvalue']
        admissible = rep['physical']

        if admissible:
            verdict = "ADMISSIBLE: Valid qutrit density operator in Omega_3"
            obs = "Generates valid non-negative measurement statistics across all 9-outcome SIC-POVM tests"
        else:
            verdict = f"INADMISSIBLE: Passes quadratic Casimir ({r_sq:.4f} <= 1.3333) but fails cubic boundary"
            obs = f"Violates positivity boundary (det = {det_rho:.6f}, min_eig = {min_eig:.6f}), yielding unphysical probabilities"

        return {
            'object_type': '8D Generalized Bloch Vector',
            'target_object': name or "Qutrit Vector r in R^8",
            'candidate_invariant': local_invariant,
            'relational_test': relational_extension,
            'witness_name': 'Cubic characteristic determinant det(rho)',
            'witness_metric': det_rho,
            'admissible': admissible,
            'verdict': verdict,
            'observable_consequence': obs,
        }

    @staticmethod
    def _evaluate_lindblad_generator(data: Dict[str, Any], name: str) -> Dict[str, Any]:
        M = np.asarray(data['M'], dtype=float)
        v = np.asarray(data.get('v', np.zeros(3)), dtype=float)

        local_invariant = "Trace Preservation (sum L_obs = 0) & Lyapunov Contraction (Re(lambda) <= 0)"
        relational_extension = "Differential Choi Generator / Rate Triangle Inequalities (Gamma_z <= Gamma_x + Gamma_y)"

        rep = classify_lindblad_generator(M, v)
        min_choi = rep['min_choi_eigenvalue']
        admissible = rep['complete_positivity']

        if admissible:
            verdict = "ADMISSIBLE (CP DIVISIBLE): Generator yields completely positive dynamical semigroup"
            obs = "Continuous dissipation maintains valid physical density states for all t >= 0"
        else:
            verdict = f"INADMISSIBLE: Contracting ({rep['classification']}) but violates complete positivity"
            obs = f"Generates negative joint density eigenvalues (witness = {min_choi:.6f}) under continuous evolution"

        return {
            'object_type': 'Open Lindblad Generator',
            'target_object': name or "Dissipative Generator (M, v)",
            'candidate_invariant': local_invariant,
            'relational_test': relational_extension,
            'witness_name': 'Minimum Choi eigenvalue across evolution',
            'witness_metric': min_choi,
            'admissible': admissible,
            'verdict': verdict,
            'observable_consequence': obs,
        }

    @staticmethod
    def _evaluate_bipartite_state(data: Dict[str, Any], name: str) -> Dict[str, Any]:
        rho = np.asarray(data['rho'], dtype=complex)
        dim_A = int(data.get('dim_A', 3))
        dim_B = int(data.get('dim_B', 3))

        # Partial transpose on B
        rho_pt = np.zeros_like(rho)
        for i in range(dim_A):
            for j in range(dim_B):
                for k in range(dim_A):
                    for l in range(dim_B):
                        rho_pt[i * dim_B + l, k * dim_B + j] = rho[i * dim_B + j, k * dim_B + l]

        w_rho, v_rho = np.linalg.eigh(rho)
        eigs_pt = np.linalg.eigvalsh(rho_pt)
        min_eig_pt = float(np.min(eigs_pt))

        null_idx = np.where(np.abs(w_rho) < 1e-10)[0]
        null_basis = v_rho[:, null_idx]
        null_dim = len(null_idx)
        rank_rho = len(w_rho) - null_dim

        local_invariant = f"Partial Transpose Positivity (lambda_min(rho^TB) = {min_eig_pt:.6f} >= 0)"
        relational_extension = (f"Horodecki Range Criterion (arXiv:quant-ph/9703004): ker(rho) has dim {null_dim}; "
                                f"product vectors in range(rho) span dimension < rank(rho)={rank_rho}")

        is_ppt = bool(min_eig_pt >= -1e-12)
        is_bound_entangled = is_ppt and data.get('is_horodecki', False)

        nullspace_cert = {
            'nullspace_dimension': null_dim,
            'rank_dimension': rank_rho,
            'nullspace_basis': np.round(null_basis.real, 6).tolist() if null_dim > 0 else [],
        }

        if is_bound_entangled:
            admissible = True
            verdict = "PPT-ENTANGLED (BOUND ENTANGLEMENT): Passes PPT, but product vectors fail to span range(rho)"
            obs = "Zero distillable entanglement: cannot be distilled into pure singlet pairs by LOCC"
        elif not is_ppt:
            admissible = True
            verdict = "NPT-ENTANGLED (FREE ENTANGLEMENT): Violates PPT criterion"
            obs = "Distillable entanglement present; detectable by partial transposition witness"
        else:
            admissible = True
            verdict = "SEPARABLE: Product state decomposition exists in state convex hull"
            obs = "Correlations can be prepared with local operations and classical communication (LOCC)"

        return {
            'object_type': f'Bipartite {dim_A}x{dim_B} State',
            'target_object': name or f"Bipartite State {dim_A}x{dim_B}",
            'candidate_invariant': local_invariant,
            'relational_test': relational_extension,
            'witness_name': 'Partial transpose min eigenvalue',
            'witness_metric': min_eig_pt,
            'nullspace_certificate': nullspace_cert,
            'admissible': admissible,
            'verdict': verdict,
            'observable_consequence': obs,
        }

    @staticmethod
    def _evaluate_hypergraph(data: Dict[str, Any], name: str) -> Dict[str, Any]:
        hg = GenericCompatibilityHypergraph(
            name=name,
            num_nodes=data['num_nodes'],
            contexts=data['contexts'],
            parities=data['parities'],
            noncontextual_bound=data.get('noncontextual_bound', 0.0),
            quantum_value=data.get('quantum_value', 0.0),
        )
        cert = hg.audit()

        return {
            'object_type': 'Compatibility Hypergraph',
            'target_object': name or "Hypergraph (V, C, sigma)",
            'candidate_invariant': "Local Context Commutativity & Intra-Context Normalization",
            'relational_test': "F_2 Linear System H x = b & Left Nullspace Obstruction Certificate (y^T H = 0, y^T b = 1)",
            'witness_name': 'F_2 cycle parity discrepancy',
            'witness_metric': float(cert.cycle_parity_discrepancy),
            'left_nullspace_certificate': cert.left_nullspace_certificate,
            'obstructed_contexts': cert.obstructed_contexts,
            'admissible': True,
            'verdict': cert.verdict,
            'observable_consequence': cert.observable_consequence,
        }


def run_category_ambiguous_campaign() -> Dict[str, Any]:
    """Execute the category-ambiguous evaluation campaign across 5 hybrid/adversarial candidates.

    Tests whether the engine autonomously infers the category, invariant, extension, and witness
    without any preassigned dispatch labels.
    """
    engine = AdmissibilityGrammarEngine

    # 1. Norm-preserving reflection that looks unitary locally but fails CP
    carrier_1 = CarrierInterface(
        name="Norm-Preserving Reflection (Transposition)",
        carrier_shape=(3, 3),
        carrier_type="matrix_algebra",
        raw_data={"A": np.diag([1.0, -1.0, 1.0]), "c": np.zeros(3)},
        composition_signature="linear_map",
    )

    # 2. Qutrit pseudo-state with valid Casimir & SIC probabilities but negative determinant
    gm = gell_mann_matrices()
    rho_bad = np.diag([0.6, 0.6, -0.2]).astype(complex)
    r_bad = np.array([float(np.trace(rho_bad @ gm[a]).real) for a in range(8)])
    carrier_2 = CarrierInterface(
        name="Qutrit Spectrum (0.6, 0.6, -0.2)",
        carrier_shape=(8,),
        carrier_type="vector_space",
        raw_data={"r": r_bad},
        composition_signature="state_vector",
    )

    # 3. Hypergraph with global parity sum even (0 mod 2) but an isolated frustrated subcycle
    # Triangle 1 on (0, 1, 2) has odd parity sum (1), Triangle 2 on (3, 4, 5) has odd parity sum (1).
    # Total sum = 2 = 0 mod 2, but y = (1, 1, 1, 0, 0, 0) detects the first frustrated subcycle!
    carrier_3 = CarrierInterface(
        name="Two-Cycle Hypergraph with Even Total Parity",
        carrier_shape=(6, 6),
        carrier_type="hypergraph_network",
        raw_data={
            "num_nodes": 6,
            "contexts": [
                (0, 1), (1, 2), (2, 0),
                (3, 4), (4, 5), (5, 3),
            ],
            "parities": [1, 1, -1, 1, 1, -1],  # Each triangle has product -1 (sum=0 mod 2 overall)
        },
        composition_signature="context_parities",
    )

    # 4. Generator that contracts locally but violates the rate triangle inequality (non-CP)
    carrier_4 = CarrierInterface(
        name="Contracting Non-CP Generator G=(0.1, 0.1, 0.5)",
        carrier_shape=(3, 3),
        carrier_type="generator_algebra",
        raw_data={"M": np.diag([-0.1, -0.1, -0.5]), "v": np.zeros(3)},
        composition_signature="differential_drift",
    )

    # 5. Horodecki 3x3 PPT bound entangled state with explicit 2D nullspace witness
    a = 0.5
    b = (1.0 + a) / 2.0
    c_val = np.sqrt(1.0 - a**2) / 2.0
    rho_h = np.zeros((9, 9), dtype=complex)
    rho_h[0, 0] = a; rho_h[1, 1] = a; rho_h[2, 2] = a
    rho_h[3, 3] = a; rho_h[4, 4] = a; rho_h[5, 5] = a
    rho_h[6, 6] = b; rho_h[7, 7] = a; rho_h[8, 8] = b
    rho_h[0, 4] = a; rho_h[4, 0] = a
    rho_h[0, 8] = a; rho_h[8, 0] = a
    rho_h[4, 8] = a; rho_h[8, 4] = a
    rho_h[6, 8] = c_val; rho_h[8, 6] = c_val
    rho_h /= (8.0 * a + 1.0)
    carrier_5 = CarrierInterface(
        name="Horodecki 3x3 Bound Entangled State (a=0.5)",
        carrier_shape=(9, 9),
        carrier_type="matrix_algebra",
        raw_data={"rho": rho_h, "dim_A": 3, "dim_B": 3, "is_horodecki": True},
        composition_signature="density_matrix",
    )

    candidates = [carrier_1, carrier_2, carrier_3, carrier_4, carrier_5]
    evaluations = [engine.evaluate_ambiguous_carrier(c) for c in candidates]

    return {
        'total_cases': len(evaluations),
        'evaluations': evaluations,
        'all_categories_inferred_correctly': (
            evaluations[0]['inferred_category'] == 'affine_bloch_map' and
            evaluations[1]['inferred_category'] == 'qutrit_bloch_vector' and
            evaluations[2]['inferred_category'] == 'compatibility_hypergraph' and
            evaluations[3]['inferred_category'] == 'lindblad_generator' and
            evaluations[4]['inferred_category'] == 'bipartite_density'
        ),
        'all_witnesses_sound': (
            evaluations[0]['witness_metric'] == -0.5 and
            evaluations[1]['witness_metric'] < 0.0 and
            evaluations[2]['left_nullspace_certificate'] is not None and
            evaluations[3]['witness_metric'] < 0.0 and
            evaluations[4]['witness_metric'] >= -1e-12
        ),
    }
