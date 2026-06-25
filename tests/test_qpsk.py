"""
单元测试 - QPSK 调制解调模块
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.qpsk import (
    qpsk_modulate,
    qpsk_demodulate,
    get_constellation_points,
    QPSK_MAPPING
)


class TestQPSKModulation:
    """QPSK 调制测试类"""

    def test_modulate_empty_bits(self):
        """测试空比特流调制"""
        symbols = qpsk_modulate(np.array([], dtype=np.int8))
        assert len(symbols) == 0
        assert padded == False

    def test_modulate_single_symbol(self):
        """测试单符号调制"""
        bits = np.array([0, 0], dtype=np.int8)
        symbols = qpsk_modulate(bits)
        assert len(symbols) == 1

    def test_modulate_padding(self):
        """测试奇数长度比特流 padding"""
        bits = np.array([0, 0, 1], dtype=np.int8)
        symbols = qpsk_modulate(bits)
        assert padded == True
        assert len(symbols) == 2  # 3 bits -> 4 bits (padded) -> 2 symbols

    def test_no_padding_even_bits(self):
        """测试偶数长度比特流无 padding"""
        bits = np.array([0, 0, 1, 1], dtype=np.int8)
        symbols = qpsk_modulate(bits)
        assert padded == False

    def test_gray_mapping_00(self):
        """测试 00 映射到第一象限"""
        bits = np.array([0, 0], dtype=np.int8)
        symbols = qpsk_modulate(bits, normalize=False)
        assert symbols[0].real > 0  # 实部 > 0
        assert symbols[0].imag > 0  # 虚部 > 0

    def test_gray_mapping_01(self):
        """测试 01 映射到第二象限"""
        bits = np.array([0, 1], dtype=np.int8)
        symbols = qpsk_modulate(bits, normalize=False)
        assert symbols[0].real < 0  # 实部 < 0
        assert symbols[0].imag > 0  # 虚部 > 0

    def test_gray_mapping_11(self):
        """测试 11 映射到第三象限"""
        bits = np.array([1, 1], dtype=np.int8)
        symbols = qpsk_modulate(bits, normalize=False)
        assert symbols[0].real < 0  # 实部 < 0
        assert symbols[0].imag < 0  # 虚部 < 0

    def test_gray_mapping_10(self):
        """测试 10 映射到第四象限"""
        bits = np.array([1, 0], dtype=np.int8)
        symbols = qpsk_modulate(bits, normalize=False)
        assert symbols[0].real > 0  # 实部 > 0
        assert symbols[0].imag < 0  # 虚部 < 0

    def test_symbol_power_normalized(self):
        """测试符号功率归一化"""
        bits = np.random.randint(0, 2, 1000, dtype=np.int8)
        symbols = qpsk_modulate(bits, normalize=True)

        # 平均功率应接近 1
        avg_power = np.mean(np.abs(symbols) ** 2)
        assert abs(avg_power - 1.0) < 0.1


class TestQPSKDemodulation:
    """QPSK 解调测试类"""

    def test_demodulate_empty_symbols(self):
        """测试空符号解调"""
        bits = qpsk_demodulate(np.array([], dtype=np.complex128))
        assert len(bits) == 0

    def test_demodulate_single_symbol(self):
        """测试单符号解调"""
        symbols = np.array([1 + 1j], dtype=np.complex128) / np.sqrt(2)
        bits = qpsk_demodulate(symbols)
        assert len(bits) == 2
        assert bits[0] == 0 and bits[1] == 0

    def test_modulate_demodulate_no_noise(self):
        """测试无噪声调制解调可逆性"""
        test_bits = np.random.randint(0, 2, 100, dtype=np.int8)

        symbols = qpsk_modulate(test_bits)
        decoded_bits = qpsk_demodulate(symbols)

        # 如果有 padding，去除最后填充的比特
        if padded:
            decoded_bits = decoded_bits[:len(test_bits)]

        assert np.array_equal(test_bits, decoded_bits)

    def test_modulate_demodulate_with_noise(self):
        """测试有噪声调制解调（BER 应该较低）"""
        test_bits = np.random.randint(0, 2, 1000, dtype=np.int8)

        symbols = qpsk_modulate(test_bits)

        # 添加小噪声
        noise = 0.1 * (np.random.randn(len(symbols)) + 1j * np.random.randn(len(symbols)))
        noisy_symbols = symbols + noise

        decoded_bits = qpsk_demodulate(noisy_symbols)

        if padded:
            decoded_bits = decoded_bits[:len(test_bits)]

        # BER 应该较低
        ber = np.sum(test_bits != decoded_bits) / len(test_bits)
        assert ber < 0.1  # 小噪声下 BER < 10%


class TestQPSKConstellation:
    """QPSK 星座点测试类"""

    def test_constellation_points_count(self):
        """测试星座点数量"""
        constellation = get_constellation_points()
        assert len(constellation) == 4

    def test_constellation_points_normalized(self):
        """测试星座点归一化"""
        constellation = get_constellation_points(normalize=True)

        # 每个星座点的功率应为 1
        for point in constellation:
            assert abs(abs(point) ** 2 - 1.0) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
