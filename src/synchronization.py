"""同步模块：滑动归一化相关，检测已知 preamble 的起始符号位置。"""
from __future__ import annotations
from typing import Iterable
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def synchronize(received_symbols: Iterable[complex], preamble: Iterable[complex]):
    received = np.asarray(list(received_symbols), dtype=complex)
    preamble = np.asarray(list(preamble), dtype=complex)
    m = len(preamble)
    n = len(received)
    if m == 0 or n < m:
        return 0
    windows = sliding_window_view(received, m)
    corr = np.abs(windows @ np.conj(preamble))
    norms = np.sqrt(np.sum(np.abs(windows) ** 2, axis=1) * np.sum(np.abs(preamble) ** 2)) + 1e-12
    scores = corr / norms
    return int(np.argmax(scores))


detect_frame_start = synchronize
find_preamble = synchronize
sync = synchronize
