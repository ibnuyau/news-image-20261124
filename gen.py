"""One-page newspaper front page for Tuesday 24 November 2026.

The script draws a 1024 by 1024 front page with Pillow: a navy masthead,
a date title, a red standfirst, a statistics strip, a coloured region
bar, a UTC timeline, three illustrated lead stories, twelve small
illustrated stories, a dotted world map beside a list of twenty-one
further stories, a date-check box and a footer. All thirty-six stories
were first reported on 24 November 2026.

Nothing here touches the network and nothing is random, so two runs
produce identical bytes. The drawing itself is organised as a tiny kit
of shape helpers (boxes, discs, segments, polygons, wrapped text) plus
a set of small pictogram painters, and a FrontPage object that lays the
sections out top to bottom.
"""

import hashlib
import math

from PIL import Image, ImageDraw, ImageFont

PAGE = 1024
EDGE = 26
GUTTER = 14

PAL = {
    "ink": (28, 28, 28),
    "navy": (23, 33, 66),
    "red": (178, 34, 34),
    "darkred": (139, 0, 0),
    "grey": (108, 108, 108),
    "rule": (196, 196, 196),
    "paper": (252, 250, 244),
    "cream": (246, 242, 232),
    "white": (255, 255, 255),
    "gold": (255, 220, 130),
    "pale": (220, 220, 220),
    "mapdot": (120, 120, 120),
}

FONT_DIR = "/usr/share/fonts/truetype/liberation/"
FONT_FILES = {
    "serif_b": "LiberationSerif-Bold.ttf",
    "serif": "LiberationSerif-Regular.ttf",
    "serif_i": "LiberationSerif-Italic.ttf",
    "sans_b": "LiberationSans-Bold.ttf",
    "sans": "LiberationSans-Regular.ttf",
}

# name -> (family key, point size); the layout asks for fonts by name.
FONT_SIZES = {
    "bar": ("sans_b", 13),
    "bar_small": ("sans", 11),
    "title": ("serif_b", 58),
    "standfirst": ("serif_i", 17),
    "stat_num": ("serif_b", 26),
    "stat_lbl": ("sans", 10),
    "region": ("sans_b", 12),
    "time": ("sans_b", 11),
    "time_txt": ("sans", 11),
    "tag": ("sans_b", 12),
    "lead_kicker": ("sans_b", 11),
    "lead_head": ("serif_b", 19),
    "lead_body": ("sans", 12),
    "grid_kicker": ("sans_b", 10),
    "grid_head": ("serif_b", 13),
    "grid_sum": ("sans", 11),
    "section": ("sans_b", 13),
    "also": ("sans", 11),
    "date": ("sans_b", 11),
    "foot": ("sans", 10),
    "bottom_bar": ("sans_b", 12),
}


def build_fonts():
    """Load every named font once and hand back a dict of them."""
    out = {}
    for name, (family, size) in FONT_SIZES.items():
        out[name] = ImageFont.truetype(FONT_DIR + FONT_FILES[family], size)
    return out


# ------------------------------------------------------------------ kit
# Small wrappers around ImageDraw calls. Every wrapper takes the same
# (x, y, w, h) box or (cx, cy) centre convention, so the pictograms and
# the layout below read as coordinates rather than raw PIL calls.


def fill_rect(pen, x, y, w, h, colour):
    pen.rectangle([x, y, x + w, y + h], fill=colour)


def outline_rect(pen, x0, y0, x1, y1, colour, width=1):
    pen.rectangle([x0, y0, x1, y1], outline=colour, width=width)


def round_box(pen, x, y, w, h, radius, fill=None, outline=None, width=1):
    pen.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill,
                          outline=outline, width=width)


def seg(pen, x0, y0, x1, y1, colour, width=1):
    pen.line([x0, y0, x1, y1], fill=colour, width=width)


def polyline(pen, points, colour, width=1):
    pen.line(points, fill=colour, width=width)


def fill_poly(pen, points, colour):
    pen.polygon(points, fill=colour)


def outline_poly(pen, points, colour, width=1):
    pen.polygon(points, outline=colour, width=width)


def disc(pen, cx, cy, r, colour):
    pen.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour)


def ring(pen, cx, cy, r, colour, width=1):
    pen.ellipse([cx - r, cy - r, cx + r, cy + r], outline=colour, width=width)


def ring_xy(pen, cx, cy, rx, ry, colour, width=1):
    pen.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=colour,
                width=width)


def fill_ellipse(pen, x0, y0, x1, y1, colour):
    pen.ellipse([x0, y0, x1, y1], fill=colour)


def put_text(pen, text, font, x, y, colour):
    pen.text((x, y), text, font=font, fill=colour)


def centred_text(pen, text, font, cx, y, colour):
    """Draw text centred on cx; return how wide it came out."""
    wide = pen.textlength(text, font=font)
    pen.text((cx - wide / 2, y), text, font=font, fill=colour)
    return wide


