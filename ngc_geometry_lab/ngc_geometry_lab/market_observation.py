"""Market observation boundary for NGC geometry research.

Deterministic: parse, validate, keep provenance, encode an explicit sampled signal,
and calculate exact-sequence matrix diagnostics.  It does NOT infer a causal law,
a quantum state, or missing quotes.  Inference/evaluation is a separate layer.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import math
from pathlib import Path
from typing import Literal, Sequence

import numpy as np

UTC = timezone.utc
_KIND = frozenset({"stock", "etf", "mutual_fund", "index", "future", "other"})
_VOLUME = frozenset({"shares", "contracts", "tick_count", "unavailable"})


@dataclass(frozen=True)
class Bar:
    timestamp_utc: datetime  # start or end, according to the declared label
    available_at_utc: datetime  # never earlier than the closing observation
    open: float
    high: float
    low: float
    close: float
    volume: float | None


@dataclass(frozen=True)
class MarketSeries:
    symbol: str
    kind: str
    source: str
    source_sha256: str
    bar_seconds: int
    timestamp_label: Literal["open", "close"]
    volume_kind: str
    bars: tuple[Bar, ...]

    def provenance(self) -> dict:
        return {
            "symbol": self.symbol, "instrument_kind": self.kind,
            "source": self.source, "source_sha256": self.source_sha256,
            "bar_seconds": self.bar_seconds,
            "timestamp_label": self.timestamp_label,
            "volume_kind": self.volume_kind, "row_count": len(self.bars),
            "first_timestamp_utc": self.bars[0].timestamp_utc.isoformat(),
            "last_timestamp_utc": self.bars[-1].timestamp_utc.isoformat(),
            "representation_status": "OBSERVED_NOT_QUANTUM",
        }


@dataclass(frozen=True)
class SampledState:
    at_utc: datetime
    earth_phase_radians: float
    coordinates: tuple[float, ...]
    lag_seconds: tuple[int, ...]
    observation_kind: str = "LOG_CLOSE_RATIO_DELAY_EMBEDDING"


def _finite_number(raw: str, field: str, *, positive: bool = False) -> float:
    try:
        value = float(raw)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{field}: not a numeric observation") from exc
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{field}: invalid finite value")
    return value


def _parse_utc(text: str) -> datetime:
    try:
        ts = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        raise ValueError("timestamps must be ISO-8601 with explicit UTC offset") from exc
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise ValueError("naive timestamps are forbidden; require explicit UTC offset")
    return ts.astimezone(UTC)


def load_ohlcv_csv(
    path: str | Path, *, symbol: str, kind: str,
    bar_seconds: int, timestamp_label: Literal["open", "close"],
    volume_kind: str, source: str,
) -> MarketSeries:
    """Read source bytes, never assume a timezone, never fill closed-market gaps.

    UTC timestamps are bar label timestamps, *not* necessarily observation availability.
    Availability is the end of the bar, so future OHLC values never leak backward.
    """
    if not symbol.strip() or not source.strip():
        raise ValueError("symbol and source are required")
    if kind not in _KIND or volume_kind not in _VOLUME:
        raise ValueError("unsupported instrument kind or volume semantics")
    if isinstance(bar_seconds, bool) or not isinstance(bar_seconds, int) or bar_seconds <= 0:
        raise ValueError("bar_seconds must be a positive integer")
    if timestamp_label not in ("open", "close"):
        raise ValueError("timestamp_label must be open or close")
    raw = Path(path).read_bytes()
    try:
        payload = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8")
    reader = csv.DictReader(payload.splitlines())
    required = {"datetime", "open", "high", "low", "close", "volume"}
    if not reader.fieldnames or set(reader.fieldnames) != required:
        raise ValueError("CSV columns must be datetime,open,high,low,close,volume")
    bars: list[Bar] = []
    prev: datetime | None = None
    for line, row in enumerate(reader, 2):
        if None in row or any(v is None for v in row.values()):
            raise ValueError(f"line {line}: malformed CSV row")
        ts = _parse_utc(row["datetime"])
        if prev is not None and ts <= prev:
            raise ValueError(f"line {line}: timestamps must be unique and strictly increasing")
        if prev is not None and (ts - prev).total_seconds() < bar_seconds:
            raise ValueError(f"line {line}: bar windows overlap")
        o, h, lo, c = (_finite_number(row[k], k, positive=True)
                        for k in ("open", "high", "low", "close"))
        if h < max(o, lo, c) or lo > min(o, h, c):
            raise ValueError(f"line {line}: impossible OHLC ordering")
        volume = None if volume_kind == "unavailable" and not row["volume"].strip() else _finite_number(row["volume"], "volume")
        if volume is not None and volume < 0:
            raise ValueError(f"line {line}: negative volume")
        if volume_kind != "unavailable" and volume is None:
            raise ValueError(f"line {line}: volume missing despite declared semantics")
        available = ts if timestamp_label == "close" else ts + timedelta(seconds=bar_seconds)
        bars.append(Bar(ts, available, o, h, lo, c, volume))
        prev = ts
    if not bars:
        raise ValueError("CSV contains no bars")
    return MarketSeries(symbol, kind, source, sha256(raw).hexdigest(),
                        bar_seconds, timestamp_label, volume_kind, tuple(bars))


def earth_phase_utc(ts: datetime) -> float:
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise ValueError("Earth phase requires timezone-aware time")
    t = ts.astimezone(UTC)
    seconds = t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1_000_000
    return 2 * math.pi * seconds / 86400


def sample_multiscale_states(series: MarketSeries, *, lags: Sequence[int] = (1, 2, 4, 8)) -> tuple[SampledState, ...]:
    """Observed delay coordinates only; reject horizons crossing an unavailable bar.

    Lags are positive *bar counts*, not estimates of an oscillator frequency.
    Every returned coordinate is calculated from observed, contiguous closes.
    """
    if not lags or any(isinstance(k, bool) or not isinstance(k, int) or k <= 0 for k in lags):
        raise ValueError("lags must be positive integer bar counts")
    if len(set(lags)) != len(lags):
        raise ValueError("lags must be unique")
    result = []
    bs = series.bars
    for i in range(max(lags), len(bs)):
        if any((bs[i].available_at_utc - bs[i-k].available_at_utc).total_seconds()
               != k * series.bar_seconds for k in lags):
            continue
        coords = tuple(math.log(bs[i].close / bs[i-k].close) for k in lags)
        at = bs[i].available_at_utc
        result.append(SampledState(at, earth_phase_utc(at), coords,
                                   tuple(k * series.bar_seconds for k in lags)))
    return tuple(result)


def adjacent_pairs(states: Sequence[SampledState], *, interval_seconds: int) -> tuple[tuple[SampledState, SampledState], ...]:
    """Never join states across missing observations, weekends or exchange closure."""
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    return tuple((a, b) for a, b in zip(states, states[1:])
                 if (b.at_utc - a.at_utc).total_seconds() == interval_seconds)


def ordered_operator_diagnostics(A, B, start, observed_after_two) -> dict:
    """Evaluate B@A versus A@B without calling noncommutativity a mechanism."""
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)
    start = np.asarray(start, dtype=float)
    end = np.asarray(observed_after_two, dtype=float)
    d = start.size
    if start.ndim != 1 or end.shape != (d,) or A.shape != (d, d) or B.shape != (d, d):
        raise ValueError("operator/state dimensional mismatch")
    if not all(np.all(np.isfinite(x)) for x in (A, B, start, end)):
        raise ValueError("operator/state values must be finite")
    BA = B @ A
    AB = A @ B
    return {
        "commutator_frobenius": float(np.linalg.norm(BA - AB, ord="fro")),
        "observed_order_error": float(np.linalg.norm(BA @ start - end)),
        "reversed_order_error": float(np.linalg.norm(AB @ start - end)),
        "evidence_status": "ALGEBRAIC_DIAGNOSTIC_NOT_CAUSAL_PROOF",
    }


def observation_carrier(series: MarketSeries, states: Sequence[SampledState]) -> dict:
    """Type-neutral GEO-X observation input; no Bloch/quantum normalization.

    This is a transport schema, not a claim of direct compatibility with the
    existing GEO-X1/X2 physical-model-specific reconstruction entrypoints.
    """
    for x in states:
        if not isinstance(x, SampledState):
            raise ValueError("carrier expects SampledState records")
    return {
        "schema": "ngc.market_observation.v0",
        "provenance": series.provenance(),
        "coordinate_dimension": len(states[0].coordinates) if states else 0,
        "observations": [
            {"utc": x.at_utc.isoformat(), "earth_phase_radians": x.earth_phase_radians,
             "coordinates": list(x.coordinates), "lag_seconds": list(x.lag_seconds)}
            for x in states
        ],
        "epistemic_status": "DETERMINISTIC_OBSERVATION_ONLY",
    }
