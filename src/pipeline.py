"""End-to-end transmit / receive orchestration.

Wires the fixed PRD link together:
    transmit:  source_encode -> (CRC over original bits) -> scramble
               -> channel_encode -> build_frame -> modulate
    channel:   random leading offset -> AWGN / Rayleigh / Rician
    receive:   synchronize -> (equalize) -> demodulate -> parse_frame
               -> channel_decode -> descramble -> CRC check -> source_decode

The end-to-end CRC covers the ORIGINAL payload bitstream (per PRD) and rides
inside the channel-coded payload, so it is FEC-protected: after Viterbi
correction the checksum passes whenever the text is correctly recovered. The
base system uses QPSK + AWGN; fading channels add preamble-based channel
estimation + MMSE equalization (Level-3 module).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.source import source_encode, source_decode
from src.scramble import scramble, descramble
from src.channel_coding import channel_encode, channel_decode, conv_encode, viterbi_decode
from src.framing import build_frame, parse_frame, PREAMBLE_BITS
from src.modulation import modulate, demodulate, qpsk_modulate, qpsk_demodulate
from src.channel import awgn, rayleigh, rician
from src.equalizer import mmse_equalize
from src.synchronization import correlate
from src.metrics import ber, fer, text_match_rate, crc16

_CRC_BITS = 16


def _int_to_bits(x: int, n: int) -> list[int]:
    return [(x >> (n - 1 - i)) & 1 for i in range(n)]


def _bits_to_int(bits: list[int]) -> int:
    v = 0
    for b in bits:
        v = (v << 1) | int(b)
    return v


@dataclass
class Config:
    """Runtime configuration for one end-to-end run."""
    snr_db: float = 12.0
    seed: int = 2026
    mod: str = "qpsk"
    channel: str = "awgn"
    code: str = "conv"


def transmit(text: str, cfg: Config) -> tuple[np.ndarray, dict]:
    """Run the transmit chain; return modulated symbols and tx-side info."""
    orig = source_encode(text)
    info = orig + _int_to_bits(crc16(orig), _CRC_BITS)   # CRC covers original bits
    scr = scramble(info, cfg.seed)
    coded = channel_encode(scr, cfg.code)
    frame = build_frame(coded, orig_len=len(orig))
    symbols = modulate(frame, cfg.mod)
    return symbols, {"orig_bits": orig, "orig_len": len(orig)}


def apply_channel(symbols: np.ndarray, cfg: Config) -> tuple[np.ndarray, np.ndarray | None, int]:
    """Insert a seeded random leading offset, then apply the channel."""
    rng = np.random.default_rng(cfg.seed)
    offset = int(rng.integers(0, 129))  # 0..128 symbols per PRD
    if offset:
        prefix = (rng.standard_normal(offset) + 1j * rng.standard_normal(offset)) / np.sqrt(2)
        tx = np.concatenate([prefix, symbols])
    else:
        tx = symbols
    if cfg.channel == "rayleigh":
        rx, h = rayleigh(tx, cfg.snr_db, cfg.seed)
    elif cfg.channel == "rician":
        rx, h = rician(tx, cfg.snr_db, cfg.seed)
    else:
        rx, h = awgn(tx, cfg.snr_db, cfg.seed), None
    return rx, h, offset


def receive(rx: np.ndarray, cfg: Config) -> dict:
    """Run the receive chain; return recovered text, sync info and diagnostics."""
    preamble_syms = modulate(PREAMBLE_BITS, cfg.mod)
    corr = correlate(rx, preamble_syms)
    start = int(np.argmax(corr)) if corr.size else 0
    frame_syms = rx[start:]
    if cfg.channel in ("rayleigh", "rician"):
        lp = len(preamble_syms)
        rx_pre = frame_syms[:lp]
        h_est = np.vdot(preamble_syms, rx_pre) / np.vdot(preamble_syms, preamble_syms)
        frame_syms = mmse_equalize(frame_syms, np.full(frame_syms.shape, h_est), cfg.snr_db)
    frame_bits = demodulate(frame_syms, cfg.mod)
    parsed = parse_frame(frame_bits)
    orig_len = parsed["length"]
    decoded = channel_decode(parsed["payload"], cfg.code)
    info = descramble(decoded[: orig_len + _CRC_BITS], cfg.seed)
    orig = info[:orig_len]
    crc_field = info[orig_len:orig_len + _CRC_BITS]
    checksum_pass = len(crc_field) == _CRC_BITS and crc16(orig) == _bits_to_int(crc_field)
    usable = orig[: (len(orig) // 8) * 8]
    try:
        text = source_decode(usable)
    except UnicodeDecodeError:
        text = ""
    return {
        "text": text, "start": start, "parsed": parsed, "corr": corr,
        "rx_symbols": frame_syms, "recovered_orig": orig, "checksum_pass": bool(checksum_pass),
    }


def run_end_to_end(text: str, cfg: Config) -> dict:
    """Full transmit->channel->receive run, returning text, metrics and plot data."""
    symbols, tx_info = transmit(text, cfg)
    rx, _h, offset = apply_channel(symbols, cfg)
    res = receive(rx, cfg)
    bit_err = ber(tx_info["orig_bits"], res["recovered_orig"])
    tmr = text_match_rate(text, res["text"])
    frame_ok = bool(res["checksum_pass"] and res["text"] == text)
    metrics = {
        "snr_db": float(cfg.snr_db),
        "seed": int(cfg.seed),
        "modulation": cfg.mod,
        "channel": cfg.channel,
        "payload_bits": int(tx_info["orig_len"]),
        "ber": float(bit_err),
        "fer": float(fer(frame_ok)),
        "text_match_rate": float(tmr),
        "checksum_pass": bool(res["checksum_pass"]),
        "sync_start_index": int(res["start"]),
    }
    return {
        "received_text": res["text"], "metrics": metrics,
        "rx_symbols": res["rx_symbols"], "corr": res["corr"], "true_offset": offset,
    }


def ber_vs_snr(snr_list, seed: int = 2026, n_bits: int = 4000) -> tuple[list[float], list[float]]:
    """Symbol-level BER comparison: uncoded QPSK vs QPSK + convolutional code."""
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, n_bits).tolist()
    uncoded: list[float] = []
    coded: list[float] = []
    for snr in snr_list:
        rb = qpsk_demodulate(awgn(qpsk_modulate(bits), snr, seed))[:n_bits]
        uncoded.append(ber(bits, rb))
        rb2 = qpsk_demodulate(awgn(qpsk_modulate(conv_encode(bits)), snr, seed))
        coded.append(ber(bits, viterbi_decode(rb2)[:n_bits]))
    return uncoded, coded
