import random
import zlib

from .channel_code import repetition_decode, repetition_encode
from .modulation import qpsk_modulate
from .source import bits_to_bytes

PREAMBLE_BITS = 128
HEADER_BITS = 64
HEADER_REPEAT = 3


def int_to_bits(value: int, width: int) -> list[int]:
    return [(value >> shift) & 1 for shift in range(width - 1, -1, -1)]


def bits_to_int(bits: list[int]) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def preamble_bits() -> list[int]:
    rng = random.Random(0x2026)
    return [rng.getrandbits(1) for _ in range(PREAMBLE_BITS)]


def preamble_symbols() -> list[complex]:
    return qpsk_modulate(preamble_bits())


def crc32_bits(payload_bits: list[int]) -> int:
    return zlib.crc32(bits_to_bytes(payload_bits)) & 0xFFFFFFFF


def build_frame(
    encoded_payload_bits: list[int], payload_bit_length: int | None = None, payload_crc32: int | None = None
) -> list[int]:
    if payload_bit_length is None:
        payload_bit_length = len(encoded_payload_bits)
    if payload_crc32 is None:
        payload_crc32 = crc32_bits(encoded_payload_bits)
    header = int_to_bits(payload_bit_length, 32) + int_to_bits(payload_crc32, 32)
    protected_header = repetition_encode(header, HEADER_REPEAT)
    return preamble_bits() + protected_header + list(encoded_payload_bits)


def parse_frame_bits(frame_bits_after_preamble: list[int]) -> tuple[int, int, list[int]]:
    protected_header_len = HEADER_BITS * HEADER_REPEAT
    if len(frame_bits_after_preamble) < protected_header_len:
        raise ValueError("frame is too short to contain protected header")
    header = repetition_decode(frame_bits_after_preamble[:protected_header_len], HEADER_REPEAT)
    payload_length = bits_to_int(header[:32])
    checksum = bits_to_int(header[32:64])
    encoded_payload = frame_bits_after_preamble[protected_header_len:]
    return payload_length, checksum, encoded_payload


def parse_frame(frame_bits: list[int]) -> dict:
    bits = [int(x) for x in frame_bits]
    preamble = preamble_bits()
    if bits[: len(preamble)] == preamble:
        bits = bits[len(preamble) :]
    payload_length, checksum, payload = parse_frame_bits(bits)
    return {
        "length": payload_length,
        "checksum": checksum,
        "crc32": checksum,
        "payload": payload[:payload_length],
        "payload_bits": payload[:payload_length],
    }


def find_frame_start(received_symbols: list[complex]) -> tuple[int, list[float]]:
    preamble = preamble_symbols()
    needed = len(preamble)
    if len(received_symbols) < needed:
        return 0, []
    peaks: list[float] = []
    best_index = 0
    best_score = -1.0
    preamble_energy = sum(abs(x) ** 2 for x in preamble) or 1.0
    for i in range(0, len(received_symbols) - needed + 1):
        window = received_symbols[i : i + needed]
        window_energy = sum(abs(x) ** 2 for x in window) or 1.0
        corr = sum(window[j] * preamble[j].conjugate() for j in range(needed))
        score = abs(corr) / ((window_energy * preamble_energy) ** 0.5)
        peaks.append(score)
        if score > best_score:
            best_score = score
            best_index = i
    return best_index, peaks


frame_build = build_frame
create_frame = build_frame
make_frame = build_frame
frame_parse = parse_frame
extract_frame = parse_frame
decode_frame = parse_frame
