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
        # Home pass item 2: the Selected work category cards (no client names) and the unchanged section copy
        "A few of the brands and products we've shaped. Some of our best work lives behind NDAs, ask us about it. "
        "Confidentiality is non-negotiable.",
        "Branding Collaterals", "Product Design",
        "Presentations", "Confidential", "Under NDA",
        "Our best work doesn't always get a public page. Ask us and we'll walk you through it.",
        "View all work",
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
        "Brands and digital products we've shaped. We work with teams where confidentiality matters, so not "
        "everything lives here. For the rest, let's chat. The Pandora's Box holds things that will keep you amazed.",
        "The Pandora's Box",
        "Want to see more?",
        "Some of our best work can only be shown in person.",
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
# Work index: rows of project tiles, (slug, card title) in order; each is one a.work-tile link to /work/<slug>/
# holding the cover (alt="", lazy, sized) and the title only. Never the emailers project or the landing pages.
WORK_TILES = [
    ("didac", "Didac Branding"),
    ("b2b-presentations", "B2B Presentations"),
    ("recruitment", "Recruitment Platform"),
]
# Recruitment case: brand-neutral (no client, product or designer names) and one request-by-email link.
RECRUITMENT_FORBIDDEN = ("Suraasa", "Radhika", "Johari", "ITU")
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
    out = check_style_text(text, label_for(path)) + check_cat_motion(text, label_for(path)) + check_all_motion(text, label_for(path))
    out += check_no_flipped_cats(text, label_for(path)) + check_manifest_refs(text, label_for(path))
    if "Crisp_Cat_" in text:
        out.append(f"{label_for(path)}: references a retired Crisp_Cat_* file")
    return out


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
    out += check_cats(text, label, page_slug(path))
    out += check_manifest_refs(text, label)
    if page_slug(path) is not None:
        out += check_hero(text, label, page_slug(path))
    if page_slug(path) == "services":
        out += check_services_index(text, label)
    if (page_slug(path) or "").startswith("work/"):
        out += check_case_page(text, label, page_slug(path))
    if page_slug(path) == "work/recruitment":
        out += check_recruitment(text, label)
    if page_slug(path) == "work":
        out += check_work_card_covers(text, label)
    if page_slug(path) == "home":
        out += check_home_sections(text, label) + check_work_row(text, label)

    return out


# Round 2, Task 3: Home "What we do" bento, the client ticker and the Why statement
BENTO_TILES = {  # anchor -> (official icon file, service tags)
    "/services/#strategy": ("Crisp_Icon_Strategy.svg", ("UX Audits", "User Research", "Journey Mapping", "Usability Testing")),
    "/services/#branding": ("Crisp_Icon_Branding.svg", ("Positioning", "Visual Identity", "Guidelines", "Brand Architecture")),
    "/services/#product": ("Crisp_Icon_UIUX.svg", ("UX & UI", "AI Experience", "Design Systems", "Prototyping")),
    "/services/#build": ("Crisp_Icon_DesignToCode.svg", ("Front-end", "Web Development", "Framer")),
}
JOB_WORDS = ["clarify", "engage", "convert", "simplify", "move someone to act"]
WHY_SENTENCE = "Everything we make has a job, to clarify, engage, convert, simplify or move someone to act."


def classes(el):
    return el["attrs"].get("class", "").split()


def inside(el, parent):
    return any(a is parent["attrs"] for _, _, a in el["ancestors"])


def norm_text(s):
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


BENTO_MODS = ("small", "small", "tall", "wide")  # by href: Strategy, Branding small; Product Design tall; Build wide


def check_home_sections(text, label):
    """Home: (1) four .bento tiles linking to the four Services anchors, each with its official icon in an
    .icon-chip and its service tags; (2) no services marquee (.svc-band / #svc-marquee / .marquee); (3) the client ticker (#track); (4) .why-statement carries the full Why sentence for
    screen readers and an aria-hidden .cycle of the five job words. Home pass item 4: no Pause/Play button
    ([data-pause]) and no [data-pausable] target anywhere on the page (the user removed them)."""
    out = []
    els = tag_contexts(text)
    bentos = [e for e in els if "bento" in classes(e)]
    if len(bentos) != 1:
        out.append(f"{label}: Home needs one .bento grid for What we do, found {len(bentos)}")
    for bento in bentos:
        links = [e for e in els if e["tag"] == "a" and inside(e, bento)]
        hrefs = [e["attrs"].get("href") for e in links]
        if hrefs != list(BENTO_TILES):
            out.append(f"{label}:{bento['line']}: .bento tiles must link to {list(BENTO_TILES)}, found {hrefs}")
        for a in links:
            want = BENTO_MODS[list(BENTO_TILES).index(a["attrs"].get("href"))] if a["attrs"].get("href") in BENTO_TILES else None
            if want and f"bento-tile--{want}" not in classes(a):
                out.append(f"{label}:{a['line']}: bento tile {a['attrs']['href']} needs the bento-tile--{want} modifier")
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
    for e in els:
        if "svc-band" in classes(e) or e["attrs"].get("id") == "svc-marquee" or "marquee" in classes(e):
            out.append(f"{label}:{e['line']}: the services marquee band is gone from Home (user removed it); delete it")
    tracks = [e for e in els if e["attrs"].get("id") == "track"]
    if len(tracks) != 1:
        out.append(f"{label}: Home needs the client logo ticker (#track)")
    for e in els:
        for attr in ("data-pause", "data-pausable"):
            if attr in e["attrs"]:
                out.append(f"{label}:{e['line']}: [{attr}] is gone from the site (no Pause/Play buttons); remove it")
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
            # Home pass item 5: each word span holds only the word; one static navy .why-dot period follows the cycle
            words = [norm_text(e["text"]) for e in els if e["tag"] == "span" and any(a is c["attrs"] for _, _, a in e["ancestors"][-1:])]
            if words != JOB_WORDS:
                out.append(f"{label}:{c['line']}: .cycle job words must be exactly {JOB_WORDS} (no period inside), found {words}")
            parent = c["ancestors"][-1][2] if c["ancestors"] else None
            dots = [e for e in els if "why-dot" in classes(e) and parent is not None and e["ancestors"] and e["ancestors"][-1][2] is parent]
            if len(dots) != 1 or norm_text(dots[0]["text"]) != "." or els.index(dots[0]) < els.index(c):
                out.append(f"{label}:{c['line']}: one .why-dot '.' must follow the .cycle in the same aria-hidden wrapper")
    return out


