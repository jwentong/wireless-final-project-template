"""
QPSK 调制解调模块

功能:
- QPSK 调制：比特流 → 复数符号
- QPSK 解调：复数符号 → 比特流

映射规则: Gray 编码
"""

import numpy as np
from typing import Tuple


# 标准 Gray 编码 QPSK 星座映射表
# b0 = Q-bit (imaginary), b1 = I-bit (real)
# PRD 期望: 00→QI, 01→QII, 11→QIII, 10→QIV
QPSK_MAPPING = {
    (0, 0): (1, 1),    # QI:  b1=0(I=+1), b0=0(Q=+1)
    (0, 1): (-1, 1),   # QII: b1=1(I=-1), b0=0(Q=+1)
    (1, 1): (-1, -1),  # QIII:b1=1(I=-1), b0=1(Q=-1)
    (1, 0): (1, -1),   # QIV: b1=0(I=+1), b0=1(Q=-1)
}

# 反向映射：判决区域 -> 比特对
QPSK_DEMAPPING = {
    (1, 1): (0, 0),    # QI
    (-1, 1): (0, 1),   # QII
    (-1, -1): (1, 1),  # QIII
    (1, -1): (1, 0),   # QIV
}


def qpsk_modulate(bits, normalize: bool = True):
    """
    QPSK 调制（标准 Gray 编码）

    参数:
        bits: 输入比特流（numpy 数组或 list）
        normalize: 是否归一化符号功率为 1

    返回:
        symbols: 复数符号序列（numpy 数组）

    映射规则 (PRD 标准 Gray 编码):
        00 -> +1+j  (第一象限, QI)
        01 -> -1+j  (第二象限, QII)
        11 -> -1-j  (第三象限, QIII)
        10 -> +1-j  (第四象限, QIV)
    """
    bits = np.asarray(bits, dtype=np.int8)
    if len(bits) == 0:
        return np.array([], dtype=np.complex128)

    # 检查是否需要 padding（奇数长度时末尾补0）
    if len(bits) % 2 != 0:
        bits = np.append(bits, 0)

    # 调制
    symbols = []
    for i in range(0, len(bits), 2):
        b0, b1 = int(bits[i]), int(bits[i + 1])
        real, imag = QPSK_MAPPING[(b0, b1)]
        symbols.append(complex(real, imag))

    symbols = np.array(symbols, dtype=np.complex128)

    # 归一化：使平均符号功率为 1
    if normalize:
        symbols = symbols / np.sqrt(2)

    return symbols


def qpsk_modulate_with_padding(bits, normalize: bool = True):
    """
    QPSK 调制（带 padding 标志返回）

    返回:
        symbols: 复数符号序列
        padded: 是否进行了 padding
    """
    bits_np = np.asarray(bits, dtype=np.int8)
    padded = (len(bits_np) % 2 != 0)
    return qpsk_modulate(bits_np, normalize), padded


def qpsk_demodulate(symbols) -> np.ndarray:
    """
    QPSK 解调

    参数:
        symbols: 接收符号序列（numpy 数组、tuple 或复数列表）

    返回:
        bits: 解调后的比特流

    判决规则 (标准 Gray 编码):
        - b0 (Q-bit): 0 if imag > 0 else 1
        - b1 (I-bit): 0 if real > 0 else 1
    """
    # 处理 tuple 输入 (symbols_array, padded)
    if isinstance(symbols, tuple):
        symbols = symbols[0]

    symbols = np.asarray(symbols, dtype=np.complex128)
    if len(symbols) == 0:
        return np.array([], dtype=np.int8)

    bits = []
    for s in symbols:
        # 判决: b0=Q-bit(imag), b1=I-bit(real)
        b0 = 0 if s.imag > 0 else 1
        b1 = 0 if s.real > 0 else 1
        bits.extend([b0, b1])

    return np.array(bits, dtype=np.int8)


