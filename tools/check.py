#!/usr/bin/env python3
"""Design-system check for the Crisp site. Exits 1 if any rule is broken.

Usage: python3 tools/check.py            (checks css/*.css and every built HTML page)
       python3 tools/check.py file ...   (checks only the given .css/.html files)
"""
import html as htmllib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ALLOWED_COLOURS = {c.upper() for c in (
    "#021F53 #FF8A00 #FF6A00 #CC4806 #FECA98 #FD9F0F #FFFFFF "
    "#F4F4F2 #ECECE9 #DEDEDA #E6E6E2 #4A5675 #FFF"
).split()}
# Copy that must appear verbatim on each page (checked in src/pages/<slug>.html and the built page).
PAGE_COPY = {
    "home": [
        "Design with a crunch!",
        "Good work speaks for itself.",
        "Brands we've been baking for!",
        "Strategy. Brand. Product. Build.",
        "Design that has a job to do.",
        "Got something worth making?",
    ],
    "services": [
        "Get the mix right.",
        "Don't design the wrong thing beautifully.",
        "Position first. Pixels second.",
        "Make complex feel simple.",
        "If we designed it, we build it.",
        "Built for people. Designed for business.",
    ],
    "work": [
        "Fresh from the Oven.",
        "HDFC securities",
        "The Mind Mojo",
        "NMIMS",
        "HDB Financial Services",
        "SAATH",
        "Kaamna",
        "Want to see more?",
    ],
}
# Pages whose case tiles (<article class="case">) must each carry a visual, a tag and a one-line description.
CASE_PAGES = {"work": 6}
# Element ids each page must carry (other pages link to them as anchors).
PAGE_IDS = {
    "services": ["strategy", "branding", "product", "build", "process"],
}
ALLOWED_RADII = {"8px", "12px", "16px", "24px", "32px", "50%", "0"}

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
FONT_FAMILY = re.compile(r"(?<![\w-])font-family\s*:\s*([^;}]+)", re.I)
FONT_SHORTHAND = re.compile(r"(?<![\w-])font\s*:\s*([^;}]+)", re.I)
RADIUS = re.compile(r"(?<![\w-])border(?:-[a-z]+){0,2}-radius\s*:\s*([^;}]+)", re.I)
SHADOW = re.compile(r"(?<![\w-])box-shadow\s*:\s*([^;}]+)", re.I)
BORDER = re.compile(
    r"(?<![\w-])((?:border(?:-(?:top|right|bottom|left|block|inline)(?:-(?:start|end))?)?(?:-width)?)"
    r"|outline(?:-width)?)\s*:\s*([^;}]+)", re.I)
COLOUR_PROP = re.compile(
    r"(?<![\w-])(color|background(?:-color|-image)?|border(?:-[a-z]+)*-color|border(?:-[a-z]+)?|outline(?:-color)?|"
    r"fill|stroke|stop-color|flood-color|text-decoration(?:-color)?|caret-color|accent-color|column-rule(?:-color)?)"
    r"\s*:\s*([^;}]+)", re.I)
COLOUR_FUNC = re.compile(r"(?<![\w-])(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\(", re.I)
ALLOWED_RGBA = re.compile(r"rgba\(\s*2\s*,\s*31\s*,\s*83\s*,[^)]*\)", re.I)
NUM = r"(-?\d*\.?\d+)"

ALLOWED_FAMILIES = {"schibsted grotesk", "system-ui", "-apple-system", "segoe ui", "arial", "sans-serif",
                    "ui-sans-serif", "inherit", "initial", "unset"}
ALLOWED_NAMED = {"white", "transparent", "currentcolor", "inherit"}
NAMED_COLOURS = set("""aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown
burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray
darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen darkslateblue
darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite
forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory
khaki lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen
lightgrey lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime
limegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue
mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy oldlace olive
olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum
powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue
slateblue slategray slategrey snow springgreen steelblue tan teal thistle tomato turquoise violet wheat whitesmoke yellow
yellowgreen""".split())


def load_shadow_tokens():
    import json
    data = json.loads((ROOT / "tools" / "tokens.json").read_text(encoding="utf-8"))
    return {norm_layer(t["value"]) for t in data["shadow"]["tokens"]}


def norm_layer(layer):
    return re.sub(r"\s*,\s*", ",", re.sub(r"\s+", " ", layer.strip().lower()))


def split_top(value, sep=","):
    """Split on sep outside of parentheses."""
    parts, depth, cur = [], 0, ""
    for ch in value:
        depth += ch == "("
        depth -= ch == ")"
        if ch == sep and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    return parts + [cur]


