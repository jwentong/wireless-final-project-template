def source_encode(text):
    bytes_data = text.encode("utf-8")
    bits = []
    for byte in bytes_data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits

def source_decode(bits):
    bits = list(bits)
    bytes_data = bytearray()
    for i in range(0, len(bits) - len(bits) % 8, 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        bytes_data.append(byte)
    return bytes_data.decode("utf-8", errors="replace")

def text_to_bits(text):
    return source_encode(text)

def bits_to_text(bits):
    return source_decode(bits)
