"""Channel module: AWGN and Rayleigh fading channels.

AWGN (Additive White Gaussian Noise):
  - Adds complex Gaussian noise to input symbols
  - SNR defined as: signal_power / noise_power (in linear, converted from dB)
  - Reproducible output with fixed seed

Rayleigh fading:
  - Multiplies signal by complex Rayleigh fading coefficient
  - Then adds AWGN
  - Flat fading (single tap), suitable for narrowband simulation
"""

import numpy as np


def awgn(symbols, snr_db: float = 12.0, seed: int = 2026):
    """Add AWGN to input symbols.

    Args:
        symbols: Array-like of complex symbols.
        snr_db: Signal-to-noise ratio in dB (SNR = signal power / noise power).
        seed: Random seed for reproducibility.

    Returns:
        Noisy symbols as a list of complex values.
    """
    syms = np.asarray(symbols, dtype=complex)
    rng = np.random.default_rng(seed)

    # Signal power
    signal_power = np.mean(np.abs(syms) ** 2)

    # SNR linear
    snr_linear = 10 ** (snr_db / 10.0)
    noise_power = signal_power / snr_linear

    # Generate complex noise (power split equally between I and Q)
    noise_std = np.sqrt(noise_power / 2.0)
    noise = rng.normal(0, noise_std, size=len(syms)) + \
            1j * rng.normal(0, noise_std, size=len(syms))

    noisy = syms + noise
    return [complex(x) for x in noisy]


def rayleigh(symbols, snr_db: float = 12.0, seed: int = 2026):
    """Apply Rayleigh flat fading + AWGN to input symbols.

    The channel coefficient h ~ CN(0, 1) (complex Gaussian, zero mean, unit variance).
    No CSI (Channel State Information) is assumed at receiver for simplicity.

    Args:
        symbols: Array-like of complex symbols.
        snr_db: Signal-to-noise ratio in dB.
        seed: Random seed for reproducibility.

    Returns:
        Faded noisy symbols as a list of complex values, and the channel coefficients.
    """
    syms = np.asarray(symbols, dtype=complex)
    rng = np.random.default_rng(seed)

    # Generate Rayleigh fading coefficients: h ~ CN(0, 1/√2) + j*CN(0, 1/√2)
    # |h| follows Rayleigh distribution with E[|h|^2] = 1
    h = (rng.normal(0, 1/np.sqrt(2), size=len(syms)) +
         1j * rng.normal(0, 1/np.sqrt(2), size=len(syms)))

    # Apply fading
    faded = syms * h

    # Signal power after fading
    signal_power = np.mean(np.abs(faded) ** 2)

    # Add AWGN
    snr_linear = 10 ** (snr_db / 10.0)
    noise_power = signal_power / snr_linear
    noise_std = np.sqrt(noise_power / 2.0)

    # Use a different seed offset for noise to decorrelate from fading
    noise_rng = np.random.default_rng(seed + 100000)
    noise = noise_rng.normal(0, noise_std, size=len(syms)) + \
            1j * noise_rng.normal(0, noise_std, size=len(syms))

    noisy = faded + noise
    return [complex(x) for x in noisy], [complex(x) for x in h]


# Alternative function names for test discovery
def awgn_channel(symbols, snr_db: float = 12.0, seed: int = 2026):
    """Alias for awgn."""
    return awgn(symbols, snr_db, seed)


def add_awgn(symbols, snr_db: float = 12.0, seed: int = 2026):
    """Alias for awgn."""
    return awgn(symbols, snr_db, seed)


def add_noise(symbols, snr_db: float = 12.0, seed: int = 2026):
    """Alias for awgn."""
    return awgn(symbols, snr_db, seed)
