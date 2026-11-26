#!/usr/bin/env python3
"""Draw Thursday 26 November 2026's world news as one dense 1024x1024 page.

Written from scratch for the make.fun bounty news-image-20261126. The page
is built from three data tables (FEATURES, ALSO_ON, TIMELINE) plus a set of
small hand-drawn vector scenes, one per illustrated card. Pillow only, no
network, no clock, no randomness, so every run writes identical bytes.

Run:  python3 render.py            (writes entry.png next to this file)
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "entry.png")

PAGE_W, PAGE_H = 1024, 1024
MARGIN = 8
INK = (26, 26, 26)
PAPER = (247, 243, 232)
RULE = (26, 26, 26)
RED = (178, 34, 34)
NAVY = (16, 42, 78)
SKY = (214, 230, 240)
PALE = (238, 236, 224)

FONT_DIR = "/usr/share/fonts/truetype/liberation"
SERIF = os.path.join(FONT_DIR, "LiberationSerif-Regular.ttf")
SERIF_B = os.path.join(FONT_DIR, "LiberationSerif-Bold.ttf")
SANS = os.path.join(FONT_DIR, "LiberationSans-Regular.ttf")
SANS_B = os.path.join(FONT_DIR, "LiberationSans-Bold.ttf")
SANS_I = os.path.join(FONT_DIR, "LiberationSans-Italic.ttf")
SANS_BI = os.path.join(FONT_DIR, "LiberationSans-BoldItalic.ttf")

_cache = {}


def fnt(size, bold=False, serif=False, italic=False):
    """Cached font loader: bold+italic picks the bold-italic face."""
    key = (size, bold, serif, italic)
    if key not in _cache:
        if serif:
            path = SERIF_B if bold else SERIF
        elif bold and italic:
            path = SANS_BI
        elif bold:
            path = SANS_B
        elif italic:
            path = SANS_I
        else:
            path = SANS
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def text_w(draw, text, font):
    return draw.textlength(text, font=font)


def wrap_lines(draw, text, font, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if text_w(draw, trial, font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_para(draw, text, font, max_w, max_lines, x, y, fill, leading=None):
    """Draw wrapped text, clipped to max_lines; returns y after last line."""
    if leading is None:
        leading = int(font.size * 1.18)
    lines = wrap_lines(draw, text, font, max_w)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        # Trim the last line so the ellipsis still fits.
        while lines and text_w(draw, lines[-1] + "...", font) > max_w:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1] + "..."
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += leading
    return y


def centre(draw, cx, y, text, font, fill):
    draw.text((cx - text_w(draw, text, font) / 2, y), text, font=font, fill=fill)


def pill(draw, x, y, label, font, fg, bg):
    """Small rounded status label; returns the x just past it."""
    pad = 5
    w = int(text_w(draw, label, font)) + pad * 2
    h = font.size + 6
    draw.rounded_rectangle([x, y, x + w, y + h], radius=3, fill=bg)
    draw.text((x + pad, y + 3), label, font=font, fill=fg)
    return x + w


STATUS_FILL = {
    "CONFIRMED": (31, 78, 121),
    "OFFICIAL": (20, 83, 45),
    "REPORTED": (146, 64, 14),
    "CLAIM": (153, 27, 27),
}

# ---------------------------------------------------------------- data
# Every story happened, or was first reported, on Thu 26 Nov 2026 (UTC).
# `region` drives the tab counts; `scene` picks the vector illustration.
FEATURES = [
    dict(n=1, place="WASHINGTON", field="TRADE", region="N. AMERICA",
         status="CONFIRMED", scene="tariff",
         headline="US proposes tariffs on 14 partners",
         deck="USTR plan: China up to 40%, India 25% (17% with a trade "
              "deal), Japan 15%. China, the EU and Brazil reject it.",
         big="40%"),
    dict(n=2, place="SAUDI ARABIA", field="CONFLICT", region="MIDDLE EAST",
         status="REPORTED", scene="refinery",
         headline="Houthis hit Saudi ports and refinery",
         deck="Drones intercepted over Ras Tanura; smoke seen by satellite, "
              "blasts heard in Riyadh. Brent back near $95.",
         big="BRENT $95"),
    dict(n=3, place="CAIRO, EGYPT", field="DISASTER", region="AFRICA",
         status="CONFIRMED", scene="tanker",
         headline="Ring-road tanker fire kills 31",
         deck="Fuel tanker overturned in Giza on Wednesday evening; the "
              "death toll - at least 31, about 21 hurt - was confirmed "
              "on Thursday.",
         big="31 KILLED"),
    dict(n=4, place="SAVASLEYKA, RUSSIA", field="WAR", region="EUROPE",
         status="CONFIRMED", scene="airbase",
         headline="Ukraine hits airbase; 5 jets damaged",
         deck="3 MiG-31s and 2 Su-34s hit; Russia fires missiles at Kyiv.",
         big="5 JETS"),
    dict(n=5, place="PYONGYANG", field="DEFENCE", region="EAST ASIA",
         status="OFFICIAL", scene="missile",
         headline="Kim calls for wider nuclear deployment",
         deck="KCNA carries the leader's call for more tactical nuclear arms.",
         big="KCNA"),
    dict(n=6, place="BRUSSELS", field="EUROPE", region="EUROPE",
         status="CONFIRMED", scene="eu",
         headline="EU leaders split over \u20ac45bn Ukraine loan",
         deck="A \u20ac2tn budget is also on the table; divisions run deep.",
         big="\u20ac45bn"),
    dict(n=7, place="JERUSALEM", field="JUSTICE", region="MIDDLE EAST",
         status="CONFIRMED", scene="court",
         headline="Judges urge dropping Netanyahu bribery charge",
         deck="Case 4000 prosecutors told to rethink; PM demands trial end.",
         big="CASE 4000"),
    dict(n=8, place="GAZA CITY", field="WAR", region="MIDDLE EAST",
         status="REPORTED", scene="gaza",
         headline="Israeli strikes kill Hamas security chief",
         deck="16 Palestinians killed on a third straight night of strikes.",
         big="16 KILLED"),
    dict(n=9, place="NEW YORK", field="MARKETS", region="N. AMERICA",
         status="CONFIRMED", scene="market",
         headline="AI sell-off nears bear market for Nasdaq",
         deck="Nvidia fell 3.9% on Wednesday; global stocks rallied Thursday.",
         big="NASDAQ -3.9%"),
    dict(n=10, place="SANTA CLARA", field="TECH", region="N. AMERICA",
         status="CONFIRMED", scene="chip",
         headline="Huang returns as Nvidia CEO",
         deck="Nvidia halts AI server shipments to four SE Asian countries.",
         big="NVDA"),
    dict(n=11, place="WASHINGTON", field="SPACE", region="N. AMERICA",
         status="CONFIRMED", scene="satellites",
         headline="FCC clears SpaceX plan for 1m satellites",
         deck="Orbital data centres approved; Musk pledges shares to US children.",
         big="1,000,000"),
    dict(n=12, place="TIANGONG", field="SPACE", region="EAST ASIA",
         status="CONFIRMED", scene="station",
         headline="First Pakistani astronaut reaches Tiangong",
         deck="Muhammad Zeeshan Ali, first foreign national aboard Shenzhou-24.",
         big="SHENZHOU-24"),
    dict(n=13, place="BOGOR, INDONESIA", field="DISASTER",
         region="SE ASIA", status="CONFIRMED", scene="mine",
         headline="Gold-mine flood kills 13; 13 trapped",
         deck="Illegal mine flooded Monday; toll confirmed, rescue halted by rain.",
         big="13 DEAD"),
]

# The remaining 30 stories, one short line each (kept under ~64 chars so
# each fits a single line of the two-column list at 10pt).
ALSO_ON = [
    "DR CONGO - Ebola cases pass 12,000 in worst outbreak",
    "TEHRAN - US tells citizens to leave Iran as war fears grow",
    "BROOKLYN - Huawei guilty of stealing US trade secrets",
    "MOSCOW - US-backed group strikes deal for Lukoil assets",
    "SPACE - Hera sees stadium-sized crater on Dimorphos",
    "LONDON - Duran Duran guitarist Andy Taylor dies at 65",
    "CALIFORNIA - King tides flood coast; Pacifica pier damaged",
    "MADRID - Spain votes Sunday 29 Nov; snap vote, right favoured",
    "SHANGHAI - China probes party chief Chen Jining for graft",
    "LONDON - UK net migration falls to 77,000, lowest since 1997",
    "LONDON - UK-EU treaties published with 10-year exit clause",
    "ESWATINI - UK-sent refugee later killed himself",
    "SUDAN - Blue Nile drone attacks kill at least 15",
    "HONG KONG - 1 year since Tai Po fire killed 168",
    "NEPAL - Missing flood victims declared dead; 213 Indians first",
    "DHAKA - Garment workers protest pay; 140 factories shut",
    "PRETORIA - Court scraps Ramaphosa impeachment report",
    "CANARIES - About 2,000 migrants arrive in one day; 15 boats",
    "CANBERRA - Australia-Solomons security treaty signed",
    "LIVERPOOL - Reds beat Club Brugge 3-0; Sinner out of Aus Open",
    "BANGKOK - Bangchak refinery fire injures 7",
    "BAGHDAD - Iraq court backs federal control of Kurdistan oil",
    "MOSCOW - Russia has lost about 490,000 troops, BBC analysis",
    "LONDON - Poundland collapses into administration, 11,000 jobs",
    "OSLO - Norse Atlantic suspends all flights, warns of bankruptcy",
    "SEOUL - Bank of Korea raises rate to 3.25%",
    "NEW YORK - Macy's postpones 100th Thanksgiving parade",
    "MADRID - Abrego Garcia leaves US for Spain voluntarily",
    "BRASILIA - Brazil withdraws ambassador to Argentina",
    "CARTAGENA - Police free 76 supermarket hostages",
]

TIMELINE = [
    ("c.00:30", "CAIRO", "Tanker toll confirmed: 31 dead"),
    ("02:00", "WASHINGTON", "US tariff plan reported"),
    ("06:00", "SEOUL", "BoK hikes to 3.25%; Asia rallies"),
    ("08:00", "BOGOR", "Mine toll confirmed: 13 dead"),
    ("09:00", "RIYADH", "Houthi attacks; Brent near $95"),
    ("11:00", "FCC", "SpaceX 1m satellites cleared"),
]

STATS = [
    ("40%", "US TARIFF PLAN - CHINA 40%"),
    ("$95", "BRENT - NEAR $95 AFTER STRIKES"),
    ("-3.9%", "NVIDIA - WEDNESDAY'S SLIDE"),
    ("1m", "SPACEX SATELLITES CLEARED"),
    ("12,000", "EBOLA CASES IN DR CONGO"),
    ("77,000", "UK NET MIGRATION - SINCE 1997"),
]

REGION_ORDER = ["N. AMERICA", "S. AMERICA", "EUROPE", "MIDDLE EAST",
                "AFRICA", "SOUTH ASIA", "EAST ASIA", "SE ASIA", "OCEANIA"]
REGION_FILL = {
    "N. AMERICA": (31, 78, 121), "S. AMERICA": (128, 34, 34),
    "EUROPE": (20, 83, 45), "MIDDLE EAST": (146, 64, 14),
    "AFRICA": (120, 53, 15), "SOUTH ASIA": (107, 33, 168),
    "EAST ASIA": (178, 34, 34), "SE ASIA": (13, 115, 119),
    "OCEANIA": (120, 53, 15),
}

DATE_CHECK = (
    "DATE CHECK - Left out as not Thursday's news: Miss Universe 2026, "
    "Jennifer Barreto crowned 24 Nov in San Juan; the Banten candy-factory "
    "fire, 24-26 dead on 24 Nov; Wednesday's market rout and hot PCE print "
    "(core PCE 3.3%) - Wednesday's close, not Thursday's; the Tai Po fire "
    "itself was 26 Nov 2025 (today is its 1-year anniversary); the Bogor "
    "mine flood happened Mon 23 Nov - Thursday's news is the confirmed toll "
    "and halted rescue; the Cairo tanker crashed Wed evening - Thursday's "
    "news is the confirmed toll."
)

SOURCES = ("Sources: Reuters - BBC - Al Jazeera - AFP - AP - CNBC - "
           "The Guardian - The Hindu - NPR - UPI - One Turn day digest - "
           "Newsquawk")

# ------------------------------------------------------- scene painters
# Each painter draws one flat vector scene inside the box (x, y, w, h).
# All shapes are axis-aligned rectangles, ellipses, polygons and lines,
# so the output is fully deterministic.

def burst(draw, cx, cy, r, colour):
    """A starburst: 8 triangles fanning out from the centre."""
    import math
    outer, inner = [], []
    for k in range(16):
        ang = math.pi * k / 8
        rad = r if k % 2 == 0 else r * 0.45
        outer.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(outer, fill=colour)
    draw.ellipse([cx - r * 0.28, cy - r * 0.28,
                  cx + r * 0.28, cy + r * 0.28], fill=(255, 255, 255))


def smoke(draw, cx, cy, r, colour=(150, 150, 150)):
    """Three overlapping grey puffs, rising to the upper right."""
    for dx, dy, rr in ((0, 0, r), (r * 0.9, -r * 0.7, r * 0.75),
                       (r * 1.8, -r * 1.3, r * 0.55)):
        draw.ellipse([cx + dx - rr, cy + dy - rr,
                      cx + dx + rr, cy + dy + rr], fill=colour)


def scene_tariff(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(232, 238, 244))
    draw.rectangle([x, y, x + w, y + 16], fill=RED)
    draw.text((x + 4, y + 2), "TARIFFS UP TO 40%",
              font=fnt(11, bold=True), fill=(255, 255, 255))
    draw.text((x + w - 4 - text_w(draw, "14 PARTNERS", fnt(11, bold=True)),
               y + 2), "14 PARTNERS", font=fnt(11, bold=True),
              fill=(255, 255, 255))
    base = y + h - 16
    bars = [("CHN", 0.78, (178, 34, 34)), ("IND", 0.45, (31, 78, 121)),
            ("JPN", 0.28, (212, 160, 23))]
    slot = w / 3
    for i, (tag, frac, col) in enumerate(bars):
        bx = x + slot * i + slot * 0.22
        bw = slot * 0.56
        bh = (h - 38) * frac
        draw.rectangle([bx, base - bh, bx + bw, base], fill=col)
        pct = {0: "40%", 1: "25%", 2: "15%"}[i]
        centre(draw, bx + bw / 2, base - bh - 13, pct,
               fnt(11, bold=True), INK)
        centre(draw, bx + bw / 2, base + 2, tag, fnt(9, bold=True), INK)
    draw.line([x, base, x + w, base], fill=INK, width=1)


def scene_refinery(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(24, 28, 44))
    # Moon and stars.
    draw.ellipse([x + w - 26, y + 6, x + w - 12, y + 20], fill=(240, 230, 180))
    for sx, sy in ((0.15, 0.2), (0.4, 0.12), (0.7, 0.25), (0.9, 0.45)):
        draw.ellipse([x + w * sx - 1, y + h * sy - 1,
                      x + w * sx + 1, y + h * sy + 1], fill=(255, 255, 255))
    ground = y + h - 14
    draw.rectangle([x, ground, x + w, y + h], fill=(12, 14, 24))
    # Tanks, towers and a flare stack, left to right.
    draw.rectangle([x + 8, ground - 26, x + 44, ground], fill=(74, 82, 104))
    draw.ellipse([x + 8, ground - 32, x + 44, ground - 24], fill=(94, 102, 124))
    draw.rectangle([x + 52, ground - 40, x + 62, ground], fill=(58, 64, 84))
    draw.rectangle([x + 52, ground - 46, x + 62, ground - 40], fill=(58, 64, 84))
    draw.rectangle([x + 70, ground - 20, x + 108, ground], fill=(74, 82, 104))
    draw.ellipse([x + 70, ground - 25, x + 108, ground - 17], fill=(94, 102, 124))
    draw.rectangle([x + w - 34, ground - 48, x + w - 26, ground], fill=(58, 64, 84))
    draw.rectangle([x + w - 52, ground - 30, x + w - 40, ground], fill=(74, 82, 104))
    burst(draw, x + w * 0.62, ground - 34, 13, (255, 176, 32))
    burst(draw, x + w * 0.38, ground - 52, 9, (255, 120, 40))
    smoke(draw, x + w * 0.62, ground - 52, 7, (120, 120, 120))
    draw.text((x + 6, y + 4), "RAS TANURA", font=fnt(11, bold=True),
              fill=(255, 255, 255))


def scene_tanker(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(240, 234, 214))
    draw.rectangle([x, y, x + w, y + h * 0.42], fill=(196, 220, 236))
    draw.ellipse([x + w - 34, y + 8, x + w - 14, y + 28], fill=(250, 220, 130))
    road = y + h * 0.62
    draw.rectangle([x, road, x + w, y + h], fill=(96, 96, 96))
    draw.line([x, road + 8, x + w, road + 8], fill=(255, 255, 255), width=2)
    # Overturned tanker: long red tank, tilted cab, spilled wheels.
    tx, ty = x + w * 0.12, road - 26
    draw.rectangle([tx, ty, tx + w * 0.62, ty + 22], fill=(178, 34, 34))
    draw.ellipse([tx + w * 0.62 - 4, ty, tx + w * 0.62 + 12, ty + 22],
                 fill=(140, 20, 20))
    draw.polygon([(tx + w * 0.66, ty + 4), (tx + w * 0.78, ty - 6),
                  (tx + w * 0.86, ty + 18), (tx + w * 0.68, ty + 22)],
                 fill=(120, 20, 20))
    for wx in (0.22, 0.42, 0.58):
        draw.ellipse([x + w * wx - 6, road - 7, x + w * wx + 6, road + 5],
                     fill=(20, 20, 20))
    burst(draw, x + w * 0.78, ty - 8, 14, (255, 176, 32))
    smoke(draw, x + w * 0.80, ty - 22, 8)
    draw.text((x + 6, y + 4), "CAIRO RING ROAD",
              font=fnt(11, bold=True), fill=(120, 40, 40))


def scene_airbase(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(196, 220, 236))
    draw.rectangle([x, y, x + w, y + 12], fill=(255, 255, 255))
    draw.text((x + 6, y + 1), "SAVASLEYKA",
              font=fnt(10, bold=True), fill=(31, 78, 121))
    draw.text((x + w - 6 - text_w(draw, "5 JETS", fnt(10, bold=True)), y + 1),
              "5 JETS", font=fnt(10, bold=True), fill=RED)
    # Runway sweeping diagonally down to the right.
    draw.polygon([(x, y + h * 0.75), (x + w, y + h * 0.45),
                  (x + w, y + h * 0.62), (x, y + h * 0.92)],
                 fill=(110, 110, 110))
    # Three parked jets (fuselage + swept wings) on the apron.
    for jx, jy, s in ((0.18, 0.42, 1.0), (0.45, 0.30, 0.85), (0.68, 0.52, 0.9)):
        cx, cy = x + w * jx, y + h * jy
        draw.polygon([(cx - 16 * s, cy), (cx + 16 * s, cy - 4 * s),
                      (cx + 20 * s, cy), (cx + 16 * s, cy + 4 * s)],
                     fill=(70, 70, 70))
        draw.polygon([(cx - 2 * s, cy - 3 * s), (cx + 6 * s, cy - 12 * s),
                      (cx + 8 * s, cy - 3 * s)], fill=(90, 90, 90))
        draw.polygon([(cx - 2 * s, cy + 3 * s), (cx + 6 * s, cy + 12 * s),
                      (cx + 8 * s, cy + 3 * s)], fill=(90, 90, 90))
    burst(draw, x + w * 0.70, y + h * 0.28, 10, (255, 176, 32))
    burst(draw, x + w * 0.88, y + h * 0.55, 8, (255, 120, 40))
    smoke(draw, x + w * 0.70, y + h * 0.22, 6)


def scene_missile(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(16, 18, 30))
    for sx, sy in ((0.1, 0.15), (0.3, 0.3), (0.55, 0.1), (0.75, 0.3),
                   (0.9, 0.15), (0.2, 0.55), (0.65, 0.6), (0.85, 0.7)):
        draw.ellipse([x + w * sx - 1, y + h * sy - 1,
                      x + w * sx + 1, y + h * sy + 1], fill=(255, 255, 255))
    draw.text((x + 5, y + 3), "PYONGYANG", font=fnt(10, bold=True),
              fill=(255, 255, 255))
    # KCNA tag, top right.
    tag = "KCNA"
    tw = text_w(draw, tag, fnt(10, bold=True)) + 10
    draw.rectangle([x + w - tw - 4, y + 3, x + w - 4, y + 17], fill=RED)
    draw.text((x + w - tw + 1, y + 4), tag, font=fnt(10, bold=True),
              fill=(255, 255, 255))
    # Missile climbing diagonally, nose up-right, flame at the tail.
    mx, my = x + w * 0.30, y + h * 0.72
    draw.polygon([(mx, my), (mx + 52, my - 34), (mx + 58, my - 28),
                  (mx + 6, my + 6)], fill=(220, 220, 220))
    draw.polygon([(mx + 52, my - 34), (mx + 62, my - 40),
                  (mx + 60, my - 28)], fill=(178, 34, 34))
    draw.polygon([(mx + 2, my - 2), (mx - 8, my - 12), (mx - 2, my + 4)],
                 fill=(150, 150, 150))
    burst(draw, mx - 6, my + 4, 9, (255, 176, 32))


def scene_eu(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(214, 228, 244))
    draw.text((x + 5, y + 3), "BRUSSELS", font=fnt(10, bold=True),
              fill=(31, 78, 121))
    # Ring of twelve gold stars, kept clear of the BRUSSELS label.
    cx, cy, r = x + w * 0.30, y + h * 0.58, min(w, h) * 0.26
    import math
    for k in range(12):
        ang = -math.pi / 2 + k * math.pi / 6
        sx, sy = cx + r * math.cos(ang), cy + r * math.sin(ang)
        draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(212, 160, 23))
    draw.text((cx - 8, cy - 7), "EU", font=fnt(13, bold=True),
              fill=(31, 78, 121))
    # Berlaymont-style block on the right.
    bx = x + w * 0.58
    draw.rectangle([bx, y + h * 0.30, bx + w * 0.36, y + h * 0.86],
                   fill=(120, 130, 145))
    for row in range(4):
        for col in range(3):
            wx = bx + 5 + col * 14
            wy = y + h * 0.36 + row * 11
            draw.rectangle([wx, wy, wx + 9, wy + 7], fill=(240, 240, 200))
    draw.text((x + w - 6 - text_w(draw, "\u20ac45bn", fnt(15, bold=True)),
               y + 3), "\u20ac45bn", font=fnt(15, bold=True), fill=RED)


def scene_court(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(238, 234, 220))
    draw.text((x + 5, y + 3), "JERUSALEM", font=fnt(10, bold=True),
              fill=(90, 60, 20))
    # Courthouse sized as fractions of the tile, so it fits a 50px grid
    # scene as well as a taller lead scene: steps, columns, entablature,
    # pediment, all measured up from the bottom edge.
    base = y + h - 3
    half = w * 0.30
    cx = x + w / 2
    col_h = h * 0.38
    ped_h = h * 0.20
    draw.rectangle([cx - half - 6, base, cx + half + 6, base + 3],
                   fill=(120, 110, 95))
    draw.rectangle([cx - half, base - 3, cx + half, base], fill=(100, 92, 78))
    for i in range(4):
        colx = cx - half + 4 + i * ((2 * half - 12) / 3)
        draw.rectangle([colx, base - 3 - col_h, colx + 7, base - 3],
                       fill=(150, 142, 126))
    ent_y = base - 3 - col_h
    draw.rectangle([cx - half, ent_y - 4, cx + half, ent_y], fill=(100, 92, 78))
    draw.polygon([(cx - half, ent_y - 4), (cx + half, ent_y - 4),
                  (cx, ent_y - 4 - ped_h)], fill=(120, 110, 95))
    # Scales of justice, small, at the pediment.
    sx, sy = cx, ent_y - 4 - ped_h + 4
    draw.line([sx, sy, sx, sy + 6], fill=INK, width=2)
    draw.line([sx - 7, sy + 3, sx + 7, sy + 3], fill=INK, width=1)
    draw.ellipse([sx - 9, sy + 4, sx - 5, sy + 7], fill=INK)
    draw.ellipse([sx + 5, sy + 4, sx + 9, sy + 7], fill=INK)


def scene_gaza(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(20, 22, 38))
    for sx, sy in ((0.1, 0.15), (0.35, 0.08), (0.6, 0.18), (0.85, 0.1),
                   (0.5, 0.3)):
        draw.ellipse([x + w * sx - 1, y + h * sy - 1,
                      x + w * sx + 1, y + h * sy + 1], fill=(255, 255, 255))
    draw.text((x + 5, y + 3), "GAZA CITY", font=fnt(10, bold=True),
              fill=(255, 255, 255))
    ground = y + h - 6
    # Night skyline: blocks of flats with a few lit windows.
    blocks = [(0.04, 0.42, 0.20, 0.34), (0.24, 0.30, 0.18, 0.46),
              (0.46, 0.38, 0.20, 0.38), (0.70, 0.26, 0.16, 0.50),
              (0.88, 0.44, 0.10, 0.32)]
    for bx, by, bw, bh in blocks:
        draw.rectangle([x + w * bx, y + h * by,
                        x + w * (bx + bw), ground], fill=(52, 56, 78))
        for wy in range(3):
            for wx in range(2):
                if (int(bx * 100) + wy + wx) % 3 == 0:
                    draw.rectangle([x + w * bx + 4 + wx * 10,
                                    y + h * by + 6 + wy * 10,
                                    x + w * bx + 9 + wx * 10,
                                    y + h * by + 11 + wy * 10],
                                   fill=(250, 220, 130))
    burst(draw, x + w * 0.36, y + h * 0.24, 11, (255, 176, 32))
    burst(draw, x + w * 0.78, y + h * 0.20, 8, (255, 120, 40))
    smoke(draw, x + w * 0.36, y + h * 0.18, 6, (110, 110, 110))

def scene_market(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
    draw.text((x + 5, y + 3), "NASDAQ -3.9%", font=fnt(10, bold=True),
              fill=RED)
    base = y + h - 14
    # Falling red bars, left to right.
    heights = [0.62, 0.55, 0.48, 0.40, 0.30, 0.22, 0.16]
    slot = w / len(heights)
    for i, frac in enumerate(heights):
        bx = x + slot * i + 3
        bh = (h - 30) * frac
        draw.rectangle([bx, base - bh, bx + slot - 6, base], fill=(178, 34, 34))
    # Downward trend arrow over the bars.
    draw.line([x + 8, y + 22, x + w - 8, base - 4], fill=(120, 20, 20), width=3)
    ax, ay = x + w - 8, base - 4
    draw.polygon([(ax, ay), (ax - 12, ay - 2), (ax - 4, ay + 10)], fill=(120, 20, 20))
    draw.text((x + w - 6 - text_w(draw, "NVDA", fnt(10, bold=True)),
               y + h - 13), "NVDA", font=fnt(10, bold=True), fill=INK)


def scene_chip(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(18, 26, 20))
    draw.text((x + 5, y + 3), "SANTA CLARA", font=fnt(10, bold=True),
              fill=(120, 220, 140))
    cx, cy = x + w / 2, y + h * 0.56
    s = min(w, h) * 0.26
    # Pins on all four sides of the die.
    for i in range(5):
        off = -s + i * (2 * s / 4)
        draw.line([cx + off, cy - s - 8, cx + off, cy - s], fill=(120, 220, 140), width=2)
        draw.line([cx + off, cy + s, cx + off, cy + s + 8], fill=(120, 220, 140), width=2)
        draw.line([cx - s - 8, cy + off, cx - s, cy + off], fill=(120, 220, 140), width=2)
        draw.line([cx + s, cy + off, cx + s + 8, cy + off], fill=(120, 220, 140), width=2)
    draw.rectangle([cx - s, cy - s, cx + s, cy + s], fill=(20, 90, 50))
    draw.rectangle([cx - s, cy - s, cx + s, cy + s], outline=(120, 220, 140), width=2)
    draw.rectangle([cx - s * 0.55, cy - s * 0.55, cx + s * 0.55, cy + s * 0.55],
                   outline=(120, 220, 140), width=1)
    centre(draw, cx, cy - 7, "NVDA", fnt(13, bold=True), (255, 255, 255))


def scene_satellites(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(12, 16, 34))
    draw.text((x + 5, y + 3), "1,000,000 SATELLITES",
              font=fnt(10, bold=True), fill=(255, 255, 255))
    # Earth arc along the bottom.
    draw.ellipse([x - w * 0.25, y + h * 0.72, x + w * 1.25, y + h * 1.55],
                 fill=(40, 90, 160))
    draw.ellipse([x - w * 0.25, y + h * 0.72, x + w * 1.25, y + h * 1.55],
                 outline=(120, 180, 230), width=2)
    # Three orbit arcs with satellites riding them.
    for ry, dots in ((0.30, (0.2, 0.5, 0.8)), (0.48, (0.35, 0.65)),
                     (0.62, (0.15, 0.55, 0.85))):
        draw.arc([x + w * 0.05, y + h * ry - 26, x + w * 0.95, y + h * ry + 26],
                 start=180, end=360, fill=(140, 160, 200), width=1)
        for dx in dots:
            sx, sy = x + w * dx, y + h * ry
            draw.rectangle([sx - 4, sy - 2, sx + 4, sy + 2], fill=(255, 220, 90))
            draw.rectangle([sx - 8, sy - 1, sx - 4, sy + 1], fill=(180, 180, 200))
            draw.rectangle([sx + 4, sy - 1, sx + 8, sy + 1], fill=(180, 180, 200))


def scene_station(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(200, 224, 240))
    for sx, sy in ((0.12, 0.15), (0.5, 0.08), (0.88, 0.18), (0.3, 0.28)):
        draw.ellipse([x + w * sx - 1, y + h * sy - 1,
                      x + w * sx + 1, y + h * sy + 1], fill=(255, 255, 255))
    draw.text((x + 5, y + 3), "TIANGONG - SHENZHOU-24",
              font=fnt(10, bold=True), fill=(31, 78, 121))
    cx, cy = x + w / 2, y + h * 0.58
    # Solar wings, left and right of the core module.
    draw.rectangle([cx - w * 0.44, cy - 7, cx - 14, cy + 7], fill=(40, 90, 180))
    draw.rectangle([cx + 14, cy - 7, cx + w * 0.44, cy + 7], fill=(40, 90, 180))
    for i in range(4):
        lx = cx - w * 0.44 + 4 + i * 16
        draw.line([lx, cy - 7, lx, cy + 7], fill=(140, 180, 230), width=1)
        rx = cx + 18 + i * 16
        draw.line([rx, cy - 7, rx, cy + 7], fill=(140, 180, 230), width=1)
    # Core module + docked Shenzhou capsule.
    draw.rectangle([cx - 14, cy - 9, cx + 14, cy + 9], fill=(220, 220, 220))
    draw.rectangle([cx - 14, cy - 9, cx + 14, cy + 9], outline=INK, width=1)
    draw.ellipse([cx + 14, cy - 6, cx + 30, cy + 6], fill=(200, 200, 200))
    draw.ellipse([cx + 14, cy - 6, cx + 30, cy + 6], outline=INK, width=1)
    # Earth curve at the bottom.
    draw.ellipse([x - w * 0.2, y + h * 0.86, x + w * 1.2, y + h * 1.4],
                 fill=(60, 130, 190))


def scene_mine(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(206, 226, 190))
    draw.text((x + 5, y + 3), "BOGOR - 13 DEAD",
              font=fnt(10, bold=True), fill=(90, 40, 20))
    # Green hills behind, grey sky rain lines above.
    draw.polygon([(x, y + h * 0.55), (x + w * 0.35, y + h * 0.28),
                  (x + w * 0.7, y + h * 0.55), (x + w, y + h * 0.38),
                  (x + w, y + h), (x, y + h)], fill=(120, 170, 100))
    for rx in range(6):
        rx0 = x + 10 + rx * (w - 20) / 5
        draw.line([rx0, y + 16, rx0 - 4, y + 26], fill=(120, 140, 160), width=1)
    ground = y + h - 10
    draw.rectangle([x, ground, x + w, y + h], fill=(90, 70, 50))
    # Mine mouth: dark arch in the hillside, water flooding out.
    mx = x + w * 0.32
    draw.rectangle([mx, ground - 26, mx + 44, ground], fill=(40, 30, 22))
    draw.ellipse([mx, ground - 34, mx + 44, ground - 18], fill=(40, 30, 22))
    draw.rectangle([mx + 44, ground - 6, x + w * 0.95, ground + 2],
                   fill=(60, 120, 190))
    draw.rectangle([mx + 44, ground - 2, x + w * 0.95, ground + 6],
                   fill=(90, 150, 210))
    # Rescue lamp post, bent by the flood.
    draw.line([x + w * 0.82, ground - 30, x + w * 0.82, ground], fill=INK, width=2)
    draw.ellipse([x + w * 0.82 - 5, ground - 36, x + w * 0.82 + 5, ground - 26],
                 fill=(255, 220, 90))


SCENES = {
    "tariff": scene_tariff, "refinery": scene_refinery,
    "tanker": scene_tanker, "airbase": scene_airbase,
    "missile": scene_missile, "eu": scene_eu, "court": scene_court,
    "gaza": scene_gaza, "market": scene_market, "chip": scene_chip,
    "satellites": scene_satellites, "station": scene_station,
    "mine": scene_mine,
}

# ------------------------------------------------------------ card painters

def number_badge(draw, x, y, n, size=17):
    """Red circle with the story number in white."""
    r = size / 2
    draw.ellipse([x, y, x + size, y + size], fill=RED)
    label = str(n)
    lf = fnt(10, bold=True)
    draw.text((x + r - text_w(draw, label, lf) / 2, y + r - 6),
              label, font=lf, fill=(255, 255, 255))


def tag_row(draw, feat, x, y, w, big=False):
    """Number badge + PLACE - FIELD, status pill pinned to the right."""
    number_badge(draw, x, y - 1, feat["n"], size=17 if big else 15)
    tag = "%s - %s" % (feat["place"], feat["field"])
    tf = fnt(10 if big else 9, bold=True)
    draw.text((x + 20, y + 1), tag, font=tf, fill=INK)
    sf = fnt(8, bold=True)
    sw = int(text_w(draw, feat["status"], sf)) + 10
    draw.rounded_rectangle([x + w - sw, y, x + w, y + 13], radius=3,
                           fill=STATUS_FILL[feat["status"]])
    draw.text((x + w - sw + 5, y + 2), feat["status"], font=sf,
              fill=(255, 255, 255))


def paint_scene(img, feat, x, y, w, h):
    """Render one vector scene onto its own tile, then paste it in.

    Painting on a tile (instead of straight onto the page) clips every
    shape to the scene box, so a wide curve can never bleed into the
    caption row underneath.
    """
    tile = Image.new("RGB", (w, h), PAPER)
    tile_draw = ImageDraw.Draw(tile)
    SCENES[feat["scene"]](tile_draw, 0, 0, w, h)
    img.paste(tile, (x, y))


def lead_card(img, draw, feat, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255),
                   outline=INK, width=1)
    scene_h = 86
    paint_scene(img, feat, x + 1, y + 1, w - 2, scene_h)
    draw.line([x, y + scene_h + 1, x + w, y + scene_h + 1], fill=INK, width=1)
    tag_row(draw, feat, x + 6, y + scene_h + 7, w - 12, big=True)
    hy = y + scene_h + 26
    fit_para(draw, feat["headline"], fnt(15, bold=True), w - 12, 2,
             x + 6, hy, INK, leading=17)
    fit_para(draw, feat["deck"], fnt(11), w - 12, 3,
             x + 6, hy + 36, (60, 60, 60), leading=13)


def grid_card(img, draw, feat, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255),
                   outline=INK, width=1)
    scene_h = 50
    paint_scene(img, feat, x + 1, y + 1, w - 2, scene_h)
    draw.line([x, y + scene_h + 1, x + w, y + scene_h + 1], fill=INK, width=1)
    tag_row(draw, feat, x + 5, y + scene_h + 6, w - 10)
    hy = y + scene_h + 22
    fit_para(draw, feat["headline"], fnt(11, bold=True), w - 10, 2,
             x + 5, hy, INK, leading=13)
    fit_para(draw, feat["deck"], fnt(9), w - 10, 2,
             x + 5, hy + 27, (60, 60, 60), leading=11)


# -------------------------------------------------------------- top sections

def paint_masthead(draw):
    draw.rectangle([0, 0, PAGE_W, 26], fill=INK)
    mast = ("THE WORLD IN ONE DAY - 43 STORIES - 9 REGIONS - 14 FIELDS - "
            "EVERY ONE FROM THURSDAY 26 NOVEMBER 2026")
    centre(draw, PAGE_W / 2, 5, mast, fnt(14, bold=True), (255, 255, 255))


def paint_title(draw):
    centre(draw, PAGE_W / 2, 30, "Thursday 26 November 2026",
           fnt(42, bold=True, serif=True), INK)
    draw.line([MARGIN, 76, PAGE_W - MARGIN, 76], fill=INK, width=2)
    sub = ("US TARIFFS UP TO 40%      HOUTHIS HIT SAUDI REFINERY      "
           "CAIRO TANKER FIRE KILLS 31")
    centre(draw, PAGE_W / 2, 80, sub, fnt(15, bold=True, italic=True), RED)
    draw.line([MARGIN, 98, PAGE_W - MARGIN, 98], fill=INK, width=1)


def paint_region_tabs(draw, y):
    counts = {}
    for feat in FEATURES:
        counts[feat["region"]] = counts.get(feat["region"], 0) + 1
    # Count the ALSO_ON stories by the region table below.
    also_regions = [
        "AFRICA", "MIDDLE EAST", "N. AMERICA", "EUROPE", "N. AMERICA",
        "EUROPE", "N. AMERICA", "EUROPE", "EAST ASIA", "EUROPE",
        "EUROPE", "AFRICA", "AFRICA", "EAST ASIA", "SOUTH ASIA",
        "SOUTH ASIA", "AFRICA", "EUROPE", "OCEANIA", "EUROPE",
        "SE ASIA", "MIDDLE EAST", "EUROPE", "EUROPE", "EUROPE",
        "EAST ASIA", "N. AMERICA", "N. AMERICA", "S. AMERICA",
        "S. AMERICA",
    ]
    for region in also_regions:
        counts[region] = counts.get(region, 0) + 1
    total = sum(counts.values())
    assert total == 43, "region counts must sum to 43, got %d" % total
    font = fnt(11, bold=True)
    labels = ["%s %d" % (name, counts.get(name, 0)) for name in REGION_ORDER]
    widths = [int(text_w(draw, lab, font)) + 12 for lab in labels]
    gap = 4
    total_w = sum(widths) + gap * (len(labels) - 1)
    x = (PAGE_W - total_w) / 2
    for lab, w, name in zip(labels, widths, REGION_ORDER):
        draw.rectangle([x, y, x + w, y + 20], fill=REGION_FILL[name])
        draw.text((x + 6, y + 4), lab, font=font, fill=(255, 255, 255))
        x += w + gap
    return y + 24


def paint_timeline(draw, y):
    draw.rectangle([MARGIN, y, PAGE_W - MARGIN, y + 36], fill=NAVY)
    draw.text((MARGIN + 6, y + 11), "THURSDAY UTC",
              font=fnt(11, bold=True), fill=(255, 255, 255))
    col_w = 268
    x0 = MARGIN + 108
    for i, (when, where, what) in enumerate(TIMELINE):
        cx = x0 + (i % 3) * col_w
        cy = y + 3 + (i // 3) * 17
        draw.text((cx, cy), when, font=fnt(10, bold=True),
                  fill=(255, 210, 90))
        wx = cx + text_w(draw, when, fnt(10, bold=True)) + 5
        rest = "%s - %s" % (where, what)
        draw.text((wx, cy), rest, font=fnt(10), fill=(255, 255, 255))
    return y + 40


def paint_stats(draw, y):
    col_w = (PAGE_W - 2 * MARGIN) / 6
    for i, (big, cap) in enumerate(STATS):
        x = MARGIN + i * col_w
        draw.text((x + 2, y), big, font=fnt(22, bold=True), fill=NAVY)
        fit_para(draw, cap, fnt(8), col_w - 8, 2, x + 2, y + 24,
                 (80, 80, 80), leading=9)
        if i:
            draw.line([x, y + 2, x, y + 34], fill=(200, 200, 200), width=1)
    draw.line([MARGIN, y + 38, PAGE_W - MARGIN, y + 38], fill=INK, width=1)
    return y + 42

# ------------------------------------------------------------------ map
# A coarse 48x22 dotted world map, drawn from a hand-made land grid.
# Columns run -180..+180 longitude, rows run +80..-60 latitude.

LAND = [
    "     ######          ##############             ",
    "   ###########     #######################     ",
    "  #############    #######################     ",
    "   ###########      #####################      ",
    "    #########  #    ###################        ",
    "     ########  ##   #################          ",
    "      ######    ##   ###############           ",
    "       ####     #     ###########  ##           ",
    "        ##     ###    #########   ###           ",
    "              #####    #######     ##           ",
    "             #######    #####      ###           ",
    "             #######     ###       ##            ",
    "              #####       #        #            ",
    "               ###                           ## ",
    "                ##                         #### ",
    "                 #                        ######",
    "                                         ##### ",
    "                                          ###  ",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                                ",
]

# Pin positions as (x fraction, y fraction) of the map box.
PINS = {
    1: (0.286, 0.294), 2: (0.665, 0.435), 3: (0.545, 0.405),
    4: (0.619, 0.175), 5: (0.849, 0.293), 6: (0.512, 0.209),
    7: (0.615, 0.320), 8: (0.570, 0.365), 9: (0.294, 0.281),
    10: (0.161, 0.304), 11: (0.276, 0.369), 13: (0.797, 0.619),
}


def paint_map(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(232, 228, 205),
                   outline=INK, width=1)
    cols = len(LAND[0])
    rows = len(LAND)
    cw, ch = w / cols, h / rows
    for r, row in enumerate(LAND):
        for c, ch_ in enumerate(row):
            if ch_ == "#":
                cx, cy = x + c * cw + cw / 2, y + r * ch + ch / 2
                draw.ellipse([cx - 1.6, cy - 1.6, cx + 1.6, cy + 1.6],
                             fill=(120, 110, 80))
    for n, (fx, fy) in PINS.items():
        px, py = x + fx * w, y + fy * h
        draw.ellipse([px - 7, py - 7, px + 7, py + 7], fill=RED,
                     outline=(255, 255, 255), width=1)
        lab = str(n)
        lf = fnt(8, bold=True)
        draw.text((px - text_w(draw, lab, lf) / 2, py - 5), lab,
                  font=lf, fill=(255, 255, 255))
    return y + h


def paint_also_on(draw, x, y, w, h):
    draw.text((x, y), "ALSO ON THURSDAY 26 NOVEMBER",
              font=fnt(13, bold=True), fill=NAVY)
    draw.text((x + w - text_w(draw, SOURCES, fnt(8)), y + 15),
              SOURCES, font=fnt(8), fill=(90, 90, 90))
    draw.line([x, y + 27, x + w, y + 27], fill=INK, width=1)
    col_w = w / 2
    row_h = 14
    font = fnt(10)
    for i, line in enumerate(ALSO_ON):
        col = i // 15
        row = i % 15
        lx = x + col * col_w
        ly = y + 31 + row * row_h
        entry = "%d. %s" % (14 + i, line)
        if text_w(draw, entry, font) > col_w - 4:
            font = fnt(9)
        draw.text((lx, ly), entry, font=font, fill=INK)
        font = fnt(10)
    return y + 31 + 15 * row_h


def paint_date_check(draw, y):
    draw.rectangle([MARGIN, y, PAGE_W - MARGIN, y + 46], outline=RED, width=2)
    fit_para(draw, DATE_CHECK, fnt(10), PAGE_W - 2 * MARGIN - 16, 3,
             MARGIN + 8, y + 4, INK, leading=13)
    return y + 50


def paint_footer(draw, y):
    centre(draw, PAGE_W / 2, y,
           "Compiled from Thursday's reporting - every story above happened, "
           "or was first reported, on Thursday 26 November 2026.",
           fnt(10, italic=True), (90, 90, 90))
    # Status legend, bottom right.
    lx = PAGE_W - MARGIN
    items = [("CONFIRMED", (31, 78, 121)), ("OFFICIAL", (20, 83, 45)),
             ("REPORTED", (146, 64, 14)), ("CLAIM", (153, 27, 27))]
    lf = fnt(8, bold=True)
    total = sum(int(text_w(draw, name, lf)) + 22 for name, _ in items)
    x = lx - total
    for name, col in items:
        draw.rectangle([x, y + 13, x + 10, y + 21], fill=col)
        draw.text((x + 13, y + 12), name, font=lf, fill=INK)
        x += int(text_w(draw, name, lf)) + 22
    return y + 24


# ------------------------------------------------------------------- build

def build():
    img = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
    draw = ImageDraw.Draw(img)

    paint_masthead(draw)
    paint_title(draw)
    y = paint_region_tabs(draw, 102)
    y = paint_timeline(draw, y)
    y = paint_stats(draw, y)

    # Three lead cards.
    lead_w, lead_h = 330, 190
    gap = 9
    for i, feat in enumerate(FEATURES[:3]):
        lead_card(img, draw, feat, MARGIN + i * (lead_w + gap), y, lead_w, lead_h)
    y += lead_h + 4

    # Ten grid cards, five across, two rows.
    grid_w, grid_h = 197, 142
    gg = 6
    for i, feat in enumerate(FEATURES[3:]):
        row, col = divmod(i, 5)
        grid_card(img, draw, feat, MARGIN + col * (grid_w + gg),
                  y + row * (grid_h + 4), grid_w, grid_h)
    y += 2 * grid_h + 8

    # Map on the left, ALSO ON list on the right.
    draw.text((MARGIN, y), "WHERE IT HAPPENED",
              font=fnt(13, bold=True), fill=NAVY)
    map_y = y + 18
    map_w, map_h = 322, 196
    paint_map(draw, MARGIN, map_y, map_w, map_h)
    draw.text((MARGIN, map_y + map_h + 4),
              "Pins 1-13 mark the illustrated stories.",
              font=fnt(9), fill=(90, 90, 90))
    draw.text((MARGIN, map_y + map_h + 16),
              "12 is in orbit, off the map.",
              font=fnt(9), fill=(90, 90, 90))
    paint_also_on(draw, MARGIN + map_w + 12, y, PAGE_W - MARGIN * 2 - map_w - 12,
                  map_h + 18)
    y = map_y + map_h + 34

    y = paint_date_check(draw, y)
    paint_footer(draw, y)
    img.save(OUT, format="PNG")
    return OUT


if __name__ == "__main__":
    build()
    print("wrote %s" % OUT)
