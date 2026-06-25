"""
帧封装模块 (Frame)

功能:
- 帧封装：将 payload 封装为完整帧
- 帧解析：从帧中提取 payload

帧结构:
+----------+--------+----------+--------+
| Preamble | Length | Payload  | CRC16  |
| 64 bits  | 16 bits| N bits   | 16 bits|
+----------+--------+----------+--------+
"""

import numpy as np
from typing import Tuple


# Preamble 模式：[1, 0, 1, 0, ...] 交替序列
PREAMBLE_LENGTH = 64
LENGTH_FIELD_BITS = 16
CRC_LENGTH = 16


def generate_preamble() -> np.ndarray:
    """
    生成 preamble 同步序列

    使用 64-bit 伪随机序列，具有良好的自相关特性，
    确保在 QPSK 调制后有足够多的不同星座点。

    返回:
        preamble: 64 bits 伪随机序列
    """
    # 使用固定种的 LFSR 生成 PRBS，确保与扰码器使用不同种子
    # LFSR: x^7 + x^6 + 1 (不同于扰码器的 x^15+x^14+1)
    # 初始种子: 0x5A (确保与扰码器不同)
    state = 0x5A
    preamble = np.zeros(PREAMBLE_LENGTH, dtype=np.int8)
    for i in range(PREAMBLE_LENGTH):
        # 输出最高位
        preamble[i] = (state >> 6) & 1
        # 反馈: bit6 XOR bit5
        feedback = ((state >> 6) ^ (state >> 5)) & 1
        state = ((state << 1) | feedback) & 0x7F
    return preamble


def encode_length(length: int) -> np.ndarray:
    """
    将长度值编码为 16 bits（大端序）

    参数:
        length: payload 比特数（0-65535）

    返回:
        length_bits: 16 bits 长度字段
    """
    if length < 0 or length > 65535:
        raise ValueError(f"Length must be in range [0, 65535], got {length}")

    # 转换为 16 位二进制（大端序）
    length_bits = np.zeros(LENGTH_FIELD_BITS, dtype=np.int8)
    for i in range(LENGTH_FIELD_BITS):
        length_bits[i] = int((length >> (LENGTH_FIELD_BITS - 1 - i)) & 1)

    return length_bits


def decode_length(length_bits: np.ndarray) -> int:
    """
    将 16 bits 长度字段解码为长度值

    参数:
        length_bits: 16 bits 长度字段

    返回:
        length: payload 比特数
    """
    length = 0
    for i in range(LENGTH_FIELD_BITS):
        length = (length << 1) | int(length_bits[i])

    return length


def compute_crc16(bits: np.ndarray) -> np.ndarray:
    """
    计算 CRC-16-CCITT 校验码

    参数:
        bits: 输入比特流

    返回:
        crc_bits: 16 bits CRC 校验码

    算法:
        多项式: 0x1021
        初始值: 0xFFFF
        输入反转: False
        输出反转: False
    """
    # CRC-16-CCITT 参数
    POLY = 0x1021
    INIT = 0xFFFF

    # 将比特流按 8 bits 分组转换为字节
    if len(bits) % 8 != 0:
        # 填充到 8 的倍数
        padding = 8 - (len(bits) % 8)
        bits = np.concatenate([bits, np.zeros(padding, dtype=np.int8)])

    bytes_data = np.packbits(bits.astype(np.uint8))

    # 计算 CRC
    crc = INIT
    for byte in bytes_data:
        crc ^= (int(byte) << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ POLY) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF

    # 转换为 16 bits
    crc_bits = np.zeros(CRC_LENGTH, dtype=np.int8)
    for i in range(CRC_LENGTH):
        crc_bits[i] = (crc >> (CRC_LENGTH - 1 - i)) & 1

    return crc_bits


def verify_crc16(bits: np.ndarray, received_crc: np.ndarray) -> bool:
    """
    验证 CRC 校验

    参数:
        bits: payload 比特流
        received_crc: 接收到的 CRC

    返回:
        valid: CRC 校验是否通过
    """
    computed_crc = compute_crc16(bits)
    return np.array_equal(computed_crc, received_crc)


