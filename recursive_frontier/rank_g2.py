"""Ranking Engine for Second-Generation Frontier Candidates U_{2026}^{(2)}.

Applies the specified second-generation scoring formula:
    S_2(u) = S(u) * P(\\Omega = 0) * C_{independent} * C_{ancestry}
where:
- S(u) is the base relational score,
- P(\\Omega = 0) is the probability of being unobstructed,
- C_{independent} rewards independent derivation paths,
- C_{ancestry} rewards independent newly proven parents (2.0 for convergent descendants).
"""

from typing import Dict, Any, List
from recursive_frontier.ancestry import AncestryCertificateBuilder
from recursive_frontier.obstruction import Generation2ObstructionEvaluator

class Generation2RankingEngine:
    """Computes S_2 scores and ranks second-generation frontier candidates."""

    def __init__(self):
        self.cert_builder = AncestryCertificateBuilder()
        self.obs_evaluator = Generation2ObstructionEvaluator()

    def rank_candidates(self) -> List[Dict[str, Any]]:
        certs = self.cert_builder.build_certificates()
        ranked = []

        for c in certs:
            cid = c["candidate_id"]
            obs_info = self.obs_evaluator.evaluate_candidate(cid)

            base_s = c["base_score_S"]
            p_omega = obs_info["p_unobstructed"]
            
            # C_independent = 1.0 + 0.1 * (num_paths - 1)
            num_paths = c["num_independent_paths"]
            c_indep = 1.0 + 0.1 * (num_paths - 1)

            # C_ancestry from certificate
            c_anc = c["ancestry_factor_C_ancestry"]

            # Composite S_2 score
            s2_score = round(base_s * p_omega * c_indep * c_anc, 4)

            record = {
                "candidate_id": cid,
                "nominal_title": c["nominal_title"],
                "domain": c["domain"],
                "unlocking_result": c["unlocking_result"],
                "base_score_S": base_s,
                "p_unobstructed": p_omega,
                "c_independent": round(c_indep, 2),
                "c_ancestry": round(c_anc, 2),
                "s2_composite_score": s2_score,
                "is_unobstructed": obs_info["is_unobstructed"],
                "obstruction_class": obs_info["obstruction_class"],
                "minimal_repair": obs_info["minimal_repair"],
                "operator_word": c["operator_word"],
                "certificate": c
            }
            ranked.append(record)

        # Sort descending by s2_composite_score
        ranked.sort(key=lambda x: x["s2_composite_score"], reverse=True)

        for rank_idx, item in enumerate(ranked, start=1):
            item["rank"] = rank_idx

        return ranked

    def get_champion_target(self) -> Dict[str, Any]:
        ranked = self.rank_candidates()
        assert len(ranked) > 0
        champion = ranked[0]
        champion["is_champion_u2_star"] = True
        return champion

if __name__ == "__main__":
    engine = Generation2RankingEngine()
    ranked = engine.rank_candidates()
    print("=== Second-Generation Frontier Ranking (U_{2026}^{(2)}) ===")
    for r in ranked:
        print(f"Rank {r['rank']}: [{r['candidate_id']}] S_2 = {r['s2_composite_score']} | {r['nominal_title']} ({r['unlocking_result']})")
    champ = engine.get_champion_target()
    print(f"\nChampion Target U_{{2026}}^{{(2)*}}: {champ['candidate_id']} - {champ['nominal_title']}")
