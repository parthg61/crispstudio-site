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

    def test_tokens_css_passes(self):
        self.assertEqual(check.check_css(check.ROOT / "css" / "tokens.css"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
