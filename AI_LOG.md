# AI_LOG.md — AI 辅助编程过程记录

> 工具：Claude Code（Opus）+ Superpowers skills。
> 工作流：严格按 `PRD → DESIGN → TEST_PLAN → mock → MOCK_TEST_REPORT → TDD 实现 → 验证` 推进，全程留痕。
> 本文件**边做边写**，既是评分要求的 AI 使用记录，也是答辩"做作业过程"的叙事大纲。
> 阅读顺序即时间线，从上到下记录每个阶段的关键 prompt、AI 产出、人工修改与采纳理由。

---

## 阶段 0 — 需求澄清与满分策略（Vibe / Brainstorm）

**关键 Prompt（人）**：「这是无线通信期末作业，要求尽可能满分、最高标准，还要准备答辩 PPT。先说思路再动手。」

**AI 产出**：通读 `PRD.docx` 与《如何使用 vibe coding.pdf》，给出关键洞察——
评分 100 分中，**设计文档(20) + mock与修订(15) + AI使用与答辩(10) = 45 分**落在"工程过程与可解释性"上，而非纯代码；
要满分必须 (a) 真实走工程流程并留痕，(b) 做到 Level 3（提高模块）。

**人工决策**：采纳"过程驱动 + Level 3"策略；提交方式先本地开发；
提高模块选 **卷积码+Viterbi、Rayleigh/Rician+均衡、多调制对比+自适应**；PPT 用传统 .pptx。

**采纳理由**：过程文档是低成本高回报拿分点；老师 PDF 明确以 vibe→spec→harness 流程为考查重点，顺势而为。

---

## 阶段 1 — 接口契约逆向（Spec 前置）

**关键 Prompt（人）**：提供 fork 仓库 `EchoTreee/wireless-final-project-template`，要求按真实接口设计。

**AI 产出**：clone fork，**逐行精读 `public_tests/` 三个测试文件**，反推出全部模块的函数命名、签名、返回约定：
`scramble` 必须接受 `seed=` kwarg；`synchronize` 必须对任意 `preamble` 做通用互相关（不能写死前导）；
`channel_encode/decode` 无噪声必须完全可逆；`build_frame` 返回比特序列、`parse_frame` 返回含 `payload/length` 的 dict；
`src/` 内禁止 `shutil.copy` 等直拷（TC-T-020 反作弊）。据此确定 `src/` 架构。

**采纳理由**：让公开测试成为设计的"single source of truth"，零适配通过、避免返工——即"测试驱动设计"。

---

## 阶段 2 — 设计冻结（Spec：DESIGN.md / TEST_PLAN.md）

**关键 Prompt（人）**：确认「卷积码主链路 + Barker 前导 + CRC-16」方向后授权写设计文档。

**AI 产出**：`PRD.md`（需求基线）、`DESIGN.md`（10 章逐模块原理 + 帧位布局 + SNR/Eb-N0 推导 + 风险表）、`TEST_PLAN.md`（20 用例映射 + 鲁棒性矩阵）。

### 关键设计决策与权衡（答辩故事线）

| 决策点 | 备选 | 采纳 | 理由 |
|---|---|---|---|
| 主信道编码 | 汉明码 / 卷积码 | 卷积码 K=7 (171,133)+Viterbi | 一举三得：主链路 + 提高模块 + BER 曲线漂亮；zero-tail 保无噪声可逆 |
| length 字段 | 单字段 | `orig_len` + `coded_len` 双字段 | 发现 PRD"原始 bit 数"语义与接收端定位需求冲突，拆开各司其职 |
| length 位宽 | 16 bit | **32 bit** | 见下方人工修改 |
| 前导序列 | m 序列 / Barker | Barker-13 → 26bit/13符号 | 自相关旁瓣≤1，同步峰尖锐，实现简单 |
| SNR 定义 | Eb/N0 / 符号SNR | 符号功率/噪声功率 + 标注换算 | 对齐 PRD 强制口径；`Eb/N0 = SNR−3.01dB` |

**人工修改（重要）**：`length` 位宽 AI 初稿写 16 bit；人工 review 时指出 16bit 上限约 2700 汉字，
隐藏验证集可能用超长文本 → 主动改为 **32 bit**。已同步修订 `DESIGN.md` 与 `TEST_PLAN.md`。

**采纳理由**：以极小开销（每帧多 4 字节）彻底消除超长文本溢出风险，提升对隐藏测试的鲁棒性。

---

## 阶段 3 — Mock 验证与设计修订（mock）

**关键 Prompt（人）**：「进入 mock 阶段」，并强调「这些小细节都要记好，方便我讲故事、讲做作业的过程」。

