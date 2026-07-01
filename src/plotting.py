"""结果可视化：星座图 / BER-SNR 曲线 / 同步相关峰值图"""
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

for _font in ("Noto Sans CJK JP", "WenQuanYi Zen Hei", "Noto Sans CJK SC"):
    if any(_font == f.name for f in fm.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [_font]
        plt.rcParams["axes.unicode_minus"] = False
        break

from .channel_coding import channel_encode, channel_decode
from .modulation import qpsk_modulate, qpsk_demodulate
from .channel import awgn


def plot_constellation(symbols, path):
    symbols = np.asarray(list(symbols), dtype=complex)
    plt.figure(figsize=(5, 5))
    plt.scatter(symbols.real, symbols.imag, s=10, alpha=0.6)
    plt.axhline(0, color="gray", linewidth=0.5)
    plt.axvline(0, color="gray", linewidth=0.5)
    plt.title("QPSK 星座图（含信道噪声）")
    plt.xlabel("I")
    plt.ylabel("Q")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def plot_ber_curve(path, seed=2026, n_bits=4000, snr_list=None):
    if snr_list is None:
        snr_list = list(range(-2, 17, 2))
    rng_bits = np.random.default_rng(seed).integers(0, 2, size=n_bits).tolist()
    coded = channel_encode(rng_bits)
    bers = []
    for snr_db in snr_list:
        symbols = qpsk_modulate(coded)
        noisy = awgn(symbols, snr_db=snr_db, seed=seed)
        demod = qpsk_demodulate(noisy)[: len(coded)]
        decoded = channel_decode(demod)[: len(rng_bits)]
        errors = sum(1 for a, b in zip(rng_bits, decoded) if a != b)
        bers.append(max(errors / len(rng_bits), 1e-6))
    plt.figure(figsize=(6, 4))
    plt.semilogy(snr_list, bers, marker="o")
    plt.xlabel("SNR (dB)")
    plt.ylabel("BER")
    plt.title("BER-SNR 曲线（QPSK + 重复码 + AWGN）")
    plt.grid(True, which="both", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def plot_sync_peak(received_symbols, preamble_symbols, path):
    received = np.asarray(list(received_symbols), dtype=complex)
    preamble = np.asarray(list(preamble_symbols), dtype=complex)
    m = len(preamble)
    n = len(received)
    if n < m:
        return
    windows = sliding_window_view(received, m)
    corr = np.abs(windows @ np.conj(preamble))
    norms = np.sqrt(np.sum(np.abs(windows) ** 2, axis=1) * np.sum(np.abs(preamble) ** 2)) + 1e-12
    scores = corr / norms
    plt.figure(figsize=(7, 4))
    plt.plot(scores)
    peak = int(np.argmax(scores))
    plt.axvline(peak, color="red", linestyle="--", label=f"检测起点={peak}")
    plt.xlabel("符号位置")
    plt.ylabel("归一化相关值")
    plt.title("同步相关峰值图")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()
