from __future__ import annotations

from difflib import SequenceMatcher


def _clean_bits(bits) -> list[int]:
    return [1 if int(bit) else 0 for bit in list(bits)]


def bit_error_rate(reference, recovered) -> float:
    ref = _clean_bits(reference)
    rec = _clean_bits(recovered)
    total = max(len(ref), len(rec))
    if total == 0:
        return 0.0
    common = min(len(ref), len(rec))
    errors = sum(ref[i] != rec[i] for i in range(common))
    errors += abs(len(ref) - len(rec))
    return errors / total


def text_match_rate(reference: str, recovered: str) -> float:
    if reference == recovered:
        return 1.0
    if not reference and not recovered:
        return 1.0
    return SequenceMatcher(None, reference, recovered).ratio()
