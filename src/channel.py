import math
import random


def awgn(symbols, snr_db: float, seed: int = 2026) -> list[complex]:
    rng = random.Random(seed + 0xBEEF)
    snr_linear = 10 ** (float(snr_db) / 10.0)
    noise_power = 1.0 / snr_linear
    sigma = math.sqrt(noise_power / 2.0)
    return [complex(s) + complex(rng.gauss(0.0, sigma), rng.gauss(0.0, sigma)) for s in symbols]


def add_awgn_with_offset(
    symbols: list[complex], snr_db: float, seed: int, max_offset: int = 128
) -> tuple[list[complex], int]:
    rng = random.Random(seed + 0xA0F0)
    offset = rng.randint(0, max_offset)
    snr_linear = 10 ** (snr_db / 10.0)
    noise_power = 1.0 / snr_linear
    sigma = math.sqrt(noise_power / 2.0)

    prefix = [complex(rng.gauss(0.0, sigma), rng.gauss(0.0, sigma)) for _ in range(offset)]
    noisy = []
    for symbol in symbols:
        noise = complex(rng.gauss(0.0, sigma), rng.gauss(0.0, sigma))
        noisy.append(symbol + noise)
    return prefix + noisy, offset


def rayleigh_channel_with_offset(
    symbols: list[complex], snr_db: float, seed: int, max_offset: int = 128
) -> tuple[list[complex], int, complex]:
    rng = random.Random(seed + 0xC0DE)
    offset = rng.randint(0, max_offset)
    snr_linear = 10 ** (snr_db / 10.0)
    noise_power = 1.0 / snr_linear
    sigma = math.sqrt(noise_power / 2.0)
    h = complex(rng.gauss(0.0, 1.0 / math.sqrt(2.0)), rng.gauss(0.0, 1.0 / math.sqrt(2.0)))
    if abs(h) < 0.15:
        h = complex(0.15, 0.0)

    prefix = [complex(rng.gauss(0.0, sigma), rng.gauss(0.0, sigma)) for _ in range(offset)]
    faded = []
    for symbol in symbols:
        noise = complex(rng.gauss(0.0, sigma), rng.gauss(0.0, sigma))
        faded.append(h * symbol + noise)
    return prefix + faded, offset, h


def estimate_flat_fading(received_preamble: list[complex], known_preamble: list[complex]) -> complex:
    denom = sum(abs(x) ** 2 for x in known_preamble) or 1.0
    h_hat = sum(received_preamble[i] * known_preamble[i].conjugate() for i in range(len(known_preamble))) / denom
    return h_hat if abs(h_hat) > 1e-9 else complex(1.0, 0.0)


def zf_equalize(symbols: list[complex], channel_gain: complex) -> list[complex]:
    if abs(channel_gain) < 1e-9:
        return list(symbols)
    return [complex(symbol) / channel_gain for symbol in symbols]


awgn_channel = awgn
add_awgn = awgn
add_noise = awgn
rayleigh = rayleigh_channel_with_offset
zero_forcing_equalize = zf_equalize