**AI 产出**：写 mock 骨架 `mock/mock_pipeline.py`（信道编码用重复码占位，隔离编码强度变量），跑 6 类 mock 场景 + 鲁棒性 sweep。
**mock 暴露真实缺陷**：帧头 `length` 字段在 PRD 链路顺序（Channel Encode → Frame Build）下不受 FEC 保护，
低 SNR 单比特错误导致整帧解析失败（4 dB 18/20、6 dB 11/20 属此类 header 损坏）。

**人工修改 / 决策**：采纳「对 length 字段 3× 重复 + 多数判决」修订；写 `mock/mock_fix_verify.py` 验证，
header 损坏率 6 dB 由 11→1、4 dB 由 18→6，修订有效。已回填 `DESIGN.md` v0.2 与 `MOCK_TEST_REPORT.md`。

**采纳理由**：length 是 framing 的"控制平面"，出错代价远高于单个 payload 比特；用极小开销换低 SNR / 隐藏测试鲁棒性。
这是答辩里"先 mock 后实现、用数据驱动设计修订"的核心案例。

## 阶段 4 — TDD 实现与端到端集成

**关键 Prompt（人）**：「开始吧不过了，最后帮我把整个流程、故事讲好就行」—— 授权连续推进，重点在过程叙事。

**AI 产出**：按 TDD 逐模块实现 `src/`（source / scramble / channel_coding(汉明+卷积Viterbi) / framing / modulation / channel / synchronization / equalizer / metrics / pipeline）+ `main.py`。**单元测试 47 全绿，公开测试 22/22 全绿**，SNR12/seed2026 下 `received.txt` 与 `Test.txt` 完全一致。

### 实现期两个关键调试（答辩素材）

**调试 1 — checksum_pass 假阴性**：首版把 CRC 算在信道编码后的 coded payload 上。AWGN 12 dB 下 coded payload 有个别比特错（被 Viterbi 纠正，故文本对），但 CRC 在译码前计算 → 校验失败、fer=1，与"文本完全恢复"矛盾。**修复**：CRC 改为覆盖**原始信息位**（符合 PRD"校验覆盖原始 payload bitstream"），并随信息一起进信道编码受 FEC 保护，接收端译码后再验 → 纠错后 checksum 通过。体现"CRC 应放在协议栈哪一层"的理解。

**调试 2 — MMSE 单测 SNR 定义不一致**：均衡对比测试把噪声功率定义为相对"衰落后信号功率"，与 MMSE 公式 `1/SNR`（相对单位功率信号）约定不一致，导致 MMSE 过度收缩、MSE 反大于 ZF。**修复**：统一噪声功率为相对单位功率信号（全系统 SNR 约定），MMSE 恢复理论最优。体现 SNR 定义一致性的重要性。

**采纳理由**：两处都不是"改测试让它过"的妥协，而是定位真实根因（协议分层 / SNR 定义）后修正，留作答辩"我理解为什么"的案例。

## 阶段 5 — 提高模块对比实验

**AI 产出**：`experiments.py` 生成三张对比图——FEC 对比（无编码 / 汉明 / 卷积）、调制对比（BPSK/QPSK/16-QAM）、衰落与均衡（AWGN / Rayleigh no-eq / ZF / MMSE）。

**关键发现（答辩素材）**：
- **编码增益**：QPSK 无编码 @10 dB BER≈5e-4 → 卷积码 0，约 4–5 dB 增益。
- **ZF ≈ MMSE for QPSK**：QPSK 仅相位判决，ZF 与 MMSE 只差一个正实标量，硬判决 BER 完全重合（图中 ZF 用虚线叠示）。但在估计 MSE 意义下 MMSE 优于 ZF（见 `test_equalizer.py`）——两个角度都正确，是理解深度点。
- **BPSK vs QPSK 差 3 dB**：因采用符号 SNR 口径，QPSK 每符号 2 bit，相同符号 SNR 下 Eb/N0 低 3 dB；若按 Eb/N0 两者 BER 相同。

## AI 协作总结：保留 / 修改 / 拒绝（学术诚信）

| AI 生成内容 | 处理 | 理由 |
|---|---|---|
| 整体架构与模块接口（对齐 public_tests） | 保留 | 契约清晰，零适配通过公开测试 |
| `length` 字段 16 bit | 修改 → 32 bit | 防超长文本溢出（隐藏测试鲁棒性） |
| 帧头 length 不保护 | 修改 → 3× 重复保护 | mock 数据证明低 SNR 会崩 |
| CRC 覆盖 coded payload | 修改 → 覆盖原始信息位 + FEC 保护 | 符合 PRD，纠错后校验通过 |
| MMSE 测试噪声功率定义 | 修改 | 统一全系统 SNR 约定 |
| "直接生成最终代码" | 拒绝 | 坚持 PRD→DESIGN→mock→TDD 流程并全程留痕 |

> 全部代码均可由本人解释通信原理、参数与逻辑；无针对公开测试的硬编码，无绕过链路的文件直拷。