# Round 2: one logo per page (the navbar), cats only in small moments
LOGO_SRC = re.compile(r"Crisp_Logo|Crisp_Avatar_(?:Orange|Navy)")
CAT_SRC = re.compile(r"/cat-poses/|Crisp_Cat_|Crisp_Avatar_(?:Samosa|Idli)")
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


def in_class(el, cls):
    return any(cls in c for _, c, _ in el["ancestors"])


def check_services_index(text, label, css=None):
    """#process must be the LAST thing inside the container holding the sticky .svc-index (index ends with it)."""
    els = tag_contexts(text)
    nav = [e for e in els if "svc-index" in classes(e)]
    proc = [e for e in els if e["attrs"].get("id") == "process"]
    if not nav or not proc:
        return [f"{label}: Services needs .svc-index and #process"]
    holder = nav[0]["ancestors"][-1]
    if not any(a is holder or a[2] is holder[2] for a in proc[0]["ancestors"]):
        return [f"{label}: #process must sit inside the sticky index's container"]
    secs = [e["attrs"]["id"] for e in els if e["tag"] == "section" and e["attrs"].get("id") and any(a is holder or a[2] is holder[2] for a in e["ancestors"])]
    if secs[-1:] != ["process"]:
        return [f"{label}: #process must be the last section in the sticky index's container"]
    if css is None:
        css = (ROOT / "css" / "site.css").read_text(encoding="utf-8")
    if not re.search(r"\.svc-main\s*>\s*\.svc:last-child\s*\{[^}]*padding-bottom:\s*0\b", css):
        return [f"{label}: the last .svc must have padding-bottom: 0 so the index stops at the table's bottom edge"]
    return []


def check_hero(text, label, slug):
    """Round 2 Home hero. Every page: one [data-logo-slot] header brandmark (an <a href="/">) inside <header>.
    Home only: exactly one <img data-hero-logo> inside .hero (it travels into the slot), on no container: no
    .hero-art tray, no .fan/.fan-card cards and no client-logo or work image anywhere in the .hero."""
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
    for e in els:
        if not in_class(e, "hero") and "hero" not in e["attrs"].get("class", "").split():
            continue
        gone = {"hero-art", "fan", "fan-card"} & set(e["attrs"].get("class", "").split())
        if gone:
            out.append(f"{label}:{e['line']}: .{sorted(gone)[0]} is gone from the hero (no tray, no work cards)")
        if e["tag"] == "img" and re.search(r"/assets/(?:clients|work)/", e["attrs"].get("src", "")):
            out.append(f"{label}:{e['line']}: work/client image inside .hero ({e['attrs']['src']}); the hero holds only the logo")
    return out


def check_images(text, label, slug):
    """(a) no logo/croissant-avatar <img> outside <header>, except the Home hero logo (data-hero-logo inside
    .hero on index.html), which travels into the navbar; (b) no cat on the Work page or inside a .hero."""
    out = []
    if (slug or "").startswith("work/") and CAT_SRC.search(strip_inert(text)):
        out.append(f"{label}: a cat (Idli/Samosa) appears on a case page; cats never sit beside client work")
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


# Cats on the site: the official "Cat poses" set (assets/cat-poses/<Name>.svg, flat tracings: whole-figure motion
# only) and the two round avatars (assets/cats/Crisp_Avatar_Samosa|Idli.svg). The old table poses
# (Crisp_Cat_*) stay in the design system and never ship. slug -> [(file stem, classes/#ids it must sit inside)].
CAT_PLACEMENTS = {
    "contact": [("Samosa_06_standing_paws_up", ("form-card", "cat-peek")), ("Idli_04_peeking_over_edge", ("form-card", "cat-peek")),
                ("Samosa_09_head_tilt_sitting", ("#form-done",)), ("Idli_14_rolled_belly_up", ("#form-done",))],
    "404": [("Samosa_07_walking", ("lost-art",)), ("Idli_02_lying_on_back_stretched", ("lost-art",))],
    # Home: only Idli in the hammock on the closing card. No page has a footer cat.
    "home": [("idli-hammock", ("closer-card",))],
    "blog": [("idli-confused", ("#blog-empty",))],
    "about": [("idli-avatar", ("closer",))],
    "services": [("samosa-ball", ("closer-cat",))],
    "work": [("samosa-sitting", ("closer-card",))],  # the Work index closing only (user)
    "work/case": [],
}
CAT_FILE = re.compile(r"/assets/(?:cat-poses|cats|illustrations)/([\w-]+)\.svg")
WORK_MARKERS = ("case", "work-grid", "work-index", "work-row", "work-card")


def within(e, where):
    if where.startswith("#"):
        return any(a.get("id") == where[1:] for _, _, a in e["ancestors"])
    return any(where in c for _, c, _ in e["ancestors"])


def check_cats(text, label, slug):
    """Every page carries exactly its assigned cats, each in its moment's container; cats are decorative
    (alt="", never inside a link/button, no tabindex), never in a .hero, and never share a section with client
    work (.case, work cards). No reference to the retired Crisp_Cat_* table poses."""
    out = []
    if "Crisp_Cat_" in text:
        out.append(f"{label}: references a retired Crisp_Cat_* file; use assets/cat-poses or the round avatars")
    els = tag_contexts(text)
    cats = [(CAT_FILE.search(e["attrs"].get("src", "")).group(1), e) for e in els
            if e["tag"] == "img" and CAT_FILE.search(e["attrs"].get("src", ""))]
    work = [e for e in els if any(c in e["attrs"].get("class", "").split() for c in WORK_MARKERS)]
    for name, e in cats:
        if e["attrs"].get("alt") != "":
            out.append(f"{label}:{e['line']}: cat {name} needs alt=\"\" (decorative)")
        if "tabindex" in e["attrs"] or any(t in ("a", "button") for t, _, _ in e["ancestors"]):
            out.append(f"{label}:{e['line']}: cat {name} must not be focusable or sit inside a link/button")
        if in_class(e, "hero"):
            out.append(f"{label}:{e['line']}: cat {name} inside a .hero")
        sections = [a for t, _, a in e["ancestors"] if t in ("section", "footer", "header")]
        if sections and any(any(a is sections[-1] for _, _, a in w["ancestors"]) for w in work):
            out.append(f"{label}:{e['line']}: cat {name} shares a section with client work")
    slug = "work/case" if (slug or "").startswith("work/") else slug  # case pages: no cats
    if slug in CAT_PLACEMENTS:
        want = CAT_PLACEMENTS[slug]
        have = sorted(n for n, _ in cats)
        if have != sorted(n for n, _ in want):
            out.append(f"{label}: cats on the page {have} != the assigned placements {sorted(n for n, _ in want)}")
        for name, where in want:
            if not any(n == name and all(within(e, w) for w in where) for n, e in cats):
                out.append(f"{label}: {name} must sit inside {' > '.join(where)}")
    return out


