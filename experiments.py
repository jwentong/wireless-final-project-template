"""Generate Level-3 comparison figures for the report.

Offline analysis (not bound by the CLI test timeout): sweeps BER over SNR to
compare (1) FEC schemes, (2) modulations, (3) AWGN vs Rayleigh with ZF/MMSE
equalization. Writes PNGs into results/. Run: python experiments.py
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np
import matplotlib.pyplot as plt

from src.modulation import (
    qpsk_modulate, qpsk_demodulate,
    bpsk_modulate, bpsk_demodulate,
    qam16_modulate, qam16_demodulate,
)
from src.channel import awgn, rayleigh
from src.channel_coding import conv_encode, viterbi_decode, hamming_encode, hamming_decode
from src.equalizer import zf_equalize, mmse_equalize
from src.metrics import ber

OUT = Path("results")
OUT.mkdir(exist_ok=True)
SNRS = list(range(0, 15, 2))
FLOOR = 1e-5


def sweep_fec(seed: int = 2026, n: int = 20000):
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, n).tolist()
    uncoded, hamming, conv = [], [], []
    for snr in SNRS:
        uncoded.append(ber(bits, qpsk_demodulate(awgn(qpsk_modulate(bits), snr, seed))[:n]))
        hr = qpsk_demodulate(awgn(qpsk_modulate(hamming_encode(bits)), snr, seed))
        hamming.append(ber(bits, hamming_decode(hr)[:n]))
        cr = qpsk_demodulate(awgn(qpsk_modulate(conv_encode(bits)), snr, seed))
        conv.append(ber(bits, viterbi_decode(cr)[:n]))
    return uncoded, hamming, conv


def sweep_modulation(seed: int = 2026, n: int = 24000):
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, n).tolist()
    out = {}
    for name, mod, demod in [
        ("BPSK", bpsk_modulate, bpsk_demodulate),
        ("QPSK", qpsk_modulate, qpsk_demodulate),
        ("16-QAM", qam16_modulate, qam16_demodulate),
    ]:
        out[name] = [ber(bits, demod(awgn(mod(bits), snr, seed))[:n]) for snr in SNRS]
    return out


def sweep_fading(seed: int = 2026, n: int = 40000):
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, n).tolist()
    sy = qpsk_modulate(bits)
    awgn_c, ray_noeq, ray_zf, ray_mmse = [], [], [], []
    for snr in SNRS:
        awgn_c.append(ber(bits, qpsk_demodulate(awgn(sy, snr, seed))[:n]))
        rx, h = rayleigh(sy, snr, seed, block_fading=False)
        ray_noeq.append(ber(bits, qpsk_demodulate(rx)[:n]))
        ray_zf.append(ber(bits, qpsk_demodulate(zf_equalize(rx, h))[:n]))
        ray_mmse.append(ber(bits, qpsk_demodulate(mmse_equalize(rx, h, snr))[:n]))
    return awgn_c, ray_noeq, ray_zf, ray_mmse


def plot(curves, title, fname):
    plt.figure(figsize=(6, 4))
    for curve, label, style in curves:
        plt.semilogy(SNRS, [max(b, FLOOR) for b in curve], style, label=label)
    plt.grid(True, which="both", ls=":")
    plt.legend()
    plt.xlabel("SNR (dB)")
    plt.ylabel("BER")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(OUT / fname, dpi=120)
    plt.close()


def main() -> None:
    unc, ham, con = sweep_fec()
    plot([(unc, "QPSK uncoded", "o-"), (ham, "Hamming(7,4)", "^-"),
          (con, "Conv K=7 + Viterbi", "s-")],
         "FEC comparison (QPSK, AWGN)", "fec_comparison.png")

    mod = sweep_modulation()
    plot([(mod["BPSK"], "BPSK", "o-"), (mod["QPSK"], "QPSK", "s-"),
          (mod["16-QAM"], "16-QAM", "^-")],
         "Modulation comparison (AWGN, uncoded)", "modulation_comparison.png")

    a, rn, rz, rm = sweep_fading()
    # For QPSK (phase-only decision) ZF and MMSE differ only by a positive real
    # scale, so their hard-decision BER coincides; ZF drawn dashed on top to show it.
    plot([(a, "AWGN", "o-"), (rn, "Rayleigh no-eq", "x-"),
          (rm, "Rayleigh MMSE", "s-"), (rz, "Rayleigh ZF (≈MMSE for QPSK)", "--")],
         "Fading & equalization (QPSK)", "fading_comparison.png")

    print("generated: fec_comparison.png, modulation_comparison.png, fading_comparison.png")
    for tag, unc_v, con_v in [("uncoded@10dB", unc[5], con[5])]:
        print(f"  coding gain check: QPSK {tag} BER {unc_v:.2e} -> conv {con_v:.2e}")


if __name__ == "__main__":
    main()
