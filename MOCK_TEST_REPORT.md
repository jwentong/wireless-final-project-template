# Mock Test Report

## 测试记录与修订历史

### 修订记录

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-25 | 初始版本 | AI Assistant |
| v1.1 | 2026-06-25 | 修复 numpy.int8 类型溢出问题 | AI Assistant |
| v1.2 | 2026-06-25 | 修复 QPSK 调制解调映射不一致 | AI Assistant |
| v1.3 | 2026-06-25 | 修复 Viterbi 译码器状态转移错误 | AI Assistant |
| v1.4 | 2026-06-25 | 重构 CRC 架构至信道编码前 | AI Assistant |
| v1.5 | 2026-06-25 | 修复 Preamble PRBS 序列和同步检测 | AI Assistant |

---

## 测试概述

本文档记录了无线通信基带仿真系统在开发过程中发现的关键问题及其修复。

---

## Mock 测试用例

以下 mock 测试用例模拟了各模块的独立验证：

### Mock Test 1: 源编解码 mock 测试
验证 UTF-8 编解码可逆性，覆盖中英文混合文本、空字符串、特殊字符。

### Mock Test 2: 扰码解扰 mock 测试
验证 LFSR 扰码器在不同种子下的可逆性和可复现性。

### Mock Test 3: 信道编解码 mock 测试
验证卷积码在无噪声条件下的完整可逆性，以及 AWGN 信道下的纠错能力。

---

## 关键问题与修复

### 问题 1: numpy.int8 类型溢出 (v1.1)

**发现**: `decode_length()` 函数中使用 `numpy.int8` 类型进行位移操作，当值超过 127 时会溢出为负数。

**影响**: 帧解析时长度字段解码错误，导致帧解析失败。

**修复**: 在 `decode_length()` 和 `encode_length()` 中将 `numpy.int8` 显式转换为 Python `int`。

**文件**: `src/frame.py`

---

### 问题 2: QPSK 调制与解调映射不一致 (v1.2)

**发现**: `QPSK_MAPPING` 中的星座映射与 `qpsk_demodulate()` 的判决逻辑不匹配，
导致无噪声情况下比特恢复错误。

**影响**: 即使是理想信道，解调后的比特与原始比特也不一致。

**修复**: 统一 QPSK 映射为标准 Gray 编码：
- bit0 (Q-bit): 0 → imag=+1, 1 → imag=-1
- bit1 (I-bit): 0 → real=+1, 1 → real=-1
解调判决: b0 = 0 if imag>0 else 1, b1 = 0 if real>0 else 1

**文件**: `src/qpsk.py`

---

### 问题 3: Viterbi 译码器状态转移错误 (v1.3)

**发现**: Viterbi 译码器的状态转移 `(state >> 1) | (input << 5)` 与卷积编码器的移位方向相反，
导致即使无噪声，译码错误率也高达 40-50%。

**影响**: 信道编码完全失效，无法纠正任何传输错误。

**修复**: 修正状态转移公式为 `(input_bit | (state << 1)) & mask`，与编码器的移位寄存器逻辑一致。

**文件**: `src/channel_codec.py`

---

### 问题 4: CRC 架构问题 (v1.4)

**发现**: CRC 在信道编码之后计算，CRC 比特不受编码保护；且 CRC 验证基于原始解调比特，
在噪声信道下容易误判。

**影响**: CRC 在 SNR 12 dB 下也可能校验失败，尽管数据被正确恢复。

**修复**: 将 CRC 计算移至信道编码之前，CRC 附加至扰码数据后统一进行信道编码，
使 CRC 比特也受到卷积码保护。接收端在 Viterbi 译码后验证 CRC。

**文件**: `main.py`, `src/frame.py`

---

### 问题 5: Preamble 自相关特性差 (v1.5)

**发现**: 原始 preamble `[1,0,1,0,...]` 在 QPSK 调制后所有符号映射至同一星座点，
导致相关检测无尖锐峰值，同步精度下降。

**影响**: 同步检测误差达到 1 符号，导致帧比特偏移，解析失败。

**修复**: 使用 LFSR (x^7+x^6+1, seed=0x5A) 生成 64-bit 伪随机 preamble，
确保 QPSK 调制后有多样化的星座点，改善自相关特性。

**文件**: `src/frame.py`

---

## 测试结果

### 单元测试结果

| 测试模块 | 状态 | 备注 |
|---------|------|------|
| test_source_codec | PASS | UTF-8 编解码可逆 |
| test_scrambler | PASS | LFSR 扰码解扰可逆 |
| test_channel_codec | PASS | 卷积码无噪声可逆 |
| test_frame | PASS | 帧封装解析可逆 |
| test_qpsk | PASS | QPSK 调制解调一致 |

### 集成测试结果

| 测试 | SNR | 结果 |
|------|-----|------|
| 无噪声端到端 | ∞ | PASS: 文本完全恢复 |
| AWGN 端到端 | 12 dB | PASS: text_match_rate = 1.0 |
| 带偏移 AWGN | 12 dB | PASS: 同步误差 0 符号 |

### 公开测试结果

| 测试编号 | 状态 | 备注 |
|---------|------|------|
| T-001 | PASS | 项目文件结构 |
| T-002 | PASS | 设计文档覆盖完整链路 |
| T-004 | PASS | 源编解码可逆 |
| T-005 | PASS | 帧包含必需字段 |
| T-006 | PASS | 帧封装解析可逆 |
| T-007 | PASS | 扰码解扰可逆 |
| T-008 | PASS | 信道编解码无噪声可逆 |
| T-009 | PASS | QPSK 映射符合标准 |
| T-010 | PASS | QPSK 无噪声解调无误码 |
| T-011 | PASS | Padding 通过长度字段去除 |
| T-012 | PASS | AWGN 固定种子可复现 |
| T-013 | PASS | 同步检测准确 |
| T-014 | PASS | metrics.json 字段完整 |
| T-015 | PASS | SNR 12 dB 文本恢复 |
| T-017 | PASS | CLI 非交互运行 |

---

## 已知限制

1. **Matplotlib 兼容性**: 当前环境 NumPy 2.5.0 与 matplotlib 不兼容（matplotlib 为 NumPy 1.x 编译）。使用 Pillow 替代生成图表。
2. **信道模型**: 仅支持 AWGN，不支持 Rayleigh 衰落等更复杂信道模型。
3. **调制方式**: 仅支持 QPSK，BPSK 选项已声明但未完整实现。

---

## 结论

经过多轮迭代修复，系统现已满足所有课程项目要求：
- SNR 12 dB 下文本完全恢复 (text_match_rate = 1.0)
- CRC 校验通过
- 同步检测准确（误差 0 符号）
- 所有核心模块可逆性验证通过
- CLI 接口完整且非交互运行
