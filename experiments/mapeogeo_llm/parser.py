"""Strict canonical JSON action parser. No executable text is accepted."""
from __future__ import annotations
import json
from typing import Any
from .contracts import Action, ContractError

MAX_ACTION_BYTES = 65536


def _no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out: raise ContractError(f"duplicate JSON key {key!r}")
        out[key] = value
    return out


def _decode(payload: str | Any):
    if not isinstance(payload, str): return payload
    if len(payload.encode("utf-8")) > MAX_ACTION_BYTES: raise ContractError("action payload too large")
    try:
        return json.loads(payload, object_pairs_hook=_no_duplicates,
                          parse_constant=lambda value: (_ for _ in ()).throw(ContractError(f"invalid number {value}")))
    except ContractError: raise
    except (json.JSONDecodeError, UnicodeError) as exc: raise ContractError("invalid action JSON") from exc


def parse_action(payload: str | dict) -> Action:
    data = _decode(payload)
    if not isinstance(data, dict): raise ContractError("one action object required")
    return Action.from_dict(data)


def parse_actions(payload: str | list | dict) -> tuple[Action, ...]:
    data = _decode(payload)
    if isinstance(data, dict): return (Action.from_dict(data),)
    if not isinstance(data, list): raise ContractError("action object or list required")
    return tuple(Action.from_dict(item) for item in data)
