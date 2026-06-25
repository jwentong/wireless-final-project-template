def source_encode(text):
    data = text.encode("utf-8")
    bits = []
    for byte in data:
        bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    return bits


def source_decode(bits):
    clean = [int(b) & 1 for b in bits]
    usable = len(clean) - (len(clean) % 8)
    data = bytearray()
    for i in range(0, usable, 8):
        value = 0
        for bit in clean[i : i + 8]:
            value = (value << 1) | bit
        data.append(value)
    return bytes(data).decode("utf-8", errors="replace")


text_to_bits = source_encode
utf8_to_bits = source_encode
encode_text = source_encode
bits_to_text = source_decode
bits_to_utf8 = source_decode
decode_text = source_decode

