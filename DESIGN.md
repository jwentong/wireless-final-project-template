# DESIGN.md — 无线通信文件传输基带仿真系统设计文档

> 本文档依据 `PRD.md` 编写，定义系统架构、模块接口、算法选择、关键参数与预期风险，
> 作为实现（`src/`）与测试（`tests/`、`public_tests/`）的设计基线。
> 文档随 mock 测试（见 `MOCK_TEST_REPORT.md`）迭代修订，修订记录见文末附录 A。

---

## 1. 设计目标与范围

将教师 `Test.txt`（任意 UTF-8 文本）作为业务载荷，经发送端、无线信道、接收端处理后，
在 `results/received.txt` 恢复，并输出性能指标与可视化。

设计原则：

1. **模块化**：每个通信功能独立成 `src/*.py`，函数级接口与 `public_tests` 的自动发现命名对齐。
2. **可复现**：所有随机过程（噪声、衰落）由 `seed` 控制，固定 seed 输出确定。
3. **通用性**：对任意 UTF-8 文本、任意长度、任意 SNR/seed 工作，**不针对公开样例硬编码**。
4. **可解释**：每个模块的通信原理、参数、码率、纠错能力可在答辩中逐一说明。

验收基线：SNR ≥ 12 dB、AWGN、固定 seed 下，`received.txt` 与 `Test.txt` **完全一致**。

---

## 2. 系统架构总览（固定链路）

系统实现 PRD 规定的固定链路，顺序不可变：

```
                          ┌─────────────────── 发送端 (Transmitter) ───────────────────┐
Test.txt ─► Source Encode ─► Encrypt/Scramble ─► Channel Encode ─► Frame Build ─► QPSK Modulate ─┐
                                                                                                 │
                                                                                          ┌──────▼──────┐
                                                                                          │   Channel   │ (AWGN / Rayleigh / Rician)
                                                                                          └──────┬──────┘
                                                                                                 │
received.txt ◄─ Source Decode ◄─ Decrypt/Descramble ◄─ Channel Decode ◄─ QPSK Demodulate ◄─ Synchronization ◄┘
                          └─────────────────── 接收端 (Receiver) ──────────────────────┘
                                                                                                 │
                                                                                          Metrics / Plots
```

数据形态在链路中的演变：

| 阶段 | 数据类型 | 说明 |
|---|---|---|
| Test.txt | `str` (UTF-8) | 业务文本 |
| Source Encode 后 | `list[int]` bits，len % 8 == 0 | 原始 payload 比特流，长度记为 `orig_len` |
| Scramble 后 | `list[int]` bits（长度不变） | 去除连 0/连 1，便于同步与功率均衡 |
| Channel Encode 后 | `list[int]` bits（变长） | 加入冗余，长度记为 `coded_len` |
| Frame Build 后 | `list[int]` bits | 前导 + 头部 + payload + CRC + padding |
| QPSK Modulate 后 | `np.ndarray[complex]` | 单位平均功率复符号 |
| Channel 后 | `np.ndarray[complex]` | 叠加噪声/衰落，前置随机偏移 |
| 接收端逐级逆变换 | … | 最终恢复 `str` |

---

## 3. 模块划分与接口契约总表

每个模块对应一个 `src/*.py`，函数命名与 `public_tests/conftest.py` 的 `find_function` 首选名一致，
保证公开测试零适配通过。

