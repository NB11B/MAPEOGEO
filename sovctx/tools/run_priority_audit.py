import sys
from pathlib import Path

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sovctx.node.priority_matrix import PriorityMatrixEngine


def main() -> None:
    engine = PriorityMatrixEngine()
    output_dir = Path("sovctx/audits/r1")
    dossier = engine.export_priority_matrix(output_dir)
    print("Exported Priority Matrix successfully!")
    print("== Top 5 Pillars in Priority Matrix ==")
    for p in dossier["top_ranking_pillars"]:
        print(f"   Rank {p['rank']}: {p['label']} ({p['item_id']}) -> Composite Index = {p['composite_index']}")
        print(f"      Schools: {p['schools']}, Span: {p['span_years']} yrs, Transfers: {p['engineering_transfers']}")


if __name__ == "__main__":
    main()
