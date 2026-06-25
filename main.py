import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.channel import awgn
from src.channel_coding import channel_decode, channel_encode
from src.framing import PREAMBLE_BITS, build_frame, checksum32, parse_frame
from src.modulation import qpsk_demodulate, qpsk_modulate
from src.scramble import descramble, scramble
from src.source import source_decode, source_encode
from src.synchronization import synchronize


def bit_error_rate(reference, recovered):
    n = max(len(reference), len(recovered))
    if n == 0:
        return 0.0
    errors = abs(len(reference) - len(recovered))
    for a, b in zip(reference, recovered):
        errors += int(int(a) != int(b))
    return errors / n


def text_match_rate(reference, recovered):
    n = max(len(reference), len(recovered))
    if n == 0:
        return 1.0
    matches = sum(1 for a, b in zip(reference, recovered) if a == b)
    return matches / n


def save_constellation(symbols, output_dir):
    arr = np.asarray(symbols, dtype=complex)
    sample = arr[: min(len(arr), 2000)]
    plt.figure(figsize=(5, 5))
    plt.scatter(sample.real, sample.imag, s=8, alpha=0.45)
    plt.axhline(0, color="black", linewidth=0.7)
    plt.axvline(0, color="black", linewidth=0.7)
    plt.xlabel("In-phase")
    plt.ylabel("Quadrature")
    plt.title("QPSK Constellation after AWGN")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / "constellation.png", dpi=150)
    plt.close()


def save_sync_peak(correlation, start_index, output_dir):
    corr = np.asarray(correlation, dtype=float)
    plt.figure(figsize=(7, 4))
    if corr.size:
        plt.plot(corr)
        plt.axvline(int(start_index), color="red", linestyle="--", label="Detected start")
        plt.legend()
    plt.xlabel("Candidate symbol index")
    plt.ylabel("Correlation magnitude")
    plt.title("Synchronization Correlation Peak")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / "sync_peak.png", dpi=150)
    plt.close()


def save_ber_curve(source_bits, frame_bits, seed, output_dir):
    snrs = [0, 3, 6, 9, 12, 15]
    preamble_symbols = qpsk_modulate(PREAMBLE_BITS)
    tx_symbols = qpsk_modulate(frame_bits)
    bers = []
    for snr in snrs:
        noisy = awgn(tx_symbols, snr_db=snr, seed=seed)
        sync_info = synchronize(noisy, preamble=preamble_symbols)
        start = int(sync_info["start_index"])
        rx_frame_symbols = noisy[start : start + len(tx_symbols)]
        parsed = parse_frame(qpsk_demodulate(rx_frame_symbols))
        decoded = channel_decode(parsed["payload"])
        recovered_bits = descramble(decoded, seed=seed)[: len(source_bits)]
        bers.append(bit_error_rate(source_bits, recovered_bits))

    plt.figure(figsize=(6, 4))
    plt.semilogy(snrs, np.maximum(bers, 1e-6), marker="o")
    plt.xlabel("SNR (dB)")
    plt.ylabel("BER")
    plt.title("BER-SNR Curve")
    plt.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / "ber_curve.png", dpi=150)
    plt.close()


def run_chain(input_path, output_path, snr_db, seed, modulation, channel_name):
    if modulation.lower() != "qpsk":
        raise ValueError("Baseline implementation supports --mod qpsk")
    if channel_name.lower() != "awgn":
        raise ValueError("Baseline implementation supports --channel awgn")

    input_path = Path(input_path)
    output_path = Path(output_path)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    text = input_path.read_text(encoding="utf-8")
    source_bits = source_encode(text)
    scrambled_bits = scramble(source_bits, seed=seed)
    coded_bits = channel_encode(scrambled_bits)
    frame_bits = build_frame(coded_bits, original_length=len(source_bits), checksum_bits=source_bits)

    tx_symbols = qpsk_modulate(frame_bits)
    rng = np.random.default_rng(int(seed) + 99)
    leading_symbols = int(rng.integers(0, 129))
    prefix = (
        rng.normal(size=leading_symbols) + 1j * rng.normal(size=leading_symbols)
    ) / np.sqrt(2.0)
    channel_input = np.concatenate([prefix, tx_symbols])
    rx_symbols = awgn(channel_input, snr_db=snr_db, seed=seed)

    preamble_symbols = qpsk_modulate(PREAMBLE_BITS)
    sync_info = synchronize(rx_symbols, preamble=preamble_symbols)
    start = int(sync_info["start_index"])
    rx_frame_symbols = rx_symbols[start : start + len(tx_symbols)]

    recovered_frame_bits = qpsk_demodulate(rx_frame_symbols)
    parsed = parse_frame(recovered_frame_bits)
    decoded_bits = channel_decode(parsed["payload"])
    recovered_source_bits = descramble(decoded_bits, seed=seed)[: len(source_bits)]

    try:
        recovered_text = source_decode(recovered_source_bits)
    except Exception:
        recovered_text = ""
    output_path.write_text(recovered_text, encoding="utf-8")

    checksum_pass = checksum32(recovered_source_bits[: len(source_bits)]) == checksum32(source_bits)
    ber = bit_error_rate(source_bits, recovered_source_bits)
    match_rate = text_match_rate(text, recovered_text)
    metrics = {
        "snr_db": float(snr_db),
        "seed": int(seed),
        "modulation": modulation.lower(),
        "channel": channel_name.lower(),
        "payload_bits": len(source_bits),
        "ber": float(ber),
        "fer": 0.0 if checksum_pass and recovered_text == text else 1.0,
        "text_match_rate": float(match_rate),
        "checksum_pass": bool(checksum_pass and recovered_text == text),
        "crc_pass": bool(checksum_pass),
        "sync_start_index": start,
        "simulated_prefix_symbols": leading_symbols,
        "coding_scheme": "convolutional(7,5)+viterbi",
        "snr_definition": "average QPSK symbol power divided by average complex AWGN noise power",
    }
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    save_constellation(rx_frame_symbols, output_dir)
    save_sync_peak(sync_info.get("correlation", []), start, output_dir)
    save_ber_curve(source_bits, frame_bits, seed, output_dir)
    return metrics


def parse_args():
    parser = argparse.ArgumentParser(description="Wireless file transfer baseband simulator")
    parser.add_argument("--input", required=True, help="Input UTF-8 text file")
    parser.add_argument("--output", required=True, help="Recovered output text file")
    parser.add_argument("--snr", type=float, default=12.0, help="AWGN SNR in dB")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    parser.add_argument("--mod", default="qpsk", help="Modulation, baseline qpsk")
    parser.add_argument("--channel", default="awgn", help="Channel, baseline awgn")
    return parser.parse_args()


def main():
    args = parse_args()
    metrics = run_chain(args.input, args.output, args.snr, args.seed, args.mod, args.channel)
    print(json.dumps(metrics, ensure_ascii=False))


if __name__ == "__main__":
    main()
