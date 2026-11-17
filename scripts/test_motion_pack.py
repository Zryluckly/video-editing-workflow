"""Run with Python; add --browser for optional Playwright/Chromium verification."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from build_motion_pack import build, load_config
from motion_pack import KINDS, _layout, ass_sections, write_html

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples/motion/demo.json"
BROWSER = "--browser" in sys.argv
if BROWSER:
    sys.argv.remove("--browser")


class MotionPackTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(DEMO)

    def layout(self, config=None):
        c = self.config if config is None else config
        return _layout(c["chapters"], c["cards"], c["fps"], c["duration_frames"])

    def test_every_template_generates_both_formats(self):
        self.assertEqual({card["kind"] for card in self.config["cards"]}, KINDS)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            result = build(DEMO, out)
            self.assertEqual(result["card_count"], 9)
            html = (out / "overlay.html").read_text(encoding="utf-8")
            svg = re.search(r"<svg.*?</svg>", html, re.S).group()
            ET.fromstring(svg)  # SVG must remain well formed.
            self.assertIn("window.film", html)
            ass = (out / "overlay.ass").read_text(encoding="utf-8-sig")
            self.assertIn("PlayResX: 1080", ass)
            self.assertIn(r"\t(0,", ass)  # Progress grows, rather than static chapter styling.
            self.assertIn(r"\move(", ass)
            self.assertNotIn("http://", (out / "preview.html").read_text(encoding="utf-8").replace("http://www.w3.org/2000/svg", ""))

    def test_rejects_bad_clock_and_duration(self):
        for field, bad_values in [("fps", [0, 101, True, 29.97]),
                                  ("duration_frames", [0, 1979, True, 3.2])]:
            for value in bad_values:
                with self.subTest(field=field, value=value):
                    c = copy.deepcopy(self.config)
                    c[field] = value
                    with self.assertRaises(ValueError):
                        self.layout(c)

    def test_rejects_chapter_gap_and_overlap(self):
        for start in [389, 391]:
            c = copy.deepcopy(self.config)
            c["chapters"][1]["start"] = start
            with self.assertRaises(ValueError):
                self.layout(c)

    def test_rejects_card_overlap_reverse_and_too_short(self):
        for start, end in [(149, 390), (150, 150), (150, 149), (-1, 140), (150, 153)]:
            c = copy.deepcopy(self.config)
            c["cards"][1].update(start=start, end=end)
            with self.assertRaises(ValueError):
                self.layout(c)

    def test_rejects_reveal_before_after_and_out_of_order(self):
        for frame in [149, 172, 386, 390, True, 200.2]:
            c = copy.deepcopy(self.config)
            c["cards"][1]["items"][1]["frame"] = frame
            if frame == 172:  # Equal timestamps are supported for intentional simultaneous reveals.
                self.layout(c)
            else:
                with self.assertRaises(ValueError):
                    self.layout(c)
        c = copy.deepcopy(self.config)
        c["cards"][4]["items"][1]["frame"] = 885
        with self.assertRaises(ValueError):
            self.layout(c)  # Active-step intervals must be strictly increasing.

    def test_rejects_safe_area_and_unreadable_text(self):
        for index, change in [(0, {"top": 200}), (1, {"top": 1000}),
                              (7, {"title": "Long " * 100}), (0, {"title": "bad\nline"}),
                              (0, {"title": "bad\x00control"})]:
            c = copy.deepcopy(self.config)
            c["cards"][index].update(change)
            with self.assertRaises(ValueError):
                self.layout(c)

    def test_rejects_invalid_graph_and_question(self):
        for index, change in [(6, {"return_frame": 1300}), (6, {"return_frame": 1470}),
                              (5, {"items": ["one"]}), (8, {"answer": 4}),
                              (8, {"answer_frame": 1700}), (8, {"answer_frame": 1980})]:
            c = copy.deepcopy(self.config)
            c["cards"][index].update(change)
            with self.assertRaises(ValueError):
                self.layout(c)

    def test_plain_text_is_escaped(self):
        cards = [{"start": 0, "end": 90, "kind": "focus", "title": "<b>A&B</b>"}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.html"
            write_html(path, [], cards)
            html = path.read_text(encoding="utf-8")
            self.assertIn("&lt;b&gt;A&amp;B&lt;/b&gt;", html)
            self.assertNotIn("<b>A&B</b>", html)
        cards[0]["title"] = r"a{b}\c"
        _, events = ass_sections([], cards)
        self.assertTrue(any("a｛b｝＼c" in event for event in events))

    def test_invalid_config_creates_no_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "bad.json"
            config.write_text('{"fps":0,"cards":[]}', encoding="utf-8")
            with self.assertRaises(ValueError):
                build(config, root / "output")
            self.assertFalse((root / "output").exists())

    def test_sparse_timeline_and_no_navigation(self):
        cards = [{"start": 30, "end": 180, "title": "示例", "kind": "steps", "items": ["一步"]}]
        duration, sprites = _layout([], cards, 30, 210)
        self.assertEqual(duration, 210)
        self.assertGreater(len(sprites), 1)

    @unittest.skipUnless(BROWSER, "optional: --browser needs Playwright and Chromium")
    def test_browser_clock_rewind_bounds_and_preview(self):
        from playwright.sync_api import sync_playwright
        build(DEMO, ROOT / "examples/motion")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto((ROOT / "examples/motion/overlay.html").as_uri())
            page.evaluate("document.fonts.ready")
            probe = """frame => {window.film.frame(frame/30);return [...document.querySelectorAll('svg>*')].map(n=>[n.style.display,n.getAttribute('opacity'),n.getAttribute('transform'),n.getAttribute('width')]);}"""
            before = page.evaluate(probe, 171)
            text_state = """() => {const n=[...document.querySelectorAll('svg text')].find(n=>n.textContent==='收集输入');return [n.style.display,Number(n.getAttribute('opacity'))];}"""
            self.assertEqual(page.evaluate(text_state)[0], "none")
            after = page.evaluate(probe, 186)
            self.assertEqual(page.evaluate(text_state)[0], "")
            self.assertGreater(page.evaluate(text_state)[1], .9)
            self.assertNotEqual(before, after)
            self.assertEqual(before, page.evaluate(probe, 171))
            # Actual glyph boxes stay inside the promised safe area at each settled card.
            for card in self.config["cards"]:
                page.evaluate(probe, card["end"] - 15)
                bad = page.evaluate("""() => [...document.querySelectorAll('svg text')].filter(n=>n.style.display!=='none' && Number(n.getAttribute('opacity'))>0).filter(n=>{const b=n.getBBox();return b.x<71 || b.x+b.width>955 || b.y<219 || b.y+b.height>1151;}).map(n=>n.textContent)""")
                self.assertEqual(bad, [], card["kind"])
            width_probe = """() => Number(document.getElementById('mg'+sprites.findIndex(s=>s.grow)).getAttribute('width'))"""
            page.evaluate(probe, 15)
            early_width = page.evaluate(width_probe)
            page.evaluate(probe, 100)
            self.assertGreater(page.evaluate(width_probe), early_width)
            active_probe = """() => [...document.querySelectorAll('rect[fill="#F4DE91"][width="5"]')].filter(n=>n.style.display!=='none').map(n=>n.id)"""
            page.evaluate(probe, 900)
            first_active = page.evaluate(active_probe)
            page.evaluate(probe, 980)
            second_active = page.evaluate(active_probe)
            self.assertEqual(len(first_active), 1)
            self.assertEqual(len(second_active), 1)
            self.assertNotEqual(first_active, second_active)
            final = page.evaluate(probe, self.config["duration_frames"])
            self.assertTrue(all(row[0] == "none" for row in final))
            page.set_viewport_size({"width": 960, "height": 760})
            page.goto((ROOT / "examples/motion/preview.html").as_uri())
            page.wait_for_function("document.querySelector('iframe').contentWindow.film !== undefined")
            page.locator("#scene").select_option("1650")
            self.assertIn("1650 /", page.locator("#time").inner_text())
            page.locator("#seek").fill("1910")
            page.locator("#seek").dispatch_event("input")
            self.assertIn("1910 /", page.locator("#time").inner_text())
            page.screenshot(path=str(ROOT / "examples/motion/preview.png"), full_page=True)
            page.locator("#reset").click()
            self.assertIn("0 /", page.locator("#time").inner_text())
            self.assertEqual(errors, [])
            browser.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
