# TEST_PLAN.md — 测试计划

> 依据 `PRD.md`、`DESIGN.md` 与教师公开 20% 测试案例（`wireless_project_test_set_20.feature`，TC-T-001~020）制定。
> 测试遵循 TDD：先写测试（RED）→ 实现至通过（GREEN）→ 重构（REFACTOR），目标行覆盖率 ≥ 80%。

---

## 1. 测试目标

1. 保证每个模块满足 `DESIGN.md` 的接口契约与通信原理（可逆性、映射正确性、可复现性）。
2. 保证端到端在 SNR ≥ 12 dB、AWGN、固定 seed 下 `received.txt` 与 `Test.txt` 完全一致。
3. 覆盖隐藏验证集可能的鲁棒性维度（不同文本/长度/SNR/seed/同步偏移/异常输入），且**无硬编码**。
4. 本地 `pytest public_tests -q` 与 `pytest tests -q` 全绿后再提交。

## 2. 测试分层策略

| 层级 | 范围 | 位置 | 手段 |
|---|---|---|---|
| 单元测试 Unit | 单模块函数（编解码可逆、映射、功率、CRC） | `tests/test_*.py` | 固定向量 + 随机往返（property-style） |
| 集成测试 Integration | 多模块串联（发送链 / 接收链 / 同步+解调+解析） | `tests/test_integration.py` | 子链路往返一致 |
| 端到端 E2E | `main.py` CLI 全流程 | `tests/test_e2e.py` + `public_tests` | 子进程跑 CLI，校验产物 |
| 公开验收 Public | 教师公开测试 | `public_tests/` | `pytest public_tests -q` |

## 3. 公开测试用例映射（TC-T-001~020）

| 用例 | 检查点 | 覆盖模块 | 本地对应测试 |
|---|---|---|---|
| TC-T-001 | 必需文件/目录存在 | 工程结构 | 提交前 checklist |
| TC-T-002 | DESIGN.md 覆盖固定链路关键词 | 文档 | `DESIGN.md` 已含 ≥9 关键词 |
| TC-T-003 | MOCK_TEST_REPORT 有 ≥3 mock + 风险 + 修订 | 文档 | mock 阶段产出 |
| TC-T-004 | UTF-8 源编码可逆，len%8==0 | source | `test_source.py` |
| TC-T-005 | 帧含 preamble/length/payload/CRC | framing | `test_framing.py` |
| TC-T-006 | 帧封装/解析可逆，length==payload 长 | framing | `test_framing.py` |
| TC-T-007 | 扰码/解扰可逆（seed=2026） | scramble | `test_scramble.py` |
| TC-T-008 | 信道编/译码无噪声可逆 | channel_coding | `test_channel_coding.py` |
| TC-T-009 | QPSK Gray 四象限 + 单位功率 | modulation | `test_modulation.py` |
| TC-T-010 | QPSK 无噪声调制解调无误码 | modulation | `test_modulation.py` |
| TC-T-011 | padding 由 length 字段去除 | framing+modulation | `test_integration.py` |
| TC-T-012 | AWGN 固定 seed 可复现 | channel | `test_channel.py` |
| TC-T-013 | 同步检测 25 符号偏移，误差≤1 | synchronization | `test_sync.py` |
| TC-T-014 | metrics.json 含全部最低字段 | pipeline/metrics | `test_e2e.py` |
| TC-T-015 | SNR 12 端到端完全恢复，match=1.0 | 全链路 | `test_e2e.py` |
| TC-T-016 | 生成 ≥2 张图 | pipeline/plots | `test_e2e.py` |
| TC-T-017 | CLI 非交互运行 | main | `test_e2e.py` |
| TC-T-018 | AI_LOG ≥3 prompt + 人工修改 + 采纳理由 | 文档 | 交付阶段产出 |
| TC-T-019 | 报告解释 QPSK 星座 + BER + 失败原因 | 文档 | `REPORT.md`/`DESIGN.md` |
| TC-T-020 | 无直接文件复制绕过链路 | 代码审查 | 静态检查 + `test_e2e.py` |

