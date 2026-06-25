"""Basic unit tests for wireless project modules."""

import numpy as np

from src.source import source_encode, source_decode
from src.crypto import scramble, descramble
from src.channel_coding import channel_encode, channel_decode
from src.framing import build_frame, parse_frame, frame_to_bits
from src.modulation import qpsk_modulate, qpsk_demodulate
from src.channel import awgn
from src.synchronization import synchronize


class TestSourceCodec:
    def test_roundtrip_chinese(self):
        text = "无线通信技术"
        bits = source_encode(text)
        assert len(bits) % 8 == 0
        assert source_decode(bits) == text

    def test_roundtrip_ascii(self):
        text = "Hello, World!"
        bits = source_encode(text)
        assert source_decode(bits) == text


class TestCrypto:
    def test_scramble_descramble(self):
        bits = [0, 1, 1, 0, 1, 0, 0, 1] * 50
        scrambled = scramble(bits, seed=2026)
        recovered = descramble(scrambled, seed=2026)
        assert recovered == bits


class TestChannelCoding:
    def test_noiseless_roundtrip(self):
        bits = [int(x) for x in np.random.default_rng(42).integers(0, 2, size=400)]
        coded = channel_encode(bits)
        decoded = channel_decode(coded)
        assert decoded[: len(bits)] == bits

    def test_single_error_correction(self):
        import numpy as np
        bits = [1, 0, 1, 0]  # 4 bits -> 7 bits
        coded = channel_encode(bits)
        # Flip one bit
        coded[2] ^= 1
        decoded = channel_decode(coded)
        assert decoded[:4] == bits


class TestFraming:
    def test_build_frame_fields(self):
        payload = [int(x) for x in np.random.default_rng(1).integers(0, 2, size=2400)]
        frame = build_frame(payload)
        assert "preamble" in str(frame).lower() or "preamble" in frame
        assert frame["length"] == 2400

    def test_roundtrip(self):
        payload = [int(x) for x in np.random.default_rng(2).integers(0, 2, size=257)]
        frame = build_frame(payload)
        parsed = parse_frame(frame)
        assert parsed["payload"][: len(payload)] == payload


class TestModulation:
    def test_constellation_quadrants(self):
        symbols = qpsk_modulate([0, 0, 0, 1, 1, 1, 1, 0])
        assert symbols[0].real > 0 and symbols[0].imag > 0  # 00 -> Q1
        assert symbols[1].real < 0 and symbols[1].imag > 0  # 01 -> Q2
        assert symbols[2].real < 0 and symbols[2].imag < 0  # 11 -> Q3
        assert symbols[3].real > 0 and symbols[3].imag < 0  # 10 -> Q4
        avg_power = float(np.mean(np.abs(symbols) ** 2))
        assert 0.8 <= avg_power <= 1.2

    def test_noiseless_roundtrip(self):
        bits = [int(x) for x in np.random.default_rng(3).integers(0, 2, size=512)]
        symbols = qpsk_modulate(bits)
        recovered = qpsk_demodulate(symbols)
        assert recovered[: len(bits)] == bits


class TestChannel:
    def test_reproducible(self):
        symbols = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]) / np.sqrt(2)
        out1 = awgn(symbols, snr_db=12, seed=2026)
        out2 = awgn(symbols, snr_db=12, seed=2026)
        assert np.allclose(out1, out2)


class TestSync:
    def test_detect_offset(self):
        rng = np.random.default_rng(2026)
        preamble = (
            np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j] * 8, dtype=complex)
            / np.sqrt(2)
        )
        payload = (
            np.array([1 - 1j, -1 - 1j, 1 + 1j, -1 + 1j] * 20, dtype=complex)
            / np.sqrt(2)
        )
        prefix = (rng.normal(size=25) + 1j * rng.normal(size=25)) / np.sqrt(2)
        received = np.concatenate([prefix, preamble, payload])
        start = synchronize(received, preamble=preamble)
        assert abs(int(start) - 25) <= 1
