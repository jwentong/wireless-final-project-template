# TEST_PLAN.md -- 无线通信基带仿真系统测试计划

## 1. 测试策略概述

本测试计划覆盖无线通信基带仿真系统的全部模块和端到端流水线。测试分为四个层次：

1. **模块单元测试**：对 src/ 下各个独立模块进行白盒测试，验证每个模块的输入输出正确性。
2. **集成测试**：验证模块间接口协作和完整流水线。
3. **教师公开测试**：public_tests/ 目录下的 20 条 BDD 场景，覆盖 TC-T-001 至 TC-T-020。
4. **自测边界用例**：针对极端输入、异常参数、反硬编码检查等补充测试。

测试运行命令：

```bash
pytest public_tests -q          # 教师公开测试
pytest tests/ -q                # 学生自测（模块单测 + 集成测试）
pytest tests/ public_tests/ -q  # 全部测试
```

---

## 2. 模块单元测试计划

### 2.1 源编解码模块 (src/source.py)

**待测函数**: `source_encode` / `text_to_bits` 和 `source_decode` / `bits_to_text`

| 测试编号 | 测试名称 | 测试输入 | 预期输出 | 优先级 |
|---------|---------|---------|---------|-------|
| UT-SRC-001 | UTF-8 中文文本编码可逆 | Test.txt 300 字中文课程描述 | 编码得到 bitstream，解码恢复原文完全一致 | P0 |
| UT-SRC-002 | 空文本编码 | 空字符串 "" | bitstream 为空列表 [] 或长度 0，解码也为空 | P1 |
| UT-SRC-003 | ASCII 英文字符 | "Hello World!" | 编解码可逆，bitstream 长度为 8 的整数倍 | P1 |
| UT-SRC-004 | 特殊字符与表情符号 | "测试😀∑αβγ\n\t\r" | 含 4 字节 UTF-8 字符，编解码可逆 | P1 |
| UT-SRC-005 | bitstream 长度验证 | 任意 UTF-8 文本 | bitstream 长度必须是 8 的整数倍 | P0 |
| UT-SRC-006 | 极长文本 (10000+ 字符) | 10000 个中文字符 | 编解码可逆，无性能退化或内存溢出 | P2 |
| UT-SRC-007 | 纯数字文本 | "0123456789" | 编解码可逆，与 ASCII 数字编码一致 | P2 |
| UT-SRC-008 | 解码空 bitstream | 空列表 [] | 返回空字符串 ""，不应抛出异常 | P2 |

**对应公开测试**：TC-T-004 (UTF-8 中文文本源编码可逆)

---

### 2.2 扰码/加密模块 (src/scramble.py 或 src/crypto.py)

**待测函数**: `scramble` / `encrypt` 和 `descramble` / `decrypt`

| 测试编号 | 测试名称 | 测试输入 | 预期输出 | 优先级 |
|---------|---------|---------|---------|-------|
| UT-SCR-001 | 固定种子可逆性 | 随机 511 bit，seed=2026 | 加扰再解扰后与原始 bitstream 完全一致 | P0 |
| UT-SCR-002 | 不同种子产生不同输出 | 同一 bitstream，seed=2026 和 seed=42 | 两个加扰输出不同，验证种子确实影响结果 | P0 |
| UT-SCR-003 | 空 bitstream | 空列表 [] | 加扰解扰后仍为空，不抛出异常 | P1 |
| UT-SCR-004 | 全零 bitstream | 1000 个 0 | 加扰后不再是全零（验证确实发生了扰码），解扰后恢复全零 | P1 |
| UT-SCR-005 | 全一 bitstream | 1000 个 1 | 加扰后不再是全一，解扰后恢复全一 | P1 |
| UT-SCR-006 | 长序列稳定性 | 100000 个随机 bit | 加扰解扰完全可逆，无偏移或截断 | P2 |
| UT-SCR-007 | 错误种子解扰 | 加扰 bitstream，用不同 seed 解扰 | 解扰结果与原始不同（验证种子安全性） | P2 |
| UT-SCR-008 | 确定性验证 | 同一输入+同一种子，执行两次 | 两次加扰输出逐位一致（确定性算法） | P1 |

