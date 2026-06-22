from __future__ import annotations

import zlib


PREAMBLE_BITS = [0, 0, 0, 1, 1, 1, 1, 0] * 8
HEADER_BITS = 96


def _clean_bits(bits) -> list[int]:
    if isinstance(bits, str):
        return [1 if ch == "1" else 0 for ch in bits if ch in "01"]
    if hasattr(bits, "tolist"):
        bits = bits.tolist()
    return [1 if int(bit) else 0 for bit in list(bits)]


def int_to_bits(value: int, width: int) -> list[int]:
    value = int(value) & ((1 << width) - 1)
    return [(value >> shift) & 1 for shift in range(width - 1, -1, -1)]


def bits_to_int(bits) -> int:
    value = 0
    for bit in _clean_bits(bits):
        value = (value << 1) | bit
    return value


def crc32_bits(bits) -> int:
    data = "".join(str(bit) for bit in _clean_bits(bits)).encode("ascii")
    return zlib.crc32(data) & 0xFFFFFFFF


def build_frame(
    payload_bits,
    original_payload_length: int | None = None,
    checksum_payload_bits=None,
) -> dict:
    payload = _clean_bits(payload_bits)
    length = len(payload) if original_payload_length is None else int(original_payload_length)
    coded_length = len(payload)
    checksum_source = payload if checksum_payload_bits is None else _clean_bits(checksum_payload_bits)
    checksum = crc32_bits(checksum_source)
    header = int_to_bits(length, 32) + int_to_bits(coded_length, 32) + int_to_bits(checksum, 32)
    bits = PREAMBLE_BITS + header + payload
    return {
        "bits": bits,
        "preamble": PREAMBLE_BITS.copy(),
        "length": length,
        "coded_length": coded_length,
        "payload": payload,
        "checksum": checksum,
        "crc": checksum,
        "checksum_pass": crc32_bits(checksum_source) == checksum,
    }


def _preamble_start(bits: list[int]) -> int:
    if len(bits) < len(PREAMBLE_BITS):
        return 0
    if bits[: len(PREAMBLE_BITS)] == PREAMBLE_BITS:
        return 0
    search_end = min(256, len(bits) - len(PREAMBLE_BITS) + 1)
    best_index = 0
    best_errors = len(PREAMBLE_BITS) + 1
    for i in range(search_end):
        errors = sum(a != b for a, b in zip(bits[i : i + len(PREAMBLE_BITS)], PREAMBLE_BITS))
        if errors < best_errors:
            best_errors = errors
            best_index = i
    return best_index


def parse_frame(frame_or_bits) -> dict:
    if isinstance(frame_or_bits, dict):
        bits = _clean_bits(frame_or_bits.get("bits", frame_or_bits.get("frame", [])))
        if not bits and "payload" in frame_or_bits:
            payload = _clean_bits(frame_or_bits["payload"])
            return {
                "preamble": _clean_bits(frame_or_bits.get("preamble", PREAMBLE_BITS)),
                "length": int(frame_or_bits.get("length", len(payload))),
                "coded_length": int(frame_or_bits.get("coded_length", len(payload))),
                "payload": payload,
                "checksum": int(frame_or_bits.get("checksum", frame_or_bits.get("crc", crc32_bits(payload)))),
                "crc": int(frame_or_bits.get("checksum", frame_or_bits.get("crc", crc32_bits(payload)))),
                "checksum_pass": bool(frame_or_bits.get("checksum_pass", True)),
            }
    else:
        bits = _clean_bits(frame_or_bits)

    start = _preamble_start(bits)
    preamble_end = start + len(PREAMBLE_BITS)
    header_end = preamble_end + HEADER_BITS
    header = bits[preamble_end:header_end]
    if len(header) < HEADER_BITS:
        header = header + [0] * (HEADER_BITS - len(header))

    length = bits_to_int(header[:32])
    coded_length = bits_to_int(header[32:64])
    checksum = bits_to_int(header[64:96])
    payload_available = bits[header_end:]
    if coded_length < 0 or coded_length > len(payload_available):
        coded_length = len(payload_available)
    payload = payload_available[:coded_length]
    payload_crc = crc32_bits(payload)
    return {
        "preamble": bits[start:preamble_end],
        "length": length,
        "coded_length": coded_length,
        "payload": payload,
        "payload_bits": payload,
        "checksum": checksum,
        "crc": checksum,
        "checksum_pass": payload_crc == checksum,
        "preamble_start": start,
    }


frame_build = build_frame
create_frame = build_frame
make_frame = build_frame
frame_parse = parse_frame
extract_frame = parse_frame
decode_frame = parse_frame
