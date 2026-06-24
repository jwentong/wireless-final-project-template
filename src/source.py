"""Source encoding: UTF-8 text <-> bitstream."""

from __future__ import annotations


def text_to_bits(text: str) -> list[int]:
    """Encode UTF-8 text to MSB-first bits (length is a multiple of 8)."""
    bits: list[int] = []
    for byte in text.encode("utf-8"):
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def bits_to_text(bits: list[int], num_bits: int | None = None) -> str:
    """Decode MSB-first bits to UTF-8 text."""
    if num_bits is None:
        num_bits = len(bits)
    effective = bits[:num_bits]
    if num_bits % 8 != 0:
        raise ValueError(f"num_bits must be a multiple of 8, got {num_bits}")
    data = bytearray()
    for i in range(0, num_bits, 8):
        byte = 0
        for bit in effective[i : i + 8]:
            byte = (byte << 1) | int(bit)
        data.append(byte)
    return data.decode("utf-8")


def source_encode(text: str) -> list[int]:
    return text_to_bits(text)


def source_decode(bits: list[int], num_bits: int | None = None) -> str:
    return bits_to_text(bits, num_bits)