**对应公开测试**：TC-T-007 (扰码或加密模块可逆)

---

### 2.3 信道编解码模块 (src/channel_coding.py)

**待测函数**: `channel_encode` 和 `channel_decode`

| 测试编号 | 测试名称 | 测试输入 | 预期输出 | 优先级 |
|---------|---------|---------|---------|-------|
| UT-COD-001 | 无噪声编解码可逆 | 随机 400 bit，无噪声 | 编码再译码后与原 bitstream 完全一致 | P0 |
| UT-COD-002 | 编码引入冗余 | 原始 bitstream 长度 N | 编码后 bitstream 长度 > N（验证冗余添加） | P0 |
| UT-COD-003 | 单比特错误纠正 | 编码后翻转 1 个 bit | 译码后与原 bitstream 一致（验证纠错能力） | P0 |
| UT-COD-004 | 多比特错误部分纠正 | 编码后翻转少量 (如 3-5) 个 bit | BER 低于无纠错时的理论值 | P1 |
| UT-COD-005 | 严重错误下的降级行为 | 编码后翻转 50% bit | 译码不崩溃，但结果很可能不同（合理降级） | P2 |
| UT-COD-006 | 空输入 | 空 bitstream | 编码译码后仍为空 | P1 |
| UT-COD-007 | 极短输入 | 仅 8 bit | 编码和译码均正常完成，可逆 | P1 |
| UT-COD-008 | 长序列 | 10000+ bit | 编解码可逆，无性能问题 | P2 |
| UT-COD-009 | 译码输入长度验证 | 非法长度编码数据 | 要么拒绝并报错，要么正确处理（不静默损坏） | P2 |

**对应公开测试**：TC-T-008 (信道编码和译码在无噪声下可逆)

---

### 2.4 帧封装/解析模块 (src/framing.py)

**待测函数**: `build_frame` 和 `parse_frame`

| 测试编号 | 测试名称 | 测试输入 | 预期输出 | 优先级 |
|---------|---------|---------|---------|-------|
| UT-FRM-001 | 帧包含 preamble | 2400 bit payload | 生成的帧包含前导码字段 | P0 |
| UT-FRM-002 | 帧包含 length | 2400 bit payload | 生成的帧包含长度字段 | P0 |
| UT-FRM-003 | 帧包含 payload | 2400 bit payload | 生成的帧包含有效载荷字段 | P0 |
| UT-FRM-004 | 帧包含 checksum/CRC | 2400 bit payload | 生成的帧包含校验和或 CRC 字段 | P0 |
| UT-FRM-005 | 帧结构可逆 | 257 bit payload | parse_frame(build_frame(payload)) == payload | P0 |
| UT-FRM-006 | length 字段准确性 | 257 bit payload | 解析得到的 length 等于 257 | P0 |
| UT-FRM-007 | 空 payload | 空 bitstream | build_frame 和 parse_frame 正常处理，不崩溃 | P1 |
| UT-FRM-008 | 极短 payload | 8 bit | 帧结构正确，可逆 | P1 |
| UT-FRM-009 | 极长 payload | 100000 bit | 帧结构正确，可逆 | P2 |
| UT-FRM-010 | checksum 校验通过 | 完好帧 | parse_frame 返回 checksum_pass=True | P1 |
| UT-FRM-011 | checksum 校验失败 | 篡改 payload 的帧 | parse_frame 返回 checksum_pass=False | P1 |
| UT-FRM-012 | 损坏帧的稳健性 | 随机翻转帧中若干 bit | parse_frame 不崩溃，返回错误标志或尽力解析 | P2 |
| UT-FRM-013 | 前导码格式验证 | 固定已知 preamble | 生成帧的前导码与设计规范一致 | P1 |

