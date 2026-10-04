#!/usr/bin/env python3
"""Self-test for tools/check.py. Run: python3 tools/test_check.py"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402


def css(text):
    return check.check_style_text(text, "t.css")


def html(text):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(text)
    return check.check_html(f.name)


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
        good = "<h1>Design with a crunch!</h1>" + "".join(f"<h2>{s}</h2>" for s in check.PAGE_COPY["home"][1:])
        self.assertEqual(check.check_copy("home", good, "t"), [])
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
            with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
                f.write(f'<div id="here"></div>{body}')
            return check.check_links([Path(f.name)])
        self.assertEqual(links('<a href="/services/#strategy"></a><a href="#here"></a><a href="#"></a>'
                               '<a href="mailto:team@crispstudio.in"></a><a href="https://x.com/"></a>'
                               '<meta property="og:url" content="https://crispstudio.in/about/">'), [])
        self.bad(links('<a href="/services/#nope"></a>'), "missing anchor on another page")
        self.bad(links('<a href="#nope"></a>'), "missing anchor on the same page")
        self.bad(links('<a href="/pricing/"></a>'), "missing page")
        self.bad(links('<img alt="" src="/assets/logo/nope.svg">'), "missing asset")
        self.bad(links('<a href="about/"></a>'), "relative link")
        self.bad(links('<meta property="og:image" content="https://crispstudio.in/assets/nope.jpg">'), "missing og:image")

    def test_tokens_css_passes(self):
        self.assertEqual(check.check_css(check.ROOT / "css" / "tokens.css"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
