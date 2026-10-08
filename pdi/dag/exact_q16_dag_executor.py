# SPDX-License-Identifier: MIT
"""PDI-135M-v0.7A Phase A3: Exact Q16.16 Reference DAG Execution.

Simulates multi-step DAG execution using bit-exact Q16.16 fixed-point arithmetic
matching RTL hardware (geo_fixed_arith.sv, geo_cl20_multivector.sv).

Records exact numerical intermediate states and final goal multivectors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from pdi.dag.dag_compiler import CompositeDAG, UoWNode
from pdi.dag.register_allocator import AllocationMap
from pdi.postcondition.fixed_point_oracle import Q16Multivector, RTLCliffordSimulator


@dataclass
class StepExecutionTrace:
    step_index: int
    node_id: str
    operator_mnemonic: str
    src_addrs: List[int]
    src_values: List[Q16Multivector]
    dest_addr: int
    result_value: Q16Multivector
    is_terminal: bool
    overflow_detected: bool = False


@dataclass
class DAGExecutionResult:
    goal_id: str
    is_successful: bool
    final_output: Optional[Q16Multivector]
    dest_addr: int
    step_traces: List[StepExecutionTrace]
    final_state_snapshot: Dict[int, Q16Multivector]
    error_message: Optional[str] = None


class ExactQ16DAGExecutor:
    """Executes multi-step DAGs with bit-exact Clifford arithmetic simulation."""

    @classmethod
    def execute_dag(
        cls,
        dag: CompositeDAG,
        alloc_map: AllocationMap,
        initial_state: Dict[int, Q16Multivector],
    ) -> DAGExecutionResult:
        if not dag.is_valid:
            return DAGExecutionResult(
                goal_id=dag.goal_id,
                is_successful=False,
                final_output=None,
                dest_addr=dag.dest_ref or 0,
                step_traces=[],
                final_state_snapshot=dict(initial_state),
                error_message=f"DAG is invalid: {dag.error_message}",
            )

        if not alloc_map.is_hazard_free:
            return DAGExecutionResult(
                goal_id=dag.goal_id,
                is_successful=False,
                final_output=None,
                dest_addr=dag.dest_ref or 0,
                step_traces=[],
                final_state_snapshot=dict(initial_state),
                error_message=f"Allocation hazards detected: {alloc_map.hazard_report}",
            )

        # Working memory copy (contains initial authoritative states + shadow scratch)
        working_state: Dict[int, Q16Multivector] = {k: v.copy() for k, v in initial_state.items()}
        traces: List[StepExecutionTrace] = []
        final_output: Optional[Q16Multivector] = None

        # Execute nodes in topological order
        for node in dag.get_topological_order():
            # Resolve source addresses and values
            src_addrs: List[int] = []
            src_values: List[Q16Multivector] = []

            for src in node.source_operands:
                if src.startswith("STAGE_"):
                    addr = alloc_map.stage_to_addr.get(src)
                elif src.startswith("REF_"):
                    addr = int(src.replace("REF_", ""))
                else:
                    addr = int(src)

                if addr not in working_state:
                    return DAGExecutionResult(
                        goal_id=dag.goal_id,
                        is_successful=False,
                        final_output=None,
                        dest_addr=dag.dest_ref or 0,
                        step_traces=traces,
                        final_state_snapshot=working_state,
                        error_message=f"Uninitialized register read: address {addr} for operand {src} in step {node.step_index}",
                    )

                src_addrs.append(addr)
                src_values.append(working_state[addr])

            # Resolve destination address
            dest_target = node.destination_target
            if dest_target.startswith("STAGE_"):
                dest_addr = alloc_map.stage_to_addr[dest_target]
            elif dest_target.startswith("GOAL_"):
                dest_addr = int(dest_target.replace("GOAL_", ""))
            else:
                dest_addr = int(dest_target)

            # Execute operator using RTLCliffordSimulator bit-exact model
            op = node.operator_mnemonic
            try:
                res, ov = RTLCliffordSimulator.compute_op(op, src_values)
                if ov:
                    return DAGExecutionResult(
                        goal_id=dag.goal_id,
                        is_successful=False,
                        final_output=None,
                        dest_addr=dag.dest_ref or 0,
                        step_traces=traces,
                        final_state_snapshot=working_state,
                        error_message=f"Arithmetic overflow in step {node.step_index}",
                    )
            except ValueError as ve:
                return DAGExecutionResult(
                    goal_id=dag.goal_id,
                    is_successful=False,
                    final_output=None,
                    dest_addr=dag.dest_ref or 0,
                    step_traces=traces,
                    final_state_snapshot=working_state,
                    error_message=str(ve),
                )
            except OverflowError as oe:
                return DAGExecutionResult(
                    goal_id=dag.goal_id,
                    is_successful=False,
                    final_output=None,
                    dest_addr=dag.dest_ref or 0,
                    step_traces=traces,
                    final_state_snapshot=working_state,
                    error_message=f"Arithmetic overflow in step {node.step_index}: {oe}",
                )

            # Commit to working state
            working_state[dest_addr] = res

            traces.append(
                StepExecutionTrace(
                    step_index=node.step_index,
                    node_id=node.node_id,
                    operator_mnemonic=op,
                    src_addrs=src_addrs,
                    src_values=src_values,
                    dest_addr=dest_addr,
                    result_value=res,
                    is_terminal=node.is_terminal,
                )
            )

            if node.is_terminal:
                final_output = res

        return DAGExecutionResult(
            goal_id=dag.goal_id,
            is_successful=True,
            final_output=final_output,
            dest_addr=dag.dest_ref or 0,
            step_traces=traces,
            final_state_snapshot=working_state,
        )
