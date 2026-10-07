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


_original_extract_record = _v2.extract_record


def _holdout_reveal_aware_extract_record(repo, path: str, theorem_name: str):
    # Training and auxiliary holdouts always read their declared challenge path.
    # Only the held-out #312 solution module needs an after-reveal fallback because
    # its configured Main.lean re-exports the declaration from ElementaryExpansion.lean.
    found = _original_extract_record(repo, path, theorem_name)
    if found is not None:
        return found
    if path == "lean/OAI/CategoryTheory/Globular/Main.lean":
        return _original_extract_record(
            repo,
            "lean/OAI/CategoryTheory/Globular/ElementaryExpansion.lean",
            theorem_name,
        )
    return None


# OpenAI/math graph node IDs are revision-qualified (oam:<rev>:file:<path>).
# Keep all compatibility handling inside the experiment package; production
# graph/code is not modified.
_v2.resource_path = _revision_qualified_resource_path
_v2.extract_record = _holdout_reveal_aware_extract_record
main = _v2.main

if __name__ == "__main__":
    raise SystemExit(main())
