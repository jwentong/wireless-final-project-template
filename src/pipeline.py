import json
import zlib
from pathlib import Path

from .channel import (
    add_awgn_with_offset,
    estimate_flat_fading,
    rayleigh_channel_with_offset,
    zf_equalize,
)
from .channel_code import repetition_decode, repetition_encode
from .convolutional import convolutional_encode, viterbi_decode
from .frame import build_frame, crc32_bits, find_frame_start, parse_frame_bits, preamble_bits
from .metrics import bit_error_rate, text_match_rate
from .modulation import qpsk_demodulate, qpsk_modulate
from .plots import constellation, line_plot
from .scrambler import descramble_bits, scramble_bits
from .source import bits_to_bytes, bits_to_text, text_to_bits


def _encode_payload(bits: list[int], fec: str) -> list[int]:
    if fec == "repetition":
        return repetition_encode(bits, 3)
    if fec == "conv":
        return convolutional_encode(bits)
    raise ValueError("supported --fec values are repetition and conv")


def _decode_payload(bits: list[int], fec: str) -> list[int]:
    if fec == "repetition":
        return repetition_decode(bits, 3)
    if fec == "conv":
        return viterbi_decode(bits)
    raise ValueError("supported --fec values are repetition and conv")


def _simulate_once(
    text: str,
    snr: float,
    seed: int,
    collect_debug: bool = False,
    channel_mode: str = "awgn",
    fec: str = "repetition",
) -> dict:
    payload_bits, payload_bytes = text_to_bits(text)
    scrambled = scramble_bits(payload_bits, seed)
    encoded_payload = _encode_payload(scrambled, fec)
    frame_bits = build_frame(encoded_payload, len(payload_bits), zlib.crc32(payload_bytes) & 0xFFFFFFFF)
    qpsk_padding = len(frame_bits) % 2
    tx_symbols = qpsk_modulate(frame_bits)
    channel_gain = complex(1.0, 0.0)
    estimated_gain = complex(1.0, 0.0)
    if channel_mode == "awgn":
        rx_symbols, true_offset = add_awgn_with_offset(tx_symbols, snr, seed)
    elif channel_mode == "rayleigh":
        rx_symbols, true_offset, channel_gain = rayleigh_channel_with_offset(tx_symbols, snr, seed)
    else:
        raise ValueError("supported --channel values are awgn and rayleigh")
    sync_start, sync_peaks = find_frame_start(rx_symbols)

    frame_symbol_count = len(tx_symbols)
    useful_symbols = rx_symbols[sync_start : sync_start + frame_symbol_count]
    if channel_mode == "rayleigh":
        known_preamble_symbols = qpsk_modulate(preamble_bits())
        received_preamble = useful_symbols[: len(known_preamble_symbols)]
        estimated_gain = estimate_flat_fading(received_preamble, known_preamble_symbols)
        useful_symbols = zf_equalize(useful_symbols, estimated_gain)
    received_frame_bits = qpsk_demodulate(useful_symbols)[: len(frame_bits)]
    preamble_len = len(preamble_bits())
    body_bits = received_frame_bits[preamble_len:]

    recovered_bits: list[int] = []
    checksum_pass = False
    recovered_text = ""
    payload_length = 0
    received_crc = 0
    failure_reason = ""
    try:
        payload_length, received_crc, encoded_rx_payload = parse_frame_bits(body_bits)
        decoded_scrambled = _decode_payload(encoded_rx_payload, fec)
        decoded_payload = descramble_bits(decoded_scrambled, seed)[:payload_length]
        recovered_bits = decoded_payload
        recovered_text = bits_to_text(decoded_payload, errors="replace")
        checksum_pass = (zlib.crc32(bits_to_bytes(decoded_payload)) & 0xFFFFFFFF) == received_crc
    except Exception as exc:
        failure_reason = str(exc)
        recovered_text = ""
        recovered_bits = []

    ber = bit_error_rate(payload_bits, recovered_bits)
    match_rate = text_match_rate(text, recovered_text)
    fer = 0.0 if checksum_pass and recovered_text == text else 1.0
    result = {
        "text": recovered_text,
        "payload_bits": len(payload_bits),
        "ber": ber,
        "fer": fer,
        "text_match_rate": match_rate,
        "checksum_pass": checksum_pass,
        "sync_start_index": sync_start,
        "true_sync_offset": true_offset,
        "sync_error_symbols": abs(sync_start - true_offset),
        "qpsk_padding_bits": qpsk_padding,
        "decoded_payload_length": payload_length,
        "decoded_crc32": received_crc,
        "failure_reason": failure_reason,
        "channel_gain_real": channel_gain.real,
        "channel_gain_imag": channel_gain.imag,
        "estimated_gain_real": estimated_gain.real,
        "estimated_gain_imag": estimated_gain.imag,
    }
    if collect_debug:
        result["tx_symbols"] = tx_symbols
        result["rx_symbols"] = rx_symbols
        result["sync_peaks"] = sync_peaks
    return result