def rel_points(x, y, w, h, fracs):
    """Turn fractions of a box into absolute (x, y) points."""
    return [(x + w * fx, y + h * fy) for fx, fy in fracs]


def offset_points(cx, cy, s, offsets):
    """Turn (dx, dy) offsets scaled by s into absolute points."""
    return [(cx + s * dx, cy + s * dy) for dx, dy in offsets]


def wave_line(pen, x, span, base, steps, amp, phase, colour, width=2):
    """One sine wave: steps+1 points from x across span, wiggling by amp."""
    pts = []
    for i in range(steps + 1):
        px = x + span * i / steps
        py = base + amp * math.sin(i * phase)
        pts.append((px, py))
    pen.line(pts, fill=colour, width=width)


def wrap_text(pen, text, font, max_w):
    """Greedy word wrap: pack words onto lines no wider than max_w."""
    lines = []
    current = ""
    for word in text.split():
        joined = (current + " " + word).strip()
        if pen.textlength(joined, font=font) <= max_w:
            current = joined
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_para(pen, text, font, x, y, max_w, leading, colour, limit=None):
    """Draw wrapped text and return the y just under the last line."""
    lines = wrap_text(pen, text, font, max_w)
    if limit is not None:
        lines = lines[:limit]
    for line in lines:
        pen.text((x, y), line, font=font, fill=colour)
        y += leading
    return y


# ------------------------------------------------------------- pictograms
# Each painter fills the box (x, y, w, h). They are pictograms, not
# photographs: flat colour, a few shapes, no detail that needs a photo.


def paint_night_sky(pen, x, y, w, h):
    """Missile trails over a city at night."""
    fill_rect(pen, x, y, w, h, (24, 32, 58))
    for sx, sy in ((0.15, 0.25), (0.5, 0.15), (0.82, 0.3)):
        disc(pen, x + w * sx, y + h * sy, 2, (255, 220, 130))
    for i in range(3):
        bx = x + w * (0.12 + i * 0.28)
        bh = h * (0.35 + 0.12 * ((i * 7) % 3))
        fill_rect(pen, bx, y + h - bh, w * 0.2, bh, (52, 62, 96))
        for wy in range(2):
            win_y = y + h - bh + 8 + wy * 16
            fill_rect(pen, bx + w * 0.04, win_y, w * 0.04, 6,
                      (255, 210, 110))
    seg(pen, x + w * 0.7, y + h * 0.2, x + w * 0.55, y + h * 0.55,
        (255, 240, 180), 3)
    seg(pen, x + w * 0.85, y + h * 0.35, x + w * 0.72, y + h * 0.6,
        (255, 240, 180), 3)


def paint_dome(pen, x, y, w, h):
    """A capitol dome under a star field."""
    fill_rect(pen, x, y, w, h, (28, 54, 96))
    for sx, sy in ((0.12, 0.2), (0.3, 0.12), (0.7, 0.18), (0.88, 0.28)):
        disc(pen, x + w * sx, y + h * sy, 2, PAL["white"])
    cx = x + w / 2
    stone = (240, 238, 228)
    fill_rect(pen, cx - w * 0.3, y + h * 0.62, w * 0.6, h * 0.38, stone)
    fill_poly(pen, [(cx - w * 0.22, y + h * 0.62),
                    (cx + w * 0.22, y + h * 0.62),
                    (cx, y + h * 0.3)], stone)
    fill_rect(pen, cx - 3, y + h * 0.22, 6, h * 0.08, stone)
    fill_rect(pen, x + w * 0.08, y + h * 0.8, w * 0.84, h * 0.2,
              (200, 196, 184))


# Two market moods share one chip drawing; only the line and its colour
# change, so one painter takes a direction flag.
TRENDS = {
    "climb": {
        "points": ((0.08, 0.75), (0.3, 0.65), (0.5, 0.7), (0.7, 0.4),
                   (0.92, 0.25)),
        "colour": (90, 220, 130),
    },
    "fall": {
        "points": ((0.08, 0.25), (0.3, 0.35), (0.5, 0.3), (0.7, 0.6),
                   (0.92, 0.75)),
        "colour": (255, 90, 70),
    },
}


def paint_market(pen, x, y, w, h, mood):
    """A market line over a chip; mood is 'climb' or 'fall'."""
    trend = TRENDS[mood]
    fill_rect(pen, x, y, w, h, (16, 60, 52))
    polyline(pen, rel_points(x, y, w, h, trend["points"]),
             trend["colour"], 4)
    cx, cy = x + w * 0.5, y + h * 0.55
    chip_edge = (150, 220, 200)
    round_box(pen, cx - w * 0.16, cy - h * 0.18, w * 0.32, h * 0.36, 6,
              fill=(30, 90, 76), outline=chip_edge, width=2)
    for k in range(3):
        px = cx - w * 0.16 + k * w * 0.16
        seg(pen, px, cy - h * 0.18, px, cy - h * 0.3, chip_edge, 2)
        seg(pen, px, cy + h * 0.18, px, cy + h * 0.3, chip_edge, 2)


