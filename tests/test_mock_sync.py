import numpy as np
from src.synchronization import detect_frame_start


class TestSynchronization:

    def test_detects_exact_offset(self, qpsk_preamble):
        rng = np.random.default_rng(2026)
        payload = np.array(
            [1 - 1j, -1 - 1j, 1 + 1j, -1 + 1j] * 20, dtype=complex
        ) / np.sqrt(2)
        prefix = (rng.normal(size=25) + 1j * rng.normal(size=25)) / np.sqrt(2)
        signal = np.concatenate([prefix, qpsk_preamble, payload]).tolist()
        start = detect_frame_start(signal, preamble=qpsk_preamble.tolist())
        assert abs(int(start) - 25) <= 1

    def test_no_offset_returns_zero(self, qpsk_preamble):
        payload = np.array(
            [1 - 1j, -1 - 1j, 1 + 1j, -1 + 1j] * 20, dtype=complex
        ) / np.sqrt(2)
        signal = np.concatenate([qpsk_preamble, payload]).tolist()
        start = detect_frame_start(signal, preamble=qpsk_preamble.tolist())
        assert start == 0

    def test_large_offset(self, qpsk_preamble):
        rng = np.random.default_rng(2026)
        payload = np.array(
            [1 - 1j, -1 - 1j, 1 + 1j, -1 + 1j] * 20, dtype=complex
        ) / np.sqrt(2)
        offset = 128
        prefix = (rng.normal(size=offset) + 1j * rng.normal(size=offset)) / np.sqrt(2)
        signal = np.concatenate([prefix, qpsk_preamble, payload]).tolist()
        start = detect_frame_start(signal, preamble=qpsk_preamble.tolist())
        assert abs(int(start) - offset) <= 2

    def test_returns_integer(self, qpsk_preamble):
        signal = qpsk_preamble.tolist() + [complex(0, 0)] * 10
        result = detect_frame_start(signal, preamble=qpsk_preamble.tolist())
        assert isinstance(result, int)

    def test_short_signal_returns_zero(self, qpsk_preamble):
        signal = [complex(1, 0)]
        result = detect_frame_start(signal, preamble=qpsk_preamble.tolist())
        assert result == 0
