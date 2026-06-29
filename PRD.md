# 无线通信技术期末项目 PRD

> 基于 AI 辅助编程的无线通信文件传输基带仿真系统
> 适用课程：无线通信技术 / 无线通信基础　考核性质：替代闭卷期末考试
>
> 本文件由教师 `PRD.docx` 转写为 Markdown，作为项目内的需求基线（single source of truth）。
> 本项目的设计（`DESIGN.md`）、测试计划（`TEST_PLAN.md`）、mock 报告（`MOCK_TEST_REPORT.md`）
> 与实现均以本文件为准绳。

## 1. 项目背景

本课程期末考核采用项目形式替代传统闭卷考试。学生需在教师提供的 PRD 和部分公开测试案例基础上，
使用 AI 辅助编程完成一个可运行的无线通信基带仿真系统：将教师给定的 `Test.txt` 作为业务载荷，
经过发送端、无线信道和接收端处理后，在接收端恢复为 `results/received.txt`。

考查重点：链路整体理解、模块化设计、测试驱动开发意识、AI 辅助编程能力，以及对通信原理、
关键参数、代码逻辑和实验结果的解释能力。

## 2. 项目目标

- 实现端到端无线通信基带仿真系统，完成 `Test.txt` → `received.txt` 的可靠传输。
- 实现源编码、扰码/加密、信道编码、QPSK 调制、无线信道、同步、解调、译码与文件恢复全流程。
- 基于公开测试案例生成并修订设计文档，完成 mock 测试并据此调整方案。
- 生成性能指标与可视化：误比特率（BER）、帧错误率（FER）、文本恢复率、星座图、同步相关峰值图等。
- 规范记录 AI 辅助编程过程，并能解释每个模块的通信原理、关键参数、代码逻辑与实验结果。

## 3. 统一系统流程（固定链路，顺序不可变）

```
Test.txt -> Source Encode -> Encrypt/Scramble -> Channel Encode -> Frame Build
         -> QPSK Modulate -> Channel -> Synchronization -> QPSK Demodulate
         -> Channel Decode -> Decrypt/Descramble -> Source Decode -> received.txt
         -> Metrics/Plots
```

QPSK 为基础必做调制方式。BPSK 与 16-QAM 作为对比/扩展，不替代 QPSK 基础要求。

## 4. 输入与输出要求

| 项目 | 要求 |
|---|---|
| 输入文件 | 教师提供 `Test.txt`，约 300 字课程描述，UTF-8 编码 |
| 输出文件 | 必须生成 `results/received.txt` |
| 一致性检查 | 比较 `Test.txt` 与 `received.txt`，输出 BER、字符恢复率或文本一致性 |
| 复现实验 | 必须支持固定随机种子，便于公开/隐藏测试复现 |
| 命令行运行 | `python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn` |

## 5. 功能需求

- **源编码**：UTF-8 文本 ↔ 比特流互转。
- **扰码/加密**：对发送比特做可逆处理（XOR、PN 序列扰码或简单流密码）。
- **信道编码**：提供基本抗噪能力（重复码、汉明码、卷积码等）。
- **帧结构**：至少包含前导序列、长度字段、载荷字段、校验字段。
- **调制**：基础必做 QPSK，须说明星座映射、归一化方式与比特到符号映射。
- **信道**：基础必做 AWGN，支持可配置 SNR；Rayleigh/Rician 衰落可作扩展。
- **同步**：利用前导序列等检测帧起点，不得假设接收端天然知道起点。
- **接收端**：完成同步、解调、信道译码、解扰/解密、源解码与文件恢复。
- **指标**：输出 `results/metrics.json`，记录 SNR、BER、FER、文本一致率、随机种子与关键参数。
- **可视化**：至少生成 QPSK 星座图、BER-SNR 曲线、同步相关峰值图三者中的两项。

## 6. 模块边界与可选设计空间

| 模块 | 固定要求 | 允许选择/扩展 |
|---|---|---|
| 源编码 | UTF-8 ↔ 比特流 | 补零、长度记录、异常字符处理策略 |
| 扰码/加密 | 必须可逆 | XOR、PN 序列扰码、简单流密码 |
| 信道编码 | 必须实现一种 | 重复码、汉明码、卷积码、简化 LDPC |
| 帧结构 | 含前导/长度/载荷/校验 | 字段长度、CRC/checksum 方案自选 |
| 调制 | 基础必做 QPSK | BPSK、16-QAM 作对比/提高 |
| 信道 | AWGN 必做 | Rayleigh、Rician、多径作提高 |
| 同步 | 必须检测帧起点 | 前导相关、匹配滤波、能量检测 |
| 均衡 | 基础可不做 | ZF、MMSE 作提高 |
| OFDM/分集/多址 | 基础可不做 | 挑战/加分模块 |

