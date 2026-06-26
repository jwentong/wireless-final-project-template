"""Frame build and parse: preamble + length + payload + CRC-16."""

from __future__ import annotations

from src.utils import (
    CRC_BITS,
    HEADER_BITS,
    bits_to_int,
    crc16_ccitt,
    int_to_bits,
    preamble_bits,
)


def _strip_qpsk_tail_padding(frame_bits: list[int]) -> list[int]:
    """Remove a single QPSK tail zero if present."""
    bits = list(frame_bits)
    if len(bits) > HEADER_BITS + CRC_BITS and len(bits) % 2 == 0 and bits[-1] == 0:
        trimmed = bits[:-1]
        if len(trimmed) >= HEADER_BITS + CRC_BITS:
            return trimmed
    return bits


def build_frame(
    payload_bits: list[int],
    source_bits_for_crc: list[int] | None = None,
) -> dict:
    """
    Build a frame dict.

    payload_bits: coded payload stored in the frame (or raw payload in unit tests).
    source_bits_for_crc: source-encoded bits before scramble (PRD length/CRC scope).
    """
    coded = [int(b) for b in payload_bits]
    if source_bits_for_crc is None:
        source_bits_for_crc = coded
    source = [int(b) for b in source_bits_for_crc]

    pre = preamble_bits()
    length_val = len(source)
    length_field = int_to_bits(length_val, 16)
    crc_val = crc16_ccitt(source)
    crc_field = int_to_bits(crc_val, 16)
    frame_bits = pre + length_field + coded + crc_field

    return {
        "preamble": pre,
        "length": length_val,
        "payload": coded,
        "crc": crc_field,
        "checksum": crc_field,
        "crc_value": crc_val,
        "bits": frame_bits,
        "frame": frame_bits,
    }


def parse_frame(frame_bits: list[int] | dict) -> dict:
    """Parse a serialized frame bitstream or build_frame dict."""
    if isinstance(frame_bits, dict):
        frame_bits = (
            frame_bits.get("bits")
            or frame_bits.get("frame")
            or frame_bits.get("payload")
        )
    bits = _strip_qpsk_tail_padding([int(b) for b in frame_bits])
    if len(bits) < HEADER_BITS + CRC_BITS:
        return {
            "length": 0,
            "payload": [],
            "crc": [],
            "checksum_pass": False,
            "crc_pass": False,
        }

    payload_end = len(bits) - CRC_BITS
    pre = bits[:32]
    length_field = bits[32:48]
    payload = bits[48:payload_end]
    crc_field = bits[payload_end:]
    length_val = bits_to_int(length_field)
    crc_val = bits_to_int(crc_field)

    return {
        "preamble": pre,
        "length": length_val,
        "payload": payload,
        "payload_bits": payload,
        "crc": crc_field,
        "crc_value": crc_val,
        "checksum_pass": None,
        "crc_pass": None,
    }
