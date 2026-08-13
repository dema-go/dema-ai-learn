# 「考我一下」HTML Prototypes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build three responsive, interactive HTML prototype galleries for the complete AI learning quest experience while preserving the existing Claude Code reference prototypes.

**Architecture:** New Codex deliverables use a shared CSS design system, a shared JavaScript interaction layer, and three independent semantic HTML galleries. A Python `unittest` suite validates page inventory, required copy, accessibility hooks, and asset references without introducing a build tool or package dependency.

**Tech Stack:** HTML5, CSS custom properties and responsive Grid, vanilla JavaScript, inline SVG, Python 3 standard-library `unittest`, browser screenshot verification.

## Global Constraints

- Preserve `prototypes/core-flow.html`, `prototypes/extended-features.html`, `prototypes/states-compliance.html`, and `prototypes/styles.css` as Claude Code reference files.
- Formal files use “考我一下 / 考考 / 暖纸红 × 薄荷青”; they must not use “读后闯关 / 小衰 / 活力橙”.
- Colors: `#FBF7EE`, `#FFFEFA`, `#DE5848`, `#FBE2DD`, `#78CDBF`, `#D9F0EB`, `#FFD45A`, `#24292D`, `#6F777E`, `#D8D4CB`, `#C9443A`.
- Font stack: `PingFang SC`, `Microsoft YaHei`, `Noto Sans SC`, sans-serif; no KaiTi, FangSong, or handwriting font for UI text.
- Gallery layout is three columns on large screens, two on medium screens, and one on small screens.
- Only pasted text and public URL are enabled inputs; photo and file controls are disabled and visibly labeled “敬请期待”.
- All question, explanation, and result views include an AI-generated-content notice and a route to source evidence.
- No real network, AI, WeChat authorization, payment, storage, or backend calls.
- All informational color states also include icon and text cues; interactive elements are keyboard focusable.

---

### Task 1: Shared Design System, SVG Character, and Contract Tests

**Files:**
- Create: `prototypes/codex-styles.css`
- Create: `prototypes/codex-app.js`
- Create: `tests/test_prototypes.py`
- Modify: `prototypes/README.md`

**Interfaces:**
- Produces CSS classes `.prototype-grid`, `.phone`, `.screen`, `.btn`, `.choice-card`, `.state-panel`, `.modal`, `.source-drawer`, `.is-visible`, and `.is-selected`.
- Produces JavaScript functions `showScreen(screenId)`, `togglePanel(panelId)`, `selectOption(button)`, `submitAnswer(button)`, `showToast(message)`, `startGeneration(root)`, and `updateTextCount(textarea)`.
- Produces an inline SVG symbol contract: every formal HTML file contains symbols `kaokao-happy`, `kaokao-thinking`, `kaokao-sweat`, and `kaokao-cheer`.

- [ ] **Step 1: Write failing shared-contract tests**

Create `tests/test_prototypes.py` with tests that load the three planned formal pages, assert they reference `codex-styles.css` and `codex-app.js`, assert required design tokens exist, reject deprecated brand terms and forbidden fonts, and verify the formal page inventory.

