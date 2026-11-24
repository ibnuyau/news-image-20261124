"""World news front page for Tuesday 24 November 2026.

Draws a 1024x1024 newspaper front page with Python + PIL, following the
front-page layout of the 23 November edition: a navy masthead bar, a large
date title, a red subtitle line, a row of big-number statistics, a coloured
region bar, a UTC timeline, three illustrated lead stories, twelve small
illustrated stories, a dotted world map with a numbered list of more stories,
a date-check box and a footer. Everything is drawn with real text and simple
shapes; there is no network access and no randomness, so running the script
twice writes identical bytes.
"""

import hashlib
import math

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
MARGIN = 26
INK = (28, 28, 28)
NAVY = (23, 33, 66)
RED = (178, 34, 34)
DARKRED = (139, 0, 0)
GREY = (108, 108, 108)
RULE = (196, 196, 196)
PAPER = (252, 250, 244)
CREAM = (246, 242, 232)

SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def load(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, font, max_w):
    """Split text into lines that fit max_w pixels."""
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(draw, text, font, x, y, max_w, leading, color=INK, max_lines=None):
    """Draw wrapped text, return the y just below the last line."""
    lines = wrap(draw, text, font, max_w)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += leading
    return y


def centre(draw, text, font, cx, y, color=INK):
    """Draw text centred on cx, return its width."""
    tw = draw.textlength(text, font=font)
    draw.text((cx - tw / 2, y), text, font=font, fill=color)
    return tw


# ---------------------------------------------------------------- scenes
# Each scene fills the box (x, y, w, h) with a flat colour and draws a few
# simple shapes in it. They are pictograms, not photographs.

def scene_sky(d, x, y, w, h):
    """Night sky with three missile trails and a city silhouette."""
    d.rectangle([x, y, x + w, y + h], fill=(24, 32, 58))
    for sx, sy in ((0.15, 0.25), (0.5, 0.15), (0.82, 0.3)):
        d.ellipse([x + w * sx - 2, y + h * sy - 2,
                   x + w * sx + 2, y + h * sy + 2], fill=(255, 220, 130))
    for i in range(3):
        bx = x + w * (0.12 + i * 0.28)
        bh = h * (0.35 + 0.12 * ((i * 7) % 3))
        d.rectangle([bx, y + h - bh, bx + w * 0.2, y + h], fill=(52, 62, 96))
        for wy in range(2):
            d.rectangle([bx + w * 0.04, y + h - bh + 8 + wy * 16,
                         bx + w * 0.08, y + h - bh + 14 + wy * 16],
                        fill=(255, 210, 110))
    d.line([x + w * 0.7, y + h * 0.2, x + w * 0.55, y + h * 0.55],
           fill=(255, 240, 180), width=3)
    d.line([x + w * 0.85, y + h * 0.35, x + w * 0.72, y + h * 0.6],
           fill=(255, 240, 180), width=3)


def scene_dome(d, x, y, w, h):
    """A capitol dome under a star field."""
    d.rectangle([x, y, x + w, y + h], fill=(28, 54, 96))
    for sx, sy in ((0.12, 0.2), (0.3, 0.12), (0.7, 0.18), (0.88, 0.28)):
        d.ellipse([x + w * sx - 2, y + h * sy - 2,
                   x + w * sx + 2, y + h * sy + 2], fill=(255, 255, 255))
    cx = x + w / 2
    d.rectangle([cx - w * 0.3, y + h * 0.62, cx + w * 0.3, y + h],
                fill=(240, 238, 228))
    d.polygon([(cx - w * 0.22, y + h * 0.62), (cx + w * 0.22, y + h * 0.62),
               (cx, y + h * 0.3)], fill=(240, 238, 228))
    d.rectangle([cx - 3, y + h * 0.22, cx + 3, y + h * 0.3],
                fill=(240, 238, 228))
    d.rectangle([x + w * 0.08, y + h * 0.8, x + w * 0.92, y + h],
                fill=(200, 196, 184))


