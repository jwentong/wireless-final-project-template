import numpy as np

# PRD 强制统一的 Gray 编码 QPSK 映射表
_QPSK_MAPPING = {
    (0, 0): (1 + 1j) / np.sqrt(2),
    (0, 1): (-1 + 1j) / np.sqrt(2),
    (1, 1): (-1 - 1j) / np.sqrt(2),
    (1, 0): (1 - 1j) / np.sqrt(2)
}


def qpsk_modulate(bits: np.ndarray) -> np.ndarray:
    """
    QPSK 调制：比特流 → 复数符号序列
    :param bits: 0/1 比特流，长度任意，不足 2 位自动补 0
    :return: 归一化后的复数符号数组，平均功率为 1
    """
    # 补零对齐到 2 的整数倍
    pad_len = (2 - len(bits) % 2) % 2
    if pad_len > 0:
        bits = np.append(bits, np.zeros(pad_len, dtype=np.int8))
    
    symbols = []
    for i in range(0, len(bits), 2):
        b1, b2 = int(bits[i]), int(bits[i+1])
        symbols.append(_QPSK_MAPPING[(b1, b2)])
    return np.array(symbols, dtype=np.complex128)


def qpsk_demodulate(symbols: np.ndarray) -> np.ndarray:
    """
    QPSK 硬判决解调：复数符号 → 比特流
    :param symbols: 接收端复数符号序列
    :return: 解调后的 0/1 比特流
    """
    bits = []
    for s in symbols:
        real, imag = s.real, s.imag
        # 根据象限硬判决
        if real >= 0 and imag >= 0:
            bits.extend([0, 0])
        elif real < 0 and imag >= 0:
            bits.extend([0, 1])
        elif real < 0 and imag < 0:
            bits.extend([1, 1])
        else:
            bits.extend([1, 0])
    return np.array(bits, dtype=np.int8)