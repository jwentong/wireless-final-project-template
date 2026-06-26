"""End-to-end wireless baseband simulation pipeline."""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .channel import awgn
from .channel_coding import channel_decode, channel_encode
from .framing import PREAMBLE_BITS, build_frame, parse_frame
from .modulation import qpsk_demodulate, qpsk_modulate
from .scramble import descramble, scramble
from .source import source_decode, source_encode
from .synchronization import synchronize


def _bit_error_rate(reference: list[int], observed: list[int]) -> float:
    n = max(len(reference), len(observed))
    if n == 0:
        return 0.0
    errors = 0
    for i in range(n):
        a = reference[i] if i < len(reference) else 0
        b = observed[i] if i < len(observed) else 0
        errors += int(a != b)
    return errors / n


def _text_match_rate(reference: str, observed: str) -> float:
    if not reference and not observed:
        return 1.0
    return float(SequenceMatcher(None, reference, observed).ratio())


def _add_prefix(symbols: np.ndarray, seed: int, max_offset: int = 128) -> tuple[np.ndarray, int]:
    rng = np.random.default_rng(int(seed) + 7919)
    offset = int(rng.integers(0, max_offset + 1))
    if offset == 0:
        return symbols, 0
    prefix = (rng.normal(size=offset) + 1j * rng.normal(size=offset)) / np.sqrt(2.0)
    return np.concatenate([prefix, symbols]), offset


def _plot_constellation(symbols: np.ndarray, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.6, 5.0), dpi=140)
    sample = symbols[: min(len(symbols), 2500)]
    ax.scatter(sample.real, sample.imag, s=6, alpha=0.45, color="#1f77b4", edgecolors="none")
    ideal = qpsk_modulate([0, 0, 0, 1, 1, 1, 1, 0])
    ax.scatter(ideal.real, ideal.imag, s=70, color="#d62728", marker="x", label="ideal")
    ax.axhline(0, color="#555555", linewidth=0.7)
    ax.axvline(0, color="#555555", linewidth=0.7)
    ax.set_title("QPSK constellation after AWGN")
    ax.set_xlabel("In-phase")
    ax.set_ylabel("Quadrature")
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal", adjustable="box")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_sync(metric: np.ndarray, start: int, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.0, 3.6), dpi=140)
    ax.plot(np.arange(metric.size), metric, color="#2ca02c", linewidth=1.1)
    if metric.size:
        ax.axvline(start, color="#d62728", linestyle="--", linewidth=1.0, label=f"start={start}")
    ax.set_title("Synchronization correlation peak")
    ax.set_xlabel("Candidate symbol offset")
    ax.set_ylabel("Correlation magnitude")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_ber_curve(path: Path, seed: int) -> None:
    rng = np.random.default_rng(int(seed) + 3571)
    bits = rng.integers(0, 2, size=12000).astype(int).tolist()
    symbols = qpsk_modulate(bits)
    snrs = np.array([0, 3, 6, 9, 12, 15], dtype=float)
    bers = []
    for snr in snrs:
        rx = awgn(symbols, snr_db=float(snr), seed=int(seed) + int(snr * 10))
        recovered = qpsk_demodulate(rx)[: len(bits)]
        bers.append(max(_bit_error_rate(bits, recovered), 1e-6))
    fig, ax = plt.subplots(figsize=(6.2, 4.0), dpi=140)
    ax.semilogy(snrs, bers, marker="o", color="#9467bd")
    ax.set_title("Uncoded QPSK BER-SNR reference")
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("BER")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def run_transmission(
    input_path: str | Path,
    output_path: str | Path,
    snr_db: float = 12.0,
    seed: int = 2026,
    modulation: str = "qpsk",
    channel_name: str = "awgn",
) -> Dict[str, Any]:
    if modulation.lower() != "qpsk":
        raise ValueError("Only qpsk is implemented for the required baseline")
    if channel_name.lower() != "awgn":
        raise ValueError("Only awgn is implemented for the required baseline")

    input_path = Path(input_path)
    output_path = Path(output_path)
    results_dir = output_path.parent
    results_dir.mkdir(parents=True, exist_ok=True)

    source_text = input_path.read_text(encoding="utf-8")
    payload_bits = source_encode(source_text)
    scrambled_bits = scramble(payload_bits, seed=seed)
    coded_bits = channel_encode(scrambled_bits)
    frame_bits = build_frame(coded_bits, source_length=len(payload_bits))
    tx_symbols = qpsk_modulate(frame_bits)

    noisy_symbols = awgn(tx_symbols, snr_db=snr_db, seed=seed)
    received_symbols, inserted_offset = _add_prefix(noisy_symbols, seed=seed)
    preamble_symbols = qpsk_modulate(PREAMBLE_BITS)
    sync_result = synchronize(received_symbols, preamble=preamble_symbols)
    sync_start = int(sync_result["start_index"])
    aligned_symbols = received_symbols[sync_start:]

    demodulated_frame_bits = qpsk_demodulate(aligned_symbols)
    parsed = parse_frame(demodulated_frame_bits)
    recovered_coded = parsed["payload"][: parsed["payload_length"]]
    recovered_scrambled = channel_decode(recovered_coded)[: parsed["length"]]
    recovered_bits = descramble(recovered_scrambled, seed=seed)[: len(payload_bits)]
    try:
        received_text = source_decode(recovered_bits, bit_length=len(payload_bits))
    except UnicodeDecodeError:
        received_text = source_decode(recovered_bits, bit_length=len(payload_bits), errors="replace")

    output_path.write_text(received_text, encoding="utf-8")

    ber = _bit_error_rate(payload_bits, recovered_bits)
    match_rate = _text_match_rate(source_text, received_text)
    checksum_pass = bool(parsed["checksum_pass"] and received_text == source_text)
    metrics: Dict[str, Any] = {
        "snr_db": float(snr_db),
        "seed": int(seed),
        "modulation": "qpsk",
        "channel": "awgn",
        "payload_bits": len(payload_bits),
        "ber": float(ber),
        "fer": 0.0 if checksum_pass else 1.0,
        "text_match_rate": float(match_rate),
        "checksum_pass": checksum_pass,
        "sync_start_index": sync_start,
        "inserted_sync_offset": inserted_offset,
        "sync_error_symbols": int(abs(sync_start - inserted_offset)),
        "frame_bits": len(frame_bits),
        "coded_payload_bits": len(coded_bits),
        "channel_code": "repetition-3",
        "scrambler": "xor-pn",
    }

    _plot_constellation(aligned_symbols, results_dir / "constellation.png")
    _plot_ber_curve(results_dir / "ber_curve.png", seed=seed)
    _plot_sync(np.asarray(sync_result["metric"], dtype=float), sync_start, results_dir / "sync_peak.png")
    return metrics

