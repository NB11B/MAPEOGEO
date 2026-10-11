import sys
from pathlib import Path

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sovctx.node.leibniz_lineage import LeibnizLineageEngine


def main() -> None:
    engine = LeibnizLineageEngine()
    output_dir = Path("sovctx/audits/r1")
    dossier = engine.export_leibniz_dossier(output_dir)
    print("Exported Leibniz lineage dossier successfully!")
    print("== Transmission Chain ==")
    for gn in dossier["genealogical_transmission_chain"]:
        print(f"   G{gn['generation_from_leibniz']}: {gn['person_name']} -> dominant verbs: {gn['dominant_relational_verbs']}")
    print("== Hypotheses ==")
    for h in dossier["hypothesis_evaluations"]:
        print(f"   {h['hypothesis_id']}: score={h['support_score']}, verdict={h['verdict']}")
    print("== Oral Provenance Isolation ==")
    print(f"   Verdict: {dossier['oral_provenance_isolation']['epistemic_verdict']}")


if __name__ == "__main__":
    main()
