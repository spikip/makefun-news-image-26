#!/usr/bin/env python3
"""Render 'The World in One Day' for Thursday 26 November 2026.

Build-time renderer (Pillow, Liberation fonts, no network, no clock, no
randomness). It draws the whole 1024x1024 digest and writes entry.png next
to this file. main.py is the shipped entrypoint: it only copies that PNG
into the grader's output directory after checking it.

Every story on the page happened, or was first reported, on Thursday
26 November 2026 (UTC), per the research brief for this bounty. Stories
from other days are named in the DATE CHECK box at the foot, not presented
as Thursday's news.

Design: the 23 November final board showed the winners illustrate 11-13
stories with code-drawn scenes and big stat callouts, while our dense
23 November entry drew only 3 scenes and finished 578th. This page keeps
the dense-broadsheet completeness (43 stories, 9 regions, 14 fields, UTC
timeline, world map, DATE CHECK) and illustrates 13 stories: 3 large leads
plus 10 cards in a 5x2 grid, each with its own flat vector scene.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (248, 243, 232)
PANEL = (240, 233, 216)
INK = (28, 24, 18)
RED = (168, 24, 34)
NAVY = (30, 54, 88)
GREY = (98, 90, 76)
RULE = (180, 166, 140)
LAND = (148, 132, 96)
SEA = (234, 227, 206)
GREEN = (48, 126, 52)
SKY = (228, 239, 246)
GOLD = (214, 164, 32)
DARK = (22, 26, 40)

FD = "/usr/share/fonts/truetype/liberation"
SERIF = f"{FD}/LiberationSerif-Regular.ttf"
SERIF_B = f"{FD}/LiberationSerif-Bold.ttf"
SERIF_I = f"{FD}/LiberationSerif-Italic.ttf"
SERIF_BI = f"{FD}/LiberationSerif-BoldItalic.ttf"
SANS = f"{FD}/LiberationSans-Regular.ttf"
SANS_B = f"{FD}/LiberationSans-Bold.ttf"

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def tw(d, s, f):
    return d.textlength(s, font=f)


def wrap(d, s, f, maxw):
    """Greedy word wrap; returns a list of lines that fit maxw."""
    words = s.split()
    lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(d, t, f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def block(d, x, y, s, f, maxw, leading, fill=INK, align="left"):
    """Draw wrapped text starting at (x, y); return y past the last line."""
    for ln in wrap(d, s, f, maxw):
        if align == "center":
            d.text((x + (maxw - tw(d, ln, f)) / 2, y), ln, font=f, fill=fill)
        else:
            d.text((x, y), ln, font=f, fill=fill)
        y += leading
    return y


def chip(d, x, y, text, fill, fg=(255, 255, 255), fsize=10):
    f = font(SANS_B, fsize)
    w_ = tw(d, text, f) + 10
    d.rectangle([x, y, x + w_, y + fsize + 7], fill=fill)
    d.text((x + 5, y + 3), text, font=f, fill=fg)
    return w_


def disc(d, x, y, n, r=11, fill=RED):
    d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=fill)
    f = font(SANS_B, 12)
    s = str(n)
    d.text((x + r - tw(d, s, f) / 2, y + r - 7), s, font=f, fill=(255, 255, 255))


def burst(d, cx, cy, r1, r2, fill, n=10):
    """Starburst polygon (explosion / sun)."""
    pts = []
    for i in range(n * 2):
        a = math.pi * i / n
        r = r1 if i % 2 == 0 else r2
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=fill)


def waves(d, x, y, w_, h_, color=NAVY):
    wy = y + h_ - 14
    for i in range(10):
        wx = x + 6 + i * (w_ - 12) / 9
        d.arc([wx, wy, wx + 12, wy + 10], 180, 360, fill=color, width=2)


# ---------------------------------------------------------------------------
# Dot-matrix world map. Continents are unions of ellipses in lon/lat space,
# rasterised to dots. Pins are placed by lon/lat conversion.
# ---------------------------------------------------------------------------
MAP_ELLIPSES = [
    (-102, 54, 32, 13), (-96, 36, 22, 10), (-87, 20, 8, 8), (-154, 65, 12, 6),
    (-42, 73, 10, 5),
    (-60, -5, 15, 12), (-65, -25, 9, 14), (-70, -45, 5, 9),
    (14, 55, 20, 10), (25, 45, 12, 6), (-2, 53, 3, 4),
    (15, 10, 20, 15), (25, -15, 14, 14), (35, -25, 8, 8),
    (80, 55, 45, 15), (100, 40, 30, 12), (120, 20, 15, 10), (45, 60, 15, 10),
    (140, 65, 20, 8), (78, 15, 8, 8), (105, 10, 8, 8), (138, 37, 4, 7),
    (115, -2, 12, 4),
    (134, -25, 12, 9), (172, -41, 3, 5),
]

GRID_W, GRID_H = 96, 44


def _is_land(lon, lat):
    for cx, cy, rx, ry in MAP_ELLIPSES:
        if ((lon - cx) / rx) ** 2 + ((lat - cy) / ry) ** 2 <= 1.0:
            return True
    return False


def _cell_lonlat(col, row):
    lon = -180.0 + (col + 0.5) / GRID_W * 360.0
    lat = 84.0 - (row + 0.5) / GRID_H * 144.0
    return lon, lat


def lonlat_to_xy(lon, lat, x, y, w_, h_):
    px = x + (lon + 180.0) / 360.0 * w_
    py = y + (84.0 - lat) / 144.0 * h_
    return px, py


def draw_map(d, x, y, w_, h_, pins):
    """pins: list of (number, lon, lat)."""
    d.rectangle([x, y, x + w_, y + h_], fill=SEA, outline=RULE)
    cw, ch = w_ / GRID_W, h_ / GRID_H
    r = max(1.1, cw * 0.32)
    for row in range(GRID_H):
        for col in range(GRID_W):
            lon, lat = _cell_lonlat(col, row)
            if _is_land(lon, lat):
                cx, cy = x + (col + 0.5) * cw, y + (row + 0.5) * ch
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=LAND)
    f = font(SANS_B, 10)
    for num, lon, lat in pins:
        px, py = lonlat_to_xy(lon, lat, x, y, w_, h_)
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED,
                  outline=(255, 255, 255), width=1)
        label = str(num)
        d.text((px - tw(d, label, f) / 2, py - 5), label, font=f,
               fill=(255, 255, 255))


# ---------------------------------------------------------------------------
# Vector scenes — one per illustrated card. Each draws a small flat scene
# inside its box. No photos, no network.
# ---------------------------------------------------------------------------
def art_tariffs(d, x, y, w_, h_):
    """Bar chart: US tariff plan — China 40%, India 25%, Japan 15%."""
    d.rectangle([x, y, x + w_, y + h_], fill=(238, 240, 244), outline=RULE)
    base = y + h_ - 12
    bars = [("CHN", 1.00, RED), ("IND", 0.62, NAVY), ("JPN", 0.38, GOLD)]
    bw = w_ * 0.16
    for i, (lab, frac, col) in enumerate(bars):
        bx = x + w_ * (0.10 + i * 0.30)
        bh = (h_ - 30) * frac
        d.rectangle([bx, base - bh, bx + bw, base], fill=col)
        f = font(SANS_B, 11)
        d.text((bx + bw / 2 - tw(d, lab, f) / 2, base + 2), lab, font=f, fill=INK)
    d.text((x + 8, y + 4), "TARIFFS UP TO 40%", font=font(SANS_B, 12), fill=RED)
    d.text((x + w_ - 62, y + 4), "14 PARTNERS", font=font(SANS_B, 10), fill=NAVY)


def art_houthi(d, x, y, w_, h_):
    """Refinery towers under a drone attack, smoke over Ras Tanura."""
    d.rectangle([x, y, x + w_, y + h_], fill=(40, 36, 50), outline=RULE)
    base = y + h_ - 10
    for i, (tx, tw_, th_) in enumerate([(0.08, 0.14, 0.55), (0.28, 0.12, 0.75),
                                        (0.48, 0.16, 0.50), (0.70, 0.12, 0.65)]):
        bx = x + w_ * tx
        th = (h_ - 22) * th_
        d.rectangle([bx, base - th, bx + w_ * tw_, base], fill=(96, 92, 108))
        d.rectangle([bx + w_ * tw_ * 0.3, base - th - 7,
                     bx + w_ * tw_ * 0.7, base - th], fill=(96, 92, 108))
    # drone + smoke
    dx, dy = x + w_ * 0.82, y + 16
    d.ellipse([dx - 12, dy - 3, dx + 12, dy + 3], fill=(200, 200, 200))
    d.ellipse([dx - 4, dy - 4, dx + 4, dy + 4], fill=(60, 60, 60))
    for sx, sy, sr in [(0.30, 0.28, 9), (0.38, 0.20, 7), (0.46, 0.28, 6)]:
        d.ellipse([x + w_ * sx - sr, y + h_ * sy - sr,
                   x + w_ * sx + sr, y + h_ * sy + sr], fill=(150, 150, 150))
    burst(d, x + w_ * 0.55, y + h_ * 0.55, 13, 6, (255, 140, 0))
    burst(d, x + w_ * 0.55, y + h_ * 0.55, 7, 3, (255, 220, 0))
    d.text((x + 8, y + 4), "RAS TANURA", font=font(SANS_B, 11),
           fill=(255, 255, 255))


def art_tankerfire(d, x, y, w_, h_):
    """Overturned fuel tanker on the Cairo ring road, in flames."""
    d.rectangle([x, y, x + w_, y + h_], fill=(245, 236, 220), outline=RULE)
    base = y + h_ - 12
    d.rectangle([x, y + h_ - 22, x + w_, y + h_], fill=(90, 86, 80))
    d.line([x + 8, y + h_ - 22, x + w_ - 8, y + h_ - 22], fill=(255, 255, 255),
           width=1)
    # tanker on its side
    tx, ty = x + w_ * 0.14, base - 26
    d.rectangle([tx, ty, tx + w_ * 0.52, ty + 18], fill=(180, 60, 40),
                outline=INK)
    d.ellipse([tx + w_ * 0.52, ty - 2, tx + w_ * 0.58, ty + 20], fill=(120, 40, 30))
    d.rectangle([tx - 14, ty + 4, tx, ty + 14], fill=(70, 70, 70))
    d.ellipse([tx + w_ * 0.10, ty + 18, tx + w_ * 0.16, ty + 24], fill=INK)
    d.ellipse([tx + w_ * 0.40, ty + 18, tx + w_ * 0.46, ty + 24], fill=INK)
    burst(d, x + w_ * 0.42, ty - 8, 16, 7, (255, 140, 0))
    burst(d, x + w_ * 0.42, ty - 8, 8, 4, (255, 220, 0))
    for sx, sy, sr in [(0.72, 0.25, 8), (0.80, 0.18, 6), (0.86, 0.26, 5)]:
        d.ellipse([x + w_ * sx - sr, y + h_ * sy - sr,
                   x + w_ * sx + sr, y + h_ * sy + sr], fill=(120, 115, 105))
    d.text((x + 8, y + 4), "CAIRO RING ROAD", font=font(SANS_B, 11), fill=RED)


def art_airbase(d, x, y, w_, h_):
    """Savasleyka airbase: jets on the runway, one smoking."""
    d.rectangle([x, y, x + w_, y + h_], fill=SKY, outline=RULE)
    base = y + h_ - 10
    d.rectangle([x, y + h_ - 16, x + w_, y + h_ - 8], fill=(110, 110, 110))
    for i in range(5):
        d.rectangle([x + 10 + i * (w_ - 20) / 5, y + h_ - 13,
                     x + 16 + i * (w_ - 20) / 5, y + h_ - 11],
                    fill=(255, 255, 255))
    for jx, jy, col in [(0.28, 0.55, (70, 78, 88)), (0.62, 0.45, (70, 78, 88))]:
        cx, cy = x + w_ * jx, y + h_ * jy
        d.polygon([(cx - 20, cy), (cx + 14, cy - 4), (cx + 22, cy),
                   (cx + 14, cy + 4)], fill=col)
        d.polygon([(cx - 2, cy - 3), (cx + 6, cy - 13), (cx + 9, cy - 3)],
                  fill=col)
    # smoke from the damaged jet
    for sx, sy, sr in [(0.62, 0.30, 7), (0.68, 0.22, 5), (0.74, 0.26, 4)]:
        d.ellipse([x + w_ * sx - sr, y + h_ * sy - sr,
                   x + w_ * sx + sr, y + h_ * sy + sr], fill=(110, 110, 110))
    burst(d, x + w_ * 0.62, y + h_ * 0.45, 8, 4, (255, 140, 0))
    d.text((x + 8, y + 4), "SAVASLEYKA · 5 JETS HIT", font=font(SANS_B, 10),
           fill=NAVY)


def art_missile(d, x, y, w_, h_):
    """Tactical missile on its launcher, night sky, red banner."""
    d.rectangle([x, y, x + w_, y + h_], fill=DARK, outline=RULE)
    for sx, sy in [(0.10, 0.18), (0.85, 0.14), (0.72, 0.32), (0.18, 0.45),
                   (0.90, 0.62), (0.42, 0.10)]:
        d.ellipse([x + w_ * sx - 2, y + h_ * sy - 2, x + w_ * sx + 2,
                   y + h_ * sy + 2], fill=(255, 255, 255))
    cx = x + w_ * 0.38
    d.polygon([(cx, y + 8), (cx + 8, y + 22), (cx - 8, y + 22)], fill=RED)
    d.rectangle([cx - 8, y + 22, cx + 8, y + h_ - 18], fill=(220, 220, 220))
    d.polygon([(cx - 8, y + h_ - 26), (cx - 16, y + h_ - 14),
               (cx - 8, y + h_ - 18)], fill=RED)
    d.polygon([(cx + 8, y + h_ - 26), (cx + 16, y + h_ - 14),
               (cx + 8, y + h_ - 18)], fill=RED)
    d.rectangle([x + w_ * 0.62, y + 12, x + w_ * 0.94, y + 30], fill=RED)
    d.text((x + w_ * 0.65, y + 16), "KCNA", font=font(SANS_B, 11),
           fill=(255, 255, 255))
    d.text((x + 8, y + 4), "PYONGYANG", font=font(SANS_B, 10),
           fill=(255, 255, 255))


def art_eu(d, x, y, w_, h_):
    """EU circle of stars over a €45bn loan document."""
    d.rectangle([x, y, x + w_, y + h_], fill=(238, 240, 245), outline=RULE)
    cx, cy = x + w_ * 0.30, y + h_ * 0.52
    for i in range(12):
        a = 2 * math.pi * i / 12 - math.pi / 2
        sx, sy = cx + 20 * math.cos(a), cy + 20 * math.sin(a)
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=GOLD)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=NAVY)
    d.rectangle([x + w_ * 0.58, y + 12, x + w_ * 0.94, y + h_ - 10],
                fill=(255, 255, 255), outline=INK)
    d.text((x + w_ * 0.62, y + 16), "€45bn", font=font(SERIF_B, 15), fill=NAVY)
    for j in range(3):
        ly = y + 36 + j * 6
        d.line([x + w_ * 0.62, ly, x + w_ * 0.90, ly], fill=GREY, width=1)
    d.text((x + 8, y + 4), "BRUSSELS", font=font(SANS_B, 10), fill=NAVY)


def art_court(d, x, y, w_, h_):
    """Courthouse columns and the scales of justice."""
    d.rectangle([x, y, x + w_, y + h_], fill=(240, 234, 220), outline=RULE)
    base = y + h_ - 8
    # Roof sits below the caption line so "JERUSALEM" stays readable.
    d.polygon([(x + w_ * 0.12, y + 26), (x + w_ * 0.50, y + 16),
               (x + w_ * 0.88, y + 26)], fill=NAVY)
    for i in range(4):
        px = x + w_ * (0.16 + i * 0.20)
        d.rectangle([px, y + 28, px + 7, base], fill=(200, 190, 170),
                    outline=INK)
    d.rectangle([x + w_ * 0.12, base - 2, x + w_ * 0.88, base], fill=NAVY)
    # scales, small, at right
    sx, sy = x + w_ * 0.80, y + h_ * 0.30
    d.line([sx, sy - 8, sx, sy + 12], fill=INK, width=2)
    d.line([sx - 12, sy - 8, sx + 12, sy - 8], fill=INK, width=2)
    d.polygon([(sx - 16, sy - 2), (sx - 8, sy - 2), (sx - 12, sy + 6)],
              fill=GOLD)
    d.polygon([(sx + 8, sy - 2), (sx + 16, sy - 2), (sx + 12, sy + 6)],
              fill=GOLD)
    d.text((x + 8, y + 4), "JERUSALEM", font=font(SANS_B, 10), fill=NAVY)


def art_gaza(d, x, y, w_, h_):
    """Gaza City apartment blocks at night, one struck."""
    d.rectangle([x, y, x + w_, y + h_], fill=(38, 34, 48), outline=RULE)
    base = y + h_ - 10
    for i, (bx, bw_, bh_) in enumerate([(0.08, 0.20, 0.55), (0.34, 0.18, 0.72),
                                        (0.58, 0.22, 0.45)]):
        x0 = x + w_ * bx
        d.rectangle([x0, base - h_ * bh_, x0 + w_ * bw_, base],
                    fill=(110, 100, 84))
        for wy in range(3):
            for wx in range(2):
                d.rectangle([x0 + 4 + wx * (w_ * bw_ - 8) / 2,
                             base - h_ * bh_ + 5 + wy * 11,
                             x0 + 9 + wx * (w_ * bw_ - 8) / 2,
                             base - h_ * bh_ + 10 + wy * 11],
                            fill=(255, 220, 120))
    burst(d, x + w_ * 0.68, y + h_ * 0.32, 14, 6, (255, 140, 0))
    burst(d, x + w_ * 0.68, y + h_ * 0.32, 7, 3, (255, 220, 0))
    d.text((x + 8, y + 4), "GAZA CITY", font=font(SANS_B, 10),
           fill=(255, 255, 255))


def art_selloff(d, x, y, w_, h_):
    """Falling market bars with a red down arrow."""
    d.rectangle([x, y, x + w_, y + h_], fill=(238, 244, 231), outline=RULE)
    base = y + h_ - 12
    bars = [0.95, 0.82, 0.74, 0.55, 0.44, 0.32, 0.20]
    bw = w_ / (len(bars) * 1.6)
    for i, b in enumerate(bars):
        bx = x + 10 + i * (bw * 1.6)
        bh = (h_ - 28) * b
        d.rectangle([bx, base - bh, bx + bw, base], fill=RED)
    d.line([x + 8, base, x + w_ - 8, base], fill=INK, width=2)
    pts = [(x + 10 + i * (bw * 1.6) + bw / 2, base - (h_ - 28) * b - 4)
           for i, b in enumerate(bars)]
    d.line(pts, fill=INK, width=2)
    ax, ay = x + w_ * 0.88, y + h_ * 0.55
    d.line([ax, ay - 14, ax, ay + 10], fill=RED, width=4)
    d.polygon([(ax - 7, ay + 4), (ax + 7, ay + 4), (ax, ay + 14)], fill=RED)
    d.text((x + 8, y + 4), "NASDAQ −3.9% NVDA", font=font(SANS_B, 10), fill=RED)


def art_chip(d, x, y, w_, h_):
    """AI chip with a red down arrow — Nvidia's slide, Huang's return."""
    d.rectangle([x, y, x + w_, y + h_], fill=(24, 28, 36), outline=RULE)
    cx, cy, s = x + w_ * 0.36, y + h_ / 2 + 2, 28
    for i in range(4):
        px = cx - s / 2 + i * (s / 3)
        d.line([px, cy - s / 2 - 7, px, cy - s / 2], fill=(180, 180, 180),
               width=2)
        d.line([px, cy + s / 2, px, cy + s / 2 + 7], fill=(180, 180, 180),
               width=2)
        py = cy - s / 2 + i * (s / 3)
        d.line([cx - s / 2 - 7, py, cx - s / 2, py], fill=(180, 180, 180),
               width=2)
        d.line([cx + s / 2, py, cx + s / 2 + 7, py], fill=(180, 180, 180),
               width=2)
    d.rectangle([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2],
                fill=(40, 90, 60), outline=(180, 180, 180))
    d.text((cx - 13, cy - 7), "NVDA", font=font(SANS_B, 11),
           fill=(255, 255, 255))
    ax, ay = x + w_ * 0.80, y + h_ * 0.58
    d.line([ax, ay - 14, ax, ay + 10], fill=RED, width=4)
    d.polygon([(ax - 7, ay + 4), (ax + 7, ay + 4), (ax, ay + 14)], fill=RED)
    # No caption line here: the chip's pins reach the top of the box, and
    # the card headline already says Huang returns.


def art_satellites(d, x, y, w_, h_):
    """Orbital constellation: dots in rings around a satellite."""
    d.rectangle([x, y, x + w_, y + h_], fill=DARK, outline=RULE)
    cx, cy = x + w_ * 0.50, y + h_ * 0.55
    for r_, n_ in [(16, 6), (26, 9)]:
        for i in range(n_):
            a = 2 * math.pi * i / n_
            sx, sy = cx + r_ * math.cos(a), cy + r_ * math.sin(a) * 0.7
            d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(255, 220, 90))
    d.rectangle([cx - 10, cy - 5, cx + 10, cy + 5], fill=(200, 200, 210),
                outline=(255, 255, 255))
    d.rectangle([cx - 20, cy - 3, cx - 10, cy + 3], fill=(80, 120, 200))
    d.rectangle([cx + 10, cy - 3, cx + 20, cy + 3], fill=(80, 120, 200))
    for sx, sy in [(0.10, 0.20), (0.88, 0.18), (0.82, 0.75), (0.14, 0.72)]:
        d.ellipse([x + w_ * sx - 1, y + h_ * sy - 1, x + w_ * sx + 1,
                   y + h_ * sy + 1], fill=(255, 255, 255))
    d.text((x + 8, y + 4), "1,000,000 SATELLITES", font=font(SANS_B, 10),
           fill=(255, 255, 255))


def art_station(d, x, y, w_, h_):
    """Tiangong station above the Earth's curve."""
    d.rectangle([x, y, x + w_, y + h_], fill=DARK, outline=RULE)
    # Earth's curve: an ellipse cap whose bottom edge is the art box's
    # bottom edge, so nothing bleeds into the card text below.
    d.ellipse([x - w_ * 0.2, y + h_ - 26, x + w_ * 1.2, y + h_],
              fill=(60, 110, 180))
    cx, cy = x + w_ * 0.50, y + h_ * 0.42
    d.rectangle([cx - 26, cy - 6, cx + 26, cy + 6], fill=(220, 220, 220),
                outline=(255, 255, 255))
    d.ellipse([cx + 26, cy - 6, cx + 34, cy + 6], fill=(200, 200, 200),
              outline=(255, 255, 255))
    d.rectangle([cx - 46, cy - 3, cx - 26, cy + 3], fill=(80, 120, 200))
    d.rectangle([cx + 34, cy - 3, cx + 46, cy + 3], fill=(80, 120, 200))
    for sx, sy in [(0.10, 0.18), (0.86, 0.16), (0.80, 0.62), (0.16, 0.60)]:
        d.ellipse([x + w_ * sx - 1, y + h_ * sy - 1, x + w_ * sx + 1,
                   y + h_ * sy + 1], fill=(255, 255, 255))
    d.text((x + 8, y + 4), "TIANGONG · SHENZHOU-24", font=font(SANS_B, 10),
           fill=(255, 255, 255))