| # | 模块文件 | 核心函数（签名） | 职责 |
|---|---|---|---|
| 1 | `src/source.py` | `source_encode(text:str)->list[int]`；`source_decode(bits:list[int])->str` | UTF-8 ↔ 比特流 |
| 2 | `src/scramble.py` | `scramble(bits, seed:int=2026)->list[int]`；`descramble(bits, seed:int=2026)->list[int]` | PN 序列扰码（可逆） |
| 3 | `src/channel_coding.py` | `channel_encode(bits, scheme="conv")->list[int]`；`channel_decode(bits, scheme="conv")->list[int]` | 前向纠错（汉明/卷积） |
| 4 | `src/framing.py` | `build_frame(payload, orig_len=None)->list[int]`；`parse_frame(frame_bits)->dict` | 帧封装/解析 |
| 5 | `src/modulation.py` | `qpsk_modulate(bits)->ndarray`；`qpsk_demodulate(symbols)->list[int]`（+BPSK/16QAM） | 比特 ↔ 复符号 |
| 6 | `src/channel.py` | `awgn(symbols, snr_db=12, seed=2026)->ndarray`（+`rayleigh`/`rician`） | 无线信道 |
| 7 | `src/synchronization.py` | `synchronize(received, preamble)->int` | 帧起点检测 |
| 8 | `src/equalizer.py` | `zf_equalize(rx, h)`；`mmse_equalize(rx, h, snr_db)` | 信道均衡（提高） |
| 9 | `src/metrics.py` | `ber(a,b)`；`fer(...)`；`text_match_rate(s1,s2)`；`crc16(bits)` | 性能指标 |
| 10 | `src/pipeline.py` | `transmit(text, cfg)`；`receive(symbols, cfg)`；`run_end_to_end(cfg)` | 端到端编排 |

接口设计要点（来自对 `public_tests` 的逐行分析）：

- `scramble`/`awgn` 必须接受**关键字参数** `seed=` / `snr_db=`（测试用 `call_with_fallback` 先带 kwargs 调用）。
- `synchronize` 必须接受**任意** `preamble`（符号序列），用通用互相关，不得内部写死前导。
- `channel_encode`∘`channel_decode` 在**无噪声**下必须完全可逆（`TC-T-008`）。
- `build_frame` 返回序列化比特序列（比 payload 长）；`parse_frame` 返回 `dict`，含 `payload` 与 `length`。

---

## 4. 各模块详细设计

### 4.1 源编码 Source Encode / Source Decode（`src/source.py`）

- **原理**：UTF-8 是变长编码（中文 3 字节/字）。`source_encode` 将 `text.encode("utf-8")` 得到字节序列，
  每字节按 **MSB-first** 展开为 8 bit，拼成比特流；`source_decode` 逆过程，每 8 bit 还原一字节再 `bytes.decode("utf-8")`。
- **关键参数**：位序 MSB-first；输出长度恒为 8 的整数倍（满足 `TC-T-004`）。
- **边界处理**：接收端用帧头 `orig_len` 截断 padding，保证字节边界对齐；解码失败（非法 UTF-8）时按系统边界抛错并在 metrics 记 `checksum_pass=false`。

### 4.2 扰码 Scramble / Descramble（`src/scramble.py`，对应 PRD 的 Encrypt/Scramble）

- **原理**：用**线性反馈移位寄存器（LFSR）**生成伪随机（PN）序列，与输入比特逐位 **XOR**。XOR 自反，
  同一 PN 序列再异或即还原，故 `descramble == scramble`（同 seed）。
- **作用**：打散长连 0/连 1，避免调制后出现长直流、利于同步与定时恢复；同时充当 PRD 要求的"可逆加扰/加密"。
- **关键参数**：PN 由 `seed` 初始化 LFSR 状态；本质生成与 `bits` 等长的密钥流。长度不变，便于在 `orig_len` 上对齐。
- **可逆性**：`descramble(scramble(b, seed), seed) == b`（满足 `TC-T-007`）。

### 4.3 信道编码 Channel Encode / Channel Decode（`src/channel_coding.py`）

提供两种方案，由 `scheme` 选择，默认 **卷积码**（主链路），汉明码作为对比基线。

**(a) 汉明码 Hamming(7,4)**（基线）
- 每 4 信息位生成 3 校验位 → 7 位码字，码率 4/7，最小汉明距离 3，**可纠 1 位错/码字**。
- 译码用伴随式（syndrome）查表定位错误位翻转。

**(b) 卷积码 Convolutional (K=7, rate 1/2)**（默认/主链路，提高模块之一）
- 生成多项式 `G1=171_oct`, `G2=133_oct`，约束长度 K=7（64 状态）。每输入 1 bit 输出 2 bit。
- 发送端在信息位后附加 **6 个 0 尾比特（zero-tail）**，使编码器回到全零态，便于 Viterbi 终止。
- 译码用 **Viterbi 算法（硬判决）**：在网格（trellis）上按汉明距离做加比选（ACS），回溯最优路径。
- **无噪声可逆性**：零尾终止 + 唯一最大似然路径，无错时回溯必得原信息位（满足 `TC-T-008`）。
- **纠错增益**：相比无编码，在相同 BER 下可降低所需 Eb/N0 ~4–5 dB（编码增益），是低 SNR 鲁棒性的主要来源。

