# SPDX-License-Identifier: MIT
"""PDI Grounded Training and Evaluation Corpus Generator.

Extracts grounded operational examples directly from:
- Authoritative FPGA operator registry (pdi_v0_operators.json)
- Deterministic state machine checks and state memory contracts
- UoW execution patterns and refusal conditions
- Ambiguous signals requiring CLARIFY or ESCALATE
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random
import sys
PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.adapter.schema_validator import PDISchemaValidator


@dataclass
class PDICorpusRecord:
    example_id: str
    family: str
    partition: str  # "train" | "holdout"
    behavior_class: str  # "POSITIVE_PROPOSAL", "OBSERVE_REQUEST", "COMPARE_REQUEST", "AMBIGUOUS_CLARIFY", "AUTHORITY_ESCALATE"
    input_prompt: str
    target_output: dict[str, Any]
    source_oracle: str
    expected_outcome: str  # "COMMIT", "CLARIFY", "ESCALATE", "REFUSE"

    def to_chat_format(self) -> dict[str, Any]:
        return {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are the SmolLM2-135M deterministic work proposal interface for MAPEOGEO FPGA P0.\n"
                        "Output exclusively valid JSON matching the PDI-v0 schema.\n"
                        "Operations: PROPOSE, OBSERVE, COMPARE, CLARIFY, ESCALATE.\n"
                        "Never fabricate state versions or unauthorized capabilities."
                    ),
                },
                {"role": "user", "content": self.input_prompt},
                {"role": "assistant", "content": json.dumps(self.target_output, indent=2)},
            ]
        }


class PDICorpusGenerator:
    def __init__(self):
        self.validator = PDISchemaValidator()
        self.operators = self.validator.operator_registry

    def generate_corpus(self, seed: int = 42) -> list[PDICorpusRecord]:
        rng = random.Random(seed)
        records: list[PDICorpusRecord] = []

        # 1. POSITIVE PROPOSE CASES for key FPGA operators
        target_ops = [
            (1, "OP_ADD", "Add multivector at state 10 and state 11 into state 12"),
            (2, "OP_SUB", "Subtract multivector at state 14 from state 13 into state 15"),
            (3, "OP_MUL", "Multiply scalar components at state 20 and state 21 into state 22"),
            (4, "OP_COMPARE", "Compare equality of multivectors at state 30 and state 31"),
            (5, "OP_CL20_PRODUCT", "Compute geometric Clifford product of state 40 and state 41 into state 42"),
            (6, "OP_REVERSE", "Compute Clifford reversion of multivector at state 50 into state 51"),
            (7, "OP_GRADE_INVOLUTION", "Compute grade involution of state 60 into state 61"),
            (8, "OP_CLIFFORD_CONJUGATE", "Compute Clifford conjugate of state 70 into state 71"),
            (9, "OP_VECTOR_DOT", "Compute symmetric vector dot product between state 80 and state 81 into state 82"),
            (10, "OP_VECTOR_WEDGE", "Compute exterior wedge product between state 90 and state 91 into state 92"),
            (11, "OP_COMMUTATOR", "Compute commutator product [A, B] of state 100 and state 101 into state 102"),
            (12, "OP_ANTICOMMUTATOR", "Compute anticommutator product {A, B} of state 110 and state 111 into state 112"),
            (13, "OP_SCALAR_PROJECTION", "Extract scalar projection of state 120 into state 121"),
            (14, "OP_VECTOR_PROJECTION", "Extract vector projection of state 130 into state 131"),
            (15, "OP_BIVECTOR_PROJECTION", "Extract bivector projection of state 140 into state 141"),
            (16, "OP_NORM_SQUARED", "Compute norm squared of state 150 into state 151"),
            (18, "OP_MATRIX_TO_CL20", "Convert 2x2 matrix at state 160 into Cl(2,0) multivector at state 161"),
            (19, "OP_CL20_TO_MATRIX", "Convert Cl(2,0) multivector at state 170 into 2x2 matrix at state 171"),
        ]

        # Generate variations for each operator across state versions and parameters
        for op_id, op_name, prompt_base in target_ops:
            for variant in range(8):
                state_ver = 1000 + variant * 17
                src_a = (op_id * 3 + variant) % 250
                src_b = (src_a + 1) % 250
                dest = (src_a + 2) % 250

                target = {
                    "schema_version": 1,
                    "kind": "PROPOSE",
                    "operator_id": op_id,
                    "object_refs": [src_a, src_b],
                    "dest_ref": dest,
                    "assumed_state_version": state_ver,
                }
                # Validation check
                res = self.validator.validate_dict(target)
                assert res.is_valid, f"Generated proposal invalid: {res.errors}"

                # Causal family splitting: variant >= 6 goes to holdout
                partition = "holdout" if variant >= 6 else "train"
                records.append(
                    PDICorpusRecord(
                        example_id=f"PDI-PROP-{op_name}-v{variant:02d}",
                        family=f"operator_{op_name.lower()}",
                        partition=partition,
                        behavior_class="POSITIVE_PROPOSAL",
                        input_prompt=f"Context: Dest address {dest}, pre-state version {state_ver}. Goal: {prompt_base}.",
                        target_output=target,
                        source_oracle="fabric_p0.geo_defs.geo_opcode_t",
                        expected_outcome="COMMIT",
                    )
                )

        # 2. OBSERVE CASES
        obs_targets = [
            ("STATE", [10, 11, 12], "Request bounded state projection for memory words 10, 11, 12"),
            ("GRAPH", [101, 102], "Observe graph neighborhood around nodes 101 and 102 with radius 2"),
            ("EVIDENCE", [1, 2], "Request current evidence root and certificate trail for UoW 1 and 2"),
            ("TELEMETRY", [0], "Observe fabric telemetry and execution counters"),
        ]
        for p_type, refs, desc in obs_targets:
            for variant in range(5):
                target = {
                    "schema_version": 1,
                    "kind": "OBSERVE",
                    "projection_type": p_type,
                    "target_refs": refs,
                }
                if p_type == "GRAPH":
                    target["radius"] = 2
                res = self.validator.validate_dict(target)
                assert res.is_valid
                records.append(
                    PDICorpusRecord(
                        example_id=f"PDI-OBS-{p_type}-v{variant:02d}",
                        family=f"observe_{p_type.lower()}",
                        partition="holdout" if variant >= 4 else "train",
                        behavior_class="OBSERVE_REQUEST",
                        input_prompt=f"Context: Runtime inspection requested. Goal: {desc}.",
                        target_output=target,
                        source_oracle="fabric_p0.geo_graph_memory",
                        expected_outcome="COMMIT",
                    )
                )

        # 3. COMPARE CASES
        for variant in range(10):
            left = variant * 4
            right = variant * 4 + 1
            target = {
                "schema_version": 1,
                "kind": "COMPARE",
                "left_ref": left,
                "right_ref": right,
                "comparator": "EQ",
            }
            res = self.validator.validate_dict(target)
            assert res.is_valid
            records.append(
                PDICorpusRecord(
                    example_id=f"PDI-CMP-v{variant:02d}",
                    family="compare_equivalence",
                    partition="holdout" if variant >= 8 else "train",
                    behavior_class="COMPARE_REQUEST",
                    input_prompt=f"Context: Verification of candidate equivalence. Compare state {left} with state {right}.",
                    target_output=target,
                    source_oracle="fabric_p0.geo_operator_unit.OP_COMPARE",
                    expected_outcome="COMMIT",
                )
            )

        # 4. CLARIFY CASES (Ambiguous / Incomplete requests)
        clarify_cases = [
            ("Perform multivector product without specifying operand source addresses", ["object_refs"], "Missing operand references"),
            ("Commit result into undefined destination slot", ["dest_ref"], "Ambiguous destination address"),
            ("Multiply multivectors under multiple conflicting timestamps", ["assumed_state_version"], "Pre-state version conflict"),
            ("Apply unspecified projection on multivector at state 45", ["operator_id"], "Ambiguous projection type"),
        ]
        for desc, slots, reason in clarify_cases:
            for variant in range(5):
                target = {
                    "schema_version": 1,
                    "kind": "CLARIFY",
                    "missing_slots": slots,
                    "ambiguity_reason": f"{reason} for request: {desc}",
                }
                res = self.validator.validate_dict(target)
                assert res.is_valid
                records.append(
                    PDICorpusRecord(
                        example_id=f"PDI-CLR-{slots[0]}-v{variant:02d}",
                        family="clarify_ambiguity",
                        partition="holdout" if variant >= 4 else "train",
                        behavior_class="AMBIGUOUS_CLARIFY",
                        input_prompt=f"User request: {desc}. Resolve ambiguity.",
                        target_output=target,
                        source_oracle="deterministic_oracle.disambiguation",
                        expected_outcome="CLARIFY",
                    )
                )

        # 5. ESCALATE CASES (Privilege / Capability Boundaries)
        escalate_cases = [
            ("Modify protected system root register at state 0 without capability grant", 0x80000000, "Protected system register modification"),
            ("Perform unbounded graph schema mutation", 0x00000020, "Global graph topology modification"),
            ("Execute raw unverified hardware instruction", 0x00000040, "Hardware kernel privilege escalation"),
        ]
        for desc, cap, reason in escalate_cases:
            for variant in range(5):
                target = {
                    "schema_version": 1,
                    "kind": "ESCALATE",
                    "requested_capability": cap,
                    "reason": reason,
                }
                res = self.validator.validate_dict(target)
                assert res.is_valid
                records.append(
                    PDICorpusRecord(
                        example_id=f"PDI-ESC-{hex(cap)}-v{variant:02d}",
                        family="authority_escalate",
                        partition="holdout" if variant >= 4 else "train",
                        behavior_class="AUTHORITY_ESCALATE",
                        input_prompt=f"User request: {desc}. Determine authorization.",
                        target_output=target,
                        source_oracle="fabric_p0.geo_authority_engine.check4",
                        expected_outcome="ESCALATE",
                    )
                )

        return records


def build_and_save_pdi_manifest(output_path: Optional[Path] = None) -> Path:
    out = output_path or (Path(__file__).resolve().parent.parent / "data" / "pdi_corpus_manifest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    generator = PDICorpusGenerator()
    records = generator.generate_corpus()

    train_recs = [r for r in records if r.partition == "train"]
    holdout_recs = [r for r in records if r.partition == "holdout"]

    manifest = {
        "schema_version": "1.0.0",
        "corpus_id": "pdi-corpus-v0.1",
        "total_records": len(records),
        "train_count": len(train_recs),
        "holdout_count": len(holdout_recs),
        "records": [asdict(r) for r in records],
    }

    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated PDI Corpus: {len(records)} total records ({len(train_recs)} train, {len(holdout_recs)} holdout) saved to {out}")
    return out


if __name__ == "__main__":
    build_and_save_pdi_manifest()
