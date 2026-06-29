"""Framing: build and parse the transmission frame.

Frame layout (bits, MSB-first):
    preamble(26) | orig_len*3(96) | coded_len*3(96) | payload | CRC-16(16) | pad

The two 32-bit length fields are protected by 3x repetition + majority vote
(design revision v0.2, see MOCK_TEST_REPORT.md): because the PRD link order puts
channel coding *before* framing, the length fields are otherwise outside FEC
protection and a single bit error would break framing. ``orig_len`` is the
original payload bit count (for UTF-8 recovery / de-padding); ``coded_len`` is
the in-frame payload bit count (for locating payload and CRC).
"""
from __future__ import annotations

from src.metrics import crc16

# Barker-13 sequence; mapped +1->bits "00", -1->bits "11" so the QPSK-modulated
# preamble lands on the main diagonal with low autocorrelation sidelobes.
BARKER13 = [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1]
_LEN_BITS = 32
_CRC_BITS = 16


def _preamble_bits() -> list[int]:
    bits: list[int] = []
    for chip in BARKER13:
        bits += [0, 0] if chip == 1 else [1, 1]
    return bits


PREAMBLE_BITS = _preamble_bits()
PREAMBLE_LEN = len(PREAMBLE_BITS)  # 26
_HDR_PROT = 6 * _LEN_BITS          # 192 (two 32-bit fields, 3x repeated)


def _int_to_bits(x: int, n: int) -> list[int]:
    return [(x >> (n - 1 - i)) & 1 for i in range(n)]


def _bits_to_int(bits: list[int]) -> int:
    v = 0
    for b in bits:
        v = (v << 1) | int(b)
    return v


def _repeat3(bits: list[int]) -> list[int]:
    out: list[int] = []
    for b in bits:
        out += [b, b, b]
    return out


def _majority3(bits: list[int]) -> list[int]:
    out: list[int] = []
    for k in range(0, len(bits) - 2, 3):
        out.append(1 if (int(bits[k]) + int(bits[k + 1]) + int(bits[k + 2])) >= 2 else 0)
    return out


def build_frame(payload: list[int], orig_len: int | None = None) -> list[int]:
    """Serialize a frame. ``orig_len`` defaults to ``len(payload)``.

    Returns a flat bit list (preamble + protected header + payload + CRC + pad).
    """
    payload = [int(b) for b in payload]
    coded_len = len(payload)
    if orig_len is None:
        orig_len = coded_len
    hdr_raw = _int_to_bits(orig_len, _LEN_BITS) + _int_to_bits(coded_len, _LEN_BITS)
    crc = _int_to_bits(crc16(hdr_raw + payload), _CRC_BITS)
    frame = PREAMBLE_BITS + _repeat3(hdr_raw) + payload + crc
    if len(frame) % 2 != 0:
        frame.append(0)  # pad to even length for QPSK alignment
    return frame


def parse_frame(frame_bits: list[int]) -> dict:
    """Parse a frame (preamble-aligned). Returns payload, lengths and CRC status."""
    bits = [int(b) for b in frame_bits]
    p = PREAMBLE_LEN
    hdr_raw = _majority3(bits[p:p + _HDR_PROT])
    orig_len = _bits_to_int(hdr_raw[:_LEN_BITS])
    coded_len = _bits_to_int(hdr_raw[_LEN_BITS:2 * _LEN_BITS])
    body_start = p + _HDR_PROT
    payload = bits[body_start:body_start + coded_len]
    crc_field = bits[body_start + coded_len:body_start + coded_len + _CRC_BITS]
    crc_pass = len(crc_field) == _CRC_BITS and _bits_to_int(crc_field) == crc16(hdr_raw + payload)
    return {
        "payload": payload,
        "length": orig_len,
        "coded_len": coded_len,
        "crc_pass": crc_pass,
        "preamble": PREAMBLE_BITS,
    }
