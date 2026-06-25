# Mock 测试报告

## 测试概览

共实现 **70 个 mock 测试**，覆盖 9 个模块，全部通过。

| 模块 | 测试文件 | 测试数 | 通过率 |
|------|---------|--------|--------|
| 信源编解码 | `test_mock_source.py` | 6 | 100% |
| 帧结构 | `test_mock_framing.py` | 8 | 100% |
| 调制（QPSK/BPSK/16-QAM） | `test_mock_modulation.py` | 22 | 100% |
| AWGN 信道 | `test_mock_channel.py` | 6 | 100% |
| 帧同步 | `test_mock_sync.py` | 5 | 100% |
| 端到端集成 | `test_mock_e2e.py` | 5 | 100% |
| FEC 编解码 | `test_mock_fec.py` | 7 | 100% |
| Rayleigh 信道 | `test_mock_rayleigh.py` | 4 | 100% |
| CRC-32 校验 | `test_mock_checksum.py` | 7 | 100% |

---

## 详细测试结果

### Mock 测试集 1：信源编解码 (`test_mock_source.py`)

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| `test_utf8_encoding_reversible` | 中文文本编码→解码后恢复一致 | 通过 |
| `test_encoding_returns_bit_list` | 编码输出为 0/1 列表 | 通过 |
| `test_empty_string` | 空字符串编解码 | 通过 |
| `test_multibyte_characters` | 含 emoji 的多字节 UTF-8 文本 | 通过 |
| `test_decoding_strips_incomplete_bytes` | 非字节对齐的比特流不会崩溃 | 通过 |
| `test_preserves_bit_count` | 编码比特数 = UTF-8 字节数 × 8 | 通过 |

**发现风险**：解码不完整字节时静默截断，应用层应确保比特流完整性。

### Mock 测试集 2：帧结构 (`test_mock_framing.py`)

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| `test_frame_contains_required_fields` | 前导码(32b)+长度(16b)+载荷+校验(8b) 完整 | 通过 |
| `test_frame_is_parsable` | 构建→解析后载荷一致 | 通过 |
| `test_checksum_passes_on_noiseless_frame` | 无噪声时校验通过 | 通过 |
| `test_length_field_matches_payload_size` | 长度字段与载荷比特数一致 | 通过 |
| `test_padding_for_odd_bit_count` | 奇数比特时帧总长为偶数（QPSK 对齐） | 通过 |
| `test_minimal_payload` | 单比特载荷 | 通过 |
| `test_large_payload` | 1000 比特载荷 | 通过 |
| `test_preamble_constant_unchanged` | 前导码常量为 32 位二进制序列 | 通过 |

**发现风险**：长度字段为 16 位无符号整数，载荷超过 65535 比特时溢出。当前场景下安全，扩展时需升级。

### Mock 测试集 3：调制 (`test_mock_modulation.py`)

#### QPSK（9 个测试）

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| `test_gray_mapping_quadrant_q1` | 00 → (1+j)/√2 (Q1: Re>0, Im>0) | 通过 |
| `test_gray_mapping_quadrant_q2` | 01 → (-1+j)/√2 (Q2: Re<0, Im>0) | 通过 |
| `test_gray_mapping_quadrant_q3` | 11 → (-1-j)/√2 (Q3: Re<0, Im<0) | 通过 |
| `test_gray_mapping_quadrant_q4` | 10 → (1-j)/√2 (Q4: Re>0, Im<0) | 通过 |
| `test_normalized_symbol_power` | 平均符号功率 = 1 | 通过 |
| `test_noiseless_loopback` | 无噪声调制解调环回零错误 | 通过 |
| `test_odd_bit_count_auto_padding` | 奇数位自动补零后调制 | 通过 |
| `test_demodulate_all_four_quadrants` | 4 个象限解调后恢复原比特 | 通过 |
| `test_symbols_are_normalized` | 每个符号功率 = 1 | 通过 |

#### BPSK（5 个测试）

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| `test_bit_0_maps_to_positive_real` | 0 → (+1, 0) | 通过 |
| `test_bit_1_maps_to_negative_real` | 1 → (-1, 0) | 通过 |
| `test_normalized_power` | 平均符号功率 = 1 | 通过 |
| `test_noiseless_loopback` | 无噪声环回零错误 | 通过 |
| `test_all_symbols_unit_magnitude` | 每个符号功率 = 1 | 通过 |

#### 16-QAM（9 个测试）

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| `test_gray_mapping_quadrant_q1` | 1111 → Q1 (Re>0, Im>0) | 通过 |
| `test_gray_mapping_quadrant_q2` | 0111 → Q2 (Re<0, Im>0) | 通过 |
| `test_gray_mapping_quadrant_q3` | 0000 → Q3 (Re<0, Im<0) | 通过 |
| `test_gray_mapping_quadrant_q4` | 1100 → Q4 (Re>0, Im<0) | 通过 |
| `test_normalized_power` | 平均符号功率 = 1 | 通过 |
| `test_noiseless_loopback` | 无噪声环回零错误 | 通过 |
| `test_quadbit_count_auto_padding` | 非 4 倍数比特自动补零 | 通过 |
| `test_demodulate_all_sixteen_points` | 全部 16 个星座点解调后恢复原比特 | 通过 |

