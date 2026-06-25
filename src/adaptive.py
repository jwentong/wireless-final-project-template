SNR_THRESHOLDS = [
    (0, "bpsk"),
    (8, "qpsk"),
    (15, "16qam"),
]

def select_modulation(snr_db):
    best = "qpsk"
    for threshold, mod in SNR_THRESHOLDS:
        if snr_db >= threshold:
            best = mod
    return best

def get_bits_per_symbol(modulation):
    table = {"bpsk": 1, "qpsk": 2, "16qam": 4}
    return table.get(modulation, 2)