def paint_flames(pen, x, y, w, h):
    """Fire over a factory roofline."""
    fill_rect(pen, x, y, w, h, (96, 30, 22))
    fill_rect(pen, x, y + h * 0.68, w, h * 0.32, (52, 52, 52))
    for fx in (0.25, 0.55, 0.8):
        cx = x + w * fx
        fill_poly(pen, [(cx - w * 0.07, y + h * 0.66), (cx, y + h * 0.3),
                        (cx + w * 0.07, y + h * 0.66)], (255, 150, 40))
        fill_poly(pen, [(cx - w * 0.035, y + h * 0.66), (cx, y + h * 0.45),
                        (cx + w * 0.035, y + h * 0.66)], (255, 220, 90))


def paint_ship(pen, x, y, w, h):
    """Waves under a listing ship."""
    fill_rect(pen, x, y, w, h, (24, 52, 84))
    fill_poly(pen, [(x + w * 0.2, y + h * 0.45),
                    (x + w * 0.8, y + h * 0.55),
                    (x + w * 0.75, y + h * 0.7),
                    (x + w * 0.25, y + h * 0.6)], (120, 120, 120))
    fill_rect(pen, x + w * 0.42, y + h * 0.3, w * 0.06, h * 0.18,
              (120, 120, 120))
    for k in range(3):
        base = y + h * (0.72 + k * 0.09)
        wave_line(pen, x + w * 0.05, w * 0.9, base, 12, 3,
                  math.pi / 3, (140, 190, 230), 2)


def paint_globe(pen, x, y, w, h):
    """A globe on a teal field."""
    fill_rect(pen, x, y, w, h, (22, 96, 88))
    cx, cy = x + w / 2, y + h / 2
    r = min(w, h) * 0.32
    globe_line = (240, 240, 230)
    ring(pen, cx, cy, r, globe_line, 3)
    ring_xy(pen, cx, cy, r * 0.45, r, globe_line, 2)
    seg(pen, x + w * 0.18, cy, x + w * 0.82, cy, globe_line, 2)


# Lead illustrations are picked by name, so the story list below only
# has to name a picture instead of holding a function reference.
SCENES = {
    "sky": paint_night_sky,
    "dome": paint_dome,
    "ship": paint_ship,
    "globe": paint_globe,
    "climb": lambda pen, x, y, w, h: paint_market(pen, x, y, w, h, "climb"),
    "fall": lambda pen, x, y, w, h: paint_market(pen, x, y, w, h, "fall"),
}


# ------------------------------------------------------------- small marks
# Each mark draws inside the square (x, y, s) in the colour given.


def mark_quake(pen, x, y, s, c):
    cx, cy = x + s / 2, y + s / 2
    zig = ((-0.35, 0.3), (-0.12, -0.15), (0.05, 0.2), (0.18, -0.3),
           (0.35, 0.1))
    polyline(pen, offset_points(cx, cy, s, zig), c, 3)


def mark_gavel(pen, x, y, s, c):
    outline_rect(pen, x + s * 0.15, y + s * 0.2, x + s * 0.75,
                 y + s * 0.38, c, 3)
    seg(pen, x + s * 0.45, y + s * 0.38, x + s * 0.45, y + s * 0.75, c, 3)
    seg(pen, x + s * 0.2, y + s * 0.78, x + s * 0.7, y + s * 0.78, c, 3)


def mark_robot(pen, x, y, s, c):
    round_box(pen, x + s * 0.18, y + s * 0.22, s * 0.64, s * 0.56,
              s * 0.08, outline=c, width=3)
    seg(pen, x + s * 0.5, y + s * 0.22, x + s * 0.5, y + s * 0.08, c, 3)
    disc(pen, x + s * 0.5, y + s * 0.07, s * 0.05, c)
    disc(pen, x + s * 0.37, y + s * 0.43, s * 0.05, c)
    disc(pen, x + s * 0.63, y + s * 0.67, s * 0.05, c)


def mark_cross(pen, x, y, s, c):
    cx, cy = x + s / 2, y + s / 2
    ring(pen, cx, cy, s * 0.4, c, 3)
    fill_rect(pen, cx - s * 0.07, cy - s * 0.25, s * 0.14, s * 0.5, c)
    fill_rect(pen, cx - s * 0.25, cy - s * 0.07, s * 0.5, s * 0.14, c)


def mark_cup(pen, x, y, s, c):
    outline_poly(pen, [(x + s * 0.2, y + s * 0.25),
                       (x + s * 0.8, y + s * 0.25),
                       (x + s * 0.68, y + s * 0.75),
                       (x + s * 0.32, y + s * 0.75)], c, 3)
    seg(pen, x + s * 0.5, y + s * 0.25, x + s * 0.5, y + s * 0.08, c, 3)
    seg(pen, x + s * 0.25, y + s * 0.85, x + s * 0.75, y + s * 0.85, c, 3)


