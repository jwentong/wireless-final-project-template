"""Transmitter pipeline."""

from __future__ import annotations

import numpy as np

from src.channel_coding import channel_encode
from src.framing import build_frame
from src.modulation import qpsk_modulate
from src.scramble import scramble
from src.source import source_encode
from src.utils import preamble_bits


def run_transmitter(text: str, seed: int = 2026, fec: str = "repeat") -> tuple[np.ndarray, dict]:
    source_bits = source_encode(text)
    scrambled = scramble(source_bits, seed=seed)
    coded = channel_encode(scrambled, mode=fec)
    frame = build_frame(coded, source_bits_for_crc=source_bits)
    frame_bits = frame["bits"]
    tx_symbols = qpsk_modulate(frame_bits)

    rng = np.random.default_rng(seed + 1)
    offset = int(rng.integers(0, 129))
    if offset > 0:
        prefix = (rng.standard_normal(offset) + 1j * rng.standard_normal(offset)) / np.sqrt(2)
        tx_symbols = np.concatenate([prefix, tx_symbols])

    preamble_symbols = qpsk_modulate(preamble_bits())
    meta = {
        "payload_bits": len(source_bits),
        "source_bits": source_bits,
        "frame_bits": frame_bits,
        "preamble_symbols": preamble_symbols,
        "offset": offset,
        "frame": frame,
        "fec": fec,
    }
    return tx_symbols, meta