def strip_comments(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def strip_colours(value):
    value = re.sub(r"(?:rgba?|hsla?)\([^)]*\)|var\([^)]*\)", " ", value, flags=re.I)
    return HEX.sub(" ", value)


def check_families(value, where):
    """Every family in a font-family list must be Schibsted, a generic keyword or a --font* token."""
    out = []
    for fam in split_top(value):
        fam = fam.strip().strip("\"'").lower() if not fam.strip().lower().startswith("var(") else fam.strip()
        fam = re.sub(r"\s*!important$", "", fam)
        if fam in ALLOWED_FAMILIES or re.fullmatch(r"var\(--font[\w-]*\)", fam, flags=re.I):
            continue
        out.append(f"{where}: font family '{fam}' is not Schibsted Grotesk, a generic keyword or a --font token")
    return out


FONT_SIZE_PART = (r"(?:var\([^)]*\)|[\d.]+(?:px|rem|em|%|pt|vw)|(?:xx?-)?(?:small|large)|medium|larger|smaller|xxx-large)"
                  r"(?:\s*/\s*(?:var\([^)]*\)|[\w.%]+))?")
FONT_SHORT_RE = re.compile(
    r"^(?:(?:italic|oblique|normal|bold|bolder|lighter|small-caps|\d{3}|var\(--fw[^)]*\))\s+)*" + FONT_SIZE_PART + r"\s+(.+)$", re.I)


def check_style_text(text, label):
    """Rules shared by .css files and inline/<style> CSS in HTML."""
    out = []
    text = strip_comments(text)
    shadow_tokens = load_shadow_tokens()

    for m in HEX.finditer(text):
        if m.group(0).upper() not in ALLOWED_COLOURS:
            out.append(f"{label}:{line_of(text, m.start())}: colour {m.group(0)} is not a design-system colour")

    for m in COLOUR_FUNC.finditer(ALLOWED_RGBA.sub("", text)):
        out.append(f"{label}: colour function {m.group(1)}() is not allowed (only rgba(2,31,83,*) for shadows)")

    for m in COLOUR_PROP.finditer(text):
        value = strip_colours(re.sub(r"url\([^)]*\)", " ", m.group(2)))
        for word in re.findall(r"[a-z]+", value.lower()):
            if word in NAMED_COLOURS and word not in ALLOWED_NAMED:
                out.append(f"{label}:{line_of(text, m.start())}: named colour '{word}' in {m.group(1)} is not allowed")

    for m in FONT_FAMILY.finditer(text):
        out += check_families(m.group(1), f"{label}:{line_of(text, m.start())}")

    for m in FONT_SHORTHAND.finditer(text):
        v = re.sub(r"\s*!important$", "", m.group(1).strip())
        where = f"{label}:{line_of(text, m.start())}"
        if v.lower() in ("inherit", "initial", "unset", "caption", "menu", "status-bar"):
            continue
        fm = FONT_SHORT_RE.match(v)
        if fm:
            out += check_families(fm.group(1), where)
        else:
            out.append(f"{where}: cannot read font shorthand '{v}'; use font-family with tokens")

    for m in RADIUS.finditer(text):
        where = f"{label}:{line_of(text, m.start())}"
        v = re.sub(r"\s*!important$", "", m.group(1).strip())
        for part in re.findall(r"var\([^)]*\)|[^\s/]+", v):
            if part in ALLOWED_RADII or part in ("0px", "inherit", "initial", "unset") or re.fullmatch(r"var\(--radius-[\w-]+\)", part):
                continue
            out.append(f"{where}: border-radius '{part}' is not an allowed radius")

    for m in SHADOW.finditer(text):
        where = f"{label}:{line_of(text, m.start())}"
        for layer in split_top(re.sub(r"\s*!important$", "", m.group(1).strip())):
            layer = layer.strip()
            if layer.lower() in ("none", "inherit", "initial", "unset") or re.fullmatch(r"var\(--shadow-[\w-]+\)", layer):
                continue
            if norm_layer(layer) in shadow_tokens:
                continue
            nums = [float(n) for n in re.findall(NUM, strip_colours(layer.lower().replace("inset", "")))]
            hard = len(nums) >= 2 and (nums[0] != 0 or nums[1] != 0) and (len(nums) < 3 or nums[2] == 0)
            kind = "hard offset " if hard else ""
            out.append(f"{where}: {kind}box-shadow '{layer}' is not one of the design-system shadow tokens")

    for m in BORDER.finditer(text):
        where = f"{label}:{line_of(text, m.start())}"
        value = strip_colours(m.group(2))
        if re.search(r"(?<![\w-])(thick|medium)(?![\w-])", value, flags=re.I):
            out.append(f"{where}: {m.group(1)} width keyword (thick/medium) is not allowed")
        # borders max 1.5px; outline max 2px (the orange focus ring)
        limit = 2 if m.group(1).lower().startswith("outline") else 1.5
        for w, unit in re.findall(r"(\d*\.?\d+)(px|rem|em)", value):
            if float(w) * (1 if unit == "px" else 16) > limit:
                out.append(f"{where}: {m.group(1)} width {w}{unit} is above {limit}px")
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
    css_bits = [m[1] for m in re.findall(r"(?<![\w-])style\s*=\s*([\"'])(.*?)\1", text, flags=re.S)]
    css_bits += re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.S)
    for bit in css_bits:
        out += check_style_text(bit, label)

    # colour-bearing attributes (svg fill/stroke etc.) are checked as if they were CSS declarations
    for m in re.finditer(r"(?<![\w-])(fill|stroke|stop-color|flood-color|color|bgcolor)\s*=\s*([\"'])(.*?)\2", text, flags=re.S):
        out += check_style_text(f"{m.group(1)}: {re.sub(r'url[(][^)]*[)]', 'none', m.group(3))};", f"{label}:{line_of(text, m.start())}")

    for m in re.finditer(r"(?<![\w-])class\s*=\s*([\"'])(.*?)\1", text, flags=re.S):
        for cls in m.group(2).split():
            if "reveal" in cls or "squiggle" in cls:
                out.append(f"{label}:{line_of(text, m.start())}: class '{cls}' is banned (no reveal/squiggle)")

    out += check_copy(page_slug(path), text, label)

    for m in re.finditer(r"<img\b[^>]*>", text, flags=re.I):
        if not re.search(r"(?<![\w-])alt\s*=", m.group(0), flags=re.I):
            out.append(f"{label}:{line_of(text, m.start())}: <img> without alt")

    return out


