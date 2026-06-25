# 无线通信基带仿真系统 — DESIGN.md

## 1. 系统架构总览

```
Test.txt → Source Encode → Scramble → Channel Encode → Frame Build → QPSK Modulate → Channel → Synchronization → QPSK Demodulate → Channel Decode → Descramble → Source Decode → received.txt → Metrics/Plots
```

系统采用模块化流水线架构，每一模块独立封装于 `src/` 目录下，通过 `main.py` 进行参数化编排。

## 2. 模块设计

### 2.1 Source Encode / Decode (`src/source.py`)

- **接口**：`source_encode(text) → bits`, `source_decode(bits) → text`
- **算法**：将 UTF-8 文本按字节逐位转换为 0/1 比特序列（大端序，MSB first）。解码时按 8 位一组还原为字节，再以 `utf-8` 编码还原文本。尾部不足 8 位的比特丢弃。
- **特性**：`text_to_bits` / `bits_to_text` 作为别名函数以兼容测试发现机制。

### 2.2 Scramble / Descramble (`src/crypto.py`)

- **接口**：`scramble(bits, seed) → bits`, `descramble(bits, seed) → bits`
- **算法**：基于 15 位 LFSR（特征多项式 x¹⁵ + x¹⁴ + 1）生成 PN 序列，与输入比特逐位 XOR。XOR 是自逆操作，因此 descramble 与 scramble 实现相同。
- **种子**：使用固定 seed 控制 LFSR 初始状态，确保可复现。
- **特性**：`encrypt` / `decrypt` 作为别名。

### 2.3 Channel Encode / Decode (`src/channel_coding.py`)

- **接口**：`channel_encode(bits) → bits`, `channel_decode(bits) → bits`
- **主选算法 — Hamming(7,4)**
  - 编码：每 4 位信息位 → 7 位码字，生成矩阵 G = [I₄ | P]，校验位 p₁、p₂、p₃ 由信息位线性组合得到。
  - 译码：计算 3 位校正子，定位单比特错误位置并纠正。
  - 码率：4/7，可纠正 1 位错误/每 7 位。
- **可选算法 — 卷积码 + Viterbi**
  - (2,1,3) 卷积码，生成多项式 (7, 5)₈，约束长度 3，4 状态。
  - Viterbi 译码：硬判决，回溯深度 14。
- **特性**：`fec_encode` / `fec_decode` 作为别名。

### 2.4 Frame Build / Parse (`src/framing.py`)

- **接口**：`build_frame(payload_bits) → frame_bits`, `parse_frame(frame_bits) → dict`
- **帧结构**：

  ```
  [Preamble (64 bits)] [Length (32 bits)] [Payload (N bits)] [Checksum (8 bits)] [Padding (0/1 bit)]
  ```

  - **Preamble**：64 位伪随机序列，用于接收端帧同步检测。
  - **Length**：32 位无符号整数，表示 Payload 的比特长度（大端序）。
  - **Payload**：信道编码后的比特序列。
  - **Checksum**：8 位异或校验和，对 Payload 逐字节 XOR 计算。
  - **Padding**：若帧总比特数为奇数，填充 1 位 0 以满足 QPSK 偶数要求。
- **解析流程**：跳过 Preamble → 读取 Length → 按长度提取 Payload → 提取 Checksum → 验证 → 返回 payload、length、checksum_pass。

### 2.5 QPSK Modulate / Demodulate (`src/modulation.py`)

- **接口**：`qpsk_modulate(bits) → symbols`, `qpsk_demodulate(symbols) → bits`
- **Gray 编码映射**（符合 PRD 6.1 节）：

  | 比特对 | 复数符号 |
  |--------|---------|
  | 00     | (1 + j)/√2 |
  | 01     | (-1 + j)/√2 |
  | 11     | (-1 - j)/√2 |
  | 10     | (1 - j)/√2 |

- **归一化**：所有符号功率归一化为 1（平均 |s|² = 1）。
- **解调**：硬判决，根据实部/虚部符号判定所在象限，反查 Gray 码。
- **扩展模块**：BPSK（二进制）、16-QAM（16 进制正交幅度调制）用于自适应调制对比。

### 2.6 Channel (`src/channel.py`)

- **AWGN**
  - 接口：`awgn(symbols, snr_db, seed) → noisy_symbols`
  - 算法：计算符号平均功率 P_s → 根据 SNR = P_s / σ² 求噪声功率 → 生成复高斯噪声叠加。
  - SNR 定义为接收端符号功率与噪声功率之比（单位 dB）。
