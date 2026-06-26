# 无线通信基带仿真系统设计文档

> 课程：无线通信技术 / 无线通信基础  
> 项目：基于 AI 辅助编程的无线通信文件传输基带仿真系统  
> 版本：v0.3（mock 测试后修订）

---

## 1. 设计目标与范围

### 1.1 目标

实现一条**固定顺序**的端到端基带仿真链路，将教师提供的 UTF-8 文本 `Test.txt` 经发送端处理、AWGN 信道传输、接收端同步与译码后，恢复为 `results/received.txt`，并输出 `results/metrics.json` 与至少两类性能图表。

### 1.2 范围

| 类别 | 本设计采用 | 备注 |
|------|-----------|------|
| 调制 | **QPSK（Gray 编码，必做）** | 符合 PRD 统一口径 |
| 信道 | **AWGN（必做）** | SNR 可配置，固定 seed 可复现 |
| 扰码/加密 | **PN 序列 XOR 扰码** | seed 驱动，可逆 |
| 信道编码 | **(3,1) 重复码** | 三重复制 + 多数表决译码，见 §4.3 |
| 同步 | **前导序列互相关峰值检测** | 支持 0～128 符号随机前置偏移 |
| 校验 | **CRC-16/CCITT** | 覆盖源编码比特流 |
| BER 曲线 | **每次 CLI 运行生成** | SNR 0～14 dB，步进 2 dB |
| 扩展（Level 3） | **Rayleigh 衰落、卷积码 + Viterbi** | 见 §11，基础链路不依赖 |

### 1.3 统一验收命令

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

---

## 2. 系统架构

### 2.1 固定系统链路

PRD 要求所有学生实现同一条链路，本系统流程如下：

```text
Test.txt
  → Source Encode          （UTF-8 文本 → 比特流）
  → Scramble               （PN XOR 扰码）
  → Channel Encode         （(3,1) 重复码）
  → Frame Build            （前导 + length + payload + CRC）
  → QPSK Modulate          （Gray 映射，必要时帧尾补 0）
  → Channel (AWGN)         （加性高斯白噪声）
  → Synchronization        （前导相关，检测帧起点）
  → QPSK Demodulate        （硬判决解调）
  → Frame Parse            （解帧、CRC 校验）
  → Channel Decode         （重复码多数表决译码）
  → Descramble             （PN XOR 解扰）
  → Source Decode          （按 length 截断 padding 比特 → UTF-8 文本）
  → results/received.txt
  → Metrics / Plots        （BER、FER、星座图、BER-SNR 曲线、同步峰值图）
```

### 2.2 逻辑分层

```text
┌─────────────────────────────────────────────────────────────┐
│  main.py          CLI 入口、参数解析、流程编排、结果落盘      │
├─────────────────────────────────────────────────────────────┤
│  src/transmitter.py   发送端流水线（编码 → 组帧 → 调制）      │
│  src/receiver.py      接收端流水线（同步 → 解调 → 译码）      │
├─────────────────────────────────────────────────────────────┤
│  信号处理模块                                                │
│    source.py          Source Encode / Source Decode          │
│    scramble.py        Scramble / Descramble                  │
│    channel_coding.py  Channel Encode / Channel Decode        │
│    framing.py         Frame Build / Frame Parse              │
│    modulation.py      QPSK Modulate / QPSK Demodulate        │
│    channel.py         AWGN 信道                              │
│    synchronization.py Synchronization                        │
├─────────────────────────────────────────────────────────────┤
│  辅助模块                                                    │
│    metrics.py         指标计算与 metrics.json 生成           │
│    plots.py           星座图、BER 曲线、同步峰值图            │
│    utils.py           比特/字节转换、CRC、随机数封装          │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 目录结构（规划）

```text
wireless-final-project-template/
  DESIGN.md
  TEST_PLAN.md
  MOCK_TEST_REPORT.md
  AI_LOG.md
  Test.txt
  main.py
  src/
    __init__.py
    source.py
    scramble.py
    channel_coding.py
    framing.py
    modulation.py
    channel.py
    synchronization.py
    transmitter.py
    receiver.py
    metrics.py
    plots.py
    utils.py
  tests/                  # 学生自测（mock / 单元测试）
  results/                # 运行输出（received.txt、metrics.json、图表）
  public_tests/           # 教师公开测试（已提供）
