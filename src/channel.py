"""Channel models and simple equalization helpers."""

from __future__ import annotations

import numpy as np


def awgn(symbols: np.ndarray | list[complex], snr_db: float, seed: int | None = None) -> np.ndarray:
    """Add complex AWGN using SNR = signal power / complex noise power."""
    tx = np.asarray(symbols, dtype=complex)
    if tx.size == 0:
        return tx.copy()

    rng = np.random.default_rng(seed)
    signal_power = float(np.mean(np.abs(tx) ** 2))
    noise_power = signal_power / (10.0 ** (float(snr_db) / 10.0))
    sigma = np.sqrt(noise_power / 2.0)
    noise = sigma * (rng.normal(size=tx.shape) + 1j * rng.normal(size=tx.shape))
    return tx + noise


def rayleigh_fading_channel(
    symbols: np.ndarray | list[complex],
    snr_db: float,
    seed: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply flat Rayleigh fading and complex AWGN.

    The fading coefficient is generated per QPSK symbol as
    ``h = (randn + 1j * randn) / sqrt(2)``. The returned ``h`` is intended for
    the known-channel simulation equalizer used by the Level 3 extension.
    """
    tx = np.asarray(symbols, dtype=complex)
    if tx.size == 0:
        return tx.copy(), tx.copy()

    rng = np.random.default_rng(seed)
    h = (rng.normal(size=tx.shape) + 1j * rng.normal(size=tx.shape)) / np.sqrt(2.0)
    faded = h * tx
    signal_power = float(np.mean(np.abs(faded) ** 2))
    noise_power = signal_power / (10.0 ** (float(snr_db) / 10.0))
    sigma = np.sqrt(noise_power / 2.0)
    noise = sigma * (rng.normal(size=tx.shape) + 1j * rng.normal(size=tx.shape))
    return faded + noise, h


def one_tap_equalize(
    received_symbols: np.ndarray | list[complex],
    fading_coefficients: np.ndarray | list[complex],
    epsilon: float = 1e-12,
) -> np.ndarray:
    """Known-channel one-tap equalization for flat Rayleigh fading."""
    rx = np.asarray(received_symbols, dtype=complex)
    h = np.asarray(fading_coefficients, dtype=complex)
    if rx.shape != h.shape:
        raise ValueError("received symbols and fading coefficients must have the same shape")
    safe_h = np.where(np.abs(h) < epsilon, epsilon + 0j, h)
    return rx / safe_h


def add_prefix(symbols: np.ndarray | list[complex], offset_symbols: int, seed: int | None = None) -> np.ndarray:
    """Insert a deterministic complex-noise prefix before valid symbols."""
    if offset_symbols < 0:
        raise ValueError("offset_symbols must be non-negative")
    tx = np.asarray(symbols, dtype=complex)
    rng = np.random.default_rng(seed)
    prefix = (rng.normal(size=offset_symbols) + 1j * rng.normal(size=offset_symbols)) / np.sqrt(2.0)
    return np.concatenate([prefix, tx])


awgn_channel = awgn
add_awgn = awgn
add_noise = awgn
rayleigh = rayleigh_fading_channel
rayleigh_channel = rayleigh_fading_channel
