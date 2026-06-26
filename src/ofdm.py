from __future__ import annotations

import numpy as np


def ofdm_modulate(symbols, fft_size: int = 64, cp_len: int = 16) -> tuple[np.ndarray, int]:
    values = np.asarray(symbols, dtype=complex)
    if fft_size <= 0 or cp_len < 0 or cp_len >= fft_size:
        raise ValueError("OFDM requires fft_size > 0 and 0 <= cp_len < fft_size")
    if values.size == 0:
        return np.array([], dtype=complex), 0
    padded_count = int(np.ceil(values.size / fft_size) * fft_size)
    padded = np.zeros(padded_count, dtype=complex)
    padded[: values.size] = values
    blocks = padded.reshape(-1, fft_size)
    time_blocks = np.fft.ifft(blocks, axis=1) * np.sqrt(fft_size)
    with_cp = np.concatenate([time_blocks[:, -cp_len:], time_blocks], axis=1) if cp_len else time_blocks
    return with_cp.reshape(-1), padded_count


def ofdm_demodulate(samples, symbol_count: int, fft_size: int = 64, cp_len: int = 16) -> np.ndarray:
    values = np.asarray(samples, dtype=complex)
    if fft_size <= 0 or cp_len < 0 or cp_len >= fft_size:
        raise ValueError("OFDM requires fft_size > 0 and 0 <= cp_len < fft_size")
    block_len = fft_size + cp_len
    if values.size == 0 or symbol_count <= 0:
        return np.array([], dtype=complex)
    usable = values.size - (values.size % block_len)
    blocks = values[:usable].reshape(-1, block_len)
    no_cp = blocks[:, cp_len:] if cp_len else blocks
    freq = np.fft.fft(no_cp, axis=1) / np.sqrt(fft_size)
    return freq.reshape(-1)[:symbol_count]
