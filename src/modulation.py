"""QPSK modulation and demodulation using the PRD Gray mapping."""

from __future__ import annotations

from typing import Iterable, List

import numpy as np


INV_SQRT2 = 1.0 / np.sqrt(2.0)
QPSK_TABLE = {
    (0, 0): (1.0 + 1.0j) * INV_SQRT2,
    (0, 1): (-1.0 + 1.0j) * INV_SQRT2,
    (1, 1): (-1.0 - 1.0j) * INV_SQRT2,
    (1, 0): (1.0 - 1.0j) * INV_SQRT2,
}


def _as_bits(bits: Iterable[int]) -> List[int]:
    return [1 if int(bit) else 0 for bit in bits]


def qpsk_modulate(bits: Iterable[int]) -> np.ndarray:
    """Map bit pairs to unit-power Gray-coded QPSK symbols."""
    bit_list = _as_bits(bits)
    if len(bit_list) % 2:
        bit_list.append(0)
    symbols = [QPSK_TABLE[(bit_list[i], bit_list[i + 1])] for i in range(0, len(bit_list), 2)]
    return np.asarray(symbols, dtype=np.complex128)


def qpsk_demodulate(symbols: Iterable[complex]) -> List[int]:
    """Hard-decision QPSK demodulation."""
    out: List[int] = []
    for symbol in np.asarray(list(symbols), dtype=np.complex128):
        if symbol.real >= 0 and symbol.imag >= 0:
            out.extend([0, 0])
        elif symbol.real < 0 and symbol.imag >= 0:
            out.extend([0, 1])
        elif symbol.real < 0 and symbol.imag < 0:
            out.extend([1, 1])
        else:
            out.extend([1, 0])
    return out


modulate_qpsk = qpsk_modulate
qpsk_mapper = qpsk_modulate
modulate = qpsk_modulate
demodulate_qpsk = qpsk_demodulate
qpsk_demapper = qpsk_demodulate
demodulate = qpsk_demodulate