对外契约：`channel_encode(bits)` 接收 `orig` 比特返回 `coded`；`channel_decode(coded)` 返回信息比特
（长度可能因 padding/tail 略长，pipeline 用 `orig_len` 截断）。

### 4.4 帧结构 Frame Build / Frame Parse（`src/framing.py`）

帧格式（比特域，MSB-first）：

| 字段 | 长度 (bit) | 内容 | 用途 |
|---|---|---|---|
| Preamble | 26 | Barker-13 序列的 QPSK 比特表示 | 同步（互相关找帧起点） |
| orig_len | 96 (32×3) | 源编码输出、扰码前的**原始** payload bit 数；**3× 重复保护**（v0.2） | 接收端多数判决恢复，去 padding 还原 UTF-8（PRD 的 length 语义） |
| coded_len | 96 (32×3) | 进帧 payload 的 bit 数（信道编码后）；**3× 重复保护**（v0.2） | 接收端多数判决恢复，定位 payload 与 CRC 边界 |
| Payload | coded_len | 扰码 + 信道编码后的比特 | 业务载荷 |
| CRC-16 | 16 | CRC-16-CCITT（多项式 0x1021），覆盖 [orig_len‖coded_len‖Payload] | 错误检测 → `checksum_pass` |
| Padding | 0 或若干 | 补 0 至总比特数为偶数 | QPSK 每符号 2 bit 对齐 |

- **header 保护（v0.2，mock 修订）**：`orig_len`/`coded_len` 采用 **3× 重复 + 接收端多数判决**。mock 测试发现：PRD 链路顺序下信道编码在帧封装之前，length 字段不受 FEC 保护，低 SNR 单比特错误即破坏 framing（见 `MOCK_TEST_REPORT.md`）；重复保护以每帧 +128 bit 的极小开销换取对单比特错误的免疫。
- **Preamble 设计**：取 Barker-13 `[+1,+1,+1,+1,+1,-1,-1,+1,+1,-1,+1,-1,+1]`，将 `+1→比特 00`、`-1→比特 11`，
  共 26 bit；经 QPSK 调制后得到 13 个落在主对角线的符号，**自相关旁瓣 ≤ 1**，相关峰尖锐，利于同步。
- **build_frame(payload, orig_len=None)**：`orig_len` 缺省时取 `len(payload)`（使 `public_tests` 直接传随机 payload 也成立）；
  pipeline 调用时显式传入真实原始长度。返回序列化比特列表。
- **parse_frame(frame_bits)**：跳过 preamble，读 `orig_len`/`coded_len`，截取 `Payload`，校验 CRC，
  返回 `{"payload": <coded payload bits>, "length": orig_len, "coded_len": ..., "crc_pass": bool}`。
- **可逆性**：`parse_frame(build_frame(p))["payload"][:len(p)] == p`，`length == len(p)`（满足 `TC-T-005/006/011`）。

### 4.5 调制 QPSK Modulate / Demodulate（`src/modulation.py`）

- **QPSK Gray 映射**（PRD 强制）：每 2 bit → 1 符号，

  | bits | 符号 | 象限 |
  |---|---|---|
  | 00 | (1+j)/√2 | I |
  | 01 | (−1+j)/√2 | II |
  | 11 | (−1−j)/√2 | III |
  | 10 | (1−j)/√2 | IV |

  Gray 编码使相邻象限只差 1 bit，降低误符号到误比特的传播。归一化因子 1/√2 使**符号平均功率 = 1**（满足 `TC-T-009` 的 0.8–1.2 功率检查）。
- **padding**：若比特数为奇数，末尾补 1 个 0 凑齐；接收端由帧头 `orig_len`/`coded_len` 去除（满足 `TC-T-011`）。
- **解调**：最小欧氏距离判决，等价于按 I、Q 两路符号实部/虚部**符号位**独立判决（QPSK = 两路正交 BPSK）。
- **扩展**：同文件提供 `bpsk_modulate/demodulate`、`qam16_modulate/demodulate`（16-QAM Gray，平均功率归一化），用于多调制对比与自适应（提高模块）。

