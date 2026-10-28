"""Versioned immutable contracts for the bounded MAPEOGEO agent runtime."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping
import json
import math
import re

ACTION_SCHEMA = "mapeogeo.llm.action.v1"
STATUSES = frozenset({"VERIFIED", "REFUTED", "UNSOLVED", "INVALID_INPUT",
                      "EXECUTION_ERROR", "BUDGET_EXHAUSTED", "RUNNING"})
PROGRAM_OPS = frozenset({"ADD", "SUB", "XOR", "AND", "OR", "EQ", "GEO_GP", "GEO_GRADE"})
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_TOKEN = re.compile(r"\w+|[^\s\w]", re.UNICODE)


class ContractError(ValueError):
    """Input did not satisfy the canonical runtime contract."""


def _check_json(value: Any, path: str = "value") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractError(f"{path} must be finite")
        return
    if isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            _check_json(item, f"{path}[{i}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractError(f"{path} keys must be strings")
            _check_json(item, f"{path}.{key}")
        return
    raise ContractError(f"{path} is not canonical JSON data")


def _freeze(value: Any) -> Any:
    _check_json(value)
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    data = value.to_dict() if hasattr(value, "to_dict") else _thaw(value)
    _check_json(data)
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False)


def canonical_digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def lexical_token_count(value: Any) -> int:
    """Conservative tokenizer-independent bound for public serialized content."""
    text = value if isinstance(value, str) else canonical_json(value)
    return len(_TOKEN.findall(text))


def _require_digest(value: Any, name: str) -> None:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ContractError(f"{name} must be a lowercase SHA-256 digest")


def _exact_keys(data: Mapping[str, Any], allowed: set[str], required: set[str]) -> None:
    unknown = set(data) - allowed
    missing = required - set(data)
    if unknown or missing:
        raise ContractError(f"invalid fields: missing={sorted(missing)}, unknown={sorted(unknown)}")


@dataclass(frozen=True)
class TypedValue:
    kind: str
    value: Any

    def __post_init__(self):
        if not isinstance(self.kind, str) or not self.kind:
            raise ContractError("TypedValue.kind must be a non-empty string")
        allowed = {"uint8", "integer", "rational", "symbolic_expression",
                   "float_multivector", "boolean", "graph_node", "proposition",
                   "proof_certificate"}
        if self.kind not in allowed:
            raise ContractError(f"unsupported TypedValue kind {self.kind!r}")
        value = self.value
        if self.kind == "uint8" and (isinstance(value, bool) or not isinstance(value, int)
                                      or not 0 <= value <= 255):
            raise ContractError("uint8 value must be an integer in [0,255]")
        if self.kind == "integer" and (isinstance(value, bool) or not isinstance(value, int)):
            raise ContractError("integer value required")
        if self.kind == "boolean" and not isinstance(value, bool):
            raise ContractError("boolean value required")
        if self.kind == "float_multivector":
            if not isinstance(value, (list, tuple)) or any(
                    isinstance(item, bool) or not isinstance(item, (int, float))
                    or not math.isfinite(item) for item in value):
                raise ContractError("finite numeric multivector required")
        if self.kind in {"proposition"} and not isinstance(value, str):
            raise ContractError("proposition string required")
        if self.kind == "rational" and not (
                isinstance(value, str) or
                (isinstance(value, (list, tuple)) and len(value) == 2 and
                 all(isinstance(item, int) and not isinstance(item, bool) for item in value))):
            raise ContractError("rational must be a string or integer numerator/denominator pair")
        if self.kind in {"graph_node", "symbolic_expression", "proof_certificate"} and not \
                isinstance(value, (str, Mapping)):
            raise ContractError(f"invalid {self.kind} value")
        object.__setattr__(self, "value", _freeze(self.value))

    def to_dict(self): return {"kind": self.kind, "value": _thaw(self.value)}
    def canonical_digest(self): return canonical_digest(self)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping): raise ContractError("TypedValue must be an object")
        _exact_keys(data, {"kind", "value"}, {"kind", "value"})
        return cls(data["kind"], data["value"])


@dataclass(frozen=True)
class Ref:
    kind: str
    id: str | None = None
    value: Any | None = None

    def __post_init__(self):
        if self.kind not in {"input", "reg", "literal", "node"}:
            raise ContractError(f"unsupported reference kind {self.kind!r}")
        if self.kind == "literal":
            if self.id is not None: raise ContractError("literal reference cannot have id")
            object.__setattr__(self, "value", _freeze(self.value))
        else:
            if not isinstance(self.id, str) or not self.id: raise ContractError("reference id required")
            if self.value is not None: raise ContractError("non-literal reference cannot have value")

    def to_dict(self):
        out = {"kind": self.kind}
        if self.id is not None: out["id"] = self.id
        if self.kind == "literal": out["value"] = _thaw(self.value)
        return out

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping): raise ContractError("Ref must be an object")
        _exact_keys(data, {"kind", "id", "value"}, {"kind"})
        return cls(data["kind"], data.get("id"), data.get("value"))


@dataclass(frozen=True)
class Action:
    op: str
    src: tuple[Ref, ...] = ()
    dst: str | None = None
    kwargs: Mapping[str, Any] = field(default_factory=dict)
    reason_code: str | None = None
    schema: str = ACTION_SCHEMA

    def __post_init__(self):
        if self.schema != ACTION_SCHEMA: raise ContractError(f"unsupported action schema {self.schema!r}")
        if not isinstance(self.op, str) or not self.op: raise ContractError("Action.op must be a string")
        if not isinstance(self.src, tuple): object.__setattr__(self, "src", tuple(self.src))
        if not all(isinstance(r, Ref) for r in self.src): raise ContractError("Action.src must contain Ref values")
        if self.dst is not None and (not isinstance(self.dst, str) or not self.dst):
            raise ContractError("Action.dst must be a non-empty string")
        if self.reason_code is not None and not isinstance(self.reason_code, str):
            raise ContractError("reason_code must be a string")
        object.__setattr__(self, "kwargs", _freeze(self.kwargs))

    def to_dict(self):
        return {"schema": self.schema, "op": self.op, "src": [r.to_dict() for r in self.src],
                "dst": self.dst, "kwargs": _thaw(self.kwargs), "reason_code": self.reason_code}
    def canonical_digest(self): return canonical_digest(self)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping): raise ContractError("Action must be an object")
        _exact_keys(data, {"schema", "op", "src", "dst", "kwargs", "reason_code"},
                    {"schema", "op", "src", "dst"})
        if not isinstance(data["src"], list): raise ContractError("Action.src must be a list")
        if not isinstance(data.get("kwargs", {}), Mapping): raise ContractError("Action.kwargs must be an object")
        return cls(data["op"], tuple(Ref.from_dict(x) for x in data["src"]), data["dst"],
                   data.get("kwargs", {}), data.get("reason_code"), data["schema"])


@dataclass(frozen=True)
class Budget:
    max_steps: int = 32
    max_registers: int = 64
    max_graph_expansion: int = 32
    max_input_bytes: int = 65536
    max_token_count: int = 4096
    wall_time_seconds: float = 30.0

    def __post_init__(self):
        for name in ("max_steps", "max_registers", "max_graph_expansion", "max_input_bytes", "max_token_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ContractError(f"{name} must be a positive integer")
        if isinstance(self.wall_time_seconds, bool) or not isinstance(self.wall_time_seconds, (int, float)) \
                or not math.isfinite(self.wall_time_seconds) or self.wall_time_seconds <= 0:
            raise ContractError("wall_time_seconds must be positive and finite")

    def to_dict(self):
        return {name: getattr(self, name) for name in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping): raise ContractError("Budget must be an object")
        _exact_keys(data, set(cls.__dataclass_fields__), set())
        return cls(**data)


@dataclass(frozen=True)
class Task:
    problem: str
    inputs: Mapping[str, TypedValue]
    goal: Mapping[str, Any]
    budget: Budget = field(default_factory=Budget)

    def __post_init__(self):
        if not isinstance(self.problem, str): raise ContractError("Task.problem must be a string")
        if not isinstance(self.budget, Budget): raise ContractError("Task.budget must be Budget")
        if not isinstance(self.inputs, Mapping) or not all(isinstance(k, str) and isinstance(v, TypedValue)
                                                            for k, v in self.inputs.items()):
            raise ContractError("Task.inputs must map names to TypedValue")
        object.__setattr__(self, "inputs", MappingProxyType(dict(self.inputs)))
        if not isinstance(self.goal, Mapping): raise ContractError("Task.goal must be an object")
        if self.goal.get("kind") == "target":
            constrained = "allowed_ops" in self.goal or "max_ops" in self.goal
            if constrained:
                if "allowed_ops" not in self.goal or "max_ops" not in self.goal:
                    raise ContractError("target constraints require allowed_ops and max_ops together")
                allowed = self.goal["allowed_ops"]
                max_ops = self.goal["max_ops"]
                if not isinstance(allowed, (list, tuple)) or not allowed or \
                        not all(isinstance(op, str) and op in PROGRAM_OPS for op in allowed) or \
                        len(set(allowed)) != len(allowed):
                    raise ContractError("allowed_ops must be unique supported EO/GEO operator names")
                if isinstance(max_ops, bool) or not isinstance(max_ops, int) or max_ops <= 0 \
                        or max_ops > self.budget.max_steps:
                    raise ContractError("max_ops must be a positive integer within max_steps")
        object.__setattr__(self, "goal", _freeze(self.goal))
        if len(canonical_json(self.to_dict()).encode()) > self.budget.max_input_bytes:
            raise ContractError("task exceeds max_input_bytes")
        if lexical_token_count(self.to_dict()) > self.budget.max_token_count:
            raise ContractError("task exceeds max_token_count")

    def to_dict(self):
        return {"problem": self.problem, "inputs": {k: v.to_dict() for k, v in self.inputs.items()},
                "goal": _thaw(self.goal), "budget": self.budget.to_dict()}
    def canonical_digest(self): return canonical_digest(self)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping): raise ContractError("Task must be an object")
        _exact_keys(data, {"problem", "inputs", "goal", "budget"}, {"problem", "inputs", "goal"})
        if not isinstance(data["inputs"], Mapping): raise ContractError("Task.inputs must be an object")
        return cls(data["problem"], {k: TypedValue.from_dict(v) for k, v in data["inputs"].items()},
                   data["goal"], Budget.from_dict(data.get("budget", {})))


@dataclass(frozen=True)
class ProofObligation:
    proposition: str
    status: str = "OPEN"
    evidence: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.proposition, str) or not self.proposition:
            raise ContractError("ProofObligation.proposition must be a non-empty string")
        if self.status not in {"OPEN", "DISCHARGED", "REFUTED"}:
            raise ContractError("invalid proof obligation status")
        if not isinstance(self.evidence, Mapping): raise ContractError("obligation evidence must be an object")
        object.__setattr__(self, "evidence", _freeze(self.evidence))
    def to_dict(self): return {"proposition": self.proposition, "status": self.status, "evidence": _thaw(self.evidence)}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping): raise ContractError("ProofObligation must be an object")
        _exact_keys(data, {"proposition", "status", "evidence"}, {"proposition"})
        return cls(data["proposition"], data.get("status", "OPEN"), data.get("evidence", {}))


@dataclass(frozen=True)
class VerificationResult:
    status: str
    output: TypedValue | None
    state_digest: str
    evidence: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if self.status not in {"VERIFIED", "REFUTED", "UNSOLVED"}: raise ContractError("invalid verification status")
        if self.output is not None and not isinstance(self.output, TypedValue):
            raise ContractError("verification output must be TypedValue or null")
        _require_digest(self.state_digest, "VerificationResult.state_digest")
        if not isinstance(self.evidence, Mapping): raise ContractError("verification evidence must be an object")
        object.__setattr__(self, "evidence", _freeze(self.evidence))
    def to_dict(self):
        return {"status": self.status, "output": None if self.output is None else self.output.to_dict(),
                "state_digest": self.state_digest, "evidence": _thaw(self.evidence)}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping): raise ContractError("VerificationResult must be an object")
        _exact_keys(data, {"status", "output", "state_digest", "evidence"},
                    {"status", "output", "state_digest"})
        output = None if data["output"] is None else TypedValue.from_dict(data["output"])
        return cls(data["status"], output, data["state_digest"], data.get("evidence", {}))


@dataclass(frozen=True)
class Observation:
    success: bool
    status: str
    action: Action | None = None
    output: TypedValue | None = None
    error: Mapping[str, Any] | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)
    obligations: tuple[ProofObligation, ...] = ()
    verification: VerificationResult | None = None
    state_digest: str = ""

    def __post_init__(self):
        if not isinstance(self.success, bool): raise ContractError("Observation.success must be boolean")
        if self.status not in STATUSES: raise ContractError("invalid observation status")
        if self.action is not None and not isinstance(self.action, Action): raise ContractError("invalid observation action")
        if self.output is not None and not isinstance(self.output, TypedValue): raise ContractError("invalid observation output")
        if self.error is not None and not isinstance(self.error, Mapping): raise ContractError("observation error must be an object")
        if not isinstance(self.evidence, Mapping): raise ContractError("observation evidence must be an object")
        if not isinstance(self.obligations, (list, tuple)) or not all(
                isinstance(item, ProofObligation) for item in self.obligations):
            raise ContractError("obligations must contain ProofObligation values")
        if self.verification is not None and not isinstance(self.verification, VerificationResult):
            raise ContractError("invalid observation verification")
        if self.state_digest:
            _require_digest(self.state_digest, "Observation.state_digest")
        if self.error is not None: object.__setattr__(self, "error", _freeze(self.error))
        object.__setattr__(self, "evidence", _freeze(self.evidence))
        object.__setattr__(self, "obligations", tuple(self.obligations))

    def to_dict(self):
        return {"success": self.success, "status": self.status,
                "action": None if self.action is None else self.action.to_dict(),
                "output": None if self.output is None else self.output.to_dict(),
                "error": None if self.error is None else _thaw(self.error), "evidence": _thaw(self.evidence),
                "obligations": [o.to_dict() for o in self.obligations],
                "verification": None if self.verification is None else self.verification.to_dict(),
                "state_digest": self.state_digest}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping): raise ContractError("Observation must be an object")
        fields = {"success", "status", "action", "output", "error", "evidence", "obligations",
                  "verification", "state_digest"}
        _exact_keys(data, fields, {"success", "status"})
        if not isinstance(data.get("obligations", []), list): raise ContractError("obligations must be a list")
        action = None if data.get("action") is None else Action.from_dict(data["action"])
        output = None if data.get("output") is None else TypedValue.from_dict(data["output"])
        verification = (None if data.get("verification") is None else
                        VerificationResult.from_dict(data["verification"]))
        obligations = tuple(ProofObligation.from_dict(item) for item in data.get("obligations", []))
        return cls(data["success"], data["status"], action, output, data.get("error"),
                   data.get("evidence", {}), obligations, verification, data.get("state_digest", ""))


@dataclass(frozen=True)
class Episode:
    task: Task
    trace: tuple[Observation, ...] = ()
    def __post_init__(self):
        if not isinstance(self.task, Task): raise ContractError("Episode.task must be Task")
        if not isinstance(self.trace, (list, tuple)) or not all(isinstance(item, Observation) for item in self.trace):
            raise ContractError("Episode.trace must contain Observation values")
        object.__setattr__(self, "trace", tuple(self.trace))
    def to_dict(self): return {"task": self.task.to_dict(), "trace": [o.to_dict() for o in self.trace]}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping): raise ContractError("Episode must be an object")
        _exact_keys(data, {"task", "trace"}, {"task", "trace"})
        if not isinstance(data["trace"], list): raise ContractError("Episode.trace must be a list")
        return cls(Task.from_dict(data["task"]), tuple(Observation.from_dict(item) for item in data["trace"]))
