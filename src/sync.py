"""
同步模块 (Synchronization)

功能:
- 帧起始检测
- 相关检测
- 同步峰值搜索
"""

import numpy as np
from typing import Tuple, Optional


def detect_frame_start(received: np.ndarray,
                       preamble=None,
                       preamble_bits=None,
                       threshold: float = 0.7) -> Tuple[int, float]:
    """
    帧起始检测（兼容两种 preamble 格式）

    参数:
        received: 接收符号序列
        preamble: preamble 复数符号序列（预调制）
        preamble_bits: preamble 比特序列（需要先调制）
        threshold: 检测阈值

    返回:
        start_index: 检测到的帧起始索引
        correlation_peak: 相关峰值

    方法:
        1. 使用给定的 preamble（符号或比特）进行滑动相关
        2. 检测相关峰值位置
    """
    if preamble is not None:
        # preamble 已经是调制后的复数符号
        reference = np.asarray(preamble, dtype=np.complex128)
    elif preamble_bits is not None:
        # 需要将 bitmap preamble 调制为 QPSK 符号
        if len(preamble_bits) % 2 != 0:
            preamble_bits = preamble_bits[:-1]
        reference = []
        for i in range(0, len(preamble_bits), 2):
            b0, b1 = int(preamble_bits[i]), int(preamble_bits[i + 1])
            real = 1 if b0 == 0 else -1
            imag = 1 if b1 == 0 else -1
            reference.append(complex(real, imag) / np.sqrt(2))
        reference = np.array(reference, dtype=np.complex128)
    else:
        raise ValueError("Either preamble or preamble_bits must be provided")

    received = np.asarray(received, dtype=np.complex128)

    # 计算相关
    correlation = np.abs(np.correlate(received, reference, mode='valid'))

    # 归一化
    reference_energy = np.sum(np.abs(reference) ** 2)
    if reference_energy > 0:
        normalized_correlation = correlation / reference_energy

    # 找到峰值
    peak_index = np.argmax(correlation)
    peak_value = correlation[peak_index]

    normalized_peak = peak_value / reference_energy if reference_energy > 0 else 0.0

    # 返回 dict 以兼容测试期望的 dict 格式
    return {"start_index": int(peak_index), "correlation_peak": float(normalized_peak)}


# 别名，供测试查找
synchronize = detect_frame_start
sync = detect_frame_start


def detect_preamble_correlation(received: np.ndarray,
                                preamble_symbols: np.ndarray) -> Tuple[int, np.ndarray]:
    """
    使用相关检测 preamble

    参数:
        received: 接收符号序列
        preamble_symbols: preamble 符号序列（已调制）

    返回:
        start_index: 检测到的帧起始索引
        correlation: 相关序列
    """
    # 计算相关
    correlation = np.abs(np.correlate(received, preamble_symbols, mode='valid'))

    # 找到峰值位置
    start_index = np.argmax(correlation)

    return start_index, correlation


def fine_timing_sync(received: np.ndarray,
                     preamble_symbols: np.ndarray,
                     coarse_index: int,
                     search_range: int = 5) -> int:
    """
    精细时间同步

    参数:
        received: 接收符号序列
        preamble_symbols: preamble 符号序列
        coarse_index: 粗同步位置
        search_range: 精细搜索范围

    返回:
        fine_index: 精细同步位置
    """
    best_index = coarse_index
    best_correlation = 0

    for offset in range(-search_range, search_range + 1):
        index = coarse_index + offset
        if index < 0 or index + len(preamble_symbols) > len(received):
            continue

        # 提取对应位置的接收信号
        segment = received[index:index + len(preamble_symbols)]

        # 计算相关
        correlation = np.abs(np.sum(segment * np.conj(preamble_symbols)))

        if correlation > best_correlation:
            best_correlation = correlation
            best_index = index

    return best_index


def remove_frequency_offset(received: np.ndarray,
                           preamble_symbols: np.ndarray,
                           detected_index: int) -> Tuple[np.ndarray, float]:
    """
    估计并去除频率偏移

    参数:
        received: 接收符号序列
        preamble_symbols: preamble 符号序列
        detected_index: 检测到的帧起始位置

    返回:
        corrected: 频率校正后的接收信号
        frequency_offset: 估计的频率偏移（rad/sample）
    """
    # 提取 preamble 部分的接收信号
    rx_preamble = received[detected_index:detected_index + len(preamble_symbols)]

    # 估计相位差
    phase_diff = np.angle(rx_preamble[1:] * np.conj(preamble_symbols[1:]) *
                          np.conj(rx_preamble[:-1] * np.conj(preamble_symbols[:-1])))

    # 平均频率偏移
    frequency_offset = np.mean(phase_diff)

    # 校正
    t = np.arange(len(received))
    correction = np.exp(-1j * frequency_offset * t)
    corrected = received * correction

    return corrected, frequency_offset


