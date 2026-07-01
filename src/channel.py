"""AWGN 信道模块：按 SNR(dB) 添加复高斯白噪声，固定 seed 可复现。"""
from __future__ import annotations
from typing import Iterable
import numpy as np


def awgn(symbols: Iterable[complex], snr_db: float = 12.0, seed: int = 2026) -> np.ndarray:
    symbols = np.asarray(list(symbols), dtype=complex)
    signal_power = float(np.mean(np.abs(symbols) ** 2)) if len(symbols) else 1.0
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear
    rng = np.random.default_rng(seed)
    noise = (rng.normal(size=symbols.shape) + 1j * rng.normal(size=symbols.shape)) * np.sqrt(noise_power / 2)
    return symbols + noise


awgn_channel = awgn
add_awgn = awgn
add_noise = awgn
