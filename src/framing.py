from __future__ import annotations

import zlib


PREAMBLE_BITS = ([1, 1, 0, 0, 1, 0, 1, 0] * 8)
LENGTH_BITS = 32
TX_LENGTH_BITS = 32
CRC_BITS = 32


def int_to_bits(value: int, width: int) -> list[int]:
    if value < 0 or value >= (1 << width):
        raise ValueError(f"value {value} does not fit in {width} bits")
    return [(value >> shift) & 1 for shift in range(width - 1, -1, -1)]


def bits_to_int(bits: list[int]) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def crc32_bits(bits: list[int]) -> int:
    usable = len(bits) - (len(bits) % 8)
    data = bytearray()
    for offset in range(0, usable, 8):
        byte = 0
        for bit in bits[offset : offset + 8]:
            byte = (byte << 1) | int(bit)
        data.append(byte)
    if usable != len(bits):
        byte = 0
        for bit in bits[usable:]:
            byte = (byte << 1) | int(bit)
        byte <<= 8 - (len(bits) - usable)
        data.append(byte)
    return zlib.crc32(bytes(data)) & 0xFFFFFFFF


def build_frame(
    payload_bits: list[int],
    tx_payload_bits: int | None = None,
    original_payload_bits: list[int] | None = None,
) -> dict[str, object]:
    payload = [int(bit) for bit in payload_bits]
    tx_length = len(payload) if tx_payload_bits is None else int(tx_payload_bits)
    original_payload = payload if original_payload_bits is None else [int(bit) for bit in original_payload_bits]
    header = int_to_bits(len(original_payload), LENGTH_BITS) + int_to_bits(tx_length, TX_LENGTH_BITS)
    crc = int_to_bits(crc32_bits(original_payload), CRC_BITS)
    bits = PREAMBLE_BITS + header + payload + crc
    return {
        "preamble": PREAMBLE_BITS.copy(),
        "length": len(original_payload),
        "tx_length": tx_length,
        "payload": payload,
        "checksum": crc,
        "bits": bits,
        "checksum_scope": "original-payload-bits" if original_payload_bits is not None else "payload-bits",
    }


def parse_frame(frame_bits: list[int] | dict[str, object]) -> dict[str, object]:
    if isinstance(frame_bits, dict):
        frame_bits = frame_bits.get("bits") or frame_bits.get("frame") or frame_bits.get("payload") or []
    bits = [int(bit) for bit in frame_bits]
    min_len = len(PREAMBLE_BITS) + LENGTH_BITS + TX_LENGTH_BITS + CRC_BITS
    if len(bits) < min_len:
        raise ValueError("frame is too short")
    offset = 0
    if bits[: len(PREAMBLE_BITS)] == PREAMBLE_BITS:
        offset = len(PREAMBLE_BITS)
    length = bits_to_int(bits[offset : offset + LENGTH_BITS])
    offset += LENGTH_BITS
    tx_length = bits_to_int(bits[offset : offset + TX_LENGTH_BITS])
    offset += TX_LENGTH_BITS
    payload = bits[offset : offset + tx_length]
    offset += tx_length
    checksum_bits = bits[offset : offset + CRC_BITS]
    expected = bits_to_int(checksum_bits) if len(checksum_bits) == CRC_BITS else -1
    actual = crc32_bits(payload)
    return {
        "length": length,
        "tx_length": tx_length,
        "payload": payload,
        "checksum": expected,
        "checksum_pass": expected == actual,
    }


frame_build = build_frame
create_frame = build_frame
make_frame = build_frame
frame_parse = parse_frame
extract_frame = parse_frame
decode_frame = parse_frame
