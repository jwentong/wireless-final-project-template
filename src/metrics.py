import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def calculate_metrics(original_bits: np.ndarray, received_bits: np.ndarray,
                      original_text: str, received_text: str,
                      checksum_pass: bool, sync_start_index: int,
                      snr_db: float, seed: int, modulation: str, channel: str) -> dict:
    """
    计算全部性能指标
    """
    # 误比特率 BER
    total_bits = len(original_bits)
    error_bits = np.sum(original_bits != received_bits[:total_bits])
    ber = float(error_bits / total_bits) if total_bits > 0 else 0.0

    # 帧错误率 FER（单帧系统，校验不通过计为1帧错误）
    fer = 0.0 if checksum_pass else 1.0

    # 文本匹配率
    if len(original_text) == 0:
        text_match_rate = 1.0
    else:
        match_chars = sum(1 for a, b in zip(original_text, received_text) if a == b)
        text_match_rate = float(match_chars / len(original_text))

    return {
        "snr_db": snr_db,
        "seed": seed,
        "modulation": modulation,
        "channel": channel,
        "payload_bits": int(total_bits),
        "ber": ber,
        "fer": fer,
        "text_match_rate": text_match_rate,
        "checksum_pass": checksum_pass,
        "sync_start_index": int(sync_start_index)
    }


def save_metrics_json(metrics: dict, output_path: str):
    """保存指标到json文件"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)


def plot_constellation(symbols: np.ndarray, save_path: str):
    """绘制QPSK星座图"""
    plt.figure(figsize=(6, 6))
    plt.scatter(symbols.real, symbols.imag, s=1, alpha=0.7)
    plt.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    plt.axvline(0, color='gray', linestyle='--', linewidth=0.8)
    plt.xlabel('In-phase')
    plt.ylabel('Quadrature')
    plt.title('QPSK Constellation')
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    plt.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150)
    plt.close()


def plot_sync_peak(corr_values: np.ndarray, peak_idx: int, save_path: str):
    """绘制同步相关峰值图"""
    plt.figure(figsize=(8, 4))
    plt.plot(np.abs(corr_values))
    plt.scatter(peak_idx, np.abs(corr_values[peak_idx]), color='red', label='Peak', zorder=5)
    plt.xlabel('Symbol Index')
    plt.ylabel('Correlation Magnitude')
    plt.title('Synchronization Correlation Peak')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150)
    plt.close()


def plot_ber_curve(snr_list: list, ber_list: list, save_path: str):
    """绘制BER-SNR曲线"""
    plt.figure(figsize=(8, 5))
    plt.semilogy(snr_list, ber_list, 'o-', linewidth=1.5, markersize=4)
    plt.xlabel('SNR (dB)')
    plt.ylabel('Bit Error Rate (BER)')
    plt.title('BER vs SNR Curve')
    plt.grid(True, alpha=0.3, which='both')
    plt.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150)
    plt.close()