```

---

## 3. 数据流与关键字段语义

### 3.1 各阶段数据形态

| 阶段 | 数据类型 | 说明 |
|------|---------|------|
| 输入文本 | `str` (UTF-8) | 来自 `Test.txt` |
| 源编码比特 | `List[int]` 或 `np.ndarray` | 每字节 8 bit，MSB 优先；长度必为 8 的整数倍 |
| 扰码后比特 | 同上 | 与源编码等长 |
| 信道编码比特 | 同上 | 长度为源编码的 **3 倍**（每位重复 3 次） |
| 帧比特流 | 同上 | 前导 ‖ length ‖ coded_payload ‖ CRC |
| QPSK 符号 | `np.ndarray(complex)` | 单位平均功率；奇数 bit 时在**整帧比特流末尾**补 1 个 0 |
| 接收符号 | `np.ndarray(complex)` | 含随机前置偏移 + 噪声 |
| 恢复文本 | `str` | 按 `length` 截断有效比特后 UTF-8 解码 |

### 3.2 `length` 字段（PRD 统一口径）

- **定义**：源编码后、扰码**前**的 payload **比特数**（记为 `payload_bits`）。
- **用途**：接收端在 Descramble 之后，取前 `length` 个比特送入 Source Decode，从而去除 QPSK 调制引入的帧尾 padding 比特。
- **编码格式**：**16 bit 无符号整数**，MSB 先发（大端比特序），可支持最长 65535 bit 的文本载荷。

### 3.3 随机种子分工

全局 CLI 参数 `--seed`（默认 `2026`）作为**主种子**，派生各子模块种子，保证端到端可复现：

| 子模块 | 派生方式（规划） |
|--------|-----------------|
| 扰码 PN 序列 | `seed` 直接用于 LFSR 初态 |
| AWGN 噪声 | `numpy.random.default_rng(seed)` |
| 帧前随机偏移 | `default_rng(seed + 1)`，均匀采样 `offset ∈ [0, 128]` 个 QPSK 符号 |
| BER 曲线扫描 | 各 SNR 点使用 `default_rng(seed + snr*100)` |

---

## 4. 模块设计与算法选择

### 4.1 Source Encode / Source Decode

**算法**：将 UTF-8 字节流按 **MSB 优先**展开为比特序列（每字节 8 bit），不额外添加长度头（长度由帧结构 `length` 字段承载）。

**Source Encode**

```python
def text_to_bits(text: str) -> list[int]:
    """UTF-8 文本 → 0/1 列表，长度是 8 的整数倍。"""

def source_encode(text: str) -> list[int]:
    """text_to_bits 的别名，供测试发现。"""
```

**Source Decode**

```python
def bits_to_text(bits: list[int], num_bits: int | None = None) -> str:
    """
    比特 → UTF-8 文本。
    num_bits: 有效载荷比特数（来自帧 length 字段）；为 None 时使用 len(bits)。
    仅取前 num_bits 个比特，再按 8 bit 组字节解码。
    """

def source_decode(bits: list[int], num_bits: int | None = None) -> str:
    """bits_to_text 的别名。"""
```

**关键参数**：无额外压缩；中文 UTF-8 每字符通常 3 字节。

---

### 4.2 Scramble / Descramble

**算法选择**：**PN 序列 XOR 扰码**（自同步、实现简单、完全可逆）。

- 使用 **16 级 LFSR** 生成 PN 序列（本原多项式 `x^16 + x^14 + x^13 + x^11 + 1`，初态由 `seed` 映射为非全零 16 bit）。
- 输出 PN 比特与载荷比特逐位 XOR；Descramble 再次 XOR 同一序列。

```python
def scramble(bits: list[int], seed: int = 2026) -> list[int]: ...

