import numpy as np

from src.modulation import (
    qpsk_modulate, qpsk_demodulate,
    bpsk_modulate, bpsk_demodulate,
    qam16_modulate, qam16_demodulate,
    modulate, demodulate, bits_per_symbol,
)


def test_qpsk_quadrants_and_unit_power():
    syms = qpsk_modulate([0, 0, 0, 1, 1, 1, 1, 0])
    expected = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    for s, (si, sq) in zip(syms, expected):
        assert np.sign(s.real) == si and np.sign(s.imag) == sq
    assert 0.8 <= float(np.mean(np.abs(syms) ** 2)) <= 1.2


def test_qpsk_roundtrip():
    bits = np.random.default_rng(1).integers(0, 2, 512).tolist()
    assert qpsk_demodulate(qpsk_modulate(bits))[:512] == bits


def test_qpsk_odd_length_padding():
    assert len(qpsk_modulate([1, 0, 1])) == 2


def test_bpsk_roundtrip_and_power():
    bits = np.random.default_rng(2).integers(0, 2, 256).tolist()
    syms = bpsk_modulate(bits)
    assert bpsk_demodulate(syms) == bits
    assert abs(float(np.mean(np.abs(syms) ** 2)) - 1.0) < 1e-9


def test_qam16_roundtrip_and_power():
    bits = np.random.default_rng(3).integers(0, 2, 4 * 256).tolist()
    syms = qam16_modulate(bits)
    assert qam16_demodulate(syms)[:len(bits)] == bits
    assert 0.8 <= float(np.mean(np.abs(syms) ** 2)) <= 1.2


def test_dispatcher_and_bps():
    assert bits_per_symbol("qpsk") == 2 and bits_per_symbol("bpsk") == 1 and bits_per_symbol("16qam") == 4
    bits = [1, 0, 1, 1, 0, 0, 1, 0]
    assert demodulate(modulate(bits, "16qam"), "16qam")[:len(bits)] == bits
