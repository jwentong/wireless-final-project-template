"""Visualization: constellation, BER curve, sync peak."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from src.channel import awgn
from src.receiver import run_receiver
from src.transmitter import run_transmitter


def _get_plt():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except ImportError:
        return None


def _get_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont

        return Image, ImageDraw, ImageFont
    except ImportError:
        return None


def _draw_axes(draw, margin, width, height, xlabel="", ylabel="", title=""):
    """Draw simple axes box and labels using Pillow."""
    draw.rectangle(
        [margin, margin, width - margin, height - margin],
        outline=(0, 0, 0),
        width=1,
    )
    if title:
        draw.text((margin, 8), title, fill=(0, 0, 0))
    if xlabel:
        draw.text((width // 2 - 40, height - margin + 8), xlabel, fill=(0, 0, 0))
    if ylabel:
        draw.text((8, margin), ylabel, fill=(0, 0, 0))


def _map_linear(x, y, xmin, xmax, ymin, ymax, margin, width, height):
    inner_w = width - 2 * margin
    inner_h = height - 2 * margin
    px = margin + (x - xmin) / (xmax - xmin) * inner_w if xmax != xmin else margin + inner_w / 2
    py = height - margin - (y - ymin) / (ymax - ymin) * inner_h if ymax != ymin else height - margin - inner_h / 2
    return px, py


def _plot_constellation_pillow(rx_symbols: np.ndarray, path: Path) -> None:
    Image, ImageDraw, _ = _get_pillow()
    width, height, margin = 640, 640, 60
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    _draw_axes(draw, margin, width, height, xlabel="I", ylabel="Q", title="QPSK Constellation")

    pts = np.asarray(rx_symbols, dtype=complex)
    if len(pts) > 4000:
        idx = np.linspace(0, len(pts) - 1, 4000, dtype=int)
        pts = pts[idx]

    xmin = xmax = ymin = ymax = None
    for sym in pts:
        for coord in (sym.real, sym.imag):
            pass
    lim = 1.5
    xmin, xmax, ymin, ymax = -lim, lim, -lim, lim

    for sym in pts:
        px, py = _map_linear(sym.real, sym.imag, xmin, xmax, ymin, ymax, margin, width, height)
        draw.ellipse([px - 1, py - 1, px + 1, py + 1], fill=(70, 130, 220))

    ideal = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]) / np.sqrt(2)
    for sym in ideal:
        px, py = _map_linear(sym.real, sym.imag, xmin, xmax, ymin, ymax, margin, width, height)
        draw.line([px - 6, py - 6, px + 6, py + 6], fill=(220, 50, 50), width=2)
        draw.line([px - 6, py + 6, px + 6, py - 6], fill=(220, 50, 50), width=2)

    draw.text((margin, height - 24), "Blue: received  Red X: ideal QPSK", fill=(80, 80, 80))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def _plot_sync_peak_pillow(correlation: np.ndarray, peak_index: int, path: Path) -> None:
    Image, ImageDraw, _ = _get_pillow()
    width, height, margin = 800, 420, 60
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    _draw_axes(
        draw,
        margin,
        width,
        height,
        xlabel="Symbol index",
        ylabel="|Correlation|",
        title="Preamble Sync Correlation Peak",
    )

    corr = np.asarray(correlation, dtype=float)
    if len(corr) == 0:
        draw.text((margin + 10, margin + 10), "No correlation data", fill=(0, 0, 0))
        img.save(path)
        return

    xs = np.arange(len(corr))
    ymin, ymax = 0.0, float(np.max(corr)) * 1.05 or 1.0
    points = [_map_linear(float(x), float(y), 0, max(len(corr) - 1, 1), ymin, ymax, margin, width, height) for x, y in zip(xs, corr)]
    draw.line(points, fill=(50, 90, 180), width=2)

    if 0 <= peak_index < len(corr):
        px, _ = _map_linear(float(peak_index), ymin, 0, max(len(corr) - 1, 1), ymin, ymax, margin, width, height)
        draw.line([px, margin, px, height - margin], fill=(220, 50, 50), width=2)
        draw.text((px + 4, margin + 4), f"Peak @ {peak_index}", fill=(220, 50, 50))

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def _plot_ber_curve_pillow(
    snr_points: list[int],
    bers: list[float],
    tmrs: list[float],
    path: Path,
    channel_name: str = "awgn",
) -> None:
    Image, ImageDraw, _ = _get_pillow()
    width, height, margin = 800, 420, 60
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    _draw_axes(
        draw,
        margin,
        width,
        height,
        xlabel="SNR (dB)",
        ylabel="BER (log)",
        title=f"BER / Text Match vs SNR ({channel_name})",
    )

    x_min, x_max = min(snr_points), max(snr_points)
    log_bers = [math.log10(max(b, 1e-6)) for b in bers]
    y_min, y_max = min(log_bers + [-6.0]), max(log_bers + [0.0])

    ber_pts = [
        _map_linear(float(x), float(y), x_min, x_max, y_min, y_max, margin, width, height)
        for x, y in zip(snr_points, log_bers)
    ]
    draw.line(ber_pts, fill=(50, 90, 180), width=2)
    for px, py in ber_pts:
        draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(50, 90, 180))

    tmr_pts = [
        _map_linear(float(x), float(t), x_min, x_max, 0.0, 1.0, margin, width, height)
        for x, t in zip(snr_points, tmrs)
    ]
    draw.line(tmr_pts, fill=(40, 160, 80), width=2)
    for px, py in tmr_pts:
        draw.rectangle([px - 3, py - 3, px + 3, py + 3], outline=(40, 160, 80))

    draw.text((margin, height - 24), "Blue: BER (log)   Green: text_match_rate", fill=(80, 80, 80))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def plot_constellation(rx_symbols: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt = _get_plt()
    if plt is not None:
        fig, ax = plt.subplots(figsize=(6, 6))
        pts = np.asarray(rx_symbols, dtype=complex)
        if len(pts) > 8000:
            pts = pts[np.linspace(0, len(pts) - 1, 8000, dtype=int)]
        ax.scatter(pts.real, pts.imag, s=4, alpha=0.35, label="Received")
        ideal = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]) / np.sqrt(2)
        ax.scatter(ideal.real, ideal.imag, s=120, marker="x", c="red", label="Ideal QPSK")
        ax.set_xlabel("I")
        ax.set_ylabel("Q")
        ax.set_title("QPSK Constellation")
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.axis("equal")
        fig.tight_layout()
        fig.savefig(path, dpi=120)
        plt.close(fig)
        return
    if _get_pillow() is not None:
        _plot_constellation_pillow(rx_symbols, path)
        return
    raise RuntimeError("Install matplotlib or pillow to generate plots.")


def plot_sync_peak(correlation: np.ndarray, peak_index: int, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt = _get_plt()
    if plt is not None:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(correlation, linewidth=1.0)
        if len(correlation) > peak_index:
            ax.axvline(peak_index, color="red", linestyle="--", label=f"Peak @ {peak_index}")
        ax.set_xlabel("Symbol index")
        ax.set_ylabel("|Correlation|")
        ax.set_title("Preamble Sync Correlation Peak")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(path, dpi=120)
        plt.close(fig)
        return
    if _get_pillow() is not None:
        _plot_sync_peak_pillow(correlation, peak_index, path)
        return
    raise RuntimeError("Install matplotlib or pillow to generate plots.")


def plot_ber_curve(
    text: str,
    seed: int,
    path: Path,
    channel_fn=awgn,
    channel_name: str = "awgn",
    fec: str = "repeat",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    snr_points = list(range(0, 16, 2))
    bers, tmrs = _sweep_ber_tmr(text, seed, snr_points, fec=fec, channel_name=channel_name)

    plt = _get_plt()
    if plt is not None:
        fig, ax1 = plt.subplots(figsize=(8, 4))
        ax1.semilogy(snr_points, [max(b, 1e-6) for b in bers], "o-", label="BER")
        ax1.set_xlabel("SNR (dB)")
        ax1.set_ylabel("BER")
        ax1.grid(True, which="both", alpha=0.3)
        ax2 = ax1.twinx()
        ax2.plot(snr_points, tmrs, "s--", color="green", label="text_match_rate")
        ax2.set_ylabel("Text match rate")
        ax2.set_ylim(-0.05, 1.05)
        ax1.set_title(f"BER / Text Match vs SNR ({channel_name}, {fec})")
        fig.tight_layout()
        fig.savefig(path, dpi=120)
        plt.close(fig)
        return
    if _get_pillow() is not None:
        _plot_ber_curve_pillow(snr_points, bers, tmrs, path, f"{channel_name}/{fec}")
        return
    raise RuntimeError("Install matplotlib or pillow to generate plots.")


def _sweep_ber_tmr(
    text: str,
    seed: int,
    snr_points: list[int],
    *,
    fec: str = "repeat",
    channel_name: str = "awgn",
) -> tuple[list[float], list[float]]:
    bers: list[float] = []
    tmrs: list[float] = []
    tx_symbols, meta = run_transmitter(text, seed=seed, fec=fec)
    preamble_symbols = meta["preamble_symbols"]

    for snr in snr_points:
        if channel_name == "rayleigh":
            from src.channel import rayleigh

            rx, _ = rayleigh(tx_symbols, snr_db=float(snr), seed=seed + snr * 100)
        else:
            rx = awgn(tx_symbols, snr_db=float(snr), seed=seed + snr * 100)
        _, partial = run_receiver(
            rx,
            seed=seed,
            preamble_symbols=preamble_symbols,
            original_text=text,
            fec=fec,
        )
        bers.append(float(partial["ber"]))
        tmrs.append(float(partial["text_match_rate"]))
    return bers, tmrs


def plot_fec_compare_ber_curve(text: str, seed: int, path: Path) -> None:
    """Compare repeat vs conv on AWGN and repeat on Rayleigh (Level 3)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    snr_points = list(range(0, 16, 2))
    curves = [
        ("repeat + AWGN", _sweep_ber_tmr(text, seed, snr_points, fec="repeat", channel_name="awgn")[0], (50, 90, 180)),
        ("conv + AWGN", _sweep_ber_tmr(text, seed, snr_points, fec="conv", channel_name="awgn")[0], (220, 120, 40)),
        ("repeat + Rayleigh", _sweep_ber_tmr(text, seed, snr_points, fec="repeat", channel_name="rayleigh")[0], (40, 160, 80)),
    ]

    plt = _get_plt()
    if plt is not None:
        fig, ax = plt.subplots(figsize=(8, 4))
        for label, bers, color in curves:
            rgb = tuple(c / 255.0 for c in color)
            ax.semilogy(snr_points, [max(b, 1e-6) for b in bers], "o-", label=label, color=rgb)
        ax.set_xlabel("SNR (dB)")
        ax.set_ylabel("BER")
        ax.set_title("FEC / Channel Comparison (Level 3)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(path, dpi=120)
        plt.close(fig)
        return

    if _get_pillow() is not None:
        Image, ImageDraw, _ = _get_pillow()
        width, height, margin = 800, 420, 60
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        _draw_axes(
            draw,
            margin,
            width,
            height,
            xlabel="SNR (dB)",
            ylabel="BER (log)",
            title="FEC / Channel Comparison (Level 3)",
        )
        x_min, x_max = min(snr_points), max(snr_points)
        all_log = [math.log10(max(b, 1e-6)) for _, bers, _ in curves for b in bers]
        y_min, y_max = min(all_log + [-6.0]), max(all_log + [0.0])
        for label, bers, color in curves:
            log_bers = [math.log10(max(b, 1e-6)) for b in bers]
            pts = [
                _map_linear(float(x), float(y), x_min, x_max, y_min, y_max, margin, width, height)
                for x, y in zip(snr_points, log_bers)
            ]
            draw.line(pts, fill=color, width=2)
        draw.text((margin, height - 24), "Blue: repeat+AWGN  Orange: conv+AWGN  Green: repeat+Rayleigh", fill=(80, 80, 80))
        img.save(path)
        return
    raise RuntimeError("Install matplotlib or pillow to generate plots.")


def generate_all_plots(
    text: str,
    seed: int,
    snr_db: float,
    results_dir: Path,
    rx_symbols: np.ndarray,
    sync_correlation: np.ndarray,
    sync_start_index: int,
    channel_name: str = "awgn",
    fec: str = "repeat",
) -> None:
    plot_constellation(rx_symbols, results_dir / "constellation.png")
    plot_sync_peak(sync_correlation, sync_start_index, results_dir / "sync_peak.png")
    plot_ber_curve(text, seed, results_dir / "ber_curve.png", channel_name=channel_name, fec=fec)
    plot_fec_compare_ber_curve(text, seed, results_dir / "ber_curve_fec_compare.png")
