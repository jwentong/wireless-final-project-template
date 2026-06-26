"""Preamble-based frame synchronization."""

from __future__ import annotations

from typing import Iterable

import numpy as np

from .framing import PREAMBLE_BITS
from .modulation import qpsk_modulate


def synchronize(received: Iterable[complex], preamble: Iterable[complex] | None = None) -> dict:
    """Detect the first preamble symbol by matched-filter correlation."""
    rx = np.asarray(list(received), dtype=np.complex128)
    pre = np.asarray(list(preamble), dtype=np.complex128) if preamble is not None else qpsk_modulate(PREAMBLE_BITS)
    if pre.size == 0 or rx.size < pre.size:
        return {"start_index": 0, "metric": np.asarray([], dtype=float), "peak_value": 0.0}
    # numpy.correlate already conjugates the second complex argument.
    metric = np.abs(np.correlate(rx, pre, mode="valid"))
    start = int(np.argmax(metric))
    return {"start_index": start, "metric": metric, "peak_value": float(metric[start])}


def detect_frame_start(received: Iterable[complex], preamble: Iterable[complex] | None = None) -> int:
    return int(synchronize(received, preamble=preamble)["start_index"])


find_preamble = detect_frame_start
sync = synchronize
