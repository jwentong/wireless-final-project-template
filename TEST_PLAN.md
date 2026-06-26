# TEST_PLAN.md

## 1. 测试目标

测试目标是验证无线通信基带仿真系统满足 PRD 的基础链路、公开测试和隐藏验证风险要求。测试覆盖 Source Encode、Scramble、Channel Encode、Frame Build、QPSK、AWGN Channel、Synchronization、Channel Decode、Source Decode、Metrics 和 Plots。

## 2. 测试分层

| 层级 | 测试内容 | 通过标准 |
|---|---|---|
| 单元测试 | UTF-8、扰码、信道编码、QPSK、AWGN、同步 | 模块输入输出可逆或可复现 |
| 集成测试 | Frame Build + Parse、QPSK 调制解调、同步后解析 | payload 和 length 正确 |
| 端到端测试 | CLI 运行完整链路 | 生成 received.txt、metrics.json、至少两张图 |
| 鲁棒性测试 | 不同文本、SNR、seed、同步偏移 | 高 SNR 完全恢复，低 SNR 不崩溃 |
| 反硬编码测试 | 替换 Test.txt 内容 | 输出由通信链路恢复，不直接复制 |

## 3. 公开测试对应关系

| PRD / Public Test | 本项目验证点 |
|---|---|
| TC-T-001 | 必需文件：DESIGN.md、TEST_PLAN.md、MOCK_TEST_REPORT.md、AI_LOG.md、main.py、src、tests |
| TC-T-002 | DESIGN.md 覆盖 Source Encode 到 Metrics 的固定链路 |
| TC-T-004 | `source_encode` / `source_decode` 可逆 |
| TC-T-005 / 006 | `build_frame` / `parse_frame` 包含并恢复 preamble、length、payload、CRC |
| TC-T-007 | `scramble` / `descramble` 可逆 |
| TC-T-008 | `channel_encode` / `channel_decode` 无噪声可逆 |
| TC-T-009 / 010 / 011 | QPSK Gray 映射、无噪声解调、padding 去除 |
| TC-T-012 | AWGN 在固定 seed 下可复现 |
| TC-T-013 | Synchronization 可检测 25 符号前置偏移 |
| TC-T-014 - 017 | CLI、metrics、received.txt、plot 非交互运行 |
| TC-T-018 / 019 | AI_LOG 和结果分析说明 |
| TC-T-020 | 不存在直接复制文件捷径 |

## 4. Mock 测试计划

1. mock source/frame test：随机中文文本经过源编码、扰码、信道编码、封帧、解析后长度和 payload 一致。
2. mock qpsk/channel test：随机 bitstream 经过 QPSK、AWGN、解调后，在高 SNR 下 BER 接近 0。
3. mock sync test：人工加入 0、25、128 个符号偏移，验证同步误差不超过 1 个符号。
4. mock CLI test：替换不同 Test.txt 内容，运行统一命令，检查 `received.txt` 和 metrics。

## 5. 隐藏测试准备

隐藏测试可能改变中文文本长度、SNR、seed、同步偏移和异常参数。因此本项目避免写死输入文件内容，所有随机过程均由 seed 控制；CLI 对 `--input`、`--output`、`--snr`、`--seed` 参数做通用处理。

