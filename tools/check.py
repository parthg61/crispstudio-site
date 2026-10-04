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
        # restored from the pre-redesign Home (2646846): status line, eyebrows, tile tags, services button
        "Design studio · Mumbai, India",
        "Selected work",
        "What we do",
        "Why Crisp",
        "From the blog",
        "All services",
        "UX Audits", "User Research", "Journey Mapping", "Usability Testing",
        "Positioning", "Visual Identity", "Guidelines", "Brand Architecture",
        "UX & UI", "AI Experience", "Design Systems", "Prototyping",
        "Front-end", "Web Development", "Framer",
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
    "about": [
        "No half-baked ideas.",
        "We're Crisp, a design studio in Mumbai.",
        "We care about one thing above the rest: does the work have a reason to exist?",
        "If it looks good but doesn't work, it's not done.",
        "If it works but nobody understands it, it's not done.",
        "If it solves the problem but feels forgettable, it's not done.",
        "We keep going until it clicks.",
        "Good design looks good. Great design works.",
        "Startups and established companies.",
        "Any team with a real problem",
        "Sound like your kind of studio?",
    ],
    "blog": [
        "Food for thought.",
        "The first batch is in the oven.",
        "New writing lands here soon. Until then, tell us what you're working on.",
    ],
    "contact": [
        "Let's make something crispy.",
        "Tell us what you're working on. We'll help you take it a notch up.",
        "Prefer email? team@crispstudio.in",
        "Mumbai, India",
        "Send it",
        "Got it. We'll be in touch within two working days.",
    ],
    "404": [
        "404",
        "Crumbled.",
        "This page doesn't exist or has moved. Head back home or pick a page from the menu.",
        "Back to home",
    ],
}
# Meta descriptions that must stay word for word (checked in the source front matter and the built <meta>).
PAGE_DESC = {
    "home": "Crisp is a design studio in Mumbai. We design brands and digital products with a clear purpose: "
            "to look sharp, work better and move the business forward.",
}
# Pages whose case tiles (<article class="case">) must each carry a visual, a tag and a one-line description.
CASE_PAGES = {"work": 6}
# Element ids each page must carry (other pages link to them as anchors).
PAGE_IDS = {
    "services": ["strategy", "branding", "product", "build", "process"],
    "blog": ["blog-list", "blog-empty"],
    "contact": ["contact-form", "f-name", "f-email", "f-company", "f-needs", "f-msg", "form-note", "form-done"],
}
# The contact form: label -> control name for the five fields, and the five "What do you need?" options.
FORM_FIELDS = {"Name": "name", "Work email": "email", "Company": "company",
               "What do you need?": "need", "Tell us a bit about it": "message"}
FORM_NEEDS = ["Strategy & Research", "Branding", "Product Design", "Build", "Not sure yet"]
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

    # filter: drop-shadow() takes a shadow token only (the logo uses --shadow-logo); no literal shadow numbers
    for m in re.finditer(r"(?<![\w-])drop-shadow\(", text, flags=re.I):
        depth, j = 1, m.end()
        while j < len(text) and depth:
            depth += {"(": 1, ")": -1}.get(text[j], 0)
            j += 1
        arg = text[m.end():j - 1].strip()
        if not re.fullmatch(r"var\(--shadow-[\w-]+\)", arg):
            out.append(f"{label}:{line_of(text, m.start())}: drop-shadow({arg}) is not a design-system shadow token (use var(--shadow-*))")

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
    text = path.read_text(encoding="utf-8")
    return check_style_text(text, label_for(path)) + check_cat_motion(text, label_for(path)) + check_all_motion(text, label_for(path))


def check_html(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    label = label_for(path)
    out = []

    # inline styles and <style> blocks follow the same rules as CSS files
    css_bits = [m[1] for m in re.findall(r"(?<![\w-])style\s*=\s*([\"'])(.*?)\1", text, flags=re.S)]
    style_blocks = re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.S)
    css_bits += style_blocks
    for bit in css_bits:
        out += check_style_text(bit, label)
    for bit in style_blocks:
        out += check_cat_motion(bit, label)

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

    out += check_images(text, label, page_slug(path))
    if page_slug(path) is not None:
        out += check_hero(text, label, page_slug(path))
    if page_slug(path) == "home":
        out += check_home_sections(text, label)

    return out