### 6.1 基础系统统一验收口径

| 项目 | 统一要求 |
|---|---|
| QPSK 映射 | Gray 编码：`00→(1+j)/√2`，`01→(-1+j)/√2`，`11→(-1-j)/√2`，`10→(1-j)/√2` |
| SNR 定义 | 接收端调制符号平均功率与复高斯噪声平均功率之比（dB）；若用 Eb/N0 须在 DESIGN 与 metrics 中说明换算 |
| length 字段 | 表示源编码后、扰码前的原始 payload bit 数；接收端据此去 padding 并恢复 UTF-8 |
| QPSK padding | 进入 QPSK 的 bit 数非偶数时帧尾补 0，接收端按 length 去除 |
| 校验字段 | 至少覆盖原始 payload bytes/bitstream；metrics 记录 `checksum_pass` 或 `crc_pass` |
| 同步偏移 | 处理 0~128 个 QPSK 符号随机前置偏移；SNR≥12 dB AWGN 下帧起点误差 ≤1 符号 |
| 公开基础通过 | SNR≥12 dB、AWGN、固定 seed 下，`received.txt` 与 `Test.txt` 完全一致 |
| 低 SNR 行为 | 不强制完全一致，但不得崩溃；须输出 BER、FER、text_match_rate 与失败/校验标记 |

### 6.2 metrics.json 最低字段

```json
{
  "snr_db": 12,
  "seed": 2026,
  "modulation": "qpsk",
  "channel": "awgn",
  "payload_bits": 2400,
  "ber": 0.0,
  "fer": 0.0,
  "text_match_rate": 1.0,
  "checksum_pass": true,
  "sync_start_index": 25
}
```

## 7. 分级要求

| 等级 | 得分上限 | 要求 |
|---|---|---|
| Level 1 基础必做 | 70 | 端到端跑通；QPSK、AWGN、帧同步、信道编码、文件恢复；基本性能指标 |
| Level 2 完整系统 | 85 | L1 + 扰码/加密、BER-SNR 曲线、星座图、同步峰值图、mock 报告与设计修订记录 |
| Level 3 提高模块 | 100 | 任选 Rayleigh、均衡、OFDM、分集、卷积码 Viterbi、自适应调制、GUI 等高级模块 |

## 8. 工程流程要求（不得直接跳到最终代码）

1. 阅读 PRD → 生成 `DESIGN.md`（架构、模块接口、算法选择、关键参数、预期风险）。
2. 阅读公开 20% 测试案例 → 生成 `TEST_PLAN.md`。
3. 进行 mock 测试，验证接口、帧结构、同步流程与端到端流程是否可行。
4. 据 mock 结果修订 `DESIGN.md`，在 `MOCK_TEST_REPORT.md` 中说明问题与调整。
5. 设计稳定后，使用 AI 辅助生成与完善代码。
6. 运行公开测试、自测与端到端实验，输出 `received.txt`、`metrics.json` 与图表。
7. 提交 `AI_LOG.md`，记录关键 prompt、AI 生成内容、人工修改与调试过程。

## 9. 提交物目录

```
DESIGN.md  TEST_PLAN.md  MOCK_TEST_REPORT.md  AI_LOG.md
PRD.md  Test.txt  main.py  src/  tests/
results/{received.txt, metrics.json, constellation.png, ber_curve.png, sync_peak.png}
```

## 10. 统一自动验收入口

```bash
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

通过条件：程序正常退出；生成 `received.txt` 与 `metrics.json`；SNR≥12 dB、AWGN、固定 seed 下
`received.txt` 与 `Test.txt` 完全一致；metrics 含全部最低字段；至少生成两张图。

## 11. 评分标准

| 评分项 | 分值 | 评价重点 |
|---|---|---|
| 需求理解与设计文档 | 20 | 设计完整性、通信原理正确性、接口清晰度、参数合理性 |
| mock 测试与设计修正 | 15 | 是否先验证设计、是否发现问题、是否据反馈修订 |
| 系统代码实现 | 25 | 端到端链路、模块化结构、QPSK/AWGN/同步/编译码质量 |
| 公开与隐藏测试 | 20 | received.txt 恢复、BER/FER、鲁棒性、无硬编码 |
| 实验分析报告 | 10 | 星座图、BER 曲线、同步图、结果解释与失败分析 |
| AI 使用记录与答辩 | 10 | AI_LOG 完整性、代码理解、现场解释、学术诚信 |

## 12. 学术诚信

- 个人独立完成；禁止复制他人完整项目或共享最终代码。
- 禁止绕过通信链路直接复制 `Test.txt` 到 `received.txt`。
- 禁止针对公开测试案例硬编码输出。
- 必须能解释每个模块的通信原理、关键参数、代码逻辑与实验结果。