def scene_chip(d, x, y, w, h):
    """A falling market line over a chip."""
    d.rectangle([x, y, x + w, y + h], fill=(16, 60, 52))
    pts = [(x + w * 0.08, y + h * 0.25), (x + w * 0.3, y + h * 0.35),
           (x + w * 0.5, y + h * 0.3), (x + w * 0.7, y + h * 0.6),
           (x + w * 0.92, y + h * 0.75)]
    d.line(pts, fill=(255, 90, 70), width=4)
    cx, cy = x + w * 0.5, y + h * 0.55
    d.rounded_rectangle([cx - w * 0.16, cy - h * 0.18, cx + w * 0.16,
                         cy + h * 0.18], radius=6,
                        fill=(30, 90, 76), outline=(150, 220, 200), width=2)
    for k in range(3):
        px = cx - w * 0.16 + k * w * 0.16
        d.line([px, cy - h * 0.18, px, cy - h * 0.3], fill=(150, 220, 200),
               width=2)
        d.line([px, cy + h * 0.18, px, cy + h * 0.3], fill=(150, 220, 200),
               width=2)


def scene_rise(d, x, y, w, h):
    """A rising market line over a chip."""
    d.rectangle([x, y, x + w, y + h], fill=(16, 60, 52))
    pts = [(x + w * 0.08, y + h * 0.75), (x + w * 0.3, y + h * 0.65),
           (x + w * 0.5, y + h * 0.7), (x + w * 0.7, y + h * 0.4),
           (x + w * 0.92, y + h * 0.25)]
    d.line(pts, fill=(90, 220, 130), width=4)
    cx, cy = x + w * 0.5, y + h * 0.55
    d.rounded_rectangle([cx - w * 0.16, cy - h * 0.18, cx + w * 0.16,
                         cy + h * 0.18], radius=6,
                        fill=(30, 90, 76), outline=(150, 220, 200), width=2)
    for k in range(3):
        px = cx - w * 0.16 + k * w * 0.16
        d.line([px, cy - h * 0.18, px, cy - h * 0.3], fill=(150, 220, 200),
               width=2)
        d.line([px, cy + h * 0.18, px, cy + h * 0.3], fill=(150, 220, 200),
               width=2)


def scene_flame(d, x, y, w, h):
    """A fire over a factory roofline."""
    d.rectangle([x, y, x + w, y + h], fill=(96, 30, 22))
    d.rectangle([x, y + h * 0.68, x + w, y + h], fill=(52, 52, 52))
    for fx in (0.25, 0.55, 0.8):
        cx = x + w * fx
        d.polygon([(cx - w * 0.07, y + h * 0.66), (cx, y + h * 0.3),
                   (cx + w * 0.07, y + h * 0.66)], fill=(255, 150, 40))
        d.polygon([(cx - w * 0.035, y + h * 0.66), (cx, y + h * 0.45),
                   (cx + w * 0.035, y + h * 0.66)], fill=(255, 220, 90))


def scene_sea(d, x, y, w, h):
    """Waves under a listing ship."""
    d.rectangle([x, y, x + w, y + h], fill=(24, 52, 84))
    d.polygon([(x + w * 0.2, y + h * 0.45), (x + w * 0.8, y + h * 0.55),
               (x + w * 0.75, y + h * 0.7), (x + w * 0.25, y + h * 0.6)],
              fill=(120, 120, 120))
    d.rectangle([x + w * 0.42, y + h * 0.3, x + w * 0.48, y + h * 0.48],
                fill=(120, 120, 120))
    for k in range(3):
        base = y + h * (0.72 + k * 0.09)
        pts = []
        for i in range(13):
            px = x + w * 0.05 + (w * 0.9) * i / 12
            py = base + 3 * math.sin(i * math.pi / 3)
            pts.append((px, py))
        d.line(pts, fill=(140, 190, 230), width=2)


def scene_globe(d, x, y, w, h):
    """A globe on a teal field."""
    d.rectangle([x, y, x + w, y + h], fill=(22, 96, 88))
    cx, cy, r = x + w / 2, y + h / 2, min(w, h) * 0.32
    d.ellipse([cx - r, cy - r, cx + r, cy + r],
              outline=(240, 240, 230), width=3)
    d.ellipse([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r],
              outline=(240, 240, 230), width=2)
    d.line([x + w * 0.18, cy, x + w * 0.82, cy], fill=(240, 240, 230),
           width=2)


# ---------------------------------------------------------------- small icons
# Each draws inside the square (x, y, s) in the given colour.

