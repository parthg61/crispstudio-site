#!/usr/bin/env python3
"""Recolour + crop the hand-drawn Idli/Samosa SVGs into the Crisp palette.

usage: python3 tools/recolour_cats.py <folder with the V1_*.svg sources>
writes assets/illustrations/<name>.svg. One rule set for every file (see recolour()),
so the same fur / eyes / ears / nose read the same everywhere. VIEWBOX holds each
file's content box (browser getBBox union of visible shapes, +2% padding).
"""
import colorsys
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "illustrations"

NAVY, MUTED, WHITE, GREY = "#021F53", "#4A5675", "#FFFFFF", "#DEDEDA"
CREAM, ORANGE, RUST, GREEN = "#FECA98", "#FD9F0F", "#CC4806", "#4DAF6B"

# source file -> (output name, title, avatar disc colour or None)
SOURCES = {
    "V1_Idli Avatar.svg": ("idli-avatar", "Idli the cat, avatar", ORANGE),
    "V1_Idli Confused.svg": ("idli-confused", "Idli sitting, looking confused", None),
    "V1_Idli Lying.svg": ("idli-lying", "Idli lying on her side", None),
    "V1_Idli Sleeping.svg": ("idli-sleeping", "Idli curled up asleep", None),
    "V1_Idli on a hamock.svg": ("idli-hammock", "Idli lounging in a hammock", None),
    "V1_Samosa avatar.svg": ("samosa-avatar", "Samosa the cat, avatar", CREAM),
    "V1_Samosa with a Ball.svg": ("samosa-ball", "Samosa playing with a ball", None),
    "V1_Samosa Being Sexy.svg": ("samosa-sitting", "Samosa sitting", None),
}

VIEWBOX = {
    "idli-avatar": "-38 -38 1997 1997",
    "idli-confused": "184 180 1693 1581",
    "idli-lying": "197 458 1716 1250",
    "idli-sleeping": "237 418 1447 1075",
    "idli-hammock": "276 0 1422 1916",  # no top padding: the rope must meet the card's top edge
    "samosa-avatar": "-38 -43 1997 2002",
    "samosa-ball": "17 587 1883 938",
    "samosa-sitting": "304 352 1255 1552",
}

# per-file class overrides: {name: {"cls-N": colour}} (judgment calls after looking at renders)
CLASS_OVERRIDES = {}

