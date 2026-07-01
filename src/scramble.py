"""
扰码模块 (Scramble / Descramble)
--------------------------------
职责：对发送比特做可逆的扰码处理，打散原始比特的统计规律
（避免长串 0/1，有利于同步和信道编码性能），并提供简单的保密性。

设计选择：PN 序列扰码（伪随机序列 XOR）
- 使用 numpy 的 PCG64 伪随机数生成器，以固定 seed 生成与输入等长的
  0/1 伪随机序列（PN 序列），与输入比特逐位 XOR。
- XOR 是自逆运算：只要发送端和接收端使用同一个 seed 生成同一段 PN 序列，
  两次 XOR 即可还原原始比特，因此 scramble 和 descramble 可以复用同一份实现。
- 相比线性反馈移位寄存器 (LFSR) 手工实现，使用 numpy 的可复现伪随机数
  生成器可以保证"固定 seed 可复现"，同时代码更简洁、更不容易出错。

课程相关性：这与教材中 PN 序列扰码（如 GSM/3G 中常见的加扰）思想一致，
只是随机序列生成方式使用了现代 PRNG 而非硬件 LFSR。
"""

from __future__ import annotations

from typing import Iterable, List

import numpy as np


def _pn_sequence(length: int, seed: int) -> List[int]:
    """使用固定 seed 生成长度为 length 的 0/1 伪随机序列。"""
    rng = np.random.default_rng(seed)
    return rng.integers(0, 2, size=length).tolist()


def scramble(bits: Iterable[int], seed: int = 2026) -> List[int]:
    """对比特序列进行 PN 序列扰码（XOR）。

    Args:
        bits: 待扰码的 0/1 序列。
        seed: PN 序列生成种子，发送端/接收端必须一致。

    Returns:
        扰码后的比特列表，长度与输入相同。
    """
    bit_list = [int(b) for b in bits]
    pn = _pn_sequence(len(bit_list), seed)
    return [b ^ p for b, p in zip(bit_list, pn)]


def descramble(bits: Iterable[int], seed: int = 2026) -> List[int]:
    """对比特序列进行解扰。XOR 为自逆运算，实现与 scramble 完全相同。"""
    return scramble(bits, seed=seed)


# ---- 兼容别名 ----
scramble_bits = scramble
descramble_bits = descramble
encrypt = scramble
decrypt = descramble
encrypt_bits = scramble
decrypt_bits = descramble
