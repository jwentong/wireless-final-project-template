# 无线通信基带仿真系统设计文档

## 1. 系统概述

本项目实现一个完整的无线通信基带仿真系统，将 UTF-8 中文文本通过发送端、无线信道和接收端处理后恢复为原始文本。系统支持参数化配置，包括 SNR、随机种子、调制方式和信道类型。

### 1.1 系统架构

```
发送端:
  文本输入 → 源编码 → 扰码 → 信道编码 → 帧封装 → QPSK调制

信道:
  AWGN信道（高斯白噪声）

接收端:
  同步 → QPSK解调 → 帧解析 → 信道译码 → 解扰 → 源解码 → 文本输出
```

### 1.2 技术指标

- **调制方式**: QPSK（正交相移键控）
- **信道类型**: AWGN（加性高斯白噪声）
- **工作 SNR**: 12 dB（保证 text_match_rate = 1.0）
- **帧结构**: Preamble + Length + Payload + CRC16
- **信道编码**: 卷积码 (rate=1/2, constraint length=7)
- **扰码**: LFSR（线性反馈移位寄存器）

---

## 2. 模块详细设计

### 2.1 源编码（Source Encode）

**功能**: 将 UTF-8 编码的中文文本转换为比特流

**实现**:
```python
def source_encode(text: str) -> np.ndarray:
    """
    将文本编码为比特流

    算法:
    1. 使用 UTF-8 编码将文本转换为字节序列
    2. 将每个字节转换为 8 位二进制
    3. 拼接为完整的比特流

    参数:
        text: UTF-8 编码的中文文本

    返回:
        bits: 比特流数组，dtype=np.int8
    """
    bytes_data = text.encode('utf-8')
    bits = np.unpackbits(np.frombuffer(bytes_data, dtype=np.uint8))
    return bits.astype(np.int8)
```

**可逆性**: 通过 `source_decode` 模块完全可逆恢复原始文本

**关键参数**:
- 编码方式: UTF-8
- 输出格式: np.int8 数组（0/1）

---

### 2.2 扰码（Scramble）

**功能**: 对比特流进行随机化处理，避免长连 0 或连 1 序列

**算法**: LFSR（线性反馈移位寄存器）

**实现细节**:
```python
class LFSRScrambler:
    """
    基于 LFSR 的扰码器

    多项式: x^15 + x^14 + 1
    初始种子: 2026（固定，保证可复现性）
    """
    def __init__(self, seed=2026):
        self.seed = seed
        self.taps = [15, 14]  # 反馈抽头位置

    def scramble(self, bits: np.ndarray) -> np.ndarray:
        """扰码：输入 XOR 伪随机序列"""
        prbs = self._generate_prbs(len(bits))
        return (bits ^ prbs).astype(np.int8)

    def descramble(self, bits: np.ndarray) -> np.ndarray:
        """解扰：与扰码相同（XOR 逆运算）"""
        return self.scramble(bits)
```

**关键特性**:
- 可逆性：扰码和解扰使用相同操作
- 随机性：PRBS 序列具有良好统计特性
- 可复现性：固定种子保证相同输入产生相同输出

---

### 2.3 信道编码（Channel Encode）

**功能**: 增加冗余比特，提高抗噪声能力

**算法**: 卷积码 (Convolutional Code)

**参数选择**:
- 码率: 1/2（每 1 bit 输入产生 2 bit 输出）
- 约束长度: 7
- 生成多项式: [133, 171]（八进制）

**实现**:
```python
class ConvolutionalEncoder:
    """
    卷积编码器

    参数:
        constraint_length: K = 7
        rate: R = 1/2
        generators: G0 = 133 (octal), G1 = 171 (octal)
    """
    def __init__(self):
        self.K = 7
        self.generators = [0o133, 0o171]  # 生成多项式

    def encode(self, bits: np.ndarray) -> np.ndarray:
        """
        卷积编码

        状态转移：
        - 输入 1 bit
        - 输出 2 bits (对应两个生成多项式)
        """
        # 实现移位寄存器和模2加法
```

