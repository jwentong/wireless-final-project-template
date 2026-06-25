#!/usr/bin/env python3
"""Wireless Communication Baseband Simulation — End-to-End Pipeline.

Unified CLI:
    python main.py --input Test.txt --output results/received.txt
                   --snr 12 --seed 2026 --mod qpsk --channel awgn
"""

import argparse
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from src.source import source_encode, source_decode
from src.crypto import scramble, descramble
from src.channel_coding import channel_encode, channel_decode
from src.framing import build_frame, parse_frame, frame_to_bits, _PREAMBLE
from src.modulation import qpsk_modulate, qpsk_demodulate
from src.channel import awgn
from src.synchronization import synchronize


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wireless Communication Baseband Simulation"
    )
    parser.add_argument("--input", default="Test.txt", help="Input UTF-8 text file")
    parser.add_argument(
        "--output", default="results/received.txt", help="Output recovered text file"
    )
    parser.add_argument("--snr", type=float, default=12.0, help="SNR in dB")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    parser.add_argument("--mod", default="qpsk", help="Modulation scheme (qpsk)")
    parser.add_argument("--channel", default="awgn", help="Channel model (awgn)")
    return parser.parse_args()


def run_pipeline(
    input_path: str,
    output_path: str,
    snr_db: float,
    seed: int,
    mod: str,
    channel: str,
) -> dict:
    """Run the full wireless communication pipeline.

    Returns:
        metrics dict.
    """

    # ── Read input ──────────────────────────────────────────────────
    text = Path(input_path).read_text(encoding="utf-8")

    # ── Transmitter ─────────────────────────────────────────────────
    # 1. Source encode: UTF-8 text -> bits
    tx_bits = source_encode(text)
    payload_bit_count = len(tx_bits)

    # 2. Scramble
    scrambled = scramble(tx_bits, seed=seed)

    # 3. Channel encode (Hamming 7,4)
    coded = channel_encode(scrambled)

    # 4. Frame build
    frame = build_frame(coded)

    # Serialize frame to bits
    frame_bits = frame_to_bits(frame)

    # 5. QPSK modulate
    symbols = qpsk_modulate(frame_bits)

    # Preamble symbols for synchronization
    preamble_symbols = qpsk_modulate(list(_PREAMBLE))

    # ── Channel ─────────────────────────────────────────────────────
    # 6. AWGN
    noisy_symbols = awgn(symbols, snr_db=snr_db, seed=seed)

    # ── Receiver ────────────────────────────────────────────────────
    # 7. Synchronization
    sync_start = synchronize(noisy_symbols, preamble=preamble_symbols)
    aligned_symbols = noisy_symbols[sync_start:]

    # 8. QPSK demodulate
    demod_bits = qpsk_demodulate(aligned_symbols)

    # 9. Parse frame
    parsed = parse_frame(demod_bits)
    rx_coded = parsed["payload"]

    # 10. Channel decode
    decoded = channel_decode(rx_coded)

    # 11. Descramble
    descrambled = descramble(decoded, seed=seed)

    # 12. Source decode
    # Truncate to original payload bit count (remove channel-coding padding)
    recovered_bits = descrambled[:payload_bit_count]
    recovered_text = source_decode(recovered_bits)

    # ── Write output ────────────────────────────────────────────────
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(recovered_text, encoding="utf-8")

    # ── Metrics ─────────────────────────────────────────────────────
    # BER: compare source-encoded original bits with recovered bits
    min_len = min(payload_bit_count, len(descrambled))
    bit_errors = sum(
        1
        for i in range(min_len)
        if tx_bits[i] != descrambled[i]
    )
    ber = bit_errors / max(payload_bit_count, 1)

    # FER (Frame Error Rate): 0 if text matches, 1 otherwise
    fer = 0.0 if recovered_text == text else 1.0

    # Text match rate
    text_match_rate = 1.0 if recovered_text == text else 0.0

    # Checksum verification (CRC-16)
    # Recompute CRC on parsed frame's length + payload
    from src.framing import _int_to_bits, _crc16

    expected_crc = _crc16(
        _int_to_bits(parsed["length"], 16) + list(parsed["payload"])
    )
    checksum_pass = parsed["crc"] == expected_crc

    metrics = {
        "snr_db": snr_db,
        "seed": seed,
        "modulation": mod,
        "channel": channel,
        "payload_bits": payload_bit_count,
        "ber": ber,
        "fer": fer,
        "text_match_rate": text_match_rate,
        "checksum_pass": checksum_pass,
        "sync_start_index": int(sync_start),
    }

    metrics_path = out_path.parent / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    # ── Plots ───────────────────────────────────────────────────────
    results_dir = out_path.parent
    _plot_constellation(noisy_symbols, results_dir)
    _plot_ber_curve(
        text, seed, mod, channel, snr_db, results_dir
    )
    _plot_sync_peak(noisy_symbols, preamble_symbols, results_dir)

    return metrics


