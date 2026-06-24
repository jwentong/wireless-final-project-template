"""Shared bit/byte helpers and CRC-16."""

from __future__ import annotations

PREAMBLE_HEX = 0xAA55AA55
PREAMBLE_BITS = 32
LENGTH_BITS = 16
CRC_BITS = 16
HEADER_BITS = PREAMBLE_BITS + LENGTH_BITS


def int_to_bits(value: int, width: int) -> list[int]:
    """Unsigned integer to MSB-first bit list."""
    return [(value >> (width - 1 - i)) & 1 for i in range(width)]


def bits_to_int(bits: list[int]) -> int:
    """MSB-first bit list to unsigned integer."""
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def preamble_bits() -> list[int]:
    return int_to_bits(PREAMBLE_HEX, PREAMBLE_BITS)


def crc16_ccitt(bits: list[int]) -> int:
    """CRC-16/CCITT-FALSE over a bit stream (poly 0x1021, init 0xFFFF)."""
    crc = 0xFFFF
    for bit in bits:
        msb = (crc >> 15) & 1
        crc = ((crc << 1) & 0xFFFF) ^ (0x1021 if (msb ^ int(bit)) else 0)
    return crc & 0xFFFF


def verify_crc16(bits: list[int], expected: int) -> bool:
    return crc16_ccitt(bits) == (expected & 0xFFFF)
