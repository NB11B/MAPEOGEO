"""Isolated statistical evaluation for candidate market-state transformations.

No part of this module runs during market observation ingestion. All metrics
refer to explicit candidate predictions and are NOT physical mechanism claims.
"""
from __future__ import annotations

import numpy as np


def evaluate_frozen_predictions(actual, proposed, baseline) -> dict:
    """Score *already frozen* predictions. This function never selects lags/models.

    Arrays must represent the exact same chronological held-out state vectors.
    """
    a, p, b = (np.asarray(x, dtype=float) for x in (actual, proposed, baseline))
    if a.ndim != 2 or not a.size or p.shape != a.shape or b.shape != a.shape:
        raise ValueError("actual/proposed/baseline must be identical nonempty 2D shapes")
    if not all(np.all(np.isfinite(x)) for x in (a, p, b)):
        raise ValueError("all evaluation values must be finite")
    mse_p = float(np.mean((a - p) ** 2))
    mse_b = float(np.mean((a - b) ** 2))
    return {
        "n_states": int(a.shape[0]), "state_dimension": int(a.shape[1]),
        "candidate_mse": mse_p, "baseline_mse": mse_b,
        "error_ratio": None if mse_b == 0 else mse_p / mse_b,
        "epistemic_status": "EMPIRICAL_HOLDOUT_SCORE_NOT_MECHANISM",
    }
