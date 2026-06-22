# 无线通信技术期末项目 PRD 摘要

## 项目目标

本项目实现一个可运行、可测试、可解释的无线通信文件传输基带仿真系统。系统读取 UTF-8 编码的 `Test.txt`，经过发送端、AWGN 信道和接收端处理后，恢复为 `results/received.txt`，并输出性能指标和图表。

## 固定系统链路

固定链路为：

```text
Test.txt
-> Source Encode
-> Encrypt/Scramble
-> Channel Encode
-> Frame Build
-> QPSK Modulate
-> Channel
-> Synchronization
-> QPSK Demodulate
-> Channel Decode
-> Decrypt/Descramble
-> Source Decode
-> results/received.txt
-> Metrics/Plots
```

基础系统必须完成 QPSK、AWGN、同步、信道编码、译码、解扰、源解码和文件恢复。BPSK、16-QAM、Rayleigh、OFDM、均衡等属于扩展内容，不替代基础 QPSK 链路。

## 输入、输出和统一 CLI

统一命令行为：

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

运行后必须生成：

- `results/received.txt`
- `results/metrics.json`
- `results/constellation.png`、`results/ber_curve.png`、`results/sync_peak.png` 中至少两张图，本实现生成三张。

在 `SNR >= 12 dB`、`channel=awgn`、`mod=qpsk`、固定 seed 条件下，`received.txt` 应与输入文本完全一致。较低 SNR 下不强制完全一致，但程序不能崩溃，仍应输出 metrics 和失败原因。

## 基础算法要求

- Source Encode / Source Decode：UTF-8 文本与 bitstream 互转。
- Encrypt/Scramble：可逆 PN XOR 扰码。
- Channel Encode / Channel Decode：基础抗噪信道编码，本实现采用 3 重复码。
- Frame Build：帧包含 preamble、length、coded_length、CRC32 checksum 和 payload。
- QPSK：采用 Gray 映射，平均符号功率归一化为 1。
- Channel：AWGN，SNR 定义为调制符号平均功率与复高斯噪声平均功率之比。
- Synchronization：利用已知 preamble 做滑动相关峰值检测，支持 0 到 128 个 QPSK 符号随机前缀。
- Metrics：记录 SNR、seed、BER、FER、text_match_rate、checksum_pass、sync_start_index 等字段。

## 提交和学术诚信

项目通过 GitHub Fork + Pull Request 提交。学生需要在 PR 中填写学号、姓名、GitHub username、Fork URL、Branch 和完成清单。

禁止直接复制 `Test.txt` 到 `received.txt`，禁止硬编码公开测试输入输出，禁止提交本人无法解释的代码。最终评分会结合公开测试、隐藏验证、文档检查和答辩解释。

## Level 3 提高模块说明

在基础 Level 2 系统之外，本项目增加 `--channel rayleigh` 可选模式，用于模拟 flat Rayleigh 衰落信道。接收端通过 preamble 估计信道并进行一拍均衡。该功能属于提高模块，不影响基础 AWGN 验收命令。