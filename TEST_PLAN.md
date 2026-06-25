# TEST_PLAN.md — 测试计划

## 1. 测试范围

本文档基于教师公开的 20% 测试案例（`public_tests/` 目录），制定模块级和端到端测试计划，用于验证系统是否满足 PRD 基本要求。

## 2. 公开测试用例映射

### 2.1 结构与文档测试

| 编号 | 测试用例 | 覆盖要求 | 预期结果 |
|------|----------|----------|----------|
| TC-T-001 | 项目目录包含必需提交物 | DESIGN.md, TEST_PLAN.md, MOCK_TEST_REPORT.md, AI_LOG.md, main.py, src/, tests/ 都存在 | 全部通过 |
| TC-T-002 | DESIGN.md 覆盖固定系统链路 | 至少 9 个关键词命中，且必须提到 QPSK | 命中 ≥ 9 个 |
| TC-T-003 | MOCK_TEST_REPORT.md 包含设计修订记录 | 至少 3 个 mock 场景，描述风险和修订 | 通过 |
| TC-T-018 | AI_LOG.md 记录 AI 辅助过程 | 至少 3 条 prompt，说明人工修改和采纳理由 | 通过 |
| TC-T-019 | 文档解释关键结果 | QPSK 星座、BER、失败原因 | 通过 |
| TC-T-020 | 无直接文件复制 | 代码中无 shutil.copy 等绕过链路操作 | 通过 |

### 2.2 核心模块测试

| 编号 | 测试用例 | 模块 | 输入 | 预期 |
|------|----------|------|------|------|
| TC-T-004 | UTF-8 源编码可逆 | source.py | 中文文本 | 编码后 bit 数为 8 的倍数，解码完全恢复 |
| TC-T-005 | 帧结构含必需字段 | framing.py | 2400 bit payload | 帧含 preamble, length, payload, checksum/CRC |
| TC-T-006 | 帧封装解析可逆 | framing.py | 257 bit payload | 解析恢复的 payload 与原 payload 一致 |
| TC-T-007 | 扰码/加密可逆 | crypto.py | 511 bit, seed=2026 | 加扰后解扰完全恢复 |
| TC-T-008 | 信道编码无噪可逆 | channel_coding.py | 400 bit | 编码译码后完全恢复 |
| TC-T-009 | QPSK 星座映射正确 | modulation.py | 00,01,11,10 | Gray 编码四个象限，单位功率 |
| TC-T-010 | QPSK 无噪解调无误 | modulation.py | 512 bit | 解调 bit 与输入一致 |
| TC-T-011 | QPSK padding 被 length 去除 | framing+modulation | 255 bit payload | 恢复长度=255 |
| TC-T-012 | AWGN 固定 seed 可复现 | channel.py | 4 symbols, SNR=12dB, seed=2026 | 两次输出完全一致 |

### 2.3 系统集成测试

| 编号 | 测试用例 | 条件 | 预期 |
|------|----------|------|------|
| TC-T-013 | 同步检测 25 符号偏移 | 噪声前缀+preamble+载荷 | 检测起点偏移 ≤ 1 符号 |
| TC-T-014 | metrics.json 含必需字段 | SNR=12dB, seed=2026 | 10 个字段全含 |
| TC-T-015 | 端到端恢复文本一致 | SNR=12dB, seed=2026 | received.txt = Test.txt, text_match_rate=1.0 |
| TC-T-016 | 生成至少两类图表 | SNR=12dB, seed=2026 | 3 图中至少 2 图非空 |
| TC-T-017 | CLI 非交互式运行 | 标准命令行参数 | 程序正常退出，无需人工输入 |

## 3. 自测计划（Mock 测试）

在正式编码前，对关键接口进行 mock 测试：

### Mock-1: 源编码往返
- 输入："无线通信技术"
- 操作：encode → decode
- 检查：输出与输入一致，bitstream 长度为 8 的倍数

### Mock-2: 帧结构字典格式
- 输入：2400 bit payload
- 操作：build_frame
- 检查：返回 dict，包含 preamble, length, payload, crc 四个键

### Mock-3: 帧封装解析往返
- 输入：257 bit payload（奇数长度）
- 操作：build_frame → parse_frame
- 检查：解析 payload 与输入一致，length 字段为 257

### Mock-4: 扰码往返
- 输入：511 bit, seed=2026
- 操作：scramble → descramble
- 检查：完全恢复

### Mock-5: 信道编码往返（无噪）
- 输入：400 bit
- 操作：encode → decode
- 检查：完全恢复

### Mock-6: QPSK 星座象限
- 输入：[0,0,0,1,1,1,1,0]
- 操作：qpsk_modulate
- 检查：4 个符号分别位于 I/II/III/IV 象限，平均功率 ≈ 1

### Mock-7: QPSK 往返（无噪）
- 输入：512 bit
- 操作：modulate → demodulate
- 检查：完全恢复

### Mock-8: AWGN 复现性
- 输入：4 个 QPSK 符号，SNR=12dB, seed=2026
- 操作：两次 awgn
- 检查：输出完全一致

### Mock-9: 同步检测偏移
- 输入：25 个噪声符号 + preamble 符号 + 载荷符号
- 操作：synchronize
- 检查：检测起点 ≈ 25

## 4. 测试环境

```bash
# 依赖安装
pip install -r requirements.txt

# 运行公开测试
pytest public_tests -q

# 运行自编单元测试
pytest tests/ -q
```

## 5. 测试通过标准

- 所有公开测试（TC-T-001 ~ TC-T-020）通过
- `python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn` 正常退出
- `results/received.txt` 与 `Test.txt` 完全一致
- `results/metrics.json` 包含全部必需字段
- 至少生成 2 张图表
