from __future__ import annotations

import math

import numpy as np


_SCALE = 1.0 / math.sqrt(2.0)
_MAPPING = {
    (0, 0): (1 + 1j) * _SCALE,
    (0, 1): (-1 + 1j) * _SCALE,
    (1, 1): (-1 - 1j) * _SCALE,
    (1, 0): (1 - 1j) * _SCALE,
}


def _clean_bits(bits) -> list[int]:
    return [1 if int(bit) else 0 for bit in list(bits)]


def qpsk_modulate(bits) -> np.ndarray:
    clean = _clean_bits(bits)
    if len(clean) % 2:
        clean.append(0)
    symbols = [_MAPPING[(clean[i], clean[i + 1])] for i in range(0, len(clean), 2)]
    return np.array(symbols, dtype=complex)


def qpsk_demodulate(symbols) -> list[int]:
    arr = np.asarray(symbols, dtype=complex)
    bits: list[int] = []
    for symbol in arr:
        real_positive = symbol.real >= 0
        imag_positive = symbol.imag >= 0
        if real_positive and imag_positive:
            bits.extend([0, 0])
        elif (not real_positive) and imag_positive:
            bits.extend([0, 1])
        elif (not real_positive) and (not imag_positive):
            bits.extend([1, 1])
        else:
            bits.extend([1, 0])
    return bits


modulate_qpsk = qpsk_modulate
qpsk_mapper = qpsk_modulate
modulate = qpsk_modulate
demodulate_qpsk = qpsk_demodulate
qpsk_demapper = qpsk_demodulate
demodulate = qpsk_demodulate
