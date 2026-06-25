"""
性能指标计算模块 (Metrics)

功能:
- 计算误码率 BER
- 计算误帧率 FER
- 计算文本匹配率
- 生成 metrics.json
"""

import numpy as np
import json
from typing import Dict, Any, Optional
from pathlib import Path


def calculate_ber(original_bits: np.ndarray, received_bits: np.ndarray) -> float:
    """
    计算误码率 (Bit Error Rate)

    参数:
        original_bits: 原始比特流
        received_bits: 接收比特流

    返回:
        ber: 误码率
    """
    if len(original_bits) == 0:
        return 0.0

    # 确保长度一致
    min_len = min(len(original_bits), len(received_bits))

    if min_len == 0:
        return 1.0

    # 计算错误比特数
    errors = np.sum(original_bits[:min_len] != received_bits[:min_len])

    ber = errors / min_len

    return ber


def calculate_fer(original_frames: int, decoded_frames: int, correct_frames: int) -> float:
    """
    计算误帧率 (Frame Error Rate)

    参数:
        original_frames: 原始帧数
        decoded_frames: 成功解码帧数
        correct_frames: 正确帧数

    返回:
        fer: 误帧率
    """
    if original_frames == 0:
        return 0.0

    fer = (original_frames - correct_frames) / original_frames

    return fer


def calculate_text_match_rate(original_text: str, received_text: str) -> float:
    """
    计算文本匹配率

    参数:
        original_text: 原始文本
        received_text: 接收文本

    返回:
        match_rate: 匹配率 (0.0 - 1.0)
    """
    if not original_text:
        return 1.0 if not received_text else 0.0

    # 计算匹配的字符数
    matches = 0
    min_len = min(len(original_text), len(received_text))

    for i in range(min_len):
        if original_text[i] == received_text[i]:
            matches += 1

    match_rate = matches / len(original_text)

    return match_rate


def calculate_ser(original_symbols: np.ndarray, received_symbols: np.ndarray) -> float:
    """
    计算符号错误率 (Symbol Error Rate)

    参数:
        original_symbols: 原始符号序列
        received_symbols: 接收符号序列

    返回:
        ser: 符号错误率
    """
    if len(original_symbols) == 0:
        return 0.0

    min_len = min(len(original_symbols), len(received_symbols))

    if min_len == 0:
        return 1.0

    # 判决接收符号
    decoded_symbols = []
    for s in received_symbols[:min_len]:
        real = 1 if s.real > 0 else -1
        imag = 1 if s.imag > 0 else -1
        decoded_symbols.append(complex(real, imag))

    decoded_symbols = np.array(decoded_symbols)

    # 归一化原始符号用于比较
    original_normalized = original_symbols[:min_len] * np.sqrt(2)

    errors = np.sum(original_normalized != decoded_symbols)
    ser = errors / min_len

    return ser


def calculate_evm(received_symbols: np.ndarray,
                  reference_symbols: np.ndarray) -> float:
    """
    计算误差向量幅度 (Error Vector Magnitude)

    参数:
        received_symbols: 接收符号序列
        reference_symbols: 参考符号序列（理想符号）

    返回:
        evm: EVM（百分比）
    """
    if len(received_symbols) == 0 or len(reference_symbols) == 0:
        return 0.0

    min_len = min(len(received_symbols), len(reference_symbols))

    # 计算误差向量
    errors = received_symbols[:min_len] - reference_symbols[:min_len]

    # 计算误差功率
    error_power = np.mean(np.abs(errors) ** 2)

    # 计算参考功率
    reference_power = np.mean(np.abs(reference_symbols[:min_len]) ** 2)

    if reference_power == 0:
        return 0.0

    # EVM
    evm = np.sqrt(error_power / reference_power) * 100

    return evm


def generate_metrics_dict(snr_db: float,
                         seed: int,
                         modulation: str,
                         channel: str,
                         payload_bits: int,
                         ber: float,
                         fer: float,
                         text_match_rate: float,
                         checksum_pass: bool,
                         sync_start_index: int,
                         additional_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    生成 metrics 字典

    参数:
        snr_db: 信噪比
        seed: 随机种子
        modulation: 调制方式
        channel: 信道类型
        payload_bits: payload 比特数
        ber: 误码率
        fer: 误帧率
        text_match_rate: 文本匹配率
        checksum_pass: 校验是否通过
        sync_start_index: 同步起始索引
        additional_metrics: 额外指标

    返回:
        metrics: 完整的 metrics 字典
    """
    metrics = {
        "snr_db": snr_db,
        "seed": seed,
        "modulation": modulation,
        "channel": channel,
        "payload_bits": payload_bits,
        "ber": ber,
        "fer": fer,
        "text_match_rate": text_match_rate,
        "checksum_pass": checksum_pass,
        "sync_start_index": sync_start_index
    }

    if additional_metrics:
        metrics.update(additional_metrics)

    return metrics


def save_metrics(metrics: Dict[str, Any], filepath: str) -> None:
    """
    保存 metrics 到 JSON 文件

    参数:
        metrics: metrics 字典
        filepath: 输出文件路径
    """
    # 确保目录存在
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    # 转换 numpy 类型为 Python 原生类型
    def convert_to_native(obj):
        if isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        else:
            return obj

    metrics_native = convert_to_native(metrics)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(metrics_native, f, indent=2, ensure_ascii=False)


def load_metrics(filepath: str) -> Dict[str, Any]:
    """
    从 JSON 文件加载 metrics

    参数:
        filepath: 文件路径

    返回:
        metrics: metrics 字典
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    print("性能指标计算测试")
    print("=" * 50)

    # 测试 BER
    original_bits = np.array([1, 0, 1, 1, 0, 0, 1, 0], dtype=np.int8)
    received_bits = np.array([1, 0, 1, 0, 0, 0, 1, 0], dtype=np.int8)  # 1 个错误
    ber = calculate_ber(original_bits, received_bits)
    print(f"BER: {ber:.4f} ({int(ber * len(original_bits))} errors)")

    # 测试文本匹配率
    original_text = "无线通信技术"
    received_text = "无线通信技木"  # 1 个错误
    match_rate = calculate_text_match_rate(original_text, received_text)
    print(f"Text match rate: {match_rate:.4f}")

    # 测试 metrics 生成
    metrics = generate_metrics_dict(
        snr_db=12,
        seed=2026,
        modulation="qpsk",
        channel="awgn",
        payload_bits=2400,
        ber=0.0,
        fer=0.0,
        text_match_rate=1.0,
        checksum_pass=True,
        sync_start_index=25
    )

    print(f"\nMetrics:")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))

    # 测试保存和加载
    test_path = "results/test_metrics.json"
    save_metrics(metrics, test_path)
    loaded = load_metrics(test_path)
    print(f"\n保存并加载 metrics:")
    print(json.dumps(loaded, indent=2, ensure_ascii=False))
