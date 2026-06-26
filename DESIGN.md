# 无线通信基带仿真系统 设计文档 (DESIGN.md)

## 一、系统概述

### 1.1 项目目标

本项目实现一个完整的无线通信基带仿真系统。系统将 UTF-8 编码的中文文本文件 `Test.txt` 作为输入，经过发送端基带处理、无线信道传输和接收端基带处理后，在 `results/received.txt` 中恢复原始文本，并生成性能指标与可视化图表。

### 1.2 设计原则

- **管道化架构**：每个处理模块独立封装，通过比特流或符号流连接，便于测试和替换。
- **可复现性**：所有随机过程（扰码、AWGN、同步测试等）接受 `seed` 参数，固定 seed 给出确定结果。
- **模块化测试**：每个模块单独可测，输入输出为纯 Python 基础类型（`list[int]` 或 `list[complex]`）。
- **Level 分级实现**：Level 1/2 覆盖核心流水线（QPSK + AWGN 可完整恢复文本），Level 3 增加 BPSK/16-QAM 对比调制和 Rayleigh 衰落信道。

### 1.3 技术栈

- 语言：Python 3.10+
- 数值计算：NumPy, SciPy
- 可视化：Matplotlib
- 测试：pytest

---

## 二、固定处理流水线

整个系统的数据流向固定如下（不可更改顺序）：

```
Test.txt → Source Encode → Encrypt / Scramble → Channel Encode → Frame Build
         → QPSK Modulate → Channel (AWGN / Rayleigh) → Synchronization
         → QPSK Demodulate → Channel Decode → Decrypt / Descramble
         → Source Decode → Received.txt → Metrics / Plots
```

各模块职责总览：

| 序号 | 模块名称 | 方向 | 功能 |
|------|----------|------|------|
| 1 | Source Encode | 发送端 | 将 UTF-8 文本转为比特流 |
| 2 | Encrypt / Scramble | 发送端 | 使用 PN 序列对比特流扰码 |
| 3 | Channel Encode | 发送端 | 卷积编码增加冗余，提升抗噪能力 |
| 4 | Frame Build | 发送端 | 组装帧结构，插入 preamble、长度字段和校验和 |
| 5 | QPSK Modulate | 发送端 | 将比特映射为 QPSK 复基带符号 |
| 6 | Channel | 信道 | AWGN 加噪或 Rayleigh 衰落 |
| 7 | Synchronization | 接收端 | 通过 preamble 互相关检测帧起始位置 |
| 8 | QPSK Demodulate | 接收端 | 从复符号判决恢复比特（硬判决） |
| 9 | Channel Decode | 接收端 | Viterbi 译码纠正传输错误 |
| 10 | Decrypt / Descramble | 接收端 | 解扰恢复原始比特顺序 |
| 11 | Source Decode | 接收端 | 将比特流还原为 UTF-8 文本 |
| 12 | Metrics / Plots | 评估 | 计算 BER、FER、text_match_rate 并生成可视化图表 |

---

## 三、模块详细设计

### 3.1 Source Encode / Decode（源编码）

**文件**：`src/source.py`

**发送端接口**：

```python
def text_to_bits(text: str) -> list[int]:
    """将 UTF-8 字符串转换为比特列表 (big-endian)"""
    ...
```

- 将输入字符串按 UTF-8 编码为字节序列。
- 每个字节展开为 8 个比特（MSB 在前），串联成 `list[int]`。
- 输出比特数为 8 的整数倍。

**接收端接口**：

```python
def bits_to_text(bits: list[int]) -> str:
    """将比特列表还原为 UTF-8 字符串"""
    ...
```

- 将比特流按 8 个一组组成字节（MSB 在前）。
- 合并字节序列，以 UTF-8 解码为字符串。
- 不对输入比特数量做整除 8 以外的约束。

**可逆性要求**：对任意合法 UTF-8 文本，`bits_to_text(text_to_bits(text)) == text` 恒成立。

---

### 3.2 Encrypt / Scramble（扰码 / 加密）

**文件**：`src/crypto.py`

**发送端接口**：

```python
def scramble(bits: list[int], seed: int) -> list[int]:
    """使用 PN 序列对输入比特进行扰码"""
    ...
```

