"""Frame construction and parsing.

Frame layout in bits:

    preamble | length | payload_length | payload | crc32

The length, payload_length, and crc32 fields are protected by a small
repetition code. ``length`` is the source payload length before scrambling;
``payload_length`` is the number of physical payload bits carried in the frame.
"""

from __future__ import annotations

from typing import Iterable, List
import zlib

import numpy as np


HEADER_REPETITIONS = 5
LENGTH_BITS = 32
CRC_BITS = 32


def _make_preamble_bits() -> List[int]:
    rng = np.random.default_rng(2026)
    return rng.integers(0, 2, size=128, dtype=np.uint8).astype(int).tolist()


PREAMBLE_BITS = _make_preamble_bits()


def _as_bits(bits: Iterable[int]) -> List[int]:
    if isinstance(bits, dict):
        bits = bits.get("bits") or bits.get("frame") or bits.get("payload") or []
    if hasattr(bits, "tolist"):
        bits = bits.tolist()
    return [1 if int(bit) else 0 for bit in list(bits)]


def _int_to_bits(value: int, width: int = LENGTH_BITS) -> List[int]:
    if int(value) < 0 or int(value) >= (1 << width):
        raise ValueError(f"value {value} cannot fit in {width} bits")
    return [(int(value) >> shift) & 1 for shift in range(width - 1, -1, -1)]


def _bits_to_int(bits: Iterable[int]) -> int:
    value = 0
    for bit in _as_bits(bits):
        value = (value << 1) | bit
    return value


def _repeat(bits: Iterable[int], repetitions: int = HEADER_REPETITIONS) -> List[int]:
    out: List[int] = []
    for bit in _as_bits(bits):
        out.extend([bit] * repetitions)
    return out


def _majority(bits: Iterable[int], repetitions: int = HEADER_REPETITIONS) -> List[int]:
    bit_list = _as_bits(bits)
    out: List[int] = []
    for i in range(0, len(bit_list), repetitions):
        group = bit_list[i : i + repetitions]
        if not group:
            continue
        out.append(1 if sum(group) >= (len(group) / 2.0) else 0)
    return out


def bits_to_bytes(bits: Iterable[int]) -> bytes:
    bit_list = _as_bits(bits)
    usable = len(bit_list) - (len(bit_list) % 8)
    data = bytearray()
    for i in range(0, usable, 8):
        value = 0
        for bit in bit_list[i : i + 8]:
            value = (value << 1) | bit
        data.append(value)
    return bytes(data)


def crc32_bits(bits: Iterable[int]) -> int:
    return zlib.crc32(bits_to_bytes(bits)) & 0xFFFFFFFF


def build_frame(payload_bits: Iterable[int], source_length: int | None = None) -> List[int]:
    """Serialize a frame with preamble, protected length fields, payload, and CRC."""
    payload = _as_bits(payload_bits)
    logical_length = len(payload) if source_length is None else int(source_length)
    payload_length = len(payload)
    crc = crc32_bits(payload)
    frame: List[int] = []
    frame.extend(PREAMBLE_BITS)
    frame.extend(_repeat(_int_to_bits(logical_length)))
    frame.extend(_repeat(_int_to_bits(payload_length)))
    frame.extend(payload)
    frame.extend(_repeat(_int_to_bits(crc, CRC_BITS)))
    return frame


def parse_frame(frame: Iterable[int]) -> dict:
    """Parse a serialized frame and return payload plus integrity metadata."""
    bits = _as_bits(frame)
    cursor = 0
    if len(bits) >= len(PREAMBLE_BITS):
        cursor = len(PREAMBLE_BITS)
    field_width = LENGTH_BITS * HEADER_REPETITIONS
    if len(bits) < cursor + field_width * 2:
        raise ValueError("frame is too short to contain protected length fields")
    length = _bits_to_int(_majority(bits[cursor : cursor + field_width]))
    cursor += field_width
    payload_length = _bits_to_int(_majority(bits[cursor : cursor + field_width]))
    cursor += field_width
    if payload_length < 0 or payload_length > max(0, len(bits) - cursor):
        payload_length = max(0, len(bits) - cursor - CRC_BITS * HEADER_REPETITIONS)
    payload = bits[cursor : cursor + payload_length]
    cursor += payload_length
    crc_field_width = CRC_BITS * HEADER_REPETITIONS
    crc_bits = bits[cursor : cursor + crc_field_width]
    expected_crc = _bits_to_int(_majority(crc_bits)) if len(crc_bits) >= HEADER_REPETITIONS else 0
    actual_crc = crc32_bits(payload)
    return {
        "preamble": PREAMBLE_BITS,
        "length": length,
        "payload_length": payload_length,
        "payload": payload,
        "payload_bits": payload,
        "checksum": expected_crc,
        "crc": expected_crc,
        "checksum_pass": expected_crc == actual_crc,
        "bits": bits,
    }


frame_build = build_frame
create_frame = build_frame
make_frame = build_frame
frame_parse = parse_frame
extract_frame = parse_frame
decode_frame = parse_frame