### 4.6 信道 Channel（`src/channel.py`）

- **AWGN（必做）**：给定符号功率 `Ps`（QPSK 归一化后 = 1）与 `snr_db`，复高斯噪声平均功率
  `Pn = Ps / 10^(snr_db/10)`，实部/虚部各 `Pn/2`：
  `noise = sqrt(Pn/2) * (randn + j·randn)`，`rng = np.random.default_rng(seed)` 保证可复现（满足 `TC-T-012`）。
- **SNR 定义**：接收端**符号平均功率 / 复噪声平均功率**，单位 dB（与 PRD 一致）。
- **Eb/N0 换算**：QPSK 每符号 2 bit，`Es/N0 = SNR`，`Eb/N0 = SNR / log2(4) = SNR / 2`，
  即 `Eb/N0(dB) = SNR(dB) − 10·log10(2) ≈ SNR(dB) − 3.01 dB`。BER 理论曲线据此对照。
- **Rayleigh / Rician 衰落（提高）**：乘性复增益 `h`。Rayleigh：`h = (randn + j·randn)/√2`（包络瑞利分布）；
  Rician：`h = sqrt(K/(K+1)) + sqrt(1/(K+1))·(randn+j·randn)/√2`（含直射径，K 为莱斯因子）。衰落后再叠加 AWGN。

### 4.7 同步 Synchronization（`src/synchronization.py`）

- **原理**：接收符号序列与已知 preamble 符号做**归一化滑动互相关**
  `R[d] = |Σ_k received[d+k]·conj(preamble[k])| / (‖window‖·‖preamble‖)`，
  取 `argmax_d R[d]` 作为帧起点 `start_index`。Barker 前导的尖锐自相关使峰值明显，旁瓣低。
- **覆盖范围**：可检测 0–128 符号随机前置偏移；SNR ≥ 12 dB AWGN 下起点误差 ≤ 1 符号（满足 `TC-T-013` 与 PRD 同步口径）。
- **接口**：`synchronize(received, preamble)` 接受任意 preamble 数组，返回 `int` 起点；同时可返回相关曲线供 `sync_peak.png` 绘制。
- **后续**：找到起点后截取 `preamble_len` 之后的符号送解调；相关峰值序列输出到 metrics/plots。

### 4.8 均衡 Equalization（`src/equalizer.py`，提高模块）

- **场景**：Rayleigh/Rician 下接收符号被复增益 `h` 旋转/缩放，需均衡恢复。
- **ZF（迫零）**：`ŝ = rx / h`，完全抵消信道但在 `|h|` 小时放大噪声。
- **MMSE（最小均方误差）**：`ŝ = conj(h)·rx / (|h|² + 1/SNR)`，在噪声与干扰间折中，低 SNR 优于 ZF。
- **对比实验**：衰落信道下 BER（无均衡 / ZF / MMSE）三条曲线，体现均衡价值。

### 4.9 指标 Metrics（`src/metrics.py`）

- `ber(tx_bits, rx_bits)`：逐位比较，`错误位数 / 总位数`。
- `fer(...)`：帧错误率（CRC 失败或文本不一致即记一帧错）。
- `text_match_rate(s_ref, s_out)`：按字符（或字节）一致比例；完全一致为 1.0（`TC-T-015`）。
- `crc16(bits)`：CRC-16-CCITT，用于 `checksum_pass`。
- 输出 `results/metrics.json`，字段：`snr_db, seed, modulation, channel, payload_bits, ber, fer, text_match_rate, checksum_pass, sync_start_index`（满足 `TC-T-014`）。

### 4.10 编排 Pipeline & CLI（`src/pipeline.py` + `main.py`）

- **发送 `transmit(text, cfg)`**：`source_encode → scramble → channel_encode → build_frame(coded, orig_len) → modulate`，返回符号。
- **信道**：按 `cfg.channel` 施加 AWGN/衰落，并在帧前插入随机偏移（由 seed 决定）。
- **接收 `receive(symbols, cfg)`**：`synchronize → (均衡) → demodulate → parse_frame → channel_decode → descramble → 取前 orig_len → source_decode`。
- **`main.py`**：`argparse` 解析 `--input --output --snr --seed --mod --channel`，**非交互**，生成 `received.txt`、`metrics.json` 与图表，正常退出码 0（满足 `TC-T-014~017`）。

