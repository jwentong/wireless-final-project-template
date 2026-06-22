# AI_LOG.md

## Prompt 1：阅读 PRD 和公开测试，生成设计与模块清单

提示：查看 `PRD.docx`、`request.md`、`README.md` 和 `public_tests/`，提出无线通信期末项目修改方案。

AI 生成内容：整理固定系统链路、必须导出的函数名、文档要求、公开测试 20 条和隐藏验证风险。

人工修改：确认不做 Level 3 扩展，优先实现 Level 2 完整基础系统；保留 `numpy`、`matplotlib`、`pytest` 轻量依赖。

采纳理由：该方案能覆盖公开测试和隐藏基础验证，同时保持答辩时容易解释。

## Prompt 2：实现 source、scramble、coding、framing、qpsk、awgn、sync

提示：按设计实现模块化 Python 代码，保证公开测试可导入别名。

AI 生成内容：生成 UTF-8 Source Encode、PN XOR Scramble、3 重复码 Channel Encode、Frame Build、Gray QPSK、AWGN Channel 和 Synchronization。

人工修改：调整帧字段为 `length + coded_length + checksum`，并加入异常长度兜底，避免低 SNR 下直接崩溃。

采纳理由：重复码、PN XOR、CRC32、相关同步和 Gray QPSK 都是课程基础内容，易解释且足以满足基础验收。

## Prompt 3：运行公开测试，修复失败

提示：运行 `pytest public_tests -q` 和自测，根据错误修复实现。

AI 生成内容：补齐公开测试需要的函数别名、CLI 参数、metrics 字段和 PNG 输出。

人工修改：检查 `checksum_pass`、`text_match_rate`、`sync_start_index` 的含义，确保 metrics 与代码行为一致。

采纳理由：公开测试只覆盖基础正确性，额外保留 failure_reason、crc_actual、prefix_len 等字段有助于隐藏验证和答辩说明。

## Prompt 4：完善 metrics、plots、文档和鲁棒性

提示：补齐 `DESIGN.md`、`TEST_PLAN.md`、`MOCK_TEST_REPORT.md`、`AI_LOG.md`，生成自测并完成端到端验收。

AI 生成内容：编写设计文档、mock 测试报告、AI 使用记录和 pytest 自测。

人工修改：拒绝了直接复制 `Test.txt` 到 `received.txt`、硬编码公开样例、过度复杂 OFDM/Rayleigh 扩展等方案。

采纳理由：最终实现遵守学术诚信限制，输出文件由接收端 Source Decode 产生，文档与代码保持一致。

## Prompt 5：增加 Level 3 Rayleigh 提高模块

提示：在不破坏公开测试默认 AWGN 链路的前提下，增加一个 Level 3 提高模块。

AI 生成内容：增加 `rayleigh` flat fading Channel、基于 preamble 的信道估计和一拍均衡、Rayleigh 自测和文档说明。

人工修改：将 Rayleigh 设计为可选 `--channel rayleigh`，默认仍为 `--channel awgn`，避免影响基础验收。选择 block fading 而不是完整 OFDM 或多径模型，是因为该方案更容易解释和测试。

采纳理由：Rayleigh 衰落和均衡属于无线通信课程提高内容，能提升项目完整度，同时保持代码复杂度可控。