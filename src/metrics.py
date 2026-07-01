"""性能指标计算：BER / FER / 文本一致率"""
from __future__ import annotations
import difflib


def bit_error_rate(ref_bits, rx_bits):
    ref = list(ref_bits)
    rx = list(rx_bits)
    n = min(len(ref), len(rx))
    if n == 0:
        return 1.0
    errors = sum(1 for i in range(n) if int(ref[i]) != int(rx[i]))
    errors += abs(len(ref) - len(rx))
    return errors / max(len(ref), len(rx), 1)


def frame_error_rate(ref_bits, rx_bits):
    return 0.0 if list(ref_bits) == list(rx_bits) else 1.0


def text_match_rate(ref_text, rx_text):
    if ref_text == rx_text:
        return 1.0
    return difflib.SequenceMatcher(None, ref_text, rx_text).ratio()
