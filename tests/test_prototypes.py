from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPES = ROOT / "prototypes"
PAGES = [
    PROTOTYPES / "codex-core-flow.html",
    PROTOTYPES / "codex-records-share.html",
    PROTOTYPES / "codex-settings-future.html",
]


class PrototypeContractTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