### Mock 测试集 4：AWGN 信道 (`test_mock_channel.py`)

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| `test_reproducible_with_same_seed` | 相同种子输出完全相同 | 通过 |
| `test_different_seed_gives_different_output` | 不同种子输出不同 | 通过 |
| `test_higher_snr_less_noise` | SNR 越高噪声方差越小 | 通过 |
| `test_mean_noise_approx_zero` | 噪声均值为零（10000 样本） | 通过 |
| `test_output_same_length_as_input` | 输出长度与输入一致 | 通过 |
| `test_snr_zero_db_noise_equals_signal_power` | SNR=0dB 时噪声功率≈信号功率 | 通过 |

### Mock 测试集 5：帧同步 (`test_mock_sync.py`)

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| `test_detects_exact_offset` | 25 符号偏移，检测误差 ≤ 1 | 通过 |
| `test_no_offset_returns_zero` | 无偏移返回 0 | 通过 |
| `test_large_offset` | 128 符号偏移，检测误差 ≤ 2 | 通过 |
| `test_returns_integer` | 返回值类型为 int | 通过 |
| `test_short_signal_returns_zero` | 信号短于前导码返回 0（不崩溃） | 通过 |

**发现风险**：大偏移(128)时检测误差增大到 2 个符号，在低 SNR 或更大偏移下可能进一步恶化。

### Mock 测试集 6：端到端集成 (`test_mock_e2e.py`)

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| `test_full_chain_12db_recovers_correct_text` | SNR 12dB 完整链路恢复中文文本 | 通过 |
| `test_checksum_verification` | 信道解码后校验码验证通过 | 通过 |
| `test_metrics_fields_present` | 帧元数据包含必需字段 | 通过 |
| `test_different_seed_gives_different_result` | 不同加扰种子输出不同 | 通过 |
| `test_multiple_texts` | 多文本（英文、短文本、长文本、中文）兼容 | 通过 |

### Mock 测试集 7：FEC 编解码 (`test_mock_fec.py`)

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| `test_conv_encode_decode_noiseless` | 卷积编码→Viterbi 译码无噪可逆 | 通过 |
| `test_varying_input_lengths` | 不同输入长度（1~512 比特）均正确编解码 | 通过 |
| `test_single_bit_error_correction` | 单比特错误可通过 Viterbi 纠正 | 通过 |
| `test_fec_factory_selects_hamming` | `get_fec("hamming")` 返回 Hamming 编解码器 | 通过 |
| `test_fec_factory_selects_convolutional` | `get_fec("convolutional")` 返回卷积编解码器 | 通过 |
| `test_fec_factory_default_hamming` | 无效参数回退到 Hamming | 通过 |
| `test_hamming_still_works` | Hamming 编解码仍正常工作 | 通过 |

**发现风险**：卷积码译码依赖 Viterbi 算法，长约束长度下延迟显著增加。当前（7, 1/2）卷积码在低 SNR 时误码率仍可能较高。

### Mock 测试集 8：Rayleigh 信道 (`test_mock_rayleigh.py`)

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| `test_reproducible_with_same_seed` | 相同种子输出完全相同 | 通过 |
| `test_output_same_length_as_input` | 输出长度与输入一致 | 通过 |
| `test_fading_reduces_avg_power` | 衰落影响符号功率 | 通过 |
| `test_high_snr_recovery` | 高 SNR 下 ZF 均衡后星座中心回归原点 | 通过 |

**发现风险**：Rayleigh 衰落使符号幅度随机变化，低 SNR 下 ZF 均衡可能放大噪声，需结合分集或信道编码。

### Mock 测试集 9：CRC-32 校验 (`test_mock_checksum.py`)

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| `test_output_32_bits` | CRC-32 输出 32 位 | 通过 |
| `test_deterministic` | 相同输入输出相同 | 通过 |
| `test_different_inputs_differ` | 不同输入输出不同 | 通过 |
| `test_checksum_len` | `get_checksum_len("crc32")` 返回 32，`get_checksum_len("xor8")` 返回 8 | 通过 |
| `test_get_checksum_fn_crc32` | `get_checksum_fn("crc32")` 可调用且输出 32 位 | 通过 |
| `test_get_checksum_fn_xor8` | `get_checksum_fn("xor8")` 返回 XOR-8 校验函数 | 通过 |
| `test_varying_input_lengths` | 不同长度输入（1~1000 比特）均输出 32 位 | 通过 |

**发现风险**：CRC-32 为 32 位额外开销，在短帧场景下开销占比较高，短突发错误场景可考虑 XOR-8。
