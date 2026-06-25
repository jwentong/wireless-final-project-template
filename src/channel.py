"""AWGN channel model."""

import numpy as np


def awgn(symbols: np.ndarray, snr_db: float = 12.0, seed: int = 2026) -> np.ndarray:
    """Add AWGN noise to complex symbols.

    Noise power is computed assuming unit signal power.
    Uses an independent RNG with fixed seed for reproducibility.

    Args:
        symbols: Complex-valued numpy array (unit average power).
        snr_db: Signal-to-noise ratio in dB.
        seed: Random seed for reproducible noise.

    Returns:
        Noisy symbols (same shape as input).
    """
    sym = np.asarray(symbols, dtype=complex)
    snr_linear = 10.0 ** (snr_db / 10.0)
    noise_power = 1.0 / snr_linear  # signal power = 1

    rng = np.random.default_rng(seed)
    noise = np.sqrt(noise_power / 2.0) * (
        rng.standard_normal(sym.shape) + 1j * rng.standard_normal(sym.shape)
    )

    return sym + noise


# Aliases for test discovery
awgn_channel = awgn
add_awgn = awgn
add_noise = awgn
