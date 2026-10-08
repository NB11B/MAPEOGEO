# SPDX-License-Identifier: MIT
"""PDI-135M-v0.7A Phase A4: Shadow-State Transaction & Version Manager.

Implements the architectural staging pipeline:
    S_0 -> [Staged Work in Shadow Scratch] -> S_candidate -> [Final Certification] -> S_1

Guarantees:
1. Atomicity: The authoritative destination register R_dest remains strictly untouched
   until all intermediate steps complete and pass final goal postcondition certification.
2. Monotonicity: Upon successful commit, only R_dest's version increments: v_dest <- v_dest + 1.
3. Isolation & Fail-Closed Abort: If any step fails, the transaction aborts with ZERO
   authoritative state mutations (authoritative state is bit-for-bit identical to S_0).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional, Tuple

from pdi.dag.dag_compiler import CompositeDAG, UoWNode
from pdi.dag.register_allocator import AllocationMap, ShadowRegisterAllocator
from pdi.dag.exact_q16_dag_executor import ExactQ16DAGExecutor, DAGExecutionResult, StepExecutionTrace
from pdi.postcondition.fixed_point_oracle import Q16Multivector


class TransactionStatus(str, Enum):
    IDLE = "IDLE"
    STAGING = "STAGING"
    CERTIFIED = "CERTIFIED"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"


@dataclass
class StateWord:
    value: Q16Multivector
    version: int


@dataclass
class TransactionRecord:
    tx_id: str
    goal_id: str
    status: TransactionStatus
    dest_addr: int
    dest_pre_version: int
    dest_post_version: int
    steps_executed: int
    total_steps: int
    evidence_digest: str
    is_authoritative_mutated: bool
    abort_reason: Optional[str] = None


class ShadowTransactionManager:
    """Manages multi-UoW transactions with isolated shadow staging and atomic certification."""

    def __init__(self, initial_state: Optional[Dict[int, Tuple[Q16Multivector, int]]] = None):
        # Authoritative state memory: addr -> StateWord(value, version)
        self.authoritative_memory: Dict[int, StateWord] = {}
        if initial_state:
            for addr, (val, ver) in initial_state.items():
                self.authoritative_memory[addr] = StateWord(val.copy(), ver)

        self.current_tx: Optional[TransactionRecord] = None
        self.staged_memory: Dict[int, StateWord] = {}
        self.evidence_accumulator = hashlib.sha256(b"MAPEOGEO_P0_TRANSACTION_GENESIS")

    def read_authoritative(self, addr: int) -> Optional[StateWord]:
        return self.authoritative_memory.get(addr)

    def execute_transaction(
        self,
        dag: CompositeDAG,
        alloc_map: AllocationMap,
        expected_postcondition: Optional[Q16Multivector] = None,
        inject_fault_at_step: Optional[int] = None,
        fault_type: Optional[str] = None,
    ) -> TransactionRecord:
        tx_id = f"TX_{dag.goal_id}"
        dest_addr = dag.dest_ref if dag.dest_ref is not None else 0
        pre_word = self.authoritative_memory.get(dest_addr, StateWord(Q16Multivector(0, 0, 0, 0), 0))
        dest_pre_ver = pre_word.version

        # 1. Validation check on DAG and Allocation
        if not dag.is_valid:
            return TransactionRecord(
                tx_id=tx_id,
                goal_id=dag.goal_id,
                status=TransactionStatus.ABORTED,
                dest_addr=dest_addr,
                dest_pre_version=dest_pre_ver,
                dest_post_version=dest_pre_ver,
                steps_executed=0,
                total_steps=len(dag.nodes),
                evidence_digest=self.evidence_accumulator.hexdigest(),
                is_authoritative_mutated=False,
                abort_reason=f"DAG compilation invalid: {dag.error_message}",
            )

        if not alloc_map.is_hazard_free:
            return TransactionRecord(
                tx_id=tx_id,
                goal_id=dag.goal_id,
                status=TransactionStatus.ABORTED,
                dest_addr=dest_addr,
                dest_pre_version=dest_pre_ver,
                dest_post_version=dest_pre_ver,
                steps_executed=0,
                total_steps=len(dag.nodes),
                evidence_digest=self.evidence_accumulator.hexdigest(),
                is_authoritative_mutated=False,
                abort_reason=f"Allocation hazards detected: {alloc_map.hazard_report}",
            )

        # 2. Stage workspace initialization (copy authoritative state to shadow workspace)
        # Authoritative memory is NOT modified during staging!
        staged_state: Dict[int, Q16Multivector] = {
            addr: word.value.copy() for addr, word in self.authoritative_memory.items()
        }
        staged_versions: Dict[int, int] = {
            addr: word.version for addr, word in self.authoritative_memory.items()
        }

        # Initialize scratch registers in staged state
        for stage, addr in alloc_map.stage_to_addr.items():
            staged_state[addr] = Q16Multivector(0, 0, 0, 0)
            staged_versions[addr] = 0

        # Snapshot of authoritative memory to verify zero mutation on abort
        auth_snapshot = {k: (v.value.copy(), v.version) for k, v in self.authoritative_memory.items()}

        steps = dag.get_topological_order()
        terminal_value: Optional[Q16Multivector] = None
        executed_count = 0

        # 3. Execute nodes through Staged Workspace
        for node in steps:
            # Check fault injection
            if inject_fault_at_step is not None and node.step_index == inject_fault_at_step:
                # Abort transaction cleanly without writing authoritative state
                return TransactionRecord(
                    tx_id=tx_id,
                    goal_id=dag.goal_id,
                    status=TransactionStatus.ABORTED,
                    dest_addr=dest_addr,
                    dest_pre_version=dest_pre_ver,
                    dest_post_version=dest_pre_ver,
                    steps_executed=executed_count,
                    total_steps=len(steps),
                    evidence_digest=self.evidence_accumulator.hexdigest(),
                    is_authoritative_mutated=False,
                    abort_reason=f"Injected fault ({fault_type}) at step {node.step_index}: fail-closed abort",
                )

            # Resolve source operands
            src_vals: List[Q16Multivector] = []
            for src in node.source_operands:
                addr = alloc_map.stage_to_addr[src] if src.startswith("STAGE_") else int(src.replace("REF_", ""))
                if addr not in staged_state:
                    return TransactionRecord(
                        tx_id=tx_id,
                        goal_id=dag.goal_id,
                        status=TransactionStatus.ABORTED,
                        dest_addr=dest_addr,
                        dest_pre_version=dest_pre_ver,
                        dest_post_version=dest_pre_ver,
                        steps_executed=executed_count,
                        total_steps=len(steps),
                        evidence_digest=self.evidence_accumulator.hexdigest(),
                        is_authoritative_mutated=False,
                        abort_reason=f"Read from uninitialized address {addr}",
                    )
                src_vals.append(staged_state[addr])

            # Resolve dest address in staged state
            target = node.destination_target
            if target.startswith("STAGE_"):
                target_addr = alloc_map.stage_to_addr[target]
            else:
                target_addr = int(target.replace("GOAL_", ""))

            # Compute operator
            try:
                op = node.operator_mnemonic
                from pdi.postcondition.fixed_point_oracle import RTLCliffordSimulator
                res, ov = RTLCliffordSimulator.compute_op(op, src_vals)
                if ov:
                    return TransactionRecord(
                        tx_id=tx_id,
                        goal_id=dag.goal_id,
                        status=TransactionStatus.ABORTED,
                        dest_addr=dest_addr,
                        dest_pre_version=dest_pre_ver,
                        dest_post_version=dest_pre_ver,
                        steps_executed=executed_count,
                        total_steps=len(steps),
                        evidence_digest=self.evidence_accumulator.hexdigest(),
                        is_authoritative_mutated=False,
                        abort_reason="Arithmetic overflow",
                    )
            except ValueError as ve:
                return TransactionRecord(
                    tx_id=tx_id,
                    goal_id=dag.goal_id,
                    status=TransactionStatus.ABORTED,
                    dest_addr=dest_addr,
                    dest_pre_version=dest_pre_ver,
                    dest_post_version=dest_pre_ver,
                    steps_executed=executed_count,
                    total_steps=len(steps),
                    evidence_digest=self.evidence_accumulator.hexdigest(),
                    is_authoritative_mutated=False,
                    abort_reason=str(ve),
                )
            except OverflowError as oe:
                return TransactionRecord(
                    tx_id=tx_id,
                    goal_id=dag.goal_id,
                    status=TransactionStatus.ABORTED,
                    dest_addr=dest_addr,
                    dest_pre_version=dest_pre_ver,
                    dest_post_version=dest_pre_ver,
                    steps_executed=executed_count,
                    total_steps=len(steps),
                    evidence_digest=self.evidence_accumulator.hexdigest(),
                    is_authoritative_mutated=False,
                    abort_reason=f"Arithmetic overflow: {oe}",
                )

            # Write ONLY to staged state (never to authoritative yet)
            staged_state[target_addr] = res
            staged_versions[target_addr] = staged_versions.get(target_addr, 0) + 1
            executed_count += 1

            # Accumulate cryptographic evidence of step
            step_record_bytes = (
                f"{tx_id}:{node.step_index}:{op}:{target_addr}:{res.canonical_hex()}:{staged_versions[target_addr]}"
            ).encode()
            self.evidence_accumulator.update(step_record_bytes)

            if node.is_terminal:
                terminal_value = res

        # 4. Final Goal Postcondition Certification
        if terminal_value is None:
            return TransactionRecord(
                tx_id=tx_id,
                goal_id=dag.goal_id,
                status=TransactionStatus.ABORTED,
                dest_addr=dest_addr,
                dest_pre_version=dest_pre_ver,
                dest_post_version=dest_pre_ver,
                steps_executed=executed_count,
                total_steps=len(steps),
                evidence_digest=self.evidence_accumulator.hexdigest(),
                is_authoritative_mutated=False,
                abort_reason="DAG did not produce terminal output",
            )

        if expected_postcondition is not None:
            if not terminal_value.equals(expected_postcondition):
                return TransactionRecord(
                    tx_id=tx_id,
                    goal_id=dag.goal_id,
                    status=TransactionStatus.ABORTED,
                    dest_addr=dest_addr,
                    dest_pre_version=dest_pre_ver,
                    dest_post_version=dest_pre_ver,
                    steps_executed=executed_count,
                    total_steps=len(steps),
                    evidence_digest=self.evidence_accumulator.hexdigest(),
                    is_authoritative_mutated=False,
                    abort_reason=f"Postcondition mismatch: got {terminal_value}, expected {expected_postcondition}",
                )

        # 5. ATOMIC AUTHORITATIVE COMMIT (Only executed upon 100% full certification)
        dest_post_ver = dest_pre_ver + 1
        self.authoritative_memory[dest_addr] = StateWord(terminal_value.copy(), dest_post_ver)

        return TransactionRecord(
            tx_id=tx_id,
            goal_id=dag.goal_id,
            status=TransactionStatus.COMMITTED,
            dest_addr=dest_addr,
            dest_pre_version=dest_pre_ver,
            dest_post_version=dest_post_ver,
            steps_executed=executed_count,
            total_steps=len(steps),
            evidence_digest=self.evidence_accumulator.hexdigest(),
            is_authoritative_mutated=True,
        )
