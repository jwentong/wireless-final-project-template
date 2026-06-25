"""
AWGN 信道模块 (Additive White Gaussian Noise)

功能:
- 添加高斯白噪声
- 计算噪声方差
"""

import numpy as np


def calculate_noise_variance(snr_db: float, symbol_power: float = 1.0) -> float:
    """
    根据 SNR 计算噪声方差

    参数:
        snr_db: 信噪比（dB）
        symbol_power: 符号功率（默认 1）

    返回:
        sigma²: 噪声方差（每维）

    公式:
        SNR_db = 10 * log10(E_s / N_0)
        N_0 = E_s / 10^(SNR_db/10)
        σ² = N_0 / 2 (每维方差)
    """
    snr_linear = 10 ** (snr_db / 10)
    n0 = symbol_power / snr_linear
    sigma_squared = n0 / 2

    return sigma_squared


def awgn_channel(symbols: np.ndarray, snr_db: float, seed: int = None) -> np.ndarray:
    """
    AWGN 信道

    参数:
        symbols: 发送符号序列（复数）
        snr_db: 信噪比（dB）
        seed: 随机种子（保证可复现，None 表示不固定）

    返回:
        received: 接收符号序列（发送符号 + 噪声）

    模型:
        y = x + n
        其中 n ~ CN(0, σ²) = N(0, σ²/2) + j*N(0, σ²/2)
    """
    if len(symbols) == 0:
        return np.array([], dtype=np.complex128)

    # 设置随机种子
    if seed is not None:
        np.random.seed(seed)

    # 计算噪声标准差
    sigma_squared = calculate_noise_variance(snr_db)
    sigma = np.sqrt(sigma_squared)

    # 生成复高斯噪声
    noise_real = np.random.randn(len(symbols)) * sigma
    noise_imag = np.random.randn(len(symbols)) * sigma
    noise = noise_real + 1j * noise_imag

    # 添加噪声
    received = symbols + noise

    return received


def add_noise_to_bits(bits: np.ndarray, snr_db: float, seed: int = None) -> np.ndarray:
    """
    给比特流添加噪声（BSC 信道模拟）

    注意: 这个函数主要用于测试，实际系统使用 AWGN 信道

    参数:
        bits: 输入比特流
        snr_db: 信噪比（dB）
        seed: 随机种子

    返回:
        noisy_bits: 噪声后的比特流

    注意: 这里将 SNR 转换为误码概率
    """
    if seed is not None:
        np.random.seed(seed)

    # 简化的误码概率计算
    from scipy import special
    snr_linear = 10 ** (snr_db / 10)
    ber = 0.5 * special.erfc(np.sqrt(2 * snr_linear) / np.sqrt(2))

    # 随机翻转比特
    error_positions = np.random.rand(len(bits)) < ber
    noisy_bits = bits.copy()
    noisy_bits[error_positions] ^= 1

    return noisy_bits


def measure_snr(symbols: np.ndarray, received: np.ndarray) -> float:
    """
    测量实际 SNR

    参数:
        symbols: 发送符号（已知）
        received: 接收符号

    返回:
        snr_db: 测量的 SNR（dB）
    """
    # 估计噪声
    noise = received - symbols

    # 信号功率
    signal_power = np.mean(np.abs(symbols) ** 2)

    # 噪声功率
    noise_power = np.mean(np.abs(noise) ** 2)

    # SNR
    snr_linear = signal_power / noise_power if noise_power > 0 else float('inf')
    snr_db = 10 * np.log10(snr_linear) if snr_linear > 0 else float('inf')

    return snr_db


def generate_noise_samples(length: int, snr_db: float, seed: int = None) -> np.ndarray:
    """
    生成噪声样本

    参数:
        length: 噪声样本数
        snr_db: 信噪比（dB）
        seed: 随机种子

    返回:
        noise: 复高斯噪声序列
    """
    if seed is not None:
        np.random.seed(seed)

    sigma_squared = calculate_noise_variance(snr_db)
    sigma = np.sqrt(sigma_squared)

    noise = sigma * (np.random.randn(length) + 1j * np.random.randn(length))

    return noise


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    print("AWGN 信道测试")
    print("=" * 50)

    # 测试噪声方差计算
    for snr_db in [0, 5, 10, 12, 15, 20]:
        sigma_squared = calculate_noise_variance(snr_db)
        sigma = np.sqrt(sigma_squared)
        print(f"SNR {snr_db} dB: σ² = {sigma_squared:.4f}, σ = {sigma:.4f}")

    # 测试 AWGN 信道
    test_symbols = np.array([1+1j, -1+1j, -1-1j, 1-1j], dtype=np.complex128) / np.sqrt(2)

    print(f"\n发送符号: {test_symbols}")

    # SNR 12 dB
    snr_db = 12
    received = awgn_channel(test_symbols, snr_db, seed=2026)
    print(f"接收符号 (SNR {snr_db} dB): {received}")

    # 测量 SNR
    measured_snr = measure_snr(test_symbols, received)
    print(f"测量 SNR: {measured_snr:.2f} dB")

    # 可复现性测试
    received1 = awgn_channel(test_symbols, snr_db, seed=2026)
    received2 = awgn_channel(test_symbols, snr_db, seed=2026)
    print(f"可复现性验证: {np.allclose(received1, received2)}")

    # 绘制噪声影响
    plt.figure(figsize=(12, 5))

    # 发送符号
    plt.subplot(1, 2, 1)
    plt.scatter(test_symbols.real, test_symbols.imag, s=100, c='blue', marker='o', label='TX')
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    plt.axvline(x=0, color='k', linestyle='--', alpha=0.3)
    plt.grid(True, alpha=0.3)
    plt.xlabel('In-phase (I)')
    plt.ylabel('Quadrature (Q)')
    plt.title('Transmitted Symbols')
    plt.legend()
    plt.axis('equal')

    # 接收符号
    plt.subplot(1, 2, 2)
    many_symbols = np.tile(test_symbols, 100)
    received_many = awgn_channel(many_symbols, snr_db=12, seed=42)
    plt.scatter(received_many.real, received_many.imag, s=1, c='red', alpha=0.5, label='RX')
    plt.scatter(test_symbols.real, test_symbols.imag, s=100, c='blue', marker='o', label='TX')
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    plt.axvline(x=0, color='k', linestyle='--', alpha=0.3)
    plt.grid(True, alpha=0.3)
    plt.xlabel('In-phase (I)')
    plt.ylabel('Quadrature (Q)')
    plt.title(f'Received Symbols (SNR = 12 dB)')
    plt.legend()
    plt.axis('equal')

    plt.tight_layout()
    plt.savefig('awgn_test.png', dpi=150)
    print(f"\n测试图已保存: awgn_test.png")
