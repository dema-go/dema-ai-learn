from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MINIPROGRAM = ROOT / "miniprogram"


class MiniProgramQuizUiContractTests(unittest.TestCase):
    def setUp(self):
        self.quiz_ts = (MINIPROGRAM / "pages/quiz/quiz.ts").read_text(encoding="utf-8")
        self.quiz_wxml = (MINIPROGRAM / "pages/quiz/quiz.wxml").read_text(encoding="utf-8")

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


if __name__ == "__main__":
    unittest.main()
