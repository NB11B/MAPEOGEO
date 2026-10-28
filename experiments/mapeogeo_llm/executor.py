"""Transactional bounded executor with independent goal verification."""
from __future__ import annotations
from hashlib import sha256
import math
import re
import time
from typing import Any
import torch

from .contracts import (Action, ContractError, Observation, ProofObligation, Ref, Task,
                        TypedValue, VerificationResult, PROGRAM_OPS, canonical_digest,
                        canonical_json, lexical_token_count)
from .datasets.oracle import geometric_grade, geometric_product, safe_expression
from .operators import CompiledALU, from_bits, to_bits
from .parser import parse_action

_ALU = {"ADD", "SUB", "XOR", "AND", "OR", "EQ"}
_ARITY = {op: 2 for op in _ALU} | {"GEO_GP": 2, "GEO_GRADE": 1, "GRAPH_QUERY": 1,
                                  "ASSERT": 0, "VERIFY": 1, "HALT": 0}
_KWARGS = {op: frozenset() for op in _ALU} | {
    "GEO_GP": frozenset({"signature"}),
    "GEO_GRADE": frozenset({"signature", "grade"}),
    "GRAPH_QUERY": frozenset({"relation", "max_results"}),
    "ASSERT": frozenset({"proposition"}),
    "VERIFY": frozenset({"proof", "timeout_seconds"}),
    "HALT": frozenset({"status"}),
}
_REGEX = re.compile(r"r(?:0|[1-9][0-9]*)\Z")


