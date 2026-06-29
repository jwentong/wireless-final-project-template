"""Wireless channel models: AWGN (baseline) plus Rayleigh / Rician fading.

SNR is defined as average symbol power over average complex-noise power, in dB,
matching the PRD. For QPSK with unit-power symbols, noise power Pn = Ps / 10^(SNR/10),
split equally between the real and imaginary parts. All randomness is seeded for
reproducibility. Fading models additionally return the complex channel gain ``h``
so the receiver can equalize.
"""
from __future__ import annotations

import numpy as np


def _complex_noise(shape, power: float, rng: np.random.Generator) -> np.ndarray:
    return np.sqrt(power / 2) * (rng.standard_normal(shape) + 1j * rng.standard_normal(shape))


def awgn(symbols: np.ndarray, snr_db: float = 12, seed: int = 2026) -> np.ndarray:
    """Add complex AWGN at the given SNR (dB). Reproducible for a fixed seed."""
    symbols = np.asarray(symbols, dtype=complex)
    ps = float(np.mean(np.abs(symbols) ** 2))
    pn = ps / (10 ** (snr_db / 10))
    rng = np.random.default_rng(seed)
    return symbols + _complex_noise(symbols.shape, pn, rng)


def rayleigh(symbols: np.ndarray, snr_db: float = 12, seed: int = 2026,
             block_fading: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Rayleigh fading + AWGN. Returns (received, channel_gain h)."""
    symbols = np.asarray(symbols, dtype=complex)
    rng = np.random.default_rng(seed)
    if block_fading:
        g = (rng.standard_normal() + 1j * rng.standard_normal()) / np.sqrt(2)
        h = np.full(symbols.shape, g, dtype=complex)
    else:
        h = (rng.standard_normal(symbols.shape) + 1j * rng.standard_normal(symbols.shape)) / np.sqrt(2)
    ps = float(np.mean(np.abs(symbols) ** 2))
    pn = ps / (10 ** (snr_db / 10))
    return h * symbols + _complex_noise(symbols.shape, pn, rng), h


def rician(symbols: np.ndarray, snr_db: float = 12, seed: int = 2026,
           k_factor: float = 4.0, block_fading: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Rician fading (LOS + scattered) + AWGN. Returns (received, channel_gain h)."""
    symbols = np.asarray(symbols, dtype=complex)
    rng = np.random.default_rng(seed)
    los = np.sqrt(k_factor / (k_factor + 1))
    nlos = np.sqrt(1 / (k_factor + 1))
    if block_fading:
        g = los + nlos * (rng.standard_normal() + 1j * rng.standard_normal()) / np.sqrt(2)
        h = np.full(symbols.shape, g, dtype=complex)
    else:
        h = los + nlos * (rng.standard_normal(symbols.shape)
                          + 1j * rng.standard_normal(symbols.shape)) / np.sqrt(2)
    ps = float(np.mean(np.abs(symbols) ** 2))
    pn = ps / (10 ** (snr_db / 10))
    return h * symbols + _complex_noise(symbols.shape, pn, rng), h
