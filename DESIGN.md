# 系统设计文档

## 系统架构

系统实现了端到端无线通信基带仿真链路：

Source Encode（信源编码）→ Encrypt/Scramble（加扰）→ Channel Encode（信道编码，可选 Hamming/卷积码）→ Frame Build（帧构建，可选 XOR8/CRC-32 校验）→ Modulate（调制，可选 BPSK / QPSK / 16-QAM）→ Channel（AWGN / Rayleigh 信道）→ Synchronization（同步）→ Demodulate（解调）→ Channel Decode（信道解码）→ Descramble（解扰）→ Source Decode（信源解码）→ Metrics（指标输出）

## 模块接口

### Source Encode / Source Decode — 信源编码 / 信源解码 (src/source.py)
- `source_encode(text: str) -> list[int]`：将 UTF-8 文本转换为比特流
- `source_decode(bits: list[int]) -> str`：从比特流恢复 UTF-8 文本

### Encrypt / Scramble — 加扰 / 解扰 (src/scramble.py)
- `scramble(bits: list[int], seed: int) -> list[int]`：与 PN 序列进行 XOR 运算
- `descramble(bits: list[int], seed: int) -> list[int]`：对称 XOR 运算
- `no_scramble / no_descramble`：直通模式（不加扰）
- 通过 `--scramble pn|none` 命令行选择

### Channel Encode / Decode — 信道编码 / 解码 (src/fec.py)
- `hamming_encode / hamming_decode`：汉明码 (7,4) 分组编码，每 7 比特纠 1 位
- `conv_encode(bits, K=7) -> list[int]`：卷积编码器，Rate 1/2，生成多项式 (133, 171)_8
- `viterbi_decode(bits, K=7) -> list[int]`：硬判决 Viterbi 译码器，64 状态
- 通过 `--fec hamming|convolutional` 命令行选择

### Frame Build / Parse — 帧构建 / 解析 (src/framing.py)
- `build_frame(payload_bits, checksum_bits=None) -> list[int]`：前导码(32b) + 长度(16b) + 载荷 + 校验(8b/32b)
- `parse_frame(frame_bits, checksum_len=8) -> tuple`：提取载荷和元数据（校验码、长度）
- 校验方式通过 `--checksum xor8|crc32` 命令行选择

### Modulate / Demodulate — 调制 / 解调 (src/modulation.py)

**BPSK**（1 比特/符号）：
- `bpsk_modulate(bits: list[int]) -> list[complex]`：0→+1, 1→-1
- `bpsk_demodulate(symbols: list[complex]) -> list[int]`：硬判决（实部符号）

**QPSK**（2 比特/符号）：
- `qpsk_modulate(bits: list[int]) -> list[complex]`：Gray 编码 QPSK 映射
- `qpsk_demodulate(symbols: list[complex]) -> list[int]`：硬判决解映射

**16-QAM**（4 比特/符号）：
- `qam16_modulate(bits: list[int]) -> list[complex]`：Gray 编码矩形 16-QAM，`1/sqrt(10)` 功率归一化
- `qam16_demodulate(symbols: list[complex]) -> list[int]`：最近邻硬判决解映射

### Channel — 信道模型 (src/channel.py)
- `awgn(symbols, snr_db, seed) -> list[complex]`：在指定 SNR 下添加复高斯噪声
- `rayleigh_fading(symbols, snr_db, seed) -> list[complex]`：平坦 Rayleigh 衰落 + AWGN + ZF 均衡
- 通过 `--channel awgn|rayleigh` 命令行选择

### Synchronization — 同步 (src/synchronization.py)
- `detect_frame_start(symbols, preamble=None) -> int`：基于互相关的前导码检测

## 算法选择

- **调制方式**：BPSK（1 比特/符号，抗干扰最强）、QPSK（2 比特/符号，平衡性能与速率）、16-QAM（4 比特/符号，最高频谱效率），均采用 Gray 编码；通过 `--mod` 选择
- **信道编码**：
  - 汉明码 (7,4)：每 7 比特块可纠正 1 位错误（默认）
  - 卷积码：Rate 1/2，K=7，生成多项式 (133, 171)_8，Viterbi 硬判决译码，可在低 SNR 和 Rayleigh 信道下显著提升性能
- **信道模型**：
  - AWGN：加性高斯白噪声（默认）
  - Rayleigh 平坦衰落：复高斯衰落系数 + AWGN + ZF 均衡，模拟多径衰落环境
- **同步方法**：滑动互相关，与已知前导码序列进行匹配
- **校验方式**：
  - XOR-8：8 位 XOR 校验和（默认）
  - CRC-32：32 位循环冗余校验（IEEE 802.3），提供更强的错误检测能力

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 前导码 | 32 位 / 16 个 QPSK 符号 | 帧同步序列 |
| 长度字段 | 16 位 | 载荷比特数 |
| 校验和 | 8 位 (XOR-8) / 32 位 (CRC-32) | 载荷校验，可通过 `--checksum` 选择 |
| 信道编码 | 汉明 (7,4) / 卷积 (Rate 1/2, K=7) | 可通过 `--fec` 选择 |
| 加扰方式 | PN 序列 XOR / 直通 | 可通过 `--scramble` 选择 |
| 调制方式 | BPSK / QPSK / 16-QAM Gray | 每符号 1 (BPSK) / 2 (QPSK) / 4 (16-QAM) 比特，可通过 `--mod` 选择 |
| 信道模型 | AWGN / Rayleigh 平坦衰落 | 可通过 `--channel` 选择 |
| SNR 定义 | Es/N0 (dB) | 符号能量与噪声功率比 |
| 随机种子 | 用户指定 | 确保噪声和加扰可复现 |

## Metrics — 指标输出

系统运行后生成 `results/metrics.json`，包含 SNR、BER、FER、文本匹配率、校验通过状态、同步起始索引以及所选 FEC/校验/加扰/信道配置等指标。同时生成星座图、BER 曲线和同步峰值图用于可视化分析。

## CLI 参数

| 参数 | 可选值 | 默认 | 说明 |
|------|--------|------|------|
| `--input` | 文件路径 | `Test.txt` | 输入文本文件 |
| `--output` | 文件路径 | `results/received.txt` | 输出恢复文本 |
| `--snr` | 浮点数 | 12.0 | SNR (dB) |
| `--seed` | 整数 | 2026 | 随机种子 |
| `--mod` | `bpsk`, `qpsk`, `16qam` | `qpsk` | 调制方式 |
| `--channel` | `awgn`, `rayleigh` | `awgn` | 信道模型 |
| `--fec` | `hamming`, `convolutional` | `hamming` | 信道编码 |
| `--checksum` | `xor8`, `crc32` | `xor8` | 帧校验算法 |
| `--scramble` | `pn`, `none` | `pn` | 加扰方式 |

## 预期风险

- **低 SNR**：SNR < 6 dB 时 BER 显著上升，汉明码纠错能力有限；卷积码可在 SNR ≥ 4 dB 时保持无差错
- **同步失败**：极低 SNR 或 Rayleigh 深衰落时前导码互相关可能产生假峰
- **校验错误**：8 位 XOR 无法检测所有多位错误模式；CRC-32 提供更强的检测能力
- **Rayleigh 信道**：深衰落会导致突发错误，卷积码比汉明码具有更强的抗衰落能力
