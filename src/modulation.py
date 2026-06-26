"""Gray-coded QPSK modulation and demodulation."""

from __future__ import annotations

import numpy as np


_NORM = np.sqrt(2.0)
QPSK_MAPPING = {
    (0, 0): (1 + 1j) / _NORM,
    (0, 1): (-1 + 1j) / _NORM,
    (1, 1): (-1 - 1j) / _NORM,
    (1, 0): (1 - 1j) / _NORM,
}


def qpsk_modulate(bits: list[int]) -> np.ndarray:
    """Map bits to normalized Gray-coded QPSK symbols."""
    padded = [int(bit) for bit in bits]
    if len(padded) % 2:
        padded.append(0)

    symbols = [QPSK_MAPPING[(padded[i], padded[i + 1])] for i in range(0, len(padded), 2)]
    return np.asarray(symbols, dtype=complex)


def qpsk_demodulate(symbols: np.ndarray | list[complex]) -> list[int]:
    """Hard-decision demodulation for the required Gray mapping."""
    recovered: list[int] = []
    for symbol in np.asarray(symbols, dtype=complex):
        if symbol.real >= 0 and symbol.imag >= 0:
            recovered.extend([0, 0])
        elif symbol.real < 0 and symbol.imag >= 0:
            recovered.extend([0, 1])
        elif symbol.real < 0 and symbol.imag < 0:
            recovered.extend([1, 1])
        else:
            recovered.extend([1, 0])
    return recovered


modulate_qpsk = qpsk_modulate
demodulate_qpsk = qpsk_demodulate
modulate = qpsk_modulate
demodulate = qpsk_demodulate