**译码算法**: Viterbi 译码

```python
class ViterbiDecoder:
    """
    Viterbi 译码器

    使用网格图进行最大似然译码
    路径度量: 汉明距离
    """
    def decode(self, received_bits: np.ndarray) -> np.ndarray:
        """硬判决 Viterbi 译码"""
```

**性能预期**:
- 编码增益: 约 3-5 dB
- SNR 12 dB 下应无误码

---

### 2.4 帧封装（Frame Build）

**功能**: 将比特流封装为帧结构，便于同步和错误检测

**帧结构设计**:

```
+----------+--------+----------+--------+
| Preamble | Length | Payload  | CRC16  |
| 64 bits  | 16 bits| N bits   | 16 bits|
+----------+--------+----------+--------+
```

**各字段说明**:

| 字段 | 长度 | 说明 |
|------|------|------|
| Preamble | 64 bits | 同步序列：[1,0,1,0,...] 交替模式 |
| Length | 16 bits | Payload 比特数（大端序） |
| Payload | N bits | 有效载荷数据 |
| CRC16 | 16 bits | CRC-16-CCITT 校验 |

**实现**:
```python
def build_frame(payload: np.ndarray) -> np.ndarray:
    """
    帧封装

    步骤:
    1. 生成 preamble (64 bits 交替序列)
    2. 计算 payload 长度并编码为 16 bits
    3. 计算 CRC16 校验码
    4. 拼接: preamble + length + payload + crc
    """
    preamble = np.array([1, 0] * 32, dtype=np.int8)
    length_bits = encode_length(len(payload))
    crc = compute_crc16(payload)
    return np.concatenate([preamble, length_bits, payload, crc])
```

**CRC-16-CCITT 参数**:
- 多项式: 0x1021
- 初始值: 0xFFFF
- 输入反转: False
- 输出反转: False

---

### 2.5 QPSK 调制（QPSK Modulate）

**功能**: 将比特流映射为复数符号

**映射规则**: Gray 编码

| 比特对 | 星座点 | 实部 | 虚部 | 象限 |
|--------|--------|------|------|------|
| 00 | +1+j | +1 | +1 | 第一象限 |
| 01 | -1+j | -1 | +1 | 第二象限 |
| 11 | -1-j | -1 | -1 | 第三象限 |
| 10 | +1-j | +1 | -1 | 第四象限 |

**实现**:
```python
def qpsk_modulate(bits: np.ndarray) -> np.ndarray:
    """
    QPSK 调制（Gray 编码）

    输入: 比特流（长度必须为偶数）
    输出: 复数符号序列
    归一化: 平均功率 = 1
    """
    if len(bits) % 2 != 0:
        bits = np.append(bits, 0)  # padding

    symbols = []
    for i in range(0, len(bits), 2):
        b0, b1 = bits[i], bits[i+1]
        if b0 == 0 and b1 == 0:
            symbols.append(1 + 1j)
        elif b0 == 0 and b1 == 1:
            symbols.append(-1 + 1j)
        elif b0 == 1 and b1 == 1:
            symbols.append(-1 - 1j)
        else:  # 10
            symbols.append(1 - 1j)

    return np.array(symbols) / np.sqrt(2)  # 归一化
```

**功率归一化**: 符号功率归一化为 1，即 `E[|s|^2] = 1`

---

### 2.6 AWGN 信道（Channel）

**功能**: 模拟加性高斯白噪声信道

**数学模型**:
```
y = x + n
```
其中：
- `x`: 发送符号
- `n`: 复高斯噪声，n ~ CN(0, σ²)
- `y`: 接收符号