def descramble(bits: list[int], seed: int = 2026) -> list[int]: ...
```

**备选方案**（未采用）：AES-CTR 流密码——安全性更高但依赖第三方库，与本课程仿真重点不匹配。

---

### 4.3 Channel Encode / Channel Decode

**算法选择**：**(3,1) 重复码**，编码率 **R = 1/3**。

**理由**（已确认）：

- 实现最简单：每位比特重复 3 次，译码时 3 取 2 多数表决；
- 在 SNR = 12 dB、QPSK、约数千比特载荷下抗噪余量充足；
- 调试直观，便于 mock 测试与答辩解释；
- 卷积码 + Viterbi 作为 Level 3 扩展模块单独实现（§11），不替代基础重复码链路。

**编码规则**：

- 对输入比特流逐位重复 3 次：`b → [b, b, b]`；
- 无分组补齐；输出长度 `len(out) = 3 * len(in)`。

**译码规则**：**硬判决 + 多数表决（3 取 2）**

- 每 3 个接收比特为一组，统计 0/1 个数，取多数作为判决结果；
- 若 3 比特各不同（理论上硬判决下不会出现 1:1:1 平局），按 0 处理并记录警告。

```python
def channel_encode(bits: list[int]) -> list[int]: ...

def channel_decode(bits: list[int]) -> list[int]:
    """无噪声下可无损恢复；有噪声时每组最多纠正 1 比特错误。"""
```

**纠错能力**：每组 3 比特中允许 1 个错误仍正确译码，等效于单比特纠错，在低 SNR 下比未编码更稳健。

**Eb/N0 与 SNR 换算**（记录于 metrics，便于分析）：

- 本系统 CLI 参数 `snr_db` 定义为 **Es/N0**（每符号能量 / 噪声功率谱密度），即接收端 QPSK 符号平均功率与复噪声平均功率之比。
- QPSK 每符号 2 bit：`Eb/N0 (dB) = Es/N0 (dB) - 10*log10(2) = snr_db - 3.01`
- 考虑编码率 R=1/3：`Eb/N0_encoded (dB) ≈ snr_db - 3.01 - 10*log10(3) ≈ snr_db - 7.78`

---

### 4.4 Frame Build / Frame Parse

**帧结构**（比特域，组帧后再统一 QPSK 调制）：

```text
┌──────────────┬────────────┬─────────────────────┬──────────────┐
│  Preamble    │  Length    │  Coded Payload      │  CRC-16      │
│  32 bit      │  16 bit    │  变长               │  16 bit      │
└──────────────┴────────────┴─────────────────────┴──────────────┘
```

| 字段 | 长度 | 内容 |
|------|------|------|
| **Preamble** | 32 bit | 固定已知比特模式 `0xAA55AA55`（映射为 **16 个 QPSK 符号**，已确认缩短） |
| **Length** | 16 bit | 源编码后、扰码前的 `payload_bits`（大端） |
| **Payload** | 变长 | 信道编码后的比特流 |
| **CRC-16** | 16 bit | 对**源编码原始比特流**（扰码前）计算 CRC-16/CCITT（多项式 0x1021，初值 0xFFFF，已确认） |

**Frame Build 接口**：

```python
def build_frame(payload_bits: list[int], source_bits_for_crc: list[int]) -> dict:
    """
    返回 dict，至少包含键：preamble, length, payload, crc（或 checksum）。
    同时提供序列化比特流 frame_bits 或 bits 字段供调制使用。
    payload_bits: 信道编码后的比特
    source_bits_for_crc: 源编码后、扰码前的比特（用于 CRC 与 length）
    """
```

**Frame Parse 接口**：

```python
def parse_frame(frame_bits: list[int]) -> dict:
    """
    返回 dict：length, payload, crc, checksum_pass（或 crc_pass）。
    解析失败时不抛异常，由上层记录 fer 与失败原因。
    """
