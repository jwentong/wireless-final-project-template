"""Metric calculation and JSON output."""

from __future__ import annotations

import json
from pathlib import Path

from .utils import compare_bits, ensure_parent_dir


def text_match_rate(expected: str, actual: str) -> float:
    if expected == actual:
        return 1.0
    if not expected:
        return 0.0 if actual else 1.0
    common = min(len(expected), len(actual))
    matches = sum(1 for left, right in zip(expected[:common], actual[:common]) if left == right)
    return matches / max(len(expected), len(actual))


def build_metrics(
    *,
    snr_db: float,
    seed: int,
    modulation: str,
    channel: str,
    original_bits: list[int],
    recovered_bits: list[int],
    original_text: str,
    recovered_text: str,
    checksum_pass: bool,
    sync_start_index: int | None,
    prefix_offset_symbols: int | None,
    crc_expected: int | None,
    crc_received: int | None,
    sync_peak_value: float | None,
    failure_reason: str | None,
    extra_fields: dict[str, object] | None = None,
) -> dict[str, object]:
    _, ber = compare_bits(original_bits, recovered_bits)
    match_rate = text_match_rate(original_text, recovered_text)
    success = checksum_pass and match_rate == 1.0
    metrics: dict[str, object] = {
        "snr_db": float(snr_db),
        "seed": int(seed),
        "modulation": modulation,
        "channel": channel,
        "payload_bits": len(original_bits),
        "ber": float(ber),
        "fer": 0.0 if success else 1.0,
        "text_match_rate": float(match_rate),
        "checksum_pass": bool(checksum_pass),
        "sync_start_index": None if sync_start_index is None else int(sync_start_index),
        "coding": "repetition-3",
        "scrambling": "pn-xor",
        "qpsk_mapping": "gray",
        "prefix_offset_symbols": prefix_offset_symbols,
        "crc_expected": None if crc_expected is None else f"0x{crc_expected:08x}",
        "crc_received": None if crc_received is None else f"0x{crc_received:08x}",
        "sync_peak_value": sync_peak_value,
        "failure_reason": failure_reason,
    }
    if prefix_offset_symbols is not None and sync_start_index is not None:
        metrics["sync_error_symbols"] = int(sync_start_index) - int(prefix_offset_symbols)
    else:
        metrics["sync_error_symbols"] = None
    if extra_fields:
        metrics.update(extra_fields)
    return metrics


def write_metrics(metrics: dict[str, object], path: str | Path) -> None:
    output = ensure_parent_dir(path)
    output.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