**噪声方差计算**:
```python
def calculate_noise_variance(snr_db: float) -> float:
    """
    根据 SNR 计算噪声方差

    SNR_db = 10 * log10(E_s / N_0)

    对于归一化符号功率 E_s = 1:
    N_0 = 1 / (10^(SNR_db/10))
    σ² = N_0 / 2 (每维方差)
    """
    snr_linear = 10 ** (snr_db / 10)
    n0 = 1 / snr_linear
    sigma = np.sqrt(n0 / 2)
    return sigma
```

**实现**:
```python
def awgn_channel(symbols: np.ndarray, snr_db: float, seed: int = None) -> np.ndarray:
    """
    AWGN 信道

    参数:
        symbols: 发送符号序列
        snr_db: 信噪比（dB）
        seed: 随机种子（保证可复现）
    """
    if seed is not None:
        np.random.seed(seed)

    sigma = calculate_noise_variance(snr_db)
    noise = sigma * (np.random.randn(len(symbols)) + 1j * np.random.randn(len(symbols)))

    return symbols + noise
```

---

### 2.7 同步（Synchronization）

**功能**: 检测帧起始位置，去除时间偏移

**算法**: 相关检测

**实现原理**:
```python
def detect_frame_start(received: np.ndarray, preamble: np.ndarray) -> int:
    """
    帧起始检测

    方法: 滑动相关
    1. 将接收信号与已知 preamble 进行相关
    2. 检测相关峰值位置
    3. 峰值位置即为帧起始

    度量: |∑ r[n] * conj(preamble[n])|²
    """
    correlation = np.abs(np.correlate(received, preamble, mode='valid'))
    peak_index = np.argmax(correlation)
    return peak_index
```

**性能要求**:
- 在 25 符号偏移下能准确检测
- SNR 12 dB 下检测误差 ≤ 1 符号

---

### 2.8 QPSK 解调（QPSK Demodulate）

**功能**: 将接收符号判决为比特流

**判决准则**: 最小欧氏距离

```python
def qpsk_demodulate(symbols: np.ndarray) -> np.ndarray:
    """
    QPSK 解调

    判决规则：
    - Re(s) > 0 → bit0 = 0, else bit0 = 1
    - Im(s) > 0 → bit1 = 0, else bit1 = 1
    """
    bits = []
    for s in symbols:
        b0 = 0 if s.real > 0 else 1
        b1 = 0 if s.imag > 0 else 1
        bits.extend([b0, b1])

    return np.array(bits, dtype=np.int8)
```

---

### 2.9 帧解析（Frame Parse）

**功能**: 从帧中提取 payload 和校验信息

**实现**:
```python
def parse_frame(frame_bits: np.ndarray) -> Tuple[np.ndarray, bool]:
    """
    帧解析

    步骤:
    1. 提取 length 字段（16 bits）
    2. 根据 length 提取 payload
    3. 提取 CRC 并验证
    4. 返回 payload 和校验结果
    """
    # 跳过 preamble (64 bits)
    length_bits = frame_bits[64:80]
    payload_length = decode_length(length_bits)

    payload = frame_bits[80:80+payload_length]
    received_crc = frame_bits[80+payload_length:80+payload_length+16]

    # CRC 校验
    computed_crc = compute_crc16(payload)
    crc_ok = np.array_equal(received_crc, computed_crc)

    return payload, crc_ok
```

---

### 2.10 信道译码（Channel Decode）

**功能**: 纠正传输错误，恢复信息比特

**算法**: Viterbi 译码

**实现要点**:
- 网格图构建
- 路径度量计算（汉明距离）
- 回溯路径

---

### 2.11 解扰（Descramble）

**功能**: 恢复扰码前的比特流

**实现**: 与扰码相同，使用相同 LFSR 种子

---

### 2.12 源解码（Source Decode）

**功能**: 将比特流恢复为 UTF-8 文本

**实现**:
```python
def source_decode(bits: np.ndarray) -> str:
    """
    将比特流解码为文本

    算法:
    1. 将比特流按 8 bits 分组
    2. 转换为字节序列
    3. UTF-8 解码为文本
    """
    # 确保比特数为 8 的倍数
    if len(bits) % 8 != 0:
        bits = bits[:-(len(bits) % 8)]

    bytes_data = np.packbits(bits.astype(np.uint8))
    return bytes_data.tobytes().decode('utf-8')
```

