import numpy as np


def text_to_bitstream(text: str) -> np.ndarray:
    """
    UTF-8 文本转换为 0/1 比特流，字节内高位在前
    :param text: 输入字符串
    :return: 一维 int8 类型 numpy 数组，元素为 0 或 1
    """
    bytes_data = text.encode("utf-8")
    bits = []
    for byte in bytes_data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return np.array(bits, dtype=np.int8)


def bitstream_to_text(bits: np.ndarray) -> str:
    """
    0/1 比特流还原为 UTF-8 文本
    :param bits: 一维 int8 比特流数组
    :return: 还原后的字符串
    """
    byte_count = len(bits) // 8
    bytes_list = []
    for i in range(byte_count):
        byte_bits = bits[i * 8 : (i + 1) * 8]
        byte_val = 0
        for bit in byte_bits:
            byte_val = (byte_val << 1) | int(bit)
        bytes_list.append(byte_val)
    return bytes(bytes_list).decode("utf-8", errors="replace")


# 兼容公开测试接口
text_to_bits = text_to_bitstream
bits_to_text = bitstream_to_text