def ico_quake(d, x, y, s, c):
    cx, cy = x + s / 2, y + s / 2
    pts = [(cx - s * 0.35, cy + s * 0.3), (cx - s * 0.12, cy - s * 0.15),
           (cx + s * 0.05, cy + s * 0.2), (cx + s * 0.18, cy - s * 0.3),
           (cx + s * 0.35, cy + s * 0.1)]
    d.line(pts, fill=c, width=3)


def ico_gavel(d, x, y, s, c):
    d.rectangle([x + s * 0.15, y + s * 0.2, x + s * 0.75, y + s * 0.38],
                outline=c, width=3)
    d.line([x + s * 0.45, y + s * 0.38, x + s * 0.45, y + s * 0.75],
           fill=c, width=3)
    d.line([x + s * 0.2, y + s * 0.78, x + s * 0.7, y + s * 0.78],
           fill=c, width=3)


def ico_robot(d, x, y, s, c):
    d.rounded_rectangle([x + s * 0.18, y + s * 0.22, x + s * 0.82,
                         y + s * 0.78], radius=s * 0.08, outline=c, width=3)
    d.line([x + s * 0.5, y + s * 0.22, x + s * 0.5, y + s * 0.08],
           fill=c, width=3)
    d.ellipse([x + s * 0.45, y + s * 0.02, x + s * 0.55, y + s * 0.12],
              fill=c)
    d.ellipse([x + s * 0.32, y + s * 0.38, x + s * 0.42, y + s * 0.48],
              fill=c)
    d.ellipse([x + s * 0.58, y + s * 0.62, x + s * 0.68, y + s * 0.72],
              fill=c)


def ico_cross(d, x, y, s, c):
    cx, cy = x + s / 2, y + s / 2
    d.ellipse([cx - s * 0.4, cy - s * 0.4, cx + s * 0.4, cy + s * 0.4],
              outline=c, width=3)
    d.rectangle([cx - s * 0.07, cy - s * 0.25, cx + s * 0.07,
                 cy + s * 0.25], fill=c)
    d.rectangle([cx - s * 0.25, cy - s * 0.07, cx + s * 0.25,
                 cy + s * 0.07], fill=c)


def ico_cup(d, x, y, s, c):
    d.polygon([(x + s * 0.2, y + s * 0.25), (x + s * 0.8, y + s * 0.25),
               (x + s * 0.68, y + s * 0.75), (x + s * 0.32, y + s * 0.75)],
              outline=c, width=3)
    d.line([x + s * 0.5, y + s * 0.25, x + s * 0.5, y + s * 0.08],
           fill=c, width=3)
    d.line([x + s * 0.25, y + s * 0.85, x + s * 0.75, y + s * 0.85],
           fill=c, width=3)


def ico_chart(d, x, y, s, c):
    for i, bh in enumerate((0.25, 0.45, 0.3, 0.6)):
        bx = x + s * (0.12 + i * 0.22)
        d.rectangle([bx, y + s * (0.85 - bh), bx + s * 0.14, y + s * 0.85],
                    fill=c)


def ico_ring(d, x, y, s, c):
    cx, cy = x + s / 2, y + s / 2
    d.ellipse([cx - s * 0.32, cy - s * 0.32, cx + s * 0.32, cy + s * 0.32],
              outline=c, width=3)
    d.ellipse([cx - s * 0.1, cy - s * 0.1, cx + s * 0.1, cy + s * 0.1],
              fill=c)


def ico_bolt(d, x, y, s, c):
    d.polygon([(x + s * 0.55, y + s * 0.05), (x + s * 0.3, y + s * 0.55),
               (x + s * 0.48, y + s * 0.55), (x + s * 0.42, y + s * 0.95),
               (x + s * 0.72, y + s * 0.42), (x + s * 0.52, y + s * 0.42)],
              fill=c)


def ico_plane(d, x, y, s, c):
    d.polygon([(x + s * 0.1, y + s * 0.55), (x + s * 0.9, y + s * 0.4),
               (x + s * 0.9, y + s * 0.55), (x + s * 0.5, y + s * 0.62)],
              outline=c, width=2)
    d.polygon([(x + s * 0.45, y + s * 0.55), (x + s * 0.6, y + s * 0.3),
               (x + s * 0.68, y + s * 0.55)], fill=c)