# Round 2, Task 3: Home "What we do" bento, the services marquee, the client ticker and the Why statement
BENTO_TILES = {  # anchor -> (official icon file, service tags)
    "/services/#strategy": ("Crisp_Icon_Strategy.svg", ("UX Audits", "User Research", "Journey Mapping", "Usability Testing")),
    "/services/#branding": ("Crisp_Icon_Branding.svg", ("Positioning", "Visual Identity", "Guidelines", "Brand Architecture")),
    "/services/#product": ("Crisp_Icon_UIUX.svg", ("UX & UI", "AI Experience", "Design Systems", "Prototyping")),
    "/services/#build": ("Crisp_Icon_DesignToCode.svg", ("Front-end", "Web Development", "Framer")),
}
MARQUEE_NAMES = ["Strategy & Research", "Branding", "Product Design", "Build"]
JOB_WORDS = ["clarify", "engage", "convert", "simplify", "move someone to act"]
WHY_SENTENCE = "Everything we make has a job, to clarify, engage, convert, simplify or move someone to act."


def classes(el):
    return el["attrs"].get("class", "").split()


def inside(el, parent):
    return any(a is parent["attrs"] for _, _, a in el["ancestors"])


def norm_text(s):
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


def check_pause_button(els, target, what, label):
    """target needs an id and data-pausable; one <button data-pause aria-pressed aria-controls=id> reads Pause."""
    out = []
    tid = target["attrs"].get("id")
    if "data-pausable" not in target["attrs"] or not tid:
        out.append(f"{label}:{target['line']}: the {what} needs data-pausable and an id (its pause button points at it)")
        return out
    btns = [e for e in els if "data-pause" in e["attrs"] and e["attrs"].get("aria-controls") == tid]
    if len(btns) != 1:
        out.append(f"{label}:{target['line']}: the {what} needs one [data-pause] button with aria-controls=\"{tid}\", found {len(btns)}")
    for b in btns:
        if b["tag"] != "button" or b["attrs"].get("type") != "button":
            out.append(f"{label}:{b['line']}: the {what} pause control must be a <button type=\"button\">")
        if b["attrs"].get("aria-pressed") not in ("true", "false"):
            out.append(f"{label}:{b['line']}: the {what} pause button needs aria-pressed")
        if not re.search(r"\b(Pause|Play)\b", b["text"]):
            out.append(f"{label}:{b['line']}: the {what} pause button must be labelled Pause/Play")
    return out