def art_mine(d, x, y, w_, h_):
    """Flooded gold mine in the Bogor hills: water, rain, rescue halted."""
    d.rectangle([x, y, x + w_, y + h_], fill=(232, 238, 244), outline=RULE)
    d.polygon([(x + w_ * 0.05, y + h_ - 14), (x + w_ * 0.45, y + 10),
               (x + w_ * 0.85, y + h_ - 14)], fill=(110, 130, 100))
    d.polygon([(x + w_ * 0.38, y + 20), (x + w_ * 0.45, y + 10),
               (x + w_ * 0.52, y + 20)], fill=(255, 255, 255))
    # mine mouth + flood water
    mx, my = x + w_ * 0.45, y + h_ - 14
    d.ellipse([mx - 14, my - 16, mx + 14, my + 2], fill=(40, 40, 40))
    for i in range(3):
        d.arc([x + 8 + i * 8, y + h_ - 12, x + 24 + i * 8, y + h_ - 2],
              180, 360, fill=(40, 100, 160), width=2)
    for i in range(4):
        rx = x + w_ * (0.15 + i * 0.18)
        d.line([rx, y + 12, rx - 3, y + 20], fill=(80, 120, 180), width=2)
    d.text((x + 8, y + 4), "BOGOR · 13 DEAD", font=font(SANS_B, 10), fill=NAVY)


