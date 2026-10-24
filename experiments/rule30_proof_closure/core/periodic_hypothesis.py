"""Representation and classification of periodic-center hypotheses H(T, P, w)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import itertools
from typing import List, Sequence, Tuple


class WordClass(str, Enum):
    """Algebraic classification of candidate center period words."""

    ALL_WHITE = "ALL_WHITE"
    ALL_BLACK = "ALL_BLACK"
    AUTONOMOUS_NO_11 = "AUTONOMOUS_NO_11"
    LONG_BLACK_SHIELD = "LONG_BLACK_SHIELD"
    GENERAL_MIXED = "GENERAL_MIXED"


@dataclass(frozen=True)
class PeriodicCenterHypothesis:
    """Represents H(T, P, w): center(T + s) = w[s mod P] for all s >= 0."""

    transient_t: int
    period_p: int
    word: Tuple[int, ...]
    word_class: WordClass

    @property
    def word_str(self) -> str:
        return "".join(str(b) for b in self.word)

    @property
    def black_count(self) -> int:
        return sum(self.word)

    @property
    def white_count(self) -> int:
        return self.period_p - sum(self.word)

    @property
    def discrepancy_weight(self) -> int:
        return sum(1 if b == 1 else -1 for b in self.word)

    def center_at_offset(self, s: int) -> int:
        return self.word[s % self.period_p]


def classify_period_word(word: Sequence[int]) -> WordClass:
    """Classify a candidate period word w into its structural obstruction regime."""
    w = tuple(int(b) for b in word)
    p = len(w)
    if all(b == 0 for b in w):
        return WordClass.ALL_WHITE
    if all(b == 1 for b in w):
        return WordClass.ALL_BLACK
    has_11 = any(w[i] == 1 and w[(i + 1) % p] == 1 for i in range(p))
    if not has_11:
        return WordClass.AUTONOMOUS_NO_11
    # Check if cyclic word has 9 consecutive 1s
    doubled = w + w
    cur_run = 0
    max_run = 0
    for b in doubled:
        if b == 1:
            cur_run += 1
            max_run = max(max_run, cur_run)
        else:
            cur_run = 0
    if max_run >= 9:
        return WordClass.LONG_BLACK_SHIELD
    return WordClass.GENERAL_MIXED


def enumerate_periodic_hypotheses(
    max_period: int,
    transients: Sequence[int],
    include_constant_words: bool = True,
) -> List[PeriodicCenterHypothesis]:
    """Enumerate periodic-center hypotheses H(T, P, w) across periods 1..max_period and transients."""
    out: List[PeriodicCenterHypothesis] = []
    for t in transients:
        for p in range(1, max_period + 1):
            for w in itertools.product((0, 1), repeat=p):
                w_class = classify_period_word(w)
                if not include_constant_words and w_class in (
                    WordClass.ALL_WHITE,
                    WordClass.ALL_BLACK,
                ):
                    continue
                out.append(
                    PeriodicCenterHypothesis(
                        transient_t=t,
                        period_p=p,
                        word=tuple(w),
                        word_class=w_class,
                    )
                )
    return out
