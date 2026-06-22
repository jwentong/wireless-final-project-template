# TEST_PLAN.md

## 公开测试映射

公开测试 20 条对应以下验收点：

| 编号 | 验收点 | 本项目覆盖 |
| --- | --- | --- |
| TC-T-001 | 必需文件和目录 | 补齐文档、`main.py`、`src/`、`tests/` |
| TC-T-002 | DESIGN 覆盖固定系统链路 | `DESIGN.md` 明确 Source Encode 到 Metrics |
| TC-T-003 | mock 报告含风险和修订 | `MOCK_TEST_REPORT.md` |
| TC-T-004 | UTF-8 source codec 可逆 | `tests/test_source.py` |
| TC-T-005 | Frame 字段完整 | `src/framing.py` |
| TC-T-006 | Frame build/parse 可逆 | `tests/test_framing.py` |
| TC-T-007 | Scramble/Encrypt 可逆 | `tests/test_channel.py` |
| TC-T-008 | Channel coding 可逆 | `tests/test_channel.py` |
| TC-T-009 | QPSK 映射符合 PRD | `tests/test_qpsk.py` |
| TC-T-010 | QPSK 无噪声解调 | `tests/test_qpsk.py` |
| TC-T-011 | QPSK padding 按 length 去除 | `tests/test_framing.py` |
| TC-T-012 | AWGN fixed seed 可复现 | `tests/test_channel.py` |
| TC-T-013 | 同步检测 25 符号 offset | `tests/test_channel.py` |
| TC-T-014 | metrics 字段 | CLI 端到端测试 |
| TC-T-015 | 12 dB 完全恢复 | `tests/test_end_to_end.py` |
| TC-T-016 | 生成至少两张图 | CLI 端到端测试 |
| TC-T-017 | 非交互 CLI | `main.py` 使用 argparse |
| TC-T-018 | AI_LOG 记录 | `AI_LOG.md` |
| TC-T-019 | 结果解释 | `DESIGN.md` |
| TC-T-020 | 不直接复制文件 | pipeline 写入接收端解码文本 |

## 单元测试

- Source：验证 `source_decode(source_encode("中文QPSK测试")) == 原文`，并检查 bitstream 长度是 8 的倍数。
- Scramble：验证相同 seed 下 `descramble(scramble(bits, seed), seed) == bits`。
- Channel coding：验证重复码无噪声下可逆，低长度或非 3 整数倍输入不崩溃。
- Framing：验证 `parse_frame(build_frame(bits))["payload"] == bits`，奇数 payload 经过 QPSK padding 后仍可按 `coded_length` 恢复。
- QPSK：验证 `00,01,11,10` 分别落在第一、第二、第三、第四象限，平均符号功率约为 1，无噪声 demodulate 无误码。
- AWGN：同一输入、同一 SNR、同一 seed 输出可复现。
- Synchronization：构造 25 符号随机前缀，检测误差不超过 1 个符号。

## 端到端和鲁棒性测试

- 在临时 UTF-8 中文文本上运行 `python main.py --input input.txt --output out/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn`，验收文本完全一致。
- 使用不同中文、英文、标点和换行文本测试 Source 和 Pipeline。
- 使用不同 seed 验证扰码、AWGN 和随机前缀仍可复现。
- 使用较低 SNR 验证程序不崩溃，仍生成 `received.txt`、`metrics.json` 和失败原因。
- 替换 `Test.txt` 内容后再次运行，验证没有针对教师样例硬编码。

## 手动验收命令

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
pytest public_tests -q
pytest tests -q
```

验收标准：

- `results/received.txt` 与 `Test.txt` 完全一致。
- `results/metrics.json` 包含最低字段，`text_match_rate == 1.0`，`checksum_pass == true`。
- `results/constellation.png`、`results/ber_curve.png`、`results/sync_peak.png` 至少两张非空，本实现应全部生成。

## Level 3 Extension Test

增加 Rayleigh 提高模块测试：

- `test_rayleigh_fixed_seed_is_reproducible_and_returns_channel_state` 验证 flat Rayleigh Channel 在固定 seed 下可复现，并返回非零复信道系数。
- `test_cli_rayleigh_extension_recovers_temp_text` 使用 `--channel rayleigh --snr 18` 验证接收端 preamble 信道估计和均衡后仍能端到端恢复文本。

该扩展不改变公开验收默认 AWGN 命令；公开测试仍使用 `--channel awgn`。