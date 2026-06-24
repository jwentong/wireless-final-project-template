"""QPSK modulation and demodulation (Gray mapping, PRD unified)."""

from __future__ import annotations

import numpy as np

# Gray QPSK: 00->(1+j), 01->(-1+j), 11->(-1-j), 10->(1-j), normalized by sqrt(2)
_MAP = {
    (0, 0): 1 + 1j,
    (0, 1): -1 + 1j,
    (1, 1): -1 - 1j,
    (1, 0): 1 - 1j,
}
_INV = {(v.real, v.imag): k for k, v in _MAP.items()}
_SCALE = np.sqrt(2.0)


def qpsk_modulate(bits: list[int]) -> np.ndarray:
    data = [int(b) for b in bits]
    if len(data) % 2 == 1:
        data.append(0)
    symbols = []
    for i in range(0, len(data), 2):
        pair = (data[i], data[i + 1])
        symbols.append(_MAP[pair] / _SCALE)
    return np.asarray(symbols, dtype=complex)


def qpsk_demodulate(symbols: np.ndarray) -> list[int]:
    bits: list[int] = []
    for sym in symbols:
        i_sign = 1 if sym.real >= 0 else -1
        q_sign = 1 if sym.imag >= 0 else -1
        key = (float(i_sign), float(q_sign))
        b0, b1 = _INV[key]
        bits.extend([b0, b1])
    return bits
