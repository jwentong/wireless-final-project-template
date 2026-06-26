"""Mock tests MK-001 ~ MK-006 from TEST_PLAN.md."""

import numpy as np

from src.channel import awgn
from src.channel_coding import channel_decode, channel_encode
from src.framing import build_frame, parse_frame
from src.modulation import qpsk_demodulate, qpsk_modulate
from src.scramble import descramble, scramble
from src.source import source_encode
from src.synchronization import detect_frame_start
from src.utils import crc16_ccitt, preamble_bits, verify_crc16


def test_mk001_frame_structure():
    """MK-001: frame field order and sizes."""
    source = source_encode("测试")
    coded = channel_encode(scramble(source, seed=2026))
    frame = build_frame(coded, source_bits_for_crc=source)
    bits = frame["bits"]
    assert bits[:32] == preamble_bits()
    assert frame["length"] == len(source)
    assert len(bits) == 32 + 16 + len(coded) + 16


def test_mk002_odd_payload_padding():
    """MK-002: odd frame bitstream QPSK padding."""
    payload = [1] * 255
    frame = build_frame(payload)
    symbols = qpsk_modulate(frame["bits"])
    recovered_bits = qpsk_demodulate(symbols)
    parsed = parse_frame(recovered_bits)
    assert parsed["length"] == 255
    assert parsed["payload"] == payload


def test_mk003_sync_offsets():
    """MK-003: sync at offset 0, 25, 128."""
    pre = qpsk_modulate(preamble_bits())
    body = qpsk_modulate([0, 1, 1, 0] * 20)
    rng = np.random.default_rng(2026)
    for offset in (0, 25, 128):
        prefix = (rng.normal(size=offset) + 1j * rng.normal(size=offset)) / np.sqrt(2) if offset else np.array([], dtype=complex)
        rx = np.concatenate([prefix, pre, body])
        start = detect_frame_start(rx, pre)
        assert abs(start - offset) <= 1


def test_mk004_repetition_corrects_one_error():
    """MK-004: (3,1) majority vote corrects single-bit error."""
    bits = [1, 0, 1, 1, 0]
    coded = channel_encode(bits)
    corrupted = coded.copy()
    corrupted[1] = 1 - corrupted[1]
    assert channel_decode(corrupted) == bits


def test_mk005_awgn_reproducible_seeds():
    """MK-005: AWGN reproducible for multiple seeds."""
    symbols = np.array([1 + 1j, -1 + 1j], dtype=complex) / np.sqrt(2)
    for seed in (2026, 2027, 9999):
        a = awgn(symbols, snr_db=12, seed=seed)
        b = awgn(symbols, snr_db=12, seed=seed)
        assert np.allclose(a, b)


def test_mk006_crc16_source_bits():
    """MK-006: CRC-16 over source-encoded bits."""
    source = source_encode("CRC校验测试")
    crc_val = crc16_ccitt(source)
    assert verify_crc16(source, crc_val)
    assert not verify_crc16(source + [1], crc_val)
