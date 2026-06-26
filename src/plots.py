"""Visualization module: Generate constellation, BER curve, and sync peak plots."""

import os
from pathlib import Path

import numpy as np

# Use non-interactive backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_constellation(symbols, output_path: str = "results/constellation.png",
                       title: str = "QPSK Constellation Diagram"):
    """Plot constellation diagram (scatter plot of received symbols).

    Args:
        symbols: List/array of complex received symbols.
        output_path: Path to save the PNG file.
        title: Plot title.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    syms = np.asarray(symbols, dtype=complex)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(syms.real, syms.imag, alpha=0.5, s=10, c='blue', label='Received')
    ax.scatter([1/np.sqrt(2), -1/np.sqrt(2), -1/np.sqrt(2), 1/np.sqrt(2)],
               [1/np.sqrt(2), 1/np.sqrt(2), -1/np.sqrt(2), -1/np.sqrt(2)],
               c='red', marker='x', s=100, linewidths=2, label='Reference')
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.3)
    ax.axvline(x=0, color='gray', linestyle='--', alpha=0.3)
    ax.set_xlabel("In-phase (I)")
    ax.set_ylabel("Quadrature (Q)")
    ax.set_title(title)
    ax.legend()
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_ber_curve(snr_values: list[float], ber_values: list[float],
                   output_path: str = "results/ber_curve.png",
                       title: str = "BER vs SNR (AWGN Channel)"):
    """Plot BER vs SNR curve.

    Args:
        snr_values: List of SNR values in dB.
        ber_values: List of corresponding BER values.
        output_path: Path to save the PNG file.
        title: Plot title.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogy(snr_values, ber_values, 'b-o', markersize=6, linewidth=2, label='Measured BER')
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("Bit Error Rate (BER)")
    ax.set_title(title)
    ax.grid(True, which='both', alpha=0.3)
    ax.legend()
    ax.set_ylim(bottom=1e-6, top=1.0)

    # Add theoretical QPSK BER reference: 0.5 * erfc(sqrt(Eb/N0))
    # For QPSK, Eb/N0 = SNR (since 2 bits per symbol, Es/N0 = 2*Eb/N0, Es = 2*Eb)
    snr_linear = [10 ** (s / 10.0) for s in snr_values]
    eb_n0_linear = [s / 2.0 for s in snr_linear]  # Eb/N0 = Es/N0 / log2(M) = SNR / 2 for QPSK
    from scipy.special import erfc
    theoretical_ber = [0.5 * erfc(np.sqrt(eb)) for eb in eb_n0_linear]
    ax.semilogy(snr_values, theoretical_ber, 'r--', linewidth=1.5, alpha=0.7, label='Theoretical QPSK')

    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_sync_peak(correlation, start_index: int = None,
                   output_path: str = "results/sync_peak.png",
                   title: str = "Synchronization Cross-Correlation"):
    """Plot synchronization cross-correlation magnitude with detected peak.

    Args:
        correlation: Array of correlation magnitudes.
        start_index: The detected peak index (optional, marked with vertical line).
        output_path: Path to save the PNG file.
        title: Plot title.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    corr = np.asarray(correlation, dtype=float)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(corr, 'b-', linewidth=1.5, label='Correlation magnitude')
    if start_index is not None and 0 <= start_index < len(corr):
        ax.axvline(x=start_index, color='r', linestyle='--', linewidth=2,
                   label=f'Detected start = {start_index}')
    ax.set_xlabel("Sample index")
    ax.set_ylabel("Correlation magnitude")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
