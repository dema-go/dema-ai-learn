from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MINIPROGRAM = ROOT / "miniprogram"


class MiniProgramQuizUiContractTests(unittest.TestCase):
    def setUp(self):
        self.quiz_ts = (MINIPROGRAM / "pages/quiz/quiz.ts").read_text(encoding="utf-8")
        self.quiz_wxml = (MINIPROGRAM / "pages/quiz/quiz.wxml").read_text(encoding="utf-8")
        self.quiz_wxss = (MINIPROGRAM / "pages/quiz/quiz.wxss").read_text(encoding="utf-8")
        self.app_wxss = (MINIPROGRAM / "app.wxss").read_text(encoding="utf-8")
        self.result_wxml = (MINIPROGRAM / "pages/result/result.wxml").read_text(encoding="utf-8")

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

    def test_quiz_layout_uses_full_width_choices_and_fixed_action(self):
        compact = "".join(self.quiz_wxss.split())
        self.assertIn(".quiz-screen{padding-left:16px;padding-right:16px", compact)
        self.assertIn(".choice-list{display:flex;flex-direction:column;gap:12px", compact)
        self.assertIn(".choice-card{width:100%;min-height:56px", compact)
        self.assertIn(".bottom-action{position:fixed", compact)
        self.assertIn("padding-bottom:calc(12px+env(safe-area-inset-bottom))", compact)

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
        compact = "".join(self.app_wxss.split())
        self.assertIn(".screen{padding:18px16px96px", compact)
        self.assertIn(".card+.card{margin-top:16px", compact)
        self.assertIn("min-height:48px", compact)
        self.assertIn(".btn+.btn{margin-top:12px", compact)
        self.assertIn(".btn-row{display:flex;gap:12px;margin-top:20px", compact)
        self.assertIn(".btn-row.btn+.btn{margin-top:0", compact)
        self.assertIn(".input-card", self.app_wxss)
        self.assertIn("margin-bottom: 12px", self.app_wxss)

    def test_no_wrong_result_does_not_repeat_again_action(self):
        self.assertIn('<block wx:if="{{result.wrong_question_ids.length}}">', self.result_wxml)
        self.assertIn("马上翻盘", self.result_wxml)
        self.assertIn('<block wx:else>', self.result_wxml)
        self.assertEqual(self.result_wxml.count("再考一篇"), 2)


if __name__ == "__main__":
    unittest.main()