---

## 3. 参数设计总结

| 参数 | 值 | 说明 |
|------|-----|------|
| Preamble 长度 | 64 bits | 同步序列 |
| Length 字段 | 16 bits | 最大支持 65535 bits |
| CRC | CRC-16-CCITT | 多项式 0x1021 |
| 扰码种子 | 2026 | 固定种子 |
| 卷积码码率 | 1/2 | 约束长度 7 |
| QPSK 映射 | Gray 编码 | 星座点归一化 |
| SNR 工作点 | 12 dB | 保证无误码 |

---

## 4. 性能分析

### 4.1 QPSK 星座图

在 SNR 12 dB 下，接收符号在四个象限聚集清晰，判决边界明显，误码率接近理论值。

### 4.2 BER 曲线

BER (Bit Error Rate) 随 SNR 的变化：
- 无编码 QPSK: BER ≈ Q(√(2·SNR))
- 卷积码 (1/2): 编码增益约 3-5 dB

### 4.3 系统可靠性

在 SNR 12 dB 下：
- 卷积码译码后无误码
- CRC 校验通过率 100%
- 文本恢复率 text_match_rate = 1.0

---

## 5. 实现要点

### 5.1 模块化设计

每个模块独立实现，便于测试和调试：
- `src/source_codec.py`
- `src/scrambler.py`
- `src/channel_codec.py`
- `src/frame.py`
- `src/qpsk.py`
- `src/awgn.py`
- `src/sync.py`
- `src/metrics.py`

### 5.2 可测试性

每个模块提供独立测试函数，验证：
- 可逆性（编码-解码一致性）
- 边界条件处理
- 参数化配置

### 5.3 可复现性

- 固定随机种子（2026）
- 确定性算法实现
- 数值精度控制

---

## 6. 文件结构

```
wireless-final-project-template/
├── DESIGN.md              # 本文档
├── TEST_PLAN.md           # 测试计划
├── MOCK_TEST_REPORT.md    # Mock 测试报告
├── AI_LOG.md              # AI 辅助日志
├── main.py                # CLI 入口
├── src/
│   ├── __init__.py
│   ├── source_codec.py    # 源编码/解码
│   ├── scrambler.py       # 扰码/解扰
│   ├── channel_codec.py   # 信道编码/译码
│   ├── frame.py           # 帧封装/解析
│   ├── qpsk.py            # QPSK 调制/解调
│   ├── awgn.py            # AWGN 信道
│   ├── sync.py            # 同步模块
│   └── metrics.py         # 性能指标
├── tests/
│   ├── test_source_codec.py
│   ├── test_scrambler.py
│   ├── test_channel_codec.py
│   ├── test_frame.py
│   ├── test_qpsk.py
│   └── test_integration.py
├── results/
│   ├── received.txt       # 接收文本
│   ├── metrics.json       # 性能指标
│   ├── constellation.png  # 星座图
│   ├── ber_curve.png      # BER 曲线
│   └── sync_peak.png      # 同步峰值
├── Test.txt               # 测试输入
└── requirements.txt       # 依赖包
```

---

## 7. 设计风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 卷积码译码复杂度高 | 性能瓶颈 | 使用 NumPy 向量化实现 |
| 同步失败 | 帧丢失 | 使用长 preamble 提高相关性 |
| CRC 碰撞 | 错误检测失效 | 使用 CRC-16-CCITT 标准算法 |
| padding 处理错误 | 文本恢复失败 | 通过 length 字段精确去除 |

---

## 8. 结论

本设计文档详细描述了无线通信基带仿真系统的各模块设计、参数选择和实现方案。系统采用模块化设计，支持参数化配置，在 SNR 12 dB 下可实现无误码传输，满足课程项目要求。
