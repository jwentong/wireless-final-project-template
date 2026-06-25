import math
import numpy as np

QPSK_MAP = {
    (0, 0): (1 + 1j) / math.sqrt(2),
    (0, 1): (-1 + 1j) / math.sqrt(2),
    (1, 1): (-1 - 1j) / math.sqrt(2),
    (1, 0): (1 - 1j) / math.sqrt(2),
}
QPSK_DEMAP = {v: k for k, v in QPSK_MAP.items()}

BPSK_MAP = {0: 1 + 0j, 1: -1 + 0j}
BPSK_DEMAP = {v: k for k, v in BPSK_MAP.items()}

QAM16_MAP = {}
gray_2bit = [(0, 0), (0, 1), (1, 1), (1, 0)]
norm = math.sqrt(10)
for i, (b1, b2) in enumerate(gray_2bit):
    for j, (b3, b4) in enumerate(gray_2bit):
        real = (2 * i - 3) / norm
        imag = (2 * j - 3) / norm
        QAM16_MAP[(b1, b2, b3, b4)] = real + 1j * imag

def qpsk_modulate(bits):
    bits = list(bits)
    if len(bits) % 2 != 0:
        bits.append(0)
    symbols = []
    for i in range(0, len(bits), 2):
        key = (bits[i], bits[i + 1])
        symbols.append(QPSK_MAP[key])
    return symbols

def qpsk_demodulate(symbols):
    bits = []
    for s in symbols:
        s_imag = s.imag if isinstance(s, complex) else 0
        s_real = s.real if isinstance(s, complex) else s
        b0 = 0 if s_imag >= 0 else 1
        b1 = 0 if s_real >= 0 else 1
        bits.append(b0)
        bits.append(b1)
    return bits

def qpsk_mapper(bits):
    return qpsk_modulate(bits)

def qpsk_demapper(symbols):
    return qpsk_demodulate(symbols)

def bpsk_modulate(bits):
    bits = list(bits)
    return [BPSK_MAP[b] for b in bits]

def bpsk_demodulate(symbols):
    bits = []
    for s in symbols:
        s_real = s.real if isinstance(s, complex) else s
        bits.append(0 if s_real >= 0 else 1)
    return bits

def qam16_modulate(bits):
    bits = list(bits)
    if len(bits) % 4 != 0:
        bits.extend([0] * (4 - len(bits) % 4))
    symbols = []
    for i in range(0, len(bits), 4):
        key = (bits[i], bits[i + 1], bits[i + 2], bits[i + 3])
        symbols.append(QAM16_MAP[key])
    return symbols

def qam16_demodulate(symbols):
    bits = []
    norm = math.sqrt(10)
    for s in symbols:
        s_real = s.real if isinstance(s, complex) else s
        s_imag = s.imag if isinstance(s, complex) else 0
        ri = round((s_real * norm + 3) / 2)
        rj = round((s_imag * norm + 3) / 2)
        ri = max(0, min(3, ri))
        rj = max(0, min(3, rj))
        gray_i = [0, 1, 3, 2]
        gray_j = [0, 1, 3, 2]
        bits.append((gray_i[ri] >> 1) & 1)
        bits.append(gray_i[ri] & 1)
        bits.append((gray_j[rj] >> 1) & 1)
        bits.append(gray_j[rj] & 1)
    return bits

def modulate(bits, scheme="qpsk"):
    if scheme == "qpsk":
        return qpsk_modulate(bits)
    elif scheme == "bpsk":
        return bpsk_modulate(bits)
    elif scheme == "16qam":
        return qam16_modulate(bits)
    return qpsk_modulate(bits)

def demodulate(symbols, scheme="qpsk"):
    if scheme == "qpsk":
        return qpsk_demodulate(symbols)
    elif scheme == "bpsk":
        return bpsk_demodulate(symbols)
    elif scheme == "16qam":
        return qam16_demodulate(symbols)
    return qpsk_demodulate(symbols)
