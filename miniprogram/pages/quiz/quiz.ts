import { api, errorMessage, Question, QuizResponse } from "../../services/api";
import {
  AnswerViewState,
  beginAnswerSubmission,
  createAnswerState,
  failAnswerSubmission,
  resolveAnswerSubmission,
} from "../../utils/answer-state";

const KEYS = ["A", "B", "C", "D"];

Page({
  data: {
    quiz: {} as QuizResponse,
    question: null as Question | null,
    index: 0,
    answer: createAnswerState() as AnswerViewState,
    explanation: "",
    sourceSpan: "",
    showSource: false,
    finished: false,
    keys: KEYS,
    percent: 0,
    attemptId: "",
  },

  async onLoad(query: Record<string, string>) {
    try {
      const quiz = await api.quiz(query.quizId || "");
      this.setData({
        quiz,
        question: quiz.questions[0],
        index: 0,
        percent: Math.round(100 / quiz.question_count),
        showSource: !!query.retest,
      });
    } catch (err) {
      wx.showToast({ title: errorMessage(err, "题目加载失败"), icon: "none" });
    }
  },

  async onSelect(event: WechatMiniprogram.TouchEvent) {
    const selectedIndex = Number(event.currentTarget.dataset.index);
    const submitting = beginAnswerSubmission(this.data.answer, selectedIndex);
    if (submitting === this.data.answer) return;

    this.setData({ answer: submitting });
    try {
      const question = this.data.question as Question;
      const res = await api.answer(this.data.quiz.id, {
        question_id: question.question_id,
        chosen_index: selectedIndex,
        attempt_id: this.data.attemptId || undefined,
      });
      this.setData({
        answer: resolveAnswerSubmission(
          submitting,
          res.is_correct,
          res.correct_index,
          res.chosen_index,
        ),
        explanation: res.explanation,
        sourceSpan: res.source_span,
        showSource: false,
        finished: res.finished,
        attemptId: res.attempt_id,
      });
      if (res.result) {
        wx.setStorageSync("last_result", {
          quizId: this.data.quiz.id,
          title: this.data.quiz.title,
          ...res.result,
        });
      }
    } catch (err) {
      this.setData({ answer: failAnswerSubmission(submitting) });
      wx.showToast({ title: errorMessage(err, "提交失败，请重新选择"), icon: "none" });
    }
  },

  onNext() {
    if (this.data.answer.phase !== "answered") return;
    if (this.data.finished) {
      wx.redirectTo({ url: `/pages/result/result?quizId=${this.data.quiz.id}` });
      return;
    }
    const nextIndex = this.data.index + 1;
    const next = this.data.quiz.questions[nextIndex];
    this.setData({
      index: nextIndex,
      question: next,
      answer: createAnswerState(),
      explanation: "",
      sourceSpan: "",
      showSource: false,
      percent: Math.round(((nextIndex + 1) / this.data.quiz.question_count) * 100),
    });
  },

  toggleSource() {
    this.setData({ showSource: !this.data.showSource });
  },

  onReport() {
    const question = this.data.question as Question;
    wx.navigateTo({ url: `/pages/report/report?questionId=${question.question_id}&stem=${encodeURIComponent(question.stem)}` });
  },
});