```python
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
            text = page.read_text(encoding="utf-8")
            self.assertIn('href="codex-styles.css"', text)
            self.assertIn('src="codex-app.js"', text)

    def test_confirmed_tokens_and_fonts(self):
        css = (PROTOTYPES / "codex-styles.css").read_text(encoding="utf-8")
        for token in ("#FBF7EE", "#DE5848", "#78CDBF", "#FFD45A", "#24292D"):
            self.assertIn(token, css)
        self.assertNotRegex(css, re.compile(r"KaiTi|FangSong|楷体|仿宋", re.I))

    def test_formal_pages_use_confirmed_brand(self):
        for page in PAGES:
            text = page.read_text(encoding="utf-8")
            self.assertIn("考我一下", text)
            self.assertIn("考考", text)
            self.assertNotIn("小衰", text)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `python3 -m unittest tests/test_prototypes.py -v`

Expected: FAIL because formal pages and shared assets do not exist.

- [ ] **Step 3: Implement shared CSS and JavaScript**

Create the exact color tokens, typography scale, gallery breakpoints, focus styles, reduced-motion rules, phone shell, cards, buttons, inputs, feedback states, drawers, sheets, toasts, disabled “敬请期待” cards, and SVG utility sizing in `codex-styles.css`. Implement the declared functions with DOM-only behavior and no network calls in `codex-app.js`.

- [ ] **Step 4: Update source documentation**

Extend `prototypes/README.md` with a “Codex 正式原型” section listing the three new pages and shared assets, while retaining the Claude Code attribution section.

- [ ] **Step 5: Commit the shared foundation**

```bash
git add prototypes/codex-styles.css prototypes/codex-app.js prototypes/README.md tests/test_prototypes.py
git commit -m "feat: add Codex prototype design system"
```

### Task 2: Core Creation, Generation, Quiz, and Retest Flow

**Files:**
- Create: `prototypes/codex-core-flow.html`
- Modify: `tests/test_prototypes.py`

**Interfaces:**
- Consumes all shared CSS classes and JavaScript functions from Task 1.
- Produces screen IDs `first-home`, `return-home`, `input-picker`, `text-input`, `url-input`, `generation`, `generation-preview`, `quiz-question`, `quiz-correct`, `quiz-wrong`, `question-report`, `quiz-result`, and `wrong-retest`.

- [ ] **Step 1: Add failing core-flow inventory tests**

Add assertions for every screen ID, the text and URL inputs, disabled photo/file entries containing “敬请期待”, the four generation stages, `source_span` evidence copy, four report reasons, and the retest CTA.

```python
def test_core_flow_inventory(self):
    text = (PROTOTYPES / "codex-core-flow.html").read_text(encoding="utf-8")
    for screen_id in ("first-home", "return-home", "input-picker", "text-input",
                      "url-input", "generation", "generation-preview", "quiz-question",
                      "quiz-correct", "quiz-wrong", "question-report", "quiz-result",
                      "wrong-retest"):
        self.assertIn(f'id="{screen_id}"', text)
    for copy in ("敬请期待", "正在理解原文", "正在抓住重点", "正在生成第",
                 "正在检查答案", "无依据", "答案错", "有歧义", "太简单"):
        self.assertIn(copy, text)
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python3 -m unittest tests.test_prototypes.PrototypeContractTests.test_core_flow_inventory -v`

Expected: FAIL because `codex-core-flow.html` is missing.

- [ ] **Step 3: Build the core gallery**

Create all listed phone screens using realistic Chinese material about procrastination and AI Agents. Include interactive textarea count and validation, URL preview/failure toggle, four-stage generation demo, answer selection and submission, source drawer, report sheet, result actions, and retest completion. Embed all four `kaokao-*` SVG symbols once and reuse them with `<use>`.

- [ ] **Step 4: Run tests**

Run: `python3 -m unittest tests/test_prototypes.py -v`

Expected: core inventory tests pass; remaining missing-page tests may still fail until Tasks 3 and 4.

- [ ] **Step 5: Commit core flow**

```bash
git add prototypes/codex-core-flow.html tests/test_prototypes.py
git commit -m "feat: build core AI quest prototype flow"
```

### Task 3: Records, Wrong Answers, Sharing, and Recall Flow

**Files:**
- Create: `prototypes/codex-records-share.html`
- Modify: `tests/test_prototypes.py`

**Interfaces:**
- Consumes the shared screen switching, panel, toast, and button interfaces.
- Produces screen IDs `recent-list`, `record-detail`, `wrong-book`, `result-card`, `share-landing`, `shared-challenge`, `subscribe-request`, `next-day-recall`, and `quota-limit`.

- [ ] **Step 1: Add failing records/share tests**

Assert all nine screen IDs, the result-card privacy rule copy, one preview question on the share landing page, optional subscription language, next-day three-question recall, and “每日 3 次” quota copy.

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python3 -m unittest tests.test_prototypes.PrototypeContractTests.test_records_share_inventory -v`