MANIFEST_DIRS = ("assets/cats/", "assets/cat-poses/", "assets/icons/")


def manifest_files(manifest=None):
    manifest = Path(manifest or ROOT / "tools" / "assets.sha256")
    return {l.split("  ", 1)[1].strip() for l in manifest.read_text(encoding="utf-8").splitlines() if "  " in l}


def check_manifest_refs(text, label, manifest=None):
    """Pages and CSS reference only pinned files from the official asset folders (cats, cat poses, icons)."""
    listed = manifest_files(manifest)
    refs = page_refs(text) + re.findall(r"url\(\s*[\"']?([^\"')]+)", text)
    out = []
    for ref in refs:
        path = ref.split("?")[0].split("#")[0].lstrip("/")
        if path.startswith(MANIFEST_DIRS) and path not in listed:
            out.append(f"{label}: {ref} is not a pinned official asset (tools/assets.sha256)")
    return sorted(set(out), key=out.index)


CAT_SELECTOR = re.compile(r"\.cat\b|\.cat-|\.pose\b|\.pose-|\.scene-hammock|cat-poses|illustrations/|Crisp_Avatar")
FLIP = re.compile(r"scaleX\(\s*-|scale\(\s*-|scale\([^,)]*,\s*-|scale3d\(\s*-|rotateY\(|rotate3d\(\s*0\s*,\s*1|"
                  r"(?<![\w-])scale\s*:\s*-|(?<![\w-])rotate\s*:\s*y|matrix\(\s*-", re.I)


def check_no_flipped_cats(text, label):
    """Samosa's clipped ear is always on the viewer's right: CSS never mirrors a cat (negative x scale, rotateY,
    a negative matrix, or direction: rtl on a cat row), in a rule or in a @keyframes named cat-*."""
    out = []
    for sel, body, ats in css_rules(text):
        kf = next((a for a in ats if a.lower().startswith("@keyframes")), None)
        if kf and not re.search(r"@keyframes\s+cat-", kf):
            continue
        if kf or CAT_SELECTOR.search(sel):
            m = FLIP.search(body) or re.search(r"direction\s*:\s*rtl", body, flags=re.I)
            if m:
                out.append(f"{label}: '{kf or sel}' mirrors a cat ({m.group(0)}...); cats are never flipped")
    return out


def check_cat_manifest(manifest=None, dirs=None):
    """Every file in assets/cats/ and assets/cat-poses/ is pinned in tools/assets.sha256."""
    listed = manifest_files(manifest)
    out = []
    for d in dirs or (ROOT / "assets" / "cats", ROOT / "assets" / "cat-poses"):
        for f in sorted(Path(d).glob("*.svg")):
            rel = f"assets/{Path(d).name}/{f.name}"
            if rel not in listed:
                out.append(f"tools/assets.sha256: {rel} is not pinned (add its sha256)")
    return out


WORK_ASSETS = ROOT / "assets" / "work" / "projects"


def work_asset_files():
    return sorted(str(f.relative_to(ROOT)) for f in WORK_ASSETS.rglob("*") if f.is_file() and not f.name.startswith("."))


def check_work_assets(manifest=None):
    """Work case media: every file in tools/work-assets.sha256 exists and matches, and every file under
    assets/work/projects/ is pinned there."""
    manifest = Path(manifest or ROOT / "tools" / "work-assets.sha256")
    out = check_assets(manifest)
    listed = manifest_files(manifest)
    out += [f"tools/work-assets.sha256: {rel} is not pinned (add its sha256)" for rel in work_asset_files() if rel not in listed]
    return out


def check_illustrations(manifest=None):
    """Non-official illustrations (assets/illustrations/): every file in tools/illustrations.sha256 exists and matches."""
    return check_assets(manifest or ROOT / "tools" / "illustrations.sha256")


ILLUSTRATION_PALETTE = {"#021f53", "#4a5675", "#ffffff", "#dededa", "#feca98", "#fd9f0f", "#cc4806", "#4daf6b"}


def illustration_svg_files():
    return sorted((ROOT / "assets" / "illustrations").glob("*.svg")) + sorted((ROOT / "assets" / "work" / "projects").glob("*/*.svg"))


def check_illustration_svgs(files=None):
    """assets/illustrations/*.svg: Crisp palette only (6-digit hex from ILLUSTRATION_PALETTE, or none/currentColor),
    a viewBox and a <title>, and no script, embedded image or external reference."""
    out = []
    for f in files or illustration_svg_files():
        text, label = Path(f).read_text(encoding="utf-8"), label_for(Path(f))
        if not re.search(r"<svg\b[^>]*\sviewBox=\"[^\"]+\"", text):
            out.append(f"{label}: no viewBox")
        if not re.search(r"<title>[^<]+</title>", text):
            out.append(f"{label}: no <title>")
        if re.search(r"<(?:script|image|foreignObject)\b|\bon\w+=", text, re.I):
            out.append(f"{label}: script, event handler or embedded image")
        if re.search(r"(?:href\s*=\s*[\"']|url\(\s*[\"']?)(?!#)", text):
            out.append(f"{label}: external reference (only #fragment links allowed)")
        for v in re.findall(r"(?:fill|stroke|stop-color|color)\s*[:=]\s*\"?([^;\"}\s]+)", text):
            if v.lower() not in ILLUSTRATION_PALETTE | {"none", "currentcolor"}:
                out.append(f"{label}: colour {v} is not in the Crisp illustration palette")
        out += [f"{label}: colour {h} is not in the Crisp illustration palette" for h in
                re.findall(r"#[0-9a-fA-F]{3,8}\b", text) if h.lower() not in ILLUSTRATION_PALETTE]
    return sorted(set(out), key=out.index)


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
    @media (prefers-reduced-motion: no-preference), so reduced motion never sees them."""
    out = []
    for name, what in (("cat", "cat"),):
        out += [f"{label}: {what} animation on '{sel}' is not inside @media (prefers-reduced-motion: no-preference)"
                for sel, safe in motion_rules(text, name) if not safe]
    return out


NO_PREF = re.compile(r"prefers-reduced-motion\s*:\s*no-preference", re.I)


def check_all_motion(text, label):
    """Everything that moves on its own (ticker and any other animation) runs only under
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
    """The client .track scrolls only under no-preference; nothing pauses them (Home pass
    item 4: no Pause/Play buttons, so no .strip-pause/.is-paused/[data-pausable] CSS left, and no :hover pause)."""
    out = []
    rules = list(css_rules(text))
    for name in ("track",):
        if not any(re.search(rf"\.{name}(?![\w])|\.{name}-", sel) and NO_PREF.search(" ".join(ats))
                   and re.search(r"(?<![\w-])animation\s*:\s*(?!none)", body) for sel, body, ats in rules):
            out.append(f"{label}: no .{name} scroll animation inside @media (prefers-reduced-motion: no-preference)")
    for sel, body, _ in rules:
        if re.search(r"\.strip-pause|\.is-paused|data-pausable|data-paused|\.why-bar|\.strip-bar|\.i-play|\.i-pause", sel):
            out.append(f"{label}: '{sel.strip()}' styles the removed Pause/Play buttons; delete it")
        if ":hover" in sel and re.search(r"animation-play-state\s*:\s*paused", body):
            out.append(f"{label}: '{sel}' pauses a strip on :hover; the strips never pause")
    # the 1.04 work-card zoom is for cards that are links only, so plain cards never look clickable
    for sel, body, _ in rules:
        if re.search(r"scale\(\s*1\.04\s*\)", body):
            for part in split_top(sel):
                if re.search(r"(?<![\w-])\.card(?![\w-])", part) and not re.search(r"(?<![\w-])a\.card(?![\w-])", part):
                    out.append(f"{label}: '{part.strip()}' zooms a card that may not be a link; use a.card")
    return out


