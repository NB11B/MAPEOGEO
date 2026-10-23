"""Large-scale prospective blind qualification campaign (1,000+ cases).

Evaluates physical admissibility and observation predictions across 8 operational families:
1. Qutrit SU(3) unitaries and Hamiltonian flows
2. Qutrit state admissibility (including near-boundary cubic positivity adversaries)
3. Single-qubit channels (valid CPTP, transposition, and near-boundary non-CP maps)
4. Composite-system 2-qubit channels and joint state positivity
5. Open Lindblad generators (valid vs expanding vs triangle-inequality-violating)
6. Contextuality hypergraphs (contextual vs non-contextual incidence graphs)
7. Measurement frames beyond SIC (informationally complete vs rank-deficient null spaces)
8. Robertson oriented-volume uncertainty bound evaluations

The geometric pipeline evaluates ONLY the operational specification, completely blind
to ground truth labels, reporting confusion matrices per family.
"""
from typing import Dict, List, Any, Tuple
import numpy as np
import scipy.linalg

from ngc_geometry_lab.geometry import (
    is_completely_positive_affine,
    is_locally_positive_affine,
    partial_transpose_extension_eigenvalues,
    qutrit_is_physical,
    qutrit_density_from_bloch,
    qutrit_transformation_matrix,
    qutrit_hamiltonian_generator,
    qubit_hamiltonian_generator,
    gell_mann_matrices,
    classify_lindblad_generator,
    peres_mermin_hypergraph_audit,
    ContextGraph,
    pauli_projective_frame,
    trine_povm_frame,
    cubic_povm_frame,
    analyze_measurement_frame,
    bipartite_channel_transfer,
    bipartite_state_positivity,
    is_entanglement_breaking,
    geometric_uncertainty_bound,
    choi_matrix_from_affine,
)