**接收端接口**：

```python
def descramble(bits: list[int], seed: int) -> list[int]:
    """使用相同 PN 序列解扰"""
    ...
```

**设计细节**：

- 使用线性反馈移位寄存器 (LFSR) 生成伪随机 (PN) 序列。
- PN 序列长度与输入比特数相等，每位比特与 PN 对应位做 XOR 得到输出。
- 相同的 `seed` 必须生成相同的 PN 序列，保证可复现。
- 解扰使用相同的 PN 序列再做 XOR，可逆恢复原始比特。
- 固定 seed 下，`descramble(scramble(bits, seed), seed) == bits` 恒成立。

**种子设计**：seed 作为 LFSR 初始状态。推荐使用 16 位或 31 位 LFSR，多项式可选用 CRC-16 多项式 `x^16 + x^15 + x^2 + 1` 或其反向。

---

### 3.3 Channel Encode / Decode（信道编码）

**文件**：`src/channel_coding.py`

**发送端接口**：

```python
def channel_encode(bits: list[int]) -> list[int]:
    """卷积编码 (rate 1/2, constraint length 7)"""
    ...
```

**接收端接口**：

```python
def channel_decode(bits: list[int]) -> list[int]:
    """Viterbi 译码"""
    ...
```

**设计细节**：

- **编码方式**：卷积码，码率 1/2，约束长度 7（对应 IEEE 802.11 标准生成多项式）。
- **生成多项式**：`g0 = 0o171` (1111001 in octal, i.e. `1 + x + x^2 + x^3 + x^6`)，`g1 = 0o133` (1011011 in octal, i.e. `1 + x^2 + x^3 + x^5 + x^6`)。
- 每输入 1 个比特产生 2 个编码输出比特（g0 在前，g1 在后）。
- 编码器尾部补零 (tail-biting 或 zero-termination)：在比特流末尾添加 6 个零比特将编码器带回全零状态。
- **译码方式**：Viterbi 硬判决译码。汉明距离为分支度量，回溯深度建议取约束长度的 5-10 倍（约 35-70 步）。
- 无噪声条件下，`channel_decode(channel_encode(bits)) == bits` 恒成立（恢复前去掉尾部补零）。

**Level 3 扩展**：可支持软判决译码（将接收符号的欧氏距离作为分支度量），在低 SNR 下性能优于硬判决。

---

### 3.4 Frame Build / Parse（帧封装与解析）

**文件**：`src/framing.py`

**发送端接口**：

```python
def build_frame(payload_bits: list[int]) -> list[int]:
    """将原始 payload 比特封装为完整帧比特序列"""
    ...
```

**接收端接口**：

```python
def parse_frame(frame_bits: list[int]) -> dict:
    """
    从接收到的帧比特序列中解析各字段。
    返回 dict: {
        "preamble": ...,
        "length": int,      # 原始 payload 比特数（扰码前）
        "payload": list[int],
        "checksum": int,
        "checksum_pass": bool
    }
    """
    ...
```

**帧结构定义**：

```
+------------+--------+---------+----------+
|  Preamble  | Length | Payload | Checksum |
+------------+--------+---------+----------+
  32 symbols   16 bit   N bit     16 bit
   (64 bit)            (变长)     (CRC-16)
```

各字段说明：

**Preamble（前导序列）**：
- 长度：32 个 QPSK 符号（即 64 个编码前比特或 32 个编码后符号位）。在帧结构层面，preamble 存储的是 32 个 QPSK 符号的比特表示（每符号 2 比特，共 64 比特），对应交替的星座点：
  `[(1+j)/√2, (-1+j)/√2, (-1-j)/√2, (1-j)/√2]` 重复 8 次。
- 由于 QPSK Gray 映射下 00, 01, 11, 10 按象限轮流排列，preamble 比特序列可以是 `[0,0,0,1,1,1,1,0]` 重复 8 次（64 比特）。
- 功能：用于接收端 Synchronization 做互相关检测帧起点。交替的星座点具有良好自相关特性（尖锐的单峰）。

