import numpy as np

from ngc_rq.objects import (
    RealPhaseOperator,
    RealPhaseState,
    block_decompose,
    is_realified_operator,
    validate_realified_operator,
)
from ngc_rq.real_phase import (
    complexify_operator,
    complexify_vector,
    random_complex_state,
    random_unitary,
    realify_operator,
    realify_vector,
)


def test_vector_roundtrip():
    rng = np.random.default_rng(1)
    psi = random_complex_state(8, rng)
    assert np.allclose(complexify_vector(realify_vector(psi)), psi)


def test_operator_roundtrip_and_block_validation():
    rng = np.random.default_rng(2)
    op = random_unitary(4, rng)
    op_r = realify_operator(op)
    assert is_realified_operator(op_r)
    validate_realified_operator(op_r, dim=4)
    a, b = block_decompose(op_r)
    assert np.allclose(a + 1j * b, op)
    assert np.allclose(complexify_operator(op_r), op)


def test_state_and_operator_wrappers_apply():
    rng = np.random.default_rng(3)
    psi = random_complex_state(4, rng)
    u = random_unitary(4, rng)
    state = RealPhaseState.from_complex(psi, dims=(2, 2))
    op = RealPhaseOperator.from_complex(u, dims=(2, 2))
    out = op.apply(state)
    assert out.dims == (2, 2)
    assert np.allclose(out.data, realify_vector(u @ psi))
