import numpy as np

from src.channel import awgn, rayleigh
from src.channel_coding import channel_decode, channel_encode
from src.modulation import qpsk_modulate
from src.scramble import descramble, scramble
from src.synchronization import synchronize


def test_scramble_and_channel_coding_are_reversible():
    bits = [int(x) for x in np.random.default_rng(7).integers(0, 2, size=67)]
    assert descramble(scramble(bits, seed=99), seed=99) == bits
    assert channel_decode(channel_encode(bits), original_len=len(bits)) == bits


def test_awgn_fixed_seed_is_reproducible():
    symbols = qpsk_modulate([0, 0, 0, 1, 1, 1, 1, 0])
    assert np.allclose(awgn(symbols, snr_db=12, seed=2026), awgn(symbols, snr_db=12, seed=2026))


def test_rayleigh_fixed_seed_is_reproducible_and_returns_channel_state():
    symbols = qpsk_modulate([0, 0, 0, 1, 1, 1, 1, 0])
    out1, h1 = rayleigh(symbols, snr_db=18, seed=2026, return_h=True)
    out2, h2 = rayleigh(symbols, snr_db=18, seed=2026, return_h=True)
    assert np.allclose(out1, out2)
    assert h1 == h2
    assert abs(h1) > 0


def test_synchronization_detects_25_symbol_offset():
    rng = np.random.default_rng(2026)
    preamble = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j] * 8, dtype=complex) / np.sqrt(2)
    payload = np.array([1 - 1j, -1 - 1j, 1 + 1j, -1 + 1j] * 20, dtype=complex) / np.sqrt(2)
    prefix = (rng.normal(size=25) + 1j * rng.normal(size=25)) / np.sqrt(2)
    result = synchronize(np.concatenate([prefix, preamble, payload]), preamble=preamble)
    assert abs(result["start_index"] - 25) <= 1