def ico_megaphone(d, x, y, s, c):
    d.polygon([(x + s * 0.12, y + s * 0.42), (x + s * 0.85, y + s * 0.18),
               (x + s * 0.85, y + s * 0.66), (x + s * 0.12, y + s * 0.58)],
              outline=c, width=3)
    d.line([x + s * 0.3, y + s * 0.58, x + s * 0.24, y + s * 0.85],
           fill=c, width=3)


def ico_star(d, x, y, s, c):
    cx, cy = x + s / 2, y + s / 2
    pts = []
    for i in range(10):
        r = s * 0.46 if i % 2 == 0 else s * 0.19
        a = math.pi * i / 5 - math.pi / 2
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, outline=c, width=2)


def ico_flag(d, x, y, s, c):
    d.rectangle([x + s * 0.1, y + s * 0.15, x + s * 0.9, y + s * 0.85],
                fill=c)
    d.line([x + s * 0.1, y + s * 0.15, x + s * 0.1, y + s * 0.98],
           fill=c, width=3)


def ico_globe(d, x, y, s, c):
    cx, cy, r = x + s / 2, y + s / 2, s * 0.42
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=3)
    d.ellipse([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r], outline=c,
              width=2)
    d.line([x + s * 0.1, cy, x + s * 0.9, cy], fill=c, width=2)


def ico_flame(d, x, y, s, c):
    cx = x + s / 2
    d.polygon([(cx - s * 0.28, y + s * 0.85), (cx, y + s * 0.08),
               (cx + s * 0.28, y + s * 0.85)], fill=c)
    d.polygon([(cx - s * 0.12, y + s * 0.85), (cx, y + s * 0.4),
               (cx + s * 0.12, y + s * 0.85)], fill=(255, 255, 255))


def ico_sea(d, x, y, s, c):
    for k in range(3):
        base = y + s * (0.25 + k * 0.25)
        pts = []
        for i in range(11):
            px = x + s * 0.05 + (s * 0.9) * i / 10
            py = base + s * 0.05 * math.sin(i * math.pi / 2.5)
            pts.append((px, py))
        d.line(pts, fill=c, width=2)


def ico_drone(d, x, y, s, c):
    """A small quadcopter drone."""
    cx, cy = x + s / 2, y + s / 2
    d.rectangle([cx - s * 0.12, cy - s * 0.1, cx + s * 0.12, cy + s * 0.1],
                fill=c)
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        rx = cx + dx * s * 0.32
        ry = cy + dy * s * 0.28
        d.line([cx, cy, rx, ry], fill=c, width=2)
        d.ellipse([rx - s * 0.09, ry - s * 0.05, rx + s * 0.09,
                   ry + s * 0.05], outline=c, width=2)


# ---------------------------------------------------------------- stories
# Every story below was first reported on Tuesday 24 November 2026.

LEADS = [
    ("NVIDIA SHARES SOAR 31%", scene_rise,
     "1  SANTA CLARA, USA  ·  MARKETS",
     "Nvidia shares soar 31% as Huang returns",
     "Nvidia shares jumped 31% in a day after the board reinstated Jensen "
     "Huang as chief executive, lifting the S&P 500 4.73% and Japan's "
     "Nikkei 3.91%.",
     "One Turn, Reuters"),
    ("RUSSIA WARNS ESTONIA OF OPEN WAR", scene_sky,
     "2  TALLINN, ESTONIA  ·  NATO",
     "Russia warns Estonia of 'open war'",
     "Moscow said Estonia's decision to close its border for six months "
     "from 1 December was 'on the verge of triggering open war', after "
     "accusing Russian agents of targeting an Estonian firm.",
     "Reuters, Medium"),
    ("UKRAINE SINKS RUSSIAN WARSHIP", scene_sea,
     "3  BENGHAZI, LIBYA  ·  CONFLICT",
     "Zelensky confirms sinking of Russian corvette",
     "President Zelensky confirmed Ukraine used seven naval drones to sink "
     "the Russian corvette Merkury at Benghazi port. The Kremlin warned of "
     "'painful consequences'.",
     "The Guardian, BBC"),
]

