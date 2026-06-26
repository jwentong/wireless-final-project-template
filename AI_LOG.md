# AI 辅助编程日志（AI_LOG）

> 项目：无线通信技术期末项目——无线通信基带仿真系统  
> 工具：Cursor Agent（Claude）  
> 日期：2026-06-24

---

## 1. 交互摘要

### Prompt 1：阅读 PRD 并理解期末项目

- **用户请求**：阅读 `无线通信技术期末项目PRD.md`，说明期末作业要求。
- **AI 输出**：梳理固定链路、统一口径、评分标准、提交流程与模板仓库现状。
- **人工修改**：无；作为后续 DESIGN 的输入。
- **采纳理由**：准确覆盖 PRD 核心约束，便于确认范围。

### Prompt 2：编写 DESIGN.md

- **用户请求**：写 DESIGN.md，说明架构、接口、算法、参数、风险；有问题需商讨。
- **AI 输出**：DESIGN v0.1，默认 (7,4) 汉明码、64 bit 前导等。
- **人工修改**：用户确认改为 **(3,1) 重复码**、**CRC-16**、**32 bit 前导**、每次 CLI 生成 BER 曲线、计划 Level 3（Rayleigh + Viterbi）。
- **采纳理由**：重复码更易实现与答辩；前导缩短节省符号；Level 3 满足加分目标。

### Prompt 3：按工程流程写 TEST_PLAN 并实施全计划

- **用户请求**：写 TEST_PLAN.md；按 plan 完成 mock、实现、测试、AI_LOG。
- **AI 输出**：TEST_PLAN.md、完整 `src/` 实现、`tests/test_mock_scenarios.py`、MOCK_TEST_REPORT、本 AI_LOG。
- **人工修改**：无（全自动按计划执行）。
- **采纳理由**：与 PRD 工程流程及公开测试命名约定一致。

---

## 2. AI 生成内容与人工决策

| 模块 | AI 生成 | 人工/ mock 调整 |
|------|---------|-----------------|
| 信道编码 | 初稿 Hamming (7,4) | 用户确认改为 (3,1) 重复码 |
| 前导长度 | 初稿 64 bit | 用户确认 32 bit |
| parse_frame | 仅接受 bit 列表 | mock 发现需支持 dict + QPSK padding 剥离 |
| 绘图 | matplotlib | 本地无 wheel 时增加最小 PNG 回退 |
| Level 3 | DESIGN 规划 | 实现 `rayleigh()`、`conv_coding.py` |

---

## 3. 测试失败与修复

1. **TC-T-006**：`parse_frame(build_frame(...))` 传入 dict 报错 → 增加 dict 入参支持与 `bits` 键提取。
2. **MK-002 / TC-T-011**：奇数帧长 QPSK 补 0 后解帧错位 → `_strip_qpsk_tail_padding()`。
3. **同步误检**（E2E 调试）：随机前缀 QPSK 数据与长载荷导致相关峰误检 → 限制搜索窗口至 128+前导长度、归一化互相关、前缀改为高斯噪声符号。
4. **matplotlib 安装失败**（Windows 无编译器）：`plots.py` lazy import + 最小 PNG 回退，保证 CI（Ubuntu）仍可用 matplotlib。

---

## 4. 最终采纳理由

- **固定链路顺序**严格遵循 PRD，不绕过无线链路。
- **模块函数命名**对齐 `public_tests/README.md`，便于 `find_function` 发现。
- **mock 先行**发现 padding 与接口问题，避免端到端调试盲目性。
- **Level 3** 与基础链路解耦（`--channel rayleigh`、`--fec conv`），不影响默认公开验收命令。

---

## 6. Pull Request 提交（待学生完成）

Fork 仓库：`https://github.com/DaviZhi/wireless-final-project-template.git`

本地验证通过后执行：

```bash
git add DESIGN.md TEST_PLAN.md MOCK_TEST_REPORT.md AI_LOG.md main.py src/ tests/ results/
git commit -m "Complete wireless final project"
git push origin main
gh pr create --repo jwentong/wireless-final-project-template --title "学号-姓名-无线通信期末项目" --body "..."
```

PR 模板需填写学号、姓名、GitHub 用户名与提交清单。
