# 无线通信基带仿真系统设计文档 (DESIGN.md)

## 1. 整体系统架构
本系统实现了一条完整的端到端无线通信基带链路。数据流向如下：
`Test.txt` -> 源编码 -> 扰码 -> 信道编码 -> 帧构建 -> QPSK调制 -> 模拟信道(AWGN+偏移) -> 帧同步 -> QPSK解调 -> 信道译码 -> 解扰 -> 源解码 -> `received.txt`

## 2. 模块接口与算法选择

| 模块名称 | 算法/方案选择 | 输入接口 | 输出接口 |
|---|---|---|---|
| **源编码 (Source Codec)** | UTF-8编码转二进制比特流 | `string` (文本) | `numpy.ndarray` (0/1比特流) |
| **扰码 (Scrambler)** | 伪随机(PN)序列异或，固定Seed | `numpy.ndarray` (比特流) | `numpy.ndarray` (加扰比特流) |
| **信道编码 (Channel Codec)**| 3倍重复码 (抗噪) | `numpy.ndarray` (比特流) | `numpy.ndarray` (编码比特流) |
| **帧结构 (Framer)** | 13位巴克码前导 + 32位长度 + 载荷 + 32位CRC校验 | `numpy.ndarray` (比特流) | `numpy.ndarray` (成帧比特流) |
| **调制 (Modem)** | QPSK (Gray映射)，尾部补0 | `numpy.ndarray` (比特流) | `numpy.ndarray` (复数符号流) |
| **信道 (Channel)** | AWGN加性高斯白噪声 + 随机符号前置偏移 | `numpy.ndarray` (符号流), SNR | `numpy.ndarray` (受损符号流) |
| **同步 (Synchronizer)** | 前导码互相关峰值检测 | `numpy.ndarray` (符号流) | `numpy.ndarray` (截取后的符号流), 偏移量 |

## 3. 关键参数设置
* **QPSK 映射规则**：严格遵循 PRD，`00 -> (1+j)/√2`, `01 -> (-1+j)/√2`, `11 -> (-1-j)/√2`, `10 -> (1-j)/√2`
* **前导序列 (Preamble)**：采用 13 位 Barker 码 `[1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1]`，具有良好的自相关特性，适合同步。
* **SNR 定义**：接收端调制符号平均功率与复高斯噪声平均功率之比。

## 4. 预期风险与应对
* **低 SNR 下同步失败**：若噪声过大，互相关峰值可能被淹没。应对方案：加入阈值保护，输出失败日志，确保系统不崩溃。
* **长度不匹配**：源文件末尾可能产生 padding。应对方案：在帧头明确记录原始 payload_bits 长度，接收端截断。

## pytest 验收关键词补充
系统包含: Source Encode, Encrypt, Scramble, Channel Encode, Frame Build, QPSK, Modulate, Demodulate, Channel, Synchronization, Channel Decode, Source Decode, Metrics.
性能包括 BER 和 text_match_rate。