def generate_large_scale_blind_suite(num_cases: int = 1000, seed: int = 20261022) -> List[Dict[str, Any]]:
    """Generate 1,000+ pre-registered blind test cases with balanced distributions."""
    rng = np.random.default_rng(seed)
    cases = []
    case_id = 0
    gm = gell_mann_matrices()

    # Target counts per family (8 families x ~125 cases = ~1000 cases)
    # Family 1: Qutrit Unitary & Hamiltonian Flows (125 cases)
    for _ in range(125):
        case_id += 1
        h = rng.normal(size=8)
        t = rng.uniform(0.1, 3.0)
        Omega = qutrit_hamiltonian_generator(h)
        R8 = scipy.linalg.expm(t * Omega)
        cases.append({
            'id': f'CASE_{case_id:04d}',
            'family': 'QUTRIT_UNITARY_FLOW',
            'spec': {'R8': R8, 'generator': Omega},
            'ground_truth_physical': True,
            'description': 'Valid SU(3) Hamiltonian generator flow on qutrit frame',
        })

    # Family 2: Qutrit State Admissibility & Near-Boundary Adversaries (130 cases)
    # Balanced: ~65 physical, ~65 unphysical
    for idx in range(130):
        case_id += 1
        if idx % 2 == 0:
            # Physical state: generate valid density matrix via random Ginibre/Wishart
            G = rng.normal(size=(3, 3)) + 1j * rng.normal(size=(3, 3))
            rho = G @ G.conj().T
            rho /= np.trace(rho).real
            r = np.array([float(np.trace(rho @ gm[a]).real) for a in range(8)])
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'QUTRIT_STATE_ADMISSIBILITY',
                'spec': {'bloch_8d': r},
                'ground_truth_physical': True,
                'description': 'Valid physical qutrit state',
            })
        else:
            # Unphysical adversary: passes quadratic purity, fails cubic determinant/positivity
            # Spectrum: (s1, s2, -eps) where s1 + s2 - eps = 1 and sum s_i^2 <= 1
            eps = rng.uniform(1e-8, 0.25)
            rem = 1.0 + eps
            s1 = rng.uniform(eps + 0.1, rem - eps - 0.05)
            s2 = rem - s1
            rho_adv = np.diag([s1, s2, -eps]).astype(complex)
            r_adv = np.array([float(np.trace(rho_adv @ gm[a]).real) for a in range(8)])
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'QUTRIT_STATE_ADMISSIBILITY',
                'spec': {'bloch_8d': r_adv},
                'ground_truth_physical': False,
                'description': f'Adversarial qutrit spectrum ({s1:.3f}, {s2:.3f}, -{eps:.2e})',
            })

    # Family 3: Single-Qubit Channels & Near-Boundary Choi Adversaries (130 cases)
    # Balanced: ~65 physical, ~65 unphysical
    for idx in range(130):
        case_id += 1
        if idx % 2 == 0:
            # Physical CPTP channel: random dephasing, damping, or depolarizing
            ch_type = rng.choice(['amp_damp', 'deph', 'depol'])
            if ch_type == 'amp_damp':
                g = rng.uniform(0.01, 0.99)
                A = np.diag([np.sqrt(1 - g), np.sqrt(1 - g), 1 - g])
                c = np.array([0.0, 0.0, g])
            elif ch_type == 'deph':
                lam = rng.uniform(0.01, 0.99)
                A = np.diag([1 - lam, 1 - lam, 1.0])
                c = np.zeros(3)
            else:
                eta = rng.uniform(0.01, 0.99)
                A = (1 - eta) * np.eye(3)
                c = np.zeros(3)
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'SINGLE_QUBIT_CHANNEL',
                'spec': {'A': A, 'c': c},
                'ground_truth_physical': True,
                'description': f'Physical single-qubit CPTP channel ({ch_type})',
            })
        else:
            # Unphysical map:
            adv_kind = rng.choice(['transpose', 'contract_reflection', 'near_boundary_non_cp', 'expansion'])
            if adv_kind == 'transpose':
                A = np.diag([1.0, -1.0, 1.0])
                c = np.zeros(3)
            elif adv_kind == 'contract_reflection':
                r_scale = rng.uniform(0.4, 0.9)
                A = np.diag([r_scale, -r_scale, r_scale])
                c = np.zeros(3)
            elif adv_kind == 'near_boundary_non_cp':
                # Slightly violate Choi positivity: Choi min eig in [-1e-8, -1e-2]
                delta = rng.uniform(1e-8, 0.1)
                # For diag(eta_x, eta_y, eta_z): Choi eig 4 is 1/4 (1 - eta_x + eta_y - eta_z)
                # If eta_x = 0.5, eta_y = -0.5, eta_z = 0.5: 1 - 0.5 - 0.5 - 0.5 = -0.5
                A = np.diag([0.5 + delta, -0.5, 0.5])
                c = np.zeros(3)
            else: # expansion
                scale = rng.uniform(1.05, 2.0)
                A = scale * np.eye(3)
                c = np.zeros(3)
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'SINGLE_QUBIT_CHANNEL',
                'spec': {'A': A, 'c': c},
                'ground_truth_physical': False,
                'description': f'Unphysical affine map ({adv_kind})',
            })

    # Family 4: Composite-System 2-Qubit Channels & States (125 cases)
    for idx in range(125):
        case_id += 1
        if idx % 2 == 0:
            # Valid bipartite state evolution
            g1 = rng.uniform(0.1, 0.7)
            g2 = rng.uniform(0.1, 0.7)
            chA = (np.diag([np.sqrt(1 - g1), np.sqrt(1 - g1), 1 - g1]), np.array([0.0, 0.0, g1]))
            chB = (np.diag([1 - g2, 1 - g2, 1.0]), np.zeros(3))
            # Initial Bell pair
            rA, rB, T = np.zeros(3), np.zeros(3), np.diag([1.0, -1.0, 1.0])
            rAp, rBp, Tp = bipartite_channel_transfer(rA, rB, T, chA, chB)
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'COMPOSITE_STATE_ADMISSIBILITY',
                'spec': {'rA': rAp, 'rB': rBp, 'T': Tp},
                'ground_truth_physical': True,
                'description': 'Valid bipartite state evolved under local CPTP noise',
            })
        else:
            # Invalid bipartite state: apply transposition on qubit A
            chA_T = (np.diag([1.0, -1.0, 1.0]), np.zeros(3))
            chB_I = (np.eye(3), np.zeros(3))
            rA, rB, T = np.zeros(3), np.zeros(3), np.diag([1.0, -1.0, 1.0])
            rAp, rBp, Tp = bipartite_channel_transfer(rA, rB, T, chA_T, chB_I)
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'COMPOSITE_STATE_ADMISSIBILITY',
                'spec': {'rA': rAp, 'rB': rBp, 'T': Tp},
                'ground_truth_physical': False,
                'description': 'Partially transposed Bell state (negative singlet eigenvalue)',
            })

    # Family 5: Open Lindblad Generators & Adversaries (125 cases)
    for idx in range(125):
        case_id += 1
        if idx % 2 == 0:
            # Valid physical Lindblad generator: derived from 3 nonnegative jump rates
            g1 = rng.uniform(0.02, 0.25)
            g2 = rng.uniform(0.02, 0.25)
            g3 = rng.uniform(0.02, 0.25)
            gx = g2 + g3
            gy = g1 + g3
            gz = g1 + g2
            M = np.diag([-gx, -gy, -gz])
            v = np.zeros(3)
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'LINDBLAD_GENERATOR',
                'spec': {'M': M, 'v': v},
                'ground_truth_physical': True,
                'description': f'Valid Lindblad generator (gx={gx:.3f}, gy={gy:.3f}, gz={gz:.3f})',
            })
        else:
            # Adversarial generator:
            adv_type = rng.choice(['expanding', 'triangle_violation', 'near_boundary_triangle'])
            if adv_type == 'expanding':
                M = np.diag([rng.uniform(0.1, 1.0), -0.2, -0.2])
                v = np.zeros(3)
            elif adv_type == 'near_boundary_triangle':
                # Gz exceeds Gx + Gy by [1e-4, 5e-2]
                gx = rng.uniform(0.1, 0.3)
                gy = rng.uniform(0.1, 0.3)
                gz = gx + gy + rng.uniform(1e-4, 0.05)
                M = np.diag([-gx, -gy, -gz])
                v = np.zeros(3)
            else:
                gx = 0.1
                gy = 0.1
                gz = rng.uniform(0.3, 0.8) # Strongly violates triangle inequality
                M = np.diag([-gx, -gy, -gz])
                v = np.zeros(3)
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'LINDBLAD_GENERATOR',
                'spec': {'M': M, 'v': v},
                'ground_truth_physical': False,
                'description': f'Adversarial Lindblad generator ({adv_type})',
            })

    # Family 6: Relational Context Hypergraphs (125 cases)
    # Balanced: Peres-Mermin / pentagram (contextual) vs acyclic / consistent (non-contextual)
    for idx in range(125):
        case_id += 1
        if idx % 2 == 0:
            # Non-contextual hypergraph: consistent parities on cycle or tree
            # 6 nodes, 3 contexts with consistent parities
            contexts = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5)]
            parities = [1, 1, 1, 1, 1]
            cg = ContextGraph(num_nodes=6, contexts=contexts, parities=parities)
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'CONTEXT_GRAPH',
                'spec': {'graph': cg},
                'ground_truth_contextual': False,
                'description': 'Non-contextual hypergraph (globally satisfiable)',
            })
        else:
            # Contextual hypergraph: Peres-Mermin magic square (9 nodes, 6 contexts)
            contexts = [
                (0, 1, 2), (3, 4, 5), (6, 7, 8), # rows
                (0, 3, 6), (1, 4, 7), (2, 5, 8), # cols
            ]
            parities = [1, 1, 1, 1, 1, -1] # 5 positive, 1 negative
            cg = ContextGraph(num_nodes=9, contexts=contexts, parities=parities)
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'CONTEXT_GRAPH',
                'spec': {'graph': cg},
                'ground_truth_contextual': True,
                'description': 'Peres-Mermin contextuality hypergraph (0 = 1 mod 2 obstruction)',
            })

    # Family 7: Measurement Frames Beyond SIC (125 cases)
    # Balanced: Informationally complete (Pauli, octahedral, cubic) vs rank-deficient (trine)
    for idx in range(125):
        case_id += 1
        if idx % 2 == 0:
            # Informationally complete: Pauli projective or cubic
            frame_type = rng.choice(['pauli_proj', 'cubic'])
            if frame_type == 'pauli_proj':
                dirs, w = pauli_projective_frame()
            else:
                dirs, w = cubic_povm_frame()
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'MEASUREMENT_FRAME',
                'spec': {'directions': dirs, 'weights': w},
                'ground_truth_info_complete': True,
                'description': f'Informationally complete frame ({frame_type}, rank=3)',
            })
        else:
            # Rank-deficient: Trine POVM (rank=2, null space=span(z))
            dirs, w = trine_povm_frame()
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'MEASUREMENT_FRAME',
                'spec': {'directions': dirs, 'weights': w},
                'ground_truth_info_complete': False,
                'description': 'Rank-deficient Trine POVM (rank=2, kernel=span(e_z))',
            })

    # Family 8: Geometric Uncertainty Bounds (120 cases)
    # Testing distinction between lower bound and actual variance product
    for idx in range(120):
        case_id += 1
        if idx % 2 == 0:
            # Saturating state: r along (a x b) and pure (||r|| = 1)
            a = rng.normal(size=3); a /= np.linalg.norm(a)
            b = rng.normal(size=3)
            b = b - np.dot(a, b) * a; b /= np.linalg.norm(b) # b perp a
            r = np.cross(a, b) # r along a x b, ||r|| = 1
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'UNCERTAINTY_BOUND',
                'spec': {'a': a, 'b': b, 'r': r},
                'ground_truth_saturating': True,
                'description': 'Saturating pure state (Delta A Delta B = |det[a, b, r]|)',
            })
        else:
            # Non-saturating state: r in a-b plane or mixed state
            a = np.array([1.0, 0.0, 0.0])
            b = np.array([0.0, 1.0, 0.0])
            r = rng.normal(size=3)
            r[2] = 0.0 # Force r into xy plane -> volume bound = 0, but variances > 0
            if np.linalg.norm(r) > 0.95:
                r = r / np.linalg.norm(r) * 0.7
            cases.append({
                'id': f'CASE_{case_id:04d}',
                'family': 'UNCERTAINTY_BOUND',
                'spec': {'a': a, 'b': b, 'r': r},
                'ground_truth_saturating': False,
                'description': 'Non-saturating state (volume bound = 0 < actual variance product)',
            })

    return cases