# per-file shape overrides: {name: {colour: [indices of path/polygon/rect/circle in document order]}}.
# idli-confused: the user wants Idli's hind legs white (the folded back leg down to the toe-pad paw);
# 242/246/247 are the thigh and shin fur, 248/228/249/251 small fur marks on it; 227 (the shadow where the
# thigh meets the front leg) and 244 (the band under the leg) become the usual light shading.
SHAPE_OVERRIDES = {
    # raised hind leg (the one with the toe beans): 229 the leg, 230 a fur patch on it; 233 its back shadow and
    # 159/231/235/236/237 small fur marks become light shading. The toe pads stay as drawn.
    "idli-confused": {WHITE: [242, 246, 247, 248, 228, 249, 251, 229, 230], GREY: [227, 244, 233, 159, 231, 235, 236, 237]},
}
# white underlays drawn right after the disc (shape 0), under all the line art: Samosa's muzzle, chin, chest and
# paws are holes in the drawing that would show the cream disc. "head" fills the outer contour of shape 25
# (his head fur); POINTS is his body silhouette from y 640 down (a browser scan of the fur shapes' left/right
# extents every 6 units, inset 4), so no white reaches past his outline.
SAMOSA_BODY = (
    "457,640 457,646 457,652 457,658 460,664 460,670 460,676 463,682 463,688 463,694 466,700 466,706 "
    "469,712 469,718 472,724 475,730 475,736 478,742 481,748 484,754 484,760 481,766 478,772 478,778 "
    "475,784 472,790 472,796 469,802 469,808 466,814 466,820 463,826 463,832 460,838 460,844 460,850 "
    "457,856 457,862 457,868 454,874 454,880 454,886 454,892 454,898 451,904 451,910 451,916 451,922 "
    "451,928 451,934 451,940 451,946 451,952 451,958 451,964 451,970 451,976 451,982 454,988 454,994 "
    "454,1000 454,1006 457,1012 457,1018 457,1024 460,1030 460,1036 463,1042 463,1048 466,1054 466,1060 "
    "469,1066 472,1072 472,1078 475,1084 478,1090 481,1096 529,1102 490,1108 490,1114 493,1120 496,1126 "
    "502,1132 505,1138 508,1144 511,1150 514,1156 517,1162 520,1168 523,1174 526,1180 532,1186 529,1192 "
    "532,1198 532,1204 532,1210 535,1216 535,1222 535,1228 535,1234 535,1240 535,1246 535,1252 535,1258 "
    "535,1264 532,1270 532,1276 532,1282 529,1288 529,1294 532,1300 526,1306 523,1312 523,1318 520,1324 "
    "517,1330 517,1336 514,1342 514,1348 511,1354 508,1360 508,1366 505,1372 505,1378 502,1384 499,1390 "
    "499,1396 496,1402 493,1408 493,1414 490,1420 487,1426 487,1432 484,1438 481,1444 481,1450 478,1456 "
    "478,1462 475,1468 472,1474 472,1480 469,1486 469,1492 466,1498 466,1504 463,1510 463,1516 460,1522 "
    "460,1528 457,1534 457,1540 454,1546 454,1552 451,1558 448,1564 439,1570 433,1576 427,1582 421,1588 "
    "415,1594 412,1600 406,1606 400,1612 397,1618 391,1624 388,1630 385,1636 382,1642 379,1648 376,1654 "
    "373,1660 370,1666 367,1672 364,1678 361,1684 358,1690 358,1696 355,1702 364,1708 370,1714 379,1720 "
    "385,1726 394,1732 400,1738 409,1744 418,1750 427,1756 436,1762 445,1768 454,1774 463,1780 475,1786 "
    "484,1792 496,1798 508,1804 517,1810 529,1816 544,1822 556,1828 568,1834 577,1840 580,1846 583,1852 "
    "589,1858 592,1864 598,1870 604,1876 610,1882 619,1888 634,1894 679,1900 694,1906 841,1912 1082,1912 "
    "1226,1906 1244,1900 1286,1894 1301,1888 1310,1882 1316,1876 1322,1870 1328,1864 1334,1858 1337,1852 "
    "1340,1846 1343,1840 1352,1834 1364,1828 1376,1822 1388,1816 1400,1810 1412,1804 1424,1798 1433,1792 "
    "1445,1786 1454,1780 1463,1774 1475,1768 1484,1762 1493,1756 1502,1750 1508,1744 1517,1738 1526,1732 "
    "1535,1726 1541,1720 1550,1714 1556,1708 1562,1702 1562,1696 1562,1690 1559,1684 1556,1678 1553,1672 "
    "1550,1666 1547,1660 1544,1654 1541,1648 1538,1642 1535,1636 1532,1630 1529,1624 1523,1618 1520,1612 "
    "1514,1606 1511,1600 1505,1594 1499,1588 1493,1582 1487,1576 1481,1570 1472,1564 1469,1558 1469,1552 "
    "1466,1546 1466,1540 1463,1534 1463,1528 1460,1522 1460,1516 1457,1510 1457,1504 1454,1498 1454,1492 "
    "1451,1486 1451,1480 1448,1474 1445,1468 1445,1462 1442,1456 1439,1450 1439,1444 1436,1438 1433,1432 "
    "1433,1426 1430,1420 1427,1414 1427,1408 1424,1402 1424,1396 1421,1390 1418,1384 1418,1378 1415,1372 "
    "1412,1366 1412,1360 1409,1354 1406,1348 1406,1342 1403,1336 1397,1330 1388,1324 1397,1318 1397,1312 "
    "1394,1306 1394,1300 1394,1294 1391,1288 1391,1282 1388,1276 1388,1270 1388,1264 1388,1258 1388,1252 "
    "1385,1246 1385,1240 1385,1234 1385,1228 1385,1222 1388,1216 1388,1210 1388,1204 1391,1198 1391,1192 "
    "1391,1186 1391,1180 1394,1174 1394,1168 1397,1162 1397,1156 1400,1150 1403,1144 1406,1138 1409,1132 "
    "1412,1126 1415,1120 1418,1114 1403,1108 1424,1102 1427,1096 1430,1090 1433,1084 1436,1078 1436,1072 "
    "1439,1066 1442,1060 1442,1054 1445,1048 1445,1042 1448,1036 1451,1030 1451,1024 1451,1018 1454,1012 "
    "1454,1006 1454,1000 1454,994 1457,988 1457,982 1457,976 1457,970 1457,964 1457,958 1457,952 1457,946 "
    "1457,940 1457,934 1457,928 1457,922 1457,916 1457,910 1457,904 1454,898 1454,892 1454,886 1454,880 "
    "1454,874 1451,868 1451,862 1451,856 1448,850 1448,844 1445,838 1445,832 1445,826 1442,820 1442,814 "
    "1439,808 1439,802 1436,796 1436,790 1433,784 1430,778 1430,772 1427,766 1427,760 1424,754 1427,748 "
    "1430,742 1433,736 1436,730 1439,724 1439,718 1442,712 1442,706 1445,700 1445,694 1445,688 1448,682 "
    "1448,676 1448,670 1448,664 1451,658 1451,652 1451,646 1454,640 "
)
UNDERLAYS = {"samosa-avatar": {"head": 25, "points": SAMOSA_BODY}}