**对应公开测试**：TC-T-005 (帧结构包含 PRD 要求字段), TC-T-006 (帧封装和解析可逆)

---

### 2.5 调制解调模块 (src/modulation.py)

**待测函数**: `qpsk_modulate` 和 `qpsk_demodulate`

| 测试编号 | 测试名称 | 测试输入 | 预期输出 | 优先级 |
|---------|---------|---------|---------|-------|
| UT-MOD-001 | QPSK Gray 映射 -- 00 第一象限 | [0,0] | 符号实部>0, 虚部>0 | P0 |
| UT-MOD-002 | QPSK Gray 映射 -- 01 第二象限 | [0,1] | 符号实部<0, 虚部>0 | P0 |
| UT-MOD-003 | QPSK Gray 映射 -- 11 第三象限 | [1,1] | 符号实部<0, 虚部<0 | P0 |
| UT-MOD-004 | QPSK Gray 映射 -- 10 第四象限 | [1,0] | 符号实部>0, 虚部<0 | P0 |
| UT-MOD-005 | QPSK 符号功率归一化 | 随机 512 bit | 平均符号功率约等于 1.0 (0.8~1.2 范围内) | P0 |
| UT-MOD-006 | QPSK 无噪声解调无误码 | 随机 512 bit | 解调 bitstream == 输入 bitstream | P0 |
| UT-MOD-007 | 输入长度为奇数时处理 | 奇数长度 bitstream | 调制正常（自动补零或报错），解调后根据 length 去除 padding | P0 |
| UT-MOD-008 | BPSK 调制解调无噪声可逆 | 随机 256 bit, BPSK | 解调 bitstream == 输入 bitstream | P1 |
| UT-MOD-009 | 16QAM 调制解调无噪声可逆 | 随机 1024 bit, 16QAM | 解调 bitstream == 输入 bitstream | P1 |
| UT-MOD-010 | BPSK vs QPSK 频谱效率对比 | 相同 bit 数 | QPSK 符号数约为 BPSK 的一半 | P2 |
| UT-MOD-011 | 16QAM vs QPSK 误码率对比 | 固定 SNR=10dB | 16QAM 的 BER 高于 QPSK（高阶调制对噪声更敏感） | P2 |
| UT-MOD-012 | Gray 编码相邻符号只差 1 bit | 任意相邻星座点 | 对应 bit 对的汉明距离为 1 | P1 |
| UT-MOD-013 | 调制输出为复数类型 | 任意输入 | 所有输出元素均为 complex 类型 | P1 |
| UT-MOD-014 | 空输入 | 空列表 [] | 输出空列表 | P2 |

**对应公开测试**：TC-T-009 (QPSK 映射符合 PRD), TC-T-010 (QPSK 无噪声调制解调无误码), TC-T-011 (QPSK padding 能被 length 字段去除)

---

### 2.6 信道模块 (src/channel.py)

**待测函数**: `awgn` / `awgn_channel` / `add_awgn`

| 测试编号 | 测试名称 | 测试输入 | 预期输出 | 优先级 |
|---------|---------|---------|---------|-------|
| UT-CHN-001 | AWGN 固定 seed 可复现 | QPSK 符号, snr=12, seed=2026 | 两次调用输出完全一致 (allclose) | P0 |
| UT-CHN-002 | 不同 seed 不同输出 | 同一输入, seed=2026 和 seed=42 | 两次输出不同（种子影响噪声） | P0 |
| UT-CHN-003 | 高 SNR (30dB) 近乎无噪声 | QPSK 符号, snr=30 | 输出与输入接近（MAE 很小） | P1 |
| UT-CHN-004 | 低 SNR (0dB) 明显噪声 | QPSK 符号, snr=0 | 输出与输入差异显著 | P1 |
| UT-CHN-005 | BER 随 SNR 升高单调下降 | QPSK 符号, 多个 SNR 点 | -5dB 到 15dB，BER 单调递减 | P1 |
| UT-CHN-006 | 无信号输入的纯噪声 | 全零符号序列 | 输出为纯噪声，不为零 | P2 |
| UT-CHN-007 | SNR 参数边界 -- 极端高 (100dB) | snr=100 | 输出几乎等于输入，不溢出 | P2 |
| UT-CHN-008 | SNR 参数边界 -- 负数 (-10dB) | snr=-10 | 噪声功率 >> 信号功率，不崩溃 | P2 |
| UT-CHN-009 | 零输入 | 零向量符号 | 输出为非零噪声（AWGN 的加性特性） | P2 |
| UT-CHN-010 | 输出维度一致性 | N 个输入符号 | 输出长度为 N（不截断不补零） | P1 |