class Engine:
    def __init__(self, task: Task, geo=None, graph=None, lean=None):
        if not isinstance(task, Task): raise ContractError("Engine requires Task")
        self.task, self.geo, self.graph, self.lean = task, geo, graph, lean
        self._alu = CompiledALU()
        self._registers: dict[str, TypedValue] = {}
        self._trace: list[Observation] = []
        self._obligations: list[ProofObligation] = []
        self._verification: VerificationResult | None = None
        self._halted = False
        self._halt_status: str | None = None
        self._program_ops_used = 0
        goal_allowed = task.goal.get("allowed_ops") if task.goal.get("kind") == "target" else None
        self._allowed_ops = frozenset(goal_allowed) if goal_allowed is not None else PROGRAM_OPS
        self._max_program_ops = task.goal.get("max_ops", task.budget.max_steps)
        self._started = time.monotonic()

    def _state_payload(self):
        return {"task_digest": self.task.canonical_digest(),
                "registers": {k: v.to_dict() for k, v in sorted(self._registers.items())},
                "obligations": [o.to_dict() for o in self._obligations],
                "steps_used": len(self._trace), "program_ops_used": self._program_ops_used,
                "allowed_ops": sorted(self._allowed_ops), "max_program_ops": self._max_program_ops,
                "halted": self._halted, "halt_status": self._halt_status}

    def _state_digest(self): return canonical_digest(self._state_payload())
    def _trace_digest(self): return canonical_digest([o.to_dict() for o in self._trace])

    def observation(self) -> dict:
        return {"registers": {k: v.to_dict() for k, v in sorted(self._registers.items())},
                "obligations": [o.to_dict() for o in self._obligations],
                "verification": None if self._verification is None else self._verification.to_dict(),
                "steps_used": len(self._trace), "steps_remaining": self.task.budget.max_steps - len(self._trace),
                "program_ops_used": self._program_ops_used,
                "program_ops_remaining": self._max_program_ops - self._program_ops_used,
                "allowed_ops": sorted(self._allowed_ops),
                "halted": self._halted, "status": self._current_status(),
                "state_digest": self._state_digest(), "trace_digest": self._trace_digest()}

    def _current_status(self):
        if self._halt_status: return self._halt_status
        if self._obligations: return "UNSOLVED"
        if self._verification and self._verification.state_digest == self._state_digest(): return self._verification.status
        return "UNSOLVED" if self._obligations or self._registers else "RUNNING"

    def _failed(self, action, status, code, message):
        return Observation(False, status, action=action, error={"code": code, "message": str(message)},
                           obligations=tuple(self._obligations), verification=self._verification,
                           state_digest=self._state_digest())

    def step(self, action: Action | dict | str) -> Observation:
        if isinstance(action, str) and len(action.encode("utf-8")) > self.task.budget.max_input_bytes:
            return self._failed(None, "INVALID_INPUT", "ACTION_SIZE", "raw action exceeds task byte budget")
        try:
            if isinstance(action, (dict, str)): action = parse_action(action)
            if not isinstance(action, Action): raise ContractError("step requires Action")
        except (ContractError, ValueError, TypeError) as exc:
            return self._failed(None, "INVALID_INPUT", "MALFORMED_ACTION", exc)
        try:
            action_bytes = len(canonical_json(action).encode("utf-8"))
            action_tokens = lexical_token_count(action)
        except ContractError as exc:
            return self._failed(action, "INVALID_INPUT", "MALFORMED_ACTION", exc)
        if action_bytes > self.task.budget.max_input_bytes or action_tokens > self.task.budget.max_token_count:
            return self._failed(action, "INVALID_INPUT", "ACTION_SIZE", "action exceeds task public size budget")
        if self._halted: return self._failed(action, "EXECUTION_ERROR", "ALREADY_HALTED", "episode already halted")
        if len(self._trace) >= self.task.budget.max_steps:
            return self._failed(action, "BUDGET_EXHAUSTED", "STEP_BUDGET", "step budget exhausted")
        if time.monotonic() - self._started > self.task.budget.wall_time_seconds:
            return self._failed(action, "BUDGET_EXHAUSTED", "WALL_TIME", "wall-time budget exhausted")
        if action.op not in _ARITY:
            return self._failed(action, "INVALID_INPUT", "UNSUPPORTED_ACTION", f"unsupported op {action.op!r}")
        if action.op in PROGRAM_OPS and action.op not in self._allowed_ops:
            return self._failed(action, "INVALID_INPUT", "DISALLOWED_OPERATOR",
                                f"operator {action.op!r} is outside task allowed_ops")
        if action.op in PROGRAM_OPS and self._program_ops_used >= self._max_program_ops:
            return self._failed(action, "BUDGET_EXHAUSTED", "OP_BUDGET", "program operation budget exhausted")
        if len(action.src) != _ARITY[action.op]:
            return self._failed(action, "INVALID_INPUT", "ARITY", f"{action.op} requires {_ARITY[action.op]} sources")
        unknown_kwargs = set(action.kwargs) - _KWARGS[action.op]
        if unknown_kwargs:
            return self._failed(action, "INVALID_INPUT", "UNKNOWN_KWARGS",
                                f"unsupported kwargs {sorted(unknown_kwargs)}")
        if action.op in {"ASSERT", "VERIFY", "HALT"} and action.dst is not None:
            return self._failed(action, "INVALID_INPUT", "INVALID_DESTINATION",
                                f"{action.op} does not write a register")
        try:
            observation, commit = self._execute(action)
        except _EarlyHalt as exc:
            return self._failed(action, "INVALID_INPUT", "EARLY_HALT", exc)
        except _StaleVerification as exc:
            return self._failed(action, "INVALID_INPUT", "STALE_VERIFICATION", exc)
        except _OpenObligations as exc:
            return self._failed(action, "INVALID_INPUT", "OPEN_OBLIGATIONS", exc)
        except (ContractError, ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
            return self._failed(action, "INVALID_INPUT", "VALIDATION", exc)
        except Exception as exc:
            return self._failed(action, "EXECUTION_ERROR", "TOOL_ERROR", exc)
        if time.monotonic() - self._started > self.task.budget.wall_time_seconds:
            return self._failed(action, "BUDGET_EXHAUSTED", "WALL_TIME", "wall-time budget exhausted")
        try:
            result_bytes = len(canonical_json(observation).encode("utf-8"))
            result_tokens = lexical_token_count(observation)
        except ContractError as exc:
            return self._failed(action, "INVALID_INPUT", "RESULT_SIZE", exc)
        if result_bytes > self.task.budget.max_input_bytes or result_tokens > self.task.budget.max_token_count:
            return self._failed(action, "INVALID_INPUT", "RESULT_SIZE", "tool result exceeds task public size budget")
        commit()
        if action.op in PROGRAM_OPS: self._program_ops_used += 1
        next_payload = self._state_payload()
        next_payload["steps_used"] += 1
        next_state_digest = canonical_digest(next_payload)
        final = Observation(True, observation.status, action=action, output=observation.output,
                            evidence=observation.evidence, obligations=tuple(self._obligations),
                            verification=self._verification, state_digest=next_state_digest)
        self._trace.append(final)
        return final

    def _resolve(self, ref: Ref) -> TypedValue:
        if ref.kind == "input":
            if ref.id not in self.task.inputs: raise ContractError(f"unknown input {ref.id!r}")
            return self.task.inputs[ref.id]
        if ref.kind == "reg":
            if ref.id not in self._registers: raise ContractError(f"uninitialized register {ref.id!r}")
            return self._registers[ref.id]
        if ref.kind == "literal":
            value = ref.value
            if isinstance(value, bool): return TypedValue("boolean", value)
            if isinstance(value, int): return TypedValue("uint8" if 0 <= value <= 255 else "integer", value)
            if isinstance(value, (tuple, list)): return TypedValue("float_multivector", value)
            if isinstance(value, str): return TypedValue("proposition", value)
            raise ContractError("unsupported literal")
        if ref.kind == "node": return TypedValue("graph_node", ref.id)
        raise ContractError("unsupported reference")

    def _check_dst(self, dst):
        if dst is None or not _REGEX.fullmatch(dst): raise ContractError("canonical destination r0..rN required")
        index = int(dst[1:])
        if index >= self.task.budget.max_registers: raise ContractError("register index exceeds budget")
        if dst not in self._registers and len(self._registers) >= self.task.budget.max_registers:
            raise ContractError("register budget exhausted")

    def _execute(self, action):
        noop = lambda: None
        if action.op in _ALU:
            self._check_dst(action.dst)
            values = [self._resolve(r) for r in action.src]
            if any(v.kind != "uint8" or isinstance(v.value, bool) or not isinstance(v.value, int)
                   or not 0 <= v.value <= 255 for v in values): raise ContractError("ALU operands must be uint8")
            a, b = (torch.tensor([v.value], dtype=torch.int64) for v in values)
            result = int(from_bits(self._alu(action.op, to_bits(a), to_bits(b)))[0])
            output = TypedValue("uint8", result)
            def commit(): self._registers[action.dst] = output
            return Observation(True, "RUNNING", output=output), commit
        if action.op in {"GEO_GP", "GEO_GRADE"}:
            self._check_dst(action.dst)
            if self.geo is None: raise ContractError("GEO adapter unavailable")
            values = [self._resolve(r) for r in action.src]
            if any(v.kind != "float_multivector" for v in values): raise ContractError("GEO operands required")
            signature = action.kwargs.get("signature")
            if not isinstance(signature, tuple) or not 1 <= len(signature) <= 6 or any(x not in (-1, 1) for x in signature):
                raise ContractError("signature must contain 1..6 entries of +/-1")
            if action.op == "GEO_GP": raw = self.geo.gp(list(values[0].value), list(values[1].value), list(signature))
            else:
                grade = action.kwargs.get("grade")
                if isinstance(grade, bool) or not isinstance(grade, int): raise ContractError("integer grade required")
                raw = self.geo.grade(list(values[0].value), grade, list(signature))
            if not isinstance(raw, list) or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in raw):
                raise ContractError("invalid GEO adapter result")
            output = TypedValue("float_multivector", raw)
            def commit(): self._registers[action.dst] = output
            return Observation(True, "RUNNING", output=output,
                               evidence={"adapter": getattr(self.geo, "metadata", lambda: {})()}), commit
        if action.op == "GRAPH_QUERY":
            self._check_dst(action.dst)
            if self.graph is None: raise ContractError("graph adapter unavailable")
            node = self._resolve(action.src[0])
            if node.kind != "graph_node": raise ContractError("graph node required")
            limit = action.kwargs.get("max_results", self.task.budget.max_graph_expansion)
            if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= self.task.budget.max_graph_expansion:
                raise ContractError("invalid graph expansion")
            raw = self.graph.query(node.value, action.kwargs.get("relation"), limit)
            if not isinstance(raw, dict): raise ContractError("invalid graph result")
            output = TypedValue("graph_node", raw)
            def commit(): self._registers[action.dst] = output
            return Observation(True, "RUNNING", output=output, evidence={"proof_verified": False}), commit
        if action.op == "ASSERT":
            proposition = action.kwargs.get("proposition")
            if not isinstance(proposition, str) or not proposition: raise ContractError("proposition required")
            obligation = ProofObligation(proposition)
            def commit(): self._obligations.append(obligation)
            return Observation(True, "UNSOLVED"), commit
        if action.op == "VERIFY": return self._verify(action)
        if action.op == "HALT": return self._halt(action)
        raise ContractError("unsupported action")

    def _verification_state_digest(self):
        payload = self._state_payload()
        payload["steps_used"] += 1
        return canonical_digest(payload)

    def _verify(self, action):
        candidate = self._resolve(action.src[0])
        goal = self.task.goal
        kind = goal.get("kind")
        evidence: dict[str, Any] = {"checker": "independent_runtime_oracle", "goal_kind": kind,
                                   "scope": "candidate_vs_goal"}
        if kind == "expression":
            names = {k: v.value for k, v in self.task.inputs.items() if v.kind in {"uint8", "integer"}}
            expected = safe_expression(goal.get("expression"), names)
            expected_kind = "boolean" if isinstance(expected, bool) else "uint8"
            verified = candidate.kind == expected_kind and candidate.value == expected
        elif kind == "target":
            target = goal.get("value")
            if isinstance(target, dict): expected = TypedValue.from_dict(target)
            elif isinstance(target, bool): expected = TypedValue("boolean", target)
            elif isinstance(target, int): expected = TypedValue("uint8" if 0 <= target <= 255 else "integer", target)
            elif isinstance(target, str): expected = TypedValue("proposition", target)
            elif isinstance(target, (list, tuple)): expected = TypedValue("float_multivector", target)
            else: raise ContractError("invalid target")
            verified = candidate.kind == expected.kind and candidate.value == expected.value
        elif kind == "geo_expression":
            op, operand_names = goal.get("op"), goal.get("operands")
            signature, tolerance = goal.get("signature"), goal.get("tolerance", 1e-9)
            if candidate.kind != "float_multivector" or not isinstance(operand_names, tuple) or \
                    not all(isinstance(name, str) and name in self.task.inputs for name in operand_names) or \
                    isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or tolerance < 0:
                raise ContractError("invalid numerical GEO goal")
            operands = [self.task.inputs[name] for name in operand_names]
            if any(value.kind != "float_multivector" for value in operands): raise ContractError("GEO inputs required")
            if op == "gp" and len(operands) == 2:
                expected = geometric_product(operands[0].value, operands[1].value, signature)
            elif op == "grade" and len(operands) == 1:
                expected = geometric_grade(operands[0].value, goal.get("grade"), signature)
            else: raise ContractError("unsupported GEO goal expression")
            verified = len(candidate.value) == len(expected) and all(math.isfinite(float(x)) and
                       abs(float(x) - float(y)) <= tolerance for x, y in zip(candidate.value, expected))
            evidence.update({"tolerance": tolerance, "evidence_class": "independent_numerical_oracle"})
        elif kind == "lean":
            if self.lean is None: raise ContractError("Lean adapter unavailable")
            proposition, proof = goal.get("proposition"), action.kwargs.get("proof")
            if not isinstance(proposition, str) or not isinstance(proof, str): raise ContractError("Lean proposition/proof required")
            raw = self.lean.verify(proposition, proof, float(action.kwargs.get("timeout_seconds", 10)))
            if not isinstance(raw, dict): raise ContractError("invalid Lean result")
            if raw.get("status") not in {"VERIFIED", "UNSOLVED", "INVALID_INPUT", "TIMEOUT"}:
                raise ContractError("invalid Lean status")
            lean_evidence = raw.get("evidence")
            if not isinstance(lean_evidence, dict): raise ContractError("invalid Lean evidence")
            kernel_checked, axioms = lean_evidence.get("kernel_checked"), lean_evidence.get("axioms")
            if not isinstance(kernel_checked, bool): raise ContractError("Lean kernel_checked must be boolean")
            if axioms is not None and (not isinstance(axioms, list) or not all(isinstance(x, str) for x in axioms)):
                raise ContractError("Lean axioms must be a string list or null")
            evidence = {"checker": "lean", **raw}
            if raw.get("status") == "VERIFIED" and kernel_checked is True and axioms == []:
                verification = VerificationResult("VERIFIED", candidate, self._verification_state_digest(), evidence)
                def commit(): self._verification = verification
                return Observation(True, "VERIFIED", output=candidate, verification=verification, evidence=evidence), commit
            verification = VerificationResult("UNSOLVED", candidate, self._verification_state_digest(), evidence)
            def commit(): self._verification = verification
            return Observation(True, "UNSOLVED", output=candidate, verification=verification, evidence=evidence), commit
        elif kind == "graph":
            raise ContractError("graph metadata is not independently replayed proof")
        else: raise ContractError(f"unsupported goal kind {kind!r}")
        status = "VERIFIED" if verified else "REFUTED"
        verification = VerificationResult(status, candidate, self._verification_state_digest(), evidence)
        def commit(): self._verification = verification
        return Observation(True, status, output=candidate, verification=verification, evidence=evidence), commit

    def _halt(self, action):
        requested = action.kwargs.get("status")
        if requested is not None:
            if requested != "UNSOLVED": raise ContractError("only explicit UNSOLVED halt is supported")
            def commit():
                self._halted, self._halt_status = True, "UNSOLVED"
            return Observation(True, "UNSOLVED"), commit
        if self._obligations: raise _OpenObligations("OPEN_OBLIGATIONS")
        if self._verification is None or self._verification.status == "UNSOLVED": raise _EarlyHalt("EARLY_HALT")
        if self._verification.state_digest != self._state_digest(): raise _StaleVerification("STALE_VERIFICATION")
        status = self._verification.status
        def commit():
            self._halted, self._halt_status = True, status
        return Observation(True, status, output=self._verification.output), commit

    def result(self) -> dict:
        status = self._current_status()
        verification = self._verification
        current = verification is not None and (verification.state_digest == self._state_digest() or
                  (self._halted and self._halt_status in {"VERIFIED", "REFUTED"}))
        output = verification.output if current else None
        return {"status": status, "output": None if output is None else output.to_dict(),
                "verification": None if verification is None else verification.to_dict(),
                "obligations": [o.to_dict() for o in self._obligations], "halted": self._halted,
                "steps_used": len(self._trace), "state_digest": self._state_digest(),
                "trace_digest": self._trace_digest(), "trace": [o.to_dict() for o in self._trace]}


class _EarlyHalt(ContractError): pass
class _StaleVerification(ContractError): pass
class _OpenObligations(ContractError): pass
