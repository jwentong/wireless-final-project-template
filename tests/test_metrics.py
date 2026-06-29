from src.metrics import crc16, ber, fer, text_match_rate


def test_ber_zero_when_identical():
    assert ber([1, 0, 1], [1, 0, 1]) == 0.0


def test_ber_one_when_all_wrong():
    assert ber([0, 0, 0], [1, 1, 1]) == 1.0


def test_ber_half():
    assert ber([0, 0, 1, 1], [0, 1, 1, 0]) == 0.5


def test_fer():
    assert fer(True) == 0.0
    assert fer(False) == 1.0


def test_text_match_identical():
    assert text_match_rate("无线通信", "无线通信") == 1.0


def test_text_match_partial():
    assert 0.0 < text_match_rate("abcd", "abxd") < 1.0


def test_crc16_deterministic_and_sensitive():
    assert crc16([1, 0, 1, 1, 0, 0, 1, 0]) == crc16([1, 0, 1, 1, 0, 0, 1, 0])
    assert crc16([1, 0, 1, 1]) != crc16([1, 0, 1, 0])
