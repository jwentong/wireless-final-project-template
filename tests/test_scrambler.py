"""
单元测试 - 扰码模块
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrambler import LFSRScrambler, scramble, descramble


class TestScrambler:
    """扰码模块测试类"""

    def test_scramble_empty_bits(self):
        """测试空比特流扰码"""
        scrambler = LFSRScrambler(seed=2026)
        bits = np.array([], dtype=np.int8)
        scrambled = scrambler.scramble(bits)
        assert len(scrambled) == 0

    def test_descramble_empty_bits(self):
        """测试空比特流解扰"""
        scrambler = LFSRScrambler(seed=2026)
        bits = np.array([], dtype=np.int8)
        descrambled = scrambler.descramble(bits)
        assert len(descrambled) == 0

    def test_scramble_descramble_reversible(self):
        """测试扰码解扰可逆性"""
        test_bits = np.random.randint(0, 2, 100, dtype=np.int8)
        scrambler = LFSRScrambler(seed=2026)

        scrambled = scrambler.scramble(test_bits)
        descrambled = scrambler.descramble(scrambled)

        assert np.array_equal(test_bits, descrambled)

    def test_fixed_seed_reproducible(self):
        """测试固定种子可复现性"""
        test_bits = np.random.randint(0, 2, 100, dtype=np.int8)

        scrambler1 = LFSRScrambler(seed=2026)
        scrambler2 = LFSRScrambler(seed=2026)

        scrambled1 = scrambler1.scramble(test_bits)
        scrambled2 = scrambler2.scramble(test_bits)

        assert np.array_equal(scrambled1, scrambled2)

    def test_different_seeds_different_output(self):
        """测试不同种子产生不同输出"""
        test_bits = np.random.randint(0, 2, 100, dtype=np.int8)

        scrambler1 = LFSRScrambler(seed=2026)
        scrambler2 = LFSRScrambler(seed=1234)

        scrambled1 = scrambler1.scramble(test_bits)
        scrambled2 = scrambler2.scramble(test_bits)

        # 不同种子应该产生不同输出（极大概率）
        assert not np.array_equal(scrambled1, scrambled2)

    def test_scramble_changes_bits(self):
        """测试扰码改变比特流"""
        # 使用全 0 序列测试
        test_bits = np.zeros(100, dtype=np.int8)
        scrambler = LFSRScrambler(seed=2026)

        scrambled = scrambler.scramble(test_bits)

        # 扰码后应该不全是 0（PRBS 特性）
        assert not np.array_equal(test_bits, scrambled)

    def test_convenience_functions(self):
        """测试便捷函数"""
        test_bits = np.random.randint(0, 2, 100, dtype=np.int8)

        scrambled = scramble(test_bits, seed=2026)
        descrambled = descramble(scrambled, seed=2026)

        assert np.array_equal(test_bits, descrambled)

    def test_long_bitstream(self):
        """测试长比特流扰码解扰"""
        test_bits = np.random.randint(0, 2, 10000, dtype=np.int8)
        scrambler = LFSRScrambler(seed=2026)

        scrambled = scrambler.scramble(test_bits)
        descrambled = scrambler.descramble(scrambled)

        assert np.array_equal(test_bits, descrambled)

    def test_all_zeros(self):
        """测试全零比特流"""
        test_bits = np.zeros(100, dtype=np.int8)
        scrambler = LFSRScrambler(seed=2026)

        scrambled = scrambler.scramble(test_bits)
        descrambled = scrambler.descramble(scrambled)

        assert np.array_equal(test_bits, descrambled)

    def test_all_ones(self):
        """测试全 1 比特流"""
        test_bits = np.ones(100, dtype=np.int8)
        scrambler = LFSRScrambler(seed=2026)

        scrambled = scrambler.scramble(test_bits)
        descrambled = scrambler.descramble(scrambled)

        assert np.array_equal(test_bits, descrambled)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