```

**QPSK padding**：若 `len(frame_bits)` 为奇数，在**末尾补 1 个 0** 再调制；接收端解调后 **`parse_frame` 先调用 `_strip_qpsk_tail_padding` 去除可能的多余尾 0**，再解析；最终在 Source Decode 前按 `length` 截断。

**parse_frame 入参**：除 bit 列表外，也接受 `build_frame` 返回的 dict（自动读取 `bits`/`frame` 键），以兼容公开测试 TC-T-006。

---

### 4.5 QPSK Modulate / QPSK Demodulate

**映射（PRD 统一 Gray 编码）**：

| 比特对 (b0,b1) | 符号 (I+jQ) / √2 |
|----------------|------------------|
| 00 | (1+j) |
| 01 | (-1+j) |
| 11 | (-1-j) |
| 10 | (1-j) |

- 比特两两分组，**每组高位 b0 → I，低位 b1 → Q**（与 TC-T-009 测试向量一致）。
- 符号能量归一化：除以 `√2`，使 `E[|s|²] = 1`。

```python
def qpsk_modulate(bits: list[int]) -> np.ndarray: ...   # complex, shape (N,)

def qpsk_demodulate(symbols: np.ndarray) -> list[int]:
    """硬判决：sign(I), sign(Q) → Gray 逆映射。"""
```

**星座图**：`results/constellation.png` 绘制接收符号散点与理想四点。

---

### 4.6 Channel (AWGN)

**模型**：`y = x + n`，其中 `n ~ CN(0, σ²)`，I/Q 独立同分布。

**SNR 定义**（PRD 口径）：

```text
SNR_linear = P_signal / P_noise
P_signal   = mean(|x|²)          # 发送符号平均功率，QPSK 归一化后 ≈ 1
P_noise    = mean(|n|²) = 2σ²
σ² = P_signal / (2 · 10^(SNR_dB/10))
```

```python
def awgn(symbols: np.ndarray, snr_db: float, seed: int = 2026) -> np.ndarray: ...
```

**可复现性**：固定 `seed` 时，`numpy.random.Generator` 生成噪声序列完全一致（满足 TC-T-012）。

**扩展（Level 3）**：`channel.py` 实现 `rayleigh()` 平坦衰落信道（见 §11.1），CLI 支持 `--channel rayleigh`。

---

### 4.7 Synchronization

**算法**：**滑动互相关（匹配滤波）**

1. 发送端在帧前插入 `offset` 个随机 QPSK 符号（`offset ~ Uniform{0,…,128}`，由 `seed+1` 决定）。
2. 接收端用已知前导符号序列 `preamble_symbols`（由 Preamble 32 bit QPSK 映射得到，共 16 符号）与接收序列做归一化互相关。
3. 相关峰值位置即为帧起点 `sync_start_index`；允许 **±1 符号**误差（PRD 要求）。

```python
def detect_frame_start(
    rx_symbols: np.ndarray,
    preamble_symbols: np.ndarray | None = None,
) -> int:
    """返回检测到的帧起点符号索引。"""

def synchronize(rx_symbols: np.ndarray, preamble: np.ndarray | None = None) -> dict:
    """返回 {sync_start_index, correlation, aligned_symbols}。"""