**Length 字段**：
- 长度：16 比特，无符号整数，大端序。
- 内容：**原始 payload 比特数**（即扰码前、信道编码前的源编码输出比特数）。用于在接收端去除 QPSK padding 比特，精确恢复原始文本。
- 取值范围由输入文本长度决定，16 位可表示 0-65535 比特（约 8 KB 文本），满足需求。

**Payload**：
- 内容：经过 Source Encode -> Scramble -> Channel Encode 后的完整比特序列。
- 由于 QPSK 调制需要偶数个比特，若 payload 总比特数为奇数，在末尾补 1 个 `0`（padding）。接收端根据 Length 字段丢弃超出原始 payload 长度的比特。
- 注意：Length 记录的是原始 payload 比特数（源编码输出、扰码前），不是 Channel Encode 后的比特数。因为 Channel Encode 的码率固定为 1/2，可以反推。但实际上 Length 表示的是 Source Encode 后的比特数，接收端在完成 Channel Decode 和 Descramble 后，使用此值精确截取。

**Checksum（校验和）**：
- 长度：16 比特。
- 算法：**CRC-16**，多项式 `x^16 + x^15 + x^2 + 1` (CRC-16-IBM)。
- 覆盖范围：原始 payload **字节**（Source Encode 输出的字节序列，即 text_to_bits 的中间结果字节），而非扰码后的比特。
- 计算方式：将原始文本的 UTF-8 字节序列输入 CRC-16 计算器，得到 16 位校验值。
- 接收端重新计算 CRC-16 并与收到的校验值比对，若相等则 `checksum_pass = True`，否则为 `False`。

---

### 3.5 QPSK Modulate / Demodulate（QPSK 调制解调）

**文件**：`src/modulation.py`

**发送端接口**：

```python
def qpsk_modulate(bits: list[int]) -> list[complex]:
    """QPSK 调制，使用 Gray 编码"""
    ...

def bpsk_modulate(bits: list[int]) -> list[complex]:
    """BPSK 调制 (Level 3)"""
    ...

def qam16_modulate(bits: list[int]) -> list[complex]:
    """16-QAM 调制 (Level 3)"""
    ...
```

**接收端接口**：

```python
def qpsk_demodulate(symbols: list[complex]) -> list[int]:
    """QPSK 硬判决解调，使用 Gray 解码"""
    ...

def bpsk_demodulate(symbols: list[complex]) -> list[int]:
    """BPSK 硬判决解调 (Level 3)"""
    ...

def qam16_demodulate(symbols: list[complex]) -> list[int]:
    """16-QAM 硬判决解调 (Level 3)"""
    ...
```

**QPSK 星座映射（Gray 编码）**：

```
比特对 (b1, b0) → 复符号
----------------------------------------------
00 →  (1 + j) / √2     (第一象限, 角度 π/4)
01 → (-1 + j) / √2     (第二象限, 角度 3π/4)
11 → (-1 - j) / √2     (第三象限, 角度 5π/4)
10 →  (1 - j) / √2     (第四象限, 角度 7π/4)
```

每个符号携带 2 比特，`b1` 为高位比特。相邻象限的比特对仅相差 1 位（Gray 编码原则），使符号判决错误时大概率只产生 1 比特误码。

归一化因子 `1/√2` 使每个符号的平均功率为 1（单位功率星座）。

**QPSK 解调（硬判决）**：

- 对接收符号按 I/Q 坐标象限做硬判决：
  - I >= 0, Q >= 0 -> 00
  - I <  0, Q >= 0 -> 01
  - I <  0, Q <  0 -> 11
  - I >= 0, Q <  0 -> 10

**Padding 处理**：
- `qpsk_modulate` 要求输入比特数为偶数。若输入为奇数，模块本身不处理 padding，由调用方（Frame Build）保证。
- 接收端通过 Frame Parse 获得 Length 字段（原始 payload 比特数），在 QPSK Demodulate 后、Channel Decode 和 Descramble 完成后，截取前 `length` 个比特，丢弃 padding。

**Level 3 扩展**：
- **BPSK 调制**: 比特 0 → +1, 比特 1 → -1。每符号 1 比特，无需 padding。
- **16-QAM 调制**: 每符号 4 比特，使用 Gray 编码的方形 16-QAM 星座。归一化平均功率为 1。

---

