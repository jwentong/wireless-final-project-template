# TEST_PLAN.md - 测试计划（基于教师公开 20 条测试案例）

参考 `wireless_project_test_set_20.feature` 中的 20 条公开测试案例，制定以下测试计划，覆盖结构检查、模块级单元测试、端到端测试三个层次。

## 1. 结构与文档检查（对应 TC-T-001, 002, 003, 018, 019, 020）

- 检查根目录存在 `DESIGN.md / TEST_PLAN.md / MOCK_TEST_REPORT.md / AI_LOG.md / main.py / src/ / tests/`。
- 检查 `DESIGN.md` 是否覆盖固定系统链路各模块关键词。
- 检查 `MOCK_TEST_REPORT.md` 是否记录了 mock 测试场景、设计缺陷和修订内容。
- 检查 `AI_LOG.md` 是否记录了关键 prompt、人工修改、采纳理由。
- 检查源码中不存在直接把 `Test.txt` 复制为 `received.txt` 的绕过行为。

## 2. 模块级单元测试（对应 TC-T-004 ~ TC-T-012）

| 测试点 | 覆盖场景 | 验证方式 |
|---|---|---|
| TC-T-004 源编码可逆 | 中文 UTF-8 文本 -> bits -> 文本 | `source_encode/source_decode` 往返一致，bits 长度为 8 的倍数 |
| TC-T-005 帧字段完整 | 2400 bit payload | `build_frame` 输出长度 > payload 长度（含 preamble/length/checksum 开销） |
| TC-T-006 帧封装解析可逆 | 257 bit 随机 payload | `build_frame` + `parse_frame` 还原 payload，length 字段与 payload 长度一致 |
| TC-T-007 扰码可逆 | 511 bit 随机比特，seed=2026 | `scramble` + `descramble` 还原原始比特 |
| TC-T-008 信道编码无噪声可逆 | 400 bit 随机比特 | `channel_encode` + `channel_decode` 无噪声下精确还原 |
| TC-T-009 QPSK 映射 | 00/01/11/10 四种比特对 | 星座点落在对应象限，Gray 编码，单位平均功率 |
| TC-T-010 QPSK 无噪声解调 | 512 bit 随机比特 | 调制+解调后与原比特完全一致 |
| TC-T-011 QPSK padding 去除 | 255 bit 奇数长度 payload | 帧内部 length 字段精确定位帧长度，qpsk 补零不影响解析 |
| TC-T-012 AWGN 可复现 | 固定符号+SNR=12+seed=2026 | 两次调用输出完全一致 |

## 3. 系统级 CLI 测试（对应 TC-T-013 ~ TC-T-017）

| 测试点 | 覆盖场景 | 验证方式 |
|---|---|---|
| TC-T-013 同步偏移检测 | 25 符号随机偏移 + 已知 preamble | `synchronize` 返回起点误差 ≤1 符号 |
| TC-T-014 metrics.json 字段 | 标准命令运行 | 输出包含 10 个必需字段 |
| TC-T-015 端到端一致性 | SNR=12, seed=2026 | `received.txt` 与 `Test.txt` 完全一致，`text_match_rate=1.0` |
| TC-T-016 图表生成 | 标准命令运行 | 至少生成 2 张图（constellation/ber_curve/sync_peak） |
| TC-T-017 CLI 非交互 | 标准命令运行 | 无需人工输入，正常退出码 0 |

## 4. 自测补充（在 `tests/` 目录中实现）

在教师公开测试之外，额外补充：
- 不同长度输入文本（很短/中等长度）下的端到端一致性；
- 低 SNR（0dB、-2dB）下系统不崩溃，能输出 BER/FER/text_match_rate（即使不完全一致）；
- 随机同步偏移在 0~128 符号范围内的检测误差统计。

## 5. 测试执行方式

```bash
pip install -r requirements.txt
pytest public_tests -q      # 教师公开测试
pytest tests -q             # 自测补充
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```