- **Rayleigh 衰落**
  - 接口：`rayleigh(symbols, snr_db, seed) → faded_symbols`
  - 算法：生成复高斯衰落系数 h ~ CN(0,1)，符号 × h 后叠加 AWGN。
- **Rician 衰落**（扩展）
  - 参数 K 控制视距分量与非视距分量功率比。

### 2.7 Synchronization (`src/synchronization.py`)

- **接口**：`synchronize(received_symbols, preamble_symbols) → start_index`
- **算法**：将接收符号序列与已知前导码符号做滑动互相关（无共轭二次处理），取绝对值峰值位置作为帧起始索引。
- **理论依据**：发射前导码与本地副本匹配滤波，相关峰值处表示帧对齐。
- **指标**：同步峰值图（sync_peak.png）可视化相关幅度。

### 2.8 OFDM（扩展模块 `src/ofdm.py`）

- 64 点 IFFT/FFT 实现 OFDM 调制解调，循环前缀长度 16。
- 数据子载波数可配置，支持频域符号映射。

### 2.9 分集合并（扩展模块 `src/diversity.py`）

- 最大比合并（MRC）：按信道估计共轭加权合并多路信号。
- 选择合并（SC）：选信噪比最高的一路。
- 等增益合并（EGC）：等权叠加。

### 2.10 自适应调制（扩展模块 `src/adaptive.py`）

- 根据 SNR 阈值切换调制方式：SNR < 8 dB → BPSK，8~15 dB → QPSK，≥15 dB → 16-QAM。

### 2.11 Metrics 与可视化

- **metrics.json** 字段：

  | 字段 | 说明 |
  |------|------|
  | snr_db | SNR (dB) |
  | seed | 随机种子 |
  | modulation | 调制方式 |
  | channel | 信道类型 |
  | payload_bits | 原始负载比特数 |
  | ber | 误比特率 |
  | fer | 误帧率 |
  | text_match_rate | 文本匹配率 (0~1) |
  | checksum_pass | 校验和是否通过 |
  | sync_start_index | 同步检测起始位置 |

- **可视化**：
  - `constellation.png`：收发符号散点图，对比理想与含噪星座。
  - `ber_curve.png`：不同 SNR 下的 BER 曲线。
  - `sync_peak.png`：滑动互相关幅度图，标注峰值位置。

## 3. 统一命令行接口

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

参数说明：
- `--input`：输入文本文件路径
- `--output`：输出接收文本路径
- `--snr`：SNR (dB)，默认 12
- `--seed`：随机种子，默认 2026
- `--mod`：调制方式（qpsk / bpsk / 16qam）
- `--channel`：信道模型（awgn / rayleigh）

## 4. 关键参数选择依据

| 参数 | 选择 | 理由 |
|------|------|------|
| QPSK | Gray 编码 | 相邻符号仅差 1 位，最小化误比特率 |
| Hamming(7,4) | 码率 4/7 | 平衡纠错能力与频谱效率，适合教学演示 |
| 64 位 Preamble | 伪随机序列 | 良好的自相关特性，抗噪声能力强 |
| CRC-8 XOR | 逐字节异或 | 简单高效，能检测奇数位错误 |
| 15 位 LFSR | x¹⁵ + x¹⁴ + 1 | 长周期 PN 序列，接近随机 |

## 5. 预期风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 低 SNR 下同步失败 | 增加前导码长度、使用非相干检测 |
| Hamming 码无法纠正多位错误 | 在尾部补充重复编码 |
| 校验和误判 | 在 payload 中嵌入 CRC-16 |
| 长文本帧过长 | 支持分帧传输（可选） |

## 6. QPSK 星座图结果分析

在 SNR = 12 dB 的 AWGN 信道下，QPSK 星座点聚集在四个象限中心附近（±1/√2）。由于 Gray 编码设计，相邻象限间的误码发生在单比特上。随着 SNR 降低，星座点弥散加剧，BER 上升。当 SNR < 4 dB 时，判决错误显著增加导致文本恢复失败。

## 7. BER 与 text_match_rate 随 SNR 变化

在 Hamming(7,4) 编码下，AWGN 信道中 SNR ≥ 8 dB 时 BER < 10⁻⁴，text_match_rate = 1.0；SNR = 6 dB 时 BER 约 10⁻³，仍有少量误码可被 Hamming 码纠正；SNR < 4 dB 时纠错失效，text_match_rate 开始下降。无编码时 QPSK 的理论 BER 为 Q(√(2·SNR))。
