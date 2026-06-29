"""Frame synchronization by normalized cross-correlation with the preamble.

The receiver slides the known preamble over the received symbol stream and picks
the lag with the highest normalized correlation magnitude as the frame start.
Works with any preamble (the function does not assume a specific sequence), and
detects arbitrary leading offsets (0..128 symbols per PRD).
"""
from __future__ import annotations

import numpy as np


def correlate(received: np.ndarray, preamble: np.ndarray) -> np.ndarray:
    """Return the normalized cross-correlation curve over all valid lags."""
    received = np.asarray(received, dtype=complex)
    preamble = np.asarray(preamble, dtype=complex)
    n = len(received) - len(preamble) + 1
    if n <= 0:
        return np.zeros(0)
    pnorm = np.linalg.norm(preamble)
    corr = np.zeros(n)
    for d in range(n):
        window = received[d:d + len(preamble)]
        wnorm = np.linalg.norm(window)
        if wnorm > 0:
            corr[d] = np.abs(np.vdot(preamble, window)) / (pnorm * wnorm)
    return corr


def synchronize(received: np.ndarray, preamble: np.ndarray) -> int:
    """Return the estimated frame-start index (argmax of the correlation)."""
    corr = correlate(received, preamble)
    if corr.size == 0:
        return 0
    return int(np.argmax(corr))
