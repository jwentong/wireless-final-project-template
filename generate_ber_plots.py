import subprocess
import json
import os
import matplotlib.pyplot as plt

# 测试参数配置，和你报告里的表格完全对应
snr_list = [0, 2, 4, 6, 8, 10, 12, 14]
seed = 2026
input_file = "Test.txt"
output_file = "results/received.txt"
metrics_file = "results/metrics.json"

os.makedirs("results", exist_ok=True)

ber_awgn = []
ber_rayleigh = []

# ========== 批量测试 AWGN 信道 ==========
print("===== 正在测试 AWGN 信道 =====")
for snr in snr_list:
    print(f"当前 SNR = {snr} dB")
    # 调用你已有的主程序运行仿真
    cmd = [
        "python", "main.py",
        "--input", input_file,
        "--output", output_file,
        "--snr", str(snr),
        "--seed", str(seed),
        "--mod", "qpsk",
        "--channel", "awgn"
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    # 读取输出的性能指标
    with open(metrics_file, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    ber_awgn.append(metrics["ber"])

# ========== 批量测试 Rayleigh 信道 ==========
print("\n===== 正在测试 Rayleigh 信道 =====")
for snr in snr_list:
    print(f"当前 SNR = {snr} dB")
    cmd = [
        "python", "main.py",
        "--input", input_file,
        "--output", output_file,
        "--snr", str(snr),
        "--seed", str(seed),
        "--mod", "qpsk",
        "--channel", "rayleigh"
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    with open(metrics_file, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    ber_rayleigh.append(metrics["ber"])

# ========== 生成图5-3：AWGN 单信道 BER 曲线 ==========
plt.figure(figsize=(8, 5))
plt.semilogy(snr_list, ber_awgn, "bo-", linewidth=1.5, markersize=6, label="AWGN Channel")
plt.xlabel("SNR (dB)", fontsize=12)
plt.ylabel("Bit Error Rate (BER)", fontsize=12)
plt.title("BER-SNR Performance Curve (AWGN Channel)", fontsize=13)
plt.grid(True, which="both", linestyle="--", alpha=0.6)
plt.legend(fontsize=11)
plt.tight_layout()
plt.savefig("results/ber_curve.png", dpi=300)
plt.close()

# ========== 生成图5-4：双信道 BER 对比曲线 ==========
plt.figure(figsize=(8, 5))
plt.semilogy(snr_list, ber_awgn, "bo-", linewidth=1.5, markersize=6, label="AWGN Channel")
plt.semilogy(snr_list, ber_rayleigh, "rs-", linewidth=1.5, markersize=6, label="Rayleigh Channel")
plt.xlabel("SNR (dB)", fontsize=12)
plt.ylabel("Bit Error Rate (BER)", fontsize=12)
plt.title("BER-SNR Comparison: AWGN vs Rayleigh Fading Channel", fontsize=13)
plt.grid(True, which="both", linestyle="--", alpha=0.6)
plt.legend(fontsize=11)
plt.tight_layout()
plt.savefig("results/ber_comparison.png", dpi=300)
plt.close()

print("\n===== 全部生成完成 =====")
print("已输出文件：")
print("1. results/ber_curve.png  → 对应报告图5-3")
print("2. results/ber_comparison.png  → 对应报告图5-4")