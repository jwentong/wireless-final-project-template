"""
源编码模块 (Source Codec)

功能:
- 将 UTF-8 文本转换为比特流
- 将比特流恢复为 UTF-8 文本
"""

import numpy as np
from typing import Union


def source_encode(text: str) -> np.ndarray:
    """
    将文本编码为比特流

    参数:
        text: UTF-8 编码的文本

    返回:
        bits: 比特流数组，dtype=np.int8，元素为 0 或 1

    算法:
        1. 使用 UTF-8 编码将文本转换为字节序列
        2. 将每个字节转换为 8 位二进制
        3. 拼接为完整的比特流
    """
    if not text:
        return np.array([], dtype=np.int8)

    # 文本编码为字节序列
    bytes_data = text.encode('utf-8')

    # 字节序列转换为比特流
    bits = np.unpackbits(np.frombuffer(bytes_data, dtype=np.uint8))

    return bits.astype(np.int8)


def source_decode(bits) -> str:
    """
    将比特流解码为文本

    参数:
        bits: 比特流（numpy 数组, list 或 str）

    返回:
        text: UTF-8 编码的文本

    算法:
        1. 确保比特数为 8 的倍数（去除多余比特）
        2. 将比特流按 8 bits 分组转换为字节序列
        3. UTF-8 解码为文本
    """
    # 支持 list[int] 输入
    if not isinstance(bits, np.ndarray):
        bits = np.array(list(bits), dtype=np.int8)

    if len(bits) == 0:
        return ""

    # 确保比特数为 8 的倍数
    if len(bits) % 8 != 0:
        bits = bits[:-(len(bits) % 8)]

    # 比特流转换为字节序列
    bytes_data = np.packbits(bits.astype(np.uint8))

    # 字节序列解码为文本
    return bytes_data.tobytes().decode('utf-8')


def count_bits(text: str) -> int:
    """
    计算文本编码后的比特数

    参数:
        text: UTF-8 编码的文本

    返回:
        比特数（字节数 × 8）
    """
    return len(text.encode('utf-8')) * 8


if __name__ == "__main__":
    # 测试代码
    test_text = "无线通信技术"

    # 编码
    bits = source_encode(test_text)
    print(f"原始文本: {test_text}")
    print(f"比特流长度: {len(bits)} bits")
    print(f"前 32 bits: {bits[:32]}")

    # 解码
    decoded_text = source_decode(bits)
    print(f"解码文本: {decoded_text}")
    print(f"可逆性验证: {test_text == decoded_text}")
