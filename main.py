import argparse
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.source import source_encode, source_decode
from src.scramble import get_scramble
from src.fec import get_fec
from src.framing import build_frame, parse_frame, xor_checksum
from src.modulation import (
    qpsk_modulate, qpsk_demodulate,
    bpsk_modulate, bpsk_demodulate,
    qam16_modulate, qam16_demodulate,
)

MODULATION_MAP = {
    "bpsk": (bpsk_modulate, bpsk_demodulate),
    "qpsk": (qpsk_modulate, qpsk_demodulate),
    "16qam": (qam16_modulate, qam16_demodulate),
}
from src.channel import get_channel, awgn
from src.checksum import get_checksum_fn, get_checksum_len
from src.synchronization import detect_frame_start


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def calculate_metrics(orig_bits: list[int], recv_bits: list[int]) -> dict:
    min_len = min(len(orig_bits), len(recv_bits))
    if min_len == 0:
        return {"ber": 1.0, "fer": 1.0}
    errors = sum(a != b for a, b in zip(orig_bits[:min_len], recv_bits[:min_len]))
    ber = errors / min_len
    fer = 1.0 if errors > 0 else 0.0
    return {"ber": ber, "fer": fer, "bit_errors": errors, "total_bits": min_len}


def ber_curve(args, payload_bits: list[int], frame_bits: list[int],
              fec_decode_fn, descramble_fn) -> None:
    modulate_fn, demodulate_fn = MODULATION_MAP[args.mod]
    bits_per_symbol = {"bpsk": 1, "qpsk": 2, "16qam": 4}[args.mod]
    snr_values = np.arange(0, 13, 2)
    bers = []
    for snr in snr_values:
        rx_noisy = awgn(
            modulate_fn(frame_bits), float(snr), args.seed
        )
        sync_idx = detect_frame_start(rx_noisy, modulation=args.mod)
        rx_frame_len = len(frame_bits) // bits_per_symbol
        rx_frame = rx_noisy[sync_idx:sync_idx + rx_frame_len]
        rx_bits = demodulate_fn(rx_frame)
        rx_payload, _ = parse_frame(rx_bits)
        rx_decoded = fec_decode_fn(rx_payload)
        rx_descrambled = descramble_fn(rx_decoded, args.seed)
        metrics = calculate_metrics(payload_bits, rx_descrambled[:len(payload_bits)])
        bers.append(metrics["ber"])
    plt.figure()
    plt.semilogy(snr_values, bers, "bo-")
    plt.xlabel("SNR (dB)")
    plt.ylabel("BER")
    plt.grid(True)
    plt.savefig("results/ber_curve.png", dpi=150)
    plt.close()


def plot_constellation(rx_symbols: list[complex]) -> None:
    plt.figure()
    plt.scatter([s.real for s in rx_symbols], [s.imag for s in rx_symbols],
                s=8, alpha=0.6)
    plt.axhline(0, color="gray", linewidth=0.5)
    plt.axvline(0, color="gray", linewidth=0.5)
    plt.xlabel("In-phase")
    plt.ylabel("Quadrature")
    plt.axis("equal")
    plt.grid(True)
    plt.savefig("results/constellation.png", dpi=150)
    plt.close()


def plot_sync_peak(symbols: list[complex], modulation: str = "qpsk") -> None:
    from src.synchronization import _PREAMBLE_MAP
    preamble = _PREAMBLE_MAP.get(modulation, _PREAMBLE_MAP["qpsk"])
    sym_arr = np.array(symbols, dtype=complex)
    corr = np.correlate(sym_arr, preamble, mode="valid")
    plt.figure()
    plt.plot(np.abs(corr))
    plt.xlabel("Symbol offset")
    plt.ylabel("Correlation magnitude")
    plt.grid(True)
    plt.savefig("results/sync_peak.png", dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Wireless Communication System Simulation"
    )
    parser.add_argument("--input", default="Test.txt")
    parser.add_argument("--output", default="results/received.txt")
    parser.add_argument("--snr", type=float, default=12.0)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--mod", default="qpsk", choices=["bpsk", "qpsk", "16qam"])
    parser.add_argument("--channel", default="awgn")
    parser.add_argument("--fec", default="hamming")
    parser.add_argument("--checksum", default="xor8")
    parser.add_argument("--scramble", default="pn")
    args = parser.parse_args()

    fec_scheme = get_fec(args.fec)
    fec_encode, fec_decode = fec_scheme["encode"], fec_scheme["decode"]
    scramble_fn, descramble_fn = get_scramble(args.scramble)
    channel_fn = get_channel(args.channel)
    checksum_fn = get_checksum_fn(args.checksum)
    cs_len = get_checksum_len(args.checksum)

    text = read_text(args.input)
    payload_bits = source_encode(text)
    scrambled = scramble_fn(payload_bits, args.seed)
    data_checksum = checksum_fn(scrambled)
    coded = fec_encode(scrambled)
    frame_bits = build_frame(coded, data_checksum)
    modulate_fn, demodulate_fn = MODULATION_MAP[args.mod]
    tx_symbols = modulate_fn(frame_bits)
    rx_symbols = channel_fn(tx_symbols, args.snr, args.seed)

    sync_index = detect_frame_start(rx_symbols, modulation=args.mod)
    frame_rx_symbols = rx_symbols[sync_index:sync_index + len(tx_symbols)]
    frame_rx_bits = demodulate_fn(frame_rx_symbols)
    rx_coded, frame_meta = parse_frame(frame_rx_bits, cs_len)
    rx_scrambled = fec_decode(rx_coded)
    rx_bits = descramble_fn(rx_scrambled, args.seed)
    recovered_text = source_decode(rx_bits[:len(payload_bits)])

    write_text(args.output, recovered_text)

    checksum_pass = checksum_fn(rx_scrambled) == frame_meta.get("checksum_bits", [])
    metrics = calculate_metrics(payload_bits, rx_bits[:len(payload_bits)])
    text_match = 1.0 if recovered_text == text else 0.0
    metrics_json = {
        "snr_db": args.snr,
        "seed": args.seed,
        "modulation": args.mod,
        "channel": args.channel,
        "payload_bits": len(payload_bits),
        "ber": metrics["ber"],
        "fer": metrics["fer"],
        "text_match_rate": text_match,
        "checksum_pass": checksum_pass,
        "sync_start_index": sync_index,
        "fec": args.fec,
        "checksum": args.checksum,
        "scramble": args.scramble,
    }
    os.makedirs("results", exist_ok=True)
    with open("results/metrics.json", "w") as f:
        json.dump(metrics_json, f, indent=2)

    plot_constellation(rx_symbols)
    plot_sync_peak(rx_symbols, modulation=args.mod)
    ber_curve(args, payload_bits, frame_bits, fec_decode, descramble_fn)

    print(f"BER: {metrics['ber']:.6f}, FER: {metrics['fer']:.2f}, "
          f"Text match: {text_match:.2f}, Sync: {sync_index}")


if __name__ == "__main__":
    main()
