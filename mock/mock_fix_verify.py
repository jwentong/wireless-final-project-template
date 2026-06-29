"""Verify the DESIGN revision: protect frame-header length fields with 3x
repetition + majority vote, so a single bit error in the 32-bit length field no
longer breaks framing. Only variable changed vs mock_pipeline = header protection
(payload still uses the repetition-3 placeholder). Run from mock/ dir:
    python mock_fix_verify.py
"""
from __future__ import annotations

import numpy as np

from mock_pipeline import (
    PREAMBLE_BITS, PREAMBLE_LEN, _int_to_bits, _bits_to_int, crc16,
    source_encode, source_decode, scramble, descramble,
    channel_encode, channel_decode, qpsk_modulate, qpsk_demodulate,
    awgn, synchronize,
)


def repeat3(bits: list[int]) -> list[int]:
    out: list[int] = []
    for b in bits:
        out += [b, b, b]
    return out


def majority3(bits: list[int]) -> list[int]:
    out: list[int] = []
    for k in range(0, len(bits) - 2, 3):
        out.append(1 if (bits[k] + bits[k + 1] + bits[k + 2]) >= 2 else 0)
    return out


def build_frame_p(payload: list[int], orig_len: int | None = None) -> list[int]:
    payload = list(payload)
    coded_len = len(payload)
    if orig_len is None:
        orig_len = coded_len
    hdr_raw = _int_to_bits(orig_len, 32) + _int_to_bits(coded_len, 32)   # 64
    hdr_prot = repeat3(hdr_raw)                                          # 192 (protected)
    crc = _int_to_bits(crc16(hdr_raw + payload), 16)
    frame = PREAMBLE_BITS + hdr_prot + payload + crc
    if len(frame) % 2 != 0:
        frame.append(0)
    return frame


def parse_frame_p(frame_bits: list[int]) -> dict:
    bits = list(frame_bits)
    p = PREAMBLE_LEN
    hdr_raw = majority3(bits[p:p + 192])
    orig_len = _bits_to_int(hdr_raw[:32])
    coded_len = _bits_to_int(hdr_raw[32:64])
    payload = bits[p + 192:p + 192 + coded_len]
    return {"payload": payload, "length": orig_len, "coded_len": coded_len}


def transmit_p(text: str, seed: int = 2026) -> np.ndarray:
    orig = source_encode(text)
    coded = channel_encode(scramble(orig, seed))
    return qpsk_modulate(build_frame_p(coded, orig_len=len(orig)))


def receive_p(symbols: np.ndarray, seed: int = 2026) -> dict:
    start = synchronize(symbols, qpsk_modulate(PREAMBLE_BITS))
    parsed = parse_frame_p(qpsk_demodulate(symbols[start:]))
    orig = descramble(channel_decode(parsed["payload"]), seed)[:parsed["length"]]
    usable = orig[: (len(orig) // 8) * 8]
    try:
        text = source_decode(usable)
    except UnicodeDecodeError:
        text = "<decode-error>"
    return {"text": text, "parsed": parsed}


def main() -> None:
    SAMPLE = "无线通信技术课程要求学生理解调制、编码、信道和接收机处理。"
    exp_orig = len(source_encode(SAMPLE))
    exp_coded = 3 * exp_orig
    print("REVISION VERIFY: header length fields protected by 3x repetition")
    print("(payload still repetition-3 placeholder; only header protection added)")
    for snr in [4, 6, 8, 10, 12]:
        ok = hdr = other = 0
        for s in range(20):
            r = receive_p(awgn(transmit_p(SAMPLE), snr, 2026 + s))
            if r["text"] == SAMPLE:
                ok += 1
            elif r["parsed"]["length"] != exp_orig or r["parsed"]["coded_len"] != exp_coded:
                hdr += 1
            else:
                other += 1
        print(f"  SNR={snr:2d}dB  ok={ok:2d}/20  header_corrupt={hdr:2d}  other_fail={other:2d}")


if __name__ == "__main__":
    main()
