def source_encode(text):
    """Convert UTF-8 text to a most-significant-bit-first bit stream."""
    data = text.encode("utf-8")
    bits = []
    for byte in data:
        bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    return bits


def source_decode(bits):
    """Convert a bit stream back to UTF-8 text."""
    bit_list = [int(bit) for bit in bits]
    usable = len(bit_list) - (len(bit_list) % 8)
    data = bytearray()
    for i in range(0, usable, 8):
        value = 0
        for bit in bit_list[i : i + 8]:
            value = (value << 1) | int(bit)
        data.append(value)
    return data.decode("utf-8", errors="replace")


text_to_bits = source_encode
bits_to_text = source_decode

