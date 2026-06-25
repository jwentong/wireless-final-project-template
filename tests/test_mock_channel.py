import numpy as np
from src.channel import awgn


class TestAWGNChannel:

    @staticmethod
    def _sample_symbols():
        return [complex(1, 1), complex(-1, 1), complex(-1, -1), complex(1, -1)]

    def test_reproducible_with_same_seed(self):
        symbols = self._sample_symbols()
        noisy1 = awgn(symbols, 10.0, 42)
        noisy2 = awgn(symbols, 10.0, 42)
        assert noisy1 == noisy2

    def test_different_seed_gives_different_output(self):
        symbols = self._sample_symbols()
        noisy1 = awgn(symbols, 10.0, 42)
        noisy2 = awgn(symbols, 10.0, 99)
        assert noisy1 != noisy2

    def test_higher_snr_less_noise(self):
        symbols = self._sample_symbols()
        noisy_low = awgn(symbols, 0.0, 42)
        noisy_high = awgn(symbols, 20.0, 42)
        low_var = np.var([(s - t) for s, t in zip(noisy_low, symbols)])
        high_var = np.var([(s - t) for s, t in zip(noisy_high, symbols)])
        assert low_var > high_var

    def test_mean_noise_approx_zero(self):
        symbols = [complex(0, 0)] * 10000
        noisy = awgn(symbols, 10.0, 42)
        mean_noise = np.mean(noisy)
        assert abs(mean_noise.real) < 0.05
        assert abs(mean_noise.imag) < 0.05

    def test_output_same_length_as_input(self):
        symbols = self._sample_symbols()
        noisy = awgn(symbols, 12.0, 2026)
        assert len(noisy) == len(symbols)

    def test_snr_zero_db_noise_equals_signal_power(self):
        symbols = [complex(1, 0)] * 10000
        noisy = awgn(symbols, 0.0, 42)
        noise = [n - s for n, s in zip(noisy, symbols)]
        noise_power = np.mean(np.abs(np.array(noise)) ** 2)
        signal_power = np.mean(np.abs(symbols) ** 2)
        assert abs(noise_power / signal_power - 1.0) < 0.15