def check_no_pausables_js(js, label="js/site.js"):
    """Home pass item 4: the Pause/Play buttons are gone, so no initPausables, [data-pause], .is-paused or
    "pausechange" code is left. The Why job-word .cycle still checks reduced motion."""
    js = re.sub(r"/\*.*?\*/|(?<![:'\"\\])//[^\n]*", "", js, flags=re.S)
    out = []
    for need, what in ((r"initPausables", "initPausables"), (r"data-pause", "[data-pause]/[data-pausable]"),
                       (r"is-paused", ".is-paused"), (r"pausechange", "the pausechange event")):
        if re.search(need, js):
            out.append(f"{label}: {what} is left over from the removed Pause/Play buttons")
    cyc = re.search(r"\.cycle", js)
    near = js[cyc.start():cyc.start() + 2500] if cyc else ""
    if not re.search(r"prefers-reduced-motion: reduce", near):
        out.append(f"{label}: the Why job-word .cycle must check matchMedia('(prefers-reduced-motion: reduce)')")
    if cyc and "why-dot" not in near:
        out.append(f"{label}: the Why job-word .cycle must place the .why-dot period after the word shown")
    return out


LOGO_MIN_PX = 120  # brand skill: the Crisp logo is never under 120px wide on screen


def css_px(value, tokens):
    """Evaluate a simple length (px, var(--token), calc with + - * /) to px; None if it can't."""
    expr = value.strip()
    for _ in range(5):
        expr = re.sub(r"var\(\s*(--[\w-]+)\s*(?:,[^()]*)?\)", lambda m: tokens.get(m.group(1), "NaN"), expr)
    expr = re.sub(r"calc\(", "(", expr)
    expr = re.sub(r"(\d*\.?\d+)px", r"\1", expr)
    if not re.fullmatch(r"[\d.\s+\-*/()]+", expr):
        return None
    try:
        return float(eval(expr, {"__builtins__": {}}))
    except Exception:
        return None


def css_tokens(*texts):
    toks = {}
    for t in texts:
        for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;}]+)", strip_comments(t)):
            toks.setdefault(m.group(1), m.group(2).strip())
    return toks


def check_header_logo(text, label, tokens_text=""):
    """The navbar logo (.brandmark img / [data-logo-slot] img) is at least 120px wide at every breakpoint
    (every width declaration in any @media resolves to >= 120px; height stays auto), and the header height
    is one variable, --nav-h: the bar height, html scroll-padding-top and the Services index sticky top use it
    (the 72px --layout-nav-height token no longer drives anything)."""
    out = []
    tokens = css_tokens(text, tokens_text)
    widths = []
    for sel, body, ats in css_rules(text):
        if not re.search(r"\.brandmark\s+img|\[data-logo-slot\]\s+img", sel):
            continue
        for prop, val in re.findall(r"(?<![\w-])(width|min-width|max-width|height|max-height)\s*:\s*([^;}]+)", body):
            where = f"{label}: {sel.strip()} {prop}: {val.strip()}" + (f" in {' '.join(ats)}" if ats else "")
            if prop in ("height", "max-height"):
                if val.strip() != "auto":
                    out.append(f"{where}: the header logo height must be auto (width drives it)")
                continue
            px = css_px(val, tokens)
            if px is None or px < LOGO_MIN_PX:
                out.append(f"{where}: header logo {prop} is under {LOGO_MIN_PX}px (or unreadable)")
            if prop == "width":
                widths.append(px)
    if not widths:
        out.append(f"{label}: no width declared for the header logo (.brandmark img); it must be >= {LOGO_MIN_PX}px")
    nav_h = css_px("var(--nav-h)", tokens)
    if nav_h is None:
        out.append(f"{label}: --nav-h (header height) is not defined")
    for sel, body, ats in css_rules(text):
        for prop, val in re.findall(r"(?<![\w-])(scroll-padding-top|height|top)\s*:\s*([^;}]+)", body):
            uses_old = "--layout-nav-height" in val
            needs = (prop == "scroll-padding-top") or (prop == "height" and re.search(r"\.site-head\s+\.bar", sel)) \
                or (prop == "top" and ".svc-index" in sel and "sticky" in body)
            if uses_old or (needs and "var(--nav-h)" not in val):
                out.append(f"{label}: {sel.strip()} {prop}: {val.strip()} must use var(--nav-h), the one header height")
    return out