Expected: FAIL because `codex-records-share.html` is missing.

- [ ] **Step 3: Build the records/share gallery**

Implement history filters, record detail, grouped wrong answers, share-card preview, single-page share landing, challenge choice, skippable subscription request, next-day recall entry, quota limit, and empty/expired/share-failed variants. Do not show full source material or reward sharing.

- [ ] **Step 4: Run tests and commit**

Run: `python3 -m unittest tests/test_prototypes.py -v`

```bash
git add prototypes/codex-records-share.html tests/test_prototypes.py
git commit -m "feat: add records and sharing prototype flows"
```

### Task 4: Profile, Privacy, Deletion, Feedback, and Future Features

**Files:**
- Create: `prototypes/codex-settings-future.html`
- Modify: `tests/test_prototypes.py`

**Interfaces:**
- Consumes shared modal, panel, toast, and disabled-card behavior.
- Produces screen IDs `profile`, `profile-consent`, `privacy-data`, `delete-confirm`, `help-feedback`, `future-photo`, `future-file`, `future-difficulty`, `future-review-plan`, and `future-stickers`.

- [ ] **Step 1: Add failing settings/future tests**

Assert all ten screen IDs, optional/skip language for profile consent, short-retention and delete controls, copyright and question-quality feedback, and “敬请期待” on all five future screens.

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python3 -m unittest tests.test_prototypes.PrototypeContractTests.test_settings_future_inventory -v`

Expected: FAIL because `codex-settings-future.html` is missing.

- [ ] **Step 3: Build the settings/future gallery**

Implement anonymous profile stats, optional nickname/avatar consent, privacy and retention explanation, destructive delete confirmation, help and feedback routes, and five visually complete but disabled future-feature screens. All destructive actions require explicit confirmation and produce a recoverability statement.

- [ ] **Step 4: Run tests and commit**

Run: `python3 -m unittest tests/test_prototypes.py -v`

Expected: all contract tests PASS.

```bash
git add prototypes/codex-settings-future.html tests/test_prototypes.py
git commit -m "feat: add settings and future feature prototypes"
```

### Task 5: Browser Verification and Final Polish

**Files:**
- Modify if required: `prototypes/codex-styles.css`
- Modify if required: `prototypes/codex-app.js`
- Modify if required: the three formal HTML files
- Create: `docs/prototype-verification.md`

**Interfaces:**
- Verifies all outputs from Tasks 1–4; produces no new runtime interface.

- [ ] **Step 1: Start a local static server**

Run: `python3 -m http.server 4173`

Expected: server exposes `/prototypes/codex-core-flow.html`, `/prototypes/codex-records-share.html`, and `/prototypes/codex-settings-future.html`.

- [ ] **Step 2: Verify desktop and mobile layouts in a real browser**

At 1440 px, confirm three gallery columns. At 900 px, confirm two columns. At 390 px, confirm one column and no horizontal overflow. Exercise textarea counting, input error states, answer submission, evidence drawers, report sheet, history filters, subscription skip, delete confirmation, and disabled future cards.

- [ ] **Step 3: Run automated checks**

Run: `python3 -m unittest tests/test_prototypes.py -v`

Run: `git diff --check`

Expected: all tests PASS and no whitespace errors in new implementation files.

- [ ] **Step 4: Record verification evidence**

Create `docs/prototype-verification.md` with the tested viewport widths, page URLs, interactions exercised, automated-test command/output summary, and any known static-prototype limitations.

- [ ] **Step 5: Commit verified delivery**

```bash
git add prototypes/codex-*.html prototypes/codex-styles.css prototypes/codex-app.js tests/test_prototypes.py docs/prototype-verification.md
git commit -m "test: verify responsive prototype delivery"
```
