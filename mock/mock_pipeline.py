"""Mock end-to-end skeleton to validate DESIGN.md BEFORE full TDD implementation.

Uses minimal / stub implementations (e.g. repetition-3 instead of convolutional
code) to verify module interfaces, frame structure, synchronization and the
end-to-end flow. Goal: expose design gaps early. This is NOT the production
implementation (that lives in src/). Run:  python mock/mock_pipeline.py
"""
from __future__ import annotations

import numpy as np


# --------------------------- Source coding ---------------------------
def source_encode(text: str) -> list[int]:
    bits: list[int] = []
    for byte in text.encode("utf-8"):
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def source_decode(bits: list[int]) -> str:
    out = bytearray()
    for k in range(len(bits) // 8):
        byte = 0
        for i in range(8):
            byte = (byte << 1) | bits[k * 8 + i]
        out.append(byte)
    return out.decode("utf-8")


# --------------------------- Scramble (PN XOR) ---------------------------
def _pn(n: int, seed: int) -> list[int]:
    return np.random.default_rng(seed).integers(0, 2, size=n).tolist()


def scramble(bits: list[int], seed: int = 2026) -> list[int]:
    return [b ^ p for b, p in zip(bits, _pn(len(bits), seed))]


def descramble(bits: list[int], seed: int = 2026) -> list[int]:
    return scramble(bits, seed)


# --------------------------- Channel coding (MOCK: repetition-3) ---------
def channel_encode(bits: list[int]) -> list[int]:
    out: list[int] = []
    for b in bits:
        out += [b, b, b]
    return out


def channel_decode(bits: list[int]) -> list[int]:
    out: list[int] = []
    for k in range(0, len(bits) - 2, 3):
        out.append(1 if (bits[k] + bits[k + 1] + bits[k + 2]) >= 2 else 0)
    return out


# --------------------------- Framing ---------------------------
BARKER13 = [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1]


def _preamble_bits() -> list[int]:
    bits: list[int] = []
    for c in BARKER13:
        bits += [0, 0] if c == 1 else [1, 1]
    return bits  # 26 bits -> 13 QPSK symbols


PREAMBLE_BITS = _preamble_bits()
PREAMBLE_LEN = len(PREAMBLE_BITS)


def _int_to_bits(x: int, n: int) -> list[int]:
    return [(x >> (n - 1 - i)) & 1 for i in range(n)]


def _bits_to_int(bits: list[int]) -> int:
    v = 0
    for b in bits:
        v = (v << 1) | int(b)
    return v


def crc16(bits: list[int]) -> int:
    """CRC-16-CCITT, poly 0x1021, init 0xFFFF (bit-wise, no reflection)."""
    reg = 0xFFFF
    for b in bits:
        msb = (reg >> 15) & 1
        reg = (reg << 1) & 0xFFFF
        if msb ^ (b & 1):
            reg ^= 0x1021
    return reg


def build_frame(payload: list[int], orig_len: int | None = None) -> list[int]:
    payload = list(payload)
    coded_len = len(payload)
    if orig_len is None:
        orig_len = coded_len
    header = _int_to_bits(orig_len, 32) + _int_to_bits(coded_len, 32)
    body = header + payload
    crc = _int_to_bits(crc16(body), 16)
    frame = PREAMBLE_BITS + body + crc
    if len(frame) % 2 != 0:
        frame.append(0)
    return frame


def parse_frame(frame_bits: list[int]) -> dict:
    bits = list(frame_bits)
    p = PREAMBLE_LEN
    orig_len = _bits_to_int(bits[p:p + 32])
    coded_len = _bits_to_int(bits[p + 32:p + 64])
    payload = bits[p + 64:p + 64 + coded_len]
    crc_field = bits[p + 64 + coded_len:p + 64 + coded_len + 16]
    body = bits[p:p + 64 + coded_len]
    crc_pass = len(crc_field) == 16 and _bits_to_int(crc_field) == crc16(body)
    return {"payload": payload, "length": orig_len, "coded_len": coded_len, "crc_pass": crc_pass}


# --------------------------- QPSK ---------------------------
_QPSK = {(0, 0): 1 + 1j, (0, 1): -1 + 1j, (1, 1): -1 - 1j, (1, 0): 1 - 1j}


def qpsk_modulate(bits: list[int]) -> np.ndarray:
    bits = list(bits)
    if len(bits) % 2 != 0:
        bits.append(0)
    syms = [_QPSK[(bits[k], bits[k + 1])] / np.sqrt(2) for k in range(0, len(bits), 2)]
    return np.array(syms, dtype=complex)


def qpsk_demodulate(symbols: np.ndarray) -> list[int]:
    bits: list[int] = []
    for s in symbols:
        bits.append(0 if s.imag >= 0 else 1)  # b0 from Q
        bits.append(0 if s.real >= 0 else 1)  # b1 from I
    return bits


# --------------------------- AWGN ---------------------------
def awgn(symbols: np.ndarray, snr_db: float = 12, seed: int = 2026) -> np.ndarray:
    symbols = np.asarray(symbols, dtype=complex)
    ps = float(np.mean(np.abs(symbols) ** 2))
    pn = ps / (10 ** (snr_db / 10))
    rng = np.random.default_rng(seed)
    noise = np.sqrt(pn / 2) * (rng.standard_normal(symbols.shape) + 1j * rng.standard_normal(symbols.shape))
    return symbols + noise


# --------------------------- Synchronization ---------------------------
def synchronize(received: np.ndarray, preamble: np.ndarray) -> int:
    received = np.asarray(received, dtype=complex)
    preamble = np.asarray(preamble, dtype=complex)
    n = len(received) - len(preamble) + 1
    if n <= 0:
        return 0
    pnorm = np.linalg.norm(preamble)
    corr = np.zeros(n)
    for d in range(n):
        window = received[d:d + len(preamble)]
        wnorm = np.linalg.norm(window)
        if wnorm > 0:
            corr[d] = np.abs(np.vdot(preamble, window)) / (pnorm * wnorm)
    return int(np.argmax(corr))


# --------------------------- End-to-end ---------------------------
def transmit(text: str, seed: int = 2026) -> np.ndarray:
    orig = source_encode(text)
    coded = channel_encode(scramble(orig, seed))
    frame = build_frame(coded, orig_len=len(orig))
    return qpsk_modulate(frame)


def receive(symbols: np.ndarray, seed: int = 2026) -> dict:
    preamble_syms = qpsk_modulate(PREAMBLE_BITS)
    start = synchronize(symbols, preamble_syms)
    frame_bits = qpsk_demodulate(symbols[start:])
    parsed = parse_frame(frame_bits)
    scr = channel_decode(parsed["payload"])
    orig = descramble(scr, seed)[:parsed["length"]]
    usable = orig[: (len(orig) // 8) * 8]
    try:
        text = source_decode(usable)
    except UnicodeDecodeError:
        text = "<decode-error>"
    return {"text": text, "start": start, "parsed": parsed}


def channel_with_offset(symbols, snr_db, seed, offset):
    rng = np.random.default_rng(seed + 777)
    prefix = (rng.standard_normal(offset) + 1j * rng.standard_normal(offset)) / np.sqrt(2)
    return awgn(np.concatenate([prefix, symbols]), snr_db, seed)


# --------------------------- Mock test runner ---------------------------
def main() -> None:
    SAMPLE = "无线通信技术课程要求学生理解调制、编码、信道和接收机处理。"
    print("=" * 64)
    print("MOCK TEST RUN (skeleton; channel code = repetition-3 placeholder)")
    print("=" * 64)

    # mock test 1: source codec reversible
    b = source_encode(SAMPLE)
    ok1 = (source_decode(b) == SAMPLE) and (len(b) % 8 == 0)
    print(f"[mock-1] source round-trip: {'PASS' if ok1 else 'FAIL'} (bits={len(b)})")

    # mock test 2: frame build/parse reversible
    payload = np.random.default_rng(1).integers(0, 2, 257).tolist()
    fr = build_frame(payload)
    pr = parse_frame(fr)
    ok2 = pr["payload"][:257] == payload and pr["length"] == 257 and pr["crc_pass"]
    print(f"[mock-2] frame round-trip: {'PASS' if ok2 else 'FAIL'} (frame_len={len(fr)}, crc_pass={pr['crc_pass']})")

    # mock test 3: sync detects offset
    syms = transmit(SAMPLE)
    rx = channel_with_offset(syms, 12, 2026, 25)
    st = synchronize(rx, qpsk_modulate(PREAMBLE_BITS))
    ok3 = abs(st - 25) <= 1
    print(f"[mock-3] sync offset detect: {'PASS' if ok3 else 'FAIL'} (detected={st}, expected=25)")

    # mock test 4: e2e noiseless
    r4 = receive(transmit(SAMPLE))
    ok4 = r4["text"] == SAMPLE
    print(f"[mock-4] e2e noiseless: {'PASS' if ok4 else 'FAIL'}")

    # mock test 5: e2e AWGN 12 dB (single seed)
    r5 = receive(awgn(transmit(SAMPLE), 12, 2026))
    ok5 = r5["text"] == SAMPLE
    print(f"[mock-5] e2e AWGN 12dB seed2026: {'PASS' if ok5 else 'FAIL'}")

    # mock test 6: robustness sweep -- classify failures (exposes design gaps)
    print("[mock-6] robustness sweep (20 seeds per SNR):")
    exp_orig = len(source_encode(SAMPLE))
    exp_coded = 3 * exp_orig
    for snr in [4, 6, 8, 10, 12]:
        ok = hdr = other = 0
        for s in range(20):
            r = receive(awgn(transmit(SAMPLE), snr, 2026 + s))
            if r["text"] == SAMPLE:
                ok += 1
            elif r["parsed"]["length"] != exp_orig or r["parsed"]["coded_len"] != exp_coded:
                hdr += 1   # length/header field corrupted -> framing breaks
            else:
                other += 1
        print(f"        SNR={snr:2d}dB  ok={ok:2d}/20  header_corrupt={hdr:2d}  other_fail={other:2d}")


if __name__ == "__main__":
    main()
