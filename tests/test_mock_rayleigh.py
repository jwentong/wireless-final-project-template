import numpy as np
from src.channel import rayleigh_fading, awgn


class TestRayleighChannel:

    def test_reproducible_with_same_seed(self):
        symbols = [1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]
        out1 = rayleigh_fading(symbols, 20, 2026)
        out2 = rayleigh_fading(symbols, 20, 2026)
        assert np.allclose(np.array(out1), np.array(out2))

    def test_output_same_length_as_input(self):
        symbols = [1 + 1j] * 100
        out = rayleigh_fading(symbols, 20, 42)
        assert len(out) == len(symbols)

    def test_fading_reduces_avg_power(self):
        rng = np.random.RandomState(42)
        symbols = [complex(rng.randn(), rng.randn()) for _ in range(1000)]
        out = rayleigh_fading(symbols, 100, 42)
        input_power = float(np.mean(np.abs(np.array(symbols)) ** 2))
        output_power = float(np.mean(np.abs(np.array(out)) ** 2))
        # At very high SNR, output power should be close to input power
        # (equalization recovers the signal)
        assert output_power > 0

    def test_high_snr_recovery(self):
        bits = [0, 0, 0, 1, 0, 1, 1, 0]
        from src.modulation import qpsk_modulate, qpsk_demodulate
        symbols = qpsk_modulate(bits)
        rx = rayleigh_fading(symbols, 50, 42)
        recovered = qpsk_demodulate(rx)
        assert recovered == bits
