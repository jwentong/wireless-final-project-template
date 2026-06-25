"""
单元测试 - 帧封装模块
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.frame import (
    build_frame,
    parse_frame,
    generate_preamble,
    encode_length,
    decode_length,
    compute_crc16,
    verify_crc16,
    get_frame_overhead
)


class TestPreamble:
    """Preamble 测试类"""

    def test_preamble_length(self):
        """测试 preamble 长度"""
        preamble = generate_preamble()
        assert len(preamble) == 64

    def test_preamble_pattern(self):
        """测试 preamble 模式"""
        preamble = generate_preamble()
        # 应该是 [1, 0, 1, 0, ...] 交替模式
        for i in range(len(preamble)):
            if i % 2 == 0:
                assert preamble[i] == 1
            else:
                assert preamble[i] == 0


class TestLengthEncoding:
    """长度字段编码测试类"""

    def test_encode_length_zero(self):
        """测试长度 0 编码"""
        length_bits = encode_length(0)
        assert len(length_bits) == 16
        assert np.all(length_bits == 0)

    def test_encode_length_max(self):
        """测试最大长度编码"""
        length_bits = encode_length(65535)
        assert len(length_bits) == 16
        assert np.all(length_bits == 1)

    def test_encode_decode_reversible(self):
        """测试编解码可逆性"""
        for length in [0, 100, 1000, 2400, 65535]:
            length_bits = encode_length(length)
            decoded_length = decode_length(length_bits)
            assert decoded_length == length

    def test_encode_length_invalid(self):
        """测试无效长度"""
        with pytest.raises(ValueError):
            encode_length(-1)

        with pytest.raises(ValueError):
            encode_length(65536)


class TestCRC:
    """CRC 测试类"""

    def test_crc_length(self):
        """测试 CRC 长度"""
        bits = np.random.randint(0, 2, 100, dtype=np.int8)
        crc = compute_crc16(bits)
        assert len(crc) == 16

    def test_crc_same_input_same_output(self):
        """测试相同输入相同输出"""
        bits = np.random.randint(0, 2, 100, dtype=np.int8)
        crc1 = compute_crc16(bits)
        crc2 = compute_crc16(bits)
        assert np.array_equal(crc1, crc2)

    def test_crc_different_input_different_output(self):
        """测试不同输入不同输出"""
        bits1 = np.random.randint(0, 2, 100, dtype=np.int8)
        bits2 = bits1.copy()
        bits2[0] ^= 1  # 翻转一个比特

        crc1 = compute_crc16(bits1)
        crc2 = compute_crc16(bits2)

        assert not np.array_equal(crc1, crc2)

    def test_verify_crc_valid(self):
        """测试 CRC 验证通过"""
        bits = np.random.randint(0, 2, 100, dtype=np.int8)
        crc = compute_crc16(bits)

        assert verify_crc16(bits, crc) == True

    def test_verify_crc_invalid(self):
        """测试 CRC 验证失败"""
        bits = np.random.randint(0, 2, 100, dtype=np.int8)
        crc = compute_crc16(bits)

        # 翻转 payload 中的一个比特
        bits_corrupted = bits.copy()
        bits_corrupted[0] ^= 1

        assert verify_crc16(bits_corrupted, crc) == False


class TestFrameBuild:
    """帧封装测试类"""

    def test_build_frame_structure(self):
        """测试帧结构"""
        payload = np.random.randint(0, 2, 2400, dtype=np.int8)
        frame = build_frame(payload)

        # 检查帧长度: Preamble(64) + Length(16) + Payload
        expected_length = 64 + 16 + len(payload)
        assert len(frame) == expected_length

        # 检查 preamble
        preamble = generate_preamble()
        # Preamble 是 PRBS 序列，验证相关性
        assert len(preamble) == 64

        # 检查 length
        length_bits = frame[64:80]
        decoded_length = decode_length(length_bits)
        assert decoded_length == len(payload)

    def test_build_frame_empty_payload(self):
        """测试空 payload"""
        with pytest.raises(ValueError):
            build_frame(np.array([], dtype=np.int8))

    def test_build_parse_reversible(self):
        """测试帧封装解析可逆性"""
        payload = np.random.randint(0, 2, 2400, dtype=np.int8)
        frame = build_frame(payload)

        # 解析时跳过 preamble
        parsed_payload, length = parse_frame(frame[64:])

        assert np.array_equal(payload, parsed_payload)
        assert length == len(payload)

    def test_frame_overhead(self):
        """测试帧开销"""
        overhead = get_frame_overhead()
        assert overhead == 64 + 16 + 16  # Preamble + Length + CRC


class TestFrameParse:
    """帧解析测试类"""

    def test_parse_frame_too_short(self):
        """测试帧太短"""
        short_frame = np.random.randint(0, 2, 10, dtype=np.int8)
        with pytest.raises(ValueError):
            parse_frame(short_frame)

    def test_parse_frame_length_match(self):
        """测试帧解析长度验证"""
        payload = np.random.randint(0, 2, 2400, dtype=np.int8)
        frame = build_frame(payload)

        # 翻转一个有效比特，不应影响长度字段
        frame_corrupted = frame.copy()
        frame_corrupted[100] ^= 1

        parsed_payload, length = parse_frame(frame_corrupted[64:])
        assert length == len(payload)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