def qpsk_demodulate_soft(symbols: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    QPSK 软判决解调

    参数:
        symbols: 接收符号序列

    返回:
        bits: 硬判决比特流
        llr: 对数似然比（Log-Likelihood Ratio）
    """
    if len(symbols) == 0:
        return np.array([], dtype=np.int8), np.array([], dtype=np.float64)

    bits = []
    llrs = []

    for s in symbols:
        # 硬判决
        b0 = 0 if s.real > 0 else 1
        b1 = 0 if s.imag > 0 else 1
        bits.extend([b0, b1])

        # 软判决（LLR 简化计算）
        # LLR ≈ 2 * Re(s) / σ² (假设 σ² = 1)
        llr0 = 2 * s.real
        llr1 = 2 * s.imag
        llrs.extend([llr0, llr1])

    return np.array(bits, dtype=np.int8), np.array(llrs, dtype=np.float64)


def get_constellation_points(normalize: bool = True) -> np.ndarray:
    """
    获取 QPSK 星座点

    参数:
        normalize: 是否归一化

    返回:
        constellation: 4 个星座点
    """
    constellation = np.array([
        complex(1, 1),   # 00
        complex(-1, 1),  # 01
        complex(-1, -1), # 11
        complex(1, -1),  # 10
    ], dtype=np.complex128)

    if normalize:
        constellation = constellation / np.sqrt(2)

    return constellation


def calculate_symbol_error_probability(snr_db: float) -> float:
    """
    计算 QPSK 理论符号错误概率

    参数:
        snr_db: 信噪比（dB）

    返回:
        ser: 符号错误概率

    公式:
        P_s = 2 * Q(√(SNR)) - Q²(√(SNR))
        其中 Q(x) = 0.5 * erfc(x / √2)
    """
    from scipy import special

    snr_linear = 10 ** (snr_db / 10)

    # Q 函数
    q_func = lambda x: 0.5 * special.erfc(x / np.sqrt(2))

    ser = 2 * q_func(np.sqrt(snr_linear)) - q_func(np.sqrt(snr_linear)) ** 2

    return ser


def calculate_bit_error_probability(snr_db: float) -> float:
    """
    计算 QPSK 理论比特错误概率（Gray 编码）

    参数:
        snr_db: 信噪比（dB）

    返回:
        ber: 比特错误概率

    公式:
        P_b = Q(√(2 * SNR))
    """
    from scipy import special

    snr_linear = 10 ** (snr_db / 10)

    # Q 函数
    q_func = lambda x: 0.5 * special.erfc(x / np.sqrt(2))

    ber = q_func(np.sqrt(2 * snr_linear))

    return ber


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # 测试代码
    print("QPSK 调制解调测试")
    print("=" * 50)

    # 测试比特流
    test_bits = np.array([0, 0, 0, 1, 1, 1, 1, 0], dtype=np.int8)
    print(f"输入比特: {test_bits}")

    # 调制
    symbols, padded = qpsk_modulate(test_bits)
    print(f"调制后符号数: {len(symbols)}")
    print(f"是否 padding: {padded}")
    print(f"符号: {symbols}")

    # 解调
    decoded_bits = qpsk_demodulate(symbols)
    print(f"解调后比特: {decoded_bits}")
    print(f"可逆性验证: {np.array_equal(test_bits, decoded_bits[:len(test_bits)])}")

    # 星座点
    constellation = get_constellation_points()
    print(f"\nQPSK 星座点:")
    for i, point in enumerate(constellation):
        print(f"  {list(QPSK_MAPPING.keys())[i]} -> {point}")

    # 理论 BER
    print(f"\n理论 BER:")
    for snr_db in [0, 5, 10, 12, 15, 20]:
        ber = calculate_bit_error_probability(snr_db)
        print(f"  SNR {snr_db} dB: BER = {ber:.2e}")

    # 绘制星座图
    plt.figure(figsize=(8, 8))
    plt.scatter(constellation.real, constellation.imag, s=100, c='blue', marker='o')
    for i, (bits, point) in enumerate(zip([(0,0), (0,1), (1,1), (1,0)], constellation)):
        plt.annotate(f'{bits[0]}{bits[1]}', (point.real, point.imag), fontsize=12, ha='center', va='bottom')

    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    plt.axvline(x=0, color='k', linestyle='--', alpha=0.3)
    plt.grid(True, alpha=0.3)
    plt.xlabel('In-phase (I)')
    plt.ylabel('Quadrature (Q)')
    plt.title('QPSK Constellation (Gray Coding)')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('qpsk_constellation_test.png', dpi=150)
    print(f"\n星座图已保存: qpsk_constellation_test.png")
