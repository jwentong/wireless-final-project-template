# AI 辅助编程日志

## Prompt 1：系统架构设计
**提示词**：

> 设计一个无线通信基带仿真系统，包含 QPSK 调制、AWGN 信道和帧同步。

**AI 生成内容**：提出了模块化架构，包括信源编码、加扰、汉明编码、帧构建、QPSK 调制、AWGN 信道、同步和指标输出模块。

**人工修改**：直接采纳。模块结构与 PRD 要求一致。

## Prompt 2：汉明码 (7,4) 实现
**提示词**：

> 实现汉明码 (7,4) 信道编解码，使用校正子进行错误纠正。

**AI 生成内容**：生成了带生成矩阵 G 和校验矩阵 H 的编解码函数。

**人工修改**：验证了校正子表映射，修正了比特顺序以匹配系统形式。原因：初始实现使用了非系统形式，难以验证正确性。

## Prompt 3：帧同步实现
**提示词**：

> 通过前导码互相关实现帧同步。

**AI 生成内容**：提供了基于已知前导码符号的相关检测实现。

**人工修改**：修正了匹配滤波器实现——将 `preamble.conj()` 改为 `preamble`，以正确计算 `sum(rx * conj(preamble))`。添加了可选的前导码参数以兼容测试。

## Prompt 4：AWGN 信道
**提示词**：

> 实现 AWGN 信道，支持可控 SNR 和可复现的随机种子。

**AI 生成内容**：生成了使用 numpy RandomState 实现可复现性的信道函数。

**人工修改**：调整 SNR 定义以匹配 PRD 中的 Es/N0 约定。原因：PRD 要求符号级 SNR 定义。

## Prompt 5：主入口与指标输出
**提示词**：

> 创建 main.py 入口点，包含 argparse CLI、完整链路、metrics.json 输出和图表生成。

**AI 生成内容**：生成了完整的 main.py，包括参数解析、系统链路、指标计算和 matplotlib 图表。

**人工修改**：将校验码计算从帧载荷移至原始加扰数据，确保汉明解码后校验仍能正确工作。原因：实现信道解码后的有效错误检测。

## Prompt 6：Mock 测试实现
**提示词**：

> 为每个模块编写 pytest mock 测试（不要参考public_tests），验证模块的正确性。

**AI 生成内容**：生成 6 个测试文件共 39 个测试用例，覆盖正常路径、边界条件和异常场景。

**人工修改**：
- 将测试按模块拆分为独立文件，每个文件使用 class 组织，提高可维护性。
- 添加 `conftest.py` 抽取共享 fixtures（`sample_text`、`test_payload`、`qpsk_preamble`），消除测试间冗余。
- 为帧同步测试添加了大偏移(128 符号)场景，验证极限情况下的检测可靠性。
- 为 AWGN 测试添加了 SNR=0dB 时噪声功率≈信号功率的理论验证。

## Prompt 7：卷积码 + Viterbi 译码器
**提示词**：

> 为系统增加可扩展的卷积码模块，在命令行选项 --fec 中可选 hamming 或 convolutional。实现 Rate 1/2、K=7、生成多项式 (133, 171)_8 的卷积编码器和 64 状态 Viterbi 硬判决译码器，保持原有汉明码不受影响。

**AI 生成内容**：生成了 `src/fec.py`，包含：
- `conv_encode()` — Rate 1/2 卷积编码器，自动添加 6 位尾比特
- `viterbi_decode()` — 64 状态 Viterbi 译码器，Hamming 距离分支度量、回溯译码
- 预计算状态转移表和期望输出表（编译期初始化）
- `FEC_SCHEMES` 注册表和 `get_fec()` 工厂函数
- 同时将汉明码从 `src/channel_coding.py` 迁移到 `src/fec.py` 中，`FEC_SCHEMES["hamming"]` 保留原有实现

## Prompt 8：CRC-32 校验 + 可扩展校验框架
**提示词**：

> 实现 CRC-32 校验函数，保持现有 XOR-8 不变，通过 --checksum 参数切换。parse_frame 需要支持变长校验位。

