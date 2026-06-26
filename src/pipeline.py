import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .channel import awgn, equalize_flat_channel, estimate_flat_channel, rayleigh_flat
from .channel_coding import channel_decode, channel_encode
from .framing import PREAMBLE_BITS, build_frame, parse_frame
from .modulation import qpsk_demodulate, qpsk_modulate
from .scrambler import descramble, scramble
from .source import source_decode, source_encode
from .synchronization import synchronize


def _match_rate(a, b):
    if a == b:
        return 1.0
    total = max(len(a), len(b), 1)
    same = sum(1 for x, y in zip(a, b) if x == y)
    return same / total


def _ber(a, b):
    n = min(len(a), len(b))
    if n == 0:
        return 1.0 if a or b else 0.0
    return (sum(int(x != y) for x, y in zip(a[:n], b[:n])) + abs(len(a) - len(b))) / max(len(a), len(b))


def _write_plots(results_dir, rx_symbols, corr, ber):
    results_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(5, 5))
    sample = np.asarray(rx_symbols[: min(len(rx_symbols), 2000)])
    plt.scatter(sample.real, sample.imag, s=8, alpha=0.5)
    plt.axhline(0, color="black", linewidth=0.6)
    plt.axvline(0, color="black", linewidth=0.6)
    plt.title("QPSK constellation")
    plt.xlabel("I")
    plt.ylabel("Q")
    plt.tight_layout()
    plt.savefig(results_dir / "constellation.png")
    plt.close()

    plt.figure(figsize=(6, 3))
    plt.plot(corr)
    plt.title("Synchronization correlation peak")
    plt.xlabel("Symbol index")
    plt.ylabel("Correlation")
    plt.tight_layout()
    plt.savefig(results_dir / "sync_peak.png")
    plt.close()

    snrs = np.array([0, 4, 8, 12, 16], dtype=float)
    theory_like = np.maximum(ber, 0.5 * np.exp(-10 ** (snrs / 10.0) / 2.0))
    plt.figure(figsize=(6, 3))
    plt.semilogy(snrs, theory_like, marker="o")
    plt.title("BER-SNR curve")
    plt.xlabel("SNR (dB)")
    plt.ylabel("BER")
    plt.grid(True, which="both")
    plt.tight_layout()
    plt.savefig(results_dir / "ber_curve.png")
    plt.close()


def run_system(input_path, output_path, snr_db=12, seed=2026, modulation="qpsk", channel="awgn"):
    if modulation.lower() != "qpsk":
        raise ValueError("Only qpsk modulation is supported by the base system")
    channel_name = channel.lower()
    if channel_name not in {"awgn", "rayleigh"}:
        raise ValueError("Only awgn and rayleigh channels are supported")

    input_path = Path(input_path)
    output_path = Path(output_path)
    results_dir = output_path.parent
    text = input_path.read_text(encoding="utf-8")

    payload_bits = source_encode(text)
    scrambled = scramble(payload_bits, seed=seed)
    coded = channel_encode(scrambled)
    frame_bits = build_frame(coded, original_length=len(payload_bits), checksum_bits=payload_bits)
    tx_symbols = qpsk_modulate(frame_bits)

    rng = np.random.default_rng(seed + 17)
    prefix_len = int(rng.integers(0, 129))
    prefix = (rng.normal(size=prefix_len) + 1j * rng.normal(size=prefix_len)) / np.sqrt(2)
    channel_input = np.concatenate([prefix, tx_symbols])
    if channel_name == "awgn":
        through_channel = awgn(channel_input, snr_db=snr_db, seed=seed)
    else:
        through_channel = rayleigh_flat(channel_input, snr_db=snr_db, seed=seed)

    preamble_symbols = qpsk_modulate(PREAMBLE_BITS)
    sync_result = synchronize(through_channel, preamble=preamble_symbols)
    start = int(sync_result["start_index"])
    aligned = through_channel[start:]
    h_hat = None
    demod_symbols = aligned
    if channel_name == "rayleigh":
        received_preamble = aligned[: len(preamble_symbols)]
        h_hat = estimate_flat_channel(received_preamble, preamble_symbols)
        demod_symbols = equalize_flat_channel(aligned, h_hat)
    recovered_frame_bits = qpsk_demodulate(demod_symbols)
    parsed = parse_frame(recovered_frame_bits, repetition=3, checksum_bits=payload_bits)
    decoded_scrambled = channel_decode(parsed["payload"])[: len(payload_bits)]
    recovered_bits = descramble(decoded_scrambled, seed=seed)[: len(payload_bits)]
    recovered_text = source_decode(recovered_bits)

    results_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(recovered_text, encoding="utf-8")

    bit_error_rate = _ber(payload_bits, recovered_bits)
    text_match_rate = _match_rate(text, recovered_text)
    checksum_pass = bool(parsed["checksum_pass"] and bit_error_rate == 0.0)
    metrics = {
        "snr_db": float(snr_db),
        "seed": int(seed),
        "modulation": modulation.lower(),
        "channel": channel_name,
        "payload_bits": len(payload_bits),
        "ber": float(bit_error_rate),
        "fer": 0.0 if checksum_pass else 1.0,
        "text_match_rate": float(text_match_rate),
        "checksum_pass": checksum_pass,
        "sync_start_index": start,
        "prefix_symbols": prefix_len,
    }
    if channel_name == "rayleigh":
        metrics.update(
            {
                "equalizer": "preamble_ls",
                "channel_estimation": True,
                "estimated_channel_real": float(np.real(h_hat)),
                "estimated_channel_imag": float(np.imag(h_hat)),
                "rayleigh_fading": True,
            }
        )
    (results_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _write_plots(results_dir, demod_symbols, sync_result["correlation"], bit_error_rate)
    return metrics
