# 无线通信基带仿真系统测试计划

> 课程：无线通信技术 / 无线通信基础  
> 关联文档：[DESIGN.md](DESIGN.md) v0.2、[无线通信技术期末项目PRD.md](无线通信技术期末项目PRD.md)  
> 版本：v0.1

---

## 1. 测试目标与范围

### 1.1 目标

- 验证 [DESIGN.md](DESIGN.md) 中固定系统链路各模块接口与算法在实现前后均满足 PRD 与教师公开测试集要求。
- 通过 mock 测试在编码前发现设计缺陷，降低端到端集成风险。
- 建立公开测试（`public_tests/`）与学生自测（`tests/`）的分工，支撑最终 PR 验收与隐藏验证集鲁棒性。

### 1.2 测试范围

| 范围 | 包含 | 不包含 |
|------|------|--------|
| 基础链路 | 源编码、扰码、重复码、组帧、QPSK、AWGN、同步、指标与图表 | — |
| 公开测试 | TC-T-001～TC-T-020（20 条） | 教师 80% 隐藏验证集 |
| Mock 测试 | MK-001～MK-006（设计验证） | 完整 GUI |
| Level 3 扩展 | Rayleigh 信道、卷积码 Viterbi（可选） | OFDM、多址 |

### 1.3 设计基线（测试前提）

- 帧结构：32 bit preamble + 16 bit length + coded payload + CRC-16
- `length` 字段：源编码后、扰码前的 payload 比特数（PRD 统一口径）
- 信道编码：(3,1) 重复码，码率 1/3
- 默认验收：SNR=12 dB，seed=2026，QPSK，AWGN

---

## 2. 测试环境与工具

### 2.1 环境

| 项目 | 要求 |
|------|------|
| Python | 3.11+（与 GitHub Actions 一致） |
| 依赖 | `numpy`, `scipy`, `matplotlib`, `pytest`（见 [requirements.txt](requirements.txt)） |
| 图形后端 | `MPLBACKEND=Agg`（CI 无头模式） |

### 2.2 安装与运行

