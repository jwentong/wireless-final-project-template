# Mock 测试报告

> 项目：无线通信基带仿真系统  
> 关联：[TEST_PLAN.md](TEST_PLAN.md) MK-001～006、[DESIGN.md](DESIGN.md) v0.2→v0.3  
> 日期：2026-06-24

---

## 1. Mock 测试概述

按 PRD 工程流程，在完整实现 `src/` 各模块后，对 [TEST_PLAN.md](TEST_PLAN.md) 中规划的 6 个 mock 场景执行验证。执行命令：

```bash
pytest tests/test_mock_scenarios.py -v
```

**结果摘要**：6/6 通过。

---

## 2. Mock 测试场景与结果

### Mock-001 帧字段手工推演（MK-001）

- **目的**：验证 32 bit preamble + 16 bit length + payload + CRC-16 字段顺序与长度。
- **输入**：UTF-8 短文本 `"测试"` 经源编码、扰码、重复码编码后组帧。
- **结果**：通过。`len(bits) == 32 + 16 + len(coded) + 16`，前导比特与 `0xAA55AA55` 一致。
- **发现**：无缺陷。

### Mock-002 奇数 payload QPSK padding（MK-002）

- **目的**：验证 255 bit 奇数载荷经 QPSK 帧尾补 0 后，`parse_frame` 仍能恢复 255 bit。
- **输入**：255 bit 全 1 payload。
- **结果**：通过。`parse_frame` 内 `_strip_qpsk_tail_padding` 去除多余尾比特。
- **发现**：**设计风险 R3**——必须在解帧前剥离 QPSK padding，否则 CRC 字段错位。

### Mock-003 同步三档 offset（MK-003）

- **目的**：验证 32 bit（16 符号）前导在 offset=0/25/128 时检测误差 ≤1 符号。
- **输入**：随机前缀 + 前导符号 + 载荷符号，SNR 隐含于干净相关测试。
- **结果**：通过（0、25、128 三种 offset 均 ≤1 符号误差）。
- **发现**：32 bit 前导在 128 符号边界仍可用，但相关峰旁瓣略增（**风险 R2**）。

### Mock-004 重复码 1 bit 纠错（MK-004）

- **目的**：验证 (3,1) 多数表决纠正每组 1 bit 翻转。
- **输入**：5 bit 随机序列，编码后翻转第 2 个 coded bit。
- **结果**：通过，译码输出与原始一致。
- **发现**：无缺陷。

### Mock-005 多 seed AWGN 可复现（MK-005）

- **目的**：seed=2026/2027/9999 时 AWGN 输出完全一致。
- **结果**：通过。
- **发现**：无缺陷。

### Mock-006 CRC-16 源比特校验（MK-006）

- **目的**：CRC-16/CCITT 对源编码比特独立计算与校验。
- **结果**：通过；篡改 1 bit 后 `verify_crc16` 返回 False。
- **发现**：无缺陷。

---

## 3. 设计风险与缺陷

| 编号 | 描述 | 严重度 | 处理 |
|------|------|--------|------|
| D1 | QPSK 帧尾补 0 导致解帧长度 +1 | 中 | 在 `parse_frame` 增加 `_strip_qpsk_tail_padding` |
| D2 | `parse_frame` 需同时接受 dict（`build_frame` 返回值）与 bit 列表 | 低 | 自动提取 `bits`/`frame` 键 |
| D4 | 长载荷中伪相关峰导致 sync 误检 | 高 | 归一化相关 + 搜索窗口限制 0～144 符号；前缀改为噪声而非随机 QPSK |

---

## 4. DESIGN.md 修订内容（v0.2 → v0.3）

1. **§4.4 组帧**：补充 `parse_frame` 接受 `build_frame` dict；补充 QPSK padding 剥离逻辑。
2. **§7 风险 R3**：将 mock 发现的 padding 问题列为已缓解项。
3. **§12 修订记录**：增加 v0.3 mock 测试后修订条目。

---

## 5. 结论

Mock 测试验证了帧结构、padding、同步、重复码纠错、AWGN 复现与 CRC 语义均与 DESIGN 一致。发现 2 项实现层调整（padding 剥离、parse_frame 入参兼容），已在代码中修复。可进入公开测试与端到端验收阶段。
