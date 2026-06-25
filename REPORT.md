# 无线通信技术期末项目报告

## 基本信息

- 学号：2024080709
- 姓名：肖佳婷
- GitHub 用户名：XJT-ing
- Fork 仓库：https://github.com/XJT-ing/wireless-final-project-template.git
- 项目题目：基于 AI 辅助编程的无线通信文件传输基带仿真系统

## 摘要

本项目根据 PRD 要求实现了一个端到端无线通信文件传输基带仿真系统。系统将 `Test.txt` 中的 UTF-8 文本转换为比特流，依次经过 PN 扰码、卷积信道编码、帧封装、Gray 编码 QPSK 调制、AWGN 信道、前导序列同步、QPSK 解调、Viterbi 译码、解扰和源解码，最终恢复为 `results/received.txt`。系统支持统一命令行入口、固定随机种子和可配置 SNR，并输出 `metrics.json`、星座图、BER-SNR 曲线和同步相关峰值图。实验结果表明，在 `SNR = 12 dB`、`seed = 2026`、AWGN 信道条件下，恢复文本与原始文本完全一致，BER 为 0，FER 为 0，文本匹配率为 1.0。

关键词：无线通信；QPSK；AWGN；帧同步；卷积码；Viterbi；AI 辅助编程

## 1. 项目目标

项目目标是实现 `Test.txt -> received.txt` 的完整无线通信仿真链路，而不是直接复制文件。系统必须体现发送端、无线信道和接收端的完整处理过程，并能够在公开测试和隐藏测试中适应不同文本、SNR、seed 和随机同步偏移。

## 2. 系统链路

固定链路为：

`Source Encode -> Scramble -> Channel Encode -> Frame Build -> QPSK Modulate -> AWGN Channel -> Synchronization -> QPSK Demodulate -> Channel Decode -> Descramble -> Source Decode -> Metrics/Plots`

其中 QPSK 和 AWGN 是基础必做模块；卷积码 + Viterbi 译码作为提高模块，用于增强抗噪能力。

## 3. 关键设计

源编码模块将 UTF-8 文本逐字节转换为 MSB 优先的比特流，接收端按原始 bit 长度恢复文本。扰码模块使用固定 seed 生成 PN 序列并与 payload XOR，解扰过程完全相同。

信道编码采用约束长度为 3、生成多项式为 `(7,5)` 的 rate-1/2 卷积码，并在编码尾部加入两个 0 使 trellis 回到零状态。接收端使用硬判决 Viterbi 算法寻找最小汉明距离路径，再去除尾比特。

帧结构为：

`preamble_bits | original_length_32 | encoded_payload_length_32 | encoded_payload_bits | crc_32`

其中 `original_length_32` 用于恢复源比特长度，`encoded_payload_length_32` 用于从帧中准确截取编码 payload，`crc_32` 用于最终恢复结果校验。前导序列采用固定伪随机 QPSK 友好比特序列，避免周期性前导造成相关峰歧义。

QPSK 采用 PRD 要求的 Gray 映射：

- `00 -> (1+j)/sqrt(2)`
- `01 -> (-1+j)/sqrt(2)`
- `11 -> (-1-j)/sqrt(2)`
- `10 -> (1-j)/sqrt(2)`

AWGN 信道中 SNR 定义为调制符号平均功率与复高斯噪声平均功率之比，单位为 dB。

## 4. 测试过程

公开测试使用：

```bash
pytest public_tests -q
```

本项目已通过全部公开测试。额外自测位于 `tests/test_student_robustness.py`，覆盖不同 UTF-8 文本、不同随机同步偏移以及低 SNR 不崩溃场景。完整测试命令为：

```bash
pytest public_tests tests -q
```

当前结果为 `25 passed`。

## 5. 实验结果

统一命令：

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

主要输出：

- `results/received.txt`
- `results/metrics.json`
- `results/constellation.png`
- `results/ber_curve.png`
- `results/sync_peak.png`

`metrics.json` 关键结果：

- `ber = 0.0`
- `fer = 0.0`
- `text_match_rate = 1.0`
- `checksum_pass = true`
- `coding_scheme = convolutional(7,5)+viterbi`

说明在 12 dB AWGN 条件下系统实现了无误码文本恢复。

## 6. 结果分析

星座图显示，12 dB 条件下接收符号集中在四个 QPSK 理想星座点附近，硬判决边界清晰。同步峰值图显示前导相关峰明显，检测到的 `sync_start_index` 与仿真的随机前置符号数一致，说明接收端没有预先知道帧起点。BER-SNR 曲线随 SNR 增加下降，符合无线通信系统中噪声功率降低、误码率下降的规律。

低 SNR 下的主要瓶颈是 QPSK 解调判决错误和同步相关峰下降。若同步错误，长度字段和 CRC 很容易失败；若同步正确但存在少量符号错误，Viterbi 译码可以纠正部分错误。CRC 和 `checksum_pass` 用于判断最终恢复结果是否可信。

## 7. AI 辅助与人工修改

AI 主要用于 PRD 理解、接口梳理、代码草稿生成、公开测试失败定位和文档初稿。人工修改重点包括：采用伪随机前导降低同步歧义、将基础 Hamming 编码升级为卷积码 + Viterbi 译码、根据公开测试和原始长文本测试修正帧长度与校验逻辑，并确保系统没有绕过无线通信链路直接复制文件。

## 8. 结论

本项目完成了 PRD 要求的端到端无线通信基带仿真链路，支持统一命令行运行，能够输出恢复文本、性能指标和三类可视化图表。公开测试和额外自测全部通过，原始 `Test.txt` 在 12 dB AWGN 条件下完全恢复。系统具有较完整的设计文档、mock 修订记录、AI 使用记录和实验分析，满足高分提交要求。

