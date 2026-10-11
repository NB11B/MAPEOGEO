import sys
from pathlib import Path

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sovctx.node.temporal_relations import TemporalRelationsEngine


def main() -> None:
    engine = TemporalRelationsEngine()
    output_dir = Path("sovctx/audits/r1")
    dossier = engine.export_temporal_dossier(output_dir)
    print("Exported temporal dossier successfully!")
    for s in dossier["historical_slices"]:
        print(f"== {s['slice_name']} ==")
        print(f"   Entities: {s['active_entity_count']}, Edges: {s['active_edge_count']}")
        print(f"   Top verbs: {s['dominant_verbs'][:4]}")
        print(f"   Top bigrams: {s['dominant_bigrams'][:3]}")


if __name__ == "__main__":
    main()
