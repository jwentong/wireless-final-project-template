# 无线通信技术期末项目 DESIGN.md

## 1. 需求理解

本项目实现一个端到端无线通信文件传输基带仿真系统。系统从 `Test.txt` 读取 UTF-8 文本，经过 Source Encode、Encrypt/Scramble、Channel Encode、Frame Build、QPSK Modulate、AWGN Channel、Synchronization、QPSK Demodulate、Channel Decode、Decrypt/Descramble、Source Decode，最终恢复为 `results/received.txt`，并输出 Metrics 和 Plots。

统一命令行入口为：

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

基础验收目标是在 SNR >= 12 dB、AWGN、固定 seed 条件下使 `received.txt` 与 `Test.txt` 完全一致，同时生成 `results/metrics.json` 和至少两张图表。

## 2. 总体链路

发送端流程：

1. Source Encode：将 UTF-8 文本按字节展开为 bitstream。
2. Scramble / Encrypt：使用固定 seed 生成 PN 序列，与 payload bit 逐位 XOR。
3. Channel Encode：使用 3 重复码进行前向纠错编码。
4. Frame Build：加入 preamble、length、payload_length、payload、CRC32。
5. QPSK Modulate：使用 PRD 要求的 Gray 编码 QPSK 星座映射。
6. Channel：通过 AWGN 信道，并加入 0 到 128 个 QPSK 符号的随机前置偏移。

接收端流程：

1. Synchronization：对已知 preamble 做相关检测，估计帧起点。
2. QPSK Demodulate：根据符号象限进行硬判决。
3. Frame Parse：解析长度字段、载荷和 CRC。
4. Channel Decode：对重复码分组多数判决。
5. Decrypt / Descramble：使用同一 seed 重新生成 PN 序列并 XOR。
6. Source Decode：按原始 payload bit 长度裁剪并恢复 UTF-8 文本。
7. Metrics / Plots：输出 BER、FER、text_match_rate、checksum_pass、sync_start_index，以及星座图、BER-SNR 曲线和同步峰值图。

## 3. 模块接口

| 模块 | 文件 | 主要接口 | 说明 |
|---|---|---|---|
| Source Encode / Source Decode | `src/source.py` | `source_encode`, `source_decode` | UTF-8 文本与 bitstream 互转 |
| Scramble / Encrypt | `src/scramble.py` | `scramble`, `descramble`, `encrypt`, `decrypt` | PN/XOR 可逆扰码 |
| Channel Encode / Channel Decode | `src/channel_coding.py` | `channel_encode`, `channel_decode` | 3 重复码，多数判决译码 |
| Frame Build / Parse | `src/framing.py` | `build_frame`, `parse_frame` | preamble、length、payload_length、CRC32 |
| QPSK Modulate / Demodulate | `src/modulation.py` | `qpsk_modulate`, `qpsk_demodulate` | Gray 编码 QPSK |
| Channel | `src/channel.py` | `awgn` | 复高斯白噪声信道 |
| Synchronization | `src/synchronization.py` | `synchronize`, `detect_frame_start` | 前导相关同步 |
| Pipeline / Metrics | `src/pipeline.py` | `run_transmission` | 端到端运行和图表输出 |

## 4. 关键算法设计

### 4.1 UTF-8 源编码

源编码以 UTF-8 字节为单位，将每个 byte 从高位到低位展开为 8 个 bit，因此 bitstream 长度一定是 8 的整数倍。接收端根据 `payload_bits` 裁剪多余 padding 后再按字节恢复文本。

### 4.2 扰码 / 加密

扰码模块用 `numpy.random.default_rng(seed)` 生成与 payload 等长的 0/1 PN 序列，再与 payload XOR。XOR 扰码满足可逆性：同一 seed 下再次 XOR 即可恢复原始 bitstream。

### 4.3 信道编码

基础系统采用 3 重复码。编码率为 1/3，传输效率下降，但在 AWGN 下可通过多数判决降低误码率。该方案容易解释、容易测试，适合本项目基础链路。

### 4.4 帧结构

帧格式如下：

```text
preamble | length | payload_length | payload | crc32
```

其中：

- `preamble`：128 bit，调制后为 64 个 QPSK 符号，用于同步。
- `length`：源编码后、扰码前的原始 payload bit 数。
- `payload_length`：实际进入帧的 channel-coded payload bit 数。
- `payload`：扰码和信道编码后的 bitstream。
- `crc32`：对帧载荷 bitstream 计算 CRC32。

`length`、`payload_length` 和 `crc32` 字段使用 5 重复保护，降低头部字段在噪声下出错导致无法解析的风险。

### 4.5 QPSK 星座映射

基础系统严格采用 PRD 指定的 Gray 编码 QPSK：

```text
00 -> ( 1 + j) / sqrt(2)
01 -> (-1 + j) / sqrt(2)
11 -> (-1 - j) / sqrt(2)
10 -> ( 1 - j) / sqrt(2)
```

归一化后平均符号功率约为 1。若进入 QPSK 的 bit 数为奇数，调制器在尾部补 0；接收端由 length 字段去除多余 bit。

### 4.6 AWGN 信道和 SNR

SNR 定义为接收端调制符号平均功率与复高斯噪声平均功率之比，单位 dB。噪声功率为：

```text
noise_power = signal_power / 10^(SNR_dB / 10)
```

复噪声的实部和虚部分别使用 `noise_power / 2` 的方差。

### 4.7 同步

接收端不假设已知帧起点。系统将已知 preamble 调制成 QPSK 符号，对接收序列做滑动相关，相关峰值最大的位置作为 `sync_start_index`。端到端仿真会加入 0 到 128 个符号的随机前置偏移，以验证同步模块。

## 5. Metrics 和图表

`results/metrics.json` 至少包含：

- `snr_db`
- `seed`
- `modulation`
- `channel`
- `payload_bits`
- `ber`
- `fer`
- `text_match_rate`
- `checksum_pass`
- `sync_start_index`

图表输出：

- `results/constellation.png`：AWGN 后的 QPSK 星座图。
- `results/ber_curve.png`：不同 SNR 下的 QPSK BER 参考曲线。
- `results/sync_peak.png`：同步相关峰值图。

## 6. 风险与处理

| 风险 | 影响 | 处理方式 |
|---|---|---|
| 低 SNR 下 payload bit 出错 | 文本乱码或 CRC 失败 | 使用 3 重复码，低 SNR 时仍输出 metrics 和失败标记 |
| length 字段被噪声破坏 | 无法正确裁剪 payload | length、payload_length、CRC 使用 5 重复保护 |
| 帧起点未知 | 解调比特整体错位 | 使用 preamble 相关峰值做 Synchronization |
| UTF-8 字节损坏 | 解码异常 | 高 SNR 下保证一致；低 SNR 下用替换解码避免程序崩溃 |
| 针对公开测试硬编码 | 隐藏测试失败和学术风险 | 所有处理均由通信链路生成，不直接复制文件 |

## 7. 结果解释

在 SNR = 12 dB 的 AWGN 条件下，QPSK 星座点集中在四个理想象限附近，硬判决误码率较低；重复码进一步修正少量 bit error，因此 text_match_rate 应达到 1.0。SNR 降低时，星座点扩散，BER 上升，最先可能出现同步峰值不明显、CRC 失败或 UTF-8 字节损坏等 failure / error。

