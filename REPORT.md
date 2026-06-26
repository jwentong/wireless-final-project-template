# 无线通信技术期末项目报告

> 基于 AI 辅助编程的无线通信文件传输基带仿真系统  
> 正文内容输出文件（封面、评分表、诚信承诺书沿用 Word 模板，不在此文件中）

---

## 摘要

本项目实现无线通信文件传输基带仿真系统，将 UTF-8 文本 Test.txt 经固定链路传输并恢复为 received.txt。系统包含源编码、PN 扰码、(3,1) 重复码、帧封装（前导+CRC-16）、Gray QPSK 调制、AWGN 信道及前导互相关同步。经 AI 辅助开发与 mock 测试修订设计后，6 项 mock 与 22 项公开测试均通过。SNR=12 dB、seed=2026 时 BER/FER 为 0，文本恢复率 1.0，并生成 metrics.json 与性能图表。结果表明系统在中等信噪比下可可靠传输文本，满足 PRD 验收要求。

## 关键词

无线通信；QPSK；AWGN；帧同步；信道编码；AI 辅助编程

---

## 1 项目概述

### 1.1 项目背景与目标

无线通信技术课程期末考核采用项目制替代传统闭卷考试，要求学生在 PRD 与公开测试约束下，使用 AI 辅助编程完成一套可运行的无线通信基带仿真系统。本项目要解决的问题是：将教师提供的 UTF-8 文本文件 `Test.txt`（约 300 字课程描述）作为业务载荷，经过完整的发送端处理、无线信道传输和接收端恢复流程，在接收端输出与原文一致的 `results/received.txt`，并给出可复现的性能指标与可视化结果。

具体目标包括：（1）实现 PRD 规定的固定顺序端到端链路，覆盖源编码、扰码、信道编码、组帧、QPSK 调制、AWGN 信道、帧同步、解调译码与文件恢复；（2）支持统一命令行入口与固定随机种子，便于公开测试与隐藏验证复现；（3）输出 `metrics.json` 及星座图、BER-SNR 曲线、同步相关峰值图等实验产物；（4）通过 mock 测试驱动设计修订，规范记录 AI 辅助开发过程，并能解释各模块的通信原理与实现逻辑。

### 1.2 PRD 关键需求理解

**固定系统链路。** PRD 要求所有学生实现同一条链路，顺序为：Source Encode → Encrypt/Scramble → Channel Encode → Frame Build → QPSK Modulate → Channel → Synchronization → QPSK Demodulate → Channel Decode → Decrypt/Descramble → Source Decode → received.txt → Metrics/Plots。本系统严格按此顺序在 `src/transmitter.py` 与 `src/receiver.py` 中编排，QPSK 为必做调制方式，AWGN 为必做信道模型。

**统一命令行接口。** 系统必须支持如下验收命令：

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

`main.py` 通过 `argparse` 解析输入/输出路径、SNR、随机种子、调制方式与信道类型等参数，一次运行完成发送、信道仿真、接收与结果落盘。

**必需输出文件与图表。** 运行后必须生成 `results/received.txt` 与 `results/metrics.json`；后者记录 SNR、BER、FER、文本一致率（text_match_rate）、随机种子及同步起点等关键字段。可视化方面，PRD 要求星座图、BER 曲线、同步峰值图三者至少完成两项；本系统三类图表均已生成。

**验收标准理解。** 功能上，各模块需满足 PRD 最低边界：UTF-8 源编解码、可逆扰码、至少一种信道编码、含前导/长度/载荷/校验的帧结构、Gray QPSK 硬判决解调、基于前导的帧起点检测（不得假设接收端已知起点）。工程上，须支持不同 SNR、seed 及同步偏移的鲁棒运行，禁止硬编码公开测试或绕过链路直接复制文件。文档上，须提交 `DESIGN.md`、`TEST_PLAN.md`、`MOCK_TEST_REPORT.md`、`AI_LOG.md` 及完整代码与测试结果。

