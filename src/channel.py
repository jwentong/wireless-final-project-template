import numpy as np


def awgn(symbols: list[complex], snr_db: float, seed: int) -> list[complex]:
    symbols_arr = np.array(symbols, dtype=complex)
    signal_power = np.mean(np.abs(symbols_arr) ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear
    noise_std = np.sqrt(noise_power / 2)
    rng = np.random.RandomState(seed)
    noise = noise_std * (rng.randn(len(symbols)) + 1j * rng.randn(len(symbols)))
    return (symbols_arr + noise).tolist()


def rayleigh_fading(symbols: list[complex], snr_db: float, seed: int) -> list[complex]:
    symbols_arr = np.array(symbols, dtype=complex)
    rng = np.random.RandomState(seed)
    h = (rng.randn(len(symbols_arr)) + 1j * rng.randn(len(symbols_arr))) / np.sqrt(2)
    faded = symbols_arr * h
    signal_power = np.mean(np.abs(faded) ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear
    noise_std = np.sqrt(noise_power / 2)
    noise = noise_std * (rng.randn(len(symbols_arr)) + 1j * rng.randn(len(symbols_arr)))
    rx = faded + noise
    rx_equalized = rx / h
    return rx_equalized.tolist()


CHANNEL_MODELS = {
    "awgn": awgn,
    "rayleigh": rayleigh_fading,
}


def get_channel(name: str):
    return CHANNEL_MODELS.get(name, awgn)


awgn_channel = awgn
add_awgn = awgn
