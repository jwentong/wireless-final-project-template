import numpy as np


def awgn(symbols, snr_db=12, seed=2026):
    """Add complex AWGN using SNR = average symbol power / average noise power."""
    x = np.asarray(symbols, dtype=complex)
    if x.size == 0:
        return x.copy()
    rng = np.random.default_rng(int(seed))
    signal_power = float(np.mean(np.abs(x) ** 2))
    snr_linear = 10.0 ** (float(snr_db) / 10.0)
    noise_power = signal_power / snr_linear if snr_linear > 0 else signal_power
    sigma = np.sqrt(noise_power / 2.0)
    noise = sigma * (rng.normal(size=x.shape) + 1j * rng.normal(size=x.shape))
    return x + noise


awgn_channel = awgn
add_awgn = awgn
add_noise = awgn

