# DESIGN.md — 无线通信基带仿真系统设计文档

## 1. 系统概述

本系统实现一条端到端无线通信基带仿真链路，将 UTF-8 文本文件 `Test.txt` 经发送端、AWGN 无线信道和接收端处理后，在 `results/received.txt` 中恢复原始文本。

### 固定系统链路（PRD 要求，模块顺序不可更改）

```
Test.txt → Source Encode → Encrypt/Scramble → Channel Encode → Frame Build
→ QPSK Modulate → Channel (AWGN) → Synchronization → QPSK Demodulate
→ Channel Decode → Decrypt/Descramble → Source Decode → received.txt → Metrics/Plots
```

## 2. 模块接口与算法设计

### 2.1 源编码模块 (`src/source.py`)

**功能**：UTF-8 文本 ↔ 比特流互转。

**接口**：
```python
def source_encode(text: str) -> list[int]:
    """将 UTF-8 文本转换为比特流（每字节 MSB 优先），返回 int 列表。"""

def source_decode(bits: list[int]) -> str:
    """将比特流恢复为 UTF-8 文本。"""
```

**算法**：
- 编码：UTF-8 字符串 → `bytes` → 每个字节展开为 8 bit（MSB first）
- 解码：每 8 bit 一组 → 整数 → `bytes` → UTF-8 字符串
- 若比特数不是 8 的倍数，尾部不足 8 bit 的部分丢弃（实际应由帧长度字段保证不会发生）

**关键参数**：无。UTF-8 编码由 Python 标准库处理。

### 2.2 扰码/加密模块 (`src/crypto.py`)

**功能**：对发送比特进行可逆处理，增加比特随机性。

**接口**：
```python
def scramble(bits: list[int], seed: int) -> list[int]:
    """使用固定种子的 PN 序列进行 XOR 扰码。"""

def descramble(bits: list[int], seed: int) -> list[int]:
    """解扰（与扰码相同操作，XOR 可逆）。"""
```

**算法**：
- 使用 NumPy 固定种子 RNG 生成与输入等长的随机比特序列
- XOR 操作：`output[i] = input[i] XOR pn[i]`
- 解扰与扰码完全相同（对称操作）

**关键参数**：
| 参数 | 说明 |
|------|------|
| `seed` | 随机种子，保证可复现性，默认 2026 |

### 2.3 信道编码模块 (`src/channel_coding.py`)

**功能**：提供前向纠错（FEC）能力，对抗信道噪声。

**接口**：
```python
def channel_encode(bits: list[int]) -> list[int]:
    """信道编码，增加冗余以对抗噪声。"""

def channel_decode(bits: list[int]) -> list[int]:
    """信道译码，纠错后恢复原始比特。"""
```

**算法**：汉明(7,4) 分组码
- 将输入比特按 4 bit 分组，若最后一组不足 4 bit 则补零
- 每 4 bit 编码为 7 bit（含 3 个奇偶校验位）
- 译码时使用伴随式（syndrome）纠正单比特错误
- 译码后去除补零 padding

**生成矩阵 G**（系统形式）：
```
G = [I₄ | P], P = [[1,1,0], [1,0,1], [0,1,1], [1,1,1]]
```

**奇偶校验矩阵 H**：
```
H = [Pᵀ | I₃]
```

**关键参数**：
| 参数 | 值 | 说明 |
|------|-----|------|
| 码率 R | 4/7 ≈ 0.57 | 每 4 bit 数据产生 7 bit 编码 |
| 纠错能力 t | 1 bit/码字 | 每 7 bit 码字可纠正 1 个错误 |

### 2.4 帧结构模块 (`src/framing.py`)

**功能**：将编码后的比特封装为可传输的帧结构，包含同步和校验信息。

**接口**：
```python
def build_frame(payload: list[int]) -> dict:
    """构建帧，返回包含 preamble, length, payload, crc 等字段的字典。"""

def parse_frame(frame) -> dict:
    """解析帧，输入可为 dict 或比特列表。"""
```

**帧结构设计**：

```
┌────────────┬────────────┬──────────────────┬────────────┐
│  Preamble  │   Length   │     Payload      │   CRC-16   │
│   32 bit   │   16 bit   │    N bit (变长)   │   16 bit   │
└────────────┴────────────┴──────────────────┴────────────┘
```

- **Preamble（前导序列）**：32-bit 巴克码扩展序列 `0xA1B2C3D4`（具有良好的自相关特性）
- **Length（长度字段）**：16-bit 无符号整数，记录 payload 的 bit 数（大端序），最大支持 65535 bit
- **Payload（载荷）**：可变长度比特数据
- **CRC-16**：16-bit CRC 校验值，覆盖 Length + Payload 字段，多项式 `0x1021`（CRC-16-CCITT）

**QPSK 适配 padding**：
- 若帧总位数（64 + N）为奇数，在帧末尾补 1 bit 零，使帧位数为偶数
- 接收端根据 Length 字段精确截取 payload，丢弃 padding

**帧结构返回格式**（dict）：
```python
{
    "preamble": [0,0,0,1, ...],   # 32 bits
    "length": 2400,                # payload bit count
    "payload": [1,0,1, ...],       # N bits
    "crc": [0,1,1, ...]            # 16 bits
}
```

**serialize 为比特列表时**：`preamble + length_bits + payload + crc [+ pad]`

**关键参数**：
| 参数 | 值 | 说明 |
|------|-----|------|
| Preamble 长度 | 32 bit (16 QPSK symbols) | 用于同步检测 |
| Length 位宽 | 16 bit | 最大 65535 bit 载荷 |
| CRC 多项式 | 0x1021 (CRC-16-CCITT) | 16 bit 校验 |

