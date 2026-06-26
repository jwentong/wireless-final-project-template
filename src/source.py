from __future__ import annotations


def source_encode(text: str) -> list[int]:
    """Convert UTF-8 text to a big-endian bit list."""
    data = text.encode("utf-8")
    bits: list[int] = []
    for byte in data:
        bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    return bits


def source_decode(bits: list[int]) -> str:
    """Recover UTF-8 text from a bit list, ignoring incomplete trailing bits."""
    usable = len(bits) - (len(bits) % 8)
    data = bytearray()
    for offset in range(0, usable, 8):
        byte = 0
        for bit in bits[offset : offset + 8]:
            byte = (byte << 1) | int(bit)
        data.append(byte)
    return data.decode("utf-8", errors="strict")


text_to_bits = source_encode
bits_to_text = source_decode

