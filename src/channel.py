from __future__ import annotations

import numpy as np


def awgn(symbols, snr_db: float = 12.0, seed: int = 2026) -> np.ndarray:
    symbols = np.asarray(symbols, dtype=complex)
    if symbols.size == 0:
        return symbols.copy()
    rng = np.random.default_rng(seed)
    signal_power = float(np.mean(np.abs(symbols) ** 2))
    snr_linear = 10 ** (float(snr_db) / 10)
    noise_power = signal_power / snr_linear
    sigma = np.sqrt(noise_power / 2)
    noise = rng.normal(0, sigma, size=symbols.shape) + 1j * rng.normal(0, sigma, size=symbols.shape)
    return symbols + noise


def rayleigh_flat(symbols, snr_db: float = 12.0, seed: int = 2026, return_gain: bool = False):
    """Flat Rayleigh fading channel with one complex gain for the whole frame."""
    symbols = np.asarray(symbols, dtype=complex)
    if symbols.size == 0:
        gain = 1 + 0j
        return (symbols.copy(), gain) if return_gain else symbols.copy()
    rng = np.random.default_rng(seed)
    gain = (rng.normal() + 1j * rng.normal()) / np.sqrt(2)
    faded = symbols * gain
    signal_power = float(np.mean(np.abs(faded) ** 2))
    snr_linear = 10 ** (float(snr_db) / 10)
    noise_power = signal_power / snr_linear
    sigma = np.sqrt(noise_power / 2)
    noise = rng.normal(0, sigma, size=symbols.shape) + 1j * rng.normal(0, sigma, size=symbols.shape)
    received = faded + noise
    return (received, gain) if return_gain else received


def equalize_flat_rayleigh(symbols, gain: complex) -> np.ndarray:
    if abs(gain) < 1e-12:
        raise ValueError("Rayleigh gain is too close to zero for stable equalization")
    return np.asarray(symbols, dtype=complex) / gain


def rayleigh_mrc2(symbols, snr_db: float = 12.0, seed: int = 2026) -> tuple[np.ndarray, tuple[complex, complex]]:
    """Two-branch flat Rayleigh receive diversity with maximal-ratio combining."""
    values = np.asarray(symbols, dtype=complex)
    if values.size == 0:
        return values.copy(), (1 + 0j, 1 + 0j)
    rng = np.random.default_rng(seed)
    gains = tuple((rng.normal() + 1j * rng.normal()) / np.sqrt(2) for _ in range(2))
    snr_linear = 10 ** (float(snr_db) / 10)
    branches = []
    for gain in gains:
        faded = values * gain
        signal_power = float(np.mean(np.abs(faded) ** 2))
        noise_power = signal_power / snr_linear
        sigma = np.sqrt(noise_power / 2)
        noise = rng.normal(0, sigma, size=values.shape) + 1j * rng.normal(0, sigma, size=values.shape)
        branches.append(faded + noise)
    denominator = sum(abs(gain) ** 2 for gain in gains)
    if denominator < 1e-12:
        raise ValueError("MRC channel gains are too close to zero")
    combined = sum(np.conj(gain) * branch for gain, branch in zip(gains, branches)) / denominator
    return np.asarray(combined, dtype=complex), gains


awgn_channel = awgn
add_awgn = awgn
add_noise = awgn
rayleigh_channel = rayleigh_flat
