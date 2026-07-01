# AI_LOG.md - AI 辅助编程记录

本项目使用 Claude 进行 AI 辅助编程。记录关键 prompt、AI 生成内容、人工修改内容、测试失败修复过程和最终采纳理由。

## Prompt 1：需求理解

**Prompt**：读取 GitHub 仓库中的 `README.md` 和 `PRD.docx`，梳理期末项目的完整要求（提交物、统一命令行、分级标准、验收流程）。

**AI 生成内容**：对 PRD 各章节的结构化总结，包括固定系统链路、metrics.json 最低字段、分级要求、GitHub Fork+PR 提交流程。

**人工修改**：无实质修改，作为后续设计的输入依据被采纳。

## Prompt 2：整体架构与模块划分

**Prompt**：按照 PRD 固定链路（Source Encode -> Scramble -> Channel Encode -> Frame Build -> QPSK Modulate -> Channel -> Sync -> Demodulate -> Channel Decode -> Descramble -> Source Decode）设计 `src/` 下的模块划分和函数接口，同时要兼容 `public_tests` 里通过 `find_function` 做的多命名兼容查找。

**AI 生成内容**：`src/source.py`、`src/scramble.py`、`src/channel_coding.py`、`src/framing.py`、`src/modulation.py`、`src/channel.py`、`src/synchronization.py` 的初版实现，以及每个函数的兼容别名。

**人工修改**：运行 `pytest public_tests -q` 后发现 checksum 校验逻辑存在"文本正确但 checksum_pass=false"的矛盾（见 MOCK_TEST_REPORT.md 场景 3），人工介入分析原因后，指导 AI 在 `main.py` 增加了 FEC 纠错后的端到端 CRC16 校验层，替换了直接使用帧内 checksum 的做法。

**采纳理由**：修改后 `checksum_pass` 与 `text_match_rate` 的结论一致，避免误导性指标，采纳该修订。

## Prompt 3：同步模块与主流程编排

**Prompt**：实现基于归一化相关的帧同步检测，并在 `main.py` 中把 25 个符号的随机偏移、AWGN 信道、metrics.json 输出、三张图表生成整合成统一 CLI 入口。

**AI 生成内容**：`src/synchronization.py` 的 `synchronize` 函数（滑动窗口归一化相关）、`main.py` 的 `transmit/add_sync_offset/receive/main` 完整流程。

**人工修改**：验证 `sync_start_index` 输出是否精确等于插入的偏移值（25），确认无误后保留该实现；对 `main.py` 里 checksum 相关变量命名做了小幅调整以提高可读性。

**采纳理由**：多次运行 `python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn` 均得到 `text_match_rate=1.0000`、`sync_start_index=25`、`checksum_pass=True`，符合 PRD 6.1 节"公开基础通过条件"，予以采纳。

## Prompt 4：测试失败修复过程

**Prompt**：跑 `pytest public_tests -q`，发现最初只有文档文件缺失导致的失败（`DESIGN.md/TEST_PLAN.md/MOCK_TEST_REPORT.md/AI_LOG.md` 尚未生成），所有 17 个代码相关测试均已通过；请补全文档使全部 22 个用例通过。

**AI 生成内容**：`DESIGN.md`、`TEST_PLAN.md`、`MOCK_TEST_REPORT.md`、本文件 `AI_LOG.md`、`REPORT.md` 的完整初稿。

**人工修改**：核对 DESIGN.md 中关于 length 字段换算关系的描述与实际代码实现（`channel_coding.py` 中 `REPEAT=3`）是否一致，确认一致后未做改动。

**采纳理由**：文档内容与实际代码行为、mock 测试发现的问题一一对应，不是空洞套话，予以采纳并提交。

## 总结

AI 承担了模块代码的初版生成、文档撰写和测试排查建议；人工承担了需求歧义的判断（如 PRD 6.1 length 字段语义与第 3 节链路顺序的冲突如何取舍）、mock 测试结果的解读、以及最终是否采纳 AI 修改建议的决策。所有关键设计取舍均已在 DESIGN.md 和本记录中说明理由。
