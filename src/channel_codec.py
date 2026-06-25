"""
信道编码模块 (Channel Codec)

功能:
- 卷积编码 (Convolutional Encoding)
- Viterbi 译码 (Viterbi Decoding)

参数:
- 码率: 1/2
- 约束长度: 7
- 生成多项式: [133, 171] (八进制)
"""

import numpy as np
from typing import Tuple, List


class ConvolutionalEncoder:
    """
    卷积编码器

    参数:
        constraint_length: 约束长度 K = 7
        rate: 码率 R = 1/2
        generators: 生成多项式 [133, 171] (八进制)
    """

    def __init__(self):
        self.K = 7  # 约束长度
        self.rate = 2  # 输出比特数/输入比特数
        self.generators = [0o133, 0o171]  # 生成多项式（八进制）

    def encode(self, bits: np.ndarray) -> np.ndarray:
        """
        卷积编码

        参数:
            bits: 输入比特流

        返回:
            encoded: 编码后的比特流（长度 = len(bits) * 2 + 12）
        """
        if len(bits) == 0:
            return np.array([], dtype=np.int8)

        # 初始化移位寄存器
        shift_reg = np.zeros(self.K, dtype=np.int8)

        encoded = []

        # 对每个输入比特进行编码
        for bit in bits:
            # 移位
            shift_reg = np.roll(shift_reg, 1)
            shift_reg[0] = bit

            # 计算两个输出比特
            for gen in self.generators:
                output = 0
                for i in range(self.K):
                    if (gen >> i) & 1:
                        output ^= shift_reg[i]
                encoded.append(output)

        # 尾比特处理：输入 K-1 个零，清空移位寄存器
        for _ in range(self.K - 1):
            shift_reg = np.roll(shift_reg, 1)
            shift_reg[0] = 0

            for gen in self.generators:
                output = 0
                for i in range(self.K):
                    if (gen >> i) & 1:
                        output ^= shift_reg[i]
                encoded.append(output)

        return np.array(encoded, dtype=np.int8)

    def get_rate(self) -> float:
        """返回码率"""
        return 1.0 / self.rate


