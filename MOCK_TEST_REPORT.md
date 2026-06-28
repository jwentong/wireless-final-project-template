# MOCK_TEST_REPORT.md

## 1. Mock 测试概述

在正式写完整代码前，按 PRD 先做 mock 测试，目标是验证设计文档中的接口、帧结构、同步流程和端到端流程是否可行。以下 mock 记录用于解释设计风险、defect 和 revision。

## 2. Mock 1：UTF-8 Source Encode 与 Source Decode

- mock 场景：输入包含中文、英文、标点的字符串。
- 检查内容：`source_encode` 输出 bitstream，长度应为 8 的整数倍；`source_decode` 应恢复原文。
- 发现问题 / issue：如果接收端不知道原始 bit 长度，QPSK padding 可能导致末尾多余 0 进入 UTF-8 解码。
- revision：在帧中加入 `length` 字段，并在 Source Decode 前按 `payload_bits` 裁剪。

## 3. Mock 2：Frame Build / Parse

- mock 场景：随机 payload bitstream，长度包括奇数长度 257 bit。
- 检查内容：帧必须包含 preamble、length、payload、checksum / CRC，并能 parse 回 payload。
- 发现问题 / risk：若只存原始 length，而 payload 实际为 channel-coded bits，接收端无法知道帧内 payload 的物理长度。
- revision：帧头同时加入 `length` 和 `payload_length`。`length` 表示源编码后原始 payload bit 数，`payload_length` 表示实际编码后载荷长度。

## 4. Mock 3：Synchronization

- mock 场景：在已知 preamble 前加入 25 个随机复符号。
- 检查内容：相关峰值位置应为 25 左右，误差不超过 1 个 QPSK 符号。
- 发现问题 / defect：短 preamble 在噪声下相关峰值可能不明显。
- revision：使用 128 bit preamble，即 64 个 QPSK 符号，提高相关峰值的区分度。

## 5. Mock 4：End-to-End CLI

- mock 场景：运行 `python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn`。
- 检查内容：生成 `received.txt`、`metrics.json`、`constellation.png`、`ber_curve.png`、`sync_peak.png`。
- 发现问题 / risk：如果 length 或 CRC 字段在噪声下出错，payload 即使能被重复码纠正，也可能无法进入译码流程。
- revision：对 length、payload_length 和 CRC 字段使用 5 重复保护；payload 使用 3 重复码。

## 6. 设计修订总结

本项目至少完成 4 个 mock 测试。主要设计 change 包括：

1. 增加 `length` 字段，用于去除 QPSK padding。
2. 增加 `payload_length` 字段，用于解析 channel-coded payload。
3. 增强 preamble 长度，提高 Synchronization 鲁棒性。
4. 对帧头关键字段增加重复保护，降低高 SNR 下偶发 header bit error。

