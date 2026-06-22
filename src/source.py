from __future__ import annotations


def _clean_bits(bits) -> list[int]:
    return [1 if int(bit) else 0 for bit in list(bits)]


def text_to_bits(text: str) -> list[int]:
    data = text.encode("utf-8")
    bits: list[int] = []
    for byte in data:
        bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    return bits


def bits_to_text(bits) -> str:
    clean = _clean_bits(bits)
    usable = len(clean) - (len(clean) % 8)
    data = bytearray()
    for i in range(0, usable, 8):
        value = 0
        for bit in clean[i : i + 8]:
            value = (value << 1) | bit
        data.append(value)
    return bytes(data).decode("utf-8", errors="replace")


def source_encode(text: str) -> list[int]:
    return text_to_bits(text)


def source_decode(bits) -> str:
    return bits_to_text(bits)


encode_text = source_encode
decode_text = source_decode
utf8_to_bits = source_encode
bits_to_utf8 = source_decode
