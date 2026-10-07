from __future__ import annotations

# Full held-out #312 campaign entrypoint.
# The v2 implementation is the domain-neutral bottom-up grammar experiment:
# it excludes #312 and auxiliary holdouts before grammar discovery, freezes the
# learned grammar before reveal, runs collision/adversarial controls, and then
# evaluates the held-out result without modifying the production graph.
from .full_campaign_v2 import main

if __name__ == "__main__":
    raise SystemExit(main())