def run_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    snr: float,
    seed: int,
    mod: str = "qpsk",
    channel: str = "awgn",
    fec: str = "repetition",
) -> dict:
    if mod.lower() != "qpsk":
        raise ValueError("base system only supports --mod qpsk")
    channel_mode = channel.lower()
    if channel_mode not in {"awgn", "rayleigh"}:
        raise ValueError("supported --channel values are awgn and rayleigh")
    fec_mode = fec.lower()

    input_path = Path(input_path)
    output_path = Path(output_path)
    result_dir = output_path.parent
    result_dir.mkdir(parents=True, exist_ok=True)

    text = input_path.read_text(encoding="utf-8")
    result = _simulate_once(text, snr, seed, collect_debug=True, channel_mode=channel_mode, fec=fec_mode)
    output_path.write_text(result["text"], encoding="utf-8")

    constellation(result_dir / "constellation.png", result["rx_symbols"])
    snrs = [0, 3, 6, 9, 12, 15]
    bers = [
        _simulate_once(text, value, seed, collect_debug=False, channel_mode=channel_mode, fec=fec_mode)["ber"]
        for value in snrs
    ]
    line_plot(result_dir / "ber_curve.png", snrs, bers, log_y=True)
    line_plot(result_dir / "sync_peak.png", list(range(len(result["sync_peaks"]))), result["sync_peaks"], log_y=False)

    enabled_level3_modules: list[str] = []
    if channel_mode == "rayleigh":
        enabled_level3_modules.extend(["rayleigh_flat_fading", "zero_forcing_equalization"])
    if fec_mode == "conv":
        enabled_level3_modules.append("convolutional_viterbi")

    metrics = {
        "snr_db": snr,
        "seed": seed,
        "modulation": mod.lower(),
        "channel": channel_mode,
        "payload_bits": result["payload_bits"],
        "ber": result["ber"],
        "fer": result["fer"],
        "text_match_rate": result["text_match_rate"],
        "checksum_pass": result["checksum_pass"],
        "sync_start_index": result["sync_start_index"],
        "true_sync_offset": result["true_sync_offset"],
        "sync_error_symbols": result["sync_error_symbols"],
        "qpsk_mapping": "00=(1+j)/sqrt(2), 01=(-1+j)/sqrt(2), 11=(-1-j)/sqrt(2), 10=(1-j)/sqrt(2)",
        "channel_code": "repetition-3" if fec_mode == "repetition" else "convolutional(7,5)-viterbi",
        "scrambler": "PN XOR",
        "snr_definition": "average received QPSK symbol power / complex AWGN noise power",
        "qpsk_padding_bits": result["qpsk_padding_bits"],
        "failure_reason": result["failure_reason"],
        "fec": fec_mode,
        "level3_modules": enabled_level3_modules,
        "available_level3_modules": [
            "rayleigh_flat_fading",
            "zero_forcing_equalization",
            "convolutional_viterbi",
        ],
        "equalizer": "ZF" if channel_mode == "rayleigh" else "not_required_for_awgn",
        "channel_gain_real": result["channel_gain_real"],
        "channel_gain_imag": result["channel_gain_imag"],
        "estimated_gain_real": result["estimated_gain_real"],
        "estimated_gain_imag": result["estimated_gain_imag"],
    }
    (result_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    return metrics