GRID = [
    ("MOSCOW · NUCLEAR", "Medvedev: nuclear strike 'considered'",
     "Medvedev says Ukraine and NATO created cases for a nuclear strike.",
     ico_flame, (178, 34, 34)),
    ("BRUSSELS · SPACE", "NATO vows to defend space from threats",
     "Rutte vows defence after reports of a Russian nuclear satellite.",
     ico_star, (28, 54, 96)),
    ("WASHINGTON · ARMS", "US delays Patriot missiles for Ukraine",
     "US delays ~60 Patriot interceptors; Hegseth has not approved them.",
     ico_plane, (90, 90, 90)),
    ("WARSAW · AIRSPACE", "Russian drone enters Polish airspace",
     "Drone briefly enters Poland in a strike on Ukraine; 2nd violation.",
     ico_drone, (178, 34, 34)),
    ("USA · TECH", "US states sue Musk firms over Grok images",
     "Oregon and Virginia sue SpaceX over Grok child-abuse images.",
     ico_robot, (52, 62, 96)),
    ("PARIS · PHARMA", "Sanofi buys Insmed for $41bn",
     "Sanofi agrees to buy US biotech Insmed; biggest deal in 3 years.",
     ico_chart, (16, 60, 52)),
    ("USA · HEALTH", "US loses measles elimination status",
     "US loses measles elimination status after more than 25 years.",
     ico_cross, (178, 34, 34)),
    ("SPACE · SCIENCE", "Astronomers find most distant black hole",
     "A quasar from 630m years after the Big Bang is the most distant yet.",
     ico_ring, (28, 54, 96)),
    ("USA · AI", "Amazon acquires Decart AI for $7.5bn",
     "Amazon agrees to buy Decart AI to boost AWS chip efficiency.",
     ico_robot, (22, 96, 88)),
    ("BERLIN · DEFENCE", "Germany first to access Ukraine's Delta",
     "Germany becomes first country to access Ukraine's Delta system.",
     ico_flag, (28, 90, 130)),
    ("BAGHDAD · OIL", "Iraq PM orders takeover of Kurdish oilfields",
     "Iraq's PM orders the oil ministry to manage Kurdish-area fields.",
     ico_bolt, (196, 130, 30)),
    ("USA · HEALTH", "FDA approves first limb-girdle drug",
     "FDA approves BridgeBio's drug, first for limb-girdle dystrophy.",
     ico_cross, (16, 60, 52)),
]

ALSO = [
    "Israeli airstrikes kill at least six in Gaza.",
    "UN mission in Libya urges probe into Benghazi port attacks.",
    "Heavy fighting in Ituri traps DR Congo Ebola teams, WHO says.",
    "Seven countries back EU push to limit Russian visas.",
    "Car bomb hits governor's office in Villavicencio, Colombia.",
    "Mexico to try 'Chapo Isidro' despite US request.",
    "Sheikh Hasina plans return to Bangladesh on Dec. 16.",
    "Nepal PM visits India; India pledges 1.4bn euros.",
    "Qatar PM seeks to revive US-Iran talks.",
    "EU proposes 22nd sanctions package, sports ban included.",
    "Spain's Supreme Court amnesties Carles Puigdemont.",
    "DR Congo says military aircraft missing; rebels claim shootdown.",
    "Indonesia factory fire toll rises to 26, dozens missing.",
    "Strikes on Yemen buses and trucks kill about 25.",
    "Brazil's real weakens as growth forecast is cut.",
    "Kushner says he urged Trump to ease pressure on Zelensky.",
    "Ukraine defence minister meets Norway counterpart in Oslo.",
    "UN: Gaza war undid 77 years of human development.",
    "UN chief urges talks on global AI safety rules.",
    "47,000 women killed by partners or relatives in 2025.",
    "Somalia and Uganda to step up operations against Al-Shabaab.",
]

STATS = [
    ("31%", "Nvidia shares jump in a day"),
    ("$41bn", "Sanofi buys Insmed"),
    ("60", "Patriot missiles delayed"),
    ("7", "drones sank Russian corvette"),
    ("700k", "Russian soldiers killed, analysis"),
    ("47,000", "women killed by relatives in 2025"),
]

REGIONS = [
    ("EUROPE", 10, (28, 90, 130)),
    ("MIDDLE EAST", 5, (178, 34, 34)),
    ("AMERICAS", 10, (28, 54, 96)),
    ("ASIA-PACIFIC", 3, (196, 130, 30)),
    ("AFRICA", 5, (34, 120, 70)),
    ("WORLD", 3, (90, 90, 90)),
]

