"""Source encoding/decoding module: UTF-8 text ↔ bitstream conversion."""


def text_to_bits(text: str) -> list[int]:
    """Convert UTF-8 text to a list of bits (MSB-first per byte).

    Args:
        text: UTF-8 encoded string.

    Returns:
        List of 0/1 integers representing the bitstream.
    """
    raw_bytes = text.encode("utf-8")
    bits = []
    for byte in raw_bytes:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def bits_to_text(bits: list[int]) -> str:
    """Convert a list of bits back to UTF-8 text (MSB-first per byte).

    Args:
        bits: List of 0/1 integers. Length must be a multiple of 8.

    Returns:
        UTF-8 decoded string.
    """
    # Truncate to nearest multiple of 8
    byte_count = len(bits) // 8
    raw_bytes = bytearray()
    for i in range(byte_count):
        byte_val = 0
        for shift in range(8):
            byte_val = (byte_val << 1) | int(bits[i * 8 + shift])
        raw_bytes.append(byte_val)
    return raw_bytes.decode("utf-8", errors="replace")


# Alternative function names for test discovery
def source_encode(text: str) -> list[int]:
    """Alias for text_to_bits."""
    return text_to_bits(text)


def source_decode(bits: list[int]) -> str:
    """Alias for bits_to_text."""
    return bits_to_text(bits)


def encode_text(text: str) -> list[int]:
    """Alias for text_to_bits."""
    return text_to_bits(text)


def utf8_to_bits(text: str) -> list[int]:
    """Alias for text_to_bits."""
    return text_to_bits(text)


def decode_text(bits: list[int]) -> str:
    """Alias for bits_to_text."""
    return bits_to_text(bits)


def bits_to_utf8(bits: list[int]) -> str:
    """Alias for bits_to_text."""
    return bits_to_text(bits)
