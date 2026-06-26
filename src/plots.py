"""Plot generation for constellation, BER curve, and synchronization peak."""

from __future__ import annotations

import os
from pathlib import Path
import gc
from io import BytesIO

import numpy as np

from .channel import awgn, one_tap_equalize, rayleigh_fading_channel
from .modulation import qpsk_demodulate, qpsk_modulate


def _prepare_matplotlib(results_dir: Path):
    config_dir = results_dir.parent / ".matplotlib-cache"
    config_dir.mkdir(parents=True, exist_ok=True)
    for lock_file in config_dir.glob("*.matplotlib-lock"):
        try:
            lock_file.unlink()
        except OSError:
            pass
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("MPLCONFIGDIR", str(config_dir))
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    return plt


def _save_figure_png(fig, plt, output: Path) -> None:
    buffer = BytesIO()
    try:
        fig.savefig(buffer, format="png")
    finally:
        plt.close(fig)
        plt.close("all")
        gc.collect()
    output.write_bytes(buffer.getvalue())
    buffer.close()


def plot_constellation(symbols: np.ndarray, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt = _prepare_matplotlib(output.parent)
    sample = np.asarray(symbols, dtype=complex)
    if sample.size > 3000:
        sample = sample[:3000]
    fig, ax = plt.subplots(figsize=(5, 5), dpi=120)
    ax.scatter(sample.real, sample.imag, s=5, alpha=0.45)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("In-phase")
    ax.set_ylabel("Quadrature")
    ax.set_title("Received QPSK Constellation")
    ax.grid(True, alpha=0.25)
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    _save_figure_png(fig, plt, output)


def plot_sync_peak(correlation: np.ndarray | list[float], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt = _prepare_matplotlib(output.parent)
    values = np.asarray(correlation, dtype=float)
    fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
    ax.plot(values)
    if values.size:
        peak = int(np.argmax(values))
        ax.axvline(peak, color="red", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Symbol offset")
    ax.set_ylabel("Normalized correlation")
    ax.set_title("Synchronization Peak")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    _save_figure_png(fig, plt, output)


def plot_ber_curve(path: str | Path, seed: int = 2026) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt = _prepare_matplotlib(output.parent)
    snr_points = np.array([0, 2, 4, 6, 8, 10, 12, 14, 16], dtype=float)
    rng = np.random.default_rng(seed)
    bits = [int(x) for x in rng.integers(0, 2, size=4000)]
    tx = qpsk_modulate(bits)
    ber_values: list[float] = []
    for snr in snr_points:
        rx = awgn(tx, float(snr), seed=seed + int(snr) + 3000)
        recovered = qpsk_demodulate(rx)[: len(bits)]
        errors = sum(1 for left, right in zip(bits, recovered) if left != right)
        ber_values.append(errors / len(bits))

    fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
    ax.semilogy(snr_points, np.maximum(ber_values, 1e-5), marker="o")
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("BER")
    ax.set_title("Noiseless Chain Reference BER-SNR")
    ax.grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    _save_figure_png(fig, plt, output)


def plot_ber_curve_compare(path: str | Path, seed: int = 2026) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt = _prepare_matplotlib(output.parent)
    snr_points = np.array([0, 2, 4, 6, 8, 10, 12, 14, 16], dtype=float)
    rng = np.random.default_rng(seed + 5000)
    bits = [int(x) for x in rng.integers(0, 2, size=6000)]
    tx = qpsk_modulate(bits)
    awgn_ber: list[float] = []
    rayleigh_ber: list[float] = []
    for snr in snr_points:
        awgn_rx = awgn(tx, float(snr), seed=seed + int(snr) + 6000)
        awgn_bits = qpsk_demodulate(awgn_rx)[: len(bits)]
        awgn_errors = sum(1 for left, right in zip(bits, awgn_bits) if left != right)
        awgn_ber.append(awgn_errors / len(bits))

        rayleigh_rx, h = rayleigh_fading_channel(tx, float(snr), seed=seed + int(snr) + 7000)
        equalized = one_tap_equalize(rayleigh_rx, h)
        rayleigh_bits = qpsk_demodulate(equalized)[: len(bits)]
        rayleigh_errors = sum(1 for left, right in zip(bits, rayleigh_bits) if left != right)
        rayleigh_ber.append(rayleigh_errors / len(bits))

    fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
    ax.semilogy(snr_points, np.maximum(awgn_ber, 1e-5), marker="o", label="AWGN")
    ax.semilogy(
        snr_points,
        np.maximum(rayleigh_ber, 1e-5),
        marker="s",
        label="Rayleigh + one-tap EQ",
    )
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("BER")
    ax.set_title("AWGN vs Rayleigh BER-SNR Comparison")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    _save_figure_png(fig, plt, output)


def generate_plots(
    *,
    results_dir: str | Path,
    received_symbols: np.ndarray,
    correlation: np.ndarray | list[float] | None,
    seed: int,
) -> list[str]:
    directory = Path(results_dir)
    directory.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    plot_constellation(received_symbols, directory / "constellation.png")
    generated.append("constellation.png")
    plot_ber_curve(directory / "ber_curve.png", seed=seed)
    generated.append("ber_curve.png")
    plot_ber_curve_compare(directory / "ber_curve_compare.png", seed=seed)
    generated.append("ber_curve_compare.png")
    if correlation is not None:
        plot_sync_peak(correlation, directory / "sync_peak.png")
        generated.append("sync_peak.png")
    return generated
