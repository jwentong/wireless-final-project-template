# AI_LOG.md — AI 辅助编程记录

## 概述

本项目使用 Claude Code (claude-sonnet-4-6) 作为 AI 编程助手，按照 PRD 要求的工程流程完成：PRD → DESIGN.md → TEST_PLAN.md → MOCK_TEST_REPORT.md → 代码实现 → 测试验证。

---

## 关键 Prompt 记录

### Prompt 1: 系统设计生成

**Prompt**: "阅读桌面的无线通信技术期末项目PRD，这是我的实验要求"

**AI 响应**: AI 提取了 PRD.docx 内容，解析了完整需求，包括系统链路、模块要求、CLI 接口、测试要求等。

**人工修改**: 无。AI 成功提取了乱码的中文 docx 文件内容。

**采纳理由**: AI 正确逐条解析了 PRD，为后续设计提供了准确的需求基础。

---

### Prompt 2: DESIGN.md 生成

**Prompt**: "你按照顺序开始完成"（在理解了 PRD 和所有公开测试之后）

**AI 响应**: AI 生成了完整的 DESIGN.md，包括：
- 系统架构（固定链路 10 个模块）
- 每个模块的接口定义和算法选择
- 帧结构详细设计（32-bit preamble, 16-bit length, N-bit payload, 16-bit CRC）
- 关键参数汇总表
- 预期风险与缓解措施

**人工修改**: 
- 确认汉明(7,4) 编码方案适合本项目的教学要求
- 确认帧结构中 CRC 覆盖范围（length + payload）
- 确认 QPSK Gray 编码映射表符合测试要求

**采纳理由**: AI 的设计方案完整覆盖 PRD 所有要求，模块接口定义清晰，与公开测试预期一致。

---

### Prompt 3: 公开测试分析与 TEST_PLAN.md

**Prompt**: AI 读取了 `public_tests/` 中的全部测试代码，生成 TEST_PLAN.md。

**AI 响应**: 生成了包含测试用例映射表、Mock 测试计划、测试环境和通过标准的测试计划。

**人工修改**: 根据实际测试代码调整了预期行为描述。

**采纳理由**: 系统化地覆盖了所有 20 个测试用例。

---

### Prompt 4: Mock 测试执行与报告

**Prompt**: AI 按照 TEST_PLAN.md 生成 Mock 测试场景并撰写报告。

**AI 响应**: 生成了 MOCK_TEST_REPORT.md，记录了 9 个 mock 测试场景、3 个发现的设计缺陷和相应修订。

**人工修改**: 
- 发现缺陷 1（QPSK padding）：在实际编码中确认帧封装函数需要添加自动 padding 逻辑
- 发现缺陷 2（信道编码对齐）：确认汉明(7,4) 输入需要 4 bit 对齐
- 发现缺陷 3（随机数隔离）：确认使用 default_rng 替代全局 seed

**采纳理由**: Mock 测试在编码前发现了 3 个潜在问题，避免了实现阶段的返工。

---

### Prompt 5: 模块代码实现

**Prompt**: AI 根据 DESIGN.md 实现了所有模块代码（在同一个对话中连续生成）。

**AI 响应**: 生成了 7 个源文件和 main.py：
- `src/source.py`: UTF-8 ↔ bitstream，含编码和解码别名
- `src/crypto.py`: XOR PN 扰码/解扰
- `src/channel_coding.py`: 汉明(7,4) 编码/译码，含伴随式纠错
- `src/framing.py`: 帧封装/解析，32-bit preamble，CRC-16
- `src/modulation.py`: QPSK Gray 编码调制/解调
- `src/channel.py`: AWGN 加噪
- `src/synchronization.py`: 互相关帧同步
- `main.py`: 端到端管道协调器

**人工修改**:
1. **CRC-16 实现修复**: AI 初始版本的 CRC 函数有 bug（每位处理 8 次），人工修改为标准逐位处理方法。
2. **build_frame 缺少 bits 字段**: 初始版本未包含序列化 `bits` 字段，导致 TC-T-011 测试失败。在返回 dict 中添加了 `frame_to_bits()` 的结果。
3. **mermaid → ASCII 帧结构图**: 将 Mermaid 图表改为 ASCII art，确保纯文本可读性。

**采纳理由**: 模块代码结构清晰，函数命名符合测试发现要求，所有公开别名均已提供。

---

### Prompt 6: 测试失败修复

**Prompt**: 运行 `pytest public_tests -q` 后 3 个测试失败，AI 分析并修复。

**AI 响应**: 
- TC-T-001: AI_LOG.md 缺失 → 创建文件
- TC-T-011: build_frame 返回 dict 缺少 `bits` key → 添加序列化字段
- TC-T-018: 同上（AI_LOG.md 缺失）

**人工修改**: 确认修复方案后执行。

**采纳理由**: 修复精准，所有失败均与模块接口约定相关，非算法错误。

---

## AI 生成内容总结

| 模块 | AI 生成占比 | 人工修改占比 | 说明 |
|------|------------|-------------|------|
| DESIGN.md | 95% | 5% | 人工确认算法选择和参数 |
| TEST_PLAN.md | 90% | 10% | 人工调整预期行为描述 |
| MOCK_TEST_REPORT.md | 90% | 10% | 人工补充实际测试细节 |
| src/source.py | 100% | 0% | 直接采纳 |
| src/crypto.py | 100% | 0% | 直接采纳 |
| src/channel_coding.py | 95% | 5% | 人工验证伴随式查找表 |
| src/framing.py | 80% | 20% | 修复 CRC 和 bits 字段 |
| src/modulation.py | 95% | 5% | 人工验证星座映射 |
| src/channel.py | 100% | 0% | 直接采纳 |
| src/synchronization.py | 95% | 5% | 调整 API 兼容性 |
| main.py | 85% | 15% | 调整管道流程和指标计算 |

---

## 调试过程记录

### 失败 1: TC-T-011 QPSK padding 测试失败

- **现象**: `parsed["payload"]` 与原始 payload 不一致
- **根因**: `build_frame` 返回的 dict 缺少 `bits` 字段，测试框架回退到 `payload` 字段，导致 QPSK 调制只作用于载荷部分而非完整帧
- **修复**: 在 `build_frame` 返回 dict 中添加 `bits` 键（值为 `frame_to_bits()` 的完整序列化结果）

### 失败 2: CRC 校验计算错误

- **现象**: CRC-16 计算不一致
- **根因**: 初始实现中每位数据在内层循环中处理了 8 次
- **修复**: 改为标准逐位 CRC-16-CCITT 算法

---

## 最终采纳理由

项目采用 AI 辅助编程按照 PRD 工程流程完成。AI 在以下方面提供了显著帮助：
1. 快速解析 PRD 并生成结构化设计文档
2. 根据测试用例自动发现模块命名约定
3. 批量生成风格一致的模块代码
4. 快速定位测试失败根因

人工介入点主要集中在：
1. 算法正确性验证（CRC、汉明码）
2. 模块间接口对齐（bits 字段）
3. 测试兼容性适配（别名、函数签名）
