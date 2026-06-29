"""Performance metrics and CRC.

Provides CRC-16-CCITT (used by framing for the checksum field) plus bit error
rate, frame error rate and text match rate used by the pipeline / reports.
"""
from __future__ import annotations


def crc16(bits: list[int]) -> int:
    """CRC-16-CCITT (poly 0x1021, init 0xFFFF), bit-wise, no reflection."""
    reg = 0xFFFF
    for b in bits:
        msb = (reg >> 15) & 1
        reg = (reg << 1) & 0xFFFF
        if msb ^ (int(b) & 1):
            reg ^= 0x1021
    return reg


def ber(tx_bits: list[int], rx_bits: list[int]) -> float:
    """Bit error rate over the overlapping prefix of the two bit lists."""
    n = min(len(tx_bits), len(rx_bits))
    if n == 0:
        return 0.0
    errors = sum(1 for i in range(n) if int(tx_bits[i]) != int(rx_bits[i]))
    return errors / n


def fer(frame_ok: bool) -> float:
    """Frame error rate for the single-frame system: 0.0 if ok else 1.0."""
    return 0.0 if frame_ok else 1.0


def text_match_rate(ref: str, out: str) -> float:
    """Fraction of matching characters, normalized by the longer string."""
    if len(ref) == 0:
        return 1.0 if len(out) == 0 else 0.0
    matches = sum(1 for a, b in zip(ref, out) if a == b)
    return matches / max(len(ref), len(out))
