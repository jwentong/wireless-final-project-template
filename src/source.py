"""UTF-8 source coding utilities."""

from __future__ import annotations

from typing import Iterable, List


def _as_bits(bits: Iterable[int]) -> List[int]:
    return [1 if int(bit) else 0 for bit in bits]


def source_encode(text: str) -> List[int]:
    """Convert UTF-8 text to a big-endian bit list."""
    data = text.encode("utf-8")
    out: List[int] = []
    for byte in data:
        out.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    return out


def source_decode(bits: Iterable[int], bit_length: int | None = None, errors: str = "strict") -> str:
    """Recover UTF-8 text from a bit list.

    Extra bits that do not form a complete byte are ignored unless
    ``bit_length`` is supplied, in which case the stream is cropped first.
    """
    bit_list = _as_bits(bits)
    if bit_length is not None:
        bit_list = bit_list[: int(bit_length)]
    usable = len(bit_list) - (len(bit_list) % 8)
    bit_list = bit_list[:usable]
    data = bytearray()
    for i in range(0, len(bit_list), 8):
        value = 0
        for bit in bit_list[i : i + 8]:
            value = (value << 1) | bit
        data.append(value)
    return bytes(data).decode("utf-8", errors=errors)


text_to_bits = source_encode
utf8_to_bits = source_encode
bits_to_text = source_decode
bits_to_utf8 = source_decode
encode_text = source_encode
decode_text = source_decode