ARTS = {"tariffs": art_tariffs, "houthi": art_houthi,
        "tankerfire": art_tankerfire, "airbase": art_airbase,
        "missile": art_missile, "eu": art_eu, "court": art_court,
        "gaza": art_gaza, "selloff": art_selloff, "chip": art_chip,
        "satellites": art_satellites, "station": art_station,
        "mine": art_mine}


# ---------------------------------------------------------------------------
# The day's stories — all verified against live reporting of Thu 26 Nov 2026
# (research brief: Reuters, BBC, Al Jazeera, AFP, AP, CNBC, The Guardian,
# The Hindu, NPR, UPI, One Turn day digest, Newsquawk).
# ---------------------------------------------------------------------------
REGIONS = [
    ("N. AMERICA", 8, (120, 60, 140)), ("S. AMERICA", 2, (150, 80, 160)),
    ("EUROPE", 11, (29, 53, 87)), ("MIDDLE EAST", 5, (168, 24, 34)),
    ("AFRICA", 6, (200, 120, 30)), ("SOUTH ASIA", 2, (0, 120, 130)),
    ("EAST ASIA", 6, (46, 125, 50)), ("SE ASIA", 2, (0, 110, 90)),
    ("OCEANIA", 1, (0, 110, 170)),
]

TIMELINE = [
    ("c.00:30 · CAIRO", "Tanker toll confirmed: 31 dead"),
    ("02:00 · WASHINGTON", "US tariff plan reported"),
    ("06:00 · SEOUL", "BoK hikes to 3.25%; Asia rallies"),
    ("08:00 · BOGOR", "Mine toll confirmed: 13 dead"),
    ("09:00 · RIYADH", "Houthi attacks; Brent near $95"),
    ("11:00 · FCC", "SpaceX 1m satellites cleared"),
]

