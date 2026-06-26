"""Preamble-correlation synchronization."""

from __future__ import annotations

import numpy as np

from .frame import PREAMBLE_BITS
from .modulation import qpsk_modulate


def preamble_symbols() -> np.ndarray:
    return qpsk_modulate(PREAMBLE_BITS)


def detect_frame_start(
    received_symbols: np.ndarray | list[complex],
    preamble: np.ndarray | list[complex] | None = None,
) -> dict[str, object]:
    """Find frame start by maximizing absolute preamble correlation."""
    rx = np.asarray(received_symbols, dtype=complex)
    ref = preamble_symbols() if preamble is None else np.asarray(preamble, dtype=complex)
    if ref.size == 0 or rx.size < ref.size:
        raise ValueError("received sequence must contain at least one preamble length")

    correlations = np.empty(rx.size - ref.size + 1, dtype=float)
    ref_energy = float(np.vdot(ref, ref).real)
    for index in range(correlations.size):
        window = rx[index : index + ref.size]
        correlations[index] = abs(np.vdot(ref, window)) / max(ref_energy, 1e-12)

    start = int(np.argmax(correlations))
    return {
        "start_index": start,
        "sync_start_index": start,
        "correlation": correlations,
        "peak_value": float(correlations[start]),
    }


synchronize = detect_frame_start
find_preamble = detect_frame_start
sync = detect_frame_start
