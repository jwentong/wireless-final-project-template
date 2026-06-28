# 无线通信文件传输基带仿真系统实验分析报告

## 摘要

本项目实现了一个基于 AI 辅助编程的无线通信文件传输基带仿真系统。系统将 `Test.txt` 的 UTF-8 文本转换为 bitstream，经 PN/XOR 扰码、3 重复码、帧封装、QPSK 调制、AWGN 信道和前导同步后，在接收端完成解调、译码、解扰和文本恢复。系统支持统一 CLI，输出 `received.txt`、`metrics.json`、QPSK 星座图、BER-SNR 曲线和同步峰值图。高 SNR 下星座聚类清晰，同步峰值显著，BER 和 FER 应为 0，text_match_rate 应为 1.0。

## 1. 系统方案

完整链路为 Source Encode -> Scramble -> Channel Encode -> Frame Build -> QPSK Modulate -> AWGN Channel -> Synchronization -> QPSK Demodulate -> Frame Parse -> Channel Decode -> Descramble -> Source Decode -> Metrics / Plots。

## 2. 关键结果解释

QPSK 星座图用于观察噪声对四个理想星座点的扰动。SNR 较高时，接收点仍集中在四个象限内，因此硬判决误码率较低。BER 曲线展示 SNR 增大时误码率下降的趋势。同步峰值图展示 preamble 相关检测结果，峰值位置即估计帧起点。

## 3. 失败原因分析

低 SNR 下可能出现三类 failure / error：第一，星座点跨越判决边界导致 BER 升高；第二，同步相关峰值被噪声淹没导致帧起点偏移；第三，关键头部字段或 payload 损坏导致 CRC 失败、UTF-8 解码异常或 text_match_rate 下降。系统通过重复码和帧头重复保护降低这些风险，并保证低 SNR 下也输出 metrics。

