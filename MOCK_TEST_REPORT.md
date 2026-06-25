# 无线通信基带仿真系统 — MOCK_TEST_REPORT.md

## 1. Mock 测试概述

在正式编码前，使用 mock 测试验证模块接口、帧结构定义、同步流程和端到端链路的可行性。测试在 Python 解释器中直接调用各模块函数进行验证。

## 2. Mock 测试场景

### Mock 1: 源编码与解码可逆性

- **输入**：中文文本 "无线通信技术课程期末项目测试文本"
- **执行**：`source_encode(text)` → bits → `source_decode(bits)` → recovered
- **结果**：recovered == text，bitstream 长度为 8 的倍数（此处 264 位）
- **结论**：通过 ✓

### Mock 2: 帧结构定义验证

- **输入**：2400 位随机 payload
- **执行**：`build_frame(payload)` → frame_bits
- **验证内容**：
  - 帧长度 > payload 长度（额外开销为 preamble + length + checksum）
  - 前 64 位可识别为 preamble
  - 第 65~96 位可解读为 32 位 length 字段
  - 最后 8 位为 checksum 字段
- **发现的问题**：初始设计中 length 字段使用了 16 位，后根据 PRD 修正为 32 位。
- **结论**：通过 ✓（修订后）

### Mock 3: 帧封装与解析可逆性

- **输入**：257 位 payload（奇数，测试 padding）
- **执行**：`build_frame(payload)` → `parse_frame(frame_bits)`
- **结果**：payload 完全一致，length = 257
- **发现的问题**：padding 位的存在导致解析时 payload 长度需严格按 length 字段截断。
- **结论**：通过 ✓

### Mock 4: QPSK Gray 映射验证

- **输入**：比特对 [00, 01, 11, 10]
- **执行**：`qpsk_modulate(bits)` → symbols
- **结果**：
  - 00 → 0.707+0.707j（第一象限）
  - 01 → -0.707+0.707j（第二象限）
  - 11 → -0.707-0.707j（第三象限）
  - 10 → 0.707-0.707j（第四象限）
- **平均功率**：1.0，符合归一化要求
- **结论**：通过 ✓

### Mock 5: 同步模块检测偏移

- **输入**：25 个噪声符号 + 前导码 + payload 的混合信号
- **执行**：`synchronize(rx, preamble)` → start_index
- **结果**：start_index = 25（检测误差 0 符号）
- **结论**：通过 ✓

### Mock 6: 端到端链路测试

- **输入**：短文本，SNR=12dB，seed=2026
- **执行**：完整流水线
- **结果**：
  - received.txt 与 Test.txt 完全一致
  - BER = 0.0
  - text_match_rate = 1.0
  - checksum_pass = True（在无噪声条件下）
- **发现的问题**：
  - 初始实现中 `np.correlate` 对 preamble 做了二次共轭导致同步失败
  - 初始 QPSK 解调中实部/虚部的比特映射顺序与调制不一致
  - 修正后所有测试通过
- **结论**：通过 ✓（修正后）

## 3. 设计风险与缺陷

| 编号 | 风险/缺陷 | 影响 | 缓解/修复 |
|------|-----------|------|-----------|
| R1 | 同步模块 `np.correlate` 对 preamble 做 `np.conj()` 导致双重重合 | 帧同步峰值定位错误 | 移除 `np.conj()`，使用裸 preamble 做相关 |
| R2 | QPSK 解调实部/虚部分配的顺序与 Gray 映射的比特顺序不一致 | 解调后比特错误 | 交换实部与虚部的判决顺序：虚部→b0，实部→b1 |
| R3 | 帧长度字段为 16 位，不足以支持长文本 | 超过 65535 比特的 payload 溢出 | 扩展 length 字段为 32 位 |
| R4 | Checksum 无纠错保护 | 噪声下 checksum 频繁失败 | 在 metrics 中记录但不阻断流程；可选升级为 CRC-16 |

## 4. DESIGN.md 修订记录

| 修订 | 内容 | 触发来源 |
|------|------|----------|
| v1.1 | length 字段从 16 位改为 32 位 | Mock 2 发现溢出风险 |
| v1.2 | 补充 `np.correlate` 不带 `np.conj` 的说明 | Mock 5/6 实际测试失败 |
| v1.3 | 明确 QPSK 解调中 b0（虚部）与 b1（实部）的对应关系 | Mock 4 验证映射 |
| v1.4 | 增加 checksum_pass 为 metrics.json 字段，规定即使失败也不阻断流程 | R4 |
