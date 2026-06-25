import zlib


PREAMBLE_BITS = [
    1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1,
    0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 1,
    0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0,
    1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1,
    0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1,
    1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0,
    1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1,
    0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0,
]
PREAMBLE_LEN = len(PREAMBLE_BITS)
HEADER_LEN = PREAMBLE_LEN + 32 + 32
CRC_LEN = 32


def _int_to_bits(value, width):
    return [(int(value) >> shift) & 1 for shift in range(width - 1, -1, -1)]


def _bits_to_int(bits):
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def _bits_to_bytes(bits):
    bit_list = [int(bit) for bit in bits]
    padded = bit_list + [0] * ((-len(bit_list)) % 8)
    data = bytearray()
    for i in range(0, len(padded), 8):
        value = 0
        for bit in padded[i : i + 8]:
            value = (value << 1) | int(bit)
        data.append(value)
    return bytes(data)


def checksum32(bits):
    return zlib.crc32(_bits_to_bytes(bits)) & 0xFFFFFFFF


def build_frame(payload_bits, original_length=None, checksum_bits=None):
    payload = [int(bit) for bit in payload_bits]
    original_length = len(payload) if original_length is None else int(original_length)
    checksum_source = payload if checksum_bits is None else [int(bit) for bit in checksum_bits]
    crc = checksum32(checksum_source)
    return (
        PREAMBLE_BITS.copy()
        + _int_to_bits(original_length, 32)
        + _int_to_bits(len(payload), 32)
        + payload
        + _int_to_bits(crc, 32)
    )


def parse_frame(frame_bits):
    bits = [int(bit) for bit in frame_bits]
    if len(bits) < HEADER_LEN + CRC_LEN:
        return {
            "payload": [],
            "payload_bits": [],
            "length": 0,
            "payload_length": 0,
            "checksum_pass": False,
            "crc_pass": False,
        }

    start = 0
    if bits[:PREAMBLE_LEN] == PREAMBLE_BITS:
        start = PREAMBLE_LEN

    original_length = _bits_to_int(bits[start : start + 32])
    payload_length = _bits_to_int(bits[start + 32 : start + 64])
    payload_start = start + 64
    max_payload = max(0, len(bits) - payload_start - CRC_LEN)
    payload_length = min(payload_length, max_payload)
    payload_end = payload_start + payload_length
    payload = bits[payload_start:payload_end]
    crc_bits = bits[payload_end : payload_end + CRC_LEN]
    expected_crc = _bits_to_int(crc_bits) if len(crc_bits) == CRC_LEN else -1
    crc_pass = checksum32(payload) == expected_crc
    return {
        "payload": payload,
        "payload_bits": payload,
        "data": payload,
        "length": original_length,
        "payload_length": payload_length,
        "checksum": expected_crc,
        "checksum_pass": bool(crc_pass),
        "crc_pass": bool(crc_pass),
    }


frame_build = build_frame
create_frame = build_frame
make_frame = build_frame
frame_parse = parse_frame
extract_frame = parse_frame
decode_frame = parse_frame
