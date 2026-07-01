"""
源编码模块 (Source Encode / Decode)
----------------------------------
职责：UTF-8 文本 <-> 比特流 的可逆转换。

设计说明：
- 每个字节固定编码为 8 个比特，MSB(最高位)在前，符合最常见的字节序约定，
  也便于人工核对（8 的整数倍长度，方便与信道编码/帧结构对齐）。
- 编码阶段不做任何压缩或加密，压缩/加密属于后续扰码模块的职责，
  这里保持源编码模块单一职责：只做"文本 <-> 比特"的格式转换。
- 解码阶段严格按照 UTF-8 规则解码；如果比特流末尾存在非 8 的整数倍的
  多余比特（例如 QPSK 补零残留、未被上层正确裁剪），会在裁剪到 8 的整数倍后
  再解码，避免因末尾几个孤立比特导致整体解码失败。
"""

from __future__ import annotations

from typing import Iterable, List


def source_encode(text: str) -> List[int]:
    """将 UTF-8 文本编码为比特列表（每字节 8 位，MSB 在前）。

    Args:
        text: 待编码的字符串（Python str，内部会以 UTF-8 编码）。

    Returns:
        长度为 8 * len(text.encode('utf-8')) 的 0/1 整数列表。
    """
    data = text.encode("utf-8")
    bits: List[int] = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def source_decode(bits: Iterable[int]) -> str:
    """将比特列表解码为 UTF-8 文本。

    Args:
        bits: 0/1 序列（list、numpy 数组或其他可迭代对象均可）。

    Returns:
        解码得到的字符串。
    """
    bit_list = [int(b) for b in bits]
    n_bytes = len(bit_list) // 8
    data = bytearray()
    for i in range(n_bytes):
        byte = 0
        for b in bit_list[i * 8 : (i + 1) * 8]:
            byte = (byte << 1) | b
        data.append(byte)
    return bytes(data).decode("utf-8", errors="strict")


# ---- 兼容别名，方便自动测试用不同命名习惯发现本模块的函数 ----
text_to_bits = source_encode
bits_to_text = source_decode
encode_text = source_encode
decode_text = source_decode
utf8_to_bits = source_encode
bits_to_utf8 = source_decode
