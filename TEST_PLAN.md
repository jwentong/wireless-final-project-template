# 无线通信基带仿真系统 — TEST_PLAN.md

## 1. 测试目标

验证基带仿真系统各模块功能和端到端链路正确性，确保满足 PRD 要求。

## 2. 测试环境

- Python 3.11+
- 依赖：numpy, scipy, matplotlib, pytest
- 运行命令：

```bash
pip install -r requirements.txt
pytest public_tests -q
```

## 3. 测试用例

### 3.1 项目结构检查 (TC-T-001)

- **验证**：项目根目录存在 DESIGN.md, TEST_PLAN.md, MOCK_TEST_REPORT.md, AI_LOG.md, main.py, src/, tests/
- **命令**：`pytest public_tests/test_01_structure_and_documents.py::test_tc_t_001_required_project_files_exist`

### 3.2 设计文档覆盖 (TC-T-002)

- **验证**：DESIGN.md 覆盖 Source Encode, Encrypt/Scramble, Channel Encode, Frame Build, QPSK Modulate, QPSK Demodulate, Channel, Synchronization, Channel Decode, Source Decode, Metrics

### 3.3 Mock 测试报告 (TC-T-003)

- **验证**：MOCK_TEST_REPORT.md 包含至少 3 个 mock 测试场景、至少 1 个设计风险/缺陷、至少 1 处 DESIGN.md 修订记录

### 3.4 源编码可逆性 (TC-T-004)

- **输入**：中文文本
- **期望**：source_encode → source_decode 后文本完全一致，bitstream 长度为 8 的倍数
- **命令**：`pytest public_tests/test_02_core_modules.py::test_tc_t_004_utf8_source_codec_is_reversible`

### 3.5 帧结构字段完整性 (TC-T-005)

- **输入**：2400 bit payload
- **期望**：帧包含 preamble, length, payload, checksum/CRC 字段
- **命令**：`pytest public_tests/test_02_core_modules.py::test_tc_t_005_frame_contains_required_fields`

### 3.6 帧封装解析可逆 (TC-T-006)

- **输入**：257 bit payload
- **期望**：build_frame → parse_frame 后 payload 一致，length 正确
- **命令**：`pytest public_tests/test_02_core_modules.py::test_tc_t_006_frame_build_and_parse_are_reversible`

### 3.7 扰码可逆 (TC-T-007)

- **输入**：511 位随机比特
- **期望**：scramble → descramble 后恢复原始比特
- **命令**：`pytest public_tests/test_02_core_modules.py::test_tc_t_007_scramble_or_encrypt_is_reversible`

### 3.8 信道编码可逆 (TC-T-008)

- **输入**：400 位随机比特
- **期望**：channel_encode → channel_decode 无噪声下恢复原始比特
- **命令**：`pytest public_tests/test_02_core_modules.py::test_tc_t_008_channel_encode_decode_noiseless_reversible`

### 3.9 QPSK 映射象限 (TC-T-009)

- **输入**：[00, 01, 11, 10]
- **期望**：QPSK 符号分别位于第 1, 2, 3, 4 象限，平均功率 ≈ 1
- **命令**：`pytest public_tests/test_02_core_modules.py::test_tc_t_009_qpsk_mapping_matches_prd_quadrants`

### 3.10 QPSK 无噪声无误码 (TC-T-010)

- **输入**：512 位随机比特
- **期望**：qpsk_modulate → qpsk_demodulate 无误码
- **命令**：`pytest public_tests/test_02_core_modules.py::test_tc_t_010_qpsk_noiseless_demodulation_has_no_bit_errors`

### 3.11 Padding 去除 (TC-T-011)

- **输入**：255 位 payload
- **期望**：build_frame → modulate → demodulate → parse_frame 后 payload 长度不变
- **命令**：`pytest public_tests/test_02_core_modules.py::test_tc_t_011_qpsk_padding_removed_by_length_field`

### 3.12 AWGN 可复现 (TC-T-012)

- **输入**：固定 QPSK 符号，SNR=12dB，seed=2026
- **期望**：两次 AWGN 输出一致
- **命令**：`pytest public_tests/test_02_core_modules.py::test_tc_t_012_awgn_channel_is_reproducible_with_fixed_seed`

### 3.13 同步检测偏移 (TC-T-013)

- **输入**：25 符号前置偏移 + preamble + payload
- **期望**：synchronize 返回起始索引 ≈ 25
- **命令**：`pytest public_tests/test_03_cli_end_to_end.py::test_tc_t_013_sync_detects_25_symbol_offset_if_sync_api_exists`

### 3.14 metrics.json 字段 (TC-T-014)

- **输入**：CLI 运行
- **期望**：metrics.json 包含 snr_db, seed, modulation, channel, payload_bits, ber, fer, text_match_rate, checksum_pass, sync_start_index

### 3.15 SNR 12dB 端到端恢复 (TC-T-015)

- **输入**：Test.txt, --snr 12 --seed 2026 --mod qpsk --channel awgn
- **期望**：received.txt 与 Test.txt 完全一致，text_match_rate = 1.0

### 3.16 可视化图表 (TC-T-016)

- **期望**：results/ 下至少存在 constellation.png, ber_curve.png, sync_peak.png 中的两项

### 3.17 非交互运行 (TC-T-017)

- **期望**：CLI 运行无 input() 等交互提示

### 3.18 AI_LOG.md 记录 (TC-T-018)

- **验证**：日志包含至少 3 条 prompt、人工修改记录、采纳理由

### 3.19 分析报告 (TC-T-019)

- **验证**：DESIGN.md 或其他报告解释 QPSK 星座图、BER 或 text_match_rate、至少一个失败/误码原因

### 3.20 反绕过检查 (TC-T-020)

- **验证**：主流程不得直接复制 Test.txt 到 received.txt

## 4. 测试结果记录

运行 `pytest public_tests -q --tb=short` 后记录输出，确认 20/20 测试通过。