def check_home_sections(text, label):
    """Home: (1) four .bento tiles linking to the four Services anchors, each with its official icon in an
    .icon-chip and its service tags; (2) one .marquee listing exactly the four service names (copies after the
    first set aria-hidden) with a pause button; (3) the client ticker (#track) is pausable too; (4) .why-statement
    carries the full Why sentence for screen readers and an aria-hidden .cycle of the five job words."""
    out = []
    els = tag_contexts(text)
    bentos = [e for e in els if "bento" in classes(e)]
    if len(bentos) != 1:
        out.append(f"{label}: Home needs one .bento grid for What we do, found {len(bentos)}")
    for bento in bentos:
        links = [e for e in els if e["tag"] == "a" and inside(e, bento)]
        hrefs = [e["attrs"].get("href") for e in links]
        if sorted(hrefs) != sorted(BENTO_TILES):
            out.append(f"{label}:{bento['line']}: .bento tiles must link to {list(BENTO_TILES)}, found {hrefs}")
        for a in links:
            icon, tags = BENTO_TILES.get(a["attrs"].get("href"), (None, ()))
            if icon is None:
                continue
            imgs = [e for e in els if e["tag"] == "img" and inside(e, a) and in_class(e, "icon-chip")]
            if not any(e["attrs"].get("src", "").endswith("/assets/icons/" + icon) for e in imgs):
                out.append(f"{label}:{a['line']}: tile {a['attrs']['href']} needs the official {icon} in an .icon-chip")
            tag_texts = [norm_text(e["text"]) for e in els if inside(e, a) and "tag" in classes(e)]
            missing = [t for t in tags if t not in tag_texts]
            if missing:
                out.append(f"{label}:{a['line']}: tile {a['attrs']['href']} lost its tags {missing}")
    marquees = [e for e in els if "marquee" in classes(e)]
    if len(marquees) != 1:
        out.append(f"{label}: Home needs one services .marquee, found {len(marquees)}")
    for mq in marquees:
        sets = [e for e in els if e["tag"] == "ul" and inside(e, mq)]
        live = [s for s in sets if s["attrs"].get("aria-hidden") != "true"]
        if len(live) != 1 or len(sets) < 2:
            out.append(f"{label}:{mq['line']}: .marquee needs one readable <ul> of names plus aria-hidden copies for the loop")
        for s in sets:
            names = [norm_text(e["text"]) for e in els if e["tag"] == "li" and inside(e, s)]
            if names != MARQUEE_NAMES:
                out.append(f"{label}:{s['line']}: .marquee names must be exactly {MARQUEE_NAMES}, found {names}")
        out += check_pause_button(els, mq, "services marquee", label)
    tracks = [e for e in els if e["attrs"].get("id") == "track"]
    if len(tracks) != 1:
        out.append(f"{label}: Home needs the client logo ticker (#track)")
    for tr in tracks:
        hosts = [e for e in els if "data-pausable" in e["attrs"] and inside(tr, e)]
        if not hosts:
            out.append(f"{label}:{tr['line']}: the client logo ticker needs a [data-pausable] wrapper with a pause button")
        for h in hosts:
            out += check_pause_button(els, h, "client logo ticker", label)
    whys = [e for e in els if "why-statement" in classes(e)]
    if len(whys) != 1:
        out.append(f"{label}: Home needs one .why-statement, found {len(whys)}")
    for w in whys:
        cycles = [e for e in els if "cycle" in classes(e) and inside(e, w)]
        spoken = w["spoken"]
        if WHY_SENTENCE not in norm_text(spoken):
            out.append(f"{label}:{w['line']}: .why-statement must keep '{WHY_SENTENCE}' readable (outside aria-hidden)")
        if len(cycles) != 1 or not any(a.get("aria-hidden") == "true" for _, _, a in cycles[0]["ancestors"] + [(0, 0, cycles[0]["attrs"])]):
            out.append(f"{label}:{w['line']}: .why-statement needs one aria-hidden .cycle of the job words")
        for c in cycles:
            words = [norm_text(e["text"]).rstrip(".") for e in els if e["tag"] == "span" and any(a is c["attrs"] for _, _, a in e["ancestors"][-1:])]
            if words != JOB_WORDS:
                out.append(f"{label}:{c['line']}: .cycle job words must be {JOB_WORDS}, found {words}")
    return out


# Round 2: one logo per page (the navbar), cats only in small moments
LOGO_SRC = re.compile(r"Crisp_Logo|Crisp_Avatar_(?:Orange|Navy)")
CAT_SRC = re.compile(r"Crisp_Cat_|Crisp_Avatar_(?:Samosa|Idli)")
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


def tag_contexts(text):
    """Every start tag as a dict: line, tag, attrs, ancestors ((tag, classes, attrs) tuples) and text
    (the element's own text content, gathered until it closes; empty for void tags) and spoken (the same text
    minus anything inside an aria-hidden="true" descendant: what a screen reader gets)."""
    from html.parser import HTMLParser

    class P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack, self.els, self.open = [], [], []

        def handle_starttag(self, tag, attrs):
            a = {k: (v or "") for k, v in attrs}
            el = {"line": self.getpos()[0], "tag": tag, "attrs": a, "ancestors": list(self.stack), "text": "", "spoken": ""}
            self.els.append(el)
            if tag not in VOID_TAGS:
                self.stack.append((tag, a.get("class", "").split(), a))
                self.open.append(el)

        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)
            if tag not in VOID_TAGS:  # <x/> on a non-void tag: close it straight away
                self.handle_endtag(tag)

        def handle_data(self, data):
            hidden = [k for k, el in enumerate(self.open) if el["attrs"].get("aria-hidden") == "true"]
            for k, el in enumerate(self.open):
                el["text"] += data
                if not any(h > k for h in hidden):  # "spoken": text outside aria-hidden descendants
                    el["spoken"] += data

        def handle_endtag(self, tag):
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    del self.open[i:]
                    break

    p = P()
    p.feed(strip_inert(text))
    return p.els


