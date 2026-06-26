"""Wireless channel models."""

from __future__ import annotations

from typing import Iterable

import numpy as np


def awgn(symbols: Iterable[complex], snr_db: float = 12.0, seed: int | None = None) -> np.ndarray:
    """Add complex AWGN using symbol-power SNR in dB."""
    x = np.asarray(list(symbols), dtype=np.complex128)
    if x.size == 0:
        return x.copy()
    snr_linear = 10.0 ** (float(snr_db) / 10.0)
    signal_power = float(np.mean(np.abs(x) ** 2))
    noise_power = signal_power / snr_linear
    rng = np.random.default_rng(seed)
    noise = np.sqrt(noise_power / 2.0) * (
        rng.normal(size=x.size) + 1j * rng.normal(size=x.size)
    )
    return x + noise


awgn_channel = awgn
add_awgn = awgn
add_noise = awgn