**对应公开测试**：TC-T-012 (AWGN 信道固定 seed 可复现)

---

### 2.7 同步模块 (src/synchronization.py)

**待测函数**: `synchronize` / `detect_frame_start` / `find_preamble`

| 测试编号 | 测试名称 | 测试输入 | 预期输出 | 优先级 |
|---------|---------|---------|---------|-------|
| UT-SYN-001 | 无偏移精确检测 | preamble + payload，无偏移 | 检测到的起始位置为 0 | P1 |
| UT-SYN-002 | 25 符号前置偏移检测 | 25 个噪声 + preamble + payload | 误差不超过 1 个符号位置 | P0 |
| UT-SYN-003 | 无噪声下精确检测 | preamble + payload，无噪声 | 检测误差为 0 | P1 |
| UT-SYN-004 | SNR=12dB 检测精度 | 偏移 preamble，SNR=12dB | 检测误差 <= 1 | P0 |
| UT-SYN-005 | SNR=6dB 检测鲁棒性 | 偏移 preamble，SNR=6dB | 检测误差 <= 2（低 SNR 允许略大误差） | P1 |
| UT-SYN-006 | SNR=0dB 降级行为 | 偏移 preamble，SNR=0dB | 模块不崩溃，返回结果（可能失败） | P2 |
| UT-SYN-007 | 大偏移量 (100 符号) | 100 个噪声 + preamble | 检测到的偏移约 100，误差 <= 2 | P2 |
| UT-SYN-008 | 无 preamble 信号 | 纯噪声 | 不返回无效帧起始（返回 -1 或特殊标记） | P2 |
| UT-SYN-009 | 同步峰值幅度验证 | preamble + payload | 在正确位置产生明显相关峰值 | P1 |
| UT-SYN-010 | 空输入 | 空列表 | 返回 -1 或空结果，不崩溃 | P2 |

**对应公开测试**：TC-T-013 (同步模块检测 25 符号前置偏移)

---

### 2.8 Metrics 模块 (src/metrics.py 或 main.py 内联)

| 测试编号 | 测试名称 | 测试输入 | 预期输出 | 优先级 |
|---------|---------|---------|---------|-------|
| UT-MET-001 | metrics.json 完整字段 | 完整流水线运行 | 包含 snr_db, seed, modulation, channel, payload_bits, ber, fer, text_match_rate, checksum_pass, sync_start_index | P0 |
| UT-MET-002 | BER 计算正确 | 已知差异的两个 bitstream | BER == 不同 bit 数 / 总 bit 数 | P1 |
| UT-MET-003 | FER 计算正确 | 多帧，部分帧校验失败 | FER == 失败帧数 / 总帧数 | P1 |
| UT-MET-004 | text_match_rate 完全匹配 | received.txt == Test.txt | text_match_rate == 1.0 | P0 |
| UT-MET-005 | text_match_rate 部分匹配 | received 与发送有差异 | 0 <= text_match_rate < 1.0 | P1 |
| UT-MET-006 | checksum_pass 布尔值 | CRC 匹配的帧 | checksum_pass == True | P0 |