def img_contexts(text):
    """Every <img> with its line, attributes and ancestors as (tag, classes, attrs) tuples."""
    return [(e["line"], e["attrs"], e["ancestors"]) for e in tag_contexts(text) if e["tag"] == "img"]


HERO_CLIENTS = ("HDFC securities", "The Mind Mojo", "NMIMS")


def in_class(el, cls):
    return any(cls in c for _, c, _ in el["ancestors"])


def check_hero(text, label, slug):
    """Round 2 Home hero. Every page: one [data-logo-slot] header brandmark (an <a href="/">) inside <header>.
    Home only: exactly one <img data-hero-logo> inside .hero (it travels into the slot), and a decorative
    .fan (aria-hidden) inside .hero holding three .fan-card cards named HDFC securities, The Mind Mojo, NMIMS."""
    out = []
    els = tag_contexts(text)
    slots = [e for e in els if "data-logo-slot" in e["attrs"]]
    if len(slots) != 1:
        out.append(f"{label}: expected one [data-logo-slot] header logo link, found {len(slots)}")
    for e in slots:
        if not any(t == "header" for t, _, _ in e["ancestors"]):
            out.append(f"{label}:{e['line']}: [data-logo-slot] must sit inside <header>")
        if e["tag"] != "a" or e["attrs"].get("href") != "/":
            out.append(f"{label}:{e['line']}: [data-logo-slot] must be the <a href=\"/\"> brandmark")
    logos = [e for e in els if "data-hero-logo" in e["attrs"]]
    if slug != "home":
        out += [f"{label}:{e['line']}: data-hero-logo is for the Home hero only" for e in logos]
        return out
    if len(logos) != 1:
        out.append(f"{label}: Home needs exactly one data-hero-logo element, found {len(logos)}")
    for e in logos:
        if e["tag"] != "img" or not in_class(e, "hero"):
            out.append(f"{label}:{e['line']}: data-hero-logo must be an <img> inside .hero")
    fans = [e for e in els if "fan" in e["attrs"].get("class", "").split()]
    if len(fans) != 1:
        out.append(f"{label}: Home needs one .fan card stack in the hero, found {len(fans)}")
    for fan in fans:
        if not in_class(fan, "hero"):
            out.append(f"{label}:{fan['line']}: .fan must sit inside .hero")
        if fan["attrs"].get("aria-hidden") != "true":
            out.append(f"{label}:{fan['line']}: .fan is decorative and needs aria-hidden=\"true\"")
        cards = [e for e in els if "fan-card" in e["attrs"].get("class", "").split()
                 and any(a is fan["attrs"] for _, _, a in e["ancestors"])]
        if len(cards) != 3:
            out.append(f"{label}:{fan['line']}: .fan needs three .fan-card cards, found {len(cards)}")
        names = [re.sub(r"\s+", " ", c["text"]).strip() for c in cards]
        for client in HERO_CLIENTS:
            if not any(client in n for n in names):
                out.append(f"{label}:{fan['line']}: .fan has no card for '{client}'")
    return out


def check_images(text, label, slug):
    """(a) no logo/croissant-avatar <img> outside <header>, except the Home hero logo (data-hero-logo inside
    .hero on index.html), which travels into the navbar; (b) no cat on the Work page or inside a .hero."""
    out = []
    if slug == "work" and CAT_SRC.search(strip_inert(text)):
        out.append(f"{label}: a cat (Idli/Samosa) appears on the Work page; cats never sit beside client work")
    for line, a, anc in img_contexts(text):
        src = a.get("src", "") + " " + a.get("srcset", "")
        in_header = any(t == "header" for t, _, _ in anc)
        in_hero = any("hero" in cls for _, cls, _ in anc)
        if LOGO_SRC.search(src) and not in_header:
            if not (slug == "home" and in_hero and "data-hero-logo" in a):
                out.append(f"{label}:{line}: logo/avatar image outside the header ({src.strip()}); one logo per page")
        if CAT_SRC.search(src) and in_hero:
            out.append(f"{label}:{line}: cat image inside a .hero ({src.strip()}); cats never sit in a hero")
    return out


