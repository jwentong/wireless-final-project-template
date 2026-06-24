"""Visualization: constellation, BER curve, sync peak."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

import numpy as np

from src.channel import awgn
from src.receiver import run_receiver
from src.transmitter import run_transmitter


def _write_minimal_png(path: Path, width: int = 64, height: int = 64) -> None:
    """Write a tiny valid PNG when matplotlib is unavailable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join(b"\x00" + bytes([120, 150, 200]) * width for _ in range(height))
    compressed = zlib.compress(raw, 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def _get_plt():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except ImportError:
        return None


def plot_constellation(rx_symbols: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt = _get_plt()
    if plt is None:
        _write_minimal_png(path)
        return
    fig, ax = plt.subplots(figsize=(6, 6))
    pts = np.asarray(rx_symbols, dtype=complex)
    ax.scatter(pts.real, pts.imag, s=4, alpha=0.35, label="Received")
    ideal = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]) / np.sqrt(2)
    ax.scatter(ideal.real, ideal.imag, s=120, marker="x", c="red", label="Ideal QPSK")
    ax.set_xlabel("I")
    ax.set_ylabel("Q")
    ax.set_title("QPSK Constellation")
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.axis("equal")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_sync_peak(correlation: np.ndarray, peak_index: int, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt = _get_plt()
    if plt is None:
        _write_minimal_png(path)
        return
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(correlation, linewidth=1.0)
    if len(correlation) > peak_index:
        ax.axvline(peak_index, color="red", linestyle="--", label=f"Peak @ {peak_index}")
    ax.set_xlabel("Symbol index")
    ax.set_ylabel("|Correlation|")
    ax.set_title("Preamble Sync Correlation Peak")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_ber_curve(
    text: str,
    seed: int,
    path: Path,
    channel_fn=awgn,
    channel_name: str = "awgn",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    snr_points = list(range(0, 16, 2))
    bers: list[float] = []
    tmrs: list[float] = []

    tx_symbols, meta = run_transmitter(text, seed=seed)
    preamble_symbols = meta["preamble_symbols"]

    for snr in snr_points:
        if channel_name == "rayleigh":
            from src.channel import rayleigh

            rx, _ = rayleigh(tx_symbols, snr_db=float(snr), seed=seed + snr * 100)
        else:
            rx = channel_fn(tx_symbols, snr_db=float(snr), seed=seed + snr * 100)
        _, partial = run_receiver(
            rx,
            seed=seed,
            preamble_symbols=preamble_symbols,
            original_text=text,
        )
        bers.append(float(partial["ber"]))
        tmrs.append(float(partial["text_match_rate"]))

    plt = _get_plt()
    if plt is None:
        _write_minimal_png(path)
        return
    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.semilogy(snr_points, [max(b, 1e-6) for b in bers], "o-", label="BER")
    ax1.set_xlabel("SNR (dB)")
    ax1.set_ylabel("BER")
    ax1.grid(True, which="both", alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(snr_points, tmrs, "s--", color="green", label="text_match_rate")
    ax2.set_ylabel("Text match rate")
    ax2.set_ylim(-0.05, 1.05)
    ax1.set_title(f"BER / Text Match vs SNR ({channel_name})")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def generate_all_plots(
    text: str,
    seed: int,
    snr_db: float,
    results_dir: Path,
    rx_symbols: np.ndarray,
    sync_correlation: np.ndarray,
    sync_start_index: int,
    channel_name: str = "awgn",
) -> None:
    plot_constellation(rx_symbols, results_dir / "constellation.png")
    plot_sync_peak(sync_correlation, sync_start_index, results_dir / "sync_peak.png")
    plot_ber_curve(text, seed, results_dir / "ber_curve.png", channel_name=channel_name)
