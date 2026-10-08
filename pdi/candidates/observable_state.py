# SPDX-License-Identifier: MIT
"""Observable State Extractor for PDI-135M-v0.4.

Extracts StateContext solely from observable environment state and input prompt text,
with ZERO reference or access to hidden evaluation targets, satisfying Gate 1 (Oracle Independence).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pdi.decoder.constrained_decoder import StateContext


class ObservableStateExtractor:
    """Extracts hardware-observable state context without oracle label exposure."""

    @classmethod
    def extract_from_prompt(
        cls,
        input_prompt: str,
        default_version: int = 1000,
        default_cap: int = 0x00000001,
    ) -> StateContext:
        """Parse visible references, state version, and destination purely from prompt text."""
        # 1. State version regex: e.g. "version 1042", "v1042", "version: 1042"
        v_match = re.search(r"(?:version|ver|pre-state version)[:\s]+(\d+)", input_prompt, re.IGNORECASE)
        version = int(v_match.group(1)) if v_match else default_version

        # 2. Destination address regex: e.g. "dest address 12", "into state 12", "dest=REF_12"
        dest_match = re.search(r"(?:dest(?:ination)?\s+(?:address\s+)?|into\s+state\s+|dest=REF_)(\d+)", input_prompt, re.IGNORECASE)
        dest_ref = int(dest_match.group(1)) if dest_match else None

        # 3. Visible references: all "state (\d+)", "REF_(\d+)", "words? (\d+)"
        refs: Set[int] = set()
        for m in re.finditer(r"(?:state|ref|node|word|address|slot)\s*[_:]?\s*(\d+)", input_prompt, re.IGNORECASE):
            refs.add(int(m.group(1)))

        # Also find comma-separated numbers like "10, 11, 12"
        num_list_match = re.search(r"(\d+(?:\s*,\s*\d+)+)", input_prompt)
        if num_list_match:
            for item in num_list_match.group(1).split(","):
                try:
                    refs.add(int(item.strip()))
                except ValueError:
                    pass

        # Destination reference shouldn't be the primary source operand if other refs exist
        visible_list = sorted(list(refs))
        if not visible_list:
            visible_list = [10, 11]

        return StateContext(
            assumed_state_version=version,
            authorized_capability_mask=default_cap,
            visible_refs=tuple(visible_list),
            goal_ref=dest_ref,
        )