```

**同步峰值图**：`results/sync_peak.png` 绘制相关值随符号索引的变化曲线并标注峰值。

---

### 4.8 Metrics / Plots

**metrics.json 最低字段**（PRD §6.2）：

```json
{
  "snr_db": 12,
  "seed": 2026,
  "modulation": "qpsk",
  "channel": "awgn",
  "payload_bits": 0,
  "ber": 0.0,
  "fer": 0.0,
  "text_match_rate": 1.0,
  "checksum_pass": true,
  "sync_start_index": 0,
  "eb_n0_db": 0.0,
  "coding_rate": 0.3333,
  "frame_error": false,
  "failure_reason": null
}
```

| 指标 | 定义 |
|------|------|
| `payload_bits` | 源编码后、扰码前比特数 |
| `ber` | 误比特率 = 错误比特数 / 比较总比特数（源编码域或译码后比特域，实现时统一并在文档注明） |
| `fer` | 帧错误率：CRC 失败或 `text_match_rate < 1` 记 1，否则 0 |
| `text_match_rate` | 恢复文本与原文一致字符比例（0.0～1.0） |
| `checksum_pass` | CRC-16 校验是否通过 |
| `sync_start_index` | 检测到的帧起点（符号索引） |

**图表**（至少生成其中两项）：

| 文件 | 内容 |
|------|------|
| `constellation.png` | 接收 QPSK 符号散点 + 理想星座点 |
| `ber_curve.png` | SNR = 0～14 dB（步进 2 dB）下的 BER 或 `text_match_rate` 曲线；**每次 CLI 运行均生成**（已确认） |
| `sync_peak.png` | 前导互相关峰值图 |

---

## 5. 端到端流水线接口

### 5.1 发送端 `run_transmitter`

```python
def run_transmitter(
    text: str,
    seed: int = 2026,
) -> tuple[np.ndarray, dict]:
    """
    返回 (tx_symbols, meta)
    meta 包含：payload_bits, preamble_symbols, frame_bits, offset 等调试信息。
    """
```

### 5.2 接收端 `run_receiver`

```python
def run_receiver(
    rx_symbols: np.ndarray,
    seed: int = 2026,
    preamble_symbols: np.ndarray | None = None,
) -> tuple[str, dict]:
    """
    返回 (recovered_text, metrics_partial)
    """