**对应公开测试**：TC-T-014 (metrics.json 包含最低字段)

---

### 2.9 可视化图表模块

| 测试编号 | 测试名称 | 测试内容 | 预期输出 | 优先级 |
|---------|---------|---------|---------|-------|
| UT-VIS-001 | 星座图生成 | QPSK AWGN 接收符号 | results/constellation.png 非空 | P0 |
| UT-VIS-002 | BER 曲线图生成 | 多 SNR 点 BER 数据 | results/ber_curve.png 非空 | P0 |
| UT-VIS-003 | 同步峰值图生成 | 相关检测峰值 | results/sync_peak.png 非空 | P1 |
| UT-VIS-004 | 至少生成两张图 | 完整流水线 | 三个候选图至少存在两个 | P0 |

**对应公开测试**：TC-T-016 (生成至少两类可视化图表)

---

## 3. 集成测试计划

### 3.1 模块间接口集成测试

| 测试编号 | 测试名称 | 测试链路 | 验证点 | 优先级 |
|---------|---------|---------|-------|-------|
| IT-PIP-001 | 源编码 -> 帧封装 | source_encode -> build_frame | 帧字段完整，payload 来源于正确编码 | P0 |
| IT-PIP-002 | 帧封装 -> 扰码 | build_frame -> scramble | 扰码后的帧仍可被 descramble 恢复 | P0 |
| IT-PIP-003 | 扰码 -> 信道编码 | scramble -> channel_encode | 编码后长度增加 | P1 |
| IT-PIP-004 | 信道编码 -> 调制 | channel_encode -> qpsk_modulate | 调制符号数正确，无数据丢失 | P1 |
| IT-PIP-005 | 调制 -> AWGN -> 解调 | modulate -> awgn -> demodulate | 在 SNR=12dB 下 BER 可接受 | P0 |
| IT-PIP-006 | 解调 -> 同步 -> 帧解析 | demodulate -> synchronize -> parse_frame | 同步找到帧起始，帧正确解析 | P0 |
| IT-PIP-007 | 帧解析 -> 信道译码 -> 解扰 -> 源解码 | parse_frame -> channel_decode -> descramble -> source_decode | 无噪声下完全可逆 | P0 |
| IT-PIP-008 | 帧解析 -> padding 去除 | parse_frame + length | 根据 length 字段正确去除 QPSK 调制的 padding | P0 |

### 3.2 端到端流水线测试

| 测试编号 | 测试名称 | 参数 | 验证点 | 优先级 |
|---------|---------|------|-------|-------|
| IT-E2E-001 | SNR=12dB QPSK AWGN 完全恢复 | --snr 12 --seed 2026 --mod qpsk --channel awgn | received.txt == Test.txt, text_match_rate=1.0 | P0 |
| IT-E2E-002 | SNR=20dB 高信噪比 | --snr 20 --seed 2026 --mod qpsk --channel awgn | received.txt == Test.txt | P1 |
| IT-E2E-003 | SNR=8dB 低信噪比 | --snr 8 --seed 2026 --mod qpsk --channel awgn | 程序正常完成，BER 合理 (高于 12dB) | P1 |
| IT-E2E-004 | SNR=4dB 极端低信噪比 | --snr 4 --seed 2026 --mod qpsk --channel awgn | 程序不崩溃，metrics.json 记录正确 BER | P2 |
| IT-E2E-005 | 不同随机种子可复现性 | seed=2026, seed=42 | 两次运行可能结果不同，但各自 metrics 正确 | P1 |
| IT-E2E-006 | 不同文本输入 | 自定义 Test.txt (英文/数字/空) | 端到端正确恢复 | P1 |
| IT-E2E-007 | BPSK 调制端到端 | --mod bpsk --channel awgn --snr 12 | 端到端恢复正确 | P2 |
| IT-E2E-008 | 16QAM 调制端到端 | --mod 16qam --channel awgn --snr 16 | 端到端恢复正确（可能需要更高 SNR） | P2 |
| IT-E2E-009 | 结果文件均生成 | 标准参数 | received.txt, metrics.json, 至少 2 张图 | P0 |
| IT-E2E-010 | 无交互命令行运行 | 标准参数 | 程序无需人工输入即完成 | P0 |