# shapes that get a navy outline copy drawn right after them (white leg against white belly fur)
OUTLINES = {"idli-confused": [229]}


def hsl(hexs):
    h = hexs.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, light, sat = colorsys.rgb_to_hls(r, g, b)
    return hue * 360, sat, light


PALETTE = {NAVY, MUTED, WHITE, GREY, CREAM, ORANGE, RUST, GREEN}


def recolour(hexs, disc):
    if hexs.upper() in PALETTE:  # already converted (style pass runs before the inline pass)
        return hexs.upper()
    h, s, l = hsl(hexs)
    if 70 <= h <= 170 and s >= 0.15:
        return (disc or WHITE) if l >= 0.8 else GREEN
    if s < 0.18 or (20 <= h < 65 and s < 0.35):  # greys, tan/brown low-sat shading
        if l >= 0.92 or (l >= 0.85 and 20 <= h < 65):
            return WHITE
        if l >= 0.62:
            return GREY
        if l >= 0.38:
            return MUTED
        return NAVY
    if h < 20 or h > 330:
        if l >= 0.65:
            return CREAM
        return RUST if l >= 0.3 else NAVY
    if 20 <= h < 65:
        return WHITE if l >= 0.85 else ORANGE
    if 170 < h <= 260:
        return WHITE if l >= 0.85 else NAVY
    return NAVY if l < 0.5 else GREY


def convert(src, name, title, disc):
    text = src.read_text(encoding="utf-8")
    text = re.sub(r"<\?xml[^>]*>\s*", "", text)
    text = re.sub(r"<!--.*?-->\s*", "", text, flags=re.S)
    text = re.sub(r'\s(?:data-name|id)="[^"]*"', "", text)
    over = CLASS_OVERRIDES.get(name, {})

    def style_rule(m):
        cls, body = m.group(1), m.group(2)
        if cls in over:
            return f".{cls}{{fill:{over[cls]}}}"
        body = re.sub(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", lambda c: recolour(c.group(0), disc), body)
        return f".{cls}{{{' '.join(body.split())}}}"

    text = re.sub(r"\.(cls-\d+)\s*\{([^}]*)\}", style_rule, text)
    text = re.sub(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", lambda c: recolour(c.group(0), disc), text)  # inline attrs
    shapes = {i: c for c, ids in SHAPE_OVERRIDES.get(name, {}).items() for i in ids}
    if shapes:
        n = iter(range(10 ** 6))

        def shape(m):
            i = next(n)
            if i not in shapes:
                return m.group(0)
            el = re.sub(r'\sclass="[^"]*"', "", m.group(0))
            out = el.replace(m.group(1), f'{m.group(1)} fill="{shapes[i]}"', 1)
            if i in OUTLINES.get(name, []):
                out += el.replace(m.group(1), f'{m.group(1)} fill="none" stroke="{NAVY}" stroke-width="5" stroke-linejoin="round"', 1)
            return out

        text = re.sub(r"<(path|polygon|rect|circle)\b[^>]*>", shape, text)
    under = UNDERLAYS.get(name)
    if under:
        els = re.findall(r"<(?:path|polygon|rect|circle)\b[^>]*>", text)
        head = re.search(r'\sd="([^"]*)"', els[under["head"]]).group(1)
        head = re.split(r"(?=[Mm])", head)[1]  # [0] is "" before the first M
        layer = f'<path fill="{WHITE}" d="{head}Z"/><polygon fill="{WHITE}" points="{under["points"].strip()}"/>'
        text = text.replace(els[0], els[0] + layer, 1)
    vb = VIEWBOX.get(name, "0 0 1920 1920")
    text = re.sub(r"<svg[^>]*>", f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" '
                  f'aria-label="{title}"><title>{title}</title>', text, count=1)
    text = re.sub(r">\s+<", "><", text).strip() + "\n"
    (OUT / f"{name}.svg").write_text(text, encoding="utf-8")


def main(folder):
    OUT.mkdir(parents=True, exist_ok=True)
    for fn, (name, title, disc) in SOURCES.items():
        convert(Path(folder) / fn, name, title, disc)


if __name__ == "__main__":
    main(sys.argv[1])
