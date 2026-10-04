#!/usr/bin/env python3
"""Stamp the shared partials into every src/pages/<slug>.html and write the site.

A page file starts with optional front matter, then the <main> body:

    ---
    title: Work — Crisp
    desc: One-sentence description.
    ogdesc: Social-card description   (optional, defaults to desc)
    robots: noindex        (optional)
    ---
    <main id="main"> ... </main>

Output: home -> index.html, 404 -> 404.html, <slug> -> <slug>/index.html.
"""
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTIALS = ROOT / "src" / "partials"
PAGES = ROOT / "src" / "pages"
NAV_SLUGS = ("work", "services", "about", "blog", "contact")
SCRIPT = '<script src="/js/site.js" defer></script>\n'
NO_CAT_SLUGS = ("work",)  # cats never sit beside client work: the footer Idli is left off these pages


def read(name):
    return (PARTIALS / name).read_text(encoding="utf-8")


def split_front_matter(text, source):
    m = re.match(r"---\n(.*?)\n---\n", text, flags=re.S)
    if not m:
        raise SystemExit(f"{source}: missing front matter (title, desc)")
    meta = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    return {k.strip(): unquote(v.strip()) for k, v in meta.items()}, text[m.end():]


def unquote(value):
    """Front matter is YAML: a value holding ": " must be double-quoted, so drop the quotes here."""
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return value


def output_path(slug):
    if slug == "home":
        return ROOT / "index.html", "/"
    if slug == "404":
        return ROOT / "404.html", "/404.html"
    return ROOT / slug / "index.html", f"/{slug}/"


def render(slug, meta, body):
    _, path = output_path(slug)
    head = read("head.html").replace("{{title}}", meta["title"]).replace("{{ogdesc}}", meta.get("ogdesc", meta["desc"]))
    head = head.replace("{{desc}}", meta["desc"])
    head = head.replace("{{slug}}", slug).replace("{{path}}", path)
    if meta.get("robots"):  # optional front matter, e.g. "robots: noindex" on the 404 page
        head = head.replace("<meta name=\"description\"", f'<meta name="robots" content="{meta["robots"]}">\n<meta name="description"', 1)
    if "noindex" in meta.get("robots", ""):  # a page kept out of the index gets no canonical or og:url
        head = re.sub(r'<link rel="canonical"[^>]*>\n|<meta property="og:url"[^>]*>\n', "", head)
    header = read("header.html")
    for s in NAV_SLUGS:
        header = header.replace("{{cur:%s}}" % s, ' aria-current="page"' if s == slug else "")
    footer = read("footer.html").replace("{{year}}", str(datetime.date.today().year))
    footer = re.sub(r"[ \t]*\{\{cat\}\}.*?\{\{/cat\}\}\n", "", footer, flags=re.S) if slug in NO_CAT_SLUGS \
        else footer.replace("{{cat}}", "").replace("{{/cat}}", "")
    return head + header + body.strip() + "\n" + footer + SCRIPT + "</body>\n</html>\n"


def main():
    pages = sorted(PAGES.glob("*.html"))
    if not pages:
        print("no pages in src/pages/ yet")
    for src in pages:
        meta, body = split_front_matter(src.read_text(encoding="utf-8"), src.name)
        out, _ = output_path(src.stem)
        out.parent.mkdir(exist_ok=True)
        out.write_text(render(src.stem, meta, body), encoding="utf-8")
        print(f"built {out.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