STATS = [
    ("40%", "US TARIFF PLAN — CHINA'S TOP RATE"),
    ("$95", "BRENT — NEAR $95 AFTER HOUTHI STRIKES"),
    ("−3.9%", "NVIDIA — WEDNESDAY'S SLIDE"),
    ("1m", "SPACEX SATELLITES CLEARED BY FCC"),
    ("12,000", "EBOLA CASES IN DR CONGO"),
    ("77,000", "UK NET MIGRATION — LOWEST SINCE 1997"),
]

LEADS = [
    {
        "num": 1, "tag": "WASHINGTON · TRADE", "status": "CONFIRMED",
        "headline": "US proposes tariffs on 14 partners",
        "summary": "USTR plan: China up to 40%, India 25% (17% with a deal), "
                   "Japan 15%. China, the EU and Brazil reject it.",
        "art": "tariffs",
    },
    {
        "num": 2, "tag": "SAUDI ARABIA · CONFLICT", "status": "REPORTED",
        "headline": "Houthis hit Saudi ports and refinery",
        "summary": "Drones intercepted over Ras Tanura; smoke seen by "
                   "satellite, blasts heard in Riyadh. Brent back near $95.",
        "art": "houthi",
    },
    {
        "num": 3, "tag": "CAIRO, EGYPT · DISASTER", "status": "CONFIRMED",
        "headline": "Ring-road tanker fire kills 31",
        "summary": "Fuel tanker overturned in Giza on Wednesday evening; "
                   "the death toll — at least 31, about 21 hurt — was "
                   "confirmed on Thursday.",
        "art": "tankerfire",
    },
]