### 3.6 Channel（信道模型）

**文件**：`src/channel.py`

**发送端接口**：

```python
def awgn(symbols: list[complex], snr_db: float, seed: int) -> list[complex]:
    """加性高斯白噪声信道"""
    ...

def rayleigh(symbols: list[complex], snr_db: float, seed: int) -> list[complex]:
    """频率平坦 Rayleigh 衰落信道 (Level 3)"""
    ...
```

**AWGN 信道设计**：

- 输入复基带符号序列，加入复高斯噪声。
- **SNR 定义**：dB 单位，`SNR_dB = 10 * log10(P_signal / P_noise)`，其中 `P_signal` 是输入符号的平均功率，`P_noise` 是噪声的平均功率。
- 噪声生成：对每个符号生成独立的复高斯随机变量 `n ~ CN(0, σ^2)`，其中 `σ^2 = P_signal / (10^(SNR_dB / 10))`。
  - 等价于：实部和虚部分别独立服从 `N(0, σ^2 / 2)`。
- 可复现性：使用 NumPy 随机数生成器，以 `seed` 初始化 `np.random.default_rng(seed)`，每次调用时传入新 seed（如 `seed + symbol_index`）保证独立性。

**Rayleigh 信道设计 (Level 3)**：

- 频率平坦 Rayleigh 衰落：对每个符号乘以独立的复高斯随机变量 `h ~ CN(0, 1)`（即实部和虚部分别独立 `N(0, 0.5)`），再加 AWGN。
- 输出：`y = h * x + n`，其中 `h` 为衰落系数，`x` 为发送符号，`n` 为 AWGN。
- SNR 定义不变（基于平均接收功率）。

---

### 3.7 Synchronization（同步）

**文件**：`src/synchronization.py`

**接收端接口**：

```python
def synchronize(
    received_symbols: list[complex],
    preamble: list[complex]
) -> dict:
    """
    通过互相关检测帧起始位置。
    返回 dict: {
        "start_index": int,       # 检测到的 preamble 起始符号索引
        "correlation_peak": float, # 互相关峰值
        "correlation_sequence": list[float]  # 完整的互相关序列（用于绘制 sync_peak.png）
    }
    ...
```

**同步算法设计**：

- **互相关检测**：将接收符号序列与已知 preamble 符号序列做滑动互相关：
  ```
  corr[k] = |sum_{i=0}^{L-1} received[k+i] * conj(preamble[i])|
  ```
  其中 L 为 preamble 长度（32 符号）。

- **峰值检测**：取 `argmax(corr[k])` 作为 preamble 起始符号索引 `start_index`。
- **处理范围**：支持 0 到 128 个符号的前置偏移（即发送帧前可能插入噪声符号）。
- **精度要求**：在 SNR >= 12 dB 的 AWGN 信道下，检测误差不超过 1 个符号。

**Preamble 设计对同步性能的影响**：
- 交替的 QPSK 星座点具有良好的自相关特性，互相关峰值尖锐。
- Preamble 长度 32 符号在 12 dB SNR 下提供足够的处理增益（约 15 dB）。

---

## 四、性能指标与可视化

### 4.1 metrics.json

**文件**：`results/metrics.json`

**必需字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `snr_db` | float | 仿真使用的 SNR (dB) |
| `seed` | int | 随机种子 |
| `modulation` | str | 调制方式 (qpsk / bpsk / qam16) |
| `channel` | str | 信道类型 (awgn / rayleigh) |
| `payload_bits` | int | 原始 payload 比特数（Source Encode 输出） |
| `ber` | float | 比特误码率 (bit error rate) |
| `fer` | float | 帧错误率 (frame error rate)，当前只有 1 帧，取值 0.0 或 1.0 |
| `text_match_rate` | float | 文本匹配率（逐字符比对，完全匹配为 1.0） |
| `checksum_pass` | bool | 帧校验和是否通过 |
| `sync_start_index` | int | Synchronization 检测到的帧起始符号索引 |

**BER 计算方式**：
```
ber = (原始 payload 比特中错误的比特数) / (原始 payload 总比特数)
```
比较对象为 Source Encode 输出（扰码前、Channel Encode 前的原始比特）与接收端 Channel Decode 和 Descramble 后截取的比特序列。