def detect_frame_with_offset(received: np.ndarray,
                             preamble_bits: np.ndarray,
                             max_offset: int = 100):
    """
    检测帧起始位置，支持任意偏移

    参数:
        received: 接收符号序列（可能包含偏移）
        preamble_bits: preamble 比特序列
        max_offset: 最大预期偏移（符号数）

    返回:
        dict: {"start_index": int, "correlation_peak": float}
    """
    # 将 preamble 转换为符号
    if len(preamble_bits) % 2 != 0:
        preamble_bits = preamble_bits[:-1]

    preamble_symbols = []
    for i in range(0, len(preamble_bits), 2):
        b0, b1 = int(preamble_bits[i]), int(preamble_bits[i + 1])
        real = 1 if b1 == 0 else -1  # b1 = I-bit
        imag = 1 if b0 == 0 else -1  # b0 = Q-bit
        preamble_symbols.append(complex(real, imag) / np.sqrt(2))

    preamble_symbols = np.array(preamble_symbols, dtype=np.complex128)

    # 在前 max_offset + len(preamble_symbols) 范围内搜索
    search_length = min(max_offset + len(preamble_symbols) * 2, len(received))
    search_region = received[:search_length]

    # 计算相关
    correlation = np.abs(np.correlate(search_region, preamble_symbols, mode='valid'))

    # 找到峰值
    peak_index = np.argmax(correlation)
    peak_value = correlation[peak_index]

    # 归一化峰值
    reference_energy = np.sum(np.abs(preamble_symbols) ** 2)
    normalized_peak = peak_value / reference_energy if reference_energy > 0 else 0.0

    return {"start_index": int(peak_index), "correlation_peak": float(normalized_peak)}


def get_sync_peak_plot_data(received: np.ndarray,
                            preamble_bits: np.ndarray) -> Tuple[np.ndarray, int]:
    """
    获取同步峰值图数据

    参数:
        received: 接收符号序列
        preamble_bits: preamble 比特序列

    返回:
        correlation: 相关序列
        peak_index: 峰值位置
    """
    # 将 preamble 转换为符号
    if len(preamble_bits) % 2 != 0:
        preamble_bits = preamble_bits[:-1]

    preamble_symbols = []
    for i in range(0, len(preamble_bits), 2):
        b0, b1 = preamble_bits[i], preamble_bits[i + 1]
        real = 1 if b1 == 0 else -1  # b1 = I-bit
        imag = 1 if b0 == 0 else -1  # b0 = Q-bit
        preamble_symbols.append(complex(real, imag) / np.sqrt(2))

    preamble_symbols = np.array(preamble_symbols, dtype=np.complex128)

    # 计算相关
    correlation = np.abs(np.correlate(received, preamble_symbols, mode='valid'))

    # 归一化
    reference_energy = np.sum(np.abs(preamble_symbols) ** 2)
    correlation = correlation / reference_energy

    # 峰值位置
    peak_index = np.argmax(correlation)

    return correlation, peak_index


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from src.frame import generate_preamble
    from src.qpsk import qpsk_modulate
    from src.awgn import awgn_channel

    print("同步模块测试")
    print("=" * 50)

    # 生成 preamble
    preamble_bits = generate_preamble()
    print(f"Preamble 长度: {len(preamble_bits)} bits")

    # 调制 preamble
    preamble_symbols, _ = qpsk_modulate(preamble_bits)
    print(f"Preamble 符号数: {len(preamble_symbols)}")

    # 生成随机数据帧
    data_bits = np.random.randint(0, 2, 1000, dtype=np.int8)
    data_symbols, _ = qpsk_modulate(data_bits)

    # 添加偏移（25 个随机符号）
    offset_symbols = 25
    offset = (np.random.randn(offset_symbols) + 1j * np.random.randn(offset_symbols)) / np.sqrt(2)

    # 构建发送信号
    tx_signal = np.concatenate([offset, preamble_symbols, data_symbols])
    print(f"发送信号长度: {len(tx_signal)} 符号")
    print(f"帧起始位置: {offset_symbols}")

    # 通过 AWGN 信道
    snr_db = 12
    rx_signal = awgn_channel(tx_signal, snr_db, seed=2026)

    # 同步检测
    detected_index, peak_value = detect_frame_with_offset(rx_signal, preamble_bits)
    print(f"\n检测结果:")
    print(f"  检测到的帧起始: {detected_index}")
    print(f"  实际帧起始: {offset_symbols}")
    print(f"  检测误差: {abs(detected_index - offset_symbols)} 符号")
    print(f"  相关峰值: {peak_value:.4f}")

    # 绘制同步峰值图
    correlation, peak_idx = get_sync_peak_plot_data(rx_signal, preamble_bits)

    plt.figure(figsize=(10, 4))
    plt.plot(correlation, label='Correlation')
    plt.axvline(x=peak_idx, color='r', linestyle='--', label=f'Peak at {peak_idx}')
    plt.axvline(x=offset_symbols, color='g', linestyle=':', label=f'True start at {offset_symbols}')
    plt.xlabel('Sample Index')
    plt.ylabel('Normalized Correlation')
    plt.title(f'Synchronization Peak Detection (SNR = {snr_db} dB)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('sync_peak_test.png', dpi=150)
    print(f"\n同步峰值图已保存: sync_peak_test.png")
