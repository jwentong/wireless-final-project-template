"""QPSK 调制/解调模块：Gray 编码映射，单位平均功率。
00 -> (1+j)/sqrt2   01 -> (-1+j)/sqrt2   11 -> (-1-j)/sqrt2   10 -> (1-j)/sqrt2
"""
from __future__ import annotations
from typing import Iterable
import numpy as np

_SQRT2 = np.sqrt(2)
_MAPPING = {
    (0, 0): (1 + 1j) / _SQRT2,
    (0, 1): (-1 + 1j) / _SQRT2,
    (1, 1): (-1 - 1j) / _SQRT2,
    (1, 0): (1 - 1j) / _SQRT2,
}
_KEYS = list(_MAPPING.keys())
_VALS = np.array([_MAPPING[k] for k in _KEYS])


def qpsk_modulate(bits: Iterable[int]) -> np.ndarray:
    bit_list = [int(b) for b in bits]
    if len(bit_list) % 2 != 0:
        bit_list.append(0)
    symbols = []
    for i in range(0, len(bit_list), 2):
        symbols.append(_MAPPING[(bit_list[i], bit_list[i + 1])])
    return np.array(symbols, dtype=complex)


def qpsk_demodulate(symbols: Iterable[complex]):
    symbols = np.asarray(list(symbols), dtype=complex)
    bits = []
    for s in symbols:
        idx = int(np.argmin(np.abs(_VALS - s)))
        bits.extend(_KEYS[idx])
    return bits


modulate_qpsk = qpsk_modulate
demodulate_qpsk = qpsk_demodulate
qpsk_mapper = qpsk_modulate
qpsk_demapper = qpsk_demodulate
modulate = qpsk_modulate
demodulate = qpsk_demodulate
