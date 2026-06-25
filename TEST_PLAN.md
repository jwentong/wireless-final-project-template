# 测试计划（公开测试）

## 测试范围

本计划涵盖教师提供的 **22 个公开测试用例**，分布于 3 个测试文件，用于验证项目结构、核心模块接口与端到端功能。

## 测试文件结构

```
public_tests/
├── conftest.py                        # 共享 fixtures 与工具函数
├── test_01_structure_and_documents.py # 项目结构与文档检查 (6)
├── test_02_core_modules.py            # 核心模块接口验证 (9)
└── test_03_cli_end_to_end.py          # CLI 端到端集成测试 (7)
```

## 公开测试用例

### 1. 项目结构与文档 (`test_01_structure_and_documents.py`)

| 编号 | 测试函数 | 验证内容 |
|------|---------|---------|
| P-001 | `test_tc_t_001` | 必需项目文件（DESIGN.md、TEST_PLAN.md、MOCK_TEST_REPORT.md、AI_LOG.md、main.py、src/、tests/）均存在 |
| P-002 | `test_tc_t_002` | DESIGN.md 涵盖固定系统链路（信源编码、加扰、信道编码、组帧、QPSK 等 ≥9 个关键词） |
| P-003 | `test_tc_t_003` | MOCK_TEST_REPORT.md 包含 ≥3 处 "mock" 描述、至少 1 个风险/缺陷项、至少 1 处修订记录 |
| P-004 | `test_tc_t_018` | AI_LOG.md 记录 ≥3 次提示词交互、说明人工修改内容与最终采纳理由 |
| P-005 | `test_tc_t_019` | 报告/DESIGN.md 解释 QPSK 星座结果、讨论 BER/text_match_rate、说明至少 1 个失败/误差原因 |
| P-006 | `test_tc_t_020` | 源代码中无直接文件复制捷径（如 shutil.copy、write_text 读取 Test.txt） |

### 2. 核心模块接口 (`test_02_core_modules.py`)

| 编号 | 测试函数 | 验证内容 |
|------|---------|---------|
| P-007 | `test_tc_t_004` | UTF-8 信源编解码可逆，比特流长度为 8 的倍数 |
| P-008 | `test_tc_t_005` | 帧包含前导码/长度/载荷/校验 4 个字段 |
| P-009 | `test_tc_t_006` | 构建→解析帧后载荷与长度一致 |
| P-010 | `test_tc_t_007` | 加扰/加密函数可逆 |
| P-011 | `test_tc_t_008` | 信道编解码无噪可逆 |
| P-012 | `test_tc_t_009` | QPSK 映射符合 4 象限格雷编码，平均功率 ≈ 1 |
| P-013 | `test_tc_t_010` | QPSK 无噪解调零误码 |
| P-014 | `test_tc_t_011` | QPSK 调制的 padding 通过帧长度字段正确去除 |
| P-015 | `test_tc_t_012` | AWGN 信道固定种子输出可重现 |

### 3. CLI 端到端集成 (`test_03_cli_end_to_end.py`)

| 编号 | 测试函数 | 验证内容 |
|------|---------|---------|
| P-016 | `test_tc_t_013` | 帧同步检测 25 符号偏移，误差 ≤ 1 |
| P-017 | `test_tc_t_014` | results/metrics.json 包含 snr_db、seed、modulation、channel、ber、fer、text_match_rate、checksum_pass、sync_start_index 等字段 |
| P-018 | `test_tc_t_015` | SNR 12dB 端到端链路正确恢复文本，text_match_rate == 1.0 |
| P-019 | `test_tc_t_016` | 生成 ≥2 个非空图片文件（constellation.png / ber_curve.png / sync_peak.png） |
| P-020 | `test_tc_t_017` | CLI 非交互式运行，无 input() 等待 |
| P-021 | `test_cli_outputs_valid_json_metrics` | metrics.json 中 modulation=qpsk、channel=awgn、seed=2026、snr_db=12 |
| P-022 | `test_main_py_exists_and_uses_argument_parsing` | main.py 存在且支持 --input / --output 参数 |

## 测试执行

```bash
# 运行全部公开测试
python -m pytest public_tests -v

# 运行单个测试文件
python -m pytest public_tests/test_01_structure_and_documents.py -v
python -m pytest public_tests/test_02_core_modules.py -v
python -m pytest public_tests/test_03_cli_end_to_end.py -v

# 端到端运行（默认配置）
python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
```

## GitHub Actions 自动评分

公开测试由教师仓库的 GitHub Actions 工作流在 Pull Request 时自动执行：

```yaml
name: PR public grading
on:
  pull_request:
    branches: [main]
jobs:
  public-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: |
          pip install pytest numpy scipy matplotlib
          pytest public_tests -q
```
