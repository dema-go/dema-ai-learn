from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MINIPROGRAM = ROOT / "miniprogram"


def css_declarations(source: str, selector: str) -> dict[str, str]:
    match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", source)
    if match is None:
        raise AssertionError(f"Missing CSS selector: {selector}")
    declarations = {}
    for declaration in match.group(1).split(";"):
        if ":" not in declaration:
            continue
        name, value = declaration.split(":", 1)
        declarations[name.strip()] = value.strip()
    return declarations


class MiniProgramQuizUiContractTests(unittest.TestCase):
    def setUp(self):
        self.quiz_ts = (MINIPROGRAM / "pages/quiz/quiz.ts").read_text(encoding="utf-8")
        self.quiz_wxml = (MINIPROGRAM / "pages/quiz/quiz.wxml").read_text(encoding="utf-8")
        self.quiz_wxss = (MINIPROGRAM / "pages/quiz/quiz.wxss").read_text(encoding="utf-8")
        self.app_wxss = (MINIPROGRAM / "app.wxss").read_text(encoding="utf-8")
        self.api_ts = (MINIPROGRAM / "services/api.ts").read_text(encoding="utf-8")
        self.result_wxml = (MINIPROGRAM / "pages/result/result.wxml").read_text(encoding="utf-8")
        self.action_pages = {
            name: (MINIPROGRAM / f"pages/{name}/{name}.wxml").read_text(encoding="utf-8")
            for name in ("preview", "quota", "delete-confirm", "record-detail", "retest")
        }

    def test_choice_tap_submits_and_confirmation_is_removed(self):
        self.assertIn("async onSelect", self.quiz_ts)
        self.assertIn("beginAnswerSubmission", self.quiz_ts)
        self.assertIn("await api.answer", self.quiz_ts)
        self.assertIn("resolveAnswerSubmission", self.quiz_ts)
        self.assertIn("failAnswerSubmission", self.quiz_ts)
        self.assertNotIn("async onConfirm", self.quiz_ts)
        self.assertNotIn("确定答案", self.quiz_wxml)
        self.assertIn('bindtap="onNext"', self.quiz_wxml)

    def test_markup_uses_server_correct_index_and_explicit_marks(self):
        self.assertIn("answer.correctIndex", self.quiz_wxml)
        self.assertNotIn("question.answer_index", self.quiz_wxml)
        self.assertIn("✓", self.quiz_wxml)
        self.assertIn("×", self.quiz_wxml)
        self.assertIn("正确答案", self.quiz_wxml)
        self.assertIn("回答正确", self.quiz_wxml)
        self.assertIn("这次选错了", self.quiz_wxml)
        self.assertIn('aria-label="正确选项"', self.quiz_wxml)
        self.assertIn('aria-label="错误选项，你的选择"', self.quiz_wxml)

    def test_retry_resolution_uses_server_persisted_choice(self):
        self.assertRegex(
            self.quiz_ts,
            r"resolveAnswerSubmission\(\s*submitting,\s*res\.is_correct,"
            r"\s*res\.correct_index,\s*res\.chosen_index,\s*\)",
        )
        answer_response = re.search(
            r"export interface AnswerResponse\s*\{([^}]*)\}",
            self.api_ts,
            re.DOTALL,
        )
        self.assertIsNotNone(answer_response)
        self.assertIn("chosen_index: number", answer_response.group(1))

    def test_source_drawer_requires_answered_phase(self):
        self.assertIn(
            '<view class="source-drawer" wx:if="{{answer.phase === \'answered\' && showSource}}">',
            self.quiz_wxml,
        )

    def test_quiz_layout_uses_full_width_choices_and_fixed_action(self):
        quiz_screen = css_declarations(self.quiz_wxss, ".quiz-screen")
        self.assertEqual(quiz_screen["padding-left"], "16px")
        self.assertEqual(quiz_screen["padding-right"], "16px")
        choice_list = css_declarations(self.quiz_wxss, ".choice-list")
        self.assertEqual(choice_list["display"], "flex")
        self.assertEqual(choice_list["flex-direction"], "column")
        self.assertEqual(choice_list["gap"], "12px")
        choice_card = css_declarations(self.quiz_wxss, ".choice-card")
        self.assertEqual(choice_card["width"], "100%")
        self.assertEqual(choice_card["min-height"], "56px")
        bottom_action = css_declarations(self.quiz_wxss, ".bottom-action")
        self.assertEqual(bottom_action["position"], "fixed")
        self.assertEqual(
            bottom_action["padding-bottom"],
            "calc(12px + env(safe-area-inset-bottom))",
        )

    def test_quiz_layout_has_distinct_submission_and_answer_states(self):
        for selector in (
            ".choice-card.submitting",
            ".choice-card.correct",
            ".choice-card.wrong",
            ".answer-feedback",
            ".correct-label",
        ):
            self.assertIn(selector, self.quiz_wxss)

    def test_shared_spacing_uses_balanced_values(self):
        self.assertEqual(
            css_declarations(self.app_wxss, ".screen")["padding"],
            "18px 16px 96px",
        )
        self.assertEqual(
            css_declarations(self.app_wxss, ".card + .card")["margin-top"],
            "16px",
        )
        self.assertEqual(css_declarations(self.app_wxss, ".btn")["min-height"], "48px")
        self.assertEqual(
            css_declarations(self.app_wxss, ".btn + .btn")["margin-top"],
            "12px",
        )
        self.assertEqual(css_declarations(self.app_wxss, ".btn-row")["gap"], "12px")
        self.assertEqual(
            css_declarations(self.app_wxss, ".input-card")["margin-bottom"],
            "12px",
        )

    def test_primary_and_secondary_actions_use_semantic_twenty_pixel_transition(self):
        self.assertEqual(
            css_declarations(self.app_wxss, ".action-group + .action-group")["margin-top"],
            "20px",
        )
        button_stack = css_declarations(self.app_wxss, ".button-stack")
        self.assertEqual(button_stack["display"], "flex")
        self.assertEqual(button_stack["flex-direction"], "column")
        self.assertEqual(button_stack["gap"], "12px")
        self.assertEqual(
            css_declarations(self.app_wxss, ".button-stack .btn")["margin-top"],
            "0",
        )

        semantic_pages = {**self.action_pages, "result": self.result_wxml}
        adjacent_groups = re.compile(
            r'<view class="action-group action-group--primary [^"]+">\s*'
            r"<button[^>]*>.*?</button>\s*</view>\s*"
            r'<view class="action-group action-group--secondary [^"]+">',
            re.DOTALL,
        )
        for name, markup in semantic_pages.items():
            with self.subTest(page=name):
                self.assertRegex(markup, adjacent_groups)

        no_wrong_result = self.result_wxml.split("<block wx:else>", 1)[1]
        self.assertRegex(no_wrong_result, adjacent_groups)

    def test_no_wrong_result_does_not_repeat_again_action(self):
        self.assertIn('<block wx:if="{{result.wrong_question_ids.length}}">', self.result_wxml)
        self.assertIn("马上翻盘", self.result_wxml)
        self.assertIn('<block wx:else>', self.result_wxml)
        self.assertEqual(self.result_wxml.count("再考一篇"), 2)


if __name__ == "__main__":
    unittest.main()