def check_bento_layout(text, label):
    """Home bento: the asymmetric layout (tall tile spanning two rows, small tiles stacked beside it, wide tile
    along the bottom) lives inside @media (min-width: 1024px)."""
    found = {"tall": False, "small": False, "wide": False}
    for sel, body, ats in css_rules(text):
        if any(re.search(r"min-width\s*:\s*1024px", a) for a in ats):
            for k, pat in (("tall", r"grid-row\s*:\s*(?:1\s*/\s*)?span 2"), ("small", r"grid-column\s*:\s*2"), ("wide", r"grid-column\s*:\s*1\s*/\s*-1|display\s*:\s*grid")):
                if re.search(rf"\.bento-tile--{k}(?![\w-])", sel) and re.search(pat, body):
                    found[k] = True
    return [f"{label}: .bento-tile--{k} needs its asymmetric grid rule inside @media (min-width: 1024px)" for k, ok in found.items() if not ok]


def check_hero_layout(text, label):
    """Home hero layout: below 1024px (phones and tablets) one column with the logo spot first and centred:
    under @media (max-width: 1023px) .hero-logo-spot has an `order` lower than .hero-copy's and
    justify-self: center. Two columns (.hero-grid grid-template-columns with 2+ tracks) only inside
    @media (min-width: 1024px+). No .hero-art tray or .fan card CSS left behind."""
    rules = list(css_rules(text))
    def decl(prop, sel_re):
        for sel, body, ats in rules:
            if any(re.search(r"max-width\s*:\s*1023px", a) for a in ats) and re.search(sel_re, sel):
                m = re.search(rf"(?<![\w-]){prop}\s*:\s*([^;}}]+)", body)
                if m:
                    return m.group(1).strip()
        return None
    out = []
    spot, copy = decl("order", r"\.hero-logo-spot(?![\w-])"), decl("order", r"\.hero-copy(?![\w-])") or "0"
    try:
        if spot is None or int(spot) >= int(copy):
            out.append(f"{label}: under max-width: 1023px .hero-logo-spot needs an order lower than .hero-copy ({spot} vs {copy})")
    except ValueError:
        out.append(f"{label}: unreadable hero order ({spot} vs {copy})")
    if decl("justify-self", r"\.hero-logo-spot(?![\w-])") != "center":
        out.append(f"{label}: under max-width: 1023px .hero-logo-spot must be centred (justify-self: center)")
    two_col = 0
    for sel, body, ats in rules:
        if re.search(r"(?:^|[\s,])\.hero-art(?![\w-])|\.fan(?:-[\w-]+)?(?![\w-])", sel):
            out.append(f"{label}: '{sel.strip()}' styles the removed hero tray/card fan; delete it")
        if not re.search(r"\.hero-grid(?![\w-])", sel):
            continue
        m = re.search(r"grid-template-columns\s*:\s*([^;}]+)", body)
        if not m or len(split_top(m.group(1).strip(), " ")) < 2 and "repeat(" not in m.group(1):
            continue
        mins = [int(x) for a in ats for x in re.findall(r"min-width\s*:\s*(\d+)px", a)]
        if mins and max(mins) >= 1024:
            two_col += 1
        else:
            out.append(f"{label}: .hero-grid two-column layout '{m.group(1).strip()}' must only apply from min-width: 1024px")
    if not two_col:
        out.append(f"{label}: no two-column .hero-grid inside @media (min-width: 1024px)")
    return out


# Home pass item 2: "Selected work" is one horizontally scrollable row of CATEGORY cards (no client names), each a
# link with a large flat icon on a Crisp brand colour. (href, title, meta) in order.
WORK_CARDS = [
    ("/work/didac/", "Branding Collaterals", None),
    ("/work/recruitment/", "Product Design", None),
    ("/work/b2b-presentations/", "Presentations", None),
    ("mailto:team@crispstudio.in?subject=Hello%20Crisp", "Confidential", "Under NDA"),
]
WORK_ROW_LABEL = "Selected work categories"
CLIENT_NAMES = ("HDFC", "Mind Mojo", "NMIMS", "HDB", "SAATH", "Kaamna")


def check_work_row(text, label):
    """Home: one scroll region (role="region", aria-label WORK_ROW_LABEL, tabindex="0") holding exactly the four
    a.work-card links of WORK_CARDS in order, each with an h3 title (the three category cards: the title only, no
    count or description, so no digits or "pieces/decks/Standees..."; the NDA card keeps its .work-meta) and one aria-hidden
    .work-icon <svg>; Previous/Next <button type="button" aria-controls=row id> (aria-labelled); no client
    names or client logos in the section; "View all work" still links to /work/."""
    out = []
    els = tag_contexts(text)
    rows = [e for e in els if e["attrs"].get("role") == "region" and e["attrs"].get("aria-label") == WORK_ROW_LABEL]
    if len(rows) != 1:
        return [f"{label}: Home needs one role=\"region\" aria-label=\"{WORK_ROW_LABEL}\" work row, found {len(rows)}"]
    row = rows[0]
    if row["attrs"].get("tabindex") != "0" or not row["attrs"].get("id"):
        out.append(f"{label}:{row['line']}: the work row needs an id and tabindex=\"0\" (keyboard-scrollable region)")
    cards = [e for e in els if e["tag"] == "a" and "work-card" in classes(e) and inside(e, row)]
    got = []
    for a in cards:
        title = next((norm_text(e["text"]) for e in els if e["tag"] == "h3" and inside(e, a)), None)
        meta = next((norm_text(e["text"]) for e in els if "work-meta" in classes(e) and inside(e, a)), None)
        got.append((a["attrs"].get("href"), title, meta))
        if meta is None:
            words = " ".join(e["text"] for e in els if inside(e, a)) + " " + " ".join(
                v for e in els if inside(e, a) or e is a for k, v in e["attrs"].items() if k in ("aria-label", "title", "alt"))
            if re.search(r"\d|piece|deck|standee|brochure|bookmark", words, re.I) or norm_text(a["text"]) != title:
                out.append(f"{label}:{a['line']}: category card {title!r} must show its title only (no count or description)")
        icons = [e for e in els if "work-icon" in classes(e) and inside(e, a)]
        if len(icons) != 1 or icons[0]["attrs"].get("aria-hidden") != "true" or \
                not any(e["tag"] == "svg" and inside(e, icons[0]) for e in els):
            out.append(f"{label}:{a['line']}: work card {a['attrs'].get('href')} needs one aria-hidden .work-icon with an inline <svg>")
    if got != WORK_CARDS:
        out.append(f"{label}:{row['line']}: work cards must be {WORK_CARDS}, found {got}")
    rid = row["attrs"].get("id")
    btns = [e for e in els if e["tag"] == "button" and rid and e["attrs"].get("aria-controls") == rid]
    names = sorted(e["attrs"].get("aria-label", "") for e in btns)
    if names != ["Next", "Previous"] or any(e["attrs"].get("type") != "button" for e in btns):
        out.append(f"{label}:{row['line']}: the work row needs Previous and Next <button type=\"button\" aria-label aria-controls=\"{rid}\">, found {names}")
    section = next((a for t, _, a in reversed(row["ancestors"]) if t == "section"), None)
    if section is not None:
        inner = [e for e in els if any(a is section for _, _, a in e["ancestors"])]
        words = " ".join(e["text"] for e in inner if e["tag"] in ("h2", "h3", "p", "span", "a"))
        hits = [n for n in CLIENT_NAMES if n in words]
        hits += [e["attrs"]["src"] for e in inner if e["tag"] == "img" and "/assets/clients/" in e["attrs"].get("src", "")]
        if hits:
            out.append(f"{label}: the Selected work section names clients {hits}; it shows categories only")
        if not any(e["tag"] == "a" and e["attrs"].get("href") == "/work/" and norm_text(e["text"]) == "View all work" for e in inner):
            out.append(f"{label}: the Selected work section lost its 'View all work' link")
    return out