TIMELINE = [
    ("07:39", "NATO vows space defence"),
    ("08:39", "Ukraine minister meets Norway"),
    ("09:37", "Kremlin warns of consequences"),
    ("09:40", "Kushner urged Trump to ease pressure"),
]

# A coarse dotted world map: '#' is land, '.' is ocean.
MAP_ROWS = [
    "................................................",
    "...#####....####......##################........",
    "..########..######..########################....",
    ".##########..#####.##########################...",
    "..#########...###...#######################....",
    "...#######.....#.....##########..#########......",
    "....#####.............########....#######.......",
    ".....###..............#######......#####........",
    "....####....#.........######.......####.........",
    "...#####...###.......#######.......###..........",
    "....###...#####.....########....................",
    ".....#....######....#########...................",
    "..........######.....########..................",
    "...........####.......######...................",
    "............##.........####......####...........",
    "...............................######..........",
    "................................####..........",
    "................................................",
]

# (map column, map row) of the numbered dots for the 15 main stories.
MAP_DOTS = [
    (7, 5), (25, 3), (26, 8), (30, 3), (23, 4),
    (9, 5), (24, 4), (10, 6), (22, 4), (9, 6),
    (38, 2), (7, 4), (23, 3), (28, 6), (10, 5),
]

FOOTER = ("Sources: Reuters, BBC, AP, AFP, The Guardian, The Kyiv "
          "Independent, Financial Times. Every story above was first "
          "reported on Tuesday 24 November 2026.")
LEGEND = ("CERTAINTY: REPORTED = carried by the day's wires  ·  "
          "CLAIM = one side's account, labelled as such  ·  "
          "FORECAST = still to happen when drawn.")
DATECHECK = ("DATE CHECK  Left out as other days' news: the ICJ Myanmar "
             "genocide ruling (19 Nov); Nvidia's Huang reinstatement "
             "(announced 23 Nov) — only the share surge is on this page; "
             "the Cikande fire started Sat 21 Nov; the Benghazi ship "
             "attack was overnight 22 Nov — only Zelensky's confirmation "
             "is on this page. Tonight's count: 36 stories.")


# ---------------------------------------------------------------- layout

