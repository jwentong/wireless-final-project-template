"""
扰码模块 (Scrambler)

功能:
- 对比特流进行随机化处理（扰码）
- 恢复扰码前的比特流（解扰）

算法: LFSR (Linear Feedback Shift Register)
多项式: x^15 + x^14 + 1
"""

import numpy as np


class LFSRScrambler:
    """
    基于 LFSR 的扰码器

    参数:
        seed: LFSR 初始种子（默认 2026）
        taps: 反馈抽头位置 [15, 14]
    """

    def __init__(self, seed: int = 2026):
        """
        初始化扰码器

        参数:
            seed: 初始种子（会取模到 15 位）
        """
        self.seed = seed
        self.taps = [15, 14]  # 反馈抽头位置
        self.state = None

    def _init_state(self):
        """初始化 LFSR 状态"""
        # 将种子转换为 15 位二进制状态
        self.state = (self.seed & 0x7FFF)  # 取低 15 位
        if self.state == 0:
            self.state = 1  # 避免全零状态

    def _generate_prbs(self, length: int) -> np.ndarray:
        """
        生成伪随机比特序列 (PRBS)

        参数:
            length: 需要生成的比特数

        返回:
            prbs: 伪随机比特序列
        """
        self._init_state()
        prbs = np.zeros(length, dtype=np.int8)

        for i in range(length):
            # 输出当前最高位
            prbs[i] = (self.state >> 14) & 1

            # 计算反馈: XOR of tap positions
            feedback = 0
            for tap in self.taps:
                feedback ^= (self.state >> (tap - 1)) & 1

            # 移位并插入反馈
            self.state = ((self.state << 1) | feedback) & 0x7FFF

        return prbs

    def scramble(self, bits: np.ndarray) -> np.ndarray:
        """
        扰码：输入 XOR 伪随机序列

        参数:
            bits: 输入比特流

        返回:
            scrambled: 扰码后的比特流
        """
        if len(bits) == 0:
            return np.array([], dtype=np.int8)

        prbs = self._generate_prbs(len(bits))
        return (bits ^ prbs).astype(np.int8)

    def descramble(self, bits: np.ndarray) -> np.ndarray:
        """
        解扰：与扰码相同（XOR 逆运算）

        参数:
            bits: 扰码后的比特流

        返回:
            descrambled: 解扰后的比特流
        """
        return self.scramble(bits)


def scramble(bits: np.ndarray, seed: int = 2026) -> np.ndarray:
    """
    扰码便捷函数

    参数:
        bits: 输入比特流
        seed: 扰码种子

    返回:
        扰码后的比特流
    """
    scrambler = LFSRScrambler(seed)
    return scrambler.scramble(bits)


def descramble(bits: np.ndarray, seed: int = 2026) -> np.ndarray:
    """
    解扰便捷函数

    参数:
        bits: 扰码后的比特流
        seed: 扰码种子

    返回:
        解扰后的比特流
    """
    scrambler = LFSRScrambler(seed)
    return scrambler.descramble(bits)


if __name__ == "__main__":
    # 测试代码
    test_bits = np.array([1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0], dtype=np.int8)

    print(f"原始比特: {test_bits}")

    # 扰码
    scrambler = LFSRScrambler(seed=2026)
    scrambled = scrambler.scramble(test_bits)
    print(f"扰码后: {scrambled}")

    # 解扰
    descrambled = scrambler.descramble(scrambled)
    print(f"解扰后: {descrambled}")

    # 可逆性验证
    print(f"可逆性验证: {np.array_equal(test_bits, descrambled)}")

    # 可复现性验证
    scrambler1 = LFSRScrambler(seed=2026)
    scrambler2 = LFSRScrambler(seed=2026)
    s1 = scrambler1.scramble(test_bits)
    s2 = scrambler2.scramble(test_bits)
    print(f"可复现性验证: {np.array_equal(s1, s2)}")
