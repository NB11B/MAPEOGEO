# SPDX-License-Identifier: MIT
"""Deterministic Schema and Grammar Validator for PDI-135M proposals."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    normalized: Optional[dict[str, Any]] = None

    def raise_for_errors(self) -> None:
        if not self.is_valid:
            raise ValueError(f"Schema validation failed: {'; '.join(self.errors)}")


class PDISchemaValidator:
    """Validates raw model output text or dictionary against PDI-v0 grammar & operator registry."""

    def __init__(
        self,
        schema_path: Optional[Path] = None,
        operators_path: Optional[Path] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent / "spec"
        self.schema_path = schema_path or (base_dir / "pdi_v0.schema.json")
        self.operators_path = operators_path or (base_dir / "pdi_v0_operators.json")

        if not self.schema_path.exists():
            raise FileNotFoundError(f"PDI Schema file not found: {self.schema_path}")
        if not self.operators_path.exists():
            raise FileNotFoundError(f"Operator registry not found: {self.operators_path}")

        self.schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        op_data = json.loads(self.operators_path.read_text(encoding="utf-8"))
        self.operator_registry = {op["opcode"]: op for op in op_data["operators"]}
        self.valid_opcodes = set(self.operator_registry.keys())

    def validate_json_string(self, raw_text: str) -> ValidationResult:
        """Parse raw text as JSON and validate against grammar."""
        text = raw_text.strip()
        # Handle optional markdown code block wrapping
        if text.startswith("```json"):
            text = text[len("```json"):].strip()
        if text.startswith("```"):
            text = text[len("```"):].strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            return ValidationResult(
                is_valid=False,
                errors=[f"JSON syntax error: {exc.msg} at line {exc.lineno} col {exc.colno}"],
            )

        if not isinstance(parsed, dict):
            return ValidationResult(
                is_valid=False,
                errors=["Top-level JSON structure must be an object/dict"],
            )

        return self.validate_dict(parsed)

    def validate_dict(self, data: dict[str, Any]) -> ValidationResult:
        """Validate parsed dictionary against the PDI-v0 contract."""
        errors: list[str] = []

        # 1. Base header validation
        schema_version = data.get("schema_version")
        if schema_version != 1:
            errors.append(f"Invalid schema_version: expected 1, got {schema_version}")

        kind = data.get("kind")
        valid_kinds = {"OBSERVE", "PROPOSE", "COMPARE", "CLARIFY", "ESCALATE"}
        if kind not in valid_kinds:
            errors.append(f"Invalid operation kind: '{kind}'. Must be one of {sorted(valid_kinds)}")
            return ValidationResult(is_valid=False, errors=errors)

        # 2. Kind-specific validation
        if kind == "PROPOSE":
            self._validate_propose(data, errors)
        elif kind == "OBSERVE":
            self._validate_observe(data, errors)
        elif kind == "COMPARE":
            self._validate_compare(data, errors)
        elif kind == "CLARIFY":
            self._validate_clarify(data, errors)
        elif kind == "ESCALATE":
            self._validate_escalate(data, errors)

        # 3. Model confidence protection
        # Confidence must never be trusted to bypass authorization
        if "confidence" in data:
            # Drop or warn: model confidence is ignored at the hardware boundary
            data = {k: v for k, v in data.items() if k != "confidence"}

        return ValidationResult(
            is_valid=(len(errors) == 0),
            errors=errors,
            normalized=data if len(errors) == 0 else None,
        )

    def _validate_propose(self, data: dict[str, Any], errors: list[str]) -> None:
        op_id = data.get("operator_id")
        if op_id is None:
            errors.append("PROPOSE operation missing required field 'operator_id'")
        elif not isinstance(op_id, int) or op_id < 0 or op_id > 33:
            errors.append(f"operator_id {op_id} out of bounds (must be 0..33)")
        elif op_id not in self.valid_opcodes:
            errors.append(f"operator_id {op_id} is not registered in authoritative hardware registry")

        obj_refs = data.get("object_refs")
        if obj_refs is None:
            errors.append("PROPOSE operation missing required field 'object_refs'")
        elif not isinstance(obj_refs, list):
            errors.append("object_refs must be a list of integer references")
        else:
            for idx, ref in enumerate(obj_refs):
                if not isinstance(ref, int) or ref < 0 or ref > 65535:
                    errors.append(f"object_refs[{idx}] ({ref}) out of valid reference range (0..65535)")

        dest_ref = data.get("dest_ref")
        if dest_ref is not None:
            if not isinstance(dest_ref, int) or dest_ref < 0 or dest_ref > 255:
                errors.append(f"dest_ref ({dest_ref}) out of valid state memory range (0..255)")

        state_ver = data.get("assumed_state_version")
        if state_ver is None:
            errors.append("PROPOSE operation missing required field 'assumed_state_version'")
        elif not isinstance(state_ver, int) or state_ver < 0 or state_ver > 4294967295:
            errors.append(f"assumed_state_version ({state_ver}) out of 32-bit unsigned range")

        # Validate parameters if present
        params = data.get("parameters")
        if params is not None:
            if not isinstance(params, list):
                errors.append("parameters must be a list of typed objects")
            else:
                for p_idx, p in enumerate(params):
                    if not isinstance(p, dict) or "type" not in p or "value" not in p:
                        errors.append(f"parameters[{p_idx}] must be an object with 'type' and 'value'")
                    else:
                        p_type = p["type"]
                        if p_type not in {"u32", "i32", "fixed_q16_16", "cl20_mv", "addr8"}:
                            errors.append(f"parameters[{p_idx}] invalid type: '{p_type}'")

    def _validate_observe(self, data: dict[str, Any], errors: list[str]) -> None:
        p_type = data.get("projection_type")
        if p_type not in {"STATE", "GRAPH", "EVIDENCE", "TELEMETRY"}:
            errors.append(f"projection_type '{p_type}' must be one of STATE, GRAPH, EVIDENCE, TELEMETRY")

        target_refs = data.get("target_refs")
        if not isinstance(target_refs, list) or len(target_refs) == 0:
            errors.append("target_refs must be a non-empty list of integer IDs")
        else:
            for r in target_refs:
                if not isinstance(r, int) or r < 0 or r > 65535:
                    errors.append(f"target_ref {r} out of valid range (0..65535)")

    def _validate_compare(self, data: dict[str, Any], errors: list[str]) -> None:
        left = data.get("left_ref")
        right = data.get("right_ref")
        if not isinstance(left, int) or left < 0 or left > 255:
            errors.append(f"left_ref {left} must be a valid state address (0..255)")
        if not isinstance(right, int) or right < 0 or right > 255:
            errors.append(f"right_ref {right} must be a valid state address (0..255)")

    def _validate_clarify(self, data: dict[str, Any], errors: list[str]) -> None:
        slots = data.get("missing_slots")
        if not isinstance(slots, list) or len(slots) == 0:
            errors.append("missing_slots must be a non-empty list of slot names")
        reason = data.get("ambiguity_reason")
        if not isinstance(reason, str) or len(reason.strip()) == 0:
            errors.append("ambiguity_reason must be a non-empty descriptive string")

    def _validate_escalate(self, data: dict[str, Any], errors: list[str]) -> None:
        cap = data.get("requested_capability")
        if not isinstance(cap, int) or cap <= 0:
            errors.append(f"requested_capability {cap} must be a positive integer bitmask")
        reason = data.get("reason")
        if not isinstance(reason, str) or len(reason.strip()) == 0:
            errors.append("reason must be a non-empty string explaining the escalation")