---

## 4. 教师公开测试对照表

public_tests/ 目录下 3 个测试文件共覆盖 20 条 BDD 场景：

### 4.1 test_01_structure_and_documents.py（结构文档检查，6 条）

| 公开测试编号 | BDD 场景 | 测试内容 |
|------------|---------|---------|
| TC-T-001 | 项目目录包含必需提交物 | DESIGN.md, TEST_PLAN.md, MOCK_TEST_REPORT.md, AI_LOG.md, main.py, src/, tests/ |
| TC-T-002 | DESIGN.md 覆盖固定系统链路 | 提及 Source Encode, Encrypt/Scramble, Channel Encode, Frame Build, QPSK, Channel, Synchronization 等 |
| TC-T-003 | MOCK_TEST_REPORT.md 包含设计修订记录 | 至少 3 个 mock 场景, 1 个风险/缺陷, DESIGN.md 修订内容 |
| TC-T-018 | AI_LOG.md 记录 AI 辅助过程 | 至少 3 条 prompt, 人工修改说明, 采纳理由 |
| TC-T-019 | 报告解释关键结果 | QPSK 星座图, BER/text_match_rate, 失败/误码原因 |
| TC-T-020 | 反硬编码直接复制检查 | 源代码中不存在直接将 Test.txt 复制为 received.txt 的逻辑 |

### 4.2 test_02_core_modules.py（核心模块测试，9 条）

| 公开测试编号 | BDD 场景 | 测试内容 |
|------------|---------|---------|
| TC-T-004 | UTF-8 中文文本源编码可逆 | encode -> decode 可逆，bitstream 长度 % 8 == 0 |
| TC-T-005 | 帧结构包含 PRD 要求字段 | frame 含 preamble, length, payload, checksum/CRC |
| TC-T-006 | 帧封装和解析可逆 | parse_frame(build_frame(payload)) == payload，length 正确 |
| TC-T-007 | 扰码/加密模块可逆 | scramble -> descramble 可逆 (seed=2026) |
| TC-T-008 | 信道编解码无噪声可逆 | channel_encode -> channel_decode 可逆 |
| TC-T-009 | QPSK 映射 Gray 编码 | 00/I, 01/II, 11/III, 10/IV 象限，单位功率 |
| TC-T-010 | QPSK 无噪声解调无误码 | qpsk_demodulate(qpsk_modulate(bits)) == bits |
| TC-T-011 | QPSK padding 被 length 去除 | 奇数 payload 经调制解调后根据 length 截断正确 |
| TC-T-012 | AWGN 固定 seed 可复现 | SNR=12dB, seed=2026，两次输出 allclose |

### 4.3 test_03_cli_end_to_end.py（端到端与 CLI 测试，5+2 条）

| 公开测试编号 | BDD 场景 | 测试内容 |
|------------|---------|---------|
| TC-T-013 | 同步模块检测 25 符号前置偏移 | 25 噪声 + preamble，检测误差 <= 1 |
| TC-T-014 | metrics.json 包含最低字段 | 10 个必要字段全部存在 |
| TC-T-015 | SNR=12dB 端到端完全恢复 | received.txt == Test.txt，text_match_rate == 1.0 |
| TC-T-016 | 生成至少两类可视化图表 | constellation.png, ber_curve.png, sync_peak.png 中至少 2 个 |
| TC-T-017 | 统一命令行入口可运行 | 无交互输入，正常退出，returncode == 0 |
| (bonus) | metrics.json 数值正确性 | modulation=qpsk, channel=awgn, seed=2026, snr_db=12 |
| (bonus) | main.py 参数解析 | 支持 --input 和 --output 参数 |

