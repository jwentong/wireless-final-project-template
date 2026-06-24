"""AWGN and Rayleigh channel models."""

from __future__ import annotations

import numpy as np


def _noise_sigma(snr_db: float, signal_power: float = 1.0) -> float:
    snr_linear = 10 ** (snr_db / 10.0)
    noise_power = signal_power / snr_linear
    return float(np.sqrt(noise_power / 2.0))


def awgn(
    symbols: np.ndarray,
    snr_db: float = 12.0,
    seed: int = 2026,
) -> np.ndarray:
    """Add complex AWGN; SNR = mean(|x|^2) / mean(|n|^2)."""
    x = np.asarray(symbols, dtype=complex)
    power = float(np.mean(np.abs(x) ** 2)) if len(x) else 1.0
    sigma = _noise_sigma(snr_db, power)
    rng = np.random.default_rng(seed)
    noise = sigma * (rng.standard_normal(len(x)) + 1j * rng.standard_normal(len(x)))
    return x + noise


def rayleigh(
    symbols: np.ndarray,
    snr_db: float = 12.0,
    seed: int = 2026,
) -> tuple[np.ndarray, np.ndarray]:
    """Flat Rayleigh fading with ideal ZF equalization at receiver side."""
    x = np.asarray(symbols, dtype=complex)
    power = float(np.mean(np.abs(x) ** 2)) if len(x) else 1.0
    sigma = _noise_sigma(snr_db, power)
    rng = np.random.default_rng(seed)
    h = (
        rng.standard_normal(len(x)) + 1j * rng.standard_normal(len(x))
    ) / np.sqrt(2.0)
    noise = sigma * (rng.standard_normal(len(x)) + 1j * rng.standard_normal(len(x)))
    y = h * x + noise
    # Ideal equalization applied here for baseband simulation convenience
    h_safe = np.where(np.abs(h) < 1e-6, 1e-6 + 0j, h)
    return y / h_safe, h