def check_assets(manifest=None):
    """(c) every file in tools/assets.sha256 exists and still matches its recorded hash (official artwork)."""
    import hashlib
    manifest = Path(manifest or ROOT / "tools" / "assets.sha256")
    out = []
    for n, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        digest, _, rel = line.strip().partition("  ")
        f = ROOT / rel.strip()
        if not f.is_file():
            out.append(f"{label_for(manifest)}:{n}: {rel} is missing")
        elif hashlib.sha256(f.read_bytes()).hexdigest() != digest:
            out.append(f"{label_for(manifest)}:{n}: {rel} changed (sha256 differs from the official file)")
    return out


def css_rules(text):
    """Yield (selector, body, at_rules) for every style rule, with the enclosing @-rule preludes."""
    text = strip_comments(text)
    stack, buf, i = [], "", 0
    while i < len(text):
        ch = text[i]
        if ch == "{":
            prelude = buf.strip()
            buf = ""
            if prelude.startswith("@"):
                stack.append(prelude)
            else:
                depth, j = 1, i + 1
                while j < len(text) and depth:
                    depth += {"{": 1, "}": -1}.get(text[j], 0)
                    j += 1
                yield prelude, text[i + 1:j - 1], list(stack)
                i = j
                continue
        elif ch == "}":
            if stack:
                stack.pop()
            buf = ""
        elif ch == ";" and not stack and buf.strip().startswith("@"):
            buf = ""  # @import/@charset
        else:
            buf += ch
        i += 1


def motion_rules(text, name):
    """(selector, safe) for every rule that animates a .<name>* selector or uses @keyframes <name>-*;
    safe means it sits inside @media (prefers-reduced-motion: no-preference)."""
    found = []
    for sel, body, ats in css_rules(text):
        if any(a.lower().startswith("@keyframes") for a in ats):
            continue
        anim = re.search(r"(?<![\w-])animation(?:-name)?\s*:\s*([^;}]+)", body, flags=re.I)
        if not anim or re.fullmatch(r"\s*none\s*(!important)?\s*", anim.group(1)):
            continue
        n = re.escape(name)
        if re.search(rf"\.{n}(?![\w])|\.{n}-", sel) or re.search(rf"(?<![\w-]){n}-[\w-]+", anim.group(1)):
            safe = any(re.search(r"prefers-reduced-motion\s*:\s*no-preference", a, flags=re.I) for a in ats)
            found.append((sel, safe))
    return found


def check_cat_motion(text, label):
    """(d) cat loops (any animation on a .cat* selector or using @keyframes cat-*) must sit inside
    @media (prefers-reduced-motion: no-preference), so reduced motion never sees them. The Home hero card
    fan (.fan*, @keyframes fan-*) follows the same rule."""
    out = []
    for name, what in (("cat", "cat"), ("fan", "hero card fan")):
        out += [f"{label}: {what} animation on '{sel}' is not inside @media (prefers-reduced-motion: no-preference)"
                for sel, safe in motion_rules(text, name) if not safe]
    return out


NO_PREF = re.compile(r"prefers-reduced-motion\s*:\s*no-preference", re.I)


def check_all_motion(text, label):
    """Everything that moves on its own (marquee, ticker, and any other animation) runs only under
    @media (prefers-reduced-motion: no-preference): every animation declaration and every @keyframes."""
    out = []
    for sel, body, ats in css_rules(text):
        kf = [i for i, a in enumerate(ats) if a.lower().startswith("@keyframes")]
        if kf:
            if not any(NO_PREF.search(a) for a in ats[:kf[0]]):
                out.append(f"{label}: {ats[kf[0]]} is not inside @media (prefers-reduced-motion: no-preference)")
            continue
        anim = re.search(r"(?<![\w-])animation(?:-name)?\s*:\s*([^;}]+)", body, flags=re.I)
        if anim and not re.fullmatch(r"\s*none\s*(!important)?\s*", anim.group(1)) and not any(NO_PREF.search(a) for a in ats):
            out.append(f"{label}: animation on '{sel}' is not inside @media (prefers-reduced-motion: no-preference)")
    return sorted(set(out), key=out.index)


