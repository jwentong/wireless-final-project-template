from __future__ import annotations

import numpy as np

from .framing import PREAMBLE_BITS
from .modulation import qpsk_modulate


PREAMBLE_SYMBOLS = qpsk_modulate(PREAMBLE_BITS)


def synchronize(received_symbols, preamble=None):
    received = np.asarray(received_symbols, dtype=complex)
    pre = PREAMBLE_SYMBOLS if preamble is None else np.asarray(preamble, dtype=complex)
    if received.size < pre.size or pre.size == 0:
        return {"start_index": 0, "sync_start_index": 0, "correlation": [], "peak": 0.0}

    metric = np.empty(received.size - pre.size + 1, dtype=float)
    conj_pre = np.conjugate(pre)
    for i in range(metric.size):
        metric[i] = abs(np.sum(received[i : i + pre.size] * conj_pre))
    start = int(np.argmax(metric))
    peak = float(metric[start])
    return {
        "start_index": start,
        "sync_start_index": start,
        "correlation": metric.tolist(),
        "peak": peak,
    }


detect_frame_start = synchronize
find_preamble = synchronize
sync = synchronize
