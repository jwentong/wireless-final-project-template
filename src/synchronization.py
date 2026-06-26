"""Frame synchronization via preamble cross-correlation."""

from __future__ import annotations

import numpy as np

from src.modulation import qpsk_modulate
from src.utils import preamble_bits

MAX_PREAMBLE_OFFSET = 128


def _preamble_symbols() -> np.ndarray:
    return qpsk_modulate(preamble_bits())


def _normalized_correlation(rx: np.ndarray, pre: np.ndarray) -> np.ndarray:
    """Normalized magnitude correlation over valid start indices."""
    pre = np.asarray(pre, dtype=complex)
    rx = np.asarray(rx, dtype=complex)
    length = len(pre)
    if len(rx) < length:
        return np.array([])

    search_end = min(len(rx), MAX_PREAMBLE_OFFSET + length + 16)
    segment = rx[:search_end]
    windows = np.lib.stride_tricks.sliding_window_view(segment, length)
    num = np.abs(np.einsum("ij,j->i", windows, np.conj(pre)))
    den = np.linalg.norm(pre) * np.linalg.norm(windows, axis=1)
    return num / (den + 1e-12)


def detect_frame_start(
    rx_symbols: np.ndarray,
    preamble_symbols: np.ndarray | None = None,
) -> int:
    """Return detected frame start symbol index."""
    rx = np.asarray(rx_symbols, dtype=complex)
    pre = np.asarray(
        preamble_symbols if preamble_symbols is not None else _preamble_symbols(),
        dtype=complex,
    )
    corr = _normalized_correlation(rx, pre)
    if len(corr) == 0:
        return 0
    return int(np.argmax(corr))


def synchronize(
    rx_symbols: np.ndarray,
    preamble: np.ndarray | None = None,
) -> dict:
    """Detect frame start and return alignment metadata."""
    rx = np.asarray(rx_symbols, dtype=complex)
    pre = np.asarray(preamble if preamble is not None else _preamble_symbols(), dtype=complex)
    corr = _normalized_correlation(rx, pre)
    start = int(np.argmax(corr)) if len(corr) else 0
    aligned = rx[start:]
    return {
        "start_index": start,
        "sync_start_index": start,
        "index": start,
        "correlation": corr,
        "aligned_symbols": aligned,
    }
