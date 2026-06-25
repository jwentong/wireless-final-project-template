import numpy as np
from src.modulation import (
    qpsk_modulate, qpsk_demodulate,
    bpsk_modulate, bpsk_demodulate,
    qam16_modulate, qam16_demodulate,
)


class TestQPSKModulation:

    def test_gray_mapping_quadrant_q1(self):
        sym = qpsk_modulate([0, 0])[0]
        assert sym.real > 0 and sym.imag > 0

    def test_gray_mapping_quadrant_q2(self):
        sym = qpsk_modulate([0, 1])[0]
        assert sym.real < 0 and sym.imag > 0

    def test_gray_mapping_quadrant_q3(self):
        sym = qpsk_modulate([1, 1])[0]
        assert sym.real < 0 and sym.imag < 0

    def test_gray_mapping_quadrant_q4(self):
        sym = qpsk_modulate([1, 0])[0]
        assert sym.real > 0 and sym.imag < 0

    def test_normalized_symbol_power(self):
        dibits = [[0, 0], [0, 1], [1, 1], [1, 0]]
        symbols = qpsk_modulate([b for pair in dibits for b in pair])
        avg_power = np.mean(np.abs(symbols) ** 2)
        assert abs(avg_power - 1.0) < 1e-10

    def test_noiseless_loopback(self):
        bits = [0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1]
        symbols = qpsk_modulate(bits)
        recovered = qpsk_demodulate(symbols)
        assert recovered == bits

    def test_odd_bit_count_auto_padding(self):
        bits = [1, 0, 1]
        symbols = qpsk_modulate(bits)
        assert len(symbols) == 2  # padded to 4 bits = 2 symbols

    def test_demodulate_all_four_quadrants(self):
        for dibit in [[0, 0], [0, 1], [1, 1], [1, 0]]:
            sym = qpsk_modulate(dibit)[0]
            recovered = qpsk_demodulate([sym])
            assert recovered == dibit

    def test_symbols_are_normalized(self):
        symbols = qpsk_modulate([0, 0, 0, 1, 1, 1, 1, 0])
        for s in symbols:
            assert abs(abs(s) - 1.0) < 1e-10


class TestBPSKModulation:

    def test_bit_0_maps_to_positive_real(self):
        sym = bpsk_modulate([0])[0]
        assert sym.real > 0 and abs(sym.imag) < 1e-15

    def test_bit_1_maps_to_negative_real(self):
        sym = bpsk_modulate([1])[0]
        assert sym.real < 0 and abs(sym.imag) < 1e-15

    def test_normalized_power(self):
        symbols = bpsk_modulate([0, 1, 0, 1])
        avg_power = np.mean(np.abs(symbols) ** 2)
        assert abs(avg_power - 1.0) < 1e-10

    def test_noiseless_loopback(self):
        bits = [0, 1, 0, 1, 1, 0, 0, 1, 1, 1]
        symbols = bpsk_modulate(bits)
        recovered = bpsk_demodulate(symbols)
        assert recovered == bits

    def test_all_symbols_unit_magnitude(self):
        symbols = bpsk_modulate([0, 1, 0, 0, 1, 1])
        for s in symbols:
            assert abs(abs(s) - 1.0) < 1e-10


class TestQAM16Modulation:

    def test_gray_mapping_quadrant_q1(self):
        sym = qam16_modulate([1, 1, 1, 1])[0]
        assert sym.real > 0 and sym.imag > 0

    def test_gray_mapping_quadrant_q2(self):
        sym = qam16_modulate([0, 1, 1, 1])[0]
        assert sym.real < 0 and sym.imag > 0

    def test_gray_mapping_quadrant_q3(self):
        sym = qam16_modulate([0, 0, 0, 0])[0]
        assert sym.real < 0 and sym.imag < 0

    def test_gray_mapping_quadrant_q4(self):
        sym = qam16_modulate([1, 1, 0, 0])[0]
        assert sym.real > 0 and sym.imag < 0

    def test_normalized_power(self):
        all_bits = []
        for b0 in (0, 1):
            for b1 in (0, 1):
                for b2 in (0, 1):
                    for b3 in (0, 1):
                        all_bits.extend([b0, b1, b2, b3])
        symbols = qam16_modulate(all_bits)
        avg_power = np.mean(np.abs(symbols) ** 2)
        assert abs(avg_power - 1.0) < 1e-10

    def test_noiseless_loopback(self):
        bits = [0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1]
        symbols = qam16_modulate(bits)
        recovered = qam16_demodulate(symbols)
        assert recovered == bits

    def test_quadbit_count_auto_padding(self):
        bits = [1, 0, 1]
        symbols = qam16_modulate(bits)
        assert len(symbols) == 1

    def test_demodulate_all_sixteen_points(self):
        for b0 in (0, 1):
            for b1 in (0, 1):
                for b2 in (0, 1):
                    for b3 in (0, 1):
                        quadbit = [b0, b1, b2, b3]
                        sym = qam16_modulate(quadbit)[0]
                        recovered = qam16_demodulate([sym])
                        assert recovered == quadbit