# Cards are grey (--surface) by default. User override (Home pass item 2): only .work-card may sit on a brand
# colour; any other card with a navy/cream/orange/rust background fails. Each .work-card colour pair must reach
# 4.5:1, and white text never sits on orange.
CARD_CLASSES = ("card", "tile", "post", "closer-card", "case", "form-card", "svc-card", "work-card", "bento-tile", "table-wrap")
BRAND_BG = {"--navy": "#021F53", "--cream": "#FECA98", "--orange": "#FF8A00", "--orange-hover": "#FF6A00",
            "--brand-orange": "#FD9F0F", "--burnt": "#CC4806"}


def luminance(hex_):
    h = hex_.lstrip("#")
    h = "".join(c * 2 for c in h) if len(h) == 3 else h[:6]
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def resolve_colour(value, tokens):
    value = value.strip()
    for _ in range(4):
        value = re.sub(r"var\(\s*(--[\w-]+)\s*(?:,[^()]*)?\)", lambda m: tokens.get(m.group(1), m.group(0)), value).strip()
    if value.lower() == "white":
        return "#FFFFFF"
    m = HEX.fullmatch(value)
    return m.group(0).upper() if m else None


def check_card_colours(text, label, tokens_text=""):
    out = []
    tokens = css_tokens(tokens_text, text)
    brand = {v.upper() for v in BRAND_BG.values()}
    card_re = re.compile(r"\.(?:%s)(?:--[\w-]+)?(?![\w-])" % "|".join(map(re.escape, CARD_CLASSES)))
    for sel, body, ats in css_rules(text):
        bg = re.search(r"(?<![\w-])background(?:-color)?\s*:\s*([^;}]+)", body)
        if not bg:
            continue
        colour = resolve_colour(bg.group(1), tokens)
        if colour not in brand:
            continue
        for part in split_top(sel):
            subject = re.split(r"\s*[\s>+~]\s*", part.strip())[-1]  # the element the rule paints
            if not card_re.search(subject):
                continue
            if not re.search(r"\.work-card(?:--[\w-]+)?(?![\w-])", subject):
                out.append(f"{label}: '{part.strip()}' puts a card on a brand colour ({colour}); only .work-card may (cards are grey)")
                continue
            fg = re.search(r"(?<![\w-])color\s*:\s*([^;}]+)", body)
            fgc = resolve_colour(fg.group(1), tokens) if fg else None
            if fgc is None:
                out.append(f"{label}: '{part.strip()}' sets a brand background without a text colour")
            elif contrast(fgc, colour) < 4.5:
                out.append(f"{label}: '{part.strip()}' text {fgc} on {colour} is {contrast(fgc, colour):.2f}:1, under 4.5:1")
    return out


# Orange is never a text colour on white (Golden Bake #FD9F0F on white is 2.07:1, #FF8A00 2.33:1): `color:` in the
# orange family is for icons and svgs only. One documented, user-chosen exception (Home pass item 5, "this rolling
# text should have brands yellow colour"): the swapping Why Crisp job words, at Display XL (88/48px, bold) only.
# Their period stays navy, and the static fallback sentence stays navy.
ORANGE_TEXT_OK = (".why-statement .cycle > span",)
ORANGE_FAMILY = {"#FD9F0F", "#FF8A00", "#FF6A00"}


def check_orange_text(text, label, tokens_text=""):
    out = []
    tokens = css_tokens(tokens_text, text)
    for sel, body, ats in css_rules(text):
        if any(a.lower().startswith("@keyframes") for a in ats):
            continue
        m = re.search(r"(?<![\w-])color\s*:\s*([^;}]+)", body)
        if not m or resolve_colour(m.group(1), tokens) not in ORANGE_FAMILY:
            continue
        for part in split_top(sel):
            part = re.sub(r"\s+", " ", part.strip())
            subject = re.split(r"\s*[\s>+~]\s*", part)[-1]
            if part in ORANGE_TEXT_OK or re.search(r"svg|icon", subject):
                continue
            out.append(f"{label}: '{part}' sets orange text ({m.group(1).strip()}); orange is for icons only "
                       f"(the one exception is {ORANGE_TEXT_OK[0]}, the Why job words)")
    return out


# Home pass item 1 ("On desktop the logo can be bigger"): the hero logo width (--logo-w on .hero-grid) per
# breakpoint, keyed by the @media min-width it applies from (0 = no media query). Phones and tablets keep 160/200px.
HERO_LOGO_W = {0: 160, 600: 200, 1024: 320, 1280: 400}


def check_hero_logo_sizes(text, label, tokens_text=""):
    """Every --logo-w declaration on .hero-grid resolves to px and the set is exactly HERO_LOGO_W (by min-width)."""
    tokens = css_tokens(text, tokens_text)
    found = {}
    for sel, body, ats in css_rules(text):
        if not re.search(r"\.hero-grid(?![\w-])", sel):
            continue
        for val in re.findall(r"--logo-w\s*:\s*([^;}]+)", body):
            mins = [int(x) for a in ats for x in re.findall(r"min-width\s*:\s*(\d+)px", a)]
            found[max(mins) if mins else 0] = css_px(val, tokens)
    if found != HERO_LOGO_W:
        return [f"{label}: hero logo widths by min-width {found} must be {HERO_LOGO_W}"]
    return []


