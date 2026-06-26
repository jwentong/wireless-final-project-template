"""End-to-end wireless file transmission pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .channel import add_prefix, awgn, one_tap_equalize, rayleigh_fading_channel
from .channel_codec import repetition_decode, repetition_encode
from .frame import build_frame, crc32_from_payload_bits, parse_frame
from .metrics import build_metrics, write_metrics
from .modulation import qpsk_demodulate, qpsk_modulate
from .plots import generate_plots
from .scrambler import descramble_bits, scramble_bits
from .source_codec import source_encode
from .synchronization import detect_frame_start, preamble_symbols
from .utils import ensure_parent_dir, safe_bits_to_text


def _choose_prefix_offset(seed: int, max_offset: int = 128) -> int:
    rng = np.random.default_rng(seed)
    return int(rng.integers(0, max_offset + 1))


def run_pipeline(
    *,
    input_path: str | Path,
    output_path: str | Path,
    snr_db: float,
    seed: int,
    modulation: str = "qpsk",
    channel: str = "awgn",
    make_plots: bool = True,
) -> dict[str, object]:
    if modulation.lower() != "qpsk":
        raise ValueError("only qpsk modulation is supported")
    channel_name = channel.lower()
    if channel_name not in {"awgn", "rayleigh"}:
        raise ValueError("only awgn and rayleigh channels are supported")

    input_file = Path(input_path)
    output_file = ensure_parent_dir(output_path)
    results_dir = output_file.parent
    metrics_path = results_dir / "metrics.json"

    original_text = input_file.read_bytes().decode("utf-8")
    payload_bits = source_encode(original_text)
    crc_expected = crc32_from_payload_bits(payload_bits)

    recovered_bits: list[int] = []
    recovered_text = ""
    checksum_pass = False
    sync_start_index: int | None = None
    sync_peak_value: float | None = None
    sync_correlation = None
    crc_received: int | None = None
    failure_reason: str | None = None

    scrambled = scramble_bits(payload_bits, seed=seed)
    encoded_payload = repetition_encode(scrambled)
    frame_bits = build_frame(
        encoded_payload,
        payload_bit_length=len(payload_bits),
        checksum=crc_expected,
    )
    tx_symbols = qpsk_modulate(frame_bits)

    prefix_offset = _choose_prefix_offset(seed)
    prefixed_symbols = add_prefix(tx_symbols, offset_symbols=prefix_offset, seed=seed + 1000)
    metrics_extra: dict[str, object]
    if channel_name == "rayleigh":
        faded_symbols, fading_coefficients = rayleigh_fading_channel(
            prefixed_symbols,
            snr_db=snr_db,
            seed=seed + 2000,
        )
        rx_symbols = one_tap_equalize(faded_symbols, fading_coefficients)
        plot_symbols = rx_symbols
        metrics_extra = {
            "equalization": "one-tap",
            "fading_model": "flat_rayleigh",
            "rayleigh_enabled": True,
            "channel_estimation": "known_h_simulation",
            "comparison_note": "Rayleigh mode applies known-channel one-tap equalization before synchronization.",
        }
    else:
        rx_symbols = awgn(prefixed_symbols, snr_db=snr_db, seed=seed + 2000)
        plot_symbols = rx_symbols
        metrics_extra = {
            "equalization": "none",
            "fading_model": None,
            "rayleigh_enabled": False,
            "channel_estimation": "not_applicable",
        }

    try:
        preamble_ref = preamble_symbols()
        sync_search_symbols = rx_symbols[: 129 + len(preamble_ref) - 1]
        sync_result = detect_frame_start(sync_search_symbols, preamble=preamble_ref)
        sync_start_index = int(sync_result["start_index"])
        sync_peak_value = float(sync_result["peak_value"])
        sync_correlation = sync_result["correlation"]

        aligned_symbols = rx_symbols[sync_start_index : sync_start_index + len(tx_symbols)]
        demod_bits = qpsk_demodulate(aligned_symbols)[: len(frame_bits)]
        parsed = parse_frame(demod_bits, require_preamble=False)
        payload_length = int(parsed["length"])
        encoded_length = payload_length * 3
        encoded_rx = list(parsed["encoded_payload"])[:encoded_length]
        decoded_scrambled = repetition_decode(encoded_rx)
        recovered_bits = descramble_bits(decoded_scrambled, seed=seed)[:payload_length]
        recovered_text, decode_failure = safe_bits_to_text(recovered_bits)
        crc_received = crc32_from_payload_bits(recovered_bits)
        checksum_pass = crc_received == int(parsed["checksum"])

        if decode_failure is not None:
            failure_reason = decode_failure
        if sync_start_index != prefix_offset and failure_reason is None:
            failure_reason = "synchronization_offset_mismatch"
        if not checksum_pass and failure_reason is None:
            failure_reason = "checksum_failed"
        if recovered_text != original_text and failure_reason is None:
            failure_reason = "text_mismatch"
    except Exception as exc:  # low-SNR runs should still produce artifacts
        recovered_text = ""
        failure_reason = f"{type(exc).__name__}: {exc}"

    output_file.write_bytes(recovered_text.encode("utf-8"))

    metrics = build_metrics(
        snr_db=snr_db,
        seed=seed,
        modulation=modulation.lower(),
        channel=channel_name,
        original_bits=payload_bits,
        recovered_bits=recovered_bits,
        original_text=original_text,
        recovered_text=recovered_text,
        checksum_pass=checksum_pass,
        sync_start_index=sync_start_index,
        prefix_offset_symbols=prefix_offset,
        crc_expected=crc_expected,
        crc_received=crc_received,
        sync_peak_value=sync_peak_value,
        failure_reason=failure_reason,
        extra_fields=metrics_extra,
    )
    write_metrics(metrics, metrics_path)

    plot_files: list[str] = []
    if make_plots:
        try:
            plot_files = generate_plots(
                results_dir=results_dir,
                received_symbols=plot_symbols,
                correlation=sync_correlation,
                seed=seed,
            )
        except Exception as exc:
            metrics["failure_reason"] = (
                f"{metrics['failure_reason']}; plot_error: {exc}"
                if metrics["failure_reason"]
                else f"plot_error: {exc}"
            )
            write_metrics(metrics, metrics_path)

    metrics["plot_files"] = plot_files
    write_metrics(metrics, metrics_path)
    if channel_name == "rayleigh":
        write_metrics(metrics, results_dir / "metrics_rayleigh.json")
    return metrics
