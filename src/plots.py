import math
import struct
import zlib
from pathlib import Path


Color = tuple[int, int, int]


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png(path: str | Path, width: int, height: int, pixels: list[Color]) -> None:
    rows = []
    for y in range(height):
        start = y * width
        raw = bytearray([0])
        for r, g, b in pixels[start : start + width]:
            raw.extend([r, g, b])
        rows.append(bytes(raw))
    data = zlib.compress(b"".join(rows), level=9)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    content = b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", header) + _png_chunk(b"IDAT", data) + _png_chunk(b"IEND", b"")
    Path(path).write_bytes(content)


def _canvas(width: int = 640, height: int = 420) -> tuple[int, int, list[Color]]:
    return width, height, [(255, 255, 255)] * (width * height)


def _set(pixels: list[Color], width: int, height: int, x: int, y: int, color: Color) -> None:
    if 0 <= x < width and 0 <= y < height:
        pixels[y * width + x] = color


def _line(pixels: list[Color], width: int, height: int, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        _set(pixels, width, height, x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _dot(pixels: list[Color], width: int, height: int, x: int, y: int, color: Color, radius: int = 2) -> None:
    for yy in range(y - radius, y + radius + 1):
        for xx in range(x - radius, x + radius + 1):
            if (xx - x) ** 2 + (yy - y) ** 2 <= radius ** 2:
                _set(pixels, width, height, xx, yy, color)


def constellation(path: str | Path, symbols: list[complex]) -> None:
    width, height, pixels = _canvas()
    left, right, top, bottom = 60, width - 40, 30, height - 50
    midx = (left + right) // 2
    midy = (top + bottom) // 2
    _line(pixels, width, height, left, midy, right, midy, (210, 210, 210))
    _line(pixels, width, height, midx, top, midx, bottom, (210, 210, 210))
    limit = max(1.5, max((abs(s.real) for s in symbols[:2000]), default=1.0), max((abs(s.imag) for s in symbols[:2000]), default=1.0))
    for symbol in symbols[:2000]:
        x = int(midx + symbol.real / limit * (right - left) / 2)
        y = int(midy - symbol.imag / limit * (bottom - top) / 2)
        _dot(pixels, width, height, x, y, (30, 96, 180), 2)
    write_png(path, width, height, pixels)


def line_plot(path: str | Path, xs: list[float], ys: list[float], log_y: bool = False) -> None:
    width, height, pixels = _canvas()
    left, right, top, bottom = 60, width - 40, 30, height - 50
    _line(pixels, width, height, left, bottom, right, bottom, (50, 50, 50))
    _line(pixels, width, height, left, top, left, bottom, (50, 50, 50))
    if not xs or not ys:
        write_png(path, width, height, pixels)
        return
    plot_ys = [math.log10(max(y, 1e-6)) if log_y else y for y in ys]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(plot_ys), max(plot_ys)
    if xmin == xmax:
        xmax = xmin + 1
    if ymin == ymax:
        ymax = ymin + 1
    points = []
    for x, y in zip(xs, plot_ys):
        px = int(left + (x - xmin) / (xmax - xmin) * (right - left))
        py = int(bottom - (y - ymin) / (ymax - ymin) * (bottom - top))
        points.append((px, py))
    for a, b in zip(points, points[1:]):
        _line(pixels, width, height, a[0], a[1], b[0], b[1], (190, 55, 45))
    for px, py in points:
        _dot(pixels, width, height, px, py, (190, 55, 45), 3)
    write_png(path, width, height, pixels)