def draw_page():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    f_bar = load(SANS_B, 13)
    f_bar_s = load(SANS, 11)
    f_title = load(SERIF_B, 58)
    f_sub = load(SERIF_I, 17)
    f_stat_n = load(SERIF_B, 26)
    f_stat_l = load(SANS, 10)
    f_reg = load(SANS_B, 12)
    f_time = load(SANS_B, 11)
    f_time_s = load(SANS, 11)
    f_tag = load(SANS_B, 12)
    f_lead_k = load(SANS_B, 11)
    f_lead_h = load(SERIF_B, 19)
    f_lead_b = load(SANS, 12)
    f_gk = load(SANS_B, 10)
    f_gh = load(SERIF_B, 13)
    f_gs = load(SANS, 11)
    f_sec = load(SANS_B, 13)
    f_also = load(SANS, 11)
    f_date = load(SANS_B, 11)
    f_foot = load(SANS, 10)

    # ---- top navy bar
    d.rectangle([0, 0, W, 26], fill=NAVY)
    d.text((MARGIN, 6), "THE WORLD IN ONE DAY", font=f_bar, fill=(255, 255, 255))
    right = "36 STORIES  ·  6 REGIONS  ·  EVERY ONE DATED TUESDAY 24 NOVEMBER 2026"
    rw = d.textlength(right, font=f_bar_s)
    d.text((W - MARGIN - rw, 7), right, font=f_bar_s, fill=(255, 255, 255))

    # ---- big date title
    centre(d, "Tuesday 24 November 2026", f_title, W / 2, 34, INK)

    # ---- red subtitle line
    sub = ("Nvidia shares soar 31% as Huang returns  ·  Russia warns "
           "Estonia of 'open war'  ·  Ukraine sinks Russian warship")
    centre(d, sub, f_sub, W / 2, 96, DARKRED)
    d.line([MARGIN, 122, W - MARGIN, 122], fill=INK, width=2)

    # ---- stats row
    col_w = (W - 2 * MARGIN) / 6
    for i, (num, label) in enumerate(STATS):
        cx = MARGIN + col_w * i + col_w / 2
        centre(d, num, f_stat_n, cx, 128, DARKRED)
        centre(d, label, f_stat_l, cx, 158, GREY)
        if i:
            d.line([MARGIN + col_w * i, 130, MARGIN + col_w * i, 168],
                   fill=RULE, width=1)

    # ---- region bar
    total = sum(c for _, c, _ in REGIONS)
    bar_y = 176
    bx = MARGIN
    bar_w = W - 2 * MARGIN
    for name, count, color in REGIONS:
        seg_w = bar_w * count / total
        d.rectangle([bx, bar_y, bx + seg_w, bar_y + 20], fill=color)
        label = "%s %d" % (name, count)
        lw = d.textlength(label, font=f_reg)
        if lw < seg_w - 6:
            d.text((bx + (seg_w - lw) / 2, bar_y + 3), label, font=f_reg,
                   fill=(255, 255, 255))
        else:
            num = str(count)
            nw = d.textlength(num, font=f_reg)
            d.text((bx + (seg_w - nw) / 2, bar_y + 3), num, font=f_reg,
                   fill=(255, 255, 255))
        bx += seg_w

    # ---- UTC timeline
    tl_y = 202
    d.rectangle([0, tl_y, W, tl_y + 16], fill=NAVY)
    d.text((MARGIN, tl_y + 2), "THE DAY IN UTC", font=f_time,
           fill=(255, 220, 130))
    tx = MARGIN + 120
    for t, ev in TIMELINE:
        d.text((tx, tl_y + 2), t, font=f_time, fill=(255, 255, 255))
        tw = d.textlength(t, font=f_time)
        d.text((tx + tw + 5, tl_y + 2), ev, font=f_time_s,
               fill=(220, 220, 220))
        tx += tw + 5 + d.textlength(ev, font=f_time_s) + 18

    return img, d, (f_tag, f_lead_k, f_lead_h, f_lead_b, f_gk, f_gh, f_gs,
                    f_sec, f_also, f_date, f_foot)


def draw_rest(img, d, fonts):
    (f_tag, f_lead_k, f_lead_h, f_lead_b, f_gk, f_gh, f_gs,
     f_sec, f_also, f_date, f_foot) = fonts

    # ---- three lead stories
    lead_top = 226
    lead_w = (W - 2 * MARGIN - 2 * 14) // 3
    lead_h = 246
    for i, (tag, scene, kicker, head, body, src) in enumerate(LEADS):
        x = MARGIN + i * (lead_w + 14)
        # tag bar
        d.rectangle([x, lead_top, x + lead_w, lead_top + 20], fill=DARKRED)
        tw = d.textlength(tag, font=f_tag)
        d.text((x + (lead_w - tw) / 2, lead_top + 3), tag, font=f_tag,
               fill=(255, 255, 255))
        # illustration
        scene(d, x, lead_top + 20, lead_w, 96)
        # kicker + headline + body
        y = lead_top + 122
        d.text((x, y), kicker, font=f_lead_k, fill=DARKRED)
        y += 16
        y = para(d, head, f_lead_h, x, y, lead_w, 22, max_lines=3)
        y = para(d, body, f_lead_b, x, y + 2, lead_w, 15, max_lines=3)
        d.text((x, y + 2), "(" + src + ")", font=f_lead_b, fill=GREY)

    # ---- twelve small stories, two rows of six
    grid_top = lead_top + lead_h + 8
    cell_w = (W - 2 * MARGIN - 5 * 10) // 6
    cell_h = 112
    for i, (kicker, head, summ, icon, banner) in enumerate(GRID):
        col = i % 6
        row = i // 6
        x = MARGIN + col * (cell_w + 10)
        cy = grid_top + row * cell_h
        # small illustration banner
        d.rectangle([x, cy, x + cell_w, cy + 28], fill=banner)
        icon(d, x + cell_w / 2 - 12, cy + 2, 24, (255, 255, 255))
        # number + kicker
        y = cy + 32
        d.text((x, y), "%d  %s" % (i + 4, kicker), font=f_gk, fill=DARKRED)
        y += 12
        y = para(d, head, f_gh, x, y, cell_w, 14, max_lines=2)
        para(d, summ, f_gs, x, y + 1, cell_w, 12, max_lines=2)

    return grid_top + 2 * cell_h + 6