def mark_chart(pen, x, y, s, c):
    for i, bh in enumerate((0.25, 0.45, 0.3, 0.6)):
        bx = x + s * (0.12 + i * 0.22)
        fill_rect(pen, bx, y + s * (0.85 - bh), s * 0.14, s * bh, c)


def mark_ring(pen, x, y, s, c):
    cx, cy = x + s / 2, y + s / 2
    ring(pen, cx, cy, s * 0.32, c, 3)
    disc(pen, cx, cy, s * 0.1, c)


def mark_bolt(pen, x, y, s, c):
    fill_poly(pen, [(x + s * 0.55, y + s * 0.05),
                    (x + s * 0.3, y + s * 0.55),
                    (x + s * 0.48, y + s * 0.55),
                    (x + s * 0.42, y + s * 0.95),
                    (x + s * 0.72, y + s * 0.42),
                    (x + s * 0.52, y + s * 0.42)], c)


def mark_plane(pen, x, y, s, c):
    outline_poly(pen, [(x + s * 0.1, y + s * 0.55),
                       (x + s * 0.9, y + s * 0.4),
                       (x + s * 0.9, y + s * 0.55),
                       (x + s * 0.5, y + s * 0.62)], c, 2)
    fill_poly(pen, [(x + s * 0.45, y + s * 0.55),
                    (x + s * 0.6, y + s * 0.3),
                    (x + s * 0.68, y + s * 0.55)], c)


def mark_megaphone(pen, x, y, s, c):
    outline_poly(pen, [(x + s * 0.12, y + s * 0.42),
                       (x + s * 0.85, y + s * 0.18),
                       (x + s * 0.85, y + s * 0.66),
                       (x + s * 0.12, y + s * 0.58)], c, 3)
    seg(pen, x + s * 0.3, y + s * 0.58, x + s * 0.24, y + s * 0.85, c, 3)


def mark_star(pen, x, y, s, c):
    cx, cy = x + s / 2, y + s / 2
    tips = []
    for i in range(10):
        r = s * 0.46 if i % 2 == 0 else s * 0.19
        a = math.pi * i / 5 - math.pi / 2
        tips.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    outline_poly(pen, tips, c, 2)


def mark_flag(pen, x, y, s, c):
    fill_rect(pen, x + s * 0.1, y + s * 0.15, s * 0.8, s * 0.7, c)
    seg(pen, x + s * 0.1, y + s * 0.15, x + s * 0.1, y + s * 0.98, c, 3)


def mark_globe(pen, x, y, s, c):
    cx, cy = x + s / 2, y + s / 2
    ring(pen, cx, cy, s * 0.42, c, 3)
    ring_xy(pen, cx, cy, s * 0.42 * 0.45, s * 0.42, c, 2)
    seg(pen, x + s * 0.1, cy, x + s * 0.9, cy, c, 2)


def mark_flame(pen, x, y, s, c):
    cx = x + s / 2
    fill_poly(pen, [(cx - s * 0.28, y + s * 0.85), (cx, y + s * 0.08),
                    (cx + s * 0.28, y + s * 0.85)], c)
    fill_poly(pen, [(cx - s * 0.12, y + s * 0.85), (cx, y + s * 0.4),
                    (cx + s * 0.12, y + s * 0.85)], PAL["white"])


def mark_sea(pen, x, y, s, c):
    for k in range(3):
        base = y + s * (0.25 + k * 0.25)
        wave_line(pen, x + s * 0.05, s * 0.9, base, 10, s * 0.05,
                  math.pi / 2.5, c, 2)


def mark_drone(pen, x, y, s, c):
    """A small quadcopter drone."""
    cx, cy = x + s / 2, y + s / 2
    fill_rect(pen, cx - s * 0.12, cy - s * 0.1, s * 0.24, s * 0.2, c)
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        rx = cx + dx * s * 0.32
        ry = cy + dy * s * 0.28
        seg(pen, cx, cy, rx, ry, c, 2)
        ring_xy(pen, rx, ry, s * 0.09, s * 0.05, c, 2)


# Grid stories name their mark; the layout looks the painter up here.
MARKS = {
    "quake": mark_quake,
    "gavel": mark_gavel,
    "robot": mark_robot,
    "cross": mark_cross,
    "cup": mark_cup,
    "chart": mark_chart,
    "ring": mark_ring,
    "bolt": mark_bolt,
    "plane": mark_plane,
    "megaphone": mark_megaphone,
    "star": mark_star,
    "flag": mark_flag,
    "globe": mark_globe,
    "flame": mark_flame,
    "sea": mark_sea,
    "drone": mark_drone,
}


# ------------------------------------------------------------------ stories
# Every story below was first reported on Tuesday 24 November 2026.

