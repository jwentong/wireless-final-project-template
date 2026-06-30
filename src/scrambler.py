import numpy as np


def generate_pn_sequence(length: int, init_state: int = 0b1111111) -> np.ndarray:
    """
    生成 7 级 m 序列，生成多项式 x^7 + x^6 + 1
    :param length: 序列长度
    :param init_state: 寄存器初始状态，默认全 1
    :return: 0/1 比特序列
    """
    state = init_state & 0x7F  # 7 位寄存器掩码
    pn_bits = []
    for _ in range(length):
        output_bit = (state >> 6) & 1  # 输出最高位
        pn_bits.append(output_bit)
        # 反馈：第 7 位 XOR 第 6 位
        feedback = ((state >> 6) ^ (state >> 5)) & 1
        state = ((state << 1) | feedback) & 0x7F
    return np.array(pn_bits, dtype=np.int8)


def scramble(bits: np.ndarray) -> np.ndarray:
    """加扰：原始比特与 PN 序列逐位异或"""
    pn = generate_pn_sequence(len(bits))
    return np.bitwise_xor(bits, pn)


def descramble(bits: np.ndarray) -> np.ndarray:
    """解扰：异或自反，与加扰逻辑完全一致"""
    return scramble(bits)