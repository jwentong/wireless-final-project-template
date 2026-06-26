from __future__ import annotations

import numpy as np


INV_SQRT2 = 1 / np.sqrt(2)
INV_SQRT10 = 1 / np.sqrt(10)
QPSK_MAP = {
    (0, 0): (1 + 1j) * INV_SQRT2,
    (0, 1): (-1 + 1j) * INV_SQRT2,
    (1, 1): (-1 - 1j) * INV_SQRT2,
    (1, 0): (1 - 1j) * INV_SQRT2,
}

_LEVEL_TO_BITS = {
    -3: [0, 0],
    -1: [0, 1],
    1: [1, 1],
    3: [1, 0],
}
_BITS_TO_LEVEL = {tuple(bits): level for level, bits in _LEVEL_TO_BITS.items()}


def bits_per_symbol(scheme: str) -> int:
    mode = scheme.lower()
    if mode == "bpsk":
        return 1
    if mode == "qpsk":
        return 2
    if mode == "16qam":
        return 4
    raise ValueError("supported modulation schemes: bpsk, qpsk, 16qam")


def select_adaptive_modulation(snr_db: float) -> str:
    if float(snr_db) < 6.0:
        return "bpsk"
    if float(snr_db) < 14.0:
        return "qpsk"
    return "16qam"


def _padded_bits(bits: list[int], group: int) -> list[int]:
    padded = [int(bit) for bit in bits]
    while len(padded) % group:
        padded.append(0)
    return padded


def qpsk_modulate(bits: list[int]) -> np.ndarray:
    padded = _padded_bits(bits, 2)
    symbols = [QPSK_MAP[(padded[i], padded[i + 1])] for i in range(0, len(padded), 2)]
    return np.array(symbols, dtype=complex)


def qpsk_demodulate(symbols) -> list[int]:
    bits: list[int] = []
    for symbol in np.asarray(symbols, dtype=complex):
        if symbol.real >= 0 and symbol.imag >= 0:
            bits.extend([0, 0])
        elif symbol.real < 0 and symbol.imag >= 0:
            bits.extend([0, 1])
        elif symbol.real < 0 and symbol.imag < 0:
            bits.extend([1, 1])
        else:
            bits.extend([1, 0])
    return bits


def bpsk_modulate(bits: list[int]) -> np.ndarray:
    return np.array([1 if int(bit) == 0 else -1 for bit in bits], dtype=complex)


def bpsk_demodulate(symbols) -> list[int]:
    return [0 if symbol.real >= 0 else 1 for symbol in np.asarray(symbols, dtype=complex)]


def qam16_modulate(bits: list[int]) -> np.ndarray:
    padded = _padded_bits(bits, 4)
    symbols: list[complex] = []
    for i in range(0, len(padded), 4):
        i_level = _BITS_TO_LEVEL[(padded[i], padded[i + 1])]
        q_level = _BITS_TO_LEVEL[(padded[i + 2], padded[i + 3])]
        symbols.append((i_level + 1j * q_level) * INV_SQRT10)
    return np.array(symbols, dtype=complex)


def _nearest_16qam_level(value: float) -> int:
    scaled = value / INV_SQRT10
    if scaled < -2:
        return -3
    if scaled < 0:
        return -1
    if scaled < 2:
        return 1
    return 3


def qam16_demodulate(symbols) -> list[int]:
    bits: list[int] = []
    for symbol in np.asarray(symbols, dtype=complex):
        bits.extend(_LEVEL_TO_BITS[_nearest_16qam_level(float(symbol.real))])
        bits.extend(_LEVEL_TO_BITS[_nearest_16qam_level(float(symbol.imag))])
    return bits


def modulate_bits(bits: list[int], scheme: str) -> np.ndarray:
    mode = scheme.lower()
    if mode == "bpsk":
        return bpsk_modulate(bits)
    if mode == "qpsk":
        return qpsk_modulate(bits)
    if mode == "16qam":
        return qam16_modulate(bits)
    raise ValueError("supported modulation schemes: bpsk, qpsk, 16qam")


def demodulate_symbols(symbols, scheme: str) -> list[int]:
    mode = scheme.lower()
    if mode == "bpsk":
        return bpsk_demodulate(symbols)
    if mode == "qpsk":
        return qpsk_demodulate(symbols)
    if mode == "16qam":
        return qam16_demodulate(symbols)
    raise ValueError("supported modulation schemes: bpsk, qpsk, 16qam")


modulate_qpsk = qpsk_modulate
qpsk_mapper = qpsk_modulate
modulate = qpsk_modulate
demodulate_qpsk = qpsk_demodulate
qpsk_demapper = qpsk_demodulate
demodulate = qpsk_demodulate
