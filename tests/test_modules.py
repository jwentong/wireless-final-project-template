"""补充自测：不同长度文本端到端一致性 + 低SNR不崩溃 + 同步偏移鲁棒性"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from src.source import source_encode, source_decode
from src.scramble import scramble, descramble
from src.channel_coding import channel_encode, channel_decode
from src.framing import build_frame, parse_frame
from src.modulation import qpsk_modulate, qpsk_demodulate
from src.channel import awgn
from src.synchronization import synchronize


def test_source_roundtrip_various_lengths():
    for text in ["", "a", "无线通信", "Hello 无线通信 123", "无" * 200]:
        bits = source_encode(text)
        assert source_decode(bits) == text


def test_scramble_roundtrip():
    bits = np.random.default_rng(1).integers(0, 2, size=999).tolist()
    s = scramble(bits, seed=42)
    assert descramble(s, seed=42) == bits


def test_channel_coding_roundtrip_noiseless():
    bits = np.random.default_rng(2).integers(0, 2, size=300).tolist()
    coded = channel_encode(bits)
    assert channel_decode(coded) == bits


def test_frame_roundtrip_various_lengths():
    for n in [1, 7, 100, 2401]:
        payload = np.random.default_rng(n).integers(0, 2, size=n).tolist()
        frame = build_frame(payload)
        parsed = parse_frame(frame)
        assert parsed["payload"] == payload
        assert parsed["checksum_pass"] is True


def test_qpsk_roundtrip_noiseless():
    bits = np.random.default_rng(3).integers(0, 2, size=1000).tolist()
    symbols = qpsk_modulate(bits)
    demod = qpsk_demodulate(symbols)
    assert demod[: len(bits)] == bits


def test_awgn_reproducible():
    symbols = np.array([1 + 1j, -1 - 1j], dtype=complex)
    a = awgn(symbols, snr_db=10, seed=5)
    b = awgn(symbols, snr_db=10, seed=5)
    assert np.allclose(a, b)


def test_sync_various_offsets():
    preamble = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j] * 8, dtype=complex) / np.sqrt(2)
    payload = np.array([1 - 1j, -1 - 1j, 1 + 1j, -1 + 1j] * 30, dtype=complex) / np.sqrt(2)
    for offset in [0, 10, 60, 120]:
        rng = np.random.default_rng(offset)
        prefix = (rng.normal(size=offset) + 1j * rng.normal(size=offset)) / np.sqrt(2)
        received = np.concatenate([prefix, preamble, payload])
        start = synchronize(received, preamble=preamble)
        assert abs(start - offset) <= 1


def test_low_snr_does_not_crash():
    bits = np.random.default_rng(9).integers(0, 2, size=200).tolist()
    coded = channel_encode(bits)
    symbols = qpsk_modulate(coded)
    noisy = awgn(symbols, snr_db=-5, seed=9)
    demod = qpsk_demodulate(noisy)
    decoded = channel_decode(demod[: len(coded)])
    assert len(decoded) == len(bits)  # 不崩溃，能正常输出（不要求内容完全正确）