---

## 5. 自测边界用例

以下是针对 PRD 要求之外边界条件和异常场景的补充测试：

### 5.1 输入边界

| 自测编号 | 测试场景 | 输入 | 预期行为 | 优先级 |
|---------|---------|------|---------|-------|
| ST-EDGE-001 | 空 Test.txt | 0 字节文件 | 程序正常退出，received.txt 为空，metrics 中 payload_bits=0 | P1 |
| ST-EDGE-002 | 单字符 Test.txt | "A" | 端到端正确恢复 | P1 |
| ST-EDGE-003 | 全 ASCII 测试文本 | 英文论文摘要 | 端到端正确恢复 | P1 |
| ST-EDGE-004 | 含换行符和制表符 | "行1\n行2\t列3" | 编解码可逆，换行和制表符保留 | P1 |
| ST-EDGE-005 | 全角半角混合 | "ABC１２３测试" | 编解码可逆，全角数字与半角区分 | P2 |
| ST-EDGE-006 | 仅含 Unicode 补充平面字符 | "😀😁😂🤣😃" | 4 字节 UTF-8 编码正确，编解码可逆 | P2 |

### 5.2 参数边界

| 自测编号 | 测试场景 | 参数 | 预期行为 | 优先级 |
|---------|---------|------|---------|-------|
| ST-EDGE-007 | SNR 为 0 | --snr 0 | 程序正常运行，BER 约 0.1~0.3 | P2 |
| ST-EDGE-008 | SNR 为负数 | --snr -10 | 程序正常运行，BER 接近 0.5 | P2 |
| ST-EDGE-009 | 极高 SNR | --snr 100 | 程序正常运行，BER=0，完美恢复 | P2 |
| ST-EDGE-010 | seed 为 0 | --seed 0 | 种子 0 是合法输入，不报错 | P1 |
| ST-EDGE-011 | seed 为大数 | --seed 999999999 | 程序正常，不溢出 | P2 |
| ST-EDGE-012 | 不支持的调制方式 | --mod 256qam | 程序应给出清晰错误信息后退出 | P1 |
| ST-EDGE-013 | 不支持的信道类型 | --channel rayleigh | 程序应给出清晰错误信息后退出 | P1 |
| ST-EDGE-014 | 缺少必要参数 | python main.py (无参数) | 打印 usage 或错误信息，returncode != 0 | P1 |
| ST-EDGE-015 | 输入文件不存在 | --input nonexistent.txt | 给出 "File not found" 错误，returncode != 0 | P1 |
| ST-EDGE-016 | 输出目录不存在 | --output newdir/received.txt | 自动创建目录或报错 | P2 |

### 5.3 反硬编码与安全

| 自测编号 | 测试场景 | 测试方法 | 预期 | 优先级 |
|---------|---------|---------|------|-------|
| ST-EDGE-017 | 文本内容不敏感 | 修改 Test.txt 为完全不同内容 | 端到端仍然正确恢复新内容，不硬编码原文 | P0 |
| ST-EDGE-018 | 不直接复制文件 | 检查 src/ 和 main.py | 无 shutil.copy, copyfile 或等效直接复制逻辑 | P0 |
| ST-EDGE-019 | preamble 不硬编码 | 修改 preamble 参数 | 同步仍然工作，不假设 preamble 固定为某值 | P2 |
| ST-EDGE-020 | SNR 不是固定 12dB | --snr 15 | 结果正确反映 SNR=15dB 的性能 | P1 |

### 5.4 并发与重复运行