**text_match_rate 计算方式**：
```
text_match_rate = 1.0 if received_text == original_text else (匹配字符数 / 总字符数)
```

### 4.2 可视化图表

**constellation.png**（星座图）：
- 绘制接收端收到的 QPSK 符号在 I/Q 复平面上的散点图。
- 叠加理想星座点（参考符号，用红色十字或星号标记）。
- 用于直观观察 AWGN 对星座点散布的影响。

**ber_curve.png**（BER 曲线）：
- 横轴：SNR (dB)，范围如 0-20 dB。
- 纵轴：BER（对数坐标）。
- 对同一输入文本，遍历多个 SNR 值运行完整流水线，绘制 BER vs SNR 曲线。
- Level 3：在同一图上叠加 BPSK、QPSK、16-QAM 三条曲线以对比不同调制方式的 BER 性能。

**sync_peak.png**（同步相关峰）：
- 横轴：符号偏移索引 k。
- 纵轴：互相关幅度 corr[k]。
- 绘制完整的互相关序列曲线，标注检测到的峰值位置。
- 用于验证 preamble 检测是否正确，以及相关峰是否尖锐。

---

## 五、命令行接口 (CLI)

### 5.1 统一运行命令

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

### 5.2 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--input` | str | 是 | - | 输入文本文件路径 (UTF-8) |
| `--output` | str | 是 | - | 输出恢复文本文件路径 |
| `--snr` | float | 否 | 12 | 信噪比 (dB) |
| `--seed` | int | 否 | 2026 | 随机种子 |
| `--mod` | str | 否 | qpsk | 调制方式: qpsk / bpsk / qam16 |
| `--channel` | str | 否 | awgn | 信道类型: awgn / rayleigh |

### 5.3 main.py 架构

```python
# main.py 伪代码结构

def main():
    args = parse_args()
    # 1. Source Encode
    original_bits = text_to_bits(read_text(args.input))
    # 2. Scramble
    scrambled = scramble(original_bits, args.seed)
    # 3. Channel Encode
    coded = channel_encode(scrambled)
    # 4. Frame Build (传入 original_bits 用于构建 length 和 checksum)
    frame_bits = build_frame(coded, original_bit_count=len(original_bits), original_bytes=...)
    # 5. Modulate
    symbols = modulate(frame_bits, args.mod)
    # 6. Channel
    received_symbols = channel(symbols, args.snr, args.seed, args.channel)
    # 7. Synchronization
    sync_result = synchronize(received_symbols, preamble)
    # 8. Demodulate
    received_bits = demodulate(received_symbols[sync_result["start_index"]:], args.mod)
    # 9. Frame Parse
    frame = parse_frame(received_bits)
    # 10. Channel Decode
    decoded = channel_decode(frame["payload"])
    # 11. Descramble
    descrambled = descramble(decoded[:frame["length"]], args.seed)
    # 12. Source Decode
    text = bits_to_text(descrambled)
    # 13. Metrics & Plots
    # 14. Write output
    write_text(args.output, text)
    write_json("results/metrics.json", metrics)
    save_plots(...)
```

### 5.4 非交互要求

程序必须完全非交互运行，不调用 `input()`，不显示任何 "请输入" 或 "Press Enter" 等提示。

---

## 六、数据处理流程详解

### 6.1 完整数据流示例

假设输入文本 "AB"（2 字符，UTF-8 编码为 2 字节 `0x41 0x42`）：

