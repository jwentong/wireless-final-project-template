"""UTF-8 source coding helpers."""

from __future__ import annotations


def bytes_to_bits(data: bytes) -> list[int]:
    """Convert bytes to big-endian bits."""
    bits: list[int] = []
    for byte in data:
        bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    return bits


def bits_to_bytes(bits: list[int]) -> bytes:
    """Convert big-endian bits to bytes.

    The input length must be a multiple of 8 so the UTF-8 source payload is
    recovered exactly instead of silently padded.
    """
    if len(bits) % 8 != 0:
        raise ValueError("bit length must be divisible by 8")

    output = bytearray()
    for index in range(0, len(bits), 8):
        value = 0
        for bit in bits[index : index + 8]:
            value = (value << 1) | int(bit)
        output.append(value)
    return bytes(output)


def source_encode(text: str) -> list[int]:
    """Encode text to UTF-8 payload bits."""
    return bytes_to_bits(text.encode("utf-8"))


def source_decode(bits: list[int]) -> str:
    """Decode UTF-8 payload bits back to text."""
    return bits_to_bytes([int(bit) for bit in bits]).decode("utf-8")


text_to_bits = source_encode
bits_to_text = source_decode
encode_text = source_encode
decode_text = source_decode
