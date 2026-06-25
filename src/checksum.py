import zlib


def crc32_checksum(bits: list[int]) -> list[int]:
    padded = bits + [0] * ((8 - len(bits) % 8) % 8)
    data = bytearray()
    for i in range(0, len(padded), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | padded[i + j]
        data.append(byte)
    crc = zlib.crc32(bytes(data)) & 0xFFFFFFFF
    return [(crc >> (31 - i)) & 1 for i in range(32)]


CHECKSUM_SCHEMES = {
    "xor8": None,
    "crc32": crc32_checksum,
}


def get_checksum_fn(name: str):
    from src.framing import xor_checksum
    fn = CHECKSUM_SCHEMES.get(name)
    if fn is None:
        return xor_checksum
    return fn


def get_checksum_len(name: str) -> int:
    return 32 if name == "crc32" else 8
