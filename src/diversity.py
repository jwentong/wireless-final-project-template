import numpy as np

def maximal_ratio_combine(received_signals, channel_estimates):
    received_signals = np.array(received_signals, dtype=complex)
    channel_estimates = np.array(channel_estimates, dtype=complex)
    combined = np.sum(received_signals * np.conj(channel_estimates), axis=0)
    return combined

def selection_combine(received_signals, channel_estimates):
    received_signals = np.array(received_signals, dtype=complex)
    channel_estimates = np.array(channel_estimates, dtype=complex)
    powers = np.abs(channel_estimates) ** 2
    best_idx = np.argmax(np.mean(powers, axis=1))
    return received_signals[best_idx]

def equal_gain_combine(received_signals):
    received_signals = np.array(received_signals, dtype=complex)
    return np.sum(received_signals, axis=0) / received_signals.shape[0]
