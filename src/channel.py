import numpy as np

def awgn(symbols, snr_db=12, seed=None):
    if seed is not None:
        np.random.seed(seed)
    symbols = np.array(symbols, dtype=complex)
    signal_power = np.mean(np.abs(symbols) ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear
    noise_std = np.sqrt(noise_power / 2)
    noise = noise_std * (np.random.randn(len(symbols)) + 1j * np.random.randn(len(symbols)))
    return symbols + noise

def awgn_channel(symbols, snr_db=12, seed=None):
    return awgn(symbols, snr_db, seed)

def add_awgn(symbols, snr_db=12, seed=None):
    return awgn(symbols, snr_db, seed)

def add_noise(symbols, snr_db=12, seed=None):
    return awgn(symbols, snr_db, seed)

def rayleigh(symbols, snr_db=12, seed=None):
    if seed is not None:
        np.random.seed(seed)
    symbols = np.array(symbols, dtype=complex)
    h = (np.random.randn(len(symbols)) + 1j * np.random.randn(len(symbols))) / np.sqrt(2)
    faded = symbols * h
    signal_power = np.mean(np.abs(faded) ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear
    noise_std = np.sqrt(noise_power / 2)
    noise = noise_std * (np.random.randn(len(symbols)) + 1j * np.random.randn(len(symbols)))
    return faded + noise

def rician(symbols, snr_db=12, K=10, seed=None):
    if seed is not None:
        np.random.seed(seed)
    symbols = np.array(symbols, dtype=complex)
    los = np.sqrt(K / (K + 1))
    nlos = np.sqrt(1 / (K + 1))
    h = los + nlos * (np.random.randn(len(symbols)) + 1j * np.random.randn(len(symbols))) / np.sqrt(2)
    faded = symbols * h
    signal_power = np.mean(np.abs(faded) ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear
    noise_std = np.sqrt(noise_power / 2)
    noise = noise_std * (np.random.randn(len(symbols)) + 1j * np.random.randn(len(symbols)))
    return faded + noise
