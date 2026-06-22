import math

import numpy as np

from src.modulation import qpsk_demodulate, qpsk_modulate


def test_qpsk_mapping_and_noiseless_demodulation():
    bits = [0, 0, 0, 1, 1, 1, 1, 0]
    symbols = qpsk_modulate(bits)
    expected = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    for symbol, signs in zip(symbols, expected):
        assert math.copysign(1, symbol.real) == signs[0]
        assert math.copysign(1, symbol.imag) == signs[1]
    assert 0.8 <= float(np.mean(np.abs(symbols) ** 2)) <= 1.2
    assert qpsk_demodulate(symbols)[: len(bits)] == bits
