from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .channel import awgn
from .metrics import bit_error_rate
from .modulation import qpsk_demodulate, qpsk_modulate


def _ensure_parent(path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def plot_constellation(symbols, path, snr_db: float, max_points: int = 4000) -> None:
    target = _ensure_parent(path)
    arr = np.asarray(symbols, dtype=complex)[:max_points]
    fig, ax = plt.subplots(figsize=(5, 5), dpi=120)
    if arr.size:
        ax.scatter(arr.real, arr.imag, s=8, alpha=0.55, edgecolors="none")
    ax.axhline(0, color="0.55", linewidth=0.8)
    ax.axvline(0, color="0.55", linewidth=0.8)
    ax.set_title(f"QPSK constellation, SNR={snr_db:g} dB")
    ax.set_xlabel("In-phase")
    ax.set_ylabel("Quadrature")
    ax.grid(True, linewidth=0.4, alpha=0.45)
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(target)
    plt.close(fig)


def plot_sync_peak(correlation, path, start_index: int) -> None:
    target = _ensure_parent(path)
    corr = np.asarray(correlation, dtype=float)
    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=120)
    if corr.size:
        ax.plot(np.arange(corr.size), corr, linewidth=1.2)
        ax.axvline(start_index, color="tab:red", linestyle="--", linewidth=1.0)
    ax.set_title(f"Synchronization correlation peak at {start_index}")
    ax.set_xlabel("Symbol offset")
    ax.set_ylabel("Correlation")
    ax.grid(True, linewidth=0.4, alpha=0.45)
    fig.tight_layout()
    fig.savefig(target)
    plt.close(fig)


def plot_ber_curve(path, seed: int = 2026) -> None:
    target = _ensure_parent(path)
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, size=4096).astype(int).tolist()
    symbols = qpsk_modulate(bits)
    snr_points = [0, 3, 6, 9, 12, 15]
    ber_values = []
    for snr in snr_points:
        received = awgn(symbols, snr_db=snr, seed=seed + int(snr) + 17)
        recovered = qpsk_demodulate(received)[: len(bits)]
        ber_values.append(bit_error_rate(bits, recovered))

    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=120)
    ax.semilogy(snr_points, ber_values, marker="o", linewidth=1.4)
    ax.set_title("QPSK over AWGN BER curve")
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("BER")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.45)
    fig.tight_layout()
    fig.savefig(target)
    plt.close(fig)
