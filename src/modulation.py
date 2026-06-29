"""Digital modulation: QPSK (default), BPSK and 16-QAM.

All constellations are normalized to unit average symbol power. QPSK uses the
PRD-mandated Gray mapping:
    00 -> (1+j)/sqrt(2)   01 -> (-1+j)/sqrt(2)
    11 -> (-1-j)/sqrt(2)  10 -> (1-j)/sqrt(2)
"""
from __future__ import annotations

import numpy as np

# ----------------------------- QPSK -----------------------------
_QPSK = {(0, 0): 1 + 1j, (0, 1): -1 + 1j, (1, 1): -1 - 1j, (1, 0): 1 - 1j}


def qpsk_modulate(bits: list[int]) -> np.ndarray:
    """Map a bit list to QPSK symbols (pads one 0 if length is odd)."""
    bits = [int(b) for b in bits]
    if len(bits) % 2 != 0:
        bits.append(0)
    syms = [_QPSK[(bits[k], bits[k + 1])] / np.sqrt(2) for k in range(0, len(bits), 2)]
    return np.array(syms, dtype=complex)


def qpsk_demodulate(symbols: np.ndarray) -> list[int]:
    """Minimum-distance QPSK demap (independent I/Q sign decisions)."""
    bits: list[int] = []
    for s in symbols:
        bits.append(0 if s.imag >= 0 else 1)  # first bit from Q sign
        bits.append(0 if s.real >= 0 else 1)  # second bit from I sign
    return bits


# ----------------------------- BPSK -----------------------------
def bpsk_modulate(bits: list[int]) -> np.ndarray:
    """Map bits to BPSK symbols: 0 -> +1, 1 -> -1 (unit power)."""
    return np.array([1.0 if int(b) == 0 else -1.0 for b in bits], dtype=complex)


def bpsk_demodulate(symbols: np.ndarray) -> list[int]:
    return [0 if s.real >= 0 else 1 for s in symbols]


# ----------------------------- 16-QAM -----------------------------
_QAM_LEVELS = [-3, -1, 1, 3]
_BITS_TO_LEVEL = {(0, 0): -3, (0, 1): -1, (1, 1): 1, (1, 0): 3}  # Gray-coded
_LEVEL_TO_BITS = {v: k for k, v in _BITS_TO_LEVEL.items()}
_QAM_NORM = np.sqrt(10.0)  # average power of {-3,-1,1,3}^2 over I&Q is 10


def qam16_modulate(bits: list[int]) -> np.ndarray:
    """Gray-coded 16-QAM, 4 bits/symbol, normalized to unit average power."""
    bits = [int(b) for b in bits]
    while len(bits) % 4 != 0:
        bits.append(0)
    syms = []
    for k in range(0, len(bits), 4):
        i = _BITS_TO_LEVEL[(bits[k], bits[k + 1])]
        q = _BITS_TO_LEVEL[(bits[k + 2], bits[k + 3])]
        syms.append((i + 1j * q) / _QAM_NORM)
    return np.array(syms, dtype=complex)


def qam16_demodulate(symbols: np.ndarray) -> list[int]:
    bits: list[int] = []
    for s in symbols:
        i_val = s.real * _QAM_NORM
        q_val = s.imag * _QAM_NORM
        li = min(_QAM_LEVELS, key=lambda x: abs(x - i_val))
        lq = min(_QAM_LEVELS, key=lambda x: abs(x - q_val))
        bits += list(_LEVEL_TO_BITS[li]) + list(_LEVEL_TO_BITS[lq])
    return bits


# ----------------------------- Dispatcher -----------------------------
_BPS = {"bpsk": 1, "qpsk": 2, "16qam": 4, "qam16": 4}


def bits_per_symbol(scheme: str) -> int:
    return _BPS[scheme.lower()]


def modulate(bits: list[int], scheme: str = "qpsk") -> np.ndarray:
    s = scheme.lower()
    if s == "bpsk":
        return bpsk_modulate(bits)
    if s in ("16qam", "qam16"):
        return qam16_modulate(bits)
    return qpsk_modulate(bits)


def demodulate(symbols: np.ndarray, scheme: str = "qpsk") -> list[int]:
    s = scheme.lower()
    if s == "bpsk":
        return bpsk_demodulate(symbols)
    if s in ("16qam", "qam16"):
        return qam16_demodulate(symbols)
    return qpsk_demodulate(symbols)
