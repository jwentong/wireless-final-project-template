"""Performance metrics helpers."""

from __future__ import annotations

import json
from pathlib import Path

from src.channel_coding import CODING_RATES


def build_metrics(
    *,
    snr_db: float,
    seed: int,
    modulation: str,
    channel: str,
    payload_bits: int,
    ber: float,
    fer: float,
    text_match_rate: float,
    checksum_pass: bool,
    sync_start_index: int,
    eb_n0_db: float | None = None,
    coding_rate: float | None = None,
    failure_reason: str | None = None,
    fec: str = "repeat",
) -> dict:
    if coding_rate is None:
        coding_rate = CODING_RATES.get(fec, 1.0 / 3.0)
    if eb_n0_db is None:
        eb_n0_db = snr_db - 3.01 - 10.0 * __import__("math").log10(1.0 / coding_rate)
    return {
        "snr_db": snr_db,
        "seed": seed,
        "modulation": modulation,
        "channel": channel,
        "payload_bits": payload_bits,
        "ber": ber,
        "fer": fer,
        "text_match_rate": text_match_rate,
        "checksum_pass": checksum_pass,
        "sync_start_index": sync_start_index,
        "eb_n0_db": eb_n0_db,
        "coding_rate": coding_rate,
        "failure_reason": failure_reason,
        "fec": fec,
    }


def save_metrics(metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
