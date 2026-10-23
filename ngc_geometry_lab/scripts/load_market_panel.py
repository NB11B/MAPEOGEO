"""Deterministic market-observation panel loader; run from ngc_geometry_lab root.

Usage: python scripts/load_market_panel.py --manifest data_sources.json --out observations.json
This emits observations, not trained or physically interpreted states.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from ngc_geometry_lab.io import write_json
from ngc_geometry_lab.market_observation import (
    load_ohlcv_csv, sample_multiscale_states, observation_carrier,
)

FIELDS = {"path", "symbol", "kind", "bar_seconds", "timestamp_label", "volume_kind", "source"}


def run(manifest_path: str | Path, out_path: str | Path) -> dict:
    path, out = Path(manifest_path).resolve(), Path(out_path).resolve()
    if out.exists():
        raise ValueError("output already exists; refuse to overwrite past evidence")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"schema", "lags", "instruments"}:
        raise ValueError("unexpected or missing manifest keys")
    if payload["schema"] != "ngc.market_panel_manifest.v0":
        raise ValueError("unsupported manifest schema")
    instruments = payload["instruments"]
    if not isinstance(instruments, list) or not instruments:
        raise ValueError("instruments must be a nonempty list")
    lags = payload["lags"]
    if not isinstance(lags, list) or not lags:
        raise ValueError("lags must be a nonempty list")
    records, symbols = [], set()
    for item in instruments:
        if not isinstance(item, dict) or set(item) != FIELDS:
            raise ValueError("unexpected or missing instrument keys")
        if not isinstance(item["path"], str):
            raise ValueError("instrument path must be a string")
        if item["symbol"] in symbols:
            raise ValueError("duplicate symbol in panel")
        symbols.add(item["symbol"])
        source_path = Path(item["path"])
        if not source_path.is_absolute():
            source_path = path.parent / source_path
        kwargs = {k: item[k] for k in FIELDS if k != "path"}
        series = load_ohlcv_csv(source_path, **kwargs)
        states = sample_multiscale_states(series, lags=lags)
        records.append(observation_carrier(series, states))
    result = {
        "schema": "ngc.market_panel_observations.v0",
        "epistemic_status": "DETERMINISTIC_OBSERVATION_ONLY",
        "instruments": records,
    }
    write_json(out, result)
    return result


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    result = run(args.manifest, args.out)
    print(f"Loaded {len(result['instruments'])} instruments as observational carriers")


if __name__ == "__main__":
    main()
