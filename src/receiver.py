"""Receiver pipeline."""

from __future__ import annotations

import numpy as np

from src.channel_coding import channel_decode
from src.framing import parse_frame
from src.modulation import qpsk_demodulate
from src.scramble import descramble
from src.source import source_decode
from src.synchronization import synchronize
from src.utils import verify_crc16


def run_receiver(
    rx_symbols: np.ndarray,
    seed: int = 2026,
    preamble_symbols: np.ndarray | None = None,
    original_text: str | None = None,
    fec: str = "repeat",
) -> tuple[str, dict]:
    sync = synchronize(rx_symbols, preamble=preamble_symbols)
    start = int(sync["sync_start_index"])
    aligned = np.asarray(rx_symbols[start:], dtype=complex)
    frame_bits = qpsk_demodulate(aligned)
    parsed = parse_frame(frame_bits)

    coded_payload = [int(b) for b in parsed.get("payload", [])]
    decoded_scrambled = channel_decode(coded_payload, mode=fec)
    length_val = int(parsed.get("length", 0))
    descrambled = descramble(decoded_scrambled, seed=seed)[:length_val]

    checksum_pass = verify_crc16(descrambled, int(parsed.get("crc_value", 0)))
    parsed["checksum_pass"] = checksum_pass
    parsed["crc_pass"] = checksum_pass

    try:
        text = source_decode(descrambled, num_bits=length_val)
    except (UnicodeDecodeError, ValueError):
        text = ""

    ber = 0.0
    if original_text is not None:
        from src.source import source_encode

        ref_bits = source_encode(original_text)
        compare_len = min(len(ref_bits), len(descrambled))
        if compare_len > 0:
            errors = sum(
                int(a != b) for a, b in zip(ref_bits[:compare_len], descrambled[:compare_len])
            )
            ber = errors / compare_len

    text_match_rate = 1.0
    if original_text is not None:
        if not original_text:
            text_match_rate = 1.0 if not text else 0.0
        else:
            matches = sum(1 for a, b in zip(text, original_text) if a == b)
            text_match_rate = matches / len(original_text)

    fer = 1.0 if (not checksum_pass or text_match_rate < 1.0) else 0.0
    failure_reason = None
    if not checksum_pass:
        failure_reason = "crc_failed"
    elif text_match_rate < 1.0:
        failure_reason = "text_mismatch"

    metrics = {
        "payload_bits": length_val,
        "ber": ber,
        "fer": fer,
        "text_match_rate": text_match_rate,
        "checksum_pass": checksum_pass,
        "sync_start_index": start,
        "sync": sync,
        "failure_reason": failure_reason,
        "fec": fec,
    }
    return text, metrics
