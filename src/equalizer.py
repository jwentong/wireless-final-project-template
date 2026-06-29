"""Channel equalization for fading channels (Level-3 module).

Given received symbols ``rx`` and the complex channel gain ``h``:
  * Zero-Forcing (ZF): divides out the channel, fully removing it but amplifying
    noise when |h| is small.
  * MMSE: trades off noise and residual interference using the SNR, outperforming
    ZF at low SNR.
"""
from __future__ import annotations

import numpy as np


def zf_equalize(rx: np.ndarray, h: np.ndarray) -> np.ndarray:
    """Zero-forcing equalizer: rx / h."""
    rx = np.asarray(rx, dtype=complex)
    h = np.asarray(h, dtype=complex)
    return rx / h


def mmse_equalize(rx: np.ndarray, h: np.ndarray, snr_db: float) -> np.ndarray:
    """MMSE equalizer: conj(h) * rx / (|h|^2 + 1/SNR)."""
    rx = np.asarray(rx, dtype=complex)
    h = np.asarray(h, dtype=complex)
    snr = 10 ** (snr_db / 10)
    return np.conj(h) * rx / (np.abs(h) ** 2 + 1.0 / snr)
