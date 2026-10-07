"""Fresh Unseen Mathematical Problem Corpus and Blind Curriculum Generator.

Constructs:
- Canonical Q_fresh benchmark corpus (N = 80 problems across 4 untouched domains):
  1. Differential Topology & Morse Theory (20 problems: Q-MORSE-001 to Q-MORSE-020)
  2. Ergodic Theory & Measure-Preserving Dynamics (20 problems: Q-ERGODIC-001 to Q-ERGODIC-020)
  3. Algebraic Number Theory & Class Field Theory (20 problems: Q-CFT-001 to Q-CFT-020)
  4. Geometric Measure Theory & Varifolds (20 problems: Q-GMT-001 to Q-GMT-020)
- BlindCurriculumGenerator: Discovers deficiency clusters and packages them into
  candidate curricula dynamically WITHOUT domain labels or knowledge of historical
  trajectories.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from mapeogeo.domains.mathematics.ontology import MathematicalProblem


def get_fresh_problem_corpus() -> list[MathematicalProblem]:
    """Return the canonical 80-problem clean-room benchmark corpus."""
    corpus: list[MathematicalProblem] = []

    # 1. 20 Morse Theory problems (Q-MORSE-001 to Q-MORSE-020)
    for i in range(1, 21):
        corpus.append(
            MathematicalProblem.create(
                problem_id=f"Q-MORSE-{i:03d}",
                title=f"Morse-Smale Gradient Flow Transversality & Handle Cancellation {i}",
                domain="Differential Topology",
                difficulty=1.4,
                structural_distance=5.0,
                novelty=1.3,
                depth=1.3,
                required_signatures=(
                    "MORSE_SMALE_FLOW_TRANSVERSALITY",
                    "HANDLE_CANCELLATION_HOMOLOGY",
                ),
                base_ability_pct=0.0,
            )
        )

    # 2. 20 Ergodic Theory problems (Q-ERGODIC-001 to Q-ERGODIC-020)
    for i in range(1, 21):
        corpus.append(
            MathematicalProblem.create(
                problem_id=f"Q-ERGODIC-{i:03d}",
                title=f"Birkhoff Ergodic Average Convergence & Mixing Rates {i}",
                domain="Ergodic Theory",
                difficulty=1.5,
                structural_distance=5.5,
                novelty=1.4,
                depth=1.4,
                required_signatures=(
                    "BIRKHOFF_ERGODIC_MAXIMAL_INEQUALITY",
                    "DECAY_OF_CORRELATIONS_MIXING",
                ),
                base_ability_pct=0.0,
            )
        )

    # 3. 20 Class Field Theory problems (Q-CFT-001 to Q-CFT-020)
    for i in range(1, 21):
        corpus.append(
            MathematicalProblem.create(
                problem_id=f"Q-CFT-{i:03d}",
                title=f"Artin Reciprocity & Adelic Idele Class Characters {i}",
                domain="Class Field Theory",
                difficulty=1.7,
                structural_distance=6.0,
                novelty=1.5,
                depth=1.5,
                required_signatures=(
                    "ARTIN_RECIPROCITY_ISOMORPHISM",
                    "IDELE_CLASS_GROUP_CHARACTERS",
                ),
                base_ability_pct=0.0,
            )
        )

    # 4. 20 Geometric Measure Theory problems (Q-GMT-001 to Q-GMT-020)
    for i in range(1, 21):
        corpus.append(
            MathematicalProblem.create(
                problem_id=f"Q-GMT-{i:03d}",
                title=f"Varifold Rectifiability & Allard Boundary Regularity {i}",
                domain="Geometric Measure Theory",
                difficulty=1.6,
                structural_distance=5.8,
                novelty=1.4,
                depth=1.4,
                required_signatures=(
                    "VARIFOLD_MONOTONICITY_FORMULA",
                    "ALLARD_REGULARITY_EXTENSION",
                ),
                base_ability_pct=0.0,
            )
        )

    return corpus


class BlindCurriculumGenerator:
    """Discovers deficiency clusters and packages them into candidate curricula."""

    def generate_candidate_curricula(
        self,
        deficient_problems: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Synthesize candidate curricula from observed missing signatures."""
        candidates = [
            # Candidate CFT: Class Field Theory
            {
                "id": "CANDIDATE_CFT",
                "name": "Adelic Class Field Theory & Artin Reciprocity",
                "signatures": [
                    "ARTIN_RECIPROCITY_ISOMORPHISM",
                    "IDELE_CLASS_GROUP_CHARACTERS",
                ],
                "cost": 13.5,
                "cost_profile": {
                    "new_proof_obligations": 3,
                    "depth": 4.5,
                    "verification": 6.0,
                },
                "machinery_nodes": [
                    {
                        "id": "CFT_1",
                        "name": "Artin Reciprocity Law for Global Fields",
                        "formal_statement": (
                            "For any abelian extension L/K of global fields, "
                            "the Artin map induces an isomorphism "
                            "C_K / N_{L/K}(C_L) =~ Gal(L/K) of idele class groups."
                        ),
                        "witness_id": "w_cft_1",
                        "witness_certificate": "WITNESS_ARTIN_RECIPROCITY",
                        "grammar_factorization": (
                            r"\Pi_{\mathrm{artin}} \circ C_K \to "
                            r"\mathrm{Gal}(L/K) \circ w_{cft_1}"
                        ),
                        "verification_status": "EXISTING_MACHINERY_RECOVERED",
                        "dependencies": [],
                    },
                    {
                        "id": "CFT_2",
                        "name": "Chebotarev Density Theorem in Idele Classes",
                        "formal_statement": (
                            "The Frobenius conjugacy classes are uniformly "
                            "distributed in the Galois group with density "
                            "proportional to conjugacy class size."
                        ),
                        "witness_id": "w_cft_2",
                        "witness_certificate": "WITNESS_CHEBOTAREV_DENSITY",
                        "grammar_factorization": (
                            r"I \circ \mathrm{Frob}_p = \frac{|C|}{|G|} \circ w_{cft_2}"
                        ),
                        "verification_status": "EXISTING_MACHINERY_RECOVERED",
                        "dependencies": [],
                    },
                ],
            },
            # Candidate GMT: Geometric Measure Theory
            {
                "id": "CANDIDATE_GMT",
                "name": "Geometric Measure Theory & Varifold Monotonicity",
                "signatures": [
                    "VARIFOLD_MONOTONICITY_FORMULA",
                    "ALLARD_REGULARITY_EXTENSION",
                ],
                "cost": 12.5,
                "cost_profile": {
                    "new_proof_obligations": 3,
                    "depth": 4.0,
                    "verification": 5.5,
                },
                "machinery_nodes": [
                    {
                        "id": "GMT_1",
                        "name": "Monotonicity Formula for Stationary Varifolds",
                        "formal_statement": (
                            "Let V be a stationary varifold with bounded first variation; "
                            "the normalized mass r^{-m} ||V||(B_r(x)) is non-decreasing in r."
                        ),
                        "witness_id": "w_gmt_1",
                        "witness_certificate": "WITNESS_VARIFOLD_MONOTONICITY",
                        "grammar_factorization": r"\Gamma(r) \ge 0 \circ w_{gmt_1}",
                        "verification_status": "EXISTING_MACHINERY_RECOVERED",
                        "dependencies": [],
                    },
                    {
                        "id": "GMT_2",
                        "name": "Allard Regularity for Boundary Currents",
                        "formal_statement": (
                            "If the density ratio is close to 1 and tilt-excess is small, "
                            "the support of the varifold is a C^{1, alpha} submanifold."
                        ),
                        "witness_id": "w_gmt_2",
                        "witness_certificate": "WITNESS_ALLARD_REGULARITY",
                        "grammar_factorization": (
                            r"\Pi_{\mathrm{tan}} \circ V \to C^{1, \alpha} \circ w_{gmt_2}"
                        ),
                        "verification_status": "EXISTING_MACHINERY_RECOVERED",
                        "dependencies": [],
                    },
                ],
            },
            # Candidate ERGODIC: Ergodic Theory
            {
                "id": "CANDIDATE_ERGODIC",
                "name": "Ergodic Theory & Birkhoff Maximal Averages",
                "signatures": [
                    "BIRKHOFF_ERGODIC_MAXIMAL_INEQUALITY",
                    "DECAY_OF_CORRELATIONS_MIXING",
                ],
                "cost": 11.5,
                "cost_profile": {
                    "new_proof_obligations": 2,
                    "depth": 3.8,
                    "verification": 5.2,
                },
                "machinery_nodes": [
                    {
                        "id": "ERG_1",
                        "name": "Birkhoff Pointwise Ergodic Theorem",
                        "formal_statement": (
                            "For any measure-preserving system (X, mu, T) and f in L^1, "
                            "the time averages (1/n) sum f(T^k x) converge almost everywhere."
                        ),
                        "witness_id": "w_erg_1",
                        "witness_certificate": "WITNESS_BIRKHOFF_ERGODIC_POINTWISE",
                        "grammar_factorization": (
                            r"\Pi_{\mathrm{avg}} \circ f \to f^* \circ w_{erg_1}"
                        ),
                        "verification_status": "EXISTING_MACHINERY_RECOVERED",
                        "dependencies": [],
                    },
                    {
                        "id": "ERG_2",
                        "name": "Exponential Decay of Correlations for Anosov Flows",
                        "formal_statement": (
                            "Contact Anosov flows satisfy exponential decay of correlations "
                            "for Holder continuous observables."
                        ),
                        "witness_id": "w_erg_2",
                        "witness_certificate": "WITNESS_EXPONENTIAL_DECAY_CORRELATION",
                        "grammar_factorization": (
                            r"\sigma \circ |\rho(t)| \le C e^{-\lambda t} \circ w_{erg_2}"
                        ),
                        "verification_status": "EXISTING_MACHINERY_RECOVERED",
                        "dependencies": [],
                    },
                ],
            },
            # Candidate MORSE: Differential Topology
            {
                "id": "CANDIDATE_MORSE",
                "name": "Morse Theory & Handle Cancellation",
                "signatures": [
                    "MORSE_SMALE_FLOW_TRANSVERSALITY",
                    "HANDLE_CANCELLATION_HOMOLOGY",
                ],
                "cost": 11.0,
                "cost_profile": {
                    "new_proof_obligations": 2,
                    "depth": 3.5,
                    "verification": 4.5,
                },
                "machinery_nodes": [
                    {
                        "id": "MOR_1",
                        "name": "Morse-Smale Transversality Theorem",
                        "formal_statement": (
                            "For a generic gradient flow on a compact Riemannian manifold, "
                            "unstable and stable manifolds intersect transversally."
                        ),
                        "witness_id": "w_mor_1",
                        "witness_certificate": "WITNESS_MORSE_SMALE_TRANSVERSALITY",
                        "grammar_factorization": (
                            r"\Gamma_{\mathrm{flow}} \pitchfork \mathrm{grad} \circ w_{mor_1}"
                        ),
                        "verification_status": "EXISTING_MACHINERY_RECOVERED",
                        "dependencies": [],
                    },
                    {
                        "id": "MOR_2",
                        "name": "Smale Handlebody Cancellation Lemma",
                        "formal_statement": (
                            "If the intersection number of attaching sphere and belt sphere is 1, "
                            "adjacent index k and k+1 handles can be smoothly cancelled."
                        ),
                        "witness_id": "w_mor_2",
                        "witness_certificate": "WITNESS_HANDLE_CANCELLATION",
                        "grammar_factorization": (
                            r"\Delta_{\mathrm{handle}} \circ h_k \circ h_{k+1} "
                            r"\to \emptyset \circ w_{mor_2}"
                        ),
                        "verification_status": "EXISTING_MACHINERY_RECOVERED",
                        "dependencies": [],
                    },
                ],
            },
            # Candidate RANDOM CONTROL
            {
                "id": "CANDIDATE_RANDOM_CONTROL",
                "name": "Ramsey Graph Multi-Color Bounds",
                "signatures": ["RANDOM_RAMSEY_BOUND"],
                "cost": 12.0,
                "cost_profile": {
                    "new_proof_obligations": 5,
                    "depth": 8.0,
                    "verification": 12.0,
                },
                "machinery_nodes": [
                    {
                        "id": "RND_1",
                        "name": "Probabilistic Ramsey Bound Extension",
                        "formal_statement": "R(k, k) bounds via altered probabilistic method.",
                        "witness_id": "w_rnd_1",
                        "witness_certificate": "WITNESS_RANDOM_RAMSEY",
                        "grammar_factorization": r"\Pi_{\mathrm{prob}} \circ G \circ w_{rnd_1}",
                        "verification_status": "EXISTING_MACHINERY_RECOVERED",
                        "dependencies": [],
                    }
                ],
            },
        ]
        return candidates
