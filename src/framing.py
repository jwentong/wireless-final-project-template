"""帧结构模块：preamble + length(16bit) + payload + checksum(16bit, CRC16)"""
from __future__ import annotations
from typing import Iterable, List
import zlib
import numpy as np

PREAMBLE_LEN = 64
LENGTH_LEN = 16
CHECKSUM_LEN = 16
_PREAMBLE_SEED = 20260101

PREAMBLE_BITS: List[int] = np.random.default_rng(_PREAMBLE_SEED).integers(0, 2, size=PREAMBLE_LEN).tolist()


def _bits_to_int(bits):
    v = 0
    for b in bits:
        v = (v << 1) | int(b)
    return v


def _int_to_bits(value, length):
    return [(value >> i) & 1 for i in range(length - 1, -1, -1)]


def _bits_to_bytes(bits):
    bits = list(bits)
    pad = (-len(bits)) % 8
    bits = bits + [0] * pad
    data = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i:i + 8]:
            byte = (byte << 1) | int(b)
        data.append(byte)
    return bytes(data)


def _checksum_bits(payload_bits):
    data = _bits_to_bytes(payload_bits)
    crc = zlib.crc32(data) & 0xFFFF
    return _int_to_bits(crc, CHECKSUM_LEN)


def build_frame(payload_bits: Iterable[int]) -> List[int]:
    payload = [int(b) for b in payload_bits]
    length_bits = _int_to_bits(len(payload), LENGTH_LEN)
    checksum_bits = _checksum_bits(payload)
    return list(PREAMBLE_BITS) + length_bits + payload + checksum_bits


def parse_frame(frame_bits: Iterable[int]) -> dict:
    bits = [int(b) for b in frame_bits]
    preamble = bits[:PREAMBLE_LEN]
    length_bits = bits[PREAMBLE_LEN:PREAMBLE_LEN + LENGTH_LEN]
    length = _bits_to_int(length_bits)
    p_start = PREAMBLE_LEN + LENGTH_LEN
    payload = bits[p_start:p_start + length]
    c_start = p_start + length
    checksum = bits[c_start:c_start + CHECKSUM_LEN]
    expected = _checksum_bits(payload)
    return {
        "preamble": preamble,
        "length": length,
        "payload": payload,
        "checksum": checksum,
        "checksum_pass": checksum == expected,
    }


frame_build = build_frame
frame_parse = parse_frame
create_frame = build_frame
make_frame = build_frame
extract_frame = parse_frame
decode_frame = parse_frame
