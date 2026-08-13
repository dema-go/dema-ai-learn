import { api, errorMessage, Question, QuizResponse } from "../../services/api";

const KEYS = ["A", "B", "C", "D"];

Page({
  data: {
    quiz: {} as QuizResponse,
    question: null as Question | null,
    index: 0,
    selected: -1,
    submitted: false,
    isCorrect: false,
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

  onSelect(event: WechatMiniprogram.TouchEvent) {
    if (this.data.submitted) return;
    this.setData({ selected: Number(event.currentTarget.dataset.index) });
  },

  async onConfirm() {
    if (!this.data.submitted) {
      if (this.data.selected < 0) {
        wx.showToast({ title: "先选一个答案", icon: "none" });
        return;
      }
      try {
        const question = this.data.question as Question;
        const res = await api.answer(this.data.quiz.id, {
          question_id: question.question_id,
          chosen_index: this.data.selected,
          attempt_id: this.data.attemptId || undefined,
        });
        this.setData({
          submitted: true,
          isCorrect: res.is_correct,
          explanation: res.explanation,
          sourceSpan: res.source_span,
          showSource: !res.is_correct,
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
        wx.showToast({ title: errorMessage(err, "提交失败"), icon: "none" });
      }
      return;
    }
    if (this.data.finished) {
      wx.redirectTo({ url: `/pages/result/result?quizId=${this.data.quiz.id}` });
      return;
    }
    const nextIndex = this.data.index + 1;
    const next = this.data.quiz.questions[nextIndex];
    this.setData({
      index: nextIndex,
      question: next,
      selected: -1,
      submitted: false,
      isCorrect: false,
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
