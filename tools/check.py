#!/usr/bin/env python3
"""Design-system check for the Crisp site. Exits 1 if any rule is broken.

Usage: python3 tools/check.py            (checks css/*.css and every built HTML page)
       python3 tools/check.py file ...   (checks only the given .css/.html files)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ALLOWED_COLOURS = {c.upper() for c in (
    "#021F53 #FF8A00 #FF6A00 #CC4806 #FECA98 #FD9F0F #FFFFFF "
    "#F4F4F2 #ECECE9 #DEDEDA #E6E6E2 #4A5675 #FFF"
).split()}
ALLOWED_RADII = {"8px", "12px", "16px", "24px", "32px", "50%", "0"}

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
FONT_FAMILY = re.compile(r"font-family\s*:\s*([^;}]+)", re.I)
RADIUS = re.compile(r"border(?:-[a-z]+){0,2}-radius\s*:\s*([^;}]+)", re.I)
SHADOW = re.compile(r"box-shadow\s*:\s*([^;}]+)", re.I)
BORDER = re.compile(r"(?<![\w-])border(?:-(?:top|right|bottom|left))?(?:-width)?\s*:\s*([^;}]+)", re.I)
NUM = r"(-?\d*\.?\d+)(?:px)?"


def strip_comments(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def check_style_text(text, label):
    """Rules shared by .css files and inline/<style> CSS in HTML."""
    out = []
    text = strip_comments(text)

    for m in HEX.finditer(text):
        if m.group(0).upper() not in ALLOWED_COLOURS:
            out.append(f"{label}:{line_of(text, m.start())}: colour {m.group(0)} is not a design-system colour")

    for m in FONT_FAMILY.finditer(text):
        v = m.group(1)
        if "schibsted" not in v.lower() and v.strip() not in ("inherit", "initial", "unset") and not v.strip().startswith("var("):
            out.append(f"{label}:{line_of(text, m.start())}: font-family '{v.strip()}' is not Schibsted Grotesk")

    for m in RADIUS.finditer(text):
        v = m.group(1).strip()
        if "var(" in v:
            continue
        for part in re.split(r"[\s/]+", re.sub(r"!important", "", v).strip()):
            if part and part not in ALLOWED_RADII and part not in ("0px",):
                out.append(f"{label}:{line_of(text, m.start())}: border-radius '{part}' is not an allowed radius")
        if re.search(r"999", v):
            out.append(f"{label}:{line_of(text, m.start())}: pill radius (999px) is not allowed")

    for m in SHADOW.finditer(text):
        for layer in re.split(r",(?![^()]*\))", m.group(1)):
            nums = re.findall(NUM, re.sub(r"rgba?\([^)]*\)", "", layer.replace("inset", "")))
            if len(nums) >= 3:
                x, y, blur = float(nums[0]), float(nums[1]), float(nums[2])
                if (x > 0 or y > 0) and blur == 0:
                    out.append(f"{label}:{line_of(text, m.start())}: hard offset box-shadow '{layer.strip()}'")

    for m in BORDER.finditer(text):
        for w in re.findall(r"(\d*\.?\d+)px", m.group(1)):
            if float(w) > 1.5:
                out.append(f"{label}:{line_of(text, m.start())}: border width {w}px is above 1.5px")
                break

    return out


def label_for(path):
    return str(path.relative_to(ROOT)) if ROOT in path.parents else str(path)


def check_css(path):
    path = Path(path)
    return check_style_text(path.read_text(encoding="utf-8"), label_for(path))


def check_html(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    label = label_for(path)
    out = []

    # inline styles and <style> blocks follow the same rules as CSS files
    css_bits = re.findall(r"style=\"([^\"]*)\"", text) + re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.S)
    for bit in css_bits:
        out += check_style_text(bit, label)

    for m in re.finditer(r"class=\"([^\"]*)\"", text):
        for cls in m.group(1).split():
            if "reveal" in cls or "squiggle" in cls:
                out.append(f"{label}:{line_of(text, m.start())}: class '{cls}' is banned (no reveal/squiggle)")

    for m in re.finditer(r"<img\b[^>]*>", text, flags=re.I):
        if not re.search(r"\balt\s*=", m.group(0), flags=re.I):
            out.append(f"{label}:{line_of(text, m.start())}: <img> without alt")

    return out


def built_pages():
    pages = [p for p in ROOT.glob("*/index.html") if p.parts[len(ROOT.parts)] not in ("src", "docs", "node_modules", "motion", "assets")]
    pages += [ROOT / "index.html", ROOT / "404.html"]
    return sorted(p for p in pages if p.exists())


def main(argv):
    if argv:
        targets = [Path(a).resolve() for a in argv]
    else:
        targets = sorted((ROOT / "css").glob("*.css")) + built_pages()
    problems = []
    for t in targets:
        problems += check_css(t) if t.suffix == ".css" else check_html(t)
    for p in problems:
        print(p)
    if problems:
        print(f"\nFAIL: {len(problems)} violation(s)")
        return 1
    print("OK: no violations")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
