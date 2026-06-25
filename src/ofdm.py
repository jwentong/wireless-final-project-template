import numpy as np

def ofdm_modulate(symbols, n_fft=64, cp_len=16):
    symbols = np.array(symbols, dtype=complex)
    n_symbols = len(symbols)
    n_data_carriers = min(n_fft - 4, n_symbols)
    n_ofdm_symbols = int(np.ceil(n_symbols / n_data_carriers))
    padded = np.zeros(n_ofdm_symbols * n_data_carriers, dtype=complex)
    padded[:n_symbols] = symbols
    output = []
    for i in range(n_ofdm_symbols):
        data = padded[i * n_data_carriers:(i + 1) * n_data_carriers]
        freq_domain = np.zeros(n_fft, dtype=complex)
        freq_domain[2:2 + n_data_carriers] = data
        time_domain = np.fft.ifft(np.fft.ifftshift(freq_domain)) * np.sqrt(n_fft)
        with_cp = np.concatenate([time_domain[-cp_len:], time_domain])
        output.extend(with_cp)
    return np.array(output)

def ofdm_demodulate(signal, n_fft=64, cp_len=16):
    signal = np.array(signal, dtype=complex)
    total_len = n_fft + cp_len
    n_ofdm_symbols = len(signal) // total_len
    signal = signal[:n_ofdm_symbols * total_len]
    n_data_carriers = n_fft - 4
    output = []
    for i in range(n_ofdm_symbols):
        ofdm_sym = signal[i * total_len + cp_len:(i + 1) * total_len]
        freq_domain = np.fft.fftshift(np.fft.fft(ofdm_sym)) / np.sqrt(n_fft)
        data = freq_domain[2:2 + n_data_carriers]
        output.extend(data)
    return np.array(output)
