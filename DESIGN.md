# DESIGN.md

## 系统架构总览

本系统按固定链路实现文件传输：`Source Encode -> Encrypt/Scramble -> Channel Encode -> Frame Build -> QPSK Modulate -> Channel -> Synchronization -> QPSK Demodulate -> Channel Decode -> Decrypt/Descramble -> Source Decode -> Metrics`。

发送端读取 UTF-8 文本，转换为 bitstream；经过 PN XOR Scramble 后，用 3 重复码做 Channel Encode；Frame Build 将前导、长度、校验和 payload 组成一帧；然后执行 QPSK Modulate。信道部分添加随机前缀和 AWGN Channel。接收端先做 Synchronization，再 QPSK Demodulate、解析帧、Channel Decode、Descramble，最后 Source Decode 得到文本。

## 模块接口

| 模块 | 文件 | 主要接口 |
| --- | --- | --- |
| Source Encode / Source Decode | `src/source.py` | `source_encode`, `source_decode`, `text_to_bits`, `bits_to_text` |
| Encrypt / Scramble | `src/scramble.py`, `src/crypto.py` | `scramble`, `descramble`, `encrypt`, `decrypt` |
| Channel Encode / Channel Decode | `src/channel_coding.py` | `channel_encode`, `channel_decode` |
| Frame Build / Frame Parse | `src/framing.py` | `build_frame`, `parse_frame` |
| QPSK Modulate / Demodulate | `src/modulation.py` | `qpsk_modulate`, `qpsk_demodulate` |
| Channel | `src/channel.py` | `awgn` |
| Synchronization | `src/synchronization.py` | `synchronize` |
| Metrics / Plots / Pipeline | `src/metrics.py`, `src/plots.py`, `src/pipeline.py` | `bit_error_rate`, `run_system` |

## 算法选择

Source Encode 使用 UTF-8 字节编码，每个 byte 按高位到低位展开为 8 个 bit，因此 bitstream 长度总是 8 的整数倍。Source Decode 会截断到整字节并用 `errors="replace"` 安全解码，避免低 SNR 乱码导致程序崩溃。

Encrypt/Scramble 使用 `numpy.random.default_rng(seed)` 生成 PN bit 序列，对 payload 做 XOR。XOR 方案可逆，接收端使用同一个 seed 再 XOR 一次即可 Decrypt/Descramble。

Channel Encode 使用重复因子为 3 的重复码，编码率为 1/3。Channel Decode 对每 3 个 bit 做多数判决，并根据 `original_len` 裁剪到源 bit 长度。重复码实现简单、可解释，适合基础 AWGN 链路。

Frame Build 格式为：

```text
preamble_bits
+ length_bits
+ coded_length_bits
+ checksum_bits
+ payload_bits
```

`length` 表示 Source Encode 后、Scramble 前的原始 payload bit 数；`coded_length` 表示 Channel Encode 后实际传输的 payload bit 数；`checksum` 使用 CRC32 覆盖原始 payload bitstream。接收端根据 `coded_length` 去除 QPSK padding，并根据 `length` 恢复 UTF-8 文本。

QPSK 采用 PRD 指定的 Gray 映射，所有符号除以 `sqrt(2)` 以保证平均符号功率约为 1：

| bits | symbol |
| --- | --- |
| 00 | `(1+j)/sqrt(2)` |
| 01 | `(-1+j)/sqrt(2)` |
| 11 | `(-1-j)/sqrt(2)` |
| 10 | `(1-j)/sqrt(2)` |

QPSK Modulate 遇到奇数 bit 会在帧尾补 0。QPSK Demodulate 使用象限硬判决，padding 不在调制层删除，而由 Frame Parse 按 `coded_length` 处理。

AWGN Channel 中，`signal_power = mean(abs(symbols)**2)`，`noise_power = signal_power / 10**(snr_db / 10)`，复噪声为 `sqrt(noise_power/2) * (N(0,1) + jN(0,1))`。固定 seed 下输出可复现。

Synchronization 使用 preamble 的 QPSK 符号序列做滑动相关：

```text
metric[i] = abs(sum(received[i:i+L] * conj(preamble)))
```

相关峰最大的位置作为 `sync_start_index`。基础系统默认加入 0 到 128 个 QPSK 符号随机前缀，接收端不能假设天然知道帧起点。

Metrics 包括 `snr_db`、`seed`、`modulation`、`channel`、`payload_bits`、`ber`、`fer`、`text_match_rate`、`checksum_pass`、`sync_start_index`。BER 比较原始 source bits 和恢复后的 source bits；text_match_rate 完全一致时为 1.0，否则用字符级相似度估计。

## 关键参数

- preamble：`[0,0,0,1,1,1,1,0] * 8`，对应 32 个 QPSK 符号。
- repetition factor：3。
- CRC32 覆盖范围：原始 source payload bitstream。
- sync offset：0 到 128 个 QPSK 符号。
- 基础验收 SNR：12 dB AWGN。

## 风险与应对

- header bit error：12 dB 下概率较低；解析时会检查长度范围，异常时用可用 payload 长度兜底，避免崩溃。
- 低 SNR 下 checksum 失败：系统仍写出 `received.txt` 和 `metrics.json`，并在 `failure_reason` 中记录失败原因。
- UTF-8 乱码：Source Decode 使用安全解码，不抛异常。
- QPSK padding：通过 `coded_length` 精确裁剪，避免尾部补零进入 payload。
- Synchronization 误检：preamble 长度为 32 个符号，相关峰明显高于随机前缀；`sync_peak.png` 用于观察峰值。

## 结果分析

QPSK 星座图展示同步后接收符号在四个象限附近的聚类。SNR 较高时，点云靠近四个理想星座点；SNR 降低时，点云扩散，象限硬判决更容易出错。

BER 曲线展示 QPSK over AWGN 中误码率随 SNR 增加而下降。`text_match_rate` 对文本恢复更敏感，只要关键 UTF-8 字节错误就可能导致字符替换或文本差异。

典型失败原因包括 AWGN 噪声导致 QPSK 判决错误、同步相关峰误检、header 或 payload bit error 导致 CRC32 checksum failure。

## 代码对应关系

`main.py` 只负责 CLI 参数解析和摘要输出。`src/pipeline.py` 串联发送端、Channel、接收端、Metrics 和 Plots。各通信算法分别放在 `src/source.py`、`src/scramble.py`、`src/channel_coding.py`、`src/framing.py`、`src/modulation.py`、`src/channel.py`、`src/synchronization.py` 中，便于公开测试和隐藏测试单独导入。

## Level 3 Rayleigh Extension

本实现额外支持 `--channel rayleigh`。该模式使用一个复高斯块衰落系数模拟 flat Rayleigh Channel，再叠加 AWGN。接收端利用已知 preamble 做一拍信道估计：`h_hat = sum(rx_preamble * conj(preamble)) / sum(abs(preamble)^2)`，随后对同步后的符号执行 `rx / h_hat` 均衡，再进入 QPSK Demodulate。默认 `--channel awgn` 行为保持不变。

该提高模块用于展示衰落信道和简单 coherent equalization 的处理方式。metrics 中额外记录 `rayleigh_h_abs` 和 `equalizer_h_abs`，便于比较真实衰落幅度和估计幅度。Rayleigh 下如果 SNR 较低或估计受噪声影响，可能出现 QPSK 判决错误、BER 上升和 checksum failure。