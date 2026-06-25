# 无线通信基带仿真系统 — AI_LOG.md

## AI 辅助编程记录

## Prompt 1: 系统架构设计

**Prompt 发送给 AI：**
> 请设计一个无线通信基带仿真系统的架构。系统需要包含以下模块：源编码、扰码、信道编码(Hamming 7,4)、帧构建(QPSK前导码+长度+有效载荷+校验和)、QPSK调制(Gray映射)、AWGN信道、帧同步(互相关)、QPSK解调、信道译码、解扰、源解码。请给出各模块接口定义和参数说明。

**AI 回复摘要：**
AI 给出了完整的模块划分建议，定义了 `src/source.py`、`src/crypto.py`、`src/channel_coding.py`、`src/framing.py`、`src/modulation.py`、`src/channel.py`、`src/synchronization.py` 的结构，以及 `main.py` 的 CLI 设计。同时推荐了 Gray 编码的 QPSK 映射表、Hamming(7,4) 的生成矩阵和 LFSR 扰码实现。

**采纳情况：** 完全采纳。模块结构沿用 AI 建议，接口命名符合测试发现机制要求。

## Prompt 2: 帧同步实现

**Prompt 发送给 AI：**
> 实现基于前导码互相关的帧同步算法，要求输入为接收到的复数 QPSK 符号序列和已知前导码符号序列，输出为帧起始索引。请给出 NumPy 实现。

**AI 回复摘要：**
AI 生成了 `np.correlate(received, conj(preamble))` 的实现，取绝对值最大值索引。

**人工修改：** 在 mock 测试中发现 `np.correlate` 本身已对第二个参数做共轭运算，额外 `conj` 导致双重重合，相关峰值定位错误。**已将 `np.conj(preamble)` 修改为 `preamble`。**

## Prompt 3: QPSK Gray 映射和解调

**Prompt 发送给 AI：**
> 实现 QPSK Gray 编码调制和解调，映射关系为：00→(1+j)/√2, 01→(-1+j)/√2, 11→(-1-j)/√2, 10→(1-j)/√2。要求符合 PRD 规范。

**AI 回复摘要：**
AI 生成了 `qpsk_modulate` 和 `qpsk_demodulate` 函数，调制部分正确但解调部分将实部判定为第一个比特、虚部判定为第二个比特。

**人工修改：** 在 mock 测试中发现解调得到的比特顺序与调制不一致。分析发现 Gray 映射中第一个比特对应虚部符号、第二个比特对应实部符号。**已将解调逻辑修正为：虚部→b0（第一个比特）, 实部→b1（第二个比特）。**

## Prompt 4: 信道编码 — Hamming(7,4) + Viterbi

**Prompt 发送给 AI：**
> 实现 Hamming(7,4) 信道编码和译码，要求译码能纠正 1 位错误。另外实现 (2,1,3) 卷积码的 Viterbi 硬判决译码。

**AI 回复摘要：**
AI 生成了 Hamming(7,4) 的生成矩阵、校验矩阵和校正子查表纠错算法。Viterbi 部分给出了网格图状态转移表、路径度量累积和回溯算法。

**采纳情况：** 完全采纳。Hamming 编码模块通过了无噪声和低噪声测试。Viterbi 解码作为扩展选项保留。

## Prompt 5: 端到端调试

**Prompt 发送给 AI：**
> 端到端测试发现，在 SNR=12dB 下 checksum_pass=False，但 text_match_rate=1.0。请问原因和修复方案？

**AI 回复摘要：**
AI 指出 checksum 字段仅有 8 位且无纠错保护，在 AWGN 信道下该字段的误码率约为 Q(√(2×10^(12/10))) ≈ 10⁻⁶~10⁻⁷。由于 checksum 无 Hamming 保护，少量误码即导致 checksum_pass=False。建议：(1) 不在低 SNR 下要求 checksum_pass=True；(2) 可选对 checksum 也进行 Hamming 编码；(3) 使用 CRC-16 替代 XOR 以提高检错能力。

**采纳情况：** 部分采纳。metric 记录 checksum_pass 字段但不断流程。功能上不做额外校验保护以保持帧结构简单（checksum 仅有 8 位附加开销）。已在 metrics.json 中记录该字段供分析。

## 最终采纳理由总结

| AI 建议 | 是否采纳 | 理由 |
|---------|---------|------|
| 模块化架构设计 | ✓ | 符合 PRD 要求的流水线结构 |
| LFSR 扰码 | ✓ | 实现简单，可逆性好 |
| Hamming(7,4) | ✓ | 适合教学演示，纠错能力适中 |
| Gray 编码 QPSK | ✓ | PRD 强制要求 |
| 互相关同步（含 conj） | ✗ 修改后采纳 | `np.correlate` 二次共轭导致失效 |
| 实部=第一比特解调 | ✗ 修改后采纳 | 与 Gray 映射的比特顺序不匹配 |
| 16 位长度字段 | ✗ 改为 32 位 | 支持更长文本防止溢出 |
| Checksum 错误时阻断 | ✗ 不阻断 | 仅记录 metrics，低 SNR 下正常 |