```
step 1 - Source Encode:
    输入: "AB"
    字节: [0x41, 0x42]
    比特: [0,1,0,0,0,0,0,1, 0,1,0,0,0,0,1,0]  (16 bits)
    length = 16

step 2 - Scramble (seed=2026):
    输入: 16 bits
    PN序列 (LFSR生成): 例如 [1,0,1,1,0,0,1,0, ...]  (16 bits)
    XOR输出: 16 bits scrambled

step 3 - Channel Encode:
    输入: 16 bits
    编码后: 32 bits (rate 1/2) + 12 tail bits (6 zeros * 2) = 44 bits

step 4 - Frame Build:
    length 字段: [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0]  (16 = 0x0010, 大端)
    checksum: CRC-16 of original bytes [0x41, 0x42] => 16 bits
    preamble: 64 bits (32 QPSK symbols' bit representation)
    payload: 44 bits (channel encoded)
    总帧比特: 64 + 16 + 44 + 16 = 140 bits
    padding: 140 为偶数，无需 padding

step 5 - QPSK Modulate:
    140 bits -> 70 QPSK symbols

step 6 - AWGN Channel:
    70 symbols + noise -> 70 received symbols

step 7 - Synchronization:
    互相关检测，找到 preamble 起始位置

step 8 - QPSK Demodulate:
    70 symbols -> 140 bits (含错误)

step 9 - Frame Parse:
    提取 length=16, payload=44 bits, checksum

step 10 - Channel Decode (Viterbi):
    44 bits -> 22 bits (去掉 tail bits) -> 截取前 16 bits

step 11 - Descramble:
    16 bits -> descramble -> 16 bits

step 12 - Source Decode:
    16 bits -> [0x41, 0x42] -> "AB"

接收端结果：若 SNR 足够高（如 12 dB），received.txt = "AB", text_match_rate = 1.0
```

### 6.2 关键参数传递说明

**Length 字段的精确含义**：
`length = len(text_to_bits(input_text))`，即 Source Encode 后、Scramble 前的比特数。

接收端在 Channel Decode 和 Descramble 完成后使用 `length` 截取精确的比特数，丢弃尾部的 padding 和 tail bits 残留。

**Checksum 的覆盖范围**：
`checksum = CRC16(text.encode('utf-8'))`，即原始 UTF-8 字节序列，而不是任何变换后的比特。

这确保了接收端可以检测到不可纠正的帧错误。接收端重新计算 CRC-16 并与帧中存储的值比较。

**Scramble seed 的传递**：
发送端和接收端使用相同的 seed 值（由 CLI 参数传入）。LFSR 初始状态完全由 seed 决定，两端生成的 PN 序列完全一致。

---

## 七、信号格式与功率规范

### 7.1 符号平均功率

- QPSK 调制符号平均功率 = 1（归一化因子 `1/√2`）。
- SNR 计算基于符号平均功率：`SNR_dB = 10 * log10(1 / σ^2)`，其中 `σ^2` 为复噪声方差。
- 噪声每个维度（I/Q）方差为 `σ^2 / 2`。

### 7.2 Preamble 设计

32 个已知 QPSK 符号，取交替象限的星座点：

```
符号序列（复数值）：[(1+j)/√2, (-1+j)/√2, (-1-j)/√2, (1-j)/√2] 重复 8 次
```

等价比特序列（Gray 编码）：`[0,0,0,1,1,1,1,0]` 重复 8 次 = 64 比特。

选择此序列的原因：
1. 交替的星座点在不同象限之间跳变，互相关旁瓣低。
2. 32 个符号长度在 12 dB SNR 下提供约 15 dB 相关处理增益，足以可靠检测。

---

## 八、Level 分级设计

### 8.1 Level 1-2（核心流水线）

完成 QPSK + AWGN 信道的完整端到端流水线，在 SNR 12 dB 下 `text_match_rate = 1.0`，所有公开测试通过。

包含模块：Source、Scramble、Channel Encode (卷积码+Viterbi)、Frame、QPSK、AWGN、Synchronization。

### 8.2 Level 3（扩展功能）

- **BPSK 调制**：`src/modulation.py` 中增加 `bpsk_modulate` 和 `bpsk_demodulate`。CLI 支持 `--mod bpsk`。在 `ber_curve.png` 中对比 BPSK、QPSK、16-QAM。
- **16-QAM 调制**：`src/modulation.py` 中增加 `qam16_modulate` 和 `qam16_demodulate`。方形星座，Gray 编码。
- **Rayleigh 衰落信道**：`src/channel.py` 中增加 `rayleigh` 函数。CLI 支持 `--channel rayleigh`。对比 AWGN 与 Rayleigh 下的 BER 性能。

---

## 九、模块接口规范汇总