---

## 5. 关键参数表

| 参数 | 取值 | 说明 |
|---|---|---|
| 调制 | QPSK（默认） | Gray 映射，单位功率；可选 BPSK/16-QAM |
| 信道编码 | 卷积码 K=7 (171,133) rate 1/2（默认） | 可选 Hamming(7,4) |
| 前导 | Barker-13 → 26 bit / 13 符号 | 同步互相关 |
| length 字段 | orig_len/coded_len 各 32 bit，帧内 3× 重复保护（各 96 bit） | 大端；防溢出 + 防单比特错（v0.2） |
| 校验 | CRC-16-CCITT (0x1021) | checksum_pass |
| SNR | 默认 12 dB，可配 | 符号功率/噪声功率 |
| seed | 默认 2026 | 复现 |
| 同步偏移范围 | 0–128 符号 | 误差 ≤ 1 符号 |

---

## 6. 提高模块设计（Level 3）

1. **卷积码 + Viterbi 译码**（默认主链路）：相对汉明码/无编码，给出更陡的 BER-SNR 曲线，量化编码增益。
2. **Rayleigh/Rician 衰落 + ZF/MMSE 均衡**：扩展信道模型，对比 AWGN，展示均衡前后 BER 改善。
3. **多调制对比 + 自适应**：BPSK/QPSK/16-QAM 同图 BER-SNR 对比；按估计 SNR 自适应选调制（高 SNR 用 16-QAM 提速，低 SNR 退回 QPSK/BPSK 保可靠）。

---

## 7. 预期风险与对策（mock 前的初判，详见 MOCK_TEST_REPORT.md）

| 风险 | 影响 | 对策 |
|---|---|---|
| 卷积码尾比特/截断处理不当 → 无噪声不可逆 | `TC-T-008` 失败 | zero-tail 终止 + 单元测试覆盖边界长度 |
| `length` 字段语义混淆（原始 vs 编码后） | 接收端去 padding 错误、乱码 | 帧头同时存 `orig_len` 与 `coded_len`，职责分离 |
| 同步在低 SNR/大偏移下峰值误判 | 帧起点错位 → 整帧乱码 | 归一化互相关 + Barker 尖峰；输出相关曲线复核 |
| QPSK 功率未归一化 | `TC-T-009` 功率检查失败、SNR 定义不符 | 1/√2 归一化，单测断言平均功率≈1 |
| 针对公开样例硬编码 | `TC-T-020` 反作弊失败、隐藏测试崩 | 全链路通用实现，禁止文件直拷 |
| **帧头 length 字段不受 FEC 保护**（mock 发现） | 低 SNR 单比特错 → 整帧解析失败 | **3× 重复 + 多数判决保护 length**（v0.2 已修订并验证，见 MOCK_TEST_REPORT.md） |

---

## 8. 结果分析框架（数值在实验后回填，见 REPORT.md / 附录 B）

- **QPSK 星座图**：高 SNR 下四个象限点紧凑、可清晰区分；SNR 降低时噪声云扩散、越过判决边界即产生误比特——直观解释误码来源。
- **BER / text_match_rate 随 SNR 变化**：SNR ≥ 12 dB 时 BER→0、text_match_rate=1.0；SNR 下降 BER 上升，卷积码曲线显著优于无编码，体现编码增益。
- **失败/误码原因分析**：低 SNR 下**同步**与**信道译码**最先失效——同步误判导致帧错位（整帧乱码），其次噪声超过纠错能力导致残余误码。排查顺序：同步峰值 → CRC → BER → 星座扩散程度。

---

## 附录 A：设计修订记录（随 mock 测试更新）

- v0.1（初版）：本文档，mock 前设计基线。
- v0.2（mock 修订）：mock 测试发现帧头 `length` 字段在 PRD 链路顺序下不受 FEC 保护，低 SNR 单比特错误即破坏 framing；**修订为对 `orig_len`/`coded_len` 做 3× 重复 + 多数判决保护**，并经 `mock/mock_fix_verify.py` 验证（header 损坏率 6 dB 由 11→1、4 dB 由 18→6）。详见 `MOCK_TEST_REPORT.md`。
