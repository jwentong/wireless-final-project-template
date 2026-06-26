"""Frame construction and parsing."""

from __future__ import annotations

from dataclasses import dataclass
import zlib

from .source_codec import bits_to_bytes


PREAMBLE_BITS = [int(bit) for bit in ("1100101001110001" * 8)]
LENGTH_BITS = 32
CRC_BITS = 32


@dataclass(frozen=True)
class ParsedFrame:
    preamble: list[int]
    length: int
    payload: list[int]
    checksum: int
    bits: list[int]


def int_to_bits(value: int, width: int = 32) -> list[int]:
    if value < 0 or value >= (1 << width):
        raise ValueError(f"value must fit in {width} bits")
    return [(value >> shift) & 1 for shift in range(width - 1, -1, -1)]


def bits_to_int(bits: list[int]) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def crc32_from_payload_bits(payload_bits: list[int]) -> int:
    """Compute CRC32 from payload bits when they form whole bytes."""
    if len(payload_bits) % 8 != 0:
        data = bytes(int("".join(str(int(b)) for b in payload_bits[i : i + 8]).ljust(8, "0"), 2)
                     for i in range(0, len(payload_bits), 8))
    else:
        data = bits_to_bytes([int(bit) for bit in payload_bits])
    return zlib.crc32(data) & 0xFFFFFFFF


def build_frame(
    payload_bits: list[int],
    payload_bit_length: int | None = None,
    checksum: int | None = None,
) -> list[int]:
    """Build ``preamble + length + payload + CRC32``.

    In the final chain, ``payload_bits`` should be the encoded payload and
    ``payload_bit_length`` should be the original source payload length. In
    mock tests, omitting ``payload_bit_length`` makes parsing round-trip the
    supplied bits directly.
    """
    payload = [int(bit) for bit in payload_bits]
    length = len(payload) if payload_bit_length is None else int(payload_bit_length)
    crc = crc32_from_payload_bits(payload) if checksum is None else int(checksum)
    return PREAMBLE_BITS + int_to_bits(length, LENGTH_BITS) + payload + int_to_bits(crc, CRC_BITS)


def parse_frame(frame_bits: list[int], require_preamble: bool = True) -> dict[str, object]:
    bits = [int(bit) for bit in frame_bits]
    header_len = len(PREAMBLE_BITS) + LENGTH_BITS
    min_len = header_len + CRC_BITS
    if len(bits) < min_len:
        raise ValueError("frame is too short")
    if require_preamble and bits[: len(PREAMBLE_BITS)] != PREAMBLE_BITS:
        raise ValueError("preamble mismatch")

    length_start = len(PREAMBLE_BITS)
    length_end = length_start + LENGTH_BITS
    length = bits_to_int(bits[length_start:length_end])
    encoded_payload_end = length_end + length * 3
    if encoded_payload_end + CRC_BITS <= len(bits):
        payload_end = encoded_payload_end
    else:
        payload_end = len(bits) - CRC_BITS
    payload = bits[length_end:payload_end]
    checksum = bits_to_int(bits[payload_end : payload_end + CRC_BITS])
    return {
        "preamble": bits[: len(PREAMBLE_BITS)],
        "length": length,
        "payload": payload,
        "encoded_payload": payload,
        "checksum": checksum,
        "bits": bits,
    }


frame_build = build_frame
frame_parse = parse_frame