def check_strips_css(text, label):
    """The services .marquee and the client .track scroll only under no-preference, and a paused strip
    ([data-pausable].is-paused) really stops its animation (animation-play-state: paused)."""
    out = []
    rules = list(css_rules(text))
    for name in ("marquee", "track"):
        if not any(re.search(rf"\.{name}(?![\w])|\.{name}-", sel) and NO_PREF.search(" ".join(ats))
                   and re.search(r"(?<![\w-])animation\s*:\s*(?!none)", body) for sel, body, ats in rules):
            out.append(f"{label}: no .{name} scroll animation inside @media (prefers-reduced-motion: no-preference)")
    if not any(".is-paused" in sel and re.search(r"animation-play-state\s*:\s*paused", body) for sel, body, _ in rules):
        out.append(f"{label}: no '.is-paused ... {{ animation-play-state: paused }}' rule for the pause buttons")
    return out


def check_pausables_js(js, label="js/site.js"):
    """initPausables() is defined once and called once; it flips aria-pressed, the Pause/Play label and the
    .is-paused class on the [data-pausable] element its [data-pause] button controls. The Why job-word cycle
    checks reduced motion before it starts."""
    js = re.sub(r"/\*.*?\*/|(?<![:'\"\\])//[^\n]*", "", js, flags=re.S)
    out = []
    m = re.search(r"function\s+initPausables\s*\(", js)
    if len(re.findall(r"function\s+initPausables\s*\(", js)) != 1:
        return [f"{label}: expected one 'function initPausables()'"]
    body = js[m.start():m.start() + 2500]
    for need, why in ((r"\[data-pause\]", "find [data-pause] buttons"), (r"aria-pressed", "set aria-pressed"),
                      (r"'Pause'|\"Pause\"", "label the button Pause"), (r"'Play'|\"Play\"", "label the button Play"),
                      (r"is-paused", "toggle .is-paused"), (r"data-pausable|dataset\.pausable", "only control [data-pausable]")):
        if not re.search(need, body):
            out.append(f"{label}: initPausables must {why}")
    if len(re.findall(r"(?<!function )(?<![\w.])initPausables\s*\(\s*\)", js)) != 1:
        out.append(f"{label}: initPausables() must be called once")
    cyc = re.search(r"\.cycle", js)
    if not cyc or not re.search(r"prefers-reduced-motion: reduce", js[max(0, cyc.start() - 600):cyc.start() + 1500]):
        out.append(f"{label}: the Why job-word .cycle must check matchMedia('(prefers-reduced-motion: reduce)')")
    return out


def check_mobile_hero_order(text, label):
    """Phones (<600px): the big hero logo must be in the first screen, so under @media (max-width: 599px)
    .hero-art opens up (display: contents) and .hero-logo-spot has an `order` lower than .hero-copy's."""
    def decl(prop, sel_re):
        for sel, body, ats in css_rules(text):
            if any(re.search(r"max-width\s*:\s*599px", a) for a in ats) and re.search(sel_re, sel):
                m = re.search(rf"(?<![\w-]){prop}\s*:\s*([^;}}]+)", body)
                if m:
                    return m.group(1).strip()
        return None
    out = []
    if decl("display", r"\.hero-art(?![\w-])") != "contents":
        out.append(f"{label}: under max-width: 599px .hero-art must be display: contents (logo spot joins the hero grid)")
    spot, copy = decl("order", r"\.hero-logo-spot(?![\w-])"), decl("order", r"\.hero-copy(?![\w-])") or "0"
    try:
        if spot is None or int(spot) >= int(copy):
            out.append(f"{label}: under max-width: 599px .hero-logo-spot needs an order lower than .hero-copy ({spot} vs {copy})")
    except ValueError:
        out.append(f"{label}: unreadable mobile hero order ({spot} vs {copy})")
    return out


def check_fan_present(text, label):
    """The Home hero cards fan out once on load: site.css must animate .fan-card under no-preference."""
    if any(safe and ".fan-card" in sel for sel, safe in motion_rules(text, "fan")):
        return []
    return [f"{label}: no .fan-card load animation inside @media (prefers-reduced-motion: no-preference)"]


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
    desc = PAGE_DESC.get(slug)
    if desc and f'desc: "{desc}"' not in text and f'<meta name="description" content="{htmllib.escape(desc)}">' not in text:
        out.append(f"{label}: meta description changed; it must read '{desc}'")
    ids = set(re.findall(r"(?<![\w-])id\s*=\s*[\"']([^\"']+)[\"']", text))
    out += [f"{label}: missing required id '#{i}'" for i in PAGE_IDS.get(slug, []) if i not in ids]
    if slug in CASE_PAGES:
        out += check_cases(text, label, CASE_PAGES[slug])
    if slug == "contact":
        out += check_form(text, label, plain)
    return out