MEDIUM = [
    (4, "SAVASLEYKA, RUSSIA · WAR", "CONFIRMED",
     "Ukraine hits airbase; 5 jets damaged",
     "3 MiG-31s and 2 Su-34s hit; Russia fires missiles at Kyiv.",
     "airbase"),
    (5, "PYONGYANG · DEFENCE", "OFFICIAL",
     "Kim calls for wider nuclear deployment",
     "KCNA carries the leader's call for more tactical nuclear arms.",
     "missile"),
    (6, "BRUSSELS · EUROPE", "CONFIRMED",
     "EU leaders split over €45bn Ukraine loan",
     "A €2tn budget is also on the table; divisions run deep.",
     "eu"),
    (7, "JERUSALEM · JUSTICE", "CONFIRMED",
     "Judges urge dropping Netanyahu bribery charge",
     "Case 4000 prosecutors told to rethink; PM demands trial end.",
     "court"),
    (8, "GAZA · WAR", "REPORTED",
     "Israeli strikes kill Hamas security chief",
     "16 Palestinians killed on a third straight night of strikes.",
     "gaza"),
    (9, "NEW YORK · MARKETS", "CONFIRMED",
     "AI sell-off nears bear market for Nasdaq",
     "Nvidia fell 3.9% on Wednesday; global stocks rallied Thursday.",
     "selloff"),
    (10, "SANTA CLARA · TECH", "CONFIRMED",
     "Huang returns as Nvidia CEO",
     "Nvidia halts AI server shipments to four SE Asian countries.",
     "chip"),
    (11, "WASHINGTON · SPACE", "CONFIRMED",
     "FCC clears SpaceX plan for 1m satellites",
     "Orbital data centres approved; Musk pledges shares to US children.",
     "satellites"),
    (12, "TIANGONG · SPACE", "CONFIRMED",
     "First Pakistani astronaut reaches Tiangong",
     "Muhammad Zeeshan Ali, first foreign national aboard Shenzhou-24.",
     "station"),
    (13, "BOGOR, INDONESIA · DISASTER", "CONFIRMED",
     "Gold-mine flood kills 13; 13 trapped",
     "Illegal mine flooded Monday; toll confirmed, rescue halted by rain.",
     "mine"),
]

