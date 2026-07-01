# MOCK_TEST_REPORT.md - Mock 测试报告

在正式实现全部代码前后，按照 TEST_PLAN.md 进行了多轮 mock 测试，用来验证 DESIGN.md 中的接口、帧结构、同步流程是否可行。以下记录了 3 个关键 mock 测试场景及其发现的问题。

## Mock 测试场景 1：帧结构 + QPSK padding 往返验证

**做法**：手工构造 257 bit（奇数长度）的随机 payload，走 `build_frame -> qpsk_modulate -> qpsk_demodulate -> parse_frame` 全流程，检查是否能精确还原 payload。

**结果**：通过。`qpsk_modulate` 对奇数长度帧自动补 1 个 0 比特，`parse_frame` 内部用 length 字段计算出帧的精确边界，天然忽略了这个补零比特，没有出现"多一位导致后续解析全部错位"的问题。这一 mock 测试验证了 DESIGN.md 中"length 字段用于去除 QPSK padding"这一设计假设是可行的。

## Mock 测试场景 2：同步偏移检测

**做法**：在发送符号前拼接 25 个随机高斯符号模拟同步偏移，SNR=12dB，跑 `synchronize` 检测帧起点。

**结果**：初版实现用简单的逐点滑动相关（未归一化），在小规模测试里表现尚可，但担心在真实较长的整帧数据上会因为累计能量差异导致误判。mock 测试后改为**归一化相关**（除以窗口能量和 preamble 能量的几何平均），实测在 SNR=12dB 下能精确命中偏移位置（`sync_start_index` 与实际插入的偏移完全一致），比未归一化版本更稳健。**这是一个通过 mock 测试发现并修正的设计缺陷**：未归一化相关容易在信号功率不均匀时被强能量段"抢峰"，归一化后消除了这一风险。

## Mock 测试场景 3：端到端 checksum_pass 异常

**做法**：跑通标准命令（`--snr 12 --seed 2026`）后检查 `metrics.json`，发现 `text_match_rate=1.0`（文本完全恢复）但 `checksum_pass=false`，二者看起来矛盾。

**问题定位**：`build_frame` 内部的 checksum 是在信道编码后（含 AWGN 噪声、FEC 纠错前）的比特上计算的；在 SNR=12dB 时仍有极少量比特因噪声翻转（`ber≈5.4e-5`），这些翻转发生在重复码的某些分组里，多数判决译码能够把最终比特纠正回正确值，但"纠错前"的原始帧比特已经和发送时不完全一致，所以帧内 checksum 会显示不通过——**这是本次 mock 测试发现的一个设计风险**：checksum 的校验粒度（纠错前）与最终验收标准（纠错后文本一致）不在同一个层次，容易造成"文本正确但 checksum 显示失败"的误导性结果。

**设计修订**：在 `main.py` 中增加了一层"端到端 CRC16"校验，覆盖扰码后、信道编码前的比特，并在**信道解码（FEC 纠错）之后**重新计算校验值再比较。修订后，只要 FEC 成功纠正了所有比特错误（本次运行确实如此），`checksum_pass` 就会正确显示为 `true`，与 `text_match_rate=1.0` 的结论一致。此修订已同步更新到 DESIGN.md 第 3、6 节。

## Mock 测试结论

三轮 mock 测试共发现 2 个设计问题（同步相关未归一化、checksum 校验粒度与最终验收标准不一致），均已在正式代码实现中修正，并在 DESIGN.md 中补充了对应的设计说明。Mock 测试证明了固定链路顺序（Channel Encode -> Frame Build）与 length 字段换算关系（length/3 = 原始比特数）在实际比特级仿真中是自洽可行的。
