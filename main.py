#!/usr/bin/env python3
"""
无线通信基带仿真系统 - 主程序入口

统一命令行接口:
    python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn

功能:
    1. 读取输入文本文件
    2. 发送端处理：源编码 → 扰码 → 信道编码 → 帧封装 → QPSK 调制
    3. 信道：AWGN
    4. 接收端处理：同步 → QPSK 解调 → 帧解析 → 信道译码 → 解扰 → 源解码
    5. 输出接收文本和性能指标
    6. 生成可视化图表
"""

import argparse
import sys
import os
from pathlib import Path
import numpy as np
import json

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.source_codec import source_encode, source_decode
from src.scrambler import LFSRScrambler
from src.channel_codec import ChannelCodec
from src.frame import build_frame, parse_frame, generate_preamble
from src.qpsk import qpsk_modulate_with_padding, qpsk_demodulate
from src.awgn import awgn_channel
from src.sync import detect_frame_with_offset, get_sync_peak_plot_data
from src.metrics import (
    calculate_ber,
    calculate_text_match_rate,
    generate_metrics_dict,
    save_metrics
)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='无线通信基带仿真系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
    python main.py --input Test.txt --output results/received.txt --snr 12 --seed 2026 --mod qpsk --channel awgn
        '''
    )

    parser.add_argument('--input', type=str, required=True,
                        help='输入文本文件路径')
    parser.add_argument('--output', type=str, required=True,
                        help='输出文本文件路径')
    parser.add_argument('--snr', type=float, default=12,
                        help='信噪比 (dB), 默认 12')
    parser.add_argument('--seed', type=int, default=2026,
                        help='随机种子, 默认 2026')
    parser.add_argument('--mod', type=str, default='qpsk',
                        choices=['qpsk', 'bpsk'],
                        help='调制方式, 默认 qpsk')
    parser.add_argument('--channel', type=str, default='awgn',
                        choices=['awgn', 'rayleigh'],
                        help='信道类型, 默认 awgn')
    parser.add_argument('--plots', action='store_true',
                        help='生成可视化图表')

    return parser.parse_args()


def transmitter(text: str, seed: int) -> tuple:
    """
    发送端处理

    参数:
        text: 输入文本
        seed: 扰码种子

    返回:
        tx_symbols: 发送符号
        original_bits: 原始比特流
        payload_bits: payload 比特流
    """
    print("=" * 50)
    print("发送端处理")
    print("=" * 50)

    # 1. 源编码
    print("\n[1/6] 源编码...")
    original_bits = source_encode(text)
    print(f"  原始文本长度: {len(text)} 字符")
    print(f"  编码后比特数: {len(original_bits)} bits")

    # 2. 扰码
    print("\n[2/6] 扰码...")
    scrambler = LFSRScrambler(seed=seed)
    scrambled_bits = scrambler.scramble(original_bits)
    print(f"  扰码种子: {seed}")
    print(f"  扰码后比特数: {len(scrambled_bits)} bits")

    # 2.5. CRC 计算（在信道编码之前）
    print("\n[2.5/6] CRC 计算...")
    from src.frame import compute_crc16, verify_crc16
    crc_bits = compute_crc16(scrambled_bits)
    protected_bits = np.concatenate([scrambled_bits, crc_bits])
    print(f"  CRC: CRC-16-CCITT (16 bits)")
    print(f"  添加CRC后比特数: {len(protected_bits)} bits")

    # 3. 信道编码
    print("\n[3/6] 信道编码...")
    codec = ChannelCodec()
    encoded_bits = codec.encode(protected_bits)
    print(f"  编码方式: 卷积码 (rate=1/2, K=7)")
    print(f"  编码后比特数: {len(encoded_bits)} bits")

    # 4. 帧封装
    print("\n[4/6] 帧封装...")
    frame_bits = build_frame(encoded_bits)
    print(f"  帧结构: Preamble(64) + Length(16) + Payload({len(encoded_bits)})")
    print(f"  帧总长度: {len(frame_bits)} bits")

    # 5. QPSK 调制
    print("\n[5/6] QPSK 调制...")
    tx_symbols, padded = qpsk_modulate_with_padding(frame_bits)
    print(f"  调制方式: QPSK (Gray 编码)")
    print(f"  符号数: {len(tx_symbols)}")
    print(f"  Padding: {'是' if padded else '否'}")

    # 6. 保存发送信息
    payload_bits = encoded_bits

    print("\n发送端处理完成!")

    return tx_symbols, original_bits, encoded_bits


def channel(tx_symbols: np.ndarray, snr_db: float, seed: int) -> np.ndarray:
    """
    信道传输

    参数:
        tx_symbols: 发送符号
        snr_db: 信噪比
        seed: 随机种子

    返回:
        rx_symbols: 接收符号
    """
    print("\n" + "=" * 50)
    print("信道传输")
    print("=" * 50)

    # 添加随机偏移（模拟真实信道）
    np.random.seed(seed)
    max_offset = 50  # 最大偏移 50 个符号
    actual_offset = np.random.randint(10, max_offset + 1)

    # 生成偏移噪声符号
    offset_symbols = (np.random.randn(actual_offset) + 1j * np.random.randn(actual_offset)) / np.sqrt(2)

    print(f"\n添加随机偏移: {actual_offset} 符号")

    # 拼接偏移和发送信号
    tx_with_offset = np.concatenate([offset_symbols, tx_symbols])

    # AWGN 信道
    print(f"信道类型: AWGN")
    print(f"SNR: {snr_db} dB")
    rx_symbols = awgn_channel(tx_with_offset, snr_db, seed=seed)

    print(f"\n接收符号数: {len(rx_symbols)}")

    return rx_symbols, actual_offset


def receiver(rx_symbols: np.ndarray, seed: int, snr_db: float) -> tuple:
    """
    接收端处理

    参数:
        rx_symbols: 接收符号
        seed: 扰码种子
        snr_db: 信噪比

    返回:
        received_text: 接收文本
        decoded_bits: 解码比特流
        sync_index: 同步索引
        crc_valid: CRC 校验结果
    """
    print("\n" + "=" * 50)
    print("接收端处理")
    print("=" * 50)

    # 1. 同步
    print("\n[1/6] 同步检测...")
    preamble_bits = generate_preamble()
    sync_result = detect_frame_with_offset(rx_symbols, preamble_bits)
    sync_index = sync_result["start_index"] if isinstance(sync_result, dict) else sync_result[0]
    peak_value = sync_result.get("correlation_peak", 0) if isinstance(sync_result, dict) else sync_result[1]
    print(f"  检测到的帧起始索引: {sync_index}")
    print(f"  相关峰值: {peak_value:.4f}")

    # 提取帧符号（从检测到的帧起始位置开始）
    frame_symbols = rx_symbols[sync_index:]

    # 2. QPSK 解调
    print("\n[2/6] QPSK 解调...")
    frame_bits = qpsk_demodulate(frame_symbols)
    print(f"  解调后比特数: {len(frame_bits)} bits")

    # 3. 帧解析（跳过 preamble 的 64 bits）
    print("\n[3/6] 帧解析...")
    try:
        payload_bits, payload_length = parse_frame(frame_bits[64:])
        print(f"  Payload 长度: {payload_length} bits")
    except Exception as e:
        print(f"  帧解析错误: {e}")
        payload_bits = frame_bits[80:80+12268]  # 默认尝试
        crc_valid = False
        payload_length = len(payload_bits)

    # 4. 信道译码
    print("\n[4/6] 信道译码...")
    codec = ChannelCodec()
    decoded_bits = codec.decode(payload_bits)
    print(f"  译码后比特数: {len(decoded_bits)} bits")

    # 4.5. CRC 验证（在信道译码之后）
    print("\n[4.5/6] CRC 验证...")
    from src.frame import verify_crc16
    data_bits = decoded_bits[:-16] if len(decoded_bits) > 16 else decoded_bits
    received_crc = decoded_bits[-16:] if len(decoded_bits) > 16 else np.zeros(16, dtype=np.int8)
    crc_valid = verify_crc16(data_bits, received_crc)
    print(f"  CRC 校验: {'通过' if crc_valid else '失败'}")

    # 5. 解扰
    print("\n[5/6] 解扰...")
    scrambler = LFSRScrambler(seed=seed)
    descrambled_bits = scrambler.descramble(data_bits)
    print(f"  解扰后比特数: {len(descrambled_bits)} bits")

    # 6. 源解码
    print("\n[6/6] 源解码...")
    try:
        received_text = source_decode(descrambled_bits)
        print(f"  解码文本长度: {len(received_text)} 字符")
    except Exception as e:
        print(f"  源解码错误: {e}")
        received_text = ""

    print("\n接收端处理完成!")

    return received_text, descrambled_bits, sync_index, crc_valid, payload_bits


def generate_plots(tx_symbols: np.ndarray,
                   rx_symbols: np.ndarray,
                   sync_index: int,
                   output_dir: str,
                   snr_db: float):
    """
    生成可视化图表（使用 Pillow 纯 Python 绘图）

    参数:
        tx_symbols: 发送符号
        rx_symbols: 接收符号
        sync_index: 同步索引
        output_dir: 输出目录
        snr_db: 信噪比
    """
    print("\n" + "=" * 50)
    print("生成可视化图表")
    print("=" * 50)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("警告: Pillow 未安装，跳过图表生成")
        return

    W, H = 800, 600

    # 辅助函数：映射坐标
    def map_coord(x, y, x_range, y_range, margin=60):
        px = margin + (x - x_range[0]) / (x_range[1] - x_range[0]) * (W - 2 * margin)
        py = H - margin - (y - y_range[0]) / (y_range[1] - y_range[0]) * (H - 2 * margin)
        return int(px), int(py)

    try:
        # 1. 星座图
        print("\n[1/3] 生成星座图...")
        img = Image.new('RGB', (W, H), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        x_range = (-2.0, 2.0)
        y_range = (-2.0, 2.0)

        # 网格
        for i in range(-2, 3):
            x0, y0 = map_coord(i, y_range[0], x_range, y_range, 40)
            x1, y1 = map_coord(i, y_range[1], x_range, y_range, 40)
            draw.line([(x0, 40), (x1, H - 40)], fill=(220, 220, 220), width=1)
            x0, y0 = map_coord(x_range[0], i, x_range, y_range, 40)
            x1, y1 = map_coord(x_range[1], i, x_range, y_range, 40)
            draw.line([(40, y0), (W - 40, y1)], fill=(220, 220, 220), width=1)

        # 坐标轴
        cx, _ = map_coord(0, 0, x_range, y_range, 40)
        draw.line([(40, H // 2), (W - 40, H // 2)], fill=(128, 128, 128), width=2)
        draw.line([(W // 2, 40), (W // 2, H - 40)], fill=(128, 128, 128), width=2)

        # 理想星座点
        from src.qpsk import get_constellation_points
        const = get_constellation_points()
        for pt in const:
            px, py = map_coord(pt.real, pt.imag, x_range, y_range, 40)
            draw.ellipse([(px - 8, py - 8), (px + 8, py + 8)], fill=(0, 0, 255))

        # 接收符号
        preamble_sym_len = 64 // 2
        frame_start = sync_index + preamble_sym_len
        limit = min(len(tx_symbols), len(rx_symbols) - frame_start)
        for i in range(frame_start, frame_start + min(limit, 2000)):
            s = rx_symbols[i]
            px, py = map_coord(s.real, s.imag, x_range, y_range, 40)
            if 40 <= px <= W - 40 and 40 <= py <= H - 40:
                draw.point((px, py), fill=(255, 100, 100))

        # 标签
        draw.text((20, 10), f'QPSK Constellation (SNR = {snr_db} dB)', fill=(0, 0, 0))
        draw.text((20, H - 20), 'Blue: Ideal  Red: Received', fill=(0, 0, 0))

        cpath = output_path / 'constellation.png'
        img.save(str(cpath))
        print(f"  星座图已保存: {cpath} ({cpath.stat().st_size} bytes)")

        # 2. 同步峰值图
        print("\n[2/3] 生成同步峰值图...")
        preamble_bits = generate_preamble()
        correlation, peak_idx = get_sync_peak_plot_data(rx_symbols, preamble_bits)

        img2 = Image.new('RGB', (W, H), (255, 255, 255))
        draw2 = ImageDraw.Draw(img2)

        x_r = (0, len(correlation) - 1)
        y_r = (0, max(correlation) * 1.2 if len(correlation) > 0 else 1)

        # 绘制相关曲线
        points = []
        for i in range(0, len(correlation), max(1, len(correlation) // W)):
            px, py = map_coord(i, correlation[i], x_r, y_r)
            points.append((px, py))
        if len(points) > 1:
            for i in range(len(points) - 1):
                draw2.line([points[i], points[i + 1]], fill=(0, 0, 255), width=2)

        # 峰值线
        px, _ = map_coord(peak_idx, 0, x_r, y_r)
        draw2.line([(px, 40), (px, H - 40)], fill=(255, 0, 0), width=2)

        draw2.text((20, 10), f'Sync Peak Detection (SNR = {snr_db} dB, Peak at {sync_index})', fill=(0, 0, 0))
        draw2.text((20, H - 20), 'Red line: Detected peak', fill=(0, 0, 0))

        spath = output_path / 'sync_peak.png'
        img2.save(str(spath))
        print(f"  同步峰值图已保存: {spath} ({spath.stat().st_size} bytes)")

        # 3. BER 曲线
        print("\n[3/3] 生成 BER 曲线...")
        import math

        img3 = Image.new('RGB', (W, H), (255, 255, 255))
        draw3 = ImageDraw.Draw(img3)

        # 使用纯 Python 计算理论 BER（避免 scipy 依赖）
        def q_func(x):
            """Q 函数近似"""
            return 0.5 * math.erfc(x / math.sqrt(2))

        snr_vals = np.arange(0, 21, 1)
        ber_vals = []
        for s in snr_vals:
            snr_lin = 10 ** (s / 10)
            ber_vals.append(q_func(math.sqrt(2 * snr_lin)))

        x_r_ber = (0, 20)
        y_r_ber = (1e-6, 1.0)

        points3 = []
        for s, b in zip(snr_vals, ber_vals):
            ly = max(b, 1e-6)  # clamp for log scale
            px, py = map_coord(s, math.log10(ly), x_r_ber, (math.log10(1e-6), math.log10(1.0)))
            points3.append((px, py))
            draw3.ellipse([(px - 3, py - 3), (px + 3, py + 3)], fill=(0, 0, 200))

        for i in range(len(points3) - 1):
            draw3.line([points3[i], points3[i + 1]], fill=(0, 0, 255), width=2)

        # 工作点
        if 0 <= snr_db <= 20:
            wb_snr_lin = 10 ** (snr_db / 10)
            wb = q_func(math.sqrt(2 * wb_snr_lin))
            wx, wy = map_coord(snr_db, math.log10(max(wb, 1e-6)), x_r_ber, (math.log10(1e-6), math.log10(1.0)))
            draw3.line([(wx, 40), (wx, H - 40)], fill=(255, 0, 0), width=2)

        draw3.text((20, 10), f'QPSK BER vs SNR (Working Point: {snr_db} dB)', fill=(0, 0, 0))
        draw3.text((20, H - 20), 'Red: Working point', fill=(0, 0, 0))

        bpath = output_path / 'ber_curve.png'
        img3.save(str(bpath))
        print(f"  BER 曲线已保存: {bpath} ({bpath.stat().st_size} bytes)")

        print("\n可视化图表生成完成!")

    except Exception as e:
        print(f"\n警告: 图表生成失败 ({type(e).__name__}: {e})")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    args = parse_args()

    print("=" * 60)
    print("无线通信基带仿真系统")
    print("=" * 60)
    print(f"\n输入文件: {args.input}")
    print(f"输出文件: {args.output}")
    print(f"SNR: {args.snr} dB")
    print(f"随机种子: {args.seed}")
    print(f"调制方式: {args.mod}")
    print(f"信道类型: {args.channel}")

    # 读取输入文本
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            input_text = f.read()
        print(f"\n输入文本长度: {len(input_text)} 字符")
    except FileNotFoundError:
        print(f"错误: 输入文件 '{args.input}' 不存在")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取输入文件失败 - {e}")
        sys.exit(1)

    # 发送端处理
    tx_symbols, original_bits, payload_bits = transmitter(input_text, args.seed)

    # 信道传输
    rx_symbols, actual_offset = channel(tx_symbols, args.snr, args.seed)

    # 接收端处理
    received_text, descrambled_bits, sync_index, crc_valid, received_payload = receiver(rx_symbols, args.seed, args.snr)

    # 计算性能指标
    print("\n" + "=" * 50)
    print("性能指标")
    print("=" * 50)

    # BER (基于解扰后的比特 vs 源编码比特)
    ber = calculate_ber(original_bits, descrambled_bits[:len(original_bits)])
    print(f"\nBER (误码率): {ber:.6f}")

    # 文本匹配率
    text_match_rate = calculate_text_match_rate(input_text, received_text)
    print(f"Text match rate (文本匹配率): {text_match_rate:.4f}")

    # FER (假设单帧)
    fer = 0.0 if text_match_rate == 1.0 else 1.0
    print(f"FER (误帧率): {fer:.4f}")

    print(f"CRC 校验: {'通过' if crc_valid else '失败'}")
    print(f"同步索引: {sync_index}")
    print(f"实际偏移: {actual_offset}")
    print(f"同步误差: {abs(sync_index - actual_offset)} 符号")

    # 生成 metrics.json
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metrics = generate_metrics_dict(
        snr_db=args.snr,
        seed=args.seed,
        modulation=args.mod,
        channel=args.channel,
        payload_bits=len(payload_bits),
        ber=ber,
        fer=fer,
        text_match_rate=text_match_rate,
        checksum_pass=crc_valid,
        sync_start_index=sync_index,
        additional_metrics={
            "sync_offset": actual_offset,
            "sync_error": abs(sync_index - actual_offset),
            "input_text_length": len(input_text),
            "output_text_length": len(received_text)
        }
    )

    metrics_path = output_path.parent / 'metrics.json'
    save_metrics(metrics, str(metrics_path))
    print(f"\n性能指标已保存: {metrics_path}")

    # 保存接收文本
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(received_text)
    print(f"接收文本已保存: {args.output}")

    # 生成可视化图表
    generate_plots(tx_symbols, rx_symbols, sync_index,
                   str(output_path.parent), args.snr)

    # 结果总结
    print("\n" + "=" * 60)
    print("运行结果总结")
    print("=" * 60)
    if text_match_rate == 1.0:
        print("\n[SUCCESS] 文本完全恢复!")
    else:
        print(f"\n[PARTIAL] 文本匹配率 {text_match_rate:.2%}")

    print(f"  原始文本: {input_text[:50]}...")
    print(f"  接收文本: {received_text[:50]}...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