| 模块文件 | 导出函数 | 输入类型 | 输出类型 |
|----------|----------|----------|----------|
| `src/source.py` | `text_to_bits` | `str` | `list[int]` |
| `src/source.py` | `bits_to_text` | `list[int]` | `str` |
| `src/crypto.py` | `scramble` | `list[int], seed: int` | `list[int]` |
| `src/crypto.py` | `descramble` | `list[int], seed: int` | `list[int]` |
| `src/channel_coding.py` | `channel_encode` | `list[int]` | `list[int]` |
| `src/channel_coding.py` | `channel_decode` | `list[int]` | `list[int]` |
| `src/framing.py` | `build_frame` | `list[int]` | `list[int]` 或 `dict` |
| `src/framing.py` | `parse_frame` | `list[int]` | `dict` |
| `src/modulation.py` | `qpsk_modulate` | `list[int]` | `list[complex]` |
| `src/modulation.py` | `qpsk_demodulate` | `list[complex]` | `list[int]` |
| `src/modulation.py` | `bpsk_modulate` | `list[int]` | `list[complex]` |
| `src/modulation.py` | `bpsk_demodulate` | `list[complex]` | `list[int]` |
| `src/modulation.py` | `qam16_modulate` | `list[int]` | `list[complex]` |
| `src/modulation.py` | `qam16_demodulate` | `list[complex]` | `list[int]` |
| `src/channel.py` | `awgn` | `list[complex], snr_db: float, seed: int` | `list[complex]` |
| `src/channel.py` | `rayleigh` | `list[complex], snr_db: float, seed: int` | `list[complex]` |
| `src/synchronization.py` | `synchronize` | `list[complex], preamble: list[complex]` | `dict` |

---

## 十、目录结构

```
wireless-final-project-template/
├── main.py                  # CLI 入口，流水线编排
├── Test.txt                 # 输入文本（UTF-8 中文）
├── requirements.txt         # 依赖: numpy, scipy, matplotlib, pytest
├── DESIGN.md                # 本文档
├── TEST_PLAN.md             # 测试计划
├── MOCK_TEST_REPORT.md      # Mock 测试报告
├── AI_LOG.md                # AI 辅助记录
├── src/
│   ├── __init__.py
│   ├── source.py            # Source Encode / Decode
│   ├── crypto.py            # Scramble / Descramble
│   ├── channel_coding.py    # Channel Encode / Decode (卷积码 + Viterbi)
│   ├── framing.py           # Frame Build / Parse
│   ├── modulation.py        # QPSK / BPSK / 16-QAM Modulate / Demodulate
│   ├── channel.py           # AWGN / Rayleigh Channel
│   └── synchronization.py   # Preamble 互相关同步
├── tests/
│   └── __init__.py
├── results/                 # 运行时生成
│   ├── received.txt
│   ├── metrics.json
│   ├── constellation.png
│   ├── ber_curve.png
│   └── sync_peak.png
├── public_tests/            # 教师提供的公开测试
└── grading/                 # 自动评分脚本
```

---

## 十一、已知设计决策与权衡

### 11.1 Preamble 与 Frame 的层级关系

Preamble 作为帧结构的一部分（Frame Build 输出中），但在 Modulation 前以符号序列的形式被同步模块使用。设计上，帧封装模块负责将 preamble 比特序列嵌入帧头，调制模块将帧比特统一映射为符号。同步模块独立使用已知 preamble 符号序列做检测。

### 11.2 硬判决 vs 软判决

Level 1-2 采用硬判决解调和硬判决 Viterbi 译码。在 12 dB SNR 的 AWGN 信道下，硬判决已能完全恢复文本。Level 3 可扩展软判决译码（解调器输出 LLR 而非硬比特，Viterbi 译码使用欧氏距离作为分支度量），在更低 SNR 下提升性能。

### 11.3 CRC-16 vs 校验和

选择 CRC-16 而非简单累加求和，因为 CRC-16 对突发错误的检测能力更强，且仅增加 16 比特开销。多项式选用 CRC-16-IBM (`0x8005`)，可在 Python 中直接实现或借助标准库二进制操作。

### 11.4 单帧设计

当前设计假设输入文本适配在单帧内。帧长度字段为 16 比特（最大 65535 比特），对应约 8 KB UTF-8 文本，满足课程实验需求。若文本更长，Level 3 可扩展多帧传输。