def check_form(text, label, plain):
    """Contact form: five labelled fields, five need checkboxes, data-endpoint, honeypot."""
    out = []
    form = re.search(r"<form\b[^>]*\bid=\"contact-form\"[^>]*>(.*?)</form>", text, flags=re.S)
    if not form:
        return [f"{label}: no <form id=\"contact-form\">"]
    if not re.search(r"<form\b[^>]*\bdata-endpoint=\"[^\"]*\"", text):
        out.append(f"{label}: contact form has no data-endpoint attribute")
    body = form.group(1)
    for text_label, name in FORM_FIELDS.items():
        if text_label not in plain:
            out.append(f"{label}: contact form missing label '{text_label}'")
        if not re.search(r"<(?:input|textarea)\b[^>]*\bname=\"%s\"" % name, body):
            out.append(f"{label}: contact form missing control name=\"{name}\"")
    values = [htmllib.unescape(v) for v in re.findall(r"<input\b[^>]*type=\"checkbox\"[^>]*value=\"([^\"]*)\"", body)]
    if values != FORM_NEEDS:
        out.append(f"{label}: contact form needs checkboxes {values} != {FORM_NEEDS}")
    if not re.search(r"<input\b[^>]*\bname=\"website\"", body):
        out.append(f"{label}: contact form lost its honeypot (name=\"website\")")
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


SITE = "https://crispstudio.in"
# href/src/poster/srcset with double, single or no quotes
REF_ATTR = re.compile(r"""\s(href|src|poster|srcset)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>"']+))""", re.I)
META_TAG = re.compile(r"<meta\b[^>]*>", re.I)
ATTR = re.compile(r"""([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>"']+))""")
ID_ATTR = re.compile(r"""(?<![\w-])id\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>"']+))""", re.I)


def attrs_of(tag):
    return {m.group(1).lower(): next(g for g in m.groups()[1:] if g is not None) for m in ATTR.finditer(tag)}


def strip_inert(text):
    """Drop comments and <script>/<style> bodies, whose markup is not part of the page."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", "", text, flags=re.S | re.I)


def page_refs(text):
    """Every URL the page itself points to: href/src/poster, each srcset candidate, og:url and og:image."""
    text = strip_inert(text)
    refs = []
    for m in REF_ATTR.finditer(text):
        value = next(g for g in m.groups()[1:] if g is not None)
        if m.group(1).lower() == "srcset":
            refs += [c.strip().split()[0] for c in value.split(",") if c.strip()]
        else:
            refs.append(value)
    for tag in META_TAG.findall(text):
        a = attrs_of(tag)
        if a.get("property", "").lower() in ("og:url", "og:image") and "content" in a:
            refs.append(a["content"])
    return refs


def target_file(path):
    """Site path (/about/, /404.html, /css/site.css) -> file under ROOT."""
    rel = path.lstrip("/")
    return ROOT / (rel + "index.html" if rel == "" or rel.endswith("/") else rel)


def check_links(pages):
    """Every internal href/src/srcset (and og:url/og:image) on a built page must exist, and #anchors must
    match an id on the target page (#top is always valid). External, mailto: and tel: links are not followed."""
    out, ids = [], {}
    def ids_of(f):
        if f not in ids:
            text = strip_inert(f.read_text(encoding="utf-8"))
            ids[f] = {next(g for g in m.groups() if g is not None) for m in ID_ATTR.finditer(text)}
        return ids[f]
    for page in pages:
        label = label_for(page)
        for ref in page_refs(page.read_text(encoding="utf-8")):
            ref = htmllib.unescape(ref)
            if ref.startswith(SITE):
                ref = ref[len(SITE):] or "/"
            if ref in ("", "#") or re.match(r"(?:[a-z][\w+.-]*:|//)", ref, flags=re.I):
                continue  # social placeholders, external, mailto:, tel:
            path, _, frag = ref.split("?")[0].partition("#")
            if path and not path.startswith("/"):
                out.append(f"{label}: relative link '{ref}' (use a root-relative path)")
                continue
            f = target_file(path) if path else page
            if not f.is_file():
                out.append(f"{label}: link '{ref}' points to a missing file")
            elif frag and frag.lower() != "top" and f.suffix == ".html" and frag not in ids_of(f):
                out.append(f"{label}: link '{ref}' points to a missing anchor #{frag}")
    return out


FM_LINE = re.compile(r"^([A-Za-z_][\w-]*):(?:[ \t]+(.*))?$")


def check_front_matter(path):
    """src/pages front matter must be valid YAML (GitHub Pages parses it): one 'key: value' per line, and a
    value containing ': ' or ' #', or starting with a YAML indicator, must be double-quoted."""
    path = Path(path)
    label = label_for(path)
    m = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), flags=re.S)
    if not m:
        return [f"{label}: missing front matter"]
    out = []
    for n, line in enumerate(m.group(1).splitlines(), 2):
        lm = FM_LINE.match(line)
        if not lm:
            out.append(f"{label}:{n}: front matter line is not 'key: value'")
            continue
        v = (lm.group(2) or "").strip()
        if v.startswith('"'):
            if not re.fullmatch(r'"(?:[^"\\]|\\.)*"', v):
                out.append(f"{label}:{n}: unterminated or broken double-quoted value")
        elif ": " in v or " #" in v or v.endswith(":") or (v and v[0] in "'&*!|>%@`{}[],?-:#"):
            out.append(f"{label}:{n}: value must be double-quoted to be valid YAML: {v[:40]}")
    return out


