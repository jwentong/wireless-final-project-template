"""Source encoding/decoding: UTF-8 text <-> bitstream."""


def source_encode(text: str) -> list[int]:
    """Convert UTF-8 text to a bitstream (MSB-first per byte).

    Args:
        text: UTF-8 string.

    Returns:
        List of bits (0/1 ints). Length is len(text.encode('utf-8')) * 8.
    """
    data = text.encode("utf-8")
    bits = []
    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def source_decode(bits: list[int]) -> str:
    """Convert a bitstream back to UTF-8 text (MSB-first per byte).

    Args:
        bits: List of bits. Length should be a multiple of 8.

    Returns:
        Recovered UTF-8 string.
    """
    # Take only full bytes
    num_bytes = len(bits) // 8
    data = bytearray()
    for i in range(num_bytes):
        byte_val = 0
        for shift in range(8):
            byte_val = (byte_val << 1) | int(bits[i * 8 + shift])
        data.append(byte_val)
    return bytes(data).decode("utf-8", errors="replace")


# Aliases for test discovery
text_to_bits = source_encode
bits_to_text = source_decode
utf8_to_bits = source_encode
bits_to_utf8 = source_decode
