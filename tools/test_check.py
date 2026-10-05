#!/usr/bin/env python3
"""Self-test for tools/check.py. Run: python3 tools/test_check.py"""
import html as html_lib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402


def css(text):
    return check.check_style_text(text, "t.css")


def tmp_file(text, suffix=".html"):
    """Write text to a temp file; the caller deletes it (see with_tmp)."""
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as f:
        f.write(text)
    return Path(f.name)


def with_tmp(text, fn, suffix=".html"):
    path = tmp_file(text, suffix)
    try:
        return fn(path)
    finally:
        path.unlink(missing_ok=True)


def html(text):
    return with_tmp(text, check.check_html)


class Bypasses(unittest.TestCase):
    def bad(self, found, why):
        self.assertTrue(found, f"not caught: {why}")

    def test_font_family(self):
        self.bad(css('a{font-family: Inter, "Schibsted Grotesk"}'), "Inter before Schibsted")
        self.bad(css("a{font-family: var(--x), Inter}"), "var() then Inter")
        self.bad(css("a{font: 16px Inter}"), "font shorthand")
        self.bad(css('a{font: 600 var(--fs-body)/var(--lh-body) Inter, sans-serif}'), "font shorthand with vars")
        self.assertEqual(css('a{font-family: "Schibsted Grotesk", system-ui, -apple-system, "Segoe UI", Arial, sans-serif}'), [])
        self.assertEqual(css("a{font-family: var(--font-sans)}"), [])
        self.assertEqual(css('a{font: 600 16px/24px "Schibsted Grotesk", sans-serif}'), [])

    def test_shadow(self):
        for v in ("-4px -4px 0 #021F53", "4px 4px #021F53", "#fff 4px 4px 0", "4px 4px 0 var(--navy)", "4px 4px 8px #021F53"):
            self.bad(css(f"a{{box-shadow: {v}}}"), v)
        self.assertEqual(css("a{box-shadow: var(--shadow-sm), var(--shadow-outline)}"), [])
        self.assertEqual(css("a{box-shadow: inset 0 0 0 1.5px #e6e6e2}"), [])
        self.assertEqual(css("a{box-shadow: 0 14px 30px -18px rgba(2, 31, 83, 0.30)}"), [])
        self.assertEqual(css("a{box-shadow: none}"), [])

    def test_drop_shadow(self):
        for v in ("filter: drop-shadow(0 24px 30px rgba(2, 31, 83, 0.14))",
                  "filter: drop-shadow(0 calc(24px * var(--k)) calc(30px * var(--k)) rgba(2, 31, 83, calc(0.14 * var(--k))))",
                  "filter: drop-shadow(var(--shadow-logo)) drop-shadow(0 1px 2px #021F53)",
                  "filter: drop-shadow(var(--x))", "-webkit-filter: drop-shadow(4px 4px 0 #021F53)"):
            self.bad(css(f"a{{{v}}}"), v)
        self.assertEqual(css("a{filter: drop-shadow(var(--shadow-logo))}"), [])
        self.assertEqual(css("a{filter: drop-shadow( var(--shadow-logo) ); transition: filter .2s}"), [])
        self.assertEqual(check.check_css(check.ROOT / "css" / "site.css"), [])

    def test_radius(self):
        self.bad(css("a{border-radius: var(--a) 999px}"), "var plus 999px")
        self.bad(css("a{border-radius: 999px}"), "pill")
        self.bad(css("a{border-radius: 10px}"), "off-scale")
        self.assertEqual(css("a{border-radius: var(--radius-md) 12px 0 50%}"), [])

    def test_border(self):
        for v in ("border-block: 4px solid #021F53", "border-inline-start: 2px solid #021F53", "border: thick solid #021F53",
                  "border: medium solid #021F53", "outline: 3px solid #021F53", "border-width: 2px", "border-top: 0.2rem solid #021F53"):
            self.bad(css(f"a{{{v}}}"), v)
        self.assertEqual(css("a{border: 1.5px solid #e6e6e2; outline: 1px solid #021F53; border-radius: 12px}"), [])

    def test_colours(self):
        for v in ("color: rgb(1,2,3)", "color: hsl(10 20% 30%)", "background: red", "border: 1px solid navy",
                  "box-shadow: 0 1px 2px rgba(0,0,0,.2)", "fill: tomato"):
            self.bad(css(f"a{{{v}}}"), v)
        self.assertEqual(css("a{color: white; background: transparent; border: 1px solid currentColor; fill: none}"), [])
        self.assertEqual(css("a{background: url(/assets/red.png) center no-repeat}"), [])

    def test_html(self):
        self.bad(html('<img data-alt="x" src="a.png">'), "data-alt")
        self.bad(html("<p class='reveal'>x</p>"), "single-quoted class")
        self.bad(html("<p style='color:#123456'>x</p>"), "single-quoted style")
        self.bad(html('<svg fill="#123456"></svg>'), "hex in fill attr")
        self.bad(html('<svg stroke="rgb(1,2,3)"></svg>'), "rgb in stroke attr")
        self.bad(html('<svg fill="red"></svg>'), "named colour attr")
        self.bad(html("<p style=\"font-family:Inter\">x</p>"), "inline font")
        self.assertEqual(html('<img src="a.png" alt=""><svg fill="currentColor" stroke="none"></svg><p class="card">x</p>'), [])
        self.assertEqual(html('<svg fill="url(#g)"></svg><a href="#strategy">x</a>'), [])

    def test_focus_outline(self):
        self.assertEqual(css("a:focus-visible{outline: 2px solid var(--focus); outline-offset: 2px}"), [])
        self.assertEqual(css("a{outline-width: 2px}"), [])
        self.bad(css("a{outline: 3px solid var(--focus)}"), "3px outline")
        self.bad(css("a{outline-width: 2.5px}"), "2.5px outline")
        self.bad(css("a{border: 2px solid #021F53}"), "2px border still fails")

    def test_page_copy(self):
        desc = f'<meta name="description" content="{html_lib.escape(check.PAGE_DESC["home"])}">'
        good = desc + "<h1>Design with a crunch!</h1>" + "".join(f"<h2>{s}</h2>" for s in check.PAGE_COPY["home"][1:])
        self.assertEqual(check.check_copy("home", good, "t"), [])
        self.bad(check.check_copy("home", good.replace(desc, '<meta name="description" content="Reworded.">'), "t"), "home desc")
        self.assertEqual(check.check_copy("home", good.replace(desc, f'desc: "{check.PAGE_DESC["home"]}"'), "t"), [])
        for s in ("Design studio · Mumbai, India", "Selected work", "All services", "UX Audits", "Framer"):
            self.bad(check.check_copy("home", good.replace(f"<h2>{s}</h2>", ""), "t"), f"restored home copy {s}")
        self.bad(check.check_copy("home", "<h1>Design with a crunch!</h1>", "t"), "missing home strings")
        self.assertEqual(check.check_copy("home", good.replace("we've", "we&#39;ve"), "t"), [])
        self.assertEqual(check.check_copy("home", good.replace("with a crunch!", 'with <span class="nowrap">a crunch!</span>'), "t"), [])

    def test_services_copy_and_ids(self):
        ids = "".join(f'<section id="{i}"></section>' for i in check.PAGE_IDS["services"])
        good = "".join(f"<h2>{s}</h2>" for s in check.PAGE_COPY["services"]) + ids
        self.assertEqual(check.check_copy("services", good, "t"), [])
        self.assertEqual(check.check_copy("services", good.replace("Don't", "Don&#39;t"), "t"), [])
        self.bad(check.check_copy("services", good.replace("Get the mix right.", ""), "t"), "missing services headline")
        self.bad(check.check_copy("services", good.replace('id="product"', 'id="product-design"'), "t"), "missing #product id")
        self.bad(check.check_copy("services", good.replace('id="process"', 'data-id="process"'), "t"), "data-id is not an id")

    def test_work_copy_and_cases(self):
        case = ('<article class="case" data-services="branding"><div class="case-visual"><img src="a.png" alt="A"></div>'
                '<span class="tag">Finance</span><p class="case-line">One line.</p></article>')
        good = "".join(f"<h2>{s}</h2>" for s in check.PAGE_COPY["work"]) + case * 6
        self.assertEqual(check.check_copy("work", good, "t"), [])
        self.bad(check.check_copy("work", good.replace("Fresh from the Oven.", ""), "t"), "missing work headline")
        self.bad(check.check_copy("work", good.replace("HDB Financial Services", "HDB"), "t"), "missing client name")
        self.bad(check.check_copy("work", good.replace(case, "", 1), "t"), "only five cases")
        self.bad(check.check_copy("work", good.replace('class="case-visual"', 'class="visual"', 1), "t"), "case without visual")
        self.bad(check.check_copy("work", good.replace('<span class="tag">Finance</span>', "", 1), "t"), "case without tag")
        self.bad(check.check_copy("work", good.replace("One line.", "", 1), "t"), "case with empty line")
        self.bad(check.check_copy("work", good.replace('class="case-line"', 'class="lede"', 1), "t"), "case without case-line")

    def test_contact_form(self):
        needs = "".join(f'<label><input type="checkbox" name="need" value="{v.replace("&", "&amp;")}">{v.replace("&", "&amp;")}</label>'
                        for v in check.FORM_NEEDS)
        form = ('<form id="contact-form" novalidate data-endpoint="">'
                '<label for="f-name">Name</label><input id="f-name" name="name">'
                '<label for="f-email">Work email</label><input id="f-email" name="email" type="email">'
                '<label for="f-company">Company</label><input id="f-company" name="company">'
                '<fieldset id="f-needs"><legend>What do you need?</legend>' + needs + '</fieldset>'
                '<label for="f-msg">Tell us a bit about it</label><textarea id="f-msg" name="message"></textarea>'
                '<input class="hp" name="website" tabindex="-1"><button>Send it</button>'
                '<p id="form-note"></p></form><div id="form-done"></div>')
        good = "".join(f"<p>{s}</p>" for s in check.PAGE_COPY["contact"]) + form
        self.assertEqual(check.check_copy("contact", good, "t"), [])
        self.bad(check.check_copy("contact", good.replace('data-endpoint=""', ""), "t"), "no data-endpoint")
        self.bad(check.check_copy("contact", good.replace('name="company"', 'name="org"'), "t"), "renamed field")
        self.bad(check.check_copy("contact", good.replace('value="Build"', 'value="Dev"'), "t"), "renamed need")
        self.bad(check.check_copy("contact", good.replace('<label><input type="checkbox" name="need" value="Not sure yet">Not sure yet</label>', ""), "t"), "four needs")
        self.bad(check.check_copy("contact", good.replace('name="website"', 'name="url"'), "t"), "no honeypot")
        self.bad(check.check_copy("contact", good.replace('id="form-done"', ""), "t"), "no #form-done")
        self.bad(check.check_copy("contact", good.replace("Work email", "Email"), "t"), "renamed label")

    def test_about_blog_404_copy(self):
        for slug in ("about", "blog", "404"):
            ids = "".join(f'<div id="{i}"></div>' for i in check.PAGE_IDS.get(slug, []))
            good = "".join(f"<p>{s}</p>" for s in check.PAGE_COPY[slug]) + ids
            self.assertEqual(check.check_copy(slug, good, "t"), [], slug)
            self.bad(check.check_copy(slug, good.replace(check.PAGE_COPY[slug][0], ""), "t"), f"{slug} headline")
        self.bad(check.check_copy("blog", "".join(f"<p>{s}</p>" for s in check.PAGE_COPY["blog"]), "t"), "blog ids")

    def test_home_source_copy(self):
        self.assertEqual(check.check_sources(), [])

    def test_links(self):
        self.assertEqual(check.check_links(check.built_pages()), [])
        self.assertEqual(check.check_js(), [])

        def links(body):
            return with_tmp(f'<div id="here"></div>{body}', lambda p: check.check_links([p]))
        self.assertEqual(links('<a href="/services/#strategy"></a><a href="#here"></a><a href="#"></a><a href="#top"></a>'
                               '<a href="mailto:team@crispstudio.in"></a><a href="https://x.com/"></a>'
                               '<meta property="og:url" content="https://crispstudio.in/about/">'), [])
        self.bad(links('<a href="/services/#nope"></a>'), "missing anchor on another page")
        self.bad(links('<a href="#nope"></a>'), "missing anchor on the same page")
        self.bad(links('<a href="/pricing/"></a>'), "missing page")
        self.bad(links('<img alt="" src="/assets/logo/nope.svg">'), "missing asset")
        self.bad(links('<a href="about/"></a>'), "relative link")
        self.bad(links('<meta property="og:image" content="https://crispstudio.in/assets/nope.jpg">'), "missing og:image")
        # quoting styles, srcset, attribute order
        self.bad(links("<a href='/pricing/'></a>"), "single-quoted href")
        self.bad(links("<a href=/pricing/>x</a>"), "unquoted href")
        self.bad(links("<img alt='' src='/nope.png'>"), "single-quoted src")
        self.bad(links('<img alt="" src="/favicon.ico" srcset="/favicon.ico 1x, /nope@2x.png 2x">'), "srcset candidate")
        self.assertEqual(links('<img alt="" srcset="/favicon.ico 1x, /assets/favicon.svg 2x">'), [])
        self.bad(links('<meta content="https://crispstudio.in/nope/" property="og:url">'), "og:url content before property")
        self.bad(links("<meta content='https://crispstudio.in/assets/nope.jpg' property='og:image'>"), "og:image single quotes")
        # ids that only exist inside a script or a comment are not anchors; links inside them are ignored
        self.bad(links('<a href="#ghost"></a><!-- <div id="ghost"></div> -->'), "id inside a comment")
        self.bad(links('<a href="#ghost"></a><script>x = \'<div id="ghost">\'</script>'), "id inside a script")
        self.assertEqual(links('<script>el.innerHTML = \'<a href="/nope/">\'</script><!-- <a href="/nope/"> -->'), [])
        self.assertEqual(links("<div id=bare></div><a href='#bare'></a>"), [])

    def test_front_matter(self):
        for src in sorted((check.ROOT / "src" / "pages").glob("*.html")):
            self.assertEqual(check.check_front_matter(src), [], src.name)

        def fm(body):
            return with_tmp(f"---\n{body}\n---\n<main></main>", check.check_front_matter)
        self.assertEqual(fm('title: Work — Crisp\ndesc: "A: b."\nrobots: noindex'), [])
        self.bad(fm("title: X\ndesc: Crisp is a studio for brands and products: strategy."), "unquoted colon")
        self.bad(fm('desc: "unterminated'), "broken quotes")
        self.bad(fm("desc: plain # comment"), "unquoted hash")
        self.bad(fm("not a key value line"), "bad line")
        self.bad(fm("desc: - starts with a dash"), "indicator")

    # ── Round 2: one logo, cats, official assets ──
    def test_logo_only_in_header(self):
        img = lambda html_, slug=None: check.check_images(html_, "t", slug)
        head = '<header class="site-head"><a class="brandmark" data-logo-slot href="/"><img src="/assets/logo/Crisp_Logo_FullColour.svg" alt="Crisp"></a></header>'
        self.assertEqual(img(head), [])
        for src in ("Crisp_Logo_FullColour.svg", "Crisp_Logo_Mono_Navy.svg", "Crisp_Avatar_Orange.svg", "Crisp_Avatar_Navy.svg"):
            self.bad(img(head + f'<footer><img src="/assets/logo/{src}" alt=""></footer>'), f"{src} in footer")
            self.bad(img(head + f'<main><div class="closer-card"><img alt="" src="/assets/logo/{src}"></div></main>'), f"{src} in main")
        self.bad(img("<main><img alt='' srcset='/assets/logo/Crisp_Logo_FullColour.svg 2x'></main>"), "logo via srcset")
        # the Home hero logo that travels into the navbar is the one exemption: data-hero-logo, inside .hero, on Home
        hero = '<section class="hero"><div class="wrap"><img data-hero-logo src="/assets/logo/Crisp_Logo_FullColour.svg" alt="Crisp"></div></section>'
        self.assertEqual(img(head + hero, "home"), [])
        self.bad(img(head + hero, "about"), "hero logo off Home")
        self.bad(img(head + hero.replace(" data-hero-logo", ""), "home"), "hero logo without data-hero-logo")
        self.bad(img(head + '<section class="closer"><img data-hero-logo src="/assets/logo/Crisp_Logo_FullColour.svg" alt=""></section>', "home"),
                 "data-hero-logo outside .hero")
        self.bad(img('<header></header><section class="hero"><div class="x"></div></section><img data-hero-logo alt="" src="/assets/logo/Crisp_Logo_FullColour.svg">', "home"),
                 "after a closed .hero")
        # the real pages: header logo only (built files)
        for page in check.built_pages():
            self.assertEqual(check.check_images(page.read_text(encoding="utf-8"), page.name, check.page_slug(page)), [], page)

    def test_cats_never_in_hero_or_on_work(self):
        img = lambda html_, slug=None: check.check_images(html_, "t", slug)
        cats = ("/assets/cats/Crisp_Cat_Samosa.svg", "/assets/cats/Crisp_Cat_Idli_Cream.svg", "/assets/cats/Crisp_Avatar_Idli.svg",
                "/assets/cats/Crisp_Avatar_Samosa.svg")
        for c in cats:
            self.bad(img(f'<section class="hero lost"><div><img src="{c}" alt=""></div></section>'), f"{c} in hero")
            self.bad(img(f'<main><img src="{c}" alt=""></main>', "work"), f"{c} on work")
            self.assertEqual(img(f'<section class="hero"></section><section class="contact"><img src="{c}" alt=""></section>', "contact"), [])
        self.bad(img('<main><div style="background:url(/assets/cats/Crisp_Cat_Idli.svg)"></div></main>', "work"), "cat as background on work")
        self.assertEqual(img('<section class="hero-grid"><img src="/assets/cats/Crisp_Cat_Idli.svg" alt=""></section>'), [])

    def test_assets_manifest(self):
        self.assertEqual(check.check_assets(), [])
        line = (check.ROOT / "tools" / "assets.sha256").read_text(encoding="utf-8").splitlines()[0]
        digest, rel = line.split("  ", 1)
        man = lambda body: with_tmp(body, check.check_assets, ".sha256")
        self.assertEqual(man(line + "\n"), [])
        self.bad(man(("0" * 64) + "  " + rel + "\n"), "hash mismatch")
        self.bad(man(digest + "  assets/cats/Nope.svg\n"), "missing file")
        for f in ("assets/icons/Crisp_Icon_Strategy.svg", "assets/cats/Crisp_Cat_Samosa.svg", "assets/icons/Crisp_Bullet_Curl.svg"):
            self.assertIn(f, (check.ROOT / "tools" / "assets.sha256").read_text(encoding="utf-8"), f)

    def test_cat_loops_respect_reduced_motion(self):
        cm = lambda t: check.check_cat_motion(t, "t.css")
        self.bad(cm(".cat-tail { animation: cat-sway 3s infinite; }"), "loop outside media")
        self.bad(cm("@media (min-width: 600px) { .cat-lid { animation: cat-blink 5s infinite; } }"), "wrong media")
        self.bad(cm(".x { animation-name: cat-blink; }"), "cat keyframes on other selector")
        self.bad(cm("@media (prefers-reduced-motion: reduce) { .cat-tail { animation: cat-sway 3s infinite; } }"), "reduce is not no-preference")
        self.assertEqual(cm("@media (prefers-reduced-motion: no-preference) { .cat-tail { animation: cat-sway 3s ease-in-out infinite; } "
                            "@keyframes cat-sway { to { transform: rotate(-4deg); } } }"), [])
        self.assertEqual(cm("@media (prefers-reduced-motion: no-preference) { @media (min-width: 600px) { .cat-peek .cat-lid { animation: cat-blink 5s infinite; } } }"), [])
        self.assertEqual(cm(".cat { animation: none; } .track { animation: ticker 40s linear infinite; }"), [])
        self.assertEqual(check.check_css(check.ROOT / "css" / "site.css"), [])

    # ── Round 2, Task 2: Home hero logo travel and the card fan ──
    HEAD = ('<header class="site-head"><a class="brandmark" data-logo-slot href="/" aria-label="Crisp home">'
            '<img src="/assets/logo/Crisp_Logo_FullColour.svg" alt="Crisp"></a></header>')
    CARD = '<div class="fan-card"><div class="fan-visual"><img src="/assets/clients/x.png" alt=""></div><p>{}</p></div>'
    LOGO = '<div class="hero-logo-spot"><img data-hero-logo class="hero-logo" src="/assets/logo/Crisp_Logo_FullColour.svg" alt=""></div>'

    def hero(self, logo=None, cards=("HDFC securities", "The Mind Mojo", "NMIMS"), fan_attrs=' aria-hidden="true"'):
        fan = f'<div class="fan"{fan_attrs}>' + "".join(self.CARD.format(c) for c in cards) + "</div>"
        return f'<section class="hero"><div class="wrap"><div class="hero-art">{self.LOGO if logo is None else logo}{fan}</div></div></section>'

    def test_hero_logo_slot_and_fan(self):
        hc = lambda html_, slug="home": check.check_hero(html_, "t", slug)
        good = self.HEAD + "<main>" + self.hero() + "</main>"
        self.assertEqual(hc(good), [])
        # the header slot: on every page, once, inside <header>, the <a href="/"> brandmark
        self.assertEqual(hc(self.HEAD + "<main></main>", "about"), [])
        self.bad(hc("<header><a class='brandmark' href='/'><img alt='' src='/a.svg'></a></header>", "about"), "no slot")
        self.bad(hc('<header></header><main><a data-logo-slot href="/">x</a></main>', "about"), "slot outside header")
        self.bad(hc('<header><span data-logo-slot></span></header>', "about"), "slot is not the home link")
        self.bad(hc(self.HEAD + self.HEAD, "about"), "two slots")
        # the hero logo: Home only, exactly one, an <img> inside .hero
        self.bad(hc(self.HEAD + "<main>" + self.hero(logo="") + "</main>"), "no hero logo on Home")
        self.bad(hc(self.HEAD + "<main>" + self.hero(logo=self.LOGO * 2) + "</main>"), "two hero logos")
        self.bad(hc(self.HEAD + "<main>" + self.hero(logo="") + self.LOGO + "</main>"), "hero logo after the hero")
        self.bad(hc(self.HEAD + "<main>" + self.hero(logo='<div data-hero-logo></div>') + "</main>"), "hero logo not an img")
        self.bad(hc(self.HEAD + '<main><section class="hero">' + self.LOGO + "</section></main>", "about"), "hero logo off Home")
        # the fan: one, decorative, in the hero, three named client cards
        self.bad(hc(self.HEAD + "<main>" + self.hero(cards=("HDFC securities", "NMIMS")) + "</main>"), "two cards")
        self.bad(hc(self.HEAD + "<main>" + self.hero(cards=("HDFC securities", "The Mind Mojo", "SAATH")) + "</main>"), "wrong client")
        self.bad(hc(self.HEAD + "<main>" + self.hero(fan_attrs="") + "</main>"), "fan not aria-hidden")
        moved = self.hero().replace('<div class="fan"', '</div></div></section><div class="fan"', 1)
        self.bad(hc(self.HEAD + "<main>" + moved + "</main>"), "fan outside the hero")
        # the real pages
        for page in check.built_pages():
            self.assertEqual(check.check_hero(page.read_text(encoding="utf-8"), page.name, check.page_slug(page)), [], page)

    def test_logo_travel_js(self):
        lt = check.check_logo_travel_js
        fn = ("function initLogoTravel() {\n  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');\n}\n")
        call = "if (document.querySelector('.hero [data-hero-logo]')) initLogoTravel();\n"
        self.assertEqual(lt(fn + call), [])
        self.bad(lt(call), "not defined")
        self.bad(lt(fn), "never called")
        self.bad(lt(fn + "initLogoTravel();\n"), "called without the hero guard")
        self.bad(lt(fn + call + "initLogoTravel();\n"), "a second, unguarded call")
        self.bad(lt(fn + "// " + call), "guard only in a comment")
        self.bad(lt(fn.replace("reduce)", "no-preference)") + call), "no reduced-motion check")
        self.assertEqual(check.check_js(), [])

    def test_fan_motion(self):
        cm = lambda t: check.check_cat_motion(t, "t.css")
        self.bad(cm(".fan-card { animation: fan-out .7s both; }"), "fan outside media")
        self.bad(cm("@media (prefers-reduced-motion: reduce) { .fan-card { animation: fan-out .7s; } }"), "fan under reduce")
        self.bad(cm(".x { animation-name: fan-out; }"), "fan keyframes elsewhere")
        self.assertEqual(cm("@media (prefers-reduced-motion: no-preference) { .fan-card { animation: fan-out .7s both; } "
                            "@keyframes fan-out { from { transform: none; } } }"), [])
        fp = lambda t: check.check_fan_present(t, "t.css")
        self.bad(fp(".fan-card { transform: rotate(4deg); }"), "no fan animation at all")
        self.bad(fp(".fan-card { animation: fan-out .7s; }"), "fan animation not under no-preference")
        self.assertEqual(fp("@media (prefers-reduced-motion: no-preference) { .fan .fan-card { animation: fan-out .7s both; } }"), [])
        self.assertEqual(fp((check.ROOT / "css" / "site.css").read_text(encoding="utf-8")), [])

    def test_mobile_hero_logo_first(self):
        mo = lambda t: check.check_mobile_hero_order(t, "t.css")
        good = "@media (max-width: 599px) { .hero-art { display: contents; } .hero-logo-spot { order: -1; } }"
        self.assertEqual(mo(good), [])
        self.assertEqual(mo(good.replace("order: -1; }", "order: 0; } .hero-copy { order: 1; }")), [])
        self.bad(mo(""), "no mobile rules")
        self.bad(mo(good.replace("order: -1", "order: 2")), "spot after the copy")
        self.bad(mo(good.replace("display: contents", "display: flex")), "spot still inside the art block")
        self.bad(mo(good.replace("max-width: 599px", "min-width: 600px")), "wrong breakpoint")
        self.assertEqual(mo((check.ROOT / "css" / "site.css").read_text(encoding="utf-8")), [])

    # ── Round 2, Task 3: bento, marquee, ticker pause, Why statement ──
    @staticmethod
    def tile(href, icon, tags):
        return (f'<a class="tile" href="{href}"><span class="icon-chip" aria-hidden="true"><img src="/assets/icons/{icon}" alt=""></span>'
                f'<h3>x</h3><div class="tags">' + "".join(f'<span class="tag">{html_lib.escape(t)}</span>' for t in tags) + "</div></a>")

    def home_sections(self, bento=None, marquee=None, ticker=None, why=None):
        if bento is None:
            bento = '<div class="bento">' + "".join(self.tile(h, i, t) for h, (i, t) in check.BENTO_TILES.items()) + "</div>"
        names = "".join(f"<li>{html_lib.escape(n)}</li>" for n in check.MARQUEE_NAMES)
        if marquee is None:
            marquee = (f'<div class="marquee" id="mq" data-pausable><div class="marquee-track"><ul>{names}</ul>'
                       f'<ul aria-hidden="true">{names}</ul></div></div>'
                       '<button type="button" data-pause aria-controls="mq">Pause<span class="sr-only"> services strip</span></button>')
        if ticker is None:
            ticker = ('<div class="ticker" id="tk" data-pausable><div class="track" id="track"></div></div>'
                      '<button type="button" data-pause aria-controls="tk">Pause</button>')
        if why is None:
            why = ('<p class="why-statement" id="why" data-pausable>Everything we make has a job<span class="why-static">, to clarify, engage, convert, '
                   'simplify or move someone to act.</span><span class="why-cycle" aria-hidden="true">, to <span class="cycle">'
                   + "".join(f"<span>{w}.</span>" for w in check.JOB_WORDS) + "</span></span> That's the crunch.</p>"
                   '<button type="button" data-pause aria-controls="why">Pause</button>')
        return "<main>" + marquee + ticker + bento + why + "</main>"

    def test_home_sections(self):
        hs = lambda t: check.check_home_sections(t, "t")
        self.assertEqual(hs(self.home_sections()), [])
        tiles = list(check.BENTO_TILES.items())
        # bento: four tiles, right anchors, official icons in an .icon-chip, tags kept
        self.bad(hs(self.home_sections(bento='<div class="do-grid">' + "".join(self.tile(h, i, t) for h, (i, t) in tiles) + "</div>")), "no .bento")
        self.bad(hs(self.home_sections(bento='<div class="bento">' + "".join(self.tile(h, i, t) for h, (i, t) in tiles[:3]) + "</div>")), "three tiles")
        swapped = [(h, (tiles[(k + 1) % 4][1][0], t)) for k, (h, (i, t)) in enumerate(tiles)]
        self.bad(hs(self.home_sections(bento='<div class="bento">' + "".join(self.tile(h, i, t) for h, (i, t) in swapped) + "</div>")), "icons swapped")
        self.bad(hs(self.home_sections(bento='<div class="bento">' + "".join(self.tile(h, i, t[:-1]) for h, (i, t) in tiles) + "</div>")), "a tag dropped")
        no_chip = self.home_sections().replace('class="icon-chip"', 'class="icon"')
        self.bad(hs(no_chip), "icon not in an .icon-chip")
        # marquee: exactly the four names, a loop copy, a pause button
        good = self.home_sections()
        self.bad(hs(good.replace("<li>Build</li>", "<li>Development</li>", 1)), "renamed service")
        self.bad(hs(good.replace("<li>Build</li>", "", 1)), "three names")
        self.bad(hs(good.replace('<ul aria-hidden="true">', "<ul>", 1)), "copy not aria-hidden")
        self.bad(hs(good.replace('aria-controls="mq"', 'aria-controls="nope"')), "no pause button for the marquee")
        self.bad(hs(good.replace('aria-controls="mq">Pause', 'aria-controls="mq">Stop')), "button not labelled Pause/Play")
        self.bad(hs(good.replace('aria-controls="mq">Pause<span class="sr-only"> services strip</span>',
                                 'aria-controls="mq"><span class="sr-only">Services strip </span>Pause')), "visible label not first in the name")
        self.bad(hs(good.replace('data-pause aria-controls="mq"', 'data-pause aria-pressed="false" aria-controls="mq"')), "aria-pressed with a toggling label")
        self.bad(hs(good.replace('<div class="marquee" id="mq" data-pausable>', '<div class="marquee" id="mq">')), "marquee not pausable")
        self.bad(hs(good.replace('<button type="button" data-pause aria-controls="mq">',
                                 '<span data-pause aria-controls="mq">', 1)), "pause control not a button")
        # ticker: needs its own pause button
        self.bad(hs(good.replace('aria-controls="tk"', 'aria-controls="x"')), "ticker has no pause button")
        self.bad(hs(good.replace('<div class="ticker" id="tk" data-pausable>', '<div class="ticker">')), "ticker not pausable")
        # why: full sentence readable, cycle aria-hidden with the five words
        self.bad(hs(self.home_sections(why="<p>Everything we make has a job.</p>")), "no .why-statement")
        self.bad(hs(good.replace('<span class="why-static">', '<span class="why-static" aria-hidden="true">')), "sentence hidden from AT")
        self.bad(hs(good.replace('<span class="why-cycle" aria-hidden="true">', '<span class="why-cycle">')), "cycle not aria-hidden")
        self.bad(hs(good.replace("<span>convert.</span>", "")), "a job word missing")
        self.bad(hs(good.replace("simplify or move", "simplify, or move")), "sentence reworded")
        self.bad(hs(good.replace('aria-controls="why"', 'aria-controls="x"')), "job-word cycle has no pause button")
        self.bad(hs(good.replace('id="why" data-pausable', 'id="why"')), "job-word cycle not pausable")
        # the real Home page
        home = check.ROOT / "index.html"
        self.assertEqual(hs(home.read_text(encoding="utf-8")), [])

    def test_all_motion_under_no_preference(self):
        am = lambda t: check.check_all_motion(t, "t.css")
        self.bad(am(".track { animation: ticker 40s linear infinite; } @keyframes ticker { to { transform: none; } }"), "ticker outside media")
        self.bad(am("@media (prefers-reduced-motion: no-preference) { .x { animation: a 1s; } } @keyframes a { to { opacity: 0; } }"), "keyframes outside")
        self.bad(am("@media (min-width: 600px) { .marquee-track { animation: m 60s linear infinite; } }"), "wrong media")
        self.assertEqual(am("@media (prefers-reduced-motion: no-preference) { .marquee-track { animation: m 60s linear infinite; } "
                            "@keyframes m { to { transform: translateX(-50%); } } } .x { animation: none; }"), [])
        self.assertEqual(am("@media (prefers-reduced-motion: no-preference) { @media (min-width: 600px) { .a { animation: m 1s; } } }"), [])
        sc = lambda t: check.check_strips_css(t, "t.css")
        good = ("@media (prefers-reduced-motion: no-preference) { html.js .marquee-track { animation: m 60s linear infinite; } "
                "html.js .track { animation: t 40s linear infinite; } } .is-paused .track { animation-play-state: paused; }")
        self.assertEqual(sc(good), [])
        self.bad(sc(good.replace(".is-paused .track", ".paused .track")), "no paused rule")
        self.bad(sc(good.replace("html.js .marquee-track { animation: m 60s linear infinite; } ", "")), "marquee does not scroll")
        self.bad(sc(good + " .marquee:hover .marquee-track { animation-play-state: paused; }"), "hover pause fights the button")
        self.bad(sc(good + " .work-grid .card:hover .card-visual { transform: scale(1.04); }"), "zoom on a non-link card")
        self.assertEqual(sc(good + " .work-grid a.card:hover .card-visual, .work-grid a.card:focus-visible .card-visual { transform: scale(1.04); }"), [])
        site_css = check.ROOT / "css" / "site.css"
        self.assertEqual(am(site_css.read_text(encoding="utf-8")), [])
        self.assertEqual(sc(site_css.read_text(encoding="utf-8")), [])

    def test_pausables_js(self):
        pj = check.check_pausables_js
        fn = ("function initPausables() {\n  document.querySelectorAll('[data-pause]').forEach(btn => {\n"
              "    const el = document.getElementById(btn.getAttribute('aria-controls'));\n"
              "    if (!el || !el.hasAttribute('data-pausable')) return;\n"
              "    btn.addEventListener('click', () => { const p = !el.classList.contains('is-paused');\n"
              "      el.classList.toggle('is-paused', p);\n"
              "      btn.textContent = p ? 'Play' : 'Pause'; });\n  });\n}\ninitPausables();\n")
        cyc = ("const cycle = document.querySelector('.why-statement .cycle');\n"
               "if (cycle && !matchMedia('(prefers-reduced-motion: reduce)').matches) { if (statement.classList.contains('is-paused')) stop(); }\n")
        self.assertEqual(pj(fn + cyc), [])
        self.bad(pj(cyc), "not defined")
        self.bad(pj(fn.replace("initPausables();\n", "") + cyc), "never called")
        self.bad(pj(fn.replace("el.classList.toggle('is-paused', p);", "el.classList.toggle('is-paused', p); btn.setAttribute('aria-pressed', String(p));") + cyc), "aria-pressed")
        self.bad(pj(fn + cyc.replace("statement.classList.contains('is-paused')", "false")), "cycle ignores its pause button")
        self.bad(pj(fn.replace("'Play'", "'Go'") + cyc), "no Play label")
        self.bad(pj(fn.replace("is-paused", "off") + cyc), "no .is-paused")
        self.bad(pj(fn), "no job-word cycle")
        self.bad(pj(fn + cyc.replace("reduce", "no-preference")), "cycle ignores reduced motion")
        self.assertEqual(check.check_js(), [])

    def test_header_logo_min_width_and_nav_height(self):
        toks = (check.ROOT / "css" / "tokens.css").read_text(encoding="utf-8")
        hl = lambda t: check.check_header_logo(t, "t.css", toks)
        base = (":root { --nav-h: var(--space-9); } html { scroll-padding-top: var(--nav-h); } "
                ".site-head .bar { height: var(--nav-h); } .svc-index { position: sticky; top: calc(var(--nav-h) + var(--space-6)); } ")
        self.assertEqual(hl(base + ".brandmark img { width: calc(var(--space-10) - var(--space-2)); height: auto; }"), [])
        self.assertEqual(hl(base + ".brandmark img { width: 120px; } @media (min-width: 1024px) { .brandmark img { width: var(--space-10); } }"), [])
        self.bad(hl(base + ".brandmark img { width: 71px; }"), "71px logo")
        self.bad(hl(base + ".brandmark img { width: 120px; } @media (max-width: 599px) { .brandmark img { width: var(--space-9); } }"), "small on mobile")
        self.bad(hl(base + ".brandmark img { width: 120px; max-width: var(--space-9); }"), "capped by max-width")
        self.bad(hl(base + ".brandmark img { height: var(--space-7); width: auto; }"), "old height-driven logo")
        self.bad(hl(base), "no width at all")
        self.bad(hl(base.replace("scroll-padding-top: var(--nav-h)", "scroll-padding-top: var(--layout-nav-height)") + ".brandmark img { width: 120px; }"), "scroll padding on old token")
        self.bad(hl(base.replace(".site-head .bar { height: var(--nav-h); }", ".site-head .bar { height: var(--space-8); }") + ".brandmark img { width: 120px; }"), "bar height not --nav-h")
        self.bad(hl(base.replace("top: calc(var(--nav-h) + var(--space-6))", "top: calc(72px + var(--space-6))") + ".brandmark img { width: 120px; }"), "sticky index top not --nav-h")
        self.bad(hl(base.replace(":root { --nav-h: var(--space-9); } ", "") + ".brandmark img { width: 120px; }"), "--nav-h undefined")
        self.assertEqual(hl((check.ROOT / "css" / "site.css").read_text(encoding="utf-8")), [])

    def test_tokens_css_passes(self):
        self.assertEqual(check.check_css(check.ROOT / "css" / "tokens.css"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