def draw_bottom(img, d, fonts, top):
    (f_tag, f_lead_k, f_lead_h, f_lead_b, f_gk, f_gh, f_gs,
     f_sec, f_also, f_date, f_foot) = fonts

    # ---- world map + also list
    map_x = MARGIN
    map_w = 300
    map_top = top
    d.text((map_x, map_top), "WHERE IT HAPPENED", font=f_sec, fill=INK)
    d.text((map_x, map_top), "WHERE IT HAPPENED", font=f_sec, fill=INK)
    d.text((map_x + 150, map_top), "pins match story numbers", font=f_foot,
           fill=GREY)
    # dotted map
    rows = len(MAP_ROWS)
    cols = len(MAP_ROWS[0])
    cell = map_w / cols
    my = map_top + 20
    for r, row in enumerate(MAP_ROWS):
        for c, ch in enumerate(row):
            if ch == '#':
                d.ellipse([map_x + c * cell + 1, my + r * cell + 1,
                           map_x + (c + 1) * cell - 1,
                           my + (r + 1) * cell - 1], fill=(120, 120, 120))
    # numbered dots for the 15 main stories
    for n, (mc, mr) in enumerate(MAP_DOTS, start=1):
        cx = map_x + (mc + 0.5) * cell
        cy = my + (mr + 0.5) * cell
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=DARKRED)
        num = str(n)
        nw = d.textlength(num, font=f_foot)
        d.text((cx - nw / 2, cy - 5), num, font=f_foot,
               fill=(255, 255, 255))

    # also list, two columns to the right of the map
    ax = map_x + map_w + 16
    aw = W - MARGIN - ax
    d.text((ax, map_top), "ALSO ON TUESDAY 24 NOVEMBER  —  21 MORE STORIES",
           font=f_sec, fill=INK)
    col_w = (aw - 14) // 2
    ay = map_top + 20
    for i, item in enumerate(ALSO):
        col = i % 2
        row = i // 2
        x = ax + col * (col_w + 14)
        y = ay + row * 14
        d.text((x, y), "%d  %s" % (i + 16, item), font=f_also, fill=INK)

    # ---- date check box
    box_top = ay + 11 * 14 + 8
    d.rectangle([MARGIN, box_top, W - MARGIN, box_top + 34],
                outline=DARKRED, width=2)
    lines = wrap(d, DATECHECK, f_date, W - 2 * MARGIN - 16)
    by = box_top + 4
    for line in lines:
        d.text((MARGIN + 8, by), line, font=f_date, fill=INK)
        by += 13

    # ---- footer
    fy = box_top + 34 + 6
    flines = wrap(d, FOOTER, f_foot, W - 2 * MARGIN)
    for line in flines:
        lw = d.textlength(line, font=f_foot)
        d.text(((W - lw) / 2, fy), line, font=f_foot, fill=GREY)
        fy += 12
    llines = wrap(d, LEGEND, f_foot, W - 2 * MARGIN)
    for line in llines:
        lw = d.textlength(line, font=f_foot)
        d.text(((W - lw) / 2, fy), line, font=f_foot, fill=GREY)
        fy += 12

    # ---- bottom navy bar
    d.rectangle([0, H - 22, W, H], fill=NAVY)
    f_bar = load(SANS_B, 12)
    d.text((MARGIN, H - 18), "THE WORLD IN ONE DAY", font=f_bar,
           fill=(255, 255, 255))
    right = "TUESDAY 24 NOVEMBER 2026  ·  ONE PAGE"
    rw = d.textlength(right, font=f_bar)
    d.text((W - MARGIN - rw, H - 18), right, font=f_bar,
           fill=(255, 255, 255))
    return fy


def main():
    img, d, fonts = draw_page()
    mid = draw_rest(img, d, fonts)
    bottom = draw_bottom(img, d, fonts, mid)
    img.save("entry.png")
    data = open("entry.png", "rb").read()
    print("size:", img.size, "bottom y:", bottom)
    print("bytes:", len(data))
    print("sha256:", hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    main()