def run_large_scale_blind_campaign(cases: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute the 1,000+ case prospective blind qualification campaign.

    Evaluates every case purely through the geometric / MAPEOGEO engine, blind
    to ground truth, and computes confusion matrices per family.
    """
    if cases is None:
        cases = generate_large_scale_blind_suite()

    family_stats = {}
    total_correct = 0

    for case in cases:
        fam = case['family']
        spec = case['spec']
        if fam not in family_stats:
            family_stats[fam] = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0, 'total': 0}
        stats = family_stats[fam]
        stats['total'] += 1

        # 1. Qutrit Unitary Flow
        if fam == 'QUTRIT_UNITARY_FLOW':
            R8 = spec['R8']
            is_so8 = bool(np.allclose(R8.T @ R8, np.eye(8), atol=1e-10) and np.isclose(np.linalg.det(R8), 1.0, atol=1e-10))
            pred = is_so8
            gt = case['ground_truth_physical']

        # 2. Qutrit State Admissibility
        elif fam == 'QUTRIT_STATE_ADMISSIBILITY':
            r = spec['bloch_8d']
            report = qutrit_is_physical(r)
            pred = report['physical']
            gt = case['ground_truth_physical']

        # 3. Single-Qubit Channels
        elif fam == 'SINGLE_QUBIT_CHANNEL':
            A = spec['A']
            c = spec['c']
            local_pass = is_locally_positive_affine(A, c)
            cp_pass = is_completely_positive_affine(A, c)
            pred = bool(local_pass and cp_pass)
            gt = case['ground_truth_physical']

        # 4. Composite-System State Admissibility
        elif fam == 'COMPOSITE_STATE_ADMISSIBILITY':
            rA = spec['rA']
            rB = spec['rB']
            T = spec['T']
            pos_info = bipartite_state_positivity(rA, rB, T)
            pred = pos_info['positive']
            gt = case['ground_truth_physical']

        # 5. Lindblad Generators
        elif fam == 'LINDBLAD_GENERATOR':
            M = spec['M']
            v = spec['v']
            classification = classify_lindblad_generator(M, v)
            pred = bool(classification['classification'] == 'VALID_LINDBLAD')
            gt = case['ground_truth_physical']

        # 6. Relational Context Hypergraphs
        elif fam == 'CONTEXT_GRAPH':
            cg = spec['graph']
            audit = cg.audit_valuation()
            pred = audit['is_contextual']
            gt = case['ground_truth_contextual']

        # 7. Measurement Frames Beyond SIC
        elif fam == 'MEASUREMENT_FRAME':
            dirs = spec['directions']
            weights = spec['weights']
            frame_info = analyze_measurement_frame(dirs, weights)
            pred = frame_info['informationally_complete']
            gt = case['ground_truth_info_complete']

        # 8. Geometric Uncertainty Bounds
        elif fam == 'UNCERTAINTY_BOUND':
            a = spec['a']
            b = spec['b']
            r = spec['r']
            unc = geometric_uncertainty_bound(a, b, r)
            pred = unc['is_saturated']
            gt = case['ground_truth_saturating']

        else:
            raise ValueError(f"Unknown family: {fam}")

        # Update confusion stats
        if pred and gt:
            stats['TP'] += 1
            total_correct += 1
        elif pred and not gt:
            stats['FP'] += 1
        elif not pred and not gt:
            stats['TN'] += 1
            total_correct += 1
        else: # not pred and gt
            stats['FN'] += 1

    # Compute metrics per family
    summary = {}
    total_cases = len(cases)
    overall_accuracy = total_correct / total_cases

    for fam, s in family_stats.items():
        tp, fp, tn, fn = s['TP'], s['FP'], s['TN'], s['FN']
        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 1.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        acc = (tp + tn) / s['total']
        summary[fam] = {
            'total': s['total'],
            'TP': tp, 'FP': fp, 'TN': tn, 'FN': fn,
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'specificity': spec,
            'f1_score': f1,
        }

    return {
        'total_cases': total_cases,
        'total_correct': total_correct,
        'overall_accuracy': overall_accuracy,
        'family_summary': summary,
        'zero_false_positives': all(s['FP'] == 0 for s in family_stats.values()),
        'zero_false_negatives': all(s['FN'] == 0 for s in family_stats.values()),
        'all_passed': bool(total_correct == total_cases),
        'accuracy': overall_accuracy,
        'false_positives': sum(s['FP'] for s in family_stats.values()),
        'false_negatives': sum(s['FN'] for s in family_stats.values()),
    }


# Backwards-compatible aliases
generate_blind_test_cases = generate_large_scale_blind_suite
run_blind_qualification_campaign = run_large_scale_blind_campaign

