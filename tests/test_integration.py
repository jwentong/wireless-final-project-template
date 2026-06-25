"""
集成测试 - 端到端通信链路
"""

import pytest
import numpy as np
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.source_codec import source_encode, source_decode
from src.scrambler import LFSRScrambler
from src.channel_codec import ChannelCodec
from src.frame import build_frame, parse_frame, generate_preamble
from src.qpsk import qpsk_modulate, qpsk_demodulate
from src.awgn import awgn_channel
from src.sync import detect_frame_with_offset
from src.metrics import calculate_ber, calculate_text_match_rate


class TestEndToEnd:
    """端到端测试类"""

    def test_end_to_end_no_noise(self):
        """测试无噪声端到端传输"""
        # 输入文本
        input_text = "无线通信技术测试"

        # 发送端
        # 1. 源编码
        original_bits = source_encode(input_text)

        # 2. 扰码
        scrambler = LFSRScrambler(seed=2026)
        scrambled_bits = scrambler.scramble(original_bits)

        # 3. 信道编码
        codec = ChannelCodec()
        encoded_bits = codec.encode(scrambled_bits)

        # 4. 帧封装
        frame_bits = build_frame(encoded_bits)

        # 5. QPSK 调制
        tx_symbols = qpsk_modulate(frame_bits)

        # 接收端（无噪声）
        # 6. QPSK 解调
        rx_bits = qpsk_demodulate(tx_symbols)

        # 7. 帧解析
        payload_bits, _ = parse_frame(rx_bits[64:])

        # 8. 信道译码
        decoded_bits = codec.decode(payload_bits)

        # 9. 解扰
        descrambled_bits = scrambler.descramble(decoded_bits)

        # 10. 源解码
        output_text = source_decode(descrambled_bits)

        # 验证
        assert output_text == input_text
        assert crc_valid == True

    def test_end_to_end_awgn_12dB(self):
        """测试 SNR 12 dB 端到端传输"""
        input_text = "无线通信技术课程要求学生理解调制编码信道和接收机处理"

        # 发送端处理
        original_bits = source_encode(input_text)

        scrambler = LFSRScrambler(seed=2026)
        scrambled_bits = scrambler.scramble(original_bits)

        codec = ChannelCodec()
        encoded_bits = codec.encode(scrambled_bits)

        frame_bits = build_frame(encoded_bits)

        tx_symbols = qpsk_modulate(frame_bits)

        # AWGN 信道 (SNR 12 dB)
        rx_symbols = awgn_channel(tx_symbols, snr_db=12, seed=2026)

        # 接收端处理
        rx_bits = qpsk_demodulate(rx_symbols)

        payload_bits, _ = parse_frame(rx_bits[64:])

        decoded_bits = codec.decode(payload_bits)

        descrambled_bits = scrambler.descramble(decoded_bits)

        output_text = source_decode(descrambled_bits)

        # 计算性能指标
        text_match_rate = calculate_text_match_rate(input_text, output_text)

        # SNR 12 dB 下应该完全恢复
        assert text_match_rate >= 0.99

    def test_end_to_end_with_offset(self):
        """测试带偏移的端到端传输"""
        input_text = "测试同步功能"

        # 发送端处理
        original_bits = source_encode(input_text)
        scrambler = LFSRScrambler(seed=2026)
        scrambled_bits = scrambler.scramble(original_bits)
        codec = ChannelCodec()
        encoded_bits = codec.encode(scrambled_bits)
        frame_bits = build_frame(encoded_bits)
        tx_symbols = qpsk_modulate(frame_bits)

        # 添加偏移
        offset_symbols = 25
        np.random.seed(2026)
        offset = (np.random.randn(offset_symbols) + 1j * np.random.randn(offset_symbols)) / np.sqrt(2)
        tx_with_offset = np.concatenate([offset, tx_symbols])

        # AWGN 信道
        rx_symbols = awgn_channel(tx_with_offset, snr_db=12, seed=2026)

        # 同步检测
        preamble_bits = generate_preamble()
        sync_index, _ = detect_frame_with_offset(rx_symbols, preamble_bits)

        # 验证同步误差
        sync_error = abs(sync_index - offset_symbols)
        assert sync_error <= 1  # 同步误差 ≤ 1 符号

        # 提取帧并处理
        frame_start = sync_index + len(preamble_bits) // 2
        rx_frame = rx_symbols[frame_start:]

        rx_bits = qpsk_demodulate(rx_frame)
        payload_bits, _, _ = parse_frame(rx_bits[64:])

        decoded_bits = codec.decode(payload_bits)
        descrambled_bits = scrambler.descramble(decoded_bits)
        output_text = source_decode(descrambled_bits)

        assert output_text == input_text


class TestModuleIntegration:
    """模块集成测试类"""

    def test_source_codec_with_scrambler(self):
        """测试源编码与扰码集成"""
        text = "测试文本"
        bits = source_encode(text)
        scrambler = LFSRScrambler(seed=2026)

        scrambled = scrambler.scramble(bits)
        descrambled = scrambler.descramble(scrambled)

        decoded_text = source_decode(descrambled)
        assert decoded_text == text

    def test_channel_codec_with_frame(self):
        """测试信道编码与帧封装集成"""
        bits = np.random.randint(0, 2, 100, dtype=np.int8)
        codec = ChannelCodec()

        encoded = codec.encode(bits)
        frame = build_frame(encoded)

        payload, _, _ = parse_frame(frame[64:])
        decoded = codec.decode(payload)

        assert np.array_equal(bits, decoded)

    def test_qpsk_with_awgn(self):
        """测试 QPSK 与 AWGN 集成"""
        bits = np.random.randint(0, 2, 1000, dtype=np.int8)
        symbols, _ = qpsk_modulate(bits)

        # SNR 20 dB（低噪声）
        rx_symbols = awgn_channel(symbols, snr_db=20, seed=2026)

        decoded_bits = qpsk_demodulate(rx_symbols)

        # 计算误码率
        ber = calculate_ber(bits, decoded_bits[:len(bits)])

        # SNR 20 dB 下 BER 应该很低
        assert ber < 0.01


class TestCLI:
    """CLI 测试类"""

    def test_main_py_execution(self):
        """测试 main.py 执行"""
        import subprocess

        # 创建临时输入文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("测试 CLI 执行")
            input_file = f.name

        # 创建临时输出目录
        output_dir = tempfile.mkdtemp()
        output_file = os.path.join(output_dir, 'received.txt')

        try:
            # 运行 main.py
            result = subprocess.run(
                ['python', 'main.py',
                 '--input', input_file,
                 '--output', output_file,
                 '--snr', '12',
                 '--seed', '2026',
                 '--mod', 'qpsk',
                 '--channel', 'awgn'],
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                capture_output=True,
                text=True,
                timeout=60
            )

            # 检查执行成功
            assert result.returncode == 0

            # 检查输出文件存在
            assert os.path.exists(output_file)

            # 检查 metrics.json 存在
            metrics_file = os.path.join(output_dir, 'metrics.json')
            assert os.path.exists(metrics_file)

        finally:
            # 清理
            if os.path.exists(input_file):
                os.remove(input_file)
            if os.path.exists(output_dir):
                import shutil
                shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
