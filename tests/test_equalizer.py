import numpy as np

from src.equalizer import zf_equalize, mmse_equalize


def test_zf_recovers_known_channel():
    s = np.array([1 + 1j, -1 - 1j, 1 - 1j]) / np.sqrt(2)
    h = np.full(3, 0.8 - 0.6j)
    assert np.allclose(zf_equalize(h * s, h), s)


def test_mmse_close_at_high_snr():
    s = np.array([1 + 1j, -1 + 1j]) / np.sqrt(2)
    h = np.full(2, 0.7 + 0.7j)
    assert np.allclose(mmse_equalize(h * s, h, 40), s, atol=1e-1)


def test_mmse_beats_zf_at_low_snr():
    rng = np.random.default_rng(0)
    n = 5000
    s = (2 * rng.integers(0, 2, n) - 1 + 1j * (2 * rng.integers(0, 2, n) - 1)) / np.sqrt(2)
    h = np.full(n, 0.3 + 0.1j)  # weak channel: ZF amplifies noise
    snr_db = 5
    # noise power relative to the unit-power signal (matches the channel SNR
    # convention and the 1/SNR term in the MMSE formula)
    pn = 1.0 / (10 ** (snr_db / 10))
    noise = np.sqrt(pn / 2) * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
    rx = h * s + noise
    err_zf = np.mean(np.abs(zf_equalize(rx, h) - s) ** 2)
    err_mmse = np.mean(np.abs(mmse_equalize(rx, h, snr_db) - s) ** 2)
    assert err_mmse < err_zf
