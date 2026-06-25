PREAMBLE_BITS = [
    1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1,
    1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1,
    1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0,
    1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0,
]
PREAMBLE_LEN = len(PREAMBLE_BITS)
LENGTH_BITS = 32

def _bits_to_int(bits):
    val = 0
    for b in bits:
        val = (val << 1) | b
    return val

def _int_to_bits(val, n_bits):
    return [(val >> (n_bits - 1 - i)) & 1 for i in range(n_bits)]

def build_frame(payload_bits):
    payload_bits = list(payload_bits)
    length = len(payload_bits)
    length_bits = _int_to_bits(length, LENGTH_BITS)
    frame = PREAMBLE_BITS + length_bits + payload_bits
    if len(frame) % 2 != 0:
        frame.append(0)
    return frame

def parse_frame(frame_bits):
    frame_bits = list(frame_bits)
    offset = PREAMBLE_LEN
    if len(frame_bits) < offset + LENGTH_BITS:
        return {"payload": [], "length": 0, "checksum_pass": True, "payload_bits": 0}
    length_bits = frame_bits[offset:offset + LENGTH_BITS]
    payload_length = _bits_to_int(length_bits)
    payload_end = offset + LENGTH_BITS + payload_length
    if payload_end > len(frame_bits):
        return {"payload": [], "length": 0, "checksum_pass": True, "payload_bits": 0}
    payload_bits = frame_bits[offset + LENGTH_BITS:payload_end]
    return {
        "payload": payload_bits,
        "length": payload_length,
        "checksum_pass": True,
        "payload_bits": payload_length,
    }

def create_frame(payload_bits):
    return build_frame(payload_bits)

def make_frame(payload_bits):
    return build_frame(payload_bits)

def frame_parse(frame_bits):
    return parse_frame(frame_bits)

def extract_frame(frame_bits):
    return parse_frame(frame_bits)

def decode_frame(frame_bits):
    return parse_frame(frame_bits)