def page_slug(path):
    path = Path(path).resolve()
    if path == ROOT / "index.html":
        return "home"
    if path == ROOT / "404.html":
        return "404"
    if path.name == "index.html" and path.parent.parent == ROOT:
        return path.parent.name
    return None


def check_copy(slug, text, label):
    """Every required string for the page must appear verbatim (entities decoded)."""
    plain = htmllib.unescape(re.sub(r"<[^>]+>", "", text)).replace("\u2019", "'")
    plain = re.sub(r"\s+", " ", plain.replace("\u00a0", " "))
    out = [f"{label}: missing required copy '{s}'" for s in PAGE_COPY.get(slug, []) if s not in plain]
    ids = set(re.findall(r"(?<![\w-])id\s*=\s*[\"']([^\"']+)[\"']", text))
    out += [f"{label}: missing required id '#{i}'" for i in PAGE_IDS.get(slug, []) if i not in ids]
    if slug in CASE_PAGES:
        out += check_cases(text, label, CASE_PAGES[slug])
    return out


def has_class(fragment, cls):
    return any(cls in m.group(2).split()
               for m in re.finditer(r"(?<![\w-])class\s*=\s*([\"'])(.*?)\1", fragment, flags=re.S))


def check_cases(text, label, expected):
    """Each <article class="case"> needs a .case-visual, a .tag and a non-empty p.case-line."""
    out = []
    cases = [m.group(0) for m in re.finditer(r"<article\b[^>]*>.*?</article>", text, flags=re.S | re.I)
             if has_class(re.match(r"<article\b[^>]*>", m.group(0), flags=re.I).group(0), "case")]
    if len(cases) != expected:
        out.append(f"{label}: expected {expected} case tiles (<article class=\"case\">), found {len(cases)}")
    for i, c in enumerate(cases, 1):
        if not has_class(c, "case-visual"):
            out.append(f"{label}: case {i} has no visual (.case-visual)")
        if not has_class(c, "tag"):
            out.append(f"{label}: case {i} has no tag (.tag)")
        line = re.search(r"<p\b[^>]*class\s*=\s*([\"'])[^\"']*\bcase-line\b[^\"']*\1[^>]*>(.*?)</p>", c, flags=re.S)
        if not line or not re.sub(r"<[^>]+>|\s", "", line.group(2)):
            out.append(f"{label}: case {i} has no one-line description (p.case-line)")
    return out


def check_sources():
    out = []
    for slug in PAGE_COPY:
        src = ROOT / "src" / "pages" / f"{slug}.html"
        if not src.exists():
            out.append(f"src/pages/{slug}.html: missing (required page)")
            continue
        out += check_copy(slug, src.read_text(encoding="utf-8"), label_for(src))
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
    problems = check_sources()
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
