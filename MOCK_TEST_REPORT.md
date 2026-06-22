# MOCK_TEST_REPORT.md

## mock 测试概览

本报告记录设计阶段的 mock 测试、发现的问题、风险和修订。mock 测试不替代公开测试，但用于提前验证接口和链路设计。

## mock 测试 1：UTF-8 Source Encode / Source Decode

输入 `"中文QPSK测试"`，执行 Source Encode 得到 bitstream，再执行 Source Decode。预期恢复文本与原文完全一致，bitstream 长度为 8 的倍数。

结果：设计通过。发现的风险是低 SNR 下恢复 bitstream 可能无法构成合法 UTF-8。修订方案是在 Source Decode 中截断到整字节，并使用安全解码避免 failure。

## mock 测试 2：Frame Build / parse_frame 与 QPSK padding

构造奇数长度 payload，执行 Frame Build、QPSK Modulate、QPSK Demodulate、parse_frame。预期解析后的 payload 与输入 payload 一致。

结果：初始设计只有 `length` 字段，无法区分原始 source length 和已编码 payload length，存在 padding 被误当 payload 的缺陷。修订为增加 `coded_length` 字段，Frame Parse 使用 `coded_length` 裁剪 payload。

## mock 测试 3：25 符号随机前缀下同步

构造 25 个随机复符号前缀，后接 preamble 和 payload，执行滑动相关 Synchronization。预期检测到的起点误差不超过 1 个符号。

结果：mock 检测通过。设计风险是低 SNR 或随机前缀偶然相关峰较高可能导致误检。修订为使用 32 个 QPSK 符号的 preamble，并输出 `sync_peak.png` 便于分析相关峰。

## mock 测试 4：SNR=12 dB 端到端恢复

运行统一 CLI，输入临时中文文本，设置 `snr=12 seed=2026 mod=qpsk channel=awgn`。预期 `received.txt` 与输入完全一致，BER 为 0，text_match_rate 为 1.0。

结果：设计要求重复码、CRC32、同步和 QPSK 判决协同工作。若 checksum failure 或 text mismatch，优先检查同步起点、header 字段、QPSK padding 和 descramble seed。

## DESIGN.md 修订记录

- revision 1：将帧结构从 `preamble + length + checksum + payload` 修改为 `preamble + length + coded_length + checksum + payload`。
- revision 2：明确 CRC32 覆盖原始 source payload bitstream，而不是覆盖扰码或信道编码后的 payload。
- revision 3：补充低 SNR failure 行为，要求不崩溃并记录 `failure_reason`。
- revision 4：补充 QPSK 星座图、BER 曲线和同步峰值图的解释。

## mock 测试 5：Rayleigh 衰落和均衡

构造可选 `--channel rayleigh` 场景，发送端使用 flat Rayleigh Channel，接收端利用 preamble 估计信道系数并均衡。mock 预期是在较高 SNR 下仍能恢复文本。发现的风险是深衰落或低 SNR 会放大均衡后的噪声，因此该功能作为 Level 3 extension，不改变默认 AWGN 验收链路。