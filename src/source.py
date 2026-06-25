def text_to_bits(text: str) -> list[int]:
    data = text.encode("utf-8")
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


def bits_to_text(bits: list[int]) -> str:
    if len(bits) % 8 != 0:
        bits = bits[:-(len(bits) % 8)]
    data = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        data.append(byte)
    return data.decode("utf-8", errors="replace")


source_encode = text_to_bits
source_decode = bits_to_text
