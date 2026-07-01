"""
信道编码模块 (Channel Encode / Decode)
--------------------------------------
职责：为发送比特提供基本的抗噪能力（前向纠错，FEC）。

设计选择：三倍重复码 (Repetition Code, rate = 1/3)
- 每个信息比特重复发送 3 次；接收端对每 3 个接收比特做多数判决(majority vote)。
- 选择重复码而不是汉明码/卷积码的原因：
  1) 原理最直观，最容易在答辩中清晰解释纠错能力和编码率的关系；
  2) 在 QPSK + AWGN 且 SNR>=12dB 的基础验收条件下，单比特误码率已经极低，
     重复码足以在低 SNR 场景下把 BER 进一步压低，同时不引入额外的
     译码时延或复杂的维特比译码；
  3) 编码率 R = 1/3 是固定且已知的常数，这一点在帧结构模块中被用来
     从"信道编码后比特数"精确反推"信道编码前(即扰码后)比特数"，
     从而满足 PRD 中"length 字段用于恢复原始 payload 长度"的约定
     （详见 DESIGN.md 第 4 节的换算说明）。

局限性（在 DESIGN.md/REPORT.md 中会进一步讨论）：
- 重复码是最简单的 FEC，编码效率低（有效吞吐量只有 1/3），
  纠错能力也弱于汉明码/卷积码，只能纠正每 3 位中的 1 位错误。
- 作为 Level 3 提高项，可以替换为卷积码 + Viterbi 译码以获得更好的
  编码增益，本项目将其列为后续可扩展方向。
"""

from __future__ import annotations

from typing import Iterable, List

REPEAT = 3  # 重复次数，即码率的倒数 (rate = 1/REPEAT)


def channel_encode(bits: Iterable[int]) -> List[int]:
    """三倍重复编码：每个比特重复 REPEAT 次。"""
    coded: List[int] = []
    for b in bits:
        b = int(b)
        coded.extend([b] * REPEAT)
    return coded


def channel_decode(bits: Iterable[int]) -> List[int]:
    """多数判决译码：每 REPEAT 个比特还原为 1 个比特。"""
    bit_list = [int(b) for b in bits]
    n = len(bit_list) // REPEAT
    decoded: List[int] = []
    for i in range(n):
        chunk = bit_list[i * REPEAT : (i + 1) * REPEAT]
        decoded.append(1 if sum(chunk) * 2 > REPEAT else 0)
    return decoded


# ---- 兼容别名 ----
encode = channel_encode
decode = channel_decode
encode_bits = channel_encode
decode_bits = channel_decode
fec_encode = channel_encode
fec_decode = channel_decode
