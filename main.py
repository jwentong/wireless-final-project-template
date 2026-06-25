import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

from src.source import source_encode, source_decode
from src.crypto import scramble, descramble
from src.channel_coding import channel_encode, channel_decode
from src.framing import build_frame, parse_frame, PREAMBLE_BITS
from src.modulation import qpsk_modulate, qpsk_demodulate, demodulate, modulate
from src.channel import awgn, rayleigh
from src.synchronization import synchronize, compute_sync_metric


def _compute_checksum(bits):
    byte_val = 0
    for i in range(len(bits)):
        byte_val ^= (bits[i] << (7 - (i % 8)))
        if i % 8 == 7:
            byte_val &= 0xFF
    return byte_val & 0xFF

def _int_to_bits(val, n_bits):
    return [(val >> (n_bits - 1 - i)) & 1 for i in range(n_bits)]


def run_pipeline(input_path, output_path, snr_db=12, seed=2026, mod="qpsk", channel="awgn"):
    text = Path(input_path).read_text(encoding="utf-8")
    raw_bits = source_encode(text)
    original_bit_count = len(raw_bits)
    np.random.seed(seed)
    scrambled_bits = scramble(raw_bits, seed=seed)
    checksum_val = _compute_checksum(scrambled_bits)
    checksum_bits = _int_to_bits(checksum_val, 8)
    data_with_checksum = scrambled_bits + checksum_bits
    coded_bits = channel_encode(data_with_checksum, method="hamming")
    frame_bits = build_frame(coded_bits)
    if mod == "qpsk":
        frame_symbols = qpsk_modulate(frame_bits)
    else:
        frame_symbols = modulate(frame_bits, mod)
    if channel == "awgn":
        rx_symbols = awgn(frame_symbols, snr_db, seed=seed)
    elif channel == "rayleigh":
        rx_symbols = rayleigh(frame_symbols, snr_db, seed=seed)
    else:
        rx_symbols = awgn(frame_symbols, snr_db, seed=seed)
    preamble_symbols = qpsk_modulate(PREAMBLE_BITS)
    sync_start = synchronize(rx_symbols, preamble_symbols)
    if sync_start + len(preamble_symbols) > len(rx_symbols):
        sync_start = 0
    data_symbols = rx_symbols[sync_start:]
    if mod == "qpsk":
        rx_bits = qpsk_demodulate(data_symbols)
    else:
        rx_bits = demodulate(data_symbols, mod)
    parsed = parse_frame(rx_bits)
    recovered_coded_bits = parsed["payload"]
    recovered_extended = channel_decode(recovered_coded_bits, method="hamming")
    if len(recovered_extended) >= 8:
        received_checksum_bits = recovered_extended[-8:]
        recovered_scrambled = recovered_extended[:-8]
        received_checksum = 0
        for b in received_checksum_bits:
            received_checksum = (received_checksum << 1) | b
        computed_checksum = _compute_checksum(recovered_scrambled)
        checksum_pass = received_checksum == computed_checksum
    else:
        recovered_scrambled = recovered_extended
        checksum_pass = False
    decoded_bits = descramble(recovered_scrambled, seed=seed)
    decoded_bits = decoded_bits[:original_bit_count]
    received_text = source_decode(decoded_bits)
    if decoded_bits and len(decoded_bits) >= 8:
        recoded_bits = source_encode(received_text)
        min_len = min(len(decoded_bits), len(recoded_bits))
        if min_len > 0:
            bit_errors = sum(a != b for a, b in zip(decoded_bits[:min_len], recoded_bits[:min_len]))
        else:
            bit_errors = 0
    else:
        recoded_bits = []
        bit_errors = 0
    total_bits = max(len(raw_bits), 1)
    ber = bit_errors / total_bits
    recovered_len = len(recovered_coded_bits)
    total_frames = 1
    frame_errors = 0 if recovered_len > 0 else 1
    fer = frame_errors / max(total_frames, 1)
    text_match = 1.0 if received_text == text else 0.0
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(received_text, encoding="utf-8")
    metrics = {
        "snr_db": float(snr_db),
        "seed": int(seed),
        "modulation": mod,
        "channel": channel,
        "payload_bits": original_bit_count,
        "ber": float(ber),
        "fer": float(fer),
        "text_match_rate": float(text_match),
        "checksum_pass": bool(checksum_pass),
        "sync_start_index": int(sync_start),
    }
    results_dir = Path(output_path).parent
    metrics_path = results_dir / "metrics.json"
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    _generate_plots(results_dir, frame_symbols, rx_symbols, preamble_symbols, snr_db, mod)
    return metrics


def _generate_plots(results_dir, tx_symbols, rx_symbols, preamble_symbols, snr_db, mod):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    rx_arr = np.array(rx_symbols)
    tx_arr = np.array(tx_symbols)
    channel_type = "awgn"

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(rx_arr.real, rx_arr.imag, s=1, alpha=0.5, label="Received")
    ax.scatter(tx_arr.real, tx_arr.imag, s=3, alpha=0.8, label="Transmitted")
    ax.set_xlabel("In-Phase")
    ax.set_ylabel("Quadrature")
    ax.set_title(f"Constellation Diagram ({mod.upper()}, SNR={snr_db}dB)")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.savefig(str(results_dir / "constellation.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    snr_range = np.arange(0, 16, 2)
    ber_values = []
    test_bit_len = 10000
    test_bits = [int(x) for x in np.random.default_rng(42).integers(0, 2, size=test_bit_len)]
    if mod == "qpsk":
        test_symbols = qpsk_modulate(test_bits)
    else:
        test_symbols = modulate(test_bits, mod)
    for s in snr_range:
        test_rx = awgn(np.array(test_symbols), s, seed=42)
        if mod == "qpsk":
            test_rx_bits = qpsk_demodulate(test_rx)
        else:
            test_rx_bits = demodulate(test_rx, mod)
        errors = sum(a != b for a, b in zip(test_bits, test_rx_bits[:len(test_bits)]))
        ber_values.append(errors / max(len(test_bits), 1))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.semilogy(snr_range, ber_values, "b-o", markersize=4)
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("BER")
    ax.set_title(f"BER vs SNR ({mod.upper()}, {channel_type.upper()})")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(top=1)
    fig.savefig(str(results_dir / "ber_curve.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    corr = compute_sync_metric(rx_arr, preamble_symbols)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(np.abs(corr))
    ax.set_xlabel("Sample Index")
    ax.set_ylabel("Correlation Magnitude")
    ax.set_title("Sync Correlation Peak")
    ax.grid(True, alpha=0.3)
    peak_idx = int(np.argmax(np.abs(corr)))
    ax.axvline(x=peak_idx, color="r", linestyle="--", alpha=0.7, label=f"Peak at {peak_idx}")
    ax.legend()
    fig.savefig(str(results_dir / "sync_peak.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Wireless Communication Baseband Simulation System")
    parser.add_argument("--input", required=True, help="Input text file path")
    parser.add_argument("--output", required=True, help="Output received text file path")
    parser.add_argument("--snr", type=float, default=12, help="SNR in dB")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    parser.add_argument("--mod", default="qpsk", choices=["qpsk", "bpsk", "16qam"], help="Modulation scheme")
    parser.add_argument("--channel", default="awgn", choices=["awgn", "rayleigh"], help="Channel model")
    args = parser.parse_args()
    metrics = run_pipeline(
        input_path=args.input,
        output_path=args.output,
        snr_db=args.snr,
        seed=args.seed,
        mod=args.mod,
        channel=args.channel,
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