```

### 5.3 CLI `main.py`

```python
# argparse 参数
--input    # 输入文本路径，默认 Test.txt
--output   # 输出文本路径，默认 results/received.txt
--snr      # 信噪比 dB，默认 12
--seed     # 随机种子，默认 2026
--mod      # 调制方式，基础仅实现 qpsk
--channel  # 信道类型：awgn（基础）/ rayleigh（Level 3 扩展）
```

主流程：读入文本 → 发送端 → 信道（AWGN / Rayleigh）→ 接收端 → 写 `received.txt` → 写 `metrics.json` → 生成图表（含 BER 曲线全 SNR 扫描）。

---

## 6. 关键参数汇总

| 参数 | 取值 | 说明 |
|------|------|------|
| 调制 | QPSK Gray | PRD 强制 |
| 符号归一化 | `1/√2` | 单位平均功率 |
| 信道 | AWGN | PRD 基础必做 |
| 默认 SNR | 12 dB | 公开测试通过条件 |
| 默认 seed | 2026 | 公开测试 / 扰码 / 噪声复现 |
| 扰码 | 16 级 LFSR XOR | seed 驱动 |
| 信道编码 | (3,1) 重复码 | R=1/3，多数表决译码 |
| 前导长度 | 32 bit（16 符号） | 固定模式 `0xAA55AA55` |
| length 字段 | 16 bit 大端 | 记录源编码比特数 |
| CRC | CRC-16/CCITT | 覆盖源编码比特流 |
| 随机偏移 | 0～128 符号 | `rng(seed+1)` |
| 同步容差 | ±1 符号 | PRD 基础口径 |
| BER 曲线 SNR 扫描 | 0,2,4,…,14 dB | 每次 CLI 运行生成 ber_curve.png |
| Level 3 扩展 | Rayleigh + Viterbi 卷积码 | 见 §11 |

以 `Test.txt`（约 300 字中文）估算：源编码约 **7200～7500 bit**；重复码编码后约 **21 600～22 500 bit**；加 32 bit 前导、16 bit length、16 bit CRC 后，QPSK 映射约 **10 800+ 符号**。重复码在 12 dB 下纠错余量充足，配合 CRC-16 可保障无错恢复。

---

## 7. 预期风险与应对

| # | 风险 | 影响 | 应对策略 |
|---|------|------|----------|
| R1 | **重复码码率 1/3 带宽开销大** | 符号数约为汉明码方案的 1.7 倍，BER 曲线扫描更慢 | 基础链路优先正确性；BER 曲线复用同一帧结构；Level 3 可对比 Viterbi 卷积码效率 |
| R2 | **前导缩短至 32 bit 后同步余量降低** | 高噪声或长偏移时误检概率略升 | 归一化互相关 + 峰值邻域确认；PRD 允许 ±1 符号误差；mock 阶段重点验证 offset=128 边界 |
| R3 | **`length` 与 padding 语义混淆** | 恢复文本乱码或多余比特 | 严格约定 + `_strip_qpsk_tail_padding`（mock MK-002 已验证） |
| R4 | **CRC 覆盖范围不一致** | `checksum_pass` 与文本恢复不一致 | CRC 统一对**源编码比特**计算；Parse 时用译码+解扰后重算比对 |
| R5 | **UTF-8 多字节截断** | `num_bits` 非 8 倍数导致解码异常 | `length` 来自源编码，天然为 8 的倍数；解码前断言 `num_bits % 8 == 0` |
| R6 | **固定 seed 下偏移与噪声耦合** | 隐藏测试换 seed 行为异常 | 子模块种子派生公式固定并写入本文档；mock 阶段多 seed 回归 |
| R7 | **每次 CLI 全 SNR 扫描耗时** | 8 个 SNR 点 × 重复码 3 倍比特，运行数十秒 | 已确认每次运行生成完整曲线；BER 扫描复用固定 `Test.txt` 不重复读盘；各 SNR 点仅重跑信道+接收端 |
| R8 | **隐藏测试不同文本长度** | 帧超长或 length 溢出 | 16 bit length 上限 65535 bit，足够；超长文本需分段（当前课程文本远小于上限） |

---

## 8. 实验结果分析（设计预期）

> 本节满足公开测试对 DESIGN.md 的结果解释要求（TC-T-019）；实现后以实测数据更新数值。

### 8.1 QPSK 星座图

- 高 SNR（12 dB）下，接收符号应紧密聚集在四个理想点 `(±1±j)/√2` 附近。
- 随 SNR 降低，散点云向原点收缩并出现径向扩散，说明噪声主导。

### 8.2 BER / text_match_rate 随 SNR 变化

- 未编码 QPSK 理论 BER：`Pb ≈ Q(√(2·10^(SNR/10)))`。
- 加入 (3,1) 重复码后，每组 3 比特可纠正 1 个错误，低 SNR 下 `text_match_rate` 优于未编码 QPSK（约 3～5 dB 量级增益）。
- 预期 **SNR ≥ 12 dB** 时 `text_match_rate = 1.0`；**SNR < 4 dB** 时可能出现 CRC 失败或字符乱码。
- 每次 CLI 运行生成的 `ber_curve.png` 应呈现 BER 随 SNR 单调下降、`text_match_rate` 在阈值附近陡升的趋势。

### 8.3 失败 / 误码原因分析

| 现象 | 可能首要环节 | 排查顺序 |
|------|-------------|----------|
| 乱码但 CRC 通过 | Source Decode 截断长度错误 | 检查 `length` 字段与 `num_bits` |
| CRC 失败 | 信道译码或同步错误 | 查 `sync_start_index`、BER、相关峰 |
| 同步峰偏移 >1 | 噪声过大或前导不匹配 | 查 `sync_peak.png`、前导比特一致性 |
| 完全随机输出 | 帧起点错误 | 查偏移量与相关峰值位置 |

---

## 9. 测试与验收对齐

本设计与 `public_tests/` 及 `wireless_project_test_set_20.feature` 对齐：

| 测试编号 | 设计对应章节 |
|----------|-------------|
| TC-T-002 | §2 固定链路、各模块英文名称 |
| TC-T-004 | §4.1 源编码 |
| TC-T-005/006/011 | §4.4 帧结构、§3.2 length、padding |
| TC-T-007 | §4.2 扰码 |
| TC-T-008 | §4.3 信道编码 |
| TC-T-009/010 | §4.5 QPSK |
| TC-T-012 | §4.6 AWGN |
| TC-T-013 | §4.7 同步 |
| TC-T-014～017 | §4.8 Metrics、§5.3 CLI |
| TC-T-019 | §8 实验分析 |

---

## 10. 已确认的设计选型

| # | 项目 | 确认结果 |
|---|------|----------|
| 1 | 信道编码 | **(3,1) 重复码**，码率 1/3，多数表决译码 |
| 2 | 校验方案 | **CRC-16/CCITT**（多项式 0x1021） |
| 3 | 前导长度 | **32 bit（16 个 QPSK 符号）**，模式 `0xAA55AA55` |
| 4 | BER 曲线 | **每次 CLI 运行**扫描 SNR 0～14 dB 并生成 `ber_curve.png` |
| 5 | Level 3 扩展 | **计划实现** Rayleigh 衰落 + 卷积码 Viterbi（见 §11） |

---

## 11. Level 3 扩展模块设计（已确认纳入）

基础链路（§2～§5）保持 **重复码 + AWGN + QPSK** 不变，扩展模块通过 CLI 参数或独立函数接入，不影响公开测试默认命令。

### 11.1 Rayleigh 平坦衰落信道

**模型**：`y = h · x + n`

- 衰落系数 `h ~ CN(0, 1)`，每符号独立（平坦衰落）；
- 噪声 `n` 与 AWGN 相同，按 `snr_db` 控制功率；
- 接收端采用**理想信道估计** `ĥ = h`（仿真简化），均衡：`ŷ = y / h`（零迫 ZF）；
- 深衰落（`|h| ≈ 0`）时置 `failure_reason = "deep_fade"`，不崩溃。

```python
def rayleigh(
    symbols: np.ndarray,
    snr_db: float,
    seed: int = 2026,
) -> tuple[np.ndarray, np.ndarray]:
    """返回 (rx_symbols, channel_coeffs)。"""
