import numpy as np
import pytest


SAMPLE_TEXT = "无线通信技术课程要求学生理解调制、编码、信道和接收机处理。"


@pytest.fixture
def sample_text():
    return SAMPLE_TEXT


@pytest.fixture
def sample_bits():
    from src.source import source_encode
    return source_encode(SAMPLE_TEXT)


@pytest.fixture
def test_payload():
    return [1, 0, 1, 1, 0, 1, 0, 0]


@pytest.fixture
def qpsk_preamble():
    return np.array(
        [1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j] * 8, dtype=complex
    ) / np.sqrt(2)


@pytest.fixture
def random_seed():
    return 2026