**AI 生成内容**：
- `src/checksum.py`：使用 `zlib.crc32` 的 CRC-32 实现，输出 32 位比特列表
- `CHECKSUM_SCHEMES` 注册表和 `get_checksum_fn()` / `get_checksum_len()` 工厂函数
- `src/framing.py` 中 `parse_frame` 增加 `checksum_len` 参数（默认 8）

**人工修改**：将 `get_checksum_fn("xor8")` 延迟导入引用 `framing.xor_checksum` 而不是复制实现，消除代码重复。

## Prompt 9：Rayleigh 平坦衰落信道
**提示词**：

> 在信道模块中增加 Rayleigh 平坦衰落信道模型，通过 --channel rayleigh 选择。包含复高斯衰落系数、AWGN 和 ZF 均衡，保持与现有 awgn 相同的接口。

**AI 生成内容**：`src/channel.py` 中增加 `rayleigh_fading()` 函数，生成 Rayleigh 分布衰落系数，应用衰落、添加 AWGN 后进行 ZF 均衡。

## Prompt 10：可扩展 CLI 架构重构
**提示词**：

> 重构 main.py 使用工厂调度表，新增 --fec、--checksum、--scramble 三个 CLI 参数，使所有模块可独立切换。所有原有命令和默认行为不变。

**AI 生成内容**：重写 `main.py`，使用调度表替代硬编码函数调用，新增 3 个 argparse 参数。`ber_curve()` 函数增加 `fec_decode_fn` 和 `descramble_fn` 参数以支持可切换 FEC。

**人工修改**：

- 调整 `ber_curve` 使用 AWGN 信道（而非当前选中的信道模型）绘制 BER 曲线，确保曲线只反映 FEC 性能而非信道差异

## Prompt 11：新增模块测试 + 文档更新
**提示词**：

> 为新增模块编写 pytest 测试，更新 DESIGN.md 和 MOCK_TEST_REPORT.md。

**AI 生成内容**：
- `tests/test_mock_fec.py` — 7 个测试：无噪可逆、变长输入、单比特纠错、工厂选择
- `tests/test_mock_rayleigh.py` — 4 个测试：可复现、长度一致、功率验证、高 SNR 恢复
- `tests/test_mock_checksum.py` — 7 个测试：32 位输出、确定性、输入区分、工厂函数
- `DESIGN.md` — 新增 CLI 参数表、FEC/信道/校验算法说明、Rayleigh 风险项
- `MOCK_TEST_REPORT.md` — 新增 13 个测试用例、4 个 CLI 运行示例

**测试结果**：全部 79 个测试通过（61 原有 + 18 新增）。

```bash
(wireless_communication) C:\Users\Alex\MyDocuments\Technology\ICT\Python\projects\wireless-final-project-template>python -m pytest public_tests tests/ -q
...............................................................................                                  [100%]
79 passed in 19.59s
```

## Prompt 12：新增 BPSK 和 16-QAM 调制方式
**提示词**：

> 调制方式新增支持 BPSK 和 16-QAM。

**AI 生成内容**：
- `src/modulation.py`：新增 `bpsk_modulate()` / `bpsk_demodulate()`（1 比特/符号，0→+1, 1→-1）和 `qam16_modulate()` / `qam16_demodulate()`（4 比特/符号，Gray 编码矩形星座，`1/sqrt(10)` 归一化）
- `main.py`：新增 `MODULATION_MAP` 派发表，`ber_curve()` 和 `main()` 中根据 `--mod`（可选 `bpsk`、`qpsk`、`16qam`）动态选择调制/解调函数
- `tests/test_mock_modulation.py`：新增 `TestBPSKModulation`（5 个测试）和 `TestQAM16Modulation`（9 个测试），覆盖象限验证、功率归一化、无噪环回、padding、全星座点解映射
- `DESIGN.md`：更新系统架构、模块接口、算法选择、参数表和 CLI 表

**人工修改**：修改了命令行入口的解析bug，确保运行正常

测试结果：


```bash
(wireless_communication) C:\Users\Alex\MyDocuments\Technology\ICT\Python\projects\wireless-final-project-template>python -m pytest public_tests tests/ -q
............................................................................................                     [100%]
92 passed in 20.65s
```