def build_frame(payload) -> np.ndarray:
    """
    帧封装

    参数:
        payload: 有效载荷比特流（list 或 ndarray）

    返回:
        frame: 完整帧比特流

    帧结构:
        Preamble (64 bits) + Length (16 bits) + Payload (N bits)
    """
    payload = np.asarray(payload, dtype=np.int8)
    if len(payload) == 0:
        raise ValueError("Payload cannot be empty")

    # 生成 preamble
    preamble = generate_preamble()

    # 编码长度字段
    length_bits = encode_length(len(payload))

    # 拼接帧
    frame = np.concatenate([preamble, length_bits, payload])

    return frame


def parse_frame(frame_bits) -> Tuple[np.ndarray, int]:
    """
    帧解析

    参数:
        frame_bits: 完整帧比特流（可能包含 preamble，list 或 ndarray）

    返回:
        payload: 有效载荷比特流
        length: payload 长度
    """
    frame_bits = np.asarray(frame_bits, dtype=np.int8)

    # 自动检测并跳过 preamble（如果帧以 preamble 开头）
    if len(frame_bits) >= PREAMBLE_LENGTH:
        preamble = generate_preamble()
        # 比较前 PREAMBLE_LENGTH 位，如果匹配度高则跳过
        match_count = np.sum(frame_bits[:PREAMBLE_LENGTH] == preamble)
        if match_count >= PREAMBLE_LENGTH - 4:  # 允许少量错误
            frame_bits = frame_bits[PREAMBLE_LENGTH:]

    if len(frame_bits) < LENGTH_FIELD_BITS:
        raise ValueError(f"Frame too short: {len(frame_bits)} bits")

    # 提取长度字段
    length_bits = frame_bits[:LENGTH_FIELD_BITS]
    length = decode_length(length_bits)

    # 检查帧长度是否合理
    expected_frame_length = LENGTH_FIELD_BITS + length
    if len(frame_bits) < expected_frame_length:
        raise ValueError(f"Frame length mismatch: expected {expected_frame_length}, got {len(frame_bits)}")

    # 提取 payload
    payload = frame_bits[LENGTH_FIELD_BITS:LENGTH_FIELD_BITS + length]

    return payload, length


def get_frame_overhead() -> int:
    """
    获取帧开销比特数

    返回:
        overhead: Preamble + Length + CRC = 64 + 16 + 16 = 96 bits
    """
    return PREAMBLE_LENGTH + LENGTH_FIELD_BITS + CRC_LENGTH


if __name__ == "__main__":
    # 测试代码
    test_payload = np.array([1, 0, 1, 1, 0, 0, 1, 0] * 100, dtype=np.int8)

    print(f"原始 payload 长度: {len(test_payload)} bits")

    # 帧封装
    frame = build_frame(test_payload)
    print(f"帧长度: {len(frame)} bits")
    print(f"帧开销: {get_frame_overhead()} bits")

    # 验证帧结构
    print(f"\n帧结构验证:")
    print(f"  Preamble: {frame[:64]}")
    print(f"  Length: {frame[64:80]} (解码: {decode_length(frame[64:80])})")

    # 帧解析（跳过 preamble）
    payload, crc_valid, length = parse_frame(frame[64:])
    print(f"\n解析结果:")
    print(f"  Payload 长度: {len(payload)} bits")
    print(f"  CRC 校验: {'通过' if crc_valid else '失败'}")
    print(f"  可逆性验证: {np.array_equal(test_payload, payload)}")

    # CRC 错误检测测试
    print(f"\nCRC 错误检测测试:")
    corrupted_frame = frame.copy()
    corrupted_frame[100] ^= 1  # 翻转一个比特
    try:
        payload_corrupted, crc_valid_corrupted, _ = parse_frame(corrupted_frame[64:])
        print(f"  翻转 bit 100 后 CRC 校验: {'通过' if crc_valid_corrupted else '失败'}")
    except Exception as e:
        print(f"  解析错误: {e}")
