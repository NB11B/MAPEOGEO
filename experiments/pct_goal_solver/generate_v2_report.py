"""Refuse current-runtime regeneration of the immutable historical V2 report."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import NoReturn

from .v2_campaign import run_v2_campaign


def generate(out_dir: Path) -> NoReturn:
    """Fail before creating ``out_dir`` because V2 cannot be rescored here."""
    del out_dir
    run_v2_campaign()


def main() -> NoReturn:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("generated-goal-solver-v2"))
    args = parser.parse_args()
    generate(args.out_dir)


if __name__ == "__main__":
    main()
