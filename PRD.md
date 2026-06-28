# 无线通信技术期末项目 PRD

## 1. 项目背景

本课程期末考核采用项目形式替代传统闭卷考试。学生需要在教师提供的 PRD 和公开测试案例基础上，使用 AI 辅助编程完成一个可运行的无线通信基带仿真系统。系统需要将教师给定的 `Test.txt` 文档作为业务载荷，经过发送端、无线信道和接收端处理后，在接收端恢复为 `results/received.txt`。

本项目重点考查学生对无线通信系统链路的整体理解、模块化设计能力、测试驱动开发意识、AI 辅助编程能力，以及对通信原理、关键参数、代码逻辑和实验结果的解释能力。

## 2. 项目目标

实现一个端到端无线通信基带仿真系统，完成 `Test.txt` 到 `received.txt` 的可靠传输。

系统必须理解并实现源编码、扰码或加密、信道编码、QPSK 调制、无线信道、同步、解调、译码和文件恢复流程；生成性能指标和可视化结果，包括误比特率、帧错误率、文本恢复率、星座图和同步相关峰值图等。

## 3. 统一系统流程

所有学生必须实现同一条固定系统链路：

```text
Test.txt
-> Source Encode
-> Encrypt/Scramble
-> Channel Encode
-> Frame Build
-> QPSK Modulate
-> Channel
-> Synchronization
-> QPSK Demodulate
-> Channel Decode
-> Decrypt/Descramble
-> Source Decode
-> received.txt
-> Metrics/Plots
```

其中 QPSK 为基础必做调制方式。BPSK 和 16-QAM 可作为对比实验或扩展模块，不替代 QPSK 基础要求。

## 4. 输入与输出要求

| 项目 | 要求 |
|---|---|
| 输入文件 | 教师提供 `Test.txt`，编码格式为 UTF-8 |
| 输出文件 | 系统必须生成 `results/received.txt` |
| 一致性检查 | 系统必须比较 `Test.txt` 与 `received.txt`，并输出 BER、字符恢复率或文本一致性结果 |
| 复现实验 | 系统必须支持固定随机种子 |
| 命令行运行 | `python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn` |

## 5. 功能需求

| 模块 | 固定要求 | 允许选择或扩展 |
|---|---|---|
| 源编码 | UTF-8 文本与比特流互转 | 可自行设计补零、长度记录、异常字符处理策略 |
| 扰码/加密 | 必须可逆 | XOR、PN 序列扰码、简单流密码 |
| 信道编码 | 必须实现一种编码 | 重复码、汉明码、卷积码、简化 LDPC |
| 帧结构 | 必须含前导、长度、载荷、校验 | 字段长度、CRC/checksum 方案可自选 |
| 调制 | 基础必做 QPSK | BPSK、16-QAM 作为对比或提高项 |
| 信道 | AWGN 必做 | Rayleigh、Rician、多径信道作为提高项 |
| 同步 | 必须检测帧起点 | 前导相关、匹配滤波、能量检测辅助 |
| 均衡 | 基础系统可不做 | ZF、MMSE 作为提高项 |
| OFDM/分集/多址 | 基础系统可不做 | 作为挑战模块或加分模块 |

## 6. 基础系统统一验收口径

基础系统必须采用以下统一口径：

| 项目 | 统一要求 |
|---|---|
| QPSK 映射 | Gray 编码：00 -> `(1+j)/sqrt(2)`，01 -> `(-1+j)/sqrt(2)`，11 -> `(-1-j)/sqrt(2)`，10 -> `(1-j)/sqrt(2)` |
| SNR 定义 | 接收端调制符号平均功率与复高斯噪声平均功率之比，单位 dB |
| length 字段 | 表示源编码后、扰码前的原始 payload bit 数 |
| QPSK padding | 若进入 QPSK 调制的 bit 数不是 2 的整数倍，帧尾补 0，接收端根据 length 去除 padding |
| 校验字段 | 至少覆盖原始 payload bytes 或原始 payload bitstream |
| 同步偏移 | 应能处理 0 到 128 个 QPSK 符号的随机前置偏移 |
| 公开基础通过条件 | SNR >= 12 dB、AWGN、固定 seed 条件下，`received.txt` 必须与 `Test.txt` 完全一致 |
| 低 SNR 行为 | 不强制完全一致，但系统不得崩溃，必须输出 BER、FER、text_match_rate 和失败标记 |

## 7. metrics.json 最低字段

系统必须生成 `results/metrics.json`，且至少包含：

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

## 8. 分级要求

| 等级 | 得分上限 | 要求 |
|---|---:|---|
| Level 1 基础必做 | 70 | 跑通端到端系统；实现 QPSK、AWGN、帧同步、信道编码、文件恢复；输出基本性能指标 |
| Level 2 完整系统 | 85 | 增加扰码或加密、BER-SNR 曲线、星座图、同步峰值图、mock 测试报告和设计修订记录 |
| Level 3 提高模块 | 100 | 任选 Rayleigh 信道、均衡、OFDM、分集、卷积码 Viterbi、自适应调制、图形化界面等高级模块 |

## 9. 工程流程要求

学生不得直接跳到最终代码生成，必须按以下工程流程完成项目：

1. 阅读教师 PRD，生成 `DESIGN.md`。
2. 阅读教师公开测试案例，生成 `TEST_PLAN.md`。
3. 进行 mock 测试，验证接口、帧结构、同步流程和端到端流程是否可行。
4. 根据 mock 测试修订 `DESIGN.md`，并在 `MOCK_TEST_REPORT.md` 中说明问题和调整。
5. 在设计文档稳定后，使用 AI 辅助生成和完善系统代码。
6. 运行公开测试、自测和端到端实验，输出 `received.txt`、`metrics.json` 和图表。
7. 提交 `AI_LOG.md`，记录关键 prompt、AI 生成内容、人工修改内容和调试过程。

## 10. 最终提交物

建议项目目录如下：

```text
wireless-final-project/
  PRD.md
  DESIGN.md
  TEST_PLAN.md
  MOCK_TEST_REPORT.md
  AI_LOG.md
  Test.txt
  main.py
  src/
  tests/
  results/
    received.txt
    metrics.json
    constellation.png
    ber_curve.png
    sync_peak.png
```

## 11. 评分标准

| 评分项 | 分值 | 评价重点 |
|---|---:|---|
| 需求理解与设计文档 | 20 | 设计完整性、通信原理正确性、接口清晰度、参数合理性 |
| mock 测试与设计修正 | 15 | 是否先验证设计、是否发现问题、是否根据测试反馈修订 |
| 系统代码实现 | 25 | 端到端链路、模块化结构、QPSK/AWGN/同步/编码译码实现质量 |
| 公开与隐藏测试通过情况 | 20 | `received.txt` 恢复、BER/FER、鲁棒性、无硬编码行为 |
| 实验分析报告 | 10 | 星座图、BER 曲线、同步图、结果解释和失败分析 |
| AI 使用记录与答辩 | 10 | `AI_LOG.md` 完整性、代码理解、现场解释能力、学术诚信 |