```

**CLI**：`--channel rayleigh`（默认 `awgn`）。

**对比实验**：同一 `Test.txt`、同一 `seed`，比较 AWGN 与 Rayleigh 下 `text_match_rate` 与 BER 曲线，写入 `metrics.json` 扩展字段 `channel_type`。

### 11.2 卷积码 + Viterbi 译码

**定位**：作为**对比/加分模块**，不替换基础 (3,1) 重复码链路。

**编码参数**（规划）：

- 约束长度 K=3，生成多项式 `g1=7, g2=5`（八进制），码率 **R=1/2**；
- 编码器：移位寄存器 + 2 路输出，尾比特冲零终止（tail-biting 或零冲刷二选一，实现时固定并文档化）。

**译码**：**硬判决 Viterbi**，Hamming 距离路径度量。

```python
def conv_encode(bits: list[int]) -> list[int]: ...
def viterbi_decode(bits: list[int]) -> list[int]: ...
```

**接入方式**：

- 模块文件 `src/conv_coding.py`，与 `channel_coding.py` 并列；
- 可选 CLI 标志 `--fec conv`（默认 `repeat`），仅用于对比实验与答辩演示；
- 公开测试与基础验收仍使用 `--channel awgn` + 重复码，确保 PRD 口径不变。

**对比指标**：在 `ber_curve.png` 或单独 `ber_curve_conv.png` 中叠加重复码与卷积码 BER 曲线，分析编码增益与复杂度权衡。

### 11.3 扩展模块目录补充

```text
src/
  conv_coding.py    # 卷积码编码 + Viterbi 译码（Level 3）
  equalization.py   # ZF 均衡（Rayleigh 接收端使用，可选独立模块）
```

---

## 12. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-24 | 初稿：架构、接口、算法、参数、风险 |
| v0.2 | 2026-06-24 | 确认选型：(3,1) 重复码、CRC-16、32 bit 前导、全 SNR BER 曲线、Level 3 扩展章节 |
| v0.3 | 2026-06-24 | mock 后修订：parse_frame 支持 dict、QPSK padding 剥离（见 MOCK_TEST_REPORT.md） |