## 4. 单元测试计划（`tests/`）

| 文件 | 关键断言 |
|---|---|
| `test_source.py` | 中/英/混合/空串/emoji 往返一致；输出 len%8==0；非法字节抛错 |
| `test_scramble.py` | `descramble(scramble(b,s),s)==b`；不同 seed 输出不同；长度不变 |
| `test_channel_coding.py` | 汉明、卷积各自 `decode(encode(b))[:len(b)]==b`；含 1 位错时汉明纠正；卷积低误码下纠错 |
| `test_framing.py` | 含 5 字段；封装/解析可逆；length 语义；CRC 翻转能被检出 |
| `test_modulation.py` | QPSK 四象限映射精确；平均功率∈[0.8,1.2]；奇数 bit 补 0；BPSK/16-QAM 往返 |
| `test_channel.py` | AWGN 同 seed 两次一致、异 seed 不同；实测 SNR≈设定值；衰落统计特性 |
| `test_sync.py` | 0/25/64/128 偏移均检测，误差≤1；噪声前缀下鲁棒 |
| `test_metrics.py` | BER/text_match 边界（全对=0/1、全错）；CRC16 已知向量 |
| `test_equalizer.py` | 已知 h 下 ZF/MMSE 恢复；MMSE 低 SNR 优于 ZF |

测试风格：固定向量（验证正确性）+ 随机种子往返（验证一般性），避免只测单一样例。

## 5. 集成测试计划（`tests/test_integration.py`）

- 发送链：`source→scramble→channel_encode→build_frame→modulate` 后，逆链恢复原文本（无信道）。
- 同步链：人工加 0~128 偏移 + 噪声，`synchronize→demodulate→parse_frame` 正确定位并恢复帧。
- padding 链：奇数长度 payload 全程往返（对应 TC-T-011）。

## 6. 端到端与鲁棒性矩阵（应对隐藏验证集）

| 维度 | 取值 | 期望 |
|---|---|---|
| 文本内容 | 教师 Test.txt / 纯中文 / 中英混合 / 含标点数字 | 完全恢复 |
| 文本长度 | 1 字 / 数十字 / 约 300 字 / 上千字 | 完全恢复，帧长字段不溢出（32bit length，远超需求） |
| SNR | 0,2,…,14 dB | BER 单调下降；≥12 dB 完全恢复 |
| seed | 2026 / 其他 | 可复现；不同 seed 噪声不同 |
| 同步偏移 | 0,1,25,64,128 符号 | 误差≤1 |
| 异常输入 | 缺失输入文件 / 非法参数 / 空文件 | 友好报错、非零退出码、不崩溃（系统边界校验） |
| 信道 | AWGN / Rayleigh / Rician | 不崩溃；衰落下报告 BER 上升与均衡改善 |

## 7. 隐藏验证集应对策略

- **通用性**：所有模块对任意 UTF-8/长度/SNR/seed 工作；禁止任何针对 Test.txt 内容的分支或常量。
- **反硬编码自查**：`src/`、`main.py` 不出现 `shutil.copy`/`copyfile`/直接写 Test.txt（对应 TC-T-020）。
- **文档一致性**：DESIGN.md 描述与代码实现保持同步（参数、帧格式、码率）。
- **异常鲁棒**：CLI 对缺文件/坏参数返回非零退出码并打印可读错误，不抛裸 traceback 到用户。

## 8. 执行与覆盖率

```bash
pytest tests -q                 # 自测单元/集成/端到端
pytest public_tests -q          # 公开验收
pytest --cov=src --cov-report=term-missing   # 覆盖率（目标 ≥80%）
```

提交前门槛：两套测试全绿 + 覆盖率达标 + 反硬编码自查通过。
