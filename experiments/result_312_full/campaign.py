from __future__ import annotations

# Full held-out #312 campaign entrypoint.
# The v2 implementation is the domain-neutral bottom-up grammar experiment:
# it excludes #312 and auxiliary holdouts before grammar discovery, freezes the
# learned grammar before reveal, runs collision/adversarial controls, and then
# evaluates the held-out result without modifying the production graph.
from . import full_campaign_v2 as _v2


def _revision_qualified_resource_path(node_id: str) -> str | None:
    raw = str(node_id)
    marker = ":file:"
    if not raw.startswith("oam:") or marker not in raw:
        return None
    path = raw.split(marker, 1)[1]
    return path.split(":record:", 1)[0].split(":reference:", 1)[0]


# OpenAI/math graph node IDs are revision-qualified (oam:<rev>:file:<path>).
# Keep the experiment package isolated; production graph/code is unchanged.
_v2.resource_path = _revision_qualified_resource_path
main = _v2.main

if __name__ == "__main__":
    raise SystemExit(main())
