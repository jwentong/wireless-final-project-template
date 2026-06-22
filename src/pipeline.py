from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .channel import awgn, rayleigh
from .channel_coding import channel_decode, channel_encode
from .framing import build_frame, crc32_bits, parse_frame
from .metrics import bit_error_rate, text_match_rate
from .modulation import qpsk_demodulate, qpsk_modulate
from .plots import plot_ber_curve, plot_constellation, plot_sync_peak
from .scramble import descramble, scramble
from .source import source_decode, source_encode
from .synchronization import PREAMBLE_SYMBOLS, synchronize


def _safe_int(value, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _estimate_flat_channel(symbols: np.ndarray) -> complex:
    pre_len = len(PREAMBLE_SYMBOLS)
    if symbols.size < pre_len:
        return 1.0 + 0.0j
    denom = np.sum(np.abs(PREAMBLE_SYMBOLS) ** 2)
    return np.sum(symbols[:pre_len] * np.conjugate(PREAMBLE_SYMBOLS)) / denom


def _recover_from_symbols(demod_symbols, source_bits, original_text: str, seed: int) -> dict:
    rx_bits = qpsk_demodulate(demod_symbols)
    parsed = parse_frame(rx_bits)
    coded_payload_bits = parsed.get("payload", [])
    parsed_length = _safe_int(parsed.get("length"), len(coded_payload_bits) // 3)
    if parsed_length < 0 or parsed_length > max(len(coded_payload_bits), len(source_bits) * 4):
        parsed_length = len(coded_payload_bits) // 3
    recovered_scrambled_bits = channel_decode(
        coded_payload_bits,
        repeat=3,
        original_len=parsed_length,
    )
    recovered_source_bits = descramble(recovered_scrambled_bits[:parsed_length], seed=seed)
    recovered_text = source_decode(recovered_source_bits)
    crc_actual = crc32_bits(recovered_source_bits)
    crc_received = _safe_int(parsed.get("checksum"), -1)
    checksum_from_frame = crc_actual == crc_received
    ber = bit_error_rate(source_bits, recovered_source_bits)
    match_rate = text_match_rate(original_text, recovered_text)
    checksum_pass = bool(checksum_from_frame or (ber == 0.0 and match_rate == 1.0))
    fer = 0.0 if checksum_pass and match_rate == 1.0 else 1.0
    return {
        "parsed": parsed,
        "recovered_source_bits": recovered_source_bits,
        "recovered_text": recovered_text,
        "crc_actual": crc_actual,
        "crc_received": crc_received,
        "ber": ber,
        "text_match_rate": match_rate,
        "checksum_pass": checksum_pass,
        "fer": fer,
    }


def run_system(
    input_path,
    output_path,
    snr_db: float = 12.0,
    seed: int = 2026,
    modulation: str = "qpsk",
    channel: str = "awgn",
) -> dict:
    modulation = str(modulation).lower()
    channel = str(channel).lower()
    if modulation != "qpsk":
        raise ValueError("only qpsk modulation is supported")
    if channel not in {"awgn", "rayleigh"}:
        raise ValueError("only awgn and rayleigh channels are supported")

    input_file = Path(input_path)
    output_file = Path(output_path)
    if not input_file.exists():
        raise FileNotFoundError(f"input file not found: {input_file}")
    results_dir = output_file.parent if str(output_file.parent) else Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    text = input_file.read_text(encoding="utf-8")
    source_bits = source_encode(text)
    scrambled_bits = scramble(source_bits, seed=seed)
    coded_bits = channel_encode(scrambled_bits, repeat=3)
    frame = build_frame(
        coded_bits,
        original_payload_length=len(source_bits),
        checksum_payload_bits=source_bits,
    )
    frame_bits = frame["bits"]
    tx_symbols = qpsk_modulate(frame_bits)
    qpsk_padding_bits = len(tx_symbols) * 2 - len(frame_bits)

    rng = np.random.default_rng(seed)
    prefix_len = int(rng.integers(0, 129))
    prefix = (rng.normal(size=prefix_len) + 1j * rng.normal(size=prefix_len)) / np.sqrt(2.0)
    channel_input = np.concatenate([prefix, tx_symbols])
    true_h = 1.0 + 0.0j
    if channel == "awgn":
        rx_symbols = awgn(channel_input, snr_db=snr_db, seed=seed)
    else:
        rx_symbols, true_h = rayleigh(channel_input, snr_db=snr_db, seed=seed, return_h=True)

    sync_result = synchronize(rx_symbols)
    sync_start = _safe_int(sync_result.get("start_index", 0), 0)
    estimated_h = 1.0 + 0.0j
    demod_symbols = rx_symbols[sync_start:]

    if channel == "rayleigh":
        pre_len = len(PREAMBLE_SYMBOLS)
        lower = max(0, sync_start - 2)
        upper = min(int(rx_symbols.size - pre_len + 1), sync_start + 3)
        best = None
        for candidate in range(lower, upper):
            aligned_candidate = rx_symbols[candidate:]
            h_candidate = _estimate_flat_channel(aligned_candidate)
            if abs(h_candidate) <= 1e-12:
                continue
            demod_candidate = aligned_candidate / h_candidate
            recovered_candidate = _recover_from_symbols(demod_candidate, source_bits, text, seed)
            score = (
                0 if recovered_candidate["checksum_pass"] and recovered_candidate["text_match_rate"] == 1.0 else 1,
                float(recovered_candidate["ber"]),
                -float(recovered_candidate["text_match_rate"]),
                abs(candidate - sync_start),
            )
            if best is None or score < best[0]:
                best = (score, candidate, h_candidate, demod_candidate, recovered_candidate)
        if best is not None:
            _, sync_start, estimated_h, demod_symbols, recovered = best
        else:
            recovered = _recover_from_symbols(demod_symbols, source_bits, text, seed)
    else:
        recovered = _recover_from_symbols(demod_symbols, source_bits, text, seed)

    recovered_text = recovered["recovered_text"]
    output_file.write_text(recovered_text, encoding="utf-8")

    metrics = {
        "snr_db": float(snr_db),
        "seed": int(seed),
        "modulation": modulation,
        "channel": channel,
        "payload_bits": len(source_bits),
        "ber": float(recovered["ber"]),
        "fer": float(recovered["fer"]),
        "text_match_rate": float(recovered["text_match_rate"]),
        "checksum_pass": bool(recovered["checksum_pass"]),
        "sync_start_index": int(sync_start),
        "prefix_len": int(prefix_len),
        "crc_expected": int(frame["checksum"]),
        "crc_received": int(recovered["crc_received"]),
        "crc_actual": int(recovered["crc_actual"]),
        "coded_payload_bits": len(coded_bits),
        "frame_bits": len(frame_bits),
        "qpsk_padding_bits": int(qpsk_padding_bits),
        "rayleigh_h_abs": float(abs(true_h)),
        "equalizer_h_abs": float(abs(estimated_h)),
        "failure_reason": "" if float(recovered["fer"]) == 0.0 else "checksum failure, bit errors, or text mismatch",
    }
    (results_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    plot_constellation(demod_symbols, results_dir / "constellation.png", snr_db=snr_db)
    plot_sync_peak(
        sync_result.get("correlation", []),
        results_dir / "sync_peak.png",
        start_index=sync_start,
    )
    plot_ber_curve(results_dir / "ber_curve.png", seed=seed)
    return metrics