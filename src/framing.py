PREAMBLE_BITS = [
    0, 0, 0, 1, 0, 1, 1, 0,
    1, 1, 1, 0, 1, 0, 0, 1,
    0, 0, 0, 1, 0, 1, 1, 0,
    1, 1, 1, 0, 1, 0, 0, 1,
]


def _bits_to_int(bits: list[int]) -> int:
    val = 0
    for b in bits:
        val = (val << 1) | b
    return val


def _int_to_bits(val: int, n: int) -> list[int]:
    return [(val >> (n - 1 - i)) & 1 for i in range(n)]


def xor_checksum(bits: list[int]) -> list[int]:
    padded = bits + [0] * ((8 - len(bits) % 8) % 8)
    checksum = 0
    for i in range(0, len(padded), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | padded[i + j]
        checksum ^= byte
    return _int_to_bits(checksum, 8)


def build_frame(payload_bits: list[int], checksum_bits: list[int] = None) -> list[int]:
    length_bits = _int_to_bits(len(payload_bits), 16)
    if checksum_bits is None:
        checksum_bits = xor_checksum(payload_bits)
    frame = PREAMBLE_BITS + length_bits + payload_bits + checksum_bits
    if len(frame) % 2 != 0:
        frame.append(0)
    return frame


def parse_frame(frame_bits: list[int], checksum_len: int = 8) -> tuple[list[int], dict]:
    meta = {}
    idx = 0
    meta["preamble"] = frame_bits[idx:idx + 32]
    idx += 32
    length = _bits_to_int(frame_bits[idx:idx + 16])
    meta["length"] = length
    idx += 16
    payload = frame_bits[idx:idx + length]
    idx += length
    stored_checksum = frame_bits[idx:idx + checksum_len]
    meta["checksum_bits"] = stored_checksum
    meta["checksum_pass"] = (stored_checksum == xor_checksum(payload))
    return payload, meta