### 2.5 QPSK 调制模块 (`src/modulation.py`)

**功能**：将比特流映射为 QPSK 复数符号，接收端解映射回比特。

**接口**：
```python
def qpsk_modulate(bits: list[int]) -> np.ndarray:
    """QPSK 调制，2 bit → 1 复数符号。返回 complex128 数组。"""

def qpsk_demodulate(symbols: np.ndarray) -> list[int]:
    """QPSK 解调（硬判决），1 复数符号 → 2 bit。"""
```

**星座映射（Gray 编码）**：

| 比特对 (b₁b₀) | I (实部) | Q (虚部) | 象限 |
|:---:|:---:|:---:|:---:|
| 00 | +1/√2 | +1/√2 | 第一象限 |
| 01 | -1/√2 | +1/√2 | 第二象限 |
| 11 | -1/√2 | -1/√2 | 第三象限 |
| 10 | +1/√2 | -1/√2 | 第四象限 |

- 归一化：幅度 ±1/√2，每个符号的平均功率 = 1
- 解调：LLR 硬判决，根据接收符号的 I/Q 分量的符号判定比特

**关键参数**：
| 参数 | 值 | 说明 |
|------|-----|------|
| 调制阶数 M | 4 | 每符号 2 bit |
| 归一化因子 | 1/√2 | 单位平均功率 |
| Gray 编码 | 是 | 相邻符号仅差 1 bit |

### 2.6 AWGN 信道模块 (`src/channel.py`)

**功能**：模拟加性高斯白噪声信道。

**接口**：
```python
def awgn(symbols: np.ndarray, snr_db: float, seed: int) -> np.ndarray:
    """对输入符号添加 AWGN 噪声，返回加噪后的符号。"""
```

**算法**：
- 根据 SNR (dB) 计算噪声功率：`σ² = 10^(-SNR_dB/10)`（信号功率归一化为 1）
- 生成复数高斯噪声：`noise = √(σ²/2) · (N(0,1) + j·N(0,1))`
- 使用固定 seed 的 NumPy RNG 保证可复现

**关键参数**：
| 参数 | 说明 |
|------|------|
| `snr_db` | 信噪比（dB），可配置 |
| `seed` | 随机种子，保证复现 |

### 2.7 同步模块 (`src/synchronization.py`)

**功能**：利用前导序列互相关检测帧起点。

**接口**：
```python
def synchronize(received: np.ndarray, preamble: np.ndarray) -> int:
    """返回检测到的帧起点索引（preamble 第一个符号的位置）。"""
```

**算法**：
- 对接收信号与已知 preamble 符号序列进行滑动互相关
- 互相关峰值位置即为帧起点
- 使用 `scipy.signal.correlate` 计算

**关键参数**：
| 参数 | 说明 |
|------|------|
| preamble | 由帧结构 preamble 比特经 QPSK 调制得到的复数符号序列（16 符号） |

### 2.8 主程序 (`main.py`)

**CLI 接口**：
```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

**参数**：
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--input` | 输入文本文件路径 | Test.txt |
| `--output` | 输出恢复文本路径 | results/received.txt |
| `--snr` | SNR (dB) | 12 |
| `--seed` | 随机种子 | 2026 |
| `--mod` | 调制方式 | qpsk |
| `--channel` | 信道类型 | awgn |

### 2.9 性能指标与可视化

生成以下输出：

1. **`results/metrics.json`**：包含 snr_db, seed, modulation, channel, payload_bits, ber, fer, text_match_rate, checksum_pass, sync_start_index
2. **`results/constellation.png`**：接收端 QPSK 星座图（I/Q 散点图）
3. **`results/ber_curve.png`**：BER vs SNR 曲线（多 SNR 点仿真）
4. **`results/sync_peak.png`**：同步互相关峰值图

## 3. 系统架构总览

```
main.py (CLI + Pipeline Orchestrator)
  │
  ├── src/source.py          (源编码/解码)
  ├── src/crypto.py          (扰码/解扰)
  ├── src/channel_coding.py  (信道编码/译码 — 汉明(7,4))
  ├── src/framing.py         (帧封装/解析)
  ├── src/modulation.py      (QPSK 调制/解调)
  ├── src/channel.py         (AWGN 信道)
  └── src/synchronization.py (帧同步)
```

## 4. 关键参数汇总

| 参数 | 值 | 位置 |
|------|-----|------|
| 前导序列长度 | 32 bit | framing.py |
| 长度字段位宽 | 16 bit | framing.py |
| CRC 多项式 | 0x1021 (CRC-16-CCITT) | framing.py |
| 调制方式 | QPSK (Gray 编码) | modulation.py |
| 归一化方式 | 1/√2 (单位功率) | modulation.py |
| 信道模型 | AWGN | channel.py |
| 信道编码 | 汉明(7,4), R=4/7 | channel_coding.py |
| 扰码方式 | XOR with PN (fixed seed) | crypto.py |

## 5. 预期风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 低 SNR 下同步失败 | 无法定位帧起点，FER=1 | preamble 选 32 bit 长序列，互相关增益足够 |
| 汉明(7,4)纠错能力有限 | 高噪声下 BER 高 | SNR ≥ 12 dB 时基本可行；可扩展为卷积码 |
| 帧长度 odd 导致 QPSK 符号对齐问题 | 最后一个符号无法完整映射 | 帧封装时自动补零，接收端靠 length 裁剪 |
| CRC 碰撞 | 错误的帧被误判为正确 | CRC-16 碰撞概率低（~1/65536） |