# Home pass item 3: the closing card's hammock sways constantly and subtly (about its cords' top, never mirrored,
# only when motion is fine): rotate within 2.5-3deg each way, 5-6s, ease-in-out, infinite alternate.
def check_hammock_css(text, label):
    out = []
    rules = list(css_rules(text))
    sway = None
    for sel, body, ats in rules:
        if any(a.lower().startswith("@keyframes") for a in ats) or not re.search(r"\.scene-hammock(?![\w-])", sel):
            continue
        anim = re.search(r"(?<![\w-])animation\s*:\s*([^;}]+)", body)
        if anim and NO_PREF.search(" ".join(ats)):
            sway = anim.group(1)
    if not sway:
        return [f"{label}: no .scene-hammock sway animation inside @media (prefers-reduced-motion: no-preference)"]
    secs = [float(s) for s in re.findall(r"(?<![\w.])(\d*\.?\d+)s(?![\w])", sway)]
    if not secs or not 5 <= secs[0] <= 6:
        out.append(f"{label}: the hammock sway must last 5-6s ('{sway.strip()}')")
    for word in ("infinite", "alternate", "ease-in-out"):
        if word not in sway:
            out.append(f"{label}: the hammock sway must be {word} ('{sway.strip()}')")
    name = next((w for w in sway.split() if w.startswith("cat-")), None)
    frames = [body for sel, body, ats in rules if name and any(re.fullmatch(rf"@keyframes\s+{re.escape(name)}", a.strip()) for a in ats)]
    degs = [abs(float(d)) for f in frames for d in re.findall(r"rotate\(\s*(-?\d*\.?\d+)deg", f)]
    if not degs or not all(2.5 <= d <= 3 for d in degs):
        out.append(f"{label}: @keyframes {name} must rotate 2.5-3deg each way (found {degs})")
    origins = [m for sel, body, ats in rules if re.search(r"\.scene-hammock(?![\w-])", sel)
               for m in re.findall(r"transform-origin\s*:\s*([^;}]+)", body)]
    if not origins or not re.fullmatch(r"\s*[\d.]+%\s+(?:0|[0-5](?:\.\d+)?%)\s*", origins[-1]):
        out.append(f"{label}: .scene-hammock must turn about its cords' top (transform-origin: <x>% <0-5%>), found {origins}")
    for sel, body, ats in rules:
        if re.search(r"cat--nudge|Samosa_01", sel + body) or any("cat-nudge" in a for a in ats):
            out.append(f"{label}: '{sel.strip()}' is left over from the removed Samosa nudge")
    return out


def check_closer_cat_css(text, label):
    """Services closing: Samosa with the ball stands on the card's top edge toward the LEFT (left inset, never
    right), unflipped."""
    rules = [(sel, body) for sel, body, ats in css_rules(text) if re.search(r"\.closer-cat(?![\w-])", sel)]
    out = []
    if not any(re.search(r"(?<![\w-])left\s*:", b) for _, b in rules):
        out.append(f"{label}: .closer-cat must be placed with a left inset (Samosa on the left of the box)")
    for sel, body in rules:
        if re.search(r"(?<![\w-])right\s*:", body):
            out.append(f"{label}: '{sel.strip()}' sets right; Samosa sits on the left of the box")
        if re.search(r"scaleX\(\s*-|scale\(\s*-", body):
            out.append(f"{label}: '{sel.strip()}' mirrors the cat")
    return out


def page_slug(path):
    path = Path(path).resolve()
    if path == ROOT / "index.html":
        return "home"
    if path == ROOT / "404.html":
        return "404"
    if path.name == "index.html" and path.parent.parent == ROOT:
        return path.parent.name
    if path.name == "index.html" and path.parent.parent.parent == ROOT and path.parent.parent.name == "work":
        return f"work/{path.parent.name}"  # nested case pages (src/pages/work/<slug>.html)
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
    if slug == "work":
        out += check_work_index(text, label)
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


def check_work_index(text, label):
    """Work: exactly the WORK_TILES links in order; each tile shows its cover (alt="", width/height, lazy) and
    its title only (no counts, descriptions, tags); no filter chips or counts; never the emailers project."""
    out = []
    els = tag_contexts(text)
    tiles = [e for e in els if e["tag"] == "a" and "work-tile" in classes(e)]
    got = [(e["attrs"].get("href"), norm_text(e["text"])) for e in tiles]
    want = [(f"/work/{s}/", t) for s, t in WORK_TILES]
    if got != want:
        out.append(f"{label}: work tiles must be {want} (title only), found {got}")
    for a in tiles:
        imgs = [e for e in els if e["tag"] == "img" and inside(e, a)]
        if len(imgs) != 1:
            out.append(f"{label}:{a['line']}: tile {a['attrs'].get('href')} needs one cover image")
            continue
        at = imgs[0]["attrs"]
        if at.get("alt") != "" or at.get("loading") != "lazy" or not at.get("width") or not at.get("height"):
            out.append(f"{label}:{a['line']}: tile cover needs alt=\"\" (the title names it), loading=\"lazy\", width and height")
        if any(e["tag"] in ("p", "span") and inside(e, a) and norm_text(e["text"]) for e in els):
            out.append(f"{label}:{a['line']}: tile {a['attrs'].get('href')} shows more than its title")
    if re.search(r'class="vault"', text):
        out.append(f"{label}: the confidential vault block was removed from the closing card")
    if re.search(r"data-filter|work-count|class=\"chip|emailer|Sure Journey|CPAT|PgCTL|M\.Ed|Research Platform", text, re.I):
        out.append(f"{label}: the Work page has no filters, counts or emailers project")
    return out


