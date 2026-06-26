"""Small file and bit utility helpers."""

from __future__ import annotations

from pathlib import Path

from .source_codec import bits_to_bytes


def ensure_parent_dir(path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def safe_bits_to_text(bits: list[int]) -> tuple[str, str | None]:
    """Decode bits as UTF-8, returning replacement text on decode failure."""
    usable_length = len(bits) - (len(bits) % 8)
    usable_bits = bits[:usable_length]
    try:
        return bits_to_bytes(usable_bits).decode("utf-8"), None
    except UnicodeDecodeError as exc:
        text = bits_to_bytes(usable_bits).decode("utf-8", errors="replace")
        return text, f"utf8_decode_error: {exc}"


def compare_bits(expected: list[int], actual: list[int]) -> tuple[int, float]:
    if not expected:
        return (0 if not actual else len(actual), 0.0 if not actual else 1.0)
    common = min(len(expected), len(actual))
    errors = sum(1 for left, right in zip(expected[:common], actual[:common]) if left != right)
    errors += abs(len(expected) - len(actual))
    return errors, errors / len(expected)
