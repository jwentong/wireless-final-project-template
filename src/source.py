def bytes_to_bits(data: bytes) -> list[int]:
    bits: list[int] = []
    for value in data:
        for shift in range(7, -1, -1):
            bits.append((value >> shift) & 1)
    return bits


def bits_to_bytes(bits: list[int]) -> bytes:
    usable = bits[: len(bits) - (len(bits) % 8)]
    out = bytearray()
    for i in range(0, len(usable), 8):
        value = 0
        for bit in usable[i : i + 8]:
            value = (value << 1) | int(bit)
        out.append(value)
    return bytes(out)


def text_to_bits(text: str) -> tuple[list[int], bytes]:
    data = text.encode("utf-8")
    return bytes_to_bits(data), data


def bits_to_text(bits: list[int], errors: str = "replace") -> str:
    return bits_to_bytes(bits).decode("utf-8", errors=errors)


def source_encode(text: str) -> list[int]:
    bits, _ = text_to_bits(text)
    return bits


def source_decode(bits: list[int]) -> str:
    return bits_to_text(bits)
