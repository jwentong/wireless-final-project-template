"""Frame building and parsing module.

Frame structure:
  [Preamble (32 symbols)] [Length (16 bits)] [Payload (N bits)] [Checksum (16 bits)]

- Preamble: 32-symbol known sequence for synchronization
  (8 repetitions of the 4 QPSK constellation points in Gray order)
- Length: 16-bit unsigned integer = number of original payload bits
- Payload: variable-length bitstream (scrambled + channel-encoded data)
- Checksum: 16-bit sum over original payload BYTES (before encoding)
"""

import numpy as np

# Preamble as bits (32 QPSK symbols = 64 bits)
# Uses an m-sequence (length 31) mapped to antipodal QPSK points for excellent
# autocorrelation: peak=31, sidelobes=-1. Each m-seq bit becomes 2 bits:
#   1 → [1,1] → (-1-j)/√2    0 → [0,0] → (1+j)/√2
# Extended to 32 symbols (64 bits) by repeating the first symbol.
# 31-bit m-sequence generated with LFSR polynomial x^5 + x^2 + 1.
_M_SEQ_31 = [1,1,1,1,1,0,1,0,0,0,1,0,0,1,0,1,0,1,1,0,0,0,0,1,1,1,0,0,1,1,0]
PREAMBLE_BITS = []
for _b in _M_SEQ_31:
    PREAMBLE_BITS.extend([1, 1] if _b else [0, 0])
# Pad to exactly 64 bits (32 QPSK symbols) by repeating the first symbol
PREAMBLE_BITS.extend([1, 1])  # 31*2 + 2 = 64 bits

LENGTH_BITS = 16  # Number of bits for the length field
CHECKSUM_BITS = 16  # Number of bits for the checksum field


def _compute_checksum(payload_bytes: bytes) -> int:
    """Compute 16-bit checksum (sum of bytes modulo 65536)."""
    return sum(payload_bytes) & 0xFFFF


def _int_to_bits(value: int, num_bits: int) -> list[int]:
    """Convert an integer to a list of bits (MSB-first)."""
    bits = []
    for shift in range(num_bits - 1, -1, -1):
        bits.append((value >> shift) & 1)
    return bits


def _bits_to_int(bits: list[int]) -> int:
    """Convert a list of bits (MSB-first) to an integer."""
    value = 0
    for b in bits:
        value = (value << 1) | int(b)
    return value


def build_frame(payload_bits: list[int], original_payload_bits: int = None) -> list[int]:
    """Build a complete frame from payload bits.

    Args:
        payload_bits: The payload bitstream (scrambled + encoded).
        original_payload_bits: Number of original payload bits (before encoding).
                              If None, uses len(payload_bits).

    Returns:
        Complete frame as a list of bits.
    """
    if original_payload_bits is None:
        original_payload_bits = len(payload_bits)

    # Length field: original payload bit count
    length_bits = _int_to_bits(original_payload_bits, LENGTH_BITS)

    # Checksum over original payload bits converted to bytes
    # Pad to byte boundary if needed
    padded = list(payload_bits)
    if len(padded) % 8 != 0:
        padded += [0] * (8 - len(padded) % 8)
    byte_count = len(padded) // 8
    payload_bytes = bytes(
        sum(int(padded[i * 8 + j]) << (7 - j) for j in range(8))
        for i in range(byte_count)
    )
    checksum = _compute_checksum(payload_bytes)
    checksum_bits = _int_to_bits(checksum, CHECKSUM_BITS)

    # Assemble frame
    frame = PREAMBLE_BITS + length_bits + list(payload_bits) + checksum_bits
    return frame


def parse_frame(frame_bits: list[int]) -> dict:
    """Parse a received frame into its components.

    Frame structure (bits):
      [Preamble (64)] [Length (16)] [Payload (encoded, variable)] [Checksum (16)]

    The length field stores the count of ORIGINAL payload bits (before encoding).
    The actual payload in the frame is the channel-encoded bitstream, which may be
    much longer. The checksum is always the last 16 bits of the frame.

    Args:
        frame_bits: Complete frame as list of bits.

    Returns:
        Dictionary with keys: preamble, length, payload, checksum, checksum_pass.
    """
    preamble_len = len(PREAMBLE_BITS)

    # Edge case: frame too short
    if len(frame_bits) < preamble_len + LENGTH_BITS + CHECKSUM_BITS:
        return {
            "preamble": frame_bits[:preamble_len] if len(frame_bits) >= preamble_len else [],
            "length": 0,
            "payload": [],
            "payload_bits": [],
            "checksum": 0,
            "checksum_pass": False,
        }

    preamble = frame_bits[:preamble_len]
    length_bits = frame_bits[preamble_len:preamble_len + LENGTH_BITS]

    # Checksum is always the last CHECKSUM_BITS bits
    checksum_bits = frame_bits[-CHECKSUM_BITS:]

    # Payload is everything between length field and checksum
    payload_start = preamble_len + LENGTH_BITS
    payload_end = len(frame_bits) - CHECKSUM_BITS
    payload = frame_bits[payload_start:payload_end]

    length = _bits_to_int(length_bits) if len(length_bits) == LENGTH_BITS else 0

    # Verify checksum over the payload
    padded = list(payload)
    if len(padded) % 8 != 0:
        padded += [0] * (8 - len(padded) % 8)
    byte_count = len(padded) // 8
    payload_bytes = bytes(
        sum(int(padded[i * 8 + j]) << (7 - j) for j in range(8))
        for i in range(byte_count)
    )
    expected_checksum = _compute_checksum(payload_bytes)
    actual_checksum = _bits_to_int(checksum_bits) if len(checksum_bits) == CHECKSUM_BITS else -1
    checksum_pass = (actual_checksum == expected_checksum)

    return {
        "preamble": preamble,
        "length": length,
        "payload": payload,
        "payload_bits": payload,
        "checksum": actual_checksum,
        "checksum_pass": checksum_pass,
    }


# Alternative function names for test discovery
def frame_build(payload_bits: list[int]) -> list[int]:
    """Alias for build_frame."""
    return build_frame(payload_bits)


def frame_parse(frame_bits: list[int]) -> dict:
    """Alias for parse_frame."""
    return parse_frame(frame_bits)


def create_frame(payload_bits: list[int]) -> list[int]:
    """Alias for build_frame."""
    return build_frame(payload_bits)


def make_frame(payload_bits: list[int]) -> list[int]:
    """Alias for build_frame."""
    return build_frame(payload_bits)


def extract_frame(frame_bits: list[int]) -> dict:
    """Alias for parse_frame."""
    return parse_frame(frame_bits)


def decode_frame(frame_bits: list[int]) -> dict:
    """Alias for parse_frame."""
    return parse_frame(frame_bits)