def _plot_constellation(
    symbols: np.ndarray, results_dir: Path
) -> None:
    """Plot received QPSK constellation (I/Q scatter)."""
    sym = np.asarray(symbols).flatten()
    plt.figure(figsize=(6, 6))
    plt.scatter(sym.real, sym.imag, s=4, alpha=0.6)
    plt.axhline(0, color="gray", linewidth=0.5)
    plt.axvline(0, color="gray", linewidth=0.5)
    plt.xlabel("In-phase (I)")
    plt.ylabel("Quadrature (Q)")
    plt.title("Received QPSK Constellation")
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.savefig(results_dir / "constellation.png", dpi=150, bbox_inches="tight")
    plt.close()


def _plot_ber_curve(
    text: str,
    seed: int,
    mod: str,
    channel: str,
    ref_snr: float,
    results_dir: Path,
) -> None:
    """Plot BER vs SNR curve by sweeping SNR values."""
    snr_range = np.arange(0, 15, 2)
    ber_values = []

    tx_bits = source_encode(text)
    payload_bit_count = len(tx_bits)

    # Use a different seed for BER sweep to avoid matching the ref seed exactly
    sweep_seed = seed + 1000

    for snr in snr_range:
        try:
            # Transmitter
            scrambled = scramble(tx_bits, seed=seed)
            coded = channel_encode(scrambled)
            frame = build_frame(coded)
            frame_bits = frame_to_bits(frame)
            symbols = qpsk_modulate(frame_bits)
            preamble_symbols = qpsk_modulate(list(_PREAMBLE))

            # Channel
            noisy = awgn(symbols, snr_db=float(snr), seed=sweep_seed)

            # Receiver
            sync_start = synchronize(noisy, preamble=preamble_symbols)
            aligned = noisy[sync_start:]
            demod_bits = qpsk_demodulate(aligned)
            parsed = parse_frame(demod_bits)
            rx_coded = parsed["payload"]
            decoded = channel_decode(rx_coded)
            descrambled = descramble(decoded, seed=seed)

            # BER
            min_len = min(payload_bit_count, len(descrambled))
            errors = sum(
                1
                for i in range(min_len)
                if tx_bits[i] != descrambled[i]
            )
            ber = errors / max(payload_bit_count, 1)
            ber_values.append(ber)
        except Exception:
            ber_values.append(0.5)  # worst-case on failure

    plt.figure(figsize=(8, 5))
    plt.semilogy(snr_range, ber_values, "b-o", linewidth=2, markersize=6)
    plt.xlabel("SNR (dB)")
    plt.ylabel("Bit Error Rate (BER)")
    plt.title("BER vs SNR (AWGN, QPSK, Hamming(7,4))")
    plt.grid(True, which="both", alpha=0.3)
    plt.ylim(1e-5, 1)
    plt.savefig(results_dir / "ber_curve.png", dpi=150, bbox_inches="tight")
    plt.close()


def _plot_sync_peak(
    noisy_symbols: np.ndarray,
    preamble_symbols: np.ndarray,
    results_dir: Path,
) -> None:
    """Plot cross-correlation magnitude for synchronization visualization."""
    from scipy import signal as scipy_signal

    noisy = np.asarray(noisy_symbols).flatten()
    pre = np.asarray(preamble_symbols).flatten()

    if len(noisy) < len(pre):
        return

    corr = scipy_signal.correlate(noisy, pre, mode="valid")
    corr_mag = np.abs(corr)

    plt.figure(figsize=(8, 4))
    plt.plot(np.arange(len(corr_mag)), corr_mag, "b-", linewidth=1)
    peak_idx = np.argmax(corr_mag)
    plt.axvline(peak_idx, color="r", linestyle="--", label=f"Peak at {peak_idx}")
    plt.xlabel("Symbol Offset")
    plt.ylabel("Correlation Magnitude")
    plt.title("Synchronization — Cross-Correlation with Preamble")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(results_dir / "sync_peak.png", dpi=150, bbox_inches="tight")
    plt.close()


def main() -> None:
    args = parse_args()
    metrics = run_pipeline(
        input_path=args.input,
        output_path=args.output,
        snr_db=args.snr,
        seed=args.seed,
        mod=args.mod,
        channel=args.channel,
    )
    print(f"Simulation complete.")
    print(f"  SNR: {metrics['snr_db']} dB")
    print(f"  BER: {metrics['ber']:.6f}")
    print(f"  FER: {metrics['fer']:.6f}")
    print(f"  Text match rate: {metrics['text_match_rate']}")
    print(f"  CRC pass: {metrics['checksum_pass']}")
    print(f"  Sync start: {metrics['sync_start_index']}")


if __name__ == "__main__":
    main()
