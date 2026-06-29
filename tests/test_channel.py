import numpy as np

from src.channel import awgn, rayleigh, rician


def _qpsk_symbols(n, seed):
    rng = np.random.default_rng(seed)
    re = 2 * rng.integers(0, 2, n) - 1
    im = 2 * rng.integers(0, 2, n) - 1
    return (re + 1j * im) / np.sqrt(2)


def test_awgn_reproducible_same_seed():
    s = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]) / np.sqrt(2)
    assert np.allclose(awgn(s, 12, 2026), awgn(s, 12, 2026))


def test_awgn_differs_with_seed():
    s = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]) / np.sqrt(2)
    assert not np.allclose(awgn(s, 12, 1), awgn(s, 12, 2))


def test_awgn_measured_snr_matches_setting():
    syms = _qpsk_symbols(20000, 5)
    out = awgn(syms, 10, 7)
    noise = out - syms
    measured = 10 * np.log10(np.mean(np.abs(syms) ** 2) / np.mean(np.abs(noise) ** 2))
    assert abs(measured - 10) < 1.0


def test_awgn_high_snr_negligible():
    s = np.array([1 + 1j, -1 + 1j]) / np.sqrt(2)
    assert np.allclose(awgn(s, 60, 1), s, atol=1e-2)


def test_rayleigh_returns_gain_and_shape():
    s = np.ones(50, dtype=complex)
    rx, h = rayleigh(s, 30, 3)
    assert rx.shape == s.shape and h.shape == s.shape


def test_rician_strong_los_has_nonzero_mean_gain():
    s = np.ones(2000, dtype=complex)
    _, h = rician(s, 40, 3, k_factor=10, block_fading=False)
    assert abs(np.mean(h)) > 0.5