**本系统设计选型（在 PRD 允许范围内）。** 源编码采用 UTF-8 字节转比特流并在接收端按 `length` 字段截断；扰码采用 seed 驱动的 PN 序列 XOR；(3,1) 重复码配合多数表决译码提供抗噪能力；帧结构为 32 bit 前导（0xAA55AA55）+ 16 bit 长度 + 载荷 + CRC-16/CCITT；同步采用前导互相关峰值检测，支持 0～128 符号随机前置偏移。

### 1.3 GitHub 提交信息


| 字段              | 内容                                                                                                                               |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| 学号              | 【待填写】                                                                                                                            |
| 姓名              | 【待填写】                                                                                                                            |
| GitHub 用户名      | DaviZhi                                                                                                                          |
| 学生 Fork 仓库地址    | [https://github.com/DaviZhi/wireless-final-project-template.git](https://github.com/DaviZhi/wireless-final-project-template.git) |
| 教师原仓库           | [https://github.com/jwentong/wireless-final-project-template](https://github.com/jwentong/wireless-final-project-template)       |
| 提交分支            | main                                                                                                                             |
| Pull Request 编号 | #3（https://github.com/jwentong/wireless-final-project-template/pull/3） |
| 最终 commit       | `ad457061f37b21402ae9877963aeb3a6a1c298a8`（Add Level 3 FEC pipeline with convolutional code and comparison plots）                |


**提交清单（PR 模板勾选项）。** 本项目已包含并提交以下交付物：

- `DESIGN.md`：系统架构、模块接口、关键参数与实验分析
- `TEST_PLAN.md`：公开测试与 mock 测试用例规划
- `MOCK_TEST_REPORT.md`：6 项 mock 场景验证结果与设计修订记录
- `AI_LOG.md`：AI 辅助编程过程记录
- `main.py`：统一 CLI 入口
- `src/`：各功能模块实现
- `tests/`：mock 与 Level 3 单元测试
- `results/`：`received.txt`、`metrics.json` 及性能图表

**公开测试情况。** 本地执行 `pytest public_tests -q`，22 项公开测试全部通过。

---

## 2 系统设计与架构

### 2.1 总体架构与固定链路

本系统采用模块化、流水线式架构，严格遵循 PRD 规定的固定处理顺序。发送端将业务文本逐步转换为比特流、组帧并调制为 QPSK 符号；信道模块对符号序列施加 AWGN 噪声；帧前另插入 0～128 个随机噪声符号作为前置偏移；接收端通过前导互相关完成帧同步，再依次解调、解帧、译码与解扰，最终恢复 UTF-8 文本。

端到端数据流如下（箭头表示处理顺序）：

Test.txt → 源编码 → 扰码 → 信道编码 → 组帧 → QPSK 调制 → AWGN 信道（含随机前置偏移）→ 帧同步 → QPSK 解调 → 解帧 → 信道译码 → 解扰 → 源解码 → received.txt → 指标计算与图表生成

各阶段职责简述如下。

（1）源编码：将 UTF-8 文本按字节展开为比特流，每字节 8 bit、高位先发（MSB 优先）。

（2）扰码：使用 seed 驱动的 PN 序列对载荷比特逐位异或，增强比特分布随机性，解扰为相同操作。

（3）信道编码：采用 (3,1) 重复码，每位重复 3 次，编码率 1/3，接收端以多数表决译码。

（4）组帧：在编码载荷前加入 32 bit 前导、16 bit 长度字段，末尾附加 CRC-16 校验。

（5）QPSK 调制：按 Gray 编码将比特两两映射为复符号，必要时在帧尾补 0 使比特数为偶数。

（6）信道：对符号序列叠加复高斯白噪声；发送端另在帧前插入 0～128 个随机噪声符号（复高斯，单位功率），模拟未知帧起点。

（7）接收恢复：互相关检测帧起点 → 硬判决解调 → 解析帧结构与 CRC → 重复码译码 → 解扰 → 按 length 字段截断有效比特并解码为文本。

### 2.2 逻辑分层与代码组织

系统按"入口层—流水线层—信号处理层—辅助层"四层组织，各层职责清晰、接口单一，便于单元测试与 mock 验证。

第一层为入口层，由 main.py 承担。负责解析命令行参数（输入输出路径、SNR、seed、调制方式、信道类型等），调用发送端与接收端流水线，并将 received.txt、metrics.json 及性能图表写入 results 目录。

第二层为流水线层，由 src/transmitter.py 与 src/receiver.py 承担。发送端按固定顺序串联各编码与调制模块；接收端按固定顺序完成同步、解调、解帧与译码，并汇总部分性能指标。

第三层为信号处理层，各功能独立成模块：source.py（源编解码）、scramble.py（扰码）、channel_coding.py（信道编解码）、framing.py（组帧与解帧）、modulation.py（QPSK 调制解调）、channel.py（AWGN 及扩展 Rayleigh 信道）、synchronization.py（帧同步）。

第四层为辅助层：metrics.py 负责指标计算与 JSON 落盘；plots.py 负责星座图、BER 曲线与同步峰值图；utils.py 提供比特转换、CRC 计算与随机数封装等公共工具。

主要源文件与功能对应关系见表 2-1（粘贴 Word 时可转为表格）。

表 2-1  主要源文件与功能对应

文件名：main.py；功能：CLI 入口、流程编排、结果落盘

文件名：transmitter.py；功能：发送端流水线

文件名：receiver.py；功能：接收端流水线

文件名：source.py；功能：UTF-8 源编解码

文件名：scramble.py；功能：PN 序列扰码与解扰

文件名：channel_coding.py；功能：(3,1) 重复码编解码（扩展支持卷积码）

文件名：framing.py；功能：帧组装、解析与 QPSK 尾比特剥离

文件名：modulation.py；功能：Gray QPSK 调制与硬判决解调

文件名：channel.py；功能：AWGN 信道仿真

文件名：synchronization.py；功能：前导互相关帧同步

文件名：metrics.py / plots.py；功能：性能指标与可视化输出

### 2.3 数据流与关键字段

各阶段数据形态随处理深度逐步变化：输入为 UTF-8 字符串；源编码后为 0/1 比特列表（长度必为 8 的整数倍）；扰码后与源编码等长；信道编码后长度扩大为原来的 3 倍；组帧后在载荷前后增加前导、长度与 CRC 字段；QPSK 调制后变为复数符号数组；经信道后接收符号序列含有随机前置噪声符号；最终恢复为 UTF-8 文本。

其中 length 字段为 PRD 统一口径的关键设计点。该字段记录源编码后、扰码前的载荷比特数（payload_bits），以 16 bit 无符号整数、大端比特序写入帧头。接收端在解扰后仅取前 length 个比特送入源解码，从而正确剥离 QPSK 调制在帧尾可能引入的 padding 比特，避免恢复乱码。以 Test.txt（约 300 字中文）估算，源编码约 1500～1600 bit（实测 payload_bits = 1544），重复码编码后约 4600 bit，加上 64 bit 帧头尾固定字段后，QPSK 映射约 2300 余个符号。

随机种子分工同样影响可复现性。全局参数 seed（默认 2026）作为主种子，各子模块按固定规则派生：扰码 LFSR 初态直接由 seed 映射；AWGN 噪声使用 numpy.random.default_rng(seed)；帧前随机偏移使用 default_rng(seed + 1)，在 0～128 间均匀采样；BER 曲线各 SNR 扫描点使用独立派生种子。同一组参数下，端到端输出完全可复现，满足公开测试与隐藏验证要求。

### 2.4 各功能模块设计

#### 2.4.1 源编解码模块

通信原理：将业务层字符信息转换为物理层可处理的二进制比特流，是数字通信链路的起点与终点。

实现方案：读取 UTF-8 文本的字节流，按 MSB 优先逐位展开，不额外添加长度头（长度由帧结构承载）。解码时根据 length 字段取前 N 个有效比特，按 8 bit 一组还原字节并 UTF-8 解码。

核心接口：source_encode(text) 返回比特列表；source_decode(bits, num_bits) 按有效比特数截断后还原文本。

#### 2.4.2 扰码与解扰模块

通信原理：扰码打乱比特统计特性，避免长串 0/1 影响同步与调制性能，同时不增加带宽开销。

实现方案：采用 16 级线性反馈移位寄存器（LFSR）生成 PN 序列，本原多项式为 x^16 + x^14 + x^13 + x^11 + 1，初态由 seed 映射为非全零 16 bit 值。发送端载荷比特与 PN 序列逐位异或；接收端以相同 seed 重新生成 PN 序列并再次异或，即可恢复原始比特。

核心接口：scramble(bits, seed) 与 descramble(bits, seed)，二者互为逆操作。

#### 2.4.3 信道编解码模块

通信原理：信道编码通过冗余比特换取抗噪能力，降低无线信道误码对业务恢复的影响。

实现方案：基础链路采用 (3,1) 重复码，编码率 R = 1/3。编码规则为每位比特重复 3 次；译码时对每 3 个接收比特做多数表决（3 取 2），每组最多可纠正 1 个比特错误。该方案实现简单、调试直观，在 SNR = 12 dB 下对数千比特载荷可提供充足纠错余量。Level 3 扩展另实现卷积码与 Viterbi 译码，通过 --fec conv 参数切换，用于对比实验，不替代基础重复码链路。

核心接口：channel_encode(bits) 与 channel_decode(bits)，扩展模式下增加 mode 参数选择编码方案。

#### 2.4.4 帧结构与校验模块

通信原理：帧结构将连续比特流划分为可识别的数据单元，前导序列用于同步，长度字段标识载荷范围，校验字段用于错误检测。

帧结构（按比特顺序拼接）：

字段一：Preamble，32 bit，固定模式 0xAA55AA55，经 QPSK 映射为 16 个已知符号，供接收端互相关检测。

字段二：Length，16 bit，记录源编码比特数 payload_bits，大端编码。

字段三：Payload，变长，为信道编码后的比特流。

字段四：CRC-16，16 bit，对源编码原始比特（扰码前）按 CRC-16/CCITT 标准（多项式 0x1021，初值 0xFFFF）计算。

QPSK 尾比特处理：若帧比特总数为奇数，发送端在末尾补 1 个 0 再调制；接收端解调后先剥离可能多余的尾 0，再解析各字段，最终在源解码前按 length 截断，双重保障避免 padding 污染业务数据。

核心接口：build_frame 完成组帧并返回含 bits 键的字典；parse_frame 完成解帧并返回 length、payload、crc 及 checksum_pass 等字段。

#### 2.4.5 QPSK 调制与解调模块

通信原理：QPSK 在每个符号周期携带 2 bit 信息，频谱效率高于 BPSK，是数字通信中常用的恒包络调制方式。

映射方案（Gray 编码，符号能量归一化因子 1/√2）：

比特对 00 → 符号 (1+j)/√2；01 → (-1+j)/√2；11 → (-1-j)/√2；10 → (1-j)/√2。

每组比特高位对应同相分量 I，低位对应正交分量 Q，与课程测试向量一致。接收端采用硬判决：根据 I、Q 符号判断所属象限，再按 Gray 逆映射还原比特对。

核心接口：qpsk_modulate(bits) 返回复数符号数组；qpsk_demodulate(symbols) 返回硬判决比特列表。

#### 2.4.6 AWGN 信道模块

通信原理：加性高斯白噪声信道是分析数字通信系统性能的基础模型，噪声在时域和频域均呈平坦分布。

实现方案：接收符号 y = x + n，其中 n 为复高斯噪声，I/Q 分量独立、均值为 0。CLI 参数 snr_db 定义为 Es/N0（每符号能量与噪声功率谱密度之比）。在 QPSK 符号平均功率归一化为 1 的条件下，按 SNR 线性值计算噪声方差并叠加。固定 seed 时噪声序列完全可复现。

核心接口：awgn(symbols, snr_db, seed) 返回加噪后的符号数组。

#### 2.4.7 帧同步模块

通信原理：实际接收中帧起点未知，需利用前导序列的已知模式，通过相关运算在接收序列中搜索帧起始位置。

实现方案：（1）发送端在完整帧符号前插入 offset 个随机噪声符号，offset 由 seed+1 决定，取值 0～128。（2）接收端将已知前导符号序列与接收序列做滑动归一化互相关。（3）相关峰值所在位置即为帧起点 sync_start_index，允许 ±1 符号误差。检测完成后从该位置截取后续符号进入解调译码流程。

核心接口：detect_frame_start 返回帧起点索引；synchronize 返回同步索引、相关序列及对齐后的符号。

#### 2.4.8 性能指标与图表输出

系统每次 CLI 运行后输出 metrics.json，记录本次实验的关键参数与结果。主要字段包括：snr_db（信噪比）、seed（随机种子）、modulation（调制方式）、channel（信道类型）、payload_bits（源编码比特数）、ber（误比特率）、fer（帧错误率）、text_match_rate（文本一致率）、checksum_pass（CRC 是否通过）、sync_start_index（同步起点）、eb_n0_db（比特信噪比）、coding_rate（编码率）等。

可视化输出三类图表：constellation.png 展示接收符号散点与理想星座点；ber_curve.png 展示 SNR 从 0 至 14 dB（步进 2 dB）下的 BER 或文本恢复率变化；sync_peak.png 展示前导互相关峰值及检测位置。三类图表均已实现，满足 PRD"至少两项"的要求。

### 2.5 端到端流水线接口

发送端流水线 run_transmitter(text, seed) 完成从文本到发射符号的全部处理，返回发射符号数组 tx_symbols 及元信息 meta。meta 中包含 payload_bits、前导符号 preamble_symbols、帧比特流 frame_bits、随机偏移量 offset 等调试与接收端同步所需字段。

接收端流水线 run_receiver(rx_symbols, seed, preamble_symbols, original_text) 完成从接收符号到恢复文本的全部处理，返回恢复文本及局部指标字典。接收端内部依次调用同步、解调、解帧、信道译码、解扰、CRC 校验与源解码，并计算 ber 与 text_match_rate。

入口程序 main.py 将上述两条流水线与信道仿真、指标落盘、图表生成串联为一次完整实验，支持教师规定的统一验收命令，无需交互式输入。

### 2.6 关键参数汇总

表 2-2  系统关键设计参数（粘贴 Word 时可转为表格）

调制方式：QPSK Gray 编码（PRD 强制）

符号归一化：1/√2，单位平均符号功率

信道模型：AWGN（基础必做）；Rayleigh 衰落（Level 3 扩展）

默认 SNR：12 dB

默认 seed：2026

扰码方式：16 级 LFSR，PN 序列 XOR

信道编码：(3,1) 重复码，编码率 1/3，多数表决译码

前导序列：32 bit，模式 0xAA55AA55，对应 16 个 QPSK 符号

长度字段：16 bit 大端无符号整数

校验方式：CRC-16/CCITT，覆盖源编码比特

随机前置偏移：0～128 个噪声符号

同步容差：±1 符号

BER 曲线扫描：SNR 0、2、4、…、14 dB，每次运行自动生成

上述参数在 DESIGN.md 中有完整记录，mock 测试阶段已对帧尾 padding、同步边界、CRC 覆盖范围等关键语义完成验证与修订（DESIGN v0.2 → v0.3），为后续实现与测试提供了稳定的设计基线。

---

## 3 Mock 测试与设计修订

### 3.1 Mock 测试概述与工程定位

按照 PRD 推荐的工程流程（PRD → DESIGN.md → TEST_PLAN.md → Mock 测试 → 代码实现 → 公开测试），本项目在 src/ 各模块实现完成后、提交公开验收之前，先执行 Mock 测试验证设计方案的可行性。Mock 测试不替代公开测试，而是针对帧结构、同步边界、padding 语义、信道编解码与随机种子复现等关键设计假设做定向验证，尽早暴露接口不一致或语义歧义问题。

Mock 测试用例来源于 TEST_PLAN.md 中规划的 MK-001～MK-006 六个场景，由 tests/test_mock_scenarios.py 统一实现。执行命令为：

pytest tests/test_mock_scenarios.py -v

六个场景全部通过（6/6），测试日期为 2026-06-24。基于 Mock 结果，项目将 DESIGN.md 从 v0.2 修订至 v0.3，并在代码中完成相应修复后再进入公开测试阶段。

### 3.2 Mock 测试场景与结果

表 3-1 汇总六个 Mock 场景的目的、输入条件、通过准则与测试结果。

| Mock 编号 | 测试场景 | 输入与步骤 | 通过准则 | 测试结果 |
|-----------|----------|------------|----------|----------|
| MK-001 | 帧字段手工推演 | 短文本「测试」经源编码、扰码、重复码编码后组帧 | 帧比特总长为 32+16+N+16；前导与 0xAA55AA55 一致 | 通过 |
| MK-002 | 奇数 payload 的 QPSK padding | 255 bit 全 1 载荷组帧，帧尾补 0 后调制 | 解帧后按 length=255 截断，无多余尾比特 | 通过 |
| MK-003 | 同步三档 offset | offset 分别为 0、25、128 符号的前缀 + 前导 + 载荷 | 检测误差 ≤1 符号 | 通过（三档均满足） |
| MK-004 | 重复码 1 bit 纠错 | 5 bit 随机序列编码后翻转第 2 个 coded bit | 多数表决译码后与原始一致 | 通过 |
| MK-005 | 多 seed AWGN 可复现 | seed=2026、2027、9999 各运行 AWGN 两次 | 同 seed 下噪声输出完全一致 | 通过 |
| MK-006 | CRC-16 源比特校验 | 已知源编码比特流计算与校验 CRC | 正确比特流校验通过；篡改 1 bit 后失败 | 通过 |

### 3.3 发现的问题与设计修订

Mock 测试发现 3 项问题，均已修复并回写 DESIGN.md（v0.2→v0.3），见表 3-2。

| 编号 | 问题描述 | 处理措施 | 状态 |
|------|----------|----------|------|
| D1 | QPSK 帧尾补 0 致 CRC 错位 | parse_frame 增加尾比特剥离 | 已修复 |
| D2 | parse_frame 需兼容 dict 入参 | 自动提取 bits/frame 键 | 已修复 |
| D4 | 长载荷下同步伪相关峰 | 归一化互相关 + 限制搜索窗口 + 前缀改噪声符号 | 已修复 |

主要文档修订：§4.4 补充 padding 剥离与 dict 入参；§7 将风险 R3 标为已缓解。Mock 6/6 通过后，公开测试 22/22 通过，设计修订有效。

---

## 4 系统实现

### 4.1 入口与整体流程

系统以 main.py 为唯一 CLI 入口，通过 argparse 解析 --input、--output、--snr、--seed、--mod、--channel、--fec 等参数，无交互式输入。主流程为：读取输入文本 → run_transmitter 生成发射符号 → awgn/rayleigh 信道加噪 → run_receiver 恢复文本 → 写入 received.txt、metrics.json 并生成图表。默认验收命令对应 --channel awgn --fec repeat。

### 4.2 流水线实现

发送端 run_transmitter 按固定顺序调用 source_encode → scramble → channel_encode → build_frame → qpsk_modulate，再由 seed+1 生成 0～128 个噪声前缀符号并拼接到帧前，同时返回 preamble_symbols、payload_bits 等元信息供接收端使用。

接收端 run_receiver 依次完成 synchronize 帧同步 → qpsk_demodulate 解调 → parse_frame 解帧（含尾比特剥离）→ channel_decode → descramble 并按 length 截断 → verify_crc16 校验 → source_decode 还原文本，同步计算 ber、fer、text_match_rate 等指标。

### 4.3 各模块实现要点

各信号处理模块独立实现于 src/ 目录，核心接口与实现要点见表 4-1。

| 模块文件 | 核心接口 | 实现要点 |
|----------|----------|----------|
| source.py | source_encode / source_decode | UTF-8 字节 MSB 优先转比特；解码按 num_bits 截断 |
| scramble.py | scramble / descramble | 16 级 LFSR 生成 PN 序列，逐位 XOR，seed 驱动 |
| channel_coding.py | channel_encode / channel_decode | 默认 (3,1) 重复码 + 多数表决；--fec conv 切换卷积码 |
| framing.py | build_frame / parse_frame | 32+16+N+16 bit 组帧；支持 dict 入参；解帧前剥离 QPSK 尾 0 |
| modulation.py | qpsk_modulate / qpsk_demodulate | Gray 映射，符号归一化 1/√2，硬判决解调 |
| channel.py | awgn / rayleigh | 按 Es/N0 叠加复高斯噪声；Rayleigh 为 Level 3 扩展 |
| synchronization.py | synchronize | 归一化互相关寻峰，搜索窗口 0～144 符号 |
| utils.py | crc16_ccitt / verify_crc16 | CRC-16/CCITT 计算与校验，前导比特生成 |
| metrics.py | build_metrics / save_metrics | 汇总 SNR、BER、FER 等字段写入 JSON |
| plots.py | generate_all_plots | 生成星座图、BER 曲线、同步峰值图及 FEC 对比图 |
| conv_coding.py | conv_encode / viterbi_decode | (2,1,3) 卷积码 + Viterbi 译码，供对比实验 |

实现遵循第 2 章设计，未采用绕过链路的文件直拷方式；Mock 阶段发现的 padding 剥离与 parse_frame 兼容性已在 framing.py 中落地。

---

## 5 测试与验证

### 5.1 测试体系

测试分三层：Mock 测试（第 3 章，6 项设计验证）、学生自测 tests/（模块边界与回归）、教师公开测试 public_tests/（PR 自动验收，22 项）。环境为 Python 3.11+，依赖 pytest、numpy、scipy、matplotlib。默认验收命令 SNR=12 dB、seed=2026、QPSK、AWGN。

### 5.2 公开测试结果

本地执行 pytest public_tests -q，22 项全部通过。按类别汇总见表 5-1。

| 类别 | 覆盖内容 | 代表用例 | 结果 |
|------|----------|----------|------|
| 文档与结构 | 必需文件、DESIGN 链路、MOCK 报告、AI_LOG | TC-T-001～003、018～019 | 通过 |
| 模块功能 | 源编码、组帧、扰码、信道编码、QPSK、AWGN | TC-T-004～012 | 通过 |
| 端到端 | 同步偏移、文本恢复、metrics、图表、无交互 CLI | TC-T-013～017 | 通过 |
| 工程规范 | 无绕过链路直拷 | TC-T-020 | 通过 |

关键验证点包括：25 符号同步偏移下仍可检测帧起点；不同 SNR/seed 下输出可复现；received.txt 与原文一致；至少生成两类图表；CLI 无交互式输入。

### 5.3 自测与 Level 3

tests/ 目录覆盖 Mock 场景聚合及 Level 3 扩展（Rayleigh 信道、卷积码 FEC 对比），不阻塞公开测试默认命令，用于开发回归与答辩演示。

---

## 6 实验结果与分析

### 6.1 默认验收条件结果

在统一验收命令下运行，主要指标见表 6-1（数据来自 results/metrics.json）。

| 指标 | 数值 | 说明 |
|------|------|------|
| SNR | 12 dB | CLI 参数 Es/N0 |
| seed | 2026 | 扰码、噪声、偏移派生种子 |
| payload_bits | 1544 | 源编码比特数 |
| BER | 0 | 与原文比特比对无误 |
| FER | 0 | CRC 通过且文本完全一致 |
| text_match_rate | 1.0 | 字符级恢复率 100% |
| checksum_pass | true | CRC-16 校验通过 |
| sync_start_index | 81 | 帧前随机偏移 80 符号，检测正确 |
| Eb/N0 | 约 4.22 dB | 考虑 QPSK 与码率 1/3 换算 |

Test.txt 与 received.txt 内容完全一致，满足 PRD 一致性要求。

### 6.2 BER 与文本恢复率随 SNR 变化

BER 曲线扫描 SNR 0～14 dB（步进 2 dB），实测结果见表 6-2。

| SNR (dB) | BER | text_match_rate |
|----------|-----|-----------------|
| 0 | 0.0699 | 0 |
| 2 | 0.0259 | 0 |
| 4 | 0.0104 | 0 |
| 6 | 0.0026 | 0 |
| 8 | 0 | 1.0 |
| 10～14 | 0 | 1.0 |

(3,1) 重复码提供约 3～5 dB 量级增益：本系统在 SNR≥8 dB 即可无损恢复文本，优于未编码 QPSK 理论预期。低 SNR 下 BER 仍下降但 CRC 失败导致 text_match_rate 为 0，说明帧级错误检测先于乱码输出生效。

### 6.3 图表与系统瓶颈

三类图表均已生成：constellation.png 显示 12 dB 下接收符号集中于四个 Gray 星座点；sync_peak.png 显示前导互相关峰值位置与 sync_start_index 一致；ber_curve.png 呈现 BER 随 SNR 下降、text_match_rate 在 8 dB 附近陡升的趋势。

系统瓶颈主要在低 SNR 下的同步与信道译码：噪声增大时相关峰旁瓣升高，误码先集中于重复码无法纠正的多比特错误组，最终由 CRC 拦截。排查顺序为：查 sync_peak.png 确认帧起点 → 查 BER → 查 checksum_pass 与 length 字段。

---

## 7 AI 辅助编程过程

### 7.1 工具与工程流程

本项目使用 Cursor Agent（Claude）辅助需求理解、设计、编码、测试与文档撰写，完整过程记录于 AI_LOG.md。遵循 PRD 推荐流程：阅读 PRD → 编写 DESIGN.md → 编写 TEST_PLAN.md → Mock 测试 → 代码实现 → 公开测试验收 → 撰写报告。AI 负责初稿生成与迭代修复，本人在关键设计选型与测试失败时进行确认与决策。

### 7.2 主要交互与人工决策

表 7-1 汇总三次核心交互及人工调整。

| 阶段 | AI 主要输出 | 人工决策 |
|------|-------------|----------|
| 需求理解 | 梳理 PRD 固定链路、评分标准与提交流程 | 确认范围，作为设计输入 |
| 系统设计 | DESIGN v0.1（初稿含汉明码、64 bit 前导） | 改为 (3,1) 重复码、CRC-16、32 bit 前导；规划 Level 3 |
| 实现与测试 | TEST_PLAN、src/ 实现、Mock 测试、MOCK_TEST_REPORT | 确认按计划执行；mock 后修订 DESIGN v0.3 |

表 7-2 列出模块级 AI 生成内容与最终采纳情况。

| 模块 | AI 初稿 | 最终采纳 |
|------|---------|----------|
| 信道编码 | Hamming (7,4) | (3,1) 重复码（易实现、易答辩） |
| 前导长度 | 64 bit | 32 bit（节省符号） |
| parse_frame | 仅 bit 列表入参 | 支持 dict + 尾比特剥离（mock 驱动） |
| 绘图 | matplotlib | matplotlib 优先，无 wheel 时 PNG 回退 |
| Level 3 | DESIGN 规划 | 实现 Rayleigh 信道与卷积码 Viterbi |

### 7.3 测试失败与修复

公开测试与 Mock 过程中，AI 辅助完成 4 类问题修复，见表 7-3。

| 问题 | 原因 | 修复措施 |
|------|------|----------|
| TC-T-006 失败 | parse_frame 不接受 dict 入参 | 自动提取 bits/frame 键 |
| MK-002 / TC-T-011 | QPSK 奇数补 0 致解帧错位 | 增加 _strip_qpsk_tail_padding |
| 端到端同步误检 | 随机 QPSK 前缀产生伪相关峰 | 归一化互相关、限制搜索窗口、前缀改噪声符号 |
| 本地绘图失败 | Windows 无 matplotlib wheel | lazy import + 最小 PNG 回退 |

### 7.4 小结

AI 辅助显著提升了文档与代码初稿效率，但关键设计（编码方案、前导长度、接口语义）需结合课程知识与 mock 结果人工确认。本人保留 AI_LOG.md 全文，能够解释各模块通信原理、参数选择与修复逻辑，并确保未绕过无线链路直接复制文件。详细 prompt 记录见仓库 AI_LOG.md。