MASTHEAD = "THE WORLD IN ONE DAY"
MASTHEAD_RIGHT = "36 STORIES  ·  6 REGIONS  ·  EVERY ONE DATED TUESDAY 24 NOVEMBER 2026"
EDITION_DATE = "Tuesday 24 November 2026"
STANDFIRST = ("Nvidia shares soar 31% as Huang returns  ·  Russia warns "
              "Estonia of 'open war'  ·  Ukraine sinks Russian warship")
TIMELINE_TITLE = "THE DAY IN UTC"
MAP_TITLE = "WHERE IT HAPPENED"
MAP_NOTE = "pins match story numbers"
ALSO_TITLE = "ALSO ON TUESDAY 24 NOVEMBER  —  21 MORE STORIES"
BOTTOM_RIGHT = "TUESDAY 24 NOVEMBER 2026  ·  ONE PAGE"

LEADS = [
    {
        "tag": "NVIDIA SHARES SOAR 31%",
        "art": "climb",
        "dateline": "1  SANTA CLARA, USA  ·  MARKETS",
        "head": "Nvidia shares soar 31% as Huang returns",
        "body": ("Nvidia shares jumped 31% in a day after the board "
                 "reinstated Jensen Huang as chief executive, lifting "
                 "the S&P 500 4.73% and Japan's Nikkei 3.91%."),
        "credit": "One Turn, Reuters",
    },
    {
        "tag": "RUSSIA WARNS ESTONIA OF OPEN WAR",
        "art": "sky",
        "dateline": "2  TALLINN, ESTONIA  ·  NATO",
        "head": "Russia warns Estonia of 'open war'",
        "body": ("Moscow said Estonia's decision to close its border "
                 "for six months from 1 December was 'on the verge of "
                 "triggering open war', after accusing Russian agents "
                 "of targeting an Estonian firm."),
        "credit": "Reuters, Medium",
    },
    {
        "tag": "UKRAINE SINKS RUSSIAN WARSHIP",
        "art": "ship",
        "dateline": "3  BENGHAZI, LIBYA  ·  CONFLICT",
        "head": "Zelensky confirms sinking of Russian corvette",
        "body": ("President Zelensky confirmed Ukraine used seven naval "
                 "drones to sink the Russian corvette Merkury at "
                 "Benghazi port. The Kremlin warned of 'painful "
                 "consequences'."),
        "credit": "The Guardian, BBC",
    },
]

GRID = [
    {
        "place": "MOSCOW · NUCLEAR",
        "head": "Medvedev: nuclear strike 'considered'",
        "summ": "Medvedev says Ukraine and NATO created cases for a nuclear strike.",
        "mark": "flame",
        "tint": (178, 34, 34),
    },
    {
        "place": "BRUSSELS · SPACE",
        "head": "NATO vows to defend space from threats",
        "summ": "Rutte vows defence after reports of a Russian nuclear satellite.",
        "mark": "star",
        "tint": (28, 54, 96),
    },
    {
        "place": "WASHINGTON · ARMS",
        "head": "US delays Patriot missiles for Ukraine",
        "summ": "US delays ~60 Patriot interceptors; Hegseth has not approved them.",
        "mark": "plane",
        "tint": (90, 90, 90),
    },
    {
        "place": "WARSAW · AIRSPACE",
        "head": "Russian drone enters Polish airspace",
        "summ": "Drone briefly enters Poland in a strike on Ukraine; 2nd violation.",
        "mark": "drone",
        "tint": (178, 34, 34),
    },
    {
        "place": "USA · TECH",
        "head": "US states sue Musk firms over Grok images",
        "summ": "Oregon and Virginia sue SpaceX over Grok child-abuse images.",
        "mark": "robot",
        "tint": (52, 62, 96),
    },
    {
        "place": "PARIS · PHARMA",
        "head": "Sanofi buys Insmed for $41bn",
        "summ": "Sanofi agrees to buy US biotech Insmed; biggest deal in 3 years.",
        "mark": "chart",
        "tint": (16, 60, 52),
    },
    {
        "place": "USA · HEALTH",
        "head": "US loses measles elimination status",
        "summ": "US loses measles elimination status after more than 25 years.",
        "mark": "cross",
        "tint": (178, 34, 34),
    },
    {
        "place": "SPACE · SCIENCE",
        "head": "Astronomers find most distant black hole",
        "summ": "A quasar from 630m years after the Big Bang is the most distant yet.",
        "mark": "ring",
        "tint": (28, 54, 96),
    },
    {
        "place": "USA · AI",
        "head": "Amazon acquires Decart AI for $7.5bn",
        "summ": "Amazon agrees to buy Decart AI to boost AWS chip efficiency.",
        "mark": "robot",
        "tint": (22, 96, 88),
    },
    {
        "place": "BERLIN · DEFENCE",
        "head": "Germany first to access Ukraine's Delta",
        "summ": "Germany becomes first country to access Ukraine's Delta system.",
        "mark": "flag",
        "tint": (28, 90, 130),
    },
    {
        "place": "BAGHDAD · OIL",
        "head": "Iraq PM orders takeover of Kurdish oilfields",
        "summ": "Iraq's PM orders the oil ministry to manage Kurdish-area fields.",
        "mark": "bolt",
        "tint": (196, 130, 30),
    },
    {
        "place": "USA · HEALTH",
        "head": "FDA approves first limb-girdle drug",
        "summ": "FDA approves BridgeBio's drug, first for limb-girdle dystrophy.",
        "mark": "cross",
        "tint": (16, 60, 52),
    },
]