```bash
pip install -r requirements.txt

# 教师公开测试（最终验收）
pytest public_tests -q

# 学生自测
pytest tests -q

# 统一 CLI 端到端
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

### 2.3 测试分工

| 目录 | 维护者 | 用途 |
|------|--------|------|
| [public_tests/](public_tests/) | 教师提供，学生不修改 | PR 自动验收 |
| [tests/](tests/) | 学生编写 | Mock 场景、边界用例、开发回归 |
| [wireless_project_test_set_20.feature](wireless_project_test_set_20.feature) | 教师 BDD 描述 | 用例语义参考 |

### 2.4 注意事项

- **Test.txt 覆盖**：TC-T-014～017 运行时，`public_tests/conftest.py` 的 `ensure_test_file` fixture 会用 `SAMPLE_TEXT` **临时覆盖** `Test.txt`，与仓库内约 300 字原始 Test.txt 不同，属预期行为。
- **build_frame 双模式**：单元测试仅传 `payload` 单参数时，`length = len(payload)`；端到端传 `(coded_payload, source_bits)` 时，`length = len(source_bits)`（见 §3.2 TC-T-006 说明）。
- **禁止硬编码**：所有用例不得绑定固定 Test.txt 输出；隐藏测试会更换文本、SNR、seed。

---

## 3. 公开测试用例映射表（TC-T-001～020）

### 3.1 总览

| 编号 | 类别 | 测试要点 | pytest 位置 | DESIGN 章节 |
|------|------|----------|-------------|-------------|
| TC-T-001 | 结构 | 必需文件/目录存在 | test_01 | §2.3 |
| TC-T-002 | 设计 | DESIGN 覆盖固定链路 | test_01 | §2.1 |
| TC-T-003 | Mock | MOCK 报告 ≥3 场景 | test_01 | §7 |
| TC-T-004 | 源编码 | UTF-8 可逆，8 倍数 | test_02 | §4.1 |
| TC-T-005 | 帧 | 四字段齐全 | test_02 | §4.4 |
| TC-T-006 | 帧 | 封装解析可逆 | test_02 | §4.4 |
| TC-T-007 | 扰码 | seed=2026 可逆 | test_02 | §4.2 |
| TC-T-008 | 信道编码 | 无噪声可逆 | test_02 | §4.3 |
| TC-T-009 | QPSK | Gray 四象限 | test_02 | §4.5 |
| TC-T-010 | QPSK | 无噪声无误码 | test_02 | §4.5 |
| TC-T-011 | Padding | length 去 padding | test_02 | §4.4 |
| TC-T-012 | AWGN | seed 可复现 | test_02 | §4.6 |
| TC-T-013 | 同步 | 25 符号偏移 ±1 | test_03 | §4.7 |
| TC-T-014 | Metrics | metrics.json 字段 | test_03 | §4.8 |
| TC-T-015 | E2E | SNR=12 文本一致 | test_03 | §5 |
| TC-T-016 | 图表 | ≥2 张非空图 | test_03 | §4.8 |
| TC-T-017 | CLI | 非交互运行 | test_03 | §5.3 |
| TC-T-018 | AI_LOG | ≥3 prompt 记录 | test_01 | — |
| TC-T-019 | 分析 | 星座/BER/失败解释 | test_01 | §8 |
| TC-T-020 | 反捷径 | 禁止直拷贝文件 | test_01 | — |

### 3.2 用例明细

#### TC-T-001 项目目录包含必需提交物

- **输入**：项目根目录
- **预期**：存在 `DESIGN.md`、`TEST_PLAN.md`、`MOCK_TEST_REPORT.md`、`AI_LOG.md`、`main.py`、`src/`、`tests/`
- **执行**：`pytest public_tests/test_01_structure_and_documents.py::test_tc_t_001_required_project_files_exist -q`

#### TC-T-002 DESIGN.md 覆盖固定系统链路

- **预期**：文档含 Source Encode、Scramble/Encrypt、Channel Encode、Frame Build、QPSK Modulate/Demodulate、Channel、Synchronization、Channel Decode、Source Decode、Metrics
- **状态**：DESIGN v0.2 已满足

#### TC-T-003 MOCK_TEST_REPORT.md 包含设计修订记录

- **预期**：≥3 个 mock 场景、≥1 风险/缺陷、DESIGN 修订说明
- **执行**：mock 阶段完成后验证

#### TC-T-004 UTF-8 中文源编码可逆

- **输入**：`sample_text`（conftest 提供的中文短句）
- **预期**：`source_encode` → `source_decode` 文本一致；bit 长度 % 8 == 0
- **模块**：`src/source.py` — `text_to_bits`, `bits_to_text`, `source_encode`, `source_decode`

#### TC-T-005 帧结构包含 PRD 要求字段

- **输入**：2400 bit 随机 payload
- **预期**：`build_frame` 返回 dict，含 `preamble`、`length`、`payload`、`crc`/`checksum`；或序列化帧长于 payload
- **模块**：`src/framing.py` — `build_frame`

#### TC-T-006 帧封装和解析可逆

- **输入**：257 bit 随机 payload（`seed=2027`）
- **预期**：`parse_frame(build_frame(payload))` 恢复 payload 一致；`length == len(payload)`
- **接口说明**：单参数调用时 payload 即帧内载荷比特，`length` 记录其长度；端到端时第二参数 `source_bits_for_crc` 提供 PRD 语义下的源编码 bit 数

#### TC-T-007 扰码或加密可逆

- **输入**：511 bit 随机序列，`seed=2026`
- **预期**：`descramble(scramble(bits, seed=2026), seed=2026) == bits`
- **模块**：`src/scramble.py`

#### TC-T-008 信道编码无噪声可逆

- **输入**：400 bit 随机序列（`seed=2028`）
- **预期**：`channel_decode(channel_encode(bits)) == bits`
- **模块**：`src/channel_coding.py` — (3,1) 重复码

#### TC-T-009 QPSK 映射符合 PRD

- **输入**：`[0,0,0,1,1,1,1,0]` → 比特对 00,01,11,10
- **预期**：四象限符号 `(±1,±1)/√2`；前 4 符号平均功率 ≈ 1（0.8～1.2）
- **模块**：`src/modulation.py` — `qpsk_modulate`

#### TC-T-010 QPSK 无噪声调制解调

- **输入**：512 bit 随机（`seed=2029`）
- **预期**：解调比特与输入完全一致
- **模块**：`qpsk_modulate`, `qpsk_demodulate`

#### TC-T-011 QPSK padding 由 length 去除

- **输入**：255 bit 奇数 payload（`seed=2030`）
- **流程**：`build_frame` → 取 `bits`/`frame` → QPSK 调制解调 → `parse_frame`
- **预期**：恢复 payload 255 bit 与输入一致

#### TC-T-012 AWGN 固定 seed 可复现

- **输入**：4 个 QPSK 符号，SNR=12 dB，seed=2026
- **预期**：两次 `awgn(...)` 输出 `np.allclose`
- **模块**：`src/channel.py` — `awgn`

#### TC-T-013 同步检测 25 符号偏移

- **输入**：25 个随机前缀符号 + 32 符号前导（测试内构造）+ payload 符号
- **预期**：`detect_frame_start` / `synchronize` 返回起点与 25 误差 ≤1
- **模块**：`src/synchronization.py`

#### TC-T-014 metrics.json 最低字段

- **命令**：统一 CLI（SNR=12, seed=2026）
- **预期**：生成 `results/metrics.json`，含 `snr_db`, `seed`, `modulation`, `channel`, `payload_bits`, `ber`, `fer`, `text_match_rate`, `checksum_pass`, `sync_start_index`

#### TC-T-015 SNR 12 dB 端到端文本完全一致

- **预期**：`results/received.txt == Test.txt`（运行时 SAMPLE_TEXT）；`text_match_rate == 1.0`

#### TC-T-016 至少两类可视化图表

- **预期**：`constellation.png`、`ber_curve.png`、`sync_peak.png` 中至少 2 个非空文件

#### TC-T-017 统一 CLI 非交互

- **预期**：returncode=0；stdout/stderr 无 `input(`、`请输入` 等交互提示

#### TC-T-018 AI_LOG.md 记录 AI 辅助过程

- **预期**：≥3 条 prompt/提示；人工修改说明；采纳理由

#### TC-T-019 实验分析报告解释关键结果

- **预期**：DESIGN §8 或 MOCK 报告解释 QPSK 星座、BER/text_match_rate、失败原因

#### TC-T-020 不得绕过无线链路直拷贝

- **预期**：`main.py` 与 `src/` 中无 `shutil.copy`、`copyfile` 等将 Test.txt 直写 received.txt 的捷径

---

## 4. Mock 测试计划（MK-001～006）

Mock 阶段在完整实现前/中验证设计可行性，结果写入 [MOCK_TEST_REPORT.md](MOCK_TEST_REPORT.md)。

| Mock ID | 场景 | 输入/步骤 | 通过准则 | DESIGN 风险 |
|---------|------|-----------|----------|-------------|
| MK-001 | 帧字段手工推演 | 拼装 32+16+N+16 bit 结构 | 字段顺序与长度与 DESIGN §4.4 一致 | R3, R4 |
| MK-002 | 奇数 payload 纸面推演 | payload_bits=255，帧尾 QPSK 补 0 | 接收端按 length=255 截断，无多余 bit | R3, TC-T-011 |
| MK-003 | 同步三档 offset | offset=0, 25, 128；SNR=12 | 检测误差 ≤1 符号 | R2, TC-T-013 |
| MK-004 | 重复码纠错 | 每组 3 bit 翻转 1 bit | 多数表决恢复正确 | R1 |
| MK-005 | 多 seed 可复现 | seed=2026/2027/9999 各跑 AWGN 两次 | 同 seed 输出一致 | R6 |
| MK-006 | CRC-16 独立校验 | 已知源编码比特流 | 计算与校验一致，checksum_pass 语义正确 | R4 |

**Mock 执行方式**：在 `tests/` 编写对应测试脚本，模块 stub 就绪后运行 `pytest tests/test_mock_*.py -v`。

---

## 5. 学生自测计划（tests/ 目录）

| 文件 | 覆盖用例 | 说明 |
|------|----------|------|
| `tests/test_source.py` | TC-T-004 | UTF-8 中英文、空串边界 |
| `tests/test_framing.py` | TC-T-005/006/011, MK-001/002 | 帧 dict 键、奇数 payload |
| `tests/test_scramble.py` | TC-T-007 | 多种 seed |
| `tests/test_channel_coding.py` | TC-T-008, MK-004 | 无噪声可逆、1 bit 纠错 |
| `tests/test_modulation.py` | TC-T-009/010 | Gray 映射、奇数 bit 补零 |
| `tests/test_channel.py` | TC-T-012, MK-005 | AWGN 可复现 |
| `tests/test_sync.py` | TC-T-013, MK-003 | offset 边界 |
| `tests/test_mock_report.py` | MK-001～006 | mock 场景聚合 |
| `tests/test_e2e.py` | TC-T-015 | 本地 main.py 冒烟 |

---

## 6. Level 3 扩展测试（可选）

| 编号 | 场景 | 命令/条件 | 通过准则 |
|------|------|-----------|----------|
| L3-001 | Rayleigh 信道 | `--channel rayleigh --snr 12` | 不崩溃，metrics 含 channel=rayleigh |
| L3-002 | AWGN vs Rayleigh 对比 | 同 seed 两种信道 | Rayleigh text_match_rate ≤ AWGN |
| L3-003 | 深衰落 | 强制小 \|h\| | failure_reason 记录，不崩溃 |
| L3-004 | 卷积码 Viterbi | `--fec conv` | 无噪声可逆 |
| L3-005 | FEC 对比曲线 | repeat vs conv | ber_curve 或独立图可对比 |

扩展测试**不阻塞**公开测试默认命令（`--channel awgn`，重复码）。

---

## 7. 通过准则与验收命令

### 7.1 基础通过（Level 1～2）

```bash
pytest public_tests -q
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

| 检查项 | 准则 |
|--------|------|
| 公开测试 | 全部 PASSED |
| received.txt | 与 Test.txt 完全一致（SNR≥12） |
| metrics.json | 10 个必填字段齐全 |
| 图表 | constellation / ber_curve / sync_peak 至少 2 张非空 |
| 低 SNR | SNR<12 可不完全一致，但不得崩溃，须输出 ber/fer/text_match_rate |

### 7.2 Level 3 通过（可选）

- `--channel rayleigh` 可运行并输出合理 metrics
- `--fec conv` 卷积码无噪声可逆
- BER 对比图可展示重复码 vs 卷积码差异

---

## 8. 测试执行顺序与里程碑

| 阶段 | 活动 | 产出 | 状态 |
|------|------|------|------|
| M1 | 完成 DESIGN.md | DESIGN v0.2 | 已完成 |
| M2 | 完成 TEST_PLAN.md | 本文档 | 进行中 |
| M3 | Mock 测试 MK-001～006 | MOCK_TEST_REPORT.md, DESIGN v0.3 | 待执行 |
| M4 | 实现 src/ + main.py | 可运行系统 | 待执行 |
| M5 | pytest public_tests 全通过 | CI 绿 | 待执行 |
| M6 | 生成 results/ 与图表 | received.txt, metrics, png | 待执行 |
| M7 | Level 3 扩展 | Rayleigh + Viterbi | 待执行 |
| M8 | AI_LOG + PR | AI_LOG.md, GitHub PR | 待执行 |

**推荐执行顺序**：M2 → M3（mock）→ M4 → M5 → M6 → M7 → M8。

---

## 9. DESIGN.md 追溯矩阵

| DESIGN 章节 | 测试用例 |
|-------------|----------|
| §4.1 源编码 | TC-T-004 |
| §4.2 扰码 | TC-T-007 |
| §4.3 重复码 | TC-T-008, MK-004 |
| §4.4 组帧 | TC-T-005/006/011, MK-001/002/006 |
| §4.5 QPSK | TC-T-009/010 |
| §4.6 AWGN | TC-T-012, MK-005 |
| §4.7 同步 | TC-T-013, MK-003 |
| §4.8 指标/图表 | TC-T-014/016 |
| §5 端到端 | TC-T-015/017 |
| §8 实验分析 | TC-T-019 |
| §11 Level 3 | L3-001～005 |

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-24 | 初稿：公开测试映射、mock 计划、tests/ 规划、追溯矩阵 |
