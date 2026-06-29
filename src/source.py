"""Source coding: UTF-8 text <-> bit stream.

Each byte of the UTF-8 encoding is expanded MSB-first into 8 bits, so the bit
stream length is always a multiple of 8. Decoding reverses the process.
"""
from __future__ import annotations


def source_encode(text: str) -> list[int]:
    """Encode UTF-8 ``text`` into a list of bits (8 bits/byte, MSB first)."""
    bits: list[int] = []
    for byte in text.encode("utf-8"):
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def source_decode(bits: list[int]) -> str:
    """Decode a bit list (length multiple of 8) back into UTF-8 text."""
    data = bytearray()
    for k in range(len(bits) // 8):
        byte = 0
        for i in range(8):
            byte = (byte << 1) | int(bits[k * 8 + i])
        data.append(byte)
    return data.decode("utf-8")
