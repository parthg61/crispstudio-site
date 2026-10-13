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

    image: /assets/...      (optional og:image, defaults to the Crunch poster)

Output: home -> index.html, 404 -> 404.html, <slug> -> <slug>/index.html, and nested pages
work/<slug>.html -> work/<slug>/index.html. Also writes sitemap.xml (every indexable page).
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
    if meta.get("image"):
        head = head.replace("https://crispstudio.in/assets/motion/crunch-poster.jpg", "https://crispstudio.in" + meta["image"])
    section = slug.split("/")[0]
    if meta.get("robots"):  # optional front matter, e.g. "robots: noindex" on the 404 page
        head = head.replace("<meta name=\"description\"", f'<meta name="robots" content="{meta["robots"]}">\n<meta name="description"', 1)
    if "noindex" in meta.get("robots", ""):  # a page kept out of the index gets no canonical or og:url
        head = re.sub(r'<link rel="canonical"[^>]*>\n|<meta property="og:url"[^>]*>\n', "", head)
    header = read("header.html")
    for s in NAV_SLUGS:
        header = header.replace("{{cur:%s}}" % s, ' aria-current="page"' if s == section else "")
    footer = read("footer.html").replace("{{year}}", str(datetime.date.today().year))
    return head + header + body.strip() + "\n" + footer + SCRIPT + "</body>\n</html>\n"


SITEMAP_ORDER = ("home",) + NAV_SLUGS


def sitemap(entries):
    """entries: (slug, meta) of every built page; 404 and noindex pages stay out. Nav pages first, then nested ones."""
    paths = [output_path(s)[1] for s, m in sorted(entries, key=lambda e: (
        SITEMAP_ORDER.index(e[0]) if e[0] in SITEMAP_ORDER else len(SITEMAP_ORDER), e[1].get("order", ""), e[0]))
        if s != "404" and "noindex" not in m.get("robots", "")]
    urls = "".join(f"  <url><loc>https://crispstudio.in{p}</loc></url>\n" for p in paths)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n'


def main():
    pages = sorted(PAGES.rglob("*.html"))
    if not pages:
        print("no pages in src/pages/ yet")
    entries = []
    for src in pages:
        slug = src.relative_to(PAGES).with_suffix("").as_posix()
        meta, body = split_front_matter(src.read_text(encoding="utf-8"), src.name)
        if meta.get("draft") == "true":  # paused page: kept in src, not built, not in the sitemap
            print(f"skipped draft {src.name}")
            continue
        out, _ = output_path(slug)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(slug, meta, body), encoding="utf-8")
        entries.append((slug, meta))
        print(f"built {out.relative_to(ROOT)}")
    (ROOT / "sitemap.xml").write_text(sitemap(entries), encoding="utf-8")
    print("built sitemap.xml")


if __name__ == "__main__":
    sys.exit(main())
