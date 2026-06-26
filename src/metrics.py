from difflib import SequenceMatcher


def bit_error_rate(reference: list[int], recovered: list[int]) -> float:
    if not reference:
        return 0.0 if not recovered else 1.0
    compare_len = min(len(reference), len(recovered))
    errors = sum(1 for i in range(compare_len) if reference[i] != recovered[i])
    errors += abs(len(reference) - len(recovered))
    return errors / len(reference)


def text_match_rate(reference: str, recovered: str) -> float:
    if not reference:
        return 1.0 if not recovered else 0.0
    return SequenceMatcher(None, reference, recovered).ratio()