class ViterbiDecoder:
    """
    Viterbi 译码器

    使用网格图进行最大似然译码
    """

    def __init__(self, constraint_length: int = 7):
        self.K = constraint_length
        self.num_states = 2 ** (constraint_length - 1)

        # 预计算状态转移表
        self._build_trellis()

    def _build_trellis(self):
        """
        构建网格图

        每个状态有两个可能的输入（0 或 1）
        转移到不同的下一个状态
        """
        self.next_state = np.zeros((self.num_states, 2), dtype=np.int32)
        self.output_bits = np.zeros((self.num_states, 2, 2), dtype=np.int8)

        for state in range(self.num_states):
            for input_bit in [0, 1]:
                # 计算下一个状态
                # 编码器: 新比特进入 shift_reg[0], 旧比特右移, 最老比特丢弃
                # 状态: shift_reg[1:K] (K-1 个历史比特), 最低位是次新比特
                # next_state = (input_bit | (state << 1)) & mask
                mask = self.num_states - 1
                next_state = (input_bit | (state << 1)) & mask
                self.next_state[state, input_bit] = next_state

                # 计算输出比特
                shift_reg = np.zeros(self.K, dtype=np.int8)
                shift_reg[0] = input_bit
                for i in range(self.K - 1):
                    shift_reg[i + 1] = (state >> i) & 1

                generators = [0o133, 0o171]
                for j, gen in enumerate(generators):
                    output = 0
                    for i in range(self.K):
                        if (gen >> i) & 1:
                            output ^= shift_reg[i]
                    self.output_bits[state, input_bit, j] = output

    def decode(self, received: np.ndarray) -> np.ndarray:
        """
        Viterbi 译码（硬判决）

        参数:
            received: 接收到的编码比特流

        返回:
            decoded: 译码后的比特流
        """
        if len(received) == 0:
            return np.array([], dtype=np.int8)

        # 计算输入比特数（考虑尾比特）
        num_codewords = len(received) // 2
        num_input_bits = num_codewords - (self.K - 1)

        if num_input_bits <= 0:
            return np.array([], dtype=np.int8)

        # 初始化路径度量
        INF = 1e9
        path_metric = np.full(self.num_states, INF)
        path_metric[0] = 0  # 从全零状态开始

        # 回溯路径存储
        traceback = np.zeros((num_codewords, self.num_states), dtype=np.int32)

        # Viterbi 算法主循环
        for i in range(num_codewords):
            # 获取当前接收的两个比特
            r0 = received[i * 2]
            r1 = received[i * 2 + 1]

            new_metric = np.full(self.num_states, INF)
            new_traceback = np.zeros(self.num_states, dtype=np.int32)

            for state in range(self.num_states):
                if path_metric[state] >= INF:
                    continue

                for input_bit in [0, 1]:
                    next_state = self.next_state[state, input_bit]
                    output0 = self.output_bits[state, input_bit, 0]
                    output1 = self.output_bits[state, input_bit, 1]

                    # 计算分支度量（汉明距离）
                    branch_metric = (output0 != r0) + (output1 != r1)
                    total_metric = path_metric[state] + branch_metric

                    if total_metric < new_metric[next_state]:
                        new_metric[next_state] = total_metric
                        new_traceback[next_state] = state

            path_metric = new_metric
            traceback[i] = new_traceback

        # 回溯
        # 从最小度量状态开始回溯
        current_state = np.argmin(path_metric)

        decoded = []
        for i in range(num_codewords - 1, -1, -1):
            # 找到当前状态是从哪个状态转移来的
            prev_state = traceback[i, current_state]

            # 确定输入比特
            if i < num_input_bits:
                # 从 prev_state 到 current_state，输入比特是...
                for input_bit in [0, 1]:
                    if self.next_state[prev_state, input_bit] == current_state:
                        decoded.append(input_bit)
                        break

            current_state = prev_state

        # 反转（因为我们是反向回溯的）
        decoded = decoded[::-1]

        return np.array(decoded, dtype=np.int8)


class ChannelCodec:
    """
    信道编码器/译码器封装类
    """

    def __init__(self):
        self.encoder = ConvolutionalEncoder()
        self.decoder = ViterbiDecoder()

    def encode(self, bits: np.ndarray) -> np.ndarray:
        """信道编码"""
        return self.encoder.encode(bits)

    def decode(self, bits: np.ndarray) -> np.ndarray:
        """信道译码"""
        return self.decoder.decode(bits)


# 顶层函数，供公开测试使用
def channel_encode(bits) -> np.ndarray:
    """信道编码顶层函数（接受 list 或 ndarray）"""
    if not isinstance(bits, np.ndarray):
        bits = np.array(list(bits), dtype=np.int8)
    encoder = ConvolutionalEncoder()
    return encoder.encode(bits)


def channel_decode(bits) -> np.ndarray:
    """信道译码顶层函数（接受 list 或 ndarray）"""
    if not isinstance(bits, np.ndarray):
        bits = np.array(list(bits), dtype=np.int8)
    decoder = ViterbiDecoder()
    return decoder.decode(bits)


if __name__ == "__main__":
    # 测试代码
    test_bits = np.array([1, 0, 1, 1, 0, 0, 1, 0], dtype=np.int8)

    print(f"原始比特: {test_bits}")
    print(f"原始比特数: {len(test_bits)}")

    # 编码
    encoder = ConvolutionalEncoder()
    encoded = encoder.encode(test_bits)
    print(f"编码后: {encoded}")
    print(f"编码后比特数: {len(encoded)}")
    print(f"码率: {len(test_bits) / len(encoded):.3f}")

    # 译码（无噪声）
    decoder = ViterbiDecoder()
    decoded = decoder.decode(encoded)
    print(f"译码后: {decoded}")
    print(f"可逆性验证（无噪声）: {np.array_equal(test_bits, decoded)}")
