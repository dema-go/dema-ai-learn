from pathlib import Path
import re
import unittest
import struct

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPES = ROOT / "prototypes"
PAGES = [
    PROTOTYPES / "codex-core-flow.html",
    PROTOTYPES / "codex-records-share.html",
    PROTOTYPES / "codex-settings-future.html",
]
SUMMARY = ROOT / "UI原型图.md"
SUMMARY_IMAGES = [
    ROOT / "docs/assets/ui-prototypes/core-flow.png",
    ROOT / "docs/assets/ui-prototypes/records-share.png",
    ROOT / "docs/assets/ui-prototypes/settings-future.png",
]
SCREEN_IDS = (
    "first-home", "return-home", "input-picker", "text-input", "url-input",
    "generation", "generation-preview", "quiz-question", "quiz-correct",
    "quiz-wrong", "question-report", "quiz-result", "wrong-retest",
    "recent-list", "record-detail", "wrong-book", "result-card",
    "share-landing", "shared-challenge", "subscribe-request",
    "next-day-recall", "quota-limit", "profile", "profile-consent",
    "privacy-data", "delete-confirm", "help-feedback", "future-photo",
    "future-file", "future-difficulty", "future-review-plan", "future-stickers",
)


class PrototypeContractTests(unittest.TestCase):
    def test_ui_summary_covers_every_formal_screen_and_overview_image(self):
        self.assertTrue(SUMMARY.exists(), SUMMARY.name)
        summary = SUMMARY.read_text(encoding="utf-8")
        for page in PAGES:
            self.assertIn(f"prototypes/{page.name}", summary)
        for screen_id in SCREEN_IDS:
            self.assertIn(f"#{screen_id}", summary)
        for image in SUMMARY_IMAGES:
            self.assertTrue(image.exists(), image)
            self.assertIn(str(image.relative_to(ROOT)), summary)
            with image.open("rb") as stream:
                self.assertEqual(stream.read(8), b"\x89PNG\r\n\x1a\n")
                width, height = struct.unpack(">II", stream.read(16)[8:16])
            self.assertEqual(width, 1440, image.name)
            self.assertGreaterEqual(height, 2800, image.name)

    def test_formal_pages_exist_and_use_shared_assets(self):
        for page in PAGES:
            self.assertTrue(page.exists(), page.name)
            text = page.read_text(encoding="utf-8")
            self.assertIn('href="codex-styles.css"', text)
            self.assertIn('src="codex-app.js"', text)

    def test_confirmed_tokens_fonts_and_breakpoints(self):
        css = (PROTOTYPES / "codex-styles.css").read_text(encoding="utf-8")
        for token in ("#FBF7EE", "#FFFEFA", "#DE5848", "#78CDBF", "#FFD45A", "#24292D"):
            self.assertIn(token, css)
        self.assertNotRegex(css, re.compile(r"KaiTi|FangSong|楷体|仿宋", re.I))
        self.assertIn("grid-template-columns:repeat(3", css.replace(" ", ""))
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn(":focus-visible", css)

    def test_formal_pages_use_confirmed_brand_and_svg_contract(self):
        for page in PAGES:
            text = page.read_text(encoding="utf-8")
            self.assertIn("考我一下", text)
            self.assertIn("考考", text)
            self.assertNotIn("小衰", text)
            for symbol in ("kaokao-happy", "kaokao-thinking", "kaokao-sweat", "kaokao-cheer"):
                self.assertIn(f'id="{symbol}"', text)

    def test_shared_javascript_exports_interactions(self):
        js = (PROTOTYPES / "codex-app.js").read_text(encoding="utf-8")
        for name in ("showScreen", "togglePanel", "selectOption", "submitAnswer",
                     "showToast", "startGeneration", "updateTextCount"):
            self.assertRegex(js, rf"function\s+{name}\s*\(")
        self.assertNotIn("fetch(", js)
        self.assertNotIn("XMLHttpRequest", js)

    def test_core_flow_inventory(self):
        text = (PROTOTYPES / "codex-core-flow.html").read_text(encoding="utf-8")
        for screen_id in ("first-home", "return-home", "input-picker", "text-input",
                          "url-input", "generation", "generation-preview", "quiz-question",
                          "quiz-correct", "quiz-wrong", "question-report", "quiz-result",
                          "wrong-retest"):
            self.assertIn(f'id="{screen_id}"', text)
        for copy in ("敬请期待", "正在理解原文", "正在抓住重点", "正在生成第",
                     "正在检查答案", "无依据", "答案错", "有歧义", "太简单",
                     "AI 依据你的材料生成，可能有误", "马上翻盘"):
            self.assertIn(copy, text)
        self.assertIn("8000", text)
        self.assertIn("公开网页", text)

    def test_records_share_inventory(self):
        text = (PROTOTYPES / "codex-records-share.html").read_text(encoding="utf-8")
        for screen_id in ("recent-list", "record-detail", "wrong-book", "result-card",
                          "share-landing", "shared-challenge", "subscribe-request",
                          "next-day-recall", "quota-limit"):
            self.assertIn(f'id="{screen_id}"', text)
        for copy in ("不包含原文", "预览题", "暂不开启", "3 道错题", "每日 3 次",
                     "挑战同一关", "创建自己的闯关", "AI 生成"):
            self.assertIn(copy, text)
        self.assertNotIn("分享解锁", text)

    def test_settings_future_inventory(self):
        text = (PROTOTYPES / "codex-settings-future.html").read_text(encoding="utf-8")
        for screen_id in ("profile", "profile-consent", "privacy-data", "delete-confirm",
                          "help-feedback", "future-photo", "future-file", "future-difficulty",
                          "future-review-plan", "future-stickers"):
            self.assertIn(f'id="{screen_id}"', text)
        for copy in ("可跳过", "短期保存", "删除后", "版权投诉", "题目质量",
                     "拍照导入", "PDF / Word / PPT", "题量与难度", "间隔复习",
                     "成就贴纸册"):
            self.assertIn(copy, text)
        self.assertGreaterEqual(text.count("敬请期待"), 5)


if __name__ == "__main__":
    unittest.main()