ALSO = """Israeli airstrikes kill at least six in Gaza.
UN mission in Libya urges probe into Benghazi port attacks.
Heavy fighting in Ituri traps DR Congo Ebola teams, WHO says.
Seven countries back EU push to limit Russian visas.
Car bomb hits governor's office in Villavicencio, Colombia.
Mexico to try 'Chapo Isidro' despite US request.
Sheikh Hasina plans return to Bangladesh on Dec. 16.
Nepal PM visits India; India pledges 1.4bn euros.
Qatar PM seeks to revive US-Iran talks.
EU proposes 22nd sanctions package, sports ban included.
Spain's Supreme Court amnesties Carles Puigdemont.
DR Congo says military aircraft missing; rebels claim shootdown.
Indonesia factory fire toll rises to 26, dozens missing.
Strikes on Yemen buses and trucks kill about 25.
Brazil's real weakens as growth forecast is cut.
Kushner says he urged Trump to ease pressure on Zelensky.
Ukraine defence minister meets Norway counterpart in Oslo.
UN: Gaza war undid 77 years of human development.
UN chief urges talks on global AI safety rules.
47,000 women killed by partners or relatives in 2025.
Somalia and Uganda to step up operations against Al-Shabaab.""".split("\n")

STATS = [
    {"big": "31%", "small": "Nvidia shares jump in a day"},
    {"big": "$41bn", "small": "Sanofi buys Insmed"},
    {"big": "60", "small": "Patriot missiles delayed"},
    {"big": "7", "small": "drones sank Russian corvette"},
    {"big": "700k", "small": "Russian soldiers killed, analysis"},
    {"big": "47,000", "small": "women killed by relatives in 2025"},
]

REGIONS = [
    {"name": "EUROPE", "n": 10, "tint": (28, 90, 130)},
    {"name": "MIDDLE EAST", "n": 5, "tint": (178, 34, 34)},
    {"name": "AMERICAS", "n": 10, "tint": (28, 54, 96)},
    {"name": "ASIA-PACIFIC", "n": 3, "tint": (196, 130, 30)},
    {"name": "AFRICA", "n": 5, "tint": (34, 120, 70)},
    {"name": "WORLD", "n": 3, "tint": (90, 90, 90)},
]

TIMELINE = [
    {"at": "07:39", "what": "NATO vows space defence"},
    {"at": "08:39", "what": "Ukraine minister meets Norway"},
    {"at": "09:37", "what": "Kremlin warns of consequences"},
    {"at": "09:40", "what": "Kushner urged Trump to ease pressure"},
]

# A coarse dotted world map: '#' is land, '.' is ocean.
MAP_ROWS = """................................................
...#####....####......##################........
..########..######..########################....
.##########..#####.##########################...
..#########...###...#######################....
...#######.....#.....##########..#########......
....#####.............########....#######.......
.....###..............#######......#####........
....####....#.........######.......####.........
...#####...###.......#######.......###..........
....###...#####.....########....................
.....#....######....#########...................
..........######.....########..................
...........####.......######...................
............##.........####......####...........
...............................######..........
................................####..........
................................................""".split("\n")

# (map column, map row) of the numbered dots for the 15 main stories.
MAP_DOTS = [(7, 5), (25, 3), (26, 8), (30, 3), (23, 4), (9, 5), (24, 4),
            (10, 6), (22, 4), (9, 6), (38, 2), (7, 4), (23, 3), (28, 6),
            (10, 5)]

FOOTER = ("Sources: Reuters, BBC, AP, AFP, The Guardian, The Kyiv Independent, "
          "Financial Times. Every story above was first reported on "
          "Tuesday 24 November 2026.")
LEGEND = ("CERTAINTY: REPORTED = carried by the day's wires  ·  CLAIM = one "
          "side's account, labelled as such  ·  FORECAST = still to happen "
          "when drawn.")
DATECHECK = ("DATE CHECK  Left out as other days' news: the ICJ Myanmar genocide "
             "ruling (19 Nov); Nvidia's Huang reinstatement (announced 23 Nov) "
             "— only the share surge is on this page; the Cikande fire started "
             "Sat 21 Nov; the Benghazi ship attack was overnight 22 Nov — only "
             "Zelensky's confirmation is on this page. Tonight's count: 36 stories.")


