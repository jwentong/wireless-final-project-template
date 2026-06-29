import numpy as np

from src.synchronization import synchronize
from src.modulation import qpsk_modulate
from src.framing import PREAMBLE_BITS
from src.channel import awgn


def _preamble_syms():
    return qpsk_modulate(PREAMBLE_BITS)


def _make_rx(offset, seed=0):
    rng = np.random.default_rng(seed)
    pre = _preamble_syms()
    payload = (2 * rng.integers(0, 2, 200) - 1 + 1j * (2 * rng.integers(0, 2, 200) - 1)) / np.sqrt(2)
    if offset > 0:
        prefix = (rng.standard_normal(offset) + 1j * rng.standard_normal(offset)) / np.sqrt(2)
    else:
        prefix = np.array([], dtype=complex)
    return np.concatenate([prefix, pre, payload])


def test_detect_zero_offset():
    assert abs(synchronize(_make_rx(0), _preamble_syms())) <= 1


def test_detect_various_offsets():
    for off in [25, 64, 128]:
        est = synchronize(_make_rx(off, seed=off), _preamble_syms())
        assert abs(est - off) <= 1


def test_robust_under_awgn_12db():
    rx = awgn(_make_rx(40, seed=2), 12, 3)
    assert abs(synchronize(rx, _preamble_syms()) - 40) <= 1
