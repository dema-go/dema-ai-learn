import { api, errorMessage, QuizResponse } from "../../services/api";

Page({
  data: {
    quiz: {
      id: "",
      material_id: "",
      title: "",
      question_count: 0,
      is_degraded: false,
      is_retest: false,
      ai_notice: "",
      questions: [],
    } as QuizResponse,
  },

  async onLoad(query: Record<string, string>) {
    try {
      const quiz = await api.quiz(query.quizId || "");
      this.setData({ quiz });
    } catch (err) {
      wx.showToast({ title: errorMessage(err, "详情加载失败"), icon: "none" });
    }
  },

  onWrong() {
    wx.navigateTo({ url: `/pages/wrong-book/wrong-book?quizId=${this.data.quiz.id}` });
  },

  onDelete() {
    wx.navigateTo({
      url: `/pages/delete-confirm/delete-confirm?materialId=${this.data.quiz.material_id}&title=${encodeURIComponent(this.data.quiz.title)}`,
    });
  },
});