# ------------------------------------------------------------------ layout
# The page is built top to bottom by a FrontPage object that owns the
# canvas, the pen and the fonts, and hands each section its turn.


class FrontPage:
    def __init__(self):
        self.image = Image.new("RGB", (PAGE, PAGE), PAL["paper"])
        self.pen = ImageDraw.Draw(self.image)
        self.fonts = build_fonts()

    def font(self, name):
        return self.fonts[name]

    def masthead(self):
        pen = self.pen
        fill_rect(pen, 0, 0, PAGE, 26, PAL["navy"])
        put_text(pen, MASTHEAD, self.font("bar"), EDGE, 6, PAL["white"])
        right = MASTHEAD_RIGHT
        wide = pen.textlength(right, font=self.font("bar_small"))
        put_text(pen, right, self.font("bar_small"), PAGE - EDGE - wide, 7,
                 PAL["white"])

    def headline(self):
        pen = self.pen
        centred_text(pen, EDITION_DATE, self.font("title"), PAGE / 2, 34,
                     PAL["ink"])
        centred_text(pen, STANDFIRST, self.font("standfirst"), PAGE / 2, 96,
                     PAL["darkred"])
        seg(pen, EDGE, 122, PAGE - EDGE, 122, PAL["ink"], 2)

    def stats_row(self):
        pen = self.pen
        slot = (PAGE - 2 * EDGE) / 6
        for i, stat in enumerate(STATS):
            cx = EDGE + slot * i + slot / 2
            centred_text(pen, stat["big"], self.font("stat_num"), cx, 128,
                         PAL["darkred"])
            centred_text(pen, stat["small"], self.font("stat_lbl"), cx, 158,
                         PAL["grey"])
            if i:
                seg(pen, EDGE + slot * i, 130, EDGE + slot * i, 168,
                    PAL["rule"], 1)

    def region_bar(self):
        pen = self.pen
        total = sum(r["n"] for r in REGIONS)
        bar_y = 176
        span = PAGE - 2 * EDGE
        bx = EDGE
        for region in REGIONS:
            seg_w = span * region["n"] / total
            fill_rect(pen, bx, bar_y, seg_w, 20, region["tint"])
            label = "%s %d" % (region["name"], region["n"])
            wide = pen.textlength(label, font=self.font("region"))
            if wide < seg_w - 6:
                shown = label
            else:
                shown = str(region["n"])
                wide = pen.textlength(shown, font=self.font("region"))
            put_text(pen, shown, self.font("region"),
                     bx + (seg_w - wide) / 2, bar_y + 3, PAL["white"])
            bx += seg_w

    def timeline(self):
        pen = self.pen
        tl_y = 202
        fill_rect(pen, 0, tl_y, PAGE, 16, PAL["navy"])
        put_text(pen, TIMELINE_TITLE, self.font("time"), EDGE, tl_y + 2,
                 PAL["gold"])
        tx = EDGE + 120
        for item in TIMELINE:
            put_text(pen, item["at"], self.font("time"), tx, tl_y + 2,
                     PAL["white"])
            wide = pen.textlength(item["at"], font=self.font("time"))
            put_text(pen, item["what"], self.font("time_txt"),
                     tx + wide + 5, tl_y + 2, PAL["pale"])
            tx += wide + 5 + pen.textlength(item["what"],
                                            font=self.font("time_txt")) + 18

    def leads(self):
        pen = self.pen
        top = 226
        col_w = (PAGE - 2 * EDGE - 2 * GUTTER) // 3
        for i, lead in enumerate(LEADS):
            x = EDGE + i * (col_w + GUTTER)
            fill_rect(pen, x, top, col_w, 20, PAL["darkred"])
            centred_text(pen, lead["tag"], self.font("tag"),
                         x + col_w / 2, top + 3, PAL["white"])
            SCENES[lead["art"]](pen, x, top + 20, col_w, 96)
            y = top + 122
            put_text(pen, lead["dateline"], self.font("lead_kicker"), x, y,
                     PAL["darkred"])
            y += 16
            y = draw_para(pen, lead["head"], self.font("lead_head"), x, y,
                          col_w, 22, PAL["ink"], limit=3)
            y = draw_para(pen, lead["body"], self.font("lead_body"), x, y + 2,
                          col_w, 15, PAL["ink"], limit=3)
            put_text(pen, "(" + lead["credit"] + ")", self.font("lead_body"),
                     x, y + 2, PAL["grey"])
        return top + 246

    def story_grid(self, top):
        pen = self.pen
        cell_w = (PAGE - 2 * EDGE - 5 * 10) // 6
        cell_h = 112
        for i, story in enumerate(GRID):
            col = i % 6
            row = i // 6
            x = EDGE + col * (cell_w + 10)
            cy = top + row * cell_h
            fill_rect(pen, x, cy, cell_w, 28, story["tint"])
            MARKS[story["mark"]](pen, x + cell_w / 2 - 12, cy + 2, 24,
                                 PAL["white"])
            y = cy + 32
            put_text(pen, "%d  %s" % (i + 4, story["place"]),
                     self.font("grid_kicker"), x, y, PAL["darkred"])
            y += 12
            y = draw_para(pen, story["head"], self.font("grid_head"), x, y,
                          cell_w, 14, PAL["ink"], limit=2)
            draw_para(pen, story["summ"], self.font("grid_sum"), x, y + 1,
                      cell_w, 12, PAL["ink"], limit=2)
        return top + 2 * cell_h + 6

    def map_panel(self, top):
        pen = self.pen
        map_x = EDGE
        map_w = 300
        put_text(pen, MAP_TITLE, self.font("section"), map_x, top, PAL["ink"])
        put_text(pen, MAP_TITLE, self.font("section"), map_x, top, PAL["ink"])
        put_text(pen, MAP_NOTE, self.font("foot"), map_x + 150, top,
                 PAL["grey"])
        rows = len(MAP_ROWS)
        cols = len(MAP_ROWS[0])
        cell = map_w / cols
        my = top + 20
        for r, row in enumerate(MAP_ROWS):
            for c, ch in enumerate(row):
                if ch == '#':
                    fill_ellipse(pen, map_x + c * cell + 1, my + r * cell + 1,
                                 map_x + (c + 1) * cell - 1,
                                 my + (r + 1) * cell - 1, PAL["mapdot"])
        for n, (mc, mr) in enumerate(MAP_DOTS, start=1):
            cx = map_x + (mc + 0.5) * cell
            cy = my + (mr + 0.5) * cell
            disc(pen, cx, cy, 6, PAL["darkred"])
            num = str(n)
            wide = pen.textlength(num, font=self.font("foot"))
            put_text(pen, num, self.font("foot"), cx - wide / 2, cy - 5,
                     PAL["white"])

    def also_list(self, top):
        pen = self.pen
        ax = EDGE + 300 + 16
        aw = PAGE - EDGE - ax
        put_text(pen, ALSO_TITLE, self.font("section"), ax, top, PAL["ink"])
        col_w = (aw - 14) // 2
        ay = top + 20
        for i, item in enumerate(ALSO):
            col = i % 2
            row = i // 2
            x = ax + col * (col_w + 14)
            y = ay + row * 14
            put_text(pen, "%d  %s" % (i + 16, item), self.font("also"), x, y,
                     PAL["ink"])
        return ay + 11 * 14 + 8

    def date_check(self, box_top):
        pen = self.pen
        outline_rect(pen, EDGE, box_top, PAGE - EDGE, box_top + 34,
                     PAL["darkred"], 2)
        lines = wrap_text(pen, DATECHECK, self.font("date"),
                          PAGE - 2 * EDGE - 16)
        by = box_top + 4
        for line in lines:
            put_text(pen, line, self.font("date"), EDGE + 8, by, PAL["ink"])
            by += 13
        return box_top + 34 + 6

    def colophon(self, fy):
        pen = self.pen
        for line in wrap_text(pen, FOOTER, self.font("foot"),
                              PAGE - 2 * EDGE):
            wide = pen.textlength(line, font=self.font("foot"))
            put_text(pen, line, self.font("foot"), (PAGE - wide) / 2, fy,
                     PAL["grey"])
            fy += 12
        for line in wrap_text(pen, LEGEND, self.font("foot"),
                              PAGE - 2 * EDGE):
            wide = pen.textlength(line, font=self.font("foot"))
            put_text(pen, line, self.font("foot"), (PAGE - wide) / 2, fy,
                     PAL["grey"])
            fy += 12
        return fy

    def bottom_bar(self):
        pen = self.pen
        fill_rect(pen, 0, PAGE - 22, PAGE, 22, PAL["navy"])
        put_text(pen, MASTHEAD, self.font("bottom_bar"), EDGE, PAGE - 18,
                 PAL["white"])
        wide = pen.textlength(BOTTOM_RIGHT, font=self.font("bottom_bar"))
        put_text(pen, BOTTOM_RIGHT, self.font("bottom_bar"),
                 PAGE - EDGE - wide, PAGE - 18, PAL["white"])

    def render(self):
        self.masthead()
        self.headline()
        self.stats_row()
        self.region_bar()
        self.timeline()
        leads_bottom = self.leads()
        grid_bottom = self.story_grid(leads_bottom + 8)
        self.map_panel(grid_bottom)
        box_top = self.also_list(grid_bottom)
        fy = self.date_check(box_top)
        bottom = self.colophon(fy)
        self.bottom_bar()
        return bottom


def main():
    page = FrontPage()
    bottom = page.render()
    page.image.save("entry.png")
    with open("entry.png", "rb") as handle:
        data = handle.read()
    print("size:", page.image.size, "bottom y:", bottom)
    print("bytes:", len(data))
    print("sha256:", hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    main()
