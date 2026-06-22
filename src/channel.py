from __future__ import annotations

import numpy as np


def awgn(symbols, snr_db: float = 12.0, seed: int = 2026) -> np.ndarray:
    arr = np.asarray(symbols, dtype=complex)
    if arr.size == 0:
        return arr.copy()
    signal_power = float(np.mean(np.abs(arr) ** 2))
    if signal_power <= 0.0:
        signal_power = 1.0
    snr_linear = 10.0 ** (float(snr_db) / 10.0)
    noise_power = signal_power / snr_linear
    rng = np.random.default_rng(seed)
    sigma = np.sqrt(noise_power / 2.0)
    noise = sigma * (rng.normal(size=arr.shape) + 1j * rng.normal(size=arr.shape))
    return arr + noise


awgn_channel = awgn
add_awgn = awgn
add_noise = awgn


def rayleigh(symbols, snr_db: float = 12.0, seed: int = 2026, return_h: bool = False):
    """Apply one complex flat Rayleigh fading coefficient to a frame plus AWGN."""
    arr = np.asarray(symbols, dtype=complex)
    if arr.size == 0:
        empty = arr.copy()
        return (empty, 1.0 + 0.0j) if return_h else empty

    rng = np.random.default_rng(seed)
    h = (rng.normal() + 1j * rng.normal()) / np.sqrt(2.0)
    faded = h * arr
    signal_power = float(np.mean(np.abs(faded) ** 2))
    if signal_power <= 0.0:
        signal_power = 1.0
    snr_linear = 10.0 ** (float(snr_db) / 10.0)
    noise_power = signal_power / snr_linear
    sigma = np.sqrt(noise_power / 2.0)
    noise = sigma * (rng.normal(size=arr.shape) + 1j * rng.normal(size=arr.shape))
    out = faded + noise
    return (out, h) if return_h else out


rayleigh_channel = rayleigh
flat_rayleigh = rayleigh