| 自测编号 | 测试场景 | 测试方法 | 预期 | 优先级 |
|---------|---------|---------|------|-------|
| ST-EDGE-021 | 多次运行完全可复现 | 同一参数运行 3 次 | 每次 metrics.json 数值一致 (seed 固定) | P1 |
| ST-EDGE-022 | 覆盖已有结果文件 | 运行两次 | 第二次运行覆盖旧的 results/，无残留 | P1 |
| ST-EDGE-023 | results 目录不存在 | 删除 results/ 后运行 | 程序自动创建目录并写入 | P1 |
| ST-EDGE-024 | 只读保护目录 | 尝试写入只读目录 | 给出 "Permission denied" 错误，不静默失败 | P2 |

---

## 6. 测试执行流程

### 6.1 本地开发阶段

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行模块单元测试
pytest tests/ -v

# 3. 运行公开测试
pytest public_tests -v

# 4. 运行全部测试
pytest tests/ public_tests/ -v --tb=short
```

### 6.2 CI 阶段 (GitHub Actions)

推送到 Fork 仓库并创建 Pull Request 后，grading.yml 工作流自动执行：

1. `pip install -r requirements.txt`
2. `pytest public_tests -q --tb=short`
3. `python grading/summarize_public_tests.py` 生成评分摘要
4. 评分摘要自动评论到 Pull Request

### 6.3 测试覆盖率目标

| 测试层次 | 目标覆盖率 |
|---------|----------|
| 模块单元测试 | 每个模块 >= 80% 行覆盖 |
| 集成测试 | 覆盖发送端、信道、接收端全链路 |
| 公开测试 | 20/20 全部通过 |
| 自测边界 | 覆盖所有 P0 和 P1 用例 |

---

## 7. 测试目录结构

```
tests/
├── __init__.py
├── test_source.py            # UT-SRC-001 ~ UT-SRC-008
├── test_scramble.py          # UT-SCR-001 ~ UT-SCR-008
├── test_channel_coding.py    # UT-COD-001 ~ UT-COD-009
├── test_framing.py           # UT-FRM-001 ~ UT-FRM-013
├── test_modulation.py        # UT-MOD-001 ~ UT-MOD-014
├── test_channel.py           # UT-CHN-001 ~ UT-CHN-010
├── test_synchronization.py   # UT-SYN-001 ~ UT-SYN-010
├── test_metrics.py           # UT-MET-001 ~ UT-MET-006
├── test_visualization.py     # UT-VIS-001 ~ UT-VIS-004
├── test_integration.py       # IT-PIP-001 ~ IT-PIP-008, IT-E2E-001 ~ IT-E2E-010
├── test_edge_cases.py        # ST-EDGE-001 ~ ST-EDGE-024
└── conftest.py               # 共享 fixtures (Test.txt 生成, results 清理等)
```

---

## 8. 测试覆盖率与公开测试映射

下表展示自测单元测试与公开测试的双向覆盖：

| 模块 | 自测单元测试覆盖 | 对应公开测试 |
|------|---------------|------------|
| 源编解码 | UT-SRC-001 ~ UT-SRC-008 | TC-T-004 |
| 扰码/加密 | UT-SCR-001 ~ UT-SCR-008 | TC-T-007 |
| 信道编解码 | UT-COD-001 ~ UT-COD-009 | TC-T-008 |
| 帧封装/解析 | UT-FRM-001 ~ UT-FRM-013 | TC-T-005, TC-T-006 |
| 调制解调 | UT-MOD-001 ~ UT-MOD-014 | TC-T-009, TC-T-010, TC-T-011 |
| 信道 | UT-CHN-001 ~ UT-CHN-010 | TC-T-012 |
| 同步 | UT-SYN-001 ~ UT-SYN-010 | TC-T-013 |
| Metrics | UT-MET-001 ~ UT-MET-006 | TC-T-014 |
| 可视化 | UT-VIS-001 ~ UT-VIS-004 | TC-T-016 |
| 端到端 | IT-E2E-* | TC-T-015, TC-T-017 |
| 结构文档 | (公开测试直接检查) | TC-T-001, TC-T-002, TC-T-003, TC-T-018, TC-T-019, TC-T-020 |
