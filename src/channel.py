import numpy as np


def awgn(symbols, snr_db=12, seed=2026):
    x = np.asarray(symbols, dtype=complex)
    if x.size == 0:
        return x.copy()
    rng = np.random.default_rng(seed)
    signal_power = float(np.mean(np.abs(x) ** 2))
    snr_linear = 10 ** (float(snr_db) / 10.0)
    noise_power = signal_power / snr_linear
    sigma = np.sqrt(noise_power / 2.0)
    noise = sigma * (rng.normal(size=x.shape) + 1j * rng.normal(size=x.shape))
    return x + noise


def rayleigh_flat(symbols, snr_db=18, seed=2026):
    x = np.asarray(symbols, dtype=complex)
    if x.size == 0:
        return x.copy()
    rng = np.random.default_rng(seed)
    h = (rng.normal() + 1j * rng.normal()) / np.sqrt(2.0)
    faded = h * x
    signal_power = float(np.mean(np.abs(faded) ** 2))
    snr_linear = 10 ** (float(snr_db) / 10.0)
    noise_power = signal_power / snr_linear
    sigma = np.sqrt(noise_power / 2.0)
    noise = sigma * (rng.normal(size=x.shape) + 1j * rng.normal(size=x.shape))
    return faded + noise


def estimate_flat_channel(received_preamble_symbols, known_preamble_symbols):
    y = np.asarray(received_preamble_symbols, dtype=complex)
    x = np.asarray(known_preamble_symbols, dtype=complex)
    n = min(len(y), len(x))
    if n == 0:
        return 1.0 + 0.0j
    y = y[:n]
    x = x[:n]
    denom = np.sum(np.abs(x) ** 2)
    if abs(denom) < 1e-12:
        return 1.0 + 0.0j
    h_hat = np.sum(y * np.conjugate(x)) / denom
    if abs(h_hat) < 1e-12:
        return 1.0 + 0.0j
    return complex(h_hat)


def equalize_flat_channel(received_symbols, h_hat):
    y = np.asarray(received_symbols, dtype=complex)
    h = complex(h_hat)
    if abs(h) < 1e-12:
        return y.copy()
    return y / h


awgn_channel = awgn
add_awgn = awgn
add_noise = awgn
rayleigh_channel = rayleigh_flat
