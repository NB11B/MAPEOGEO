# SPDX-License-Identifier: MIT
"""Unit and Integration Tests for Track PDI-v0.7A Complete-Work DAG Qualification."""

import pytest
from pdi.dag.dag_compiler import DAGCompiler, CompositeDAG, ExpressionFamily
from pdi.dag.register_allocator import ShadowRegisterAllocator, AllocationMap
from pdi.dag.exact_q16_dag_executor import ExactQ16DAGExecutor
from pdi.dag.transaction_manager import ShadowTransactionManager, TransactionStatus, StateWord
from pdi.postcondition.fixed_point_oracle import Q16Multivector, RTLCliffordSimulator


def test_dag_compilation_families():
    # 1. Contraction on exterior wedge
    dag1 = DAGCompiler.compile_expression("G1", "(state 10 ^ state 11) . state 12", dest_ref=100)
    assert dag1.is_valid
    assert dag1.family == ExpressionFamily.CONTRACTION_WEDGE
    assert len(dag1.nodes) == 2
    assert dag1.nodes[0].operator_mnemonic == "OP_VECTOR_WEDGE"
    assert dag1.nodes[1].operator_mnemonic == "OP_VECTOR_DOT"
    assert dag1.scratch_registers_required == 1

    # 2. Commutator bracket
    dag2 = DAGCompiler.compile_expression("G2", "[state 20, state 21]", dest_ref=140)
    assert dag2.is_valid
    assert dag2.family == ExpressionFamily.COMMUTATOR_BRACKET
    assert len(dag2.nodes) == 3
    assert dag2.scratch_registers_required == 2

    # 3. Rotor sandwich
    dag3 = DAGCompiler.compile_expression("G3", "state 30 * state 31 * ~state 30", dest_ref=180)
    assert dag3.is_valid
    assert dag3.family == ExpressionFamily.ROTOR_SANDWICH
    assert len(dag3.nodes) == 3
    assert dag3.nodes[0].operator_mnemonic == "OP_REVERSE"
    assert dag3.scratch_registers_required == 2

    # 4. Unsupported expression (Fail-closed)
    dag4 = DAGCompiler.compile_expression("G4", "division of state 10 / state 11", dest_ref=200)
    assert not dag4.is_valid
    assert dag4.family == ExpressionFamily.UNSUPPORTED
    assert "fail-closed" in dag4.error_message.lower()


def test_shadow_register_allocation_hazard_freedom():
    dag = DAGCompiler.compile_expression("G1", "(state 10 ^ state 11) . state 12", dest_ref=100)
    alloc = ShadowRegisterAllocator.allocate_registers(dag)
    assert alloc.is_hazard_free
    assert len(alloc.stage_to_addr) == 1
    scratch_addr = alloc.stage_to_addr["STAGE_0"]
    assert scratch_addr >= 0xE0 and scratch_addr <= 0xFE
    assert scratch_addr not in {10, 11, 12, 100}


def test_exact_q16_mathematical_invariants():
    # Vector wedge antisymmetry: A ^ B == -(B ^ A)
    va = Q16Multivector.from_floats(s=0, e1=1.5, e2=-0.5, e12=0)
    vb = Q16Multivector.from_floats(s=0, e1=0.8, e2=1.2, e12=0)

    w_ab, _ = RTLCliffordSimulator.compute_op("OP_VECTOR_WEDGE", [va, vb])
    w_ba, _ = RTLCliffordSimulator.compute_op("OP_VECTOR_WEDGE", [vb, va])
    assert w_ab.e12 == -w_ba.e12

    # Commutator bracket on vectors: [A, B] = 2 * (A ^ B) in Cl(2,0)
    p_ab, _ = RTLCliffordSimulator.compute_op("OP_CL20_PRODUCT", [va, vb])
    p_ba, _ = RTLCliffordSimulator.compute_op("OP_CL20_PRODUCT", [vb, va])
    comm_manual, _ = RTLCliffordSimulator.compute_op("OP_SUB", [p_ab, p_ba])
    # The bivector component of AB - BA is exactly 2 * (A ^ B)
    assert abs(comm_manual.e12 - 2 * w_ab.e12) <= 1


def test_shadow_transaction_isolation_and_rollback():
    dag = DAGCompiler.compile_expression("G_ROTOR", "state 30 * state 31 * ~state 30", dest_ref=180)
    alloc = ShadowRegisterAllocator.allocate_registers(dag)

    # Initial state
    vr = Q16Multivector.from_floats(s=1.0, e1=0, e2=0, e12=0)  # identity rotor
    va = Q16Multivector.from_floats(s=0, e1=1.0, e2=2.0, e12=0)
    initial_state = {
        30: (vr, 1),
        31: (va, 1),
        180: (Q16Multivector(0, 0, 0, 0), 1),
    }

    # 1. Successful commit test
    tx_mgr = ShadowTransactionManager(initial_state)
    tx_rec = tx_mgr.execute_transaction(dag, alloc)
    assert tx_rec.status == TransactionStatus.COMMITTED
    assert tx_rec.dest_post_version == 2
    dest_word = tx_mgr.read_authoritative(180)
    assert dest_word.version == 2
    assert dest_word.value.e1 == va.e1
    assert dest_word.value.e2 == va.e2

    # 2. Fault injection rollback test
    tx_mgr_fault = ShadowTransactionManager(initial_state)
    fault_rec = tx_mgr_fault.execute_transaction(dag, alloc, inject_fault_at_step=1, fault_type="BUS_TIMEOUT")
    assert fault_rec.status == TransactionStatus.ABORTED
    assert not fault_rec.is_authoritative_mutated
    # Destination register version and value MUST remain untouched at initial state!
    dest_fault_word = tx_mgr_fault.read_authoritative(180)
    assert dest_fault_word.version == 1
    assert dest_fault_word.value.equals(Q16Multivector(0, 0, 0, 0))
    # Scratch space must not exist in authoritative memory
    for stage_addr in alloc.stage_to_addr.values():
        assert tx_mgr_fault.read_authoritative(stage_addr) is None