def check_case_page(text, label, slug):
    """Work case pages: .case-page with a .case-text column (back link to /work/, one h1, a .case-next link to the
    next case in WORK_TILES order, wrapping) and a .case-media column. Media images carry alt text, width/height and
    loading="lazy"; videos are named (aria-label), muted, loop, playsinline, preload="metadata", with a poster and
    no autoplay attribute (JS plays them in view, only when motion is fine)."""
    out = []
    els = tag_contexts(text)
    slugs = [s for s, _ in WORK_TILES]
    me = slug.split("/", 1)[1]
    if me not in slugs:
        return [f"{label}: {slug} is not a listed Work case"]
    nxt = f"/work/{slugs[(slugs.index(me) + 1) % len(slugs)]}/"
    text_col = [e for e in els if "case-text" in classes(e)]
    media = [e for e in els if "case-media" in classes(e)]
    if not any("case-page" in classes(e) for e in els) or len(text_col) != 1 or len(media) != 1:
        return [f"{label}: a case page needs .case-page, one .case-text and one .case-media"]
    inner = [e for e in els if inside(e, text_col[0])]
    if not any(e["tag"] == "a" and e["attrs"].get("href") == "/work/" for e in inner):
        out.append(f"{label}: the case text needs a link back to /work/")
    if sum(e["tag"] == "h1" for e in els) != 1 or not any(e["tag"] == "h1" for e in inner):
        out.append(f"{label}: the case title is the page's one h1, in .case-text")
    if not any(e["tag"] == "a" and "case-next" in classes(e) and e["attrs"].get("href") == nxt for e in inner):
        out.append(f"{label}: the Next project link must go to {nxt}")
    for e in els:
        if not inside(e, media[0]):
            continue
        a = e["attrs"]
        if e["tag"] == "img" and (not a.get("alt") or a.get("loading") != "lazy" or not a.get("width") or not a.get("height")):
            out.append(f"{label}:{e['line']}: case image needs alt text, width, height and loading=\"lazy\"")
        if e["tag"] == "video":
            if not a.get("aria-label") or not a.get("poster") or a.get("preload") != "metadata" or "autoplay" in a \
                    or not all(k in a for k in ("muted", "loop", "playsinline")):
                out.append(f"{label}:{e['line']}: case video needs aria-label, poster, muted loop playsinline preload=\"metadata\", no autoplay")
    return out


def check_recruitment(text, label):
    """work/recruitment: no client/designer names anywhere; exactly one mailto: to team@crispstudio.in whose
    subject names the Recruitment Platform; one media image, the brand diagram (alt, width, height, lazy); no
    .png/.jpg anywhere in <main> (no product screens)."""
    from urllib.parse import unquote
    out = [f"{label}: names '{w}' (the case is brand-neutral)" for w in RECRUITMENT_FORBIDDEN
           if re.search(rf"\b{w}\b", text, re.I)]
    mails = re.findall(r'href="(mailto:[^"]*)"', text)
    ok = [m for m in mails if m.lower().startswith("mailto:team@crispstudio.in?")
          and "Recruitment Platform" in unquote(htmllib.unescape(m).split("subject=", 1)[-1].split("&")[0])]
    if len(ok) != 1:
        out.append(f"{label}: needs exactly one mailto:team@crispstudio.in link with a subject naming the Recruitment Platform (found {mails})")
    els = tag_contexts(text)
    media = [e for e in els if "case-media" in classes(e)]
    imgs = [e for e in els if e["tag"] == "img" and media and inside(e, media[0])]
    if len(imgs) != 1 or not all(e["attrs"].get(k) for e in imgs for k in ("alt", "width", "height")) \
            or any(e["attrs"].get("loading") != "lazy" or not e["attrs"].get("src", "").endswith(".svg") for e in imgs):
        out.append(f"{label}: the case media needs exactly one lazy .svg diagram with alt, width and height (found {len(imgs)})")
    body = text.split("<main", 1)[-1]
    out += [f"{label}: raster image {m} (no product screens on this case)" for m in re.findall(r"[\w/.-]+\.(?:png|jpe?g)\b", body, re.I)]
    return out


def check_work_card_covers(text, label):
    """work index: every card cover is its own flat icon, /assets/work/projects/<slug>/cover-icon.svg; no raster covers."""
    out = []
    for slug, _ in WORK_TILES:
        m = re.search(rf'href="/work/{slug}/".*?<img\b[^>]*src="([^"]+)"', text, re.S)
        want = f"/assets/work/projects/{slug}/cover-icon.svg"
        if not m or m.group(1) != want:
            out.append(f"{label}: the {slug} card cover must be {want} (found {m and m.group(1)})")
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


def check_sitemap(locs=None):
    """sitemap.xml lists every indexable built page (no 404, no noindex), nested case pages included."""
    if locs is None:
        locs = [l[len(SITE):] for l in re.findall(r"<loc>([^<]+)</loc>", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))]
    out = []
    for page in built_pages():
        text = page.read_text(encoding="utf-8")
        if page.name == "404.html" or re.search(r'<meta name="robots" content="[^"]*noindex', text):
            continue
        path = "/" + str(page.parent.relative_to(ROOT)).replace(".", "") + "/" if page.parent != ROOT else "/"
        path = path.replace("//", "/")
        if path not in locs:
            out.append(f"sitemap.xml: {path} is missing (run tools/build.py)")
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
    return out + check_logo_travel_js(js) + check_no_pausables_js(js)


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
    pages += list((ROOT / "work").glob("*/index.html"))  # nested case pages
    pages += [ROOT / "index.html", ROOT / "404.html"]
    return sorted(p for p in pages if p.exists())


def main(argv):
    if argv:
        targets = [Path(a).resolve() for a in argv]
    else:
        targets = sorted((ROOT / "css").glob("*.css")) + built_pages()
    problems = check_sources()
    for src in sorted((ROOT / "src" / "pages").rglob("*.html")):
        problems += check_front_matter(src)
    if not argv:
        problems += check_links(built_pages()) + check_js() + check_assets() + check_cat_manifest() + check_work_assets() + check_illustrations() + check_illustration_svgs() + check_sitemap()
        site_css = ROOT / "css" / "site.css"
        problems += check_hero_layout(site_css.read_text(encoding="utf-8"), label_for(site_css))
        problems += check_bento_layout(site_css.read_text(encoding="utf-8"), label_for(site_css))
        problems += check_card_colours(site_css.read_text(encoding="utf-8"), label_for(site_css),
                                       (ROOT / "css" / "tokens.css").read_text(encoding="utf-8"))
        problems += check_orange_text(site_css.read_text(encoding="utf-8"), label_for(site_css),
                                      (ROOT / "css" / "tokens.css").read_text(encoding="utf-8"))
        problems += check_closer_cat_css(site_css.read_text(encoding="utf-8"), label_for(site_css))
        problems += check_hammock_css(site_css.read_text(encoding="utf-8"), label_for(site_css))
        problems += check_hero_logo_sizes(site_css.read_text(encoding="utf-8"), label_for(site_css),
                                          (ROOT / "css" / "tokens.css").read_text(encoding="utf-8"))
        problems += check_header_logo(site_css.read_text(encoding="utf-8"), label_for(site_css),
                                      (ROOT / "css" / "tokens.css").read_text(encoding="utf-8"))
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
