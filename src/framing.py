import zlib


def _make_preamble_bits():
    state = 0b1110011
    bits = []
    for _ in range(128):
        new_bit = ((state >> 6) ^ (state >> 5)) & 1
        bits.append(state & 1)
        state = ((state << 1) & 0b1111111) | new_bit
    return bits


PREAMBLE_BITS = _make_preamble_bits()
LENGTH_BITS = 32
CHECKSUM_BITS = 32


def int_to_bits(value, width):
    return [(int(value) >> shift) & 1 for shift in range(width - 1, -1, -1)]


def bits_to_int(bits):
    value = 0
    for bit in bits:
        value = (value << 1) | (int(bit) & 1)
    return value


def checksum32(bits):
    clean = [int(b) & 1 for b in bits]
    padded = clean + [0] * ((8 - len(clean) % 8) % 8)
    data = bytearray()
    for i in range(0, len(padded), 8):
        data.append(bits_to_int(padded[i : i + 8]))
    return zlib.crc32(bytes(data)) & 0xFFFFFFFF


def build_frame(payload_bits, original_length=None, checksum_bits=None):
    payload = [int(b) & 1 for b in payload_bits]
    length = len(payload) if original_length is None else int(original_length)
    checksum_source = payload if checksum_bits is None else [int(b) & 1 for b in checksum_bits]
    return (
        list(PREAMBLE_BITS)
        + int_to_bits(length, LENGTH_BITS)
        + payload
        + int_to_bits(checksum32(checksum_source), CHECKSUM_BITS)
    )


def parse_frame(frame, repetition=1, checksum_bits=None):
    bits = [int(b) & 1 for b in (frame.get("bits") if isinstance(frame, dict) else frame)]
    offset = 0
    if bits[: len(PREAMBLE_BITS)] == PREAMBLE_BITS:
        offset = len(PREAMBLE_BITS)
    length = bits_to_int(bits[offset : offset + LENGTH_BITS])
    payload_start = offset + LENGTH_BITS
    payload_len = length * int(repetition)
    payload = bits[payload_start : payload_start + payload_len]
    checksum_start = payload_start + payload_len
    received_checksum = bits_to_int(bits[checksum_start : checksum_start + CHECKSUM_BITS])
    checksum_source = payload if checksum_bits is None else [int(b) & 1 for b in checksum_bits]
    expected_checksum = checksum32(checksum_source)
    return {
        "preamble": PREAMBLE_BITS,
        "length": length,
        "payload": payload,
        "checksum": received_checksum,
        "checksum_pass": received_checksum == expected_checksum,
    }


frame_build = build_frame
create_frame = build_frame
make_frame = build_frame
frame_parse = parse_frame
extract_frame = parse_frame
decode_frame = parse_frame