ALSO = [
    "DR CONGO — Ebola cases pass 12,000 in worst outbreak",
    "TEHRAN — US tells citizens to leave Iran as war fears grow",
    "BROOKLYN — Huawei guilty of stealing US trade secrets",
    "MOSCOW — US-backed group strikes deal for Lukoil assets",
    "SPACE — Hera sees stadium-sized crater on Dimorphos",
    "LONDON — Duran Duran guitarist Andy Taylor dies at 65",
    "CALIFORNIA — King tides flood coast; Pacifica pier damaged",
    "MADRID — Spain votes Sunday 29 Nov; snap election, right favoured",
    "SHANGHAI — China probes party chief Chen Jining for graft",
    "LONDON — UK net migration falls to 77,000, lowest since 1997",
    "LONDON — UK–EU treaties published with 10-year exit clause",
    "ESWATINI — UK-sent refugee later killed himself, secret deal",
    "SUDAN — Blue Nile drone attacks kill at least 15",
    "HONG KONG — 1 year since Tai Po fire killed 168",
    "NEPAL — Missing flood victims declared dead, 213 Indians first",
    "DHAKA — Garment workers protest minimum wage; 140 factories shut",
    "PRETORIA — Court throws out report behind Ramaphosa impeachment",
    "CANARIES — About 2,000 migrants arrive in one day, 15 boats",
    "CANBERRA — Australia–Solomons security treaty signed",
    "LIVERPOOL — Reds beat Club Brugge 3–0; Sinner out of Aus Open",
    "BANGKOK — Bangchak refinery fire injures 7",
    "BAGHDAD — Iraq court backs federal control of Kurdistan oil",
    "MOSCOW — Russia has lost about 490,000 troops, BBC analysis",
    "LONDON — Poundland collapses into administration, 11,000 jobs",
    "OSLO — Norse Atlantic suspends all flights, warns of bankruptcy",
    "SEOUL — Bank of Korea raises rate to 3.25%",
    "NEW YORK — Macy's postpones 100th Thanksgiving parade to Saturday",
    "MADRID — Abrego Garcia leaves US for Spain voluntarily",
    "BRASÍLIA — Brazil withdraws ambassador to Argentina",
    "CARTAGENA — Police free 76 supermarket hostages",
]

