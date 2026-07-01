# DESIGN.md - 系统设计文档

## 1. 总体架构

本系统实现 PRD 规定的固定链路：

```
Test.txt -> Source Encode -> Scramble -> Channel Encode -> Frame Build
-> QPSK Modulate -> Channel(AWGN) -> Synchronization -> QPSK Demodulate
-> Frame Parse -> Channel Decode -> Descramble -> Source Decode -> received.txt -> Metrics/Plots
```

发送端 (`transmit`) 和接收端 (`receive`) 均在 `main.py` 中编排，各模块的算法实现放在 `src/` 下，模块之间用普通的 `list[int]` 比特序列或 `numpy` 复数数组做接口，方便单独测试。

## 2. 模块接口与算法选择

| 模块 | 文件 | 关键函数 | 算法/参数 |
|---|---|---|---|
| Source Encode/Decode | `src/source.py` | `source_encode`, `source_decode` | UTF-8 文本按字节转 8bit（MSB 在前），逆过程按 8bit 分组还原字节再 UTF-8 解码 |
| Scramble/Descramble (Encrypt/Decrypt) | `src/scramble.py` | `scramble`, `descramble` | PN 序列扰码：`numpy.random.default_rng(seed)` 生成与数据等长的 0/1 伪随机序列，逐位 XOR；XOR 自逆，descramble 直接复用同一实现 |
| Channel Encode/Decode | `src/channel_coding.py` | `channel_encode`, `channel_decode` | 三倍重复码（rate=1/3），译码用多数判决 |
| Frame Build/Parse | `src/framing.py` | `build_frame`, `parse_frame` | 帧 = preamble(64bit 固定伪随机序列) + length(16bit) + payload + checksum(16bit, CRC32 截断) |
| QPSK Modulate/Demodulate | `src/modulation.py` | `qpsk_modulate`, `qpsk_demodulate` | Gray 映射：00->(1+j)/√2, 01->(-1+j)/√2, 11->(-1-j)/√2, 10->(1-j)/√2；解调用最近邻判决 |
| Channel (AWGN) | `src/channel.py` | `awgn` | 按 SNR(dB) 计算噪声功率，`numpy.random.default_rng(seed)` 生成复高斯噪声，可复现 |
| Synchronization | `src/synchronization.py` | `synchronize` | 滑动窗口归一化相关（matched filter），取相关峰值位置为帧起点 |
| Metrics/Plots | `src/metrics.py`, `src/plotting.py` | `bit_error_rate`, `text_match_rate`, `plot_constellation`, `plot_ber_curve`, `plot_sync_peak` | BER/FER/文本一致率计算；三张图：星座图、BER-SNR曲线、同步相关峰值图 |

## 3. 关键参数

- QPSK 星座点为单位平均功率（|s|²≈1），四个象限对应 Gray 编码的 4 种比特对，避免相邻符号误判造成 2 bit 错误。
- SNR 定义为接收符号平均功率 / 复高斯噪声平均功率（dB），不使用 Eb/N0，故不需要额外换算。
- 信道编码采用固定码率 1/3 的重复码，编码开销固定已知。
- length 字段位宽 16bit（最大 65535 bit ≈ 8KB 文本），对约 300 字中文（约 900~1200 字节，即 7200~9600 bit）留有充分余量。
- 帧结构中 checksum 覆盖的是 payload（即信道编码后的比特），用于检测信道编码前是否发生"整帧级别"的丢帧/错帧；同时在 `main.py` 中额外计算了一层端到端 CRC16（覆盖扰码后、信道编码前的比特），在信道解码(FEC纠正)之后再校验一次，作为 metrics.json 中 `checksum_pass` 字段的判定依据——因为原始帧内 checksum 是在 FEC 纠错之前算的，在低 SNR 下即使最终文本能被 FEC 纠回原样，帧内逐比特 checksum 也可能因残余噪声而不通过，这属于预期现象，在第 6 节失败分析中详细说明。
- QPSK 补零：若整帧比特数为奇数，`qpsk_modulate` 会在尾部补一个 0，接收端 `parse_frame` 内部根据 length 字段精确计算帧的真实长度，天然忽略这个多余的补零比特，不需要额外处理逻辑。
- 同步：`main.py` 默认在发送符号前人为插入 25 个随机噪声符号模拟前置偏移（呼应 PRD 示例 `sync_start_index=25`），`synchronize` 用归一化相关在 SNR>=12dB 下可精确检测到偏移起点（详见 MOCK_TEST_REPORT.md 与 REPORT.md 的实测结果）。

## 4. 设计决策与风险说明

PRD 第 3 节给出的固定链路顺序是 `Channel Encode -> Frame Build`，与 PRD 6.1 节"length 字段表示源编码后、扰码前的原始 payload bit 数"字面上的顺序略有出入（如果 Frame Build 包裹的是信道编码后的 payload，length 字段按通用帧协议语义应记录的是信道编码后的比特数，而不是编码前的原始比特数）。

本实现的处理方式：`build_frame` 作为通用帧组件，其 length 字段就是记录"传入它的 payload 参数的比特数"（本系统中即信道编码后比特数）；由于信道编码码率固定为 1/3 且双端已知，接收端可以用 `length / 3` 精确换算出编码前（即扰码后、源编码后）的原始比特数，因此仍然满足 PRD 6.1 "用 length 字段去除 padding 并恢复 UTF-8 文本" 的实际功能要求，只是换算关系是"除以固定码率"而不是"直接相等"。这一点已在这里明确说明换算关系，风险已通过公开测试和 mock 测试验证（详见 MOCK_TEST_REPORT.md）。

## 5. 模块边界与可扩展项

当前为 Level 2 完整系统：QPSK + AWGN + 帧同步 + 重复码信道编码 + PN 序列扰码 + BER-SNR 曲线 + 星座图 + 同步峰值图 + mock 测试与设计修订记录。

可选的 Level 3 提高项（未在本次提交中实现，留作后续扩展）：Rayleigh/Rician 衰落信道、ZF/MMSE 均衡、卷积码+Viterbi 译码替换重复码、16-QAM/BPSK 对比实验、OFDM/多址。

## 6. 结果与失败分析（QPSK 星座图 / BER / 文本一致率）

在 `--snr 12 --seed 2026 --mod qpsk --channel awgn` 标准命令下：`text_match_rate = 1.0`（`received.txt` 与 `Test.txt` 完全一致），`ber ≈ 5.4e-5`（信道编码后比特级的残余误码率，主要来自 AWGN 在个别重复码分组中翻转 1/3 比特，但多数判决仍能纠正，因此不影响最终文本恢复），`checksum_pass = true`，`sync_start_index = 25`（与人为插入的偏移完全一致，说明同步模块检测精确）。

当 SNR 降低（例如 0dB 附近）时，误码率会显著上升，重复码的纠错能力（每 3 位纠 1 位）会被突破，`text_match_rate` 会明显小于 1，`ber_curve.png` 中可以看到 BER 随 SNR 下降快速上升的曲线；这是本系统在低噪声容限下最先出问题的模块——信道编码的纠错能力不足以覆盖突发的高噪声，是典型的失败原因，详见 REPORT.md。
