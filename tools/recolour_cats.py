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
    "Untitled-1.svg": ("samosa-avatar", "Samosa the cat, avatar", CREAM),
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
# User: "add a light colour fill in cats ears that matches their nose": inner-ear shapes take the nose's
# Flake cream (every nose here is cream). Indices are source shapes, found by browser inspection.
EARS = {
    "idli-avatar": [78, 79], "idli-confused": [41, 49, 51, 160, 163, 194], "idli-lying": [6, 31],
    "idli-sleeping": [30, 54, 63], "idli-hammock": [579, 580], "samosa-avatar": [6, 12],
    "samosa-ball": [42, 46, 106], "samosa-sitting": [120, 121, 123],
}

# User: "his closed eyes cant be seen, so colour that path in white": closed-eye lines that vanished on navy fur.
CLOSED_EYES = {"idli-avatar": [73], "idli-sleeping": [61, 62]}

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
    shapes.update({i: CREAM for i in EARS.get(name, [])})
    shapes.update({i: WHITE for i in CLOSED_EYES.get(name, [])})
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