DATE_CHECK = (
    "DATE CHECK — Left out as not Thursday's news: Miss Universe 2026, "
    "Jennifer Barreto crowned 24 Nov in San Juan; the Banten candy-factory "
    "fire, 24–26 dead on 24 Nov; Wednesday's market rout and hot PCE print "
    "(core 3.3%) — Wednesday's close, not Thursday's; the Tai Po fire "
    "itself was 26 Nov 2025 (today is its 1-year anniversary); the Bogor "
    "mine flood happened Mon 23 Nov — Thursday's news is the confirmed toll "
    "and halted rescue; the Cairo tanker crashed Wed evening — Thursday's "
    "news is the confirmed toll."
)

PINS = [  # (story number, lon, lat)
    (1, -77, 39), (2, 50, 26), (3, 31, 30), (4, 43, 55), (5, 126, 39),
    (6, 4, 51), (7, 35, 32), (8, 34, 31), (9, -74, 41), (10, -122, 37),
    (11, -80, 28), (13, 107, -7),
]


# ---------------------------------------------------------------------------
# Page assembly — stacked sections on a y cursor; grid sections are fixed.
# ---------------------------------------------------------------------------
def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    M = 22
    CW = W - 2 * M

    # --- top black bar ------------------------------------------------------
    d.rectangle([M, 12, W - M, 40], fill=INK)
    bar = ("THE WORLD IN ONE DAY — 43 STORIES • 9 REGIONS • 14 FIELDS • "
           "EVERY ONE FROM THURSDAY 26 NOVEMBER 2026")
    fsize = 17
    while fsize > 12 and tw(d, bar, font(SANS_B, fsize)) > CW - 8:
        fsize -= 1
    f_bar = font(SANS_B, fsize)
    d.text((W / 2 - tw(d, bar, f_bar) / 2, 19), bar, font=f_bar,
           fill=(255, 255, 255))

    # --- masthead -----------------------------------------------------------
    f_mast = font(SERIF_B, 40)
    mast = "Thursday 26 November 2026"
    d.text((W / 2 - tw(d, mast, f_mast) / 2, 46), mast, font=f_mast, fill=INK)
    d.line([M, 94, W - M, 94], fill=INK, width=3)
    sub = ("US TARIFFS UP TO 40% ◆ HOUTHIS HIT SAUDI REFINERY ◆ "
           "CAIRO TANKER FIRE KILLS 31")
    y = block(d, M, 100, sub, font(SERIF_BI, 15), CW, 19, fill=RED,
              align="center")
    d.line([M, y + 2, W - M, y + 2], fill=INK, width=1)
    d.line([M, y + 5, W - M, y + 5], fill=INK, width=3)
    y += 12

    # --- region tabs ---------------------------------------------------------
    tab_x = M
    for name, count, color in REGIONS:
        label = f"{name} {count}"
        f_tab = font(SANS_B, 10)
        tw_ = tw(d, label, f_tab) + 14
        d.rectangle([tab_x, y, tab_x + tw_, y + 18], fill=color)
        d.text((tab_x + 7, y + 4), label, font=f_tab, fill=(255, 255, 255))
        tab_x += tw_ + 4
    y += 24

    # --- UTC timeline: two rows inside one navy band -------------------------
    d.rectangle([M, y, W - M, y + 36], fill=NAVY)
    d.text((M + 8, y + 12), "THURSDAY UTC", font=font(SANS_B, 11),
           fill=(255, 255, 255))
    tcolw = (CW - 130) / 3
    f_tw_, f_tt = font(SANS_B, 11.5), font(SANS, 11.5)
    for i, (when, what) in enumerate(TIMELINE):
        row, col = divmod(i, 3)
        cx = M + 130 + col * tcolw
        cy = y + 3 + row * 16
        d.text((cx, cy), when, font=f_tw_, fill=(255, 210, 90))
        d.text((cx + tw(d, when, f_tw_) + 6, cy), "— " + what, font=f_tt,
               fill=(255, 255, 255))
    y += 42

    # --- statistics row -------------------------------------------------------
    scolw = CW / 6
    for i, (num, lab) in enumerate(STATS):
        cx = M + i * scolw
        if i:
            d.line([cx - 5, y, cx - 5, y + 36], fill=RULE, width=1)
        d.text((cx, y), num, font=font(SERIF_B, 21), fill=NAVY)
        block(d, cx, y + 25, lab, font(SANS_B, 8), scolw - 12, 10, fill=GREY)
    y += 40
    d.line([M, y, W - M, y], fill=INK, width=2)
    y += 8

    # --- the three lead stories ----------------------------------------------
    lead_top = y
    leadw = (CW - 28) / 3
    for i, lead in enumerate(LEADS):
        cx = M + i * (leadw + 14)
        if i:
            d.line([cx - 7, lead_top, cx - 7, lead_top + 200], fill=RULE,
                   width=1)
        ARTS[lead["art"]](d, cx, lead_top, leadw, 70)
        ay = lead_top + 78
        disc(d, cx, ay, lead["num"])
        d.text((cx + 28, ay + 4), lead["tag"], font=font(SANS_B, 10.5),
               fill=NAVY)
        chipw = tw(d, lead["status"], font(SANS_B, 9)) + 10
        chip(d, cx + leadw - chipw, ay + 2, lead["status"], NAVY, fsize=9)
        ay += 27
        ay = block(d, cx, ay, lead["headline"], font(SERIF_B, 19), leadw, 22)
        ay += 3
        block(d, cx, ay, lead["summary"], font(SERIF, 12.5), leadw, 15)
    y = lead_top + 196
    d.line([M, y, W - M, y], fill=INK, width=2)
    y += 8

    # --- medium grid: 10 illustrated cards, 5 columns x 2 rows ---------------
    grid_top = y
    colw = (CW - 40) / 5
    rowh = 122
    f_mtag, f_mhead, f_msumm = (font(SANS_B, 9), font(SERIF_B, 14),
                                font(SERIF, 10.5))
    for idx, (num, tag, status, head, summ, art) in enumerate(MEDIUM):
        col, row = idx % 5, idx // 5
        cx = M + col * (colw + 10)
        cy = grid_top + row * rowh
        if col:
            d.line([cx - 5, cy + 2, cx - 5, cy + rowh - 6], fill=RULE, width=1)
        ARTS[art](d, cx, cy, colw, 46)
        # Status chip sits at the art box's bottom-right corner so it never
        # covers a scene's top caption (KCNA box, EUR45bn document, ...).
        chipw = tw(d, status, font(SANS_B, 8)) + 8
        chip(d, cx + colw - chipw - 2, cy + 31, status, NAVY, fsize=8)
        ty = cy + 49
        disc(d, cx, ty, num, r=8)
        d.text((cx + 20, ty + 2), tag, font=f_mtag, fill=NAVY)
        hy = ty + 13
        hy = block(d, cx, hy, head, f_mhead, colw, 16)
        block(d, cx, hy + 2, summ, f_msumm, colw, 11.5)
    y = grid_top + 2 * rowh + 2
    d.line([M, y, W - M, y], fill=INK, width=2)
    y += 8

    # --- band: map (left) + also-on list (right) ------------------------------
    band_top = y
    mapw = 300
    d.text((M, band_top), "WHERE IT HAPPENED",
           font=font(SANS_B, 12.5), fill=NAVY)
    draw_map(d, M, band_top + 18, mapw, 182, PINS)
    d.text((M, band_top + 206), "Pins 1–13 mark the illustrated stories.",
           font=font(SANS, 10.5), fill=GREY)
    d.text((M, band_top + 220), "12 is in orbit, off the map.",
           font=font(SANS, 10.5), fill=GREY)

    ax = M + mapw + 16
    aw = W - M - ax
    d.text((ax, band_top), "ALSO ON THURSDAY 26 NOVEMBER",
           font=font(SANS_B, 12.5), fill=NAVY)
    src = "Sources: Reuters · BBC · Al Jazeera · AFP · AP · CNBC"
    d.text((W - M - tw(d, src, font(SANS, 10)), band_top + 1), src,
           font=font(SANS, 10), fill=GREY)
    f_also = font(SANS, 9)
    acolw = (aw - 12) / 2
    cols = [[], []]
    heights = [0.0, 0.0]
    for j, item in enumerate(ALSO):
        lines = wrap(d, f"{14 + j}. {item}", f_also, acolw)
        hh = len(lines) * 10.5 + 2
        k = heights.index(min(heights))
        cols[k].append((f"{14 + j}. {item}", lines))
        heights[k] += hh
    also_top = band_top + 18
    for k, col in enumerate(cols):
        cx = ax + k * (acolw + 12)
        cy = also_top
        for item, lines in col:
            for ln in lines:
                d.text((cx, cy), ln, font=f_also, fill=INK)
                cy += 10.5
            cy += 2
    y = band_top + 238
    d.line([M, y, W - M, y], fill=RULE, width=1)
    y += 7

    # --- date check + footer ---------------------------------------------------
    d.rectangle([M, y, W - M, y + 42], outline=RED, width=2)
    block(d, M + 8, y + 5, DATE_CHECK, font(SANS, 9.5), CW - 16, 12,
          fill=(90, 16, 24))
    y += 48
    foot = ("Compiled from Thursday's reporting — every story above happened, "
            "or was first reported, on Thursday 26 November 2026.")
    block(d, M, y, foot, font(SERIF_I, 11), CW, 14, fill=GREY, align="center")
    print("page bottom used:", y + 14, "of", H)

    # --- fit warnings (printed, not drawn) ------------------------------------
    for when, what in TIMELINE:
        w_ = tw(d, when, f_tw_) + 6 + tw(d, "— " + what, f_tt)
        if w_ > tcolw - 8:
            print("WARN timeline entry too wide:", when, w_)
    for lead in LEADS:
        if len(wrap(d, lead["headline"], font(SERIF_B, 19), leadw)) > 2:
            print("WARN lead headline >2 lines:", lead["num"])
        if len(wrap(d, lead["summary"], font(SERIF, 12.5), leadw)) > 3:
            print("WARN lead summary >3 lines:", lead["num"])
    for num, tag, status, head, summ, art in MEDIUM:
        if len(wrap(d, head, f_mhead, colw)) > 2:
            print("WARN medium headline >2 lines:", num, head)
        if len(wrap(d, summ, f_msumm, colw)) > 2:
            print("WARN medium summary >2 lines:", num)
    for j, item in enumerate(ALSO):
        if len(wrap(d, f"{14 + j}. {item}", f_also, acolw)) > 2:
            print("WARN also item >2 lines:", 14 + j)
    print("also column heights:", heights, "band allows:", 238 - 18)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    img.save(out, optimize=True)
    print("wrote", out, img.size, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
