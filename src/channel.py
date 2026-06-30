import numpy as np


def awgn_channel(symbols: np.ndarray, snr_db: float, seed: int = 2026) -> np.ndarray:
    """
    AWGN 加性高斯白噪声信道
    :param symbols: 发送端调制符号序列
    :param snr_db: 信噪比，单位 dB
    :param seed: 随机种子，保证结果可复现
    :return: 叠加噪声后的接收符号序列
    """
    rng = np.random.default_rng(seed)
    snr_linear = 10 ** (snr_db / 10)
    
    # QPSK 符号归一化后平均功率为 1，噪声功率 = 1 / SNR
    noise_power = 1.0 / snr_linear
    # 复高斯噪声：实部虚部独立，各占一半功率
    sigma = np.sqrt(noise_power / 2)
    
    noise = rng.normal(0, sigma, len(symbols)) + 1j * rng.normal(0, sigma, len(symbols))
    return symbols + noise

def rayleigh_channel(symbols: np.ndarray, snr_db: float, seed: int = 2026) -> np.ndarray:
    """
    平坦瑞利（Rayleigh）衰落信道 + AWGN 噪声
    信道系数为复高斯分布，平均信道增益归一化为1，保证SNR定义与AWGN可比
    :param symbols: 发送端调制符号序列
    :param snr_db: 信噪比，单位 dB
    :param seed: 随机种子，保证结果可复现
    :return: 经过衰落和噪声后的接收符号序列
    """
    rng = np.random.default_rng(seed)
    n_symbols = len(symbols)
    
    # 生成瑞利衰落信道系数：实部虚部独立高斯分布，平均功率为1
    h_real = rng.normal(0, np.sqrt(0.5), n_symbols)
    h_imag = rng.normal(0, np.sqrt(0.5), n_symbols)
    h = h_real + 1j * h_imag
    
    # 信号经过衰落
    faded_symbols = h * symbols
    
    # 叠加AWGN噪声（与AWGN信道噪声模型完全一致）
    snr_linear = 10 ** (snr_db / 10)
    noise_power = 1.0 / snr_linear
    sigma = np.sqrt(noise_power / 2)
    noise = rng.normal(0, sigma, n_symbols) + 1j * rng.normal(0, sigma, n_symbols)
    
    return faded_symbols + noise