def check_js():
    """Regressions found in whole-site verification that only show in the browser."""
    js = (ROOT / "js" / "site.js").read_text(encoding="utf-8")
    out = []
    # Tab focus on a half-hidden Services index chip must scroll the chip row (Chrome does not on its own)
    if not re.search(r"\.svc-index ul'\)[\s\S]{0,400}focusin[\s\S]{0,200}scrollIntoView", js):
        out.append("js/site.js: Services index chip row no longer scrolls the focused chip into view")
    return out + check_logo_travel_js(js) + check_pausables_js(js)


LOGO_TRAVEL_GUARD = re.compile(
    r"if\s*\(\s*document\.querySelector\(\s*(['\"])\.hero \[data-hero-logo\]\1\s*\)\s*\)\s*initLogoTravel\(\s*\)")


def check_logo_travel_js(js, label="js/site.js"):
    """initLogoTravel() is defined once, honours reduced motion, and is called exactly once, guarded by
    the Home hero logo: if (document.querySelector('.hero [data-hero-logo]')) initLogoTravel();"""
    js = re.sub(r"/\*.*?\*/|(?<![:'\"\\])//[^\n]*", "", js, flags=re.S)
    out = []
    defs = re.findall(r"function\s+initLogoTravel\s*\(", js)
    if len(defs) != 1:
        out.append(f"{label}: expected one 'function initLogoTravel()', found {len(defs)}")
    else:
        body = js[js.index(re.search(r"function\s+initLogoTravel\s*\(", js).group(0)):]
        if not re.search(r"matchMedia\(\s*(['\"])\(prefers-reduced-motion: reduce\)\1\s*\)", body[:4000]):
            out.append(f"{label}: initLogoTravel must check matchMedia('(prefers-reduced-motion: reduce)')")
    calls = [m for m in re.finditer(r"(?<!function )(?<![\w.])initLogoTravel\s*\(\s*\)", js)]
    guarded = LOGO_TRAVEL_GUARD.findall(js)
    if len(calls) != 1 or len(guarded) != 1:
        out.append(f"{label}: initLogoTravel() must be called once, only when '.hero [data-hero-logo]' exists "
                   f"({len(calls)} call(s), {len(guarded)} guarded)")
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
    for src in sorted((ROOT / "src" / "pages").glob("*.html")):
        problems += check_front_matter(src)
    if not argv:
        problems += check_links(built_pages()) + check_js() + check_assets()
        site_css = ROOT / "css" / "site.css"
        problems += check_fan_present(site_css.read_text(encoding="utf-8"), label_for(site_css))
        problems += check_mobile_hero_order(site_css.read_text(encoding="utf-8"), label_for(site_css))
        problems += check_strips_css(site_css.read_text(encoding="utf-8"), label_for(site